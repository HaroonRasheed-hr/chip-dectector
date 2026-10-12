# Chip Detector — Frontend/Backend Integration Documentation

This document explains exactly how the Next.js frontend is built and served
by the Django backend so the entire application runs from a single port
(`http://localhost:8000`). It covers:

1. The integration strategy and why each piece was chosen.
2. Every file that was created or modified, with the rationale.
3. How to build and run the application — both for local use and for
   production deployment.
4. How URL routing is resolved at request time.
5. Troubleshooting tips.

---

## Table of Contents

1. [Goal](#1-goal)
2. [High-Level Approach](#2-high-level-approach)
3. [Architecture Overview](#3-architecture-overview)
4. [Files Changed](#4-files-changed)
   - 4.1 [`frontend/next.config.mjs`](#41-frontendnextconfigmjs)
   - 4.2 [`frontend/src/app/page.tsx`](#42-frontendsrcapppagetsx)
   - 4.3 [`backend/requirements.txt`](#43-backendrequirementstxt)
   - 4.4 [`backend/config/settings/base.py`](#44-backendconfigsettingsbasepy)
   - 4.5 [`backend/config/settings/production.py`](#45-backendconfigsettingsproductionpy)
   - 4.6 [`backend/core/views/__init__.py`](#46-backendcoreviewsinitpy)
   - 4.7 [`backend/core/views/frontend.py`](#47-backendcoreviewsfrontendpy)
   - 4.8 [`backend/config/urls.py`](#48-backendconfigurlspy)
   - 4.9 [`backend/scripts/build_frontend.py`](#49-backendscriptsbuild_frontendpy)
   - 4.10 [`run.py`](#410-runpy)
5. [How to Build and Run](#5-how-to-build-and-run)
6. [URL Resolution at Request Time](#6-url-resolution-at-request-time)
7. [Production Deployment](#7-production-deployment)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Goal

When the backend server is started, the entire application — both the
Next.js UI and the Django REST API — must be reachable through a single
URL (`http://localhost:8000`), with **one command** to start everything.

Concretely:

- Visiting `/` opens the Next.js UI (login page).
- `/login/`, `/register/`, `/detection/` render the corresponding Next.js
  pages.
- `/api/...` continues to serve JSON from Django REST Framework.
- `/admin/...` still serves the Django admin.
- No separate `npm run dev` / `next start` process is required.

---

## 2. High-Level Approach

We compile the Next.js application to a **static HTML/JS/CSS export** and
let Django serve those files directly. This works because the frontend
talks to the backend through HTTP/JSON only; it does not need a Node.js
runtime in production.

The three building blocks:

1. **Next.js static export** — `output: "export"` in `next.config.mjs`
   produces `frontend/out/` containing pre-rendered HTML for every route
   plus the hashed `_next/static/*` asset bundle.
2. **Django catch-all view** — a single view (`serve_frontend`) maps any
   non-API URL to a file inside `frontend/out/`, returning the correct
   MIME type and cache headers.
3. **WhiteNoise middleware** — production-grade static-file handler for
   Django's own assets (admin/DRF CSS), with gzip/brotli compression and
   hashed filenames.

A one-command launcher (`run.py`) ties them together: build the
frontend, run migrations, collect Django static files, then start the
server.

---

## 3. Architecture Overview

```
            Browser
                │
                ▼
   ┌──────────────────────────┐
   │  http://localhost:8000   │
   └──────────────────────────┘
                │
                ▼
   ┌──────────────────────────┐
   │   Django (wsgi/asgi)     │
   ├──────────────────────────┤
   │ MIDDLEWARE:              │
   │   SecurityMiddleware     │
   │   WhiteNoiseMiddleware ──┼──► /static/*  (Django admin / DRF)
   │   ...                    │
   ├──────────────────────────┤
   │ URL conf (config/urls.py)│
   │                          │
   │   /admin/* ──► admin     │
   │   /api/*   ──► DRF apps  │
   │   /media/* ──► media     │
   │   else     ──► serve_frontend(path)
   │                 │
   │                 ▼
   │       frontend/out/
   │         index.html
   │         login/index.html
   │         register/index.html
   │         detection/index.html
   │         _next/static/<hash>.{js,css}
   │         images/...
   │         404.html
   └──────────────────────────┘
```

The frontend build directory (`frontend/out/`) is **read at request
time** — there is no copy step into Django. This keeps the build flow
simple: rebuild the frontend, restart Django, and the new assets are
live.

---

## 4. Files Changed

Below, every file that was added or modified, in order, with the reason
and the relevant snippet.

### 4.1 `frontend/next.config.mjs`

**Why:** Enable static export so the frontend can be served by Django.

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static HTML/CSS/JS export so the Django backend can serve the
  // frontend without running a separate Node.js process in production.
  output: "export",

  // Emit `route/index.html` instead of `route.html` so Django's catch-all
  // can serve a folder for every client-side route.
  trailingSlash: true,

  // `next/image` requires a runtime image optimizer; disable it for the
  // static export so images are served as plain files.
  images: {
    unoptimized: true,
    remotePatterns: [],
  },
};

export default nextConfig;
```

Notes:

- `output: "export"` replaces the legacy `next export` command in Next.js
  14 and produces a fully static `out/` directory.
- `trailingSlash: true` makes every route a folder with `index.html`
  inside — easier to serve from a generic file handler.
- `images.unoptimized: true` is mandatory for static export because the
  default `next/image` loader needs a server process.

### 4.2 `frontend/src/app/page.tsx`

**Why:** The original root page used `redirect()` from `next/navigation`
in a server component. Under `output: "export"` that produces an
`__next_error__` page (with a `NEXT_REDIRECT` digest) instead of a real
HTML file. Converted to a client-side redirect.

```tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return null;
}
```

### 4.3 `backend/requirements.txt`

**Why:** Add WhiteNoise so Django can serve its own static assets with
gzip/brotli compression and hashed filenames in production.

```diff
 django-environ==0.11.2
 Pillow==10.4.0
+
+# Production static-file serving (also fronts the Next.js export)
+whitenoise==6.7.0
```

### 4.4 `backend/config/settings/base.py`

Three coordinated changes:

**(a) Project-root + frontend paths** — exposed as Django settings so the
catch-all view can find `frontend/out/` regardless of where Django was
started from.

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / 'frontend'
FRONTEND_BUILD_DIR = FRONTEND_DIR / 'out'
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
```

**(b) WhiteNoise middleware** — registered immediately after
`SecurityMiddleware`, which is WhiteNoise's required position.

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must come directly after SecurityMiddleware so it can
    # serve the collected Django static files AND the Next.js export
    # (mounted via STATICFILES_DIRS below) with proper cache headers.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    ...
]
```

**(c) Static-files configuration**

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'   # collectstatic target
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_DIRS = [
    p for p in [BASE_DIR / 'static'] if p.exists()
]

# Compressed (gzip/brotli) storage for Django's own static assets.
# `production.py` swaps this for the manifest variant so admin/DRF CSS
# gets content-addressed filenames behind a CDN.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}
```

`STATIC_ROOT` was renamed from `static/` to `staticfiles/` so
`collectstatic` does not clobber any project-owned source assets sitting
in `backend/static/` (declared via `STATICFILES_DIRS`).

### 4.5 `backend/config/settings/production.py`

**Why:** In production, swap to the manifest storage so admin/DRF CSS
gets hashed filenames behind a CDN.

```python
STORAGES['staticfiles'] = {  # noqa: F405
    'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
}
```

### 4.6 `backend/core/views/__init__.py`

**Why:** Promotes `core/views/` from a stale `__pycache__`-only folder to
a proper Python package so `core.views.frontend` is importable.

```python
# (empty)
```

### 4.7 `backend/core/views/frontend.py`

**Why:** The single catch-all view that resolves any non-API URL to a
file inside `frontend/out/`.

Key behaviours:

- **Direct file hits** (e.g. `/_next/static/chunks/foo.js`,
  `/favicon.ico`, images) are returned as-is with the right MIME type.
- **Route HTML** (`/login`, `/login/`, …) is resolved to
  `frontend/out/<path>/index.html` thanks to the `trailingSlash: true`
  build config.
- **Path traversal** attempts (`/../../etc/passwd`) are rejected by
  resolving the candidate path and checking it stays inside
  `FRONTEND_BUILD_DIR`.
- **Caching** — hashed `_next/static/*` assets get
  `Cache-Control: public, max-age=31536000, immutable`; HTML shells get
  `Cache-Control: no-cache` so they always pick up the latest hashed
  chunk references.
- **404 fallback** — unknown routes return Next.js' generated
  `404.html` with HTTP status 404.

Excerpt:

```python
@require_safe
def serve_frontend(request, path: str = "") -> HttpResponse:
    root = _build_root()

    clean = posixpath.normpath("/" + path).lstrip("/")
    if clean == ".":
        clean = ""

    # 1) Try a direct file hit (assets, images, …)
    if clean:
        direct = _resolve_safe(root, clean)
        if direct is not None and direct.is_file():
            response = _file_response(direct)
            if clean.startswith("_next/static/"):
                response["Cache-Control"] = (
                    "public, max-age=31536000, immutable"
                )
            return response

    # 2) Fall back to <path>/index.html for client-side routes
    html_candidate = _resolve_safe(root, posixpath.join(clean, "index.html"))
    if html_candidate is not None and html_candidate.is_file():
        response = _file_response(html_candidate)
        response["Cache-Control"] = "no-cache"
        return response

    return _serve_404(root)
```

### 4.8 `backend/config/urls.py`

**Why:** Register the catch-all _after_ all reserved prefixes, and use a
regex with a negative lookahead so the API and admin routes always win.

```python
_RESERVED_PREFIXES = ("api/", "admin/", "static/", "media/")
_RESERVED_PATTERN = r"^(?P<path>(?!(?:{})).*)$".format(
    "|".join(p.replace("/", r"\/") for p in _RESERVED_PREFIXES)
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/inference/', include('apps.inference.urls')),
    path('api/monitoring/', include('apps.monitoring.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    path('', serve_index, name='frontend-index'),
    re_path(_RESERVED_PATTERN, serve_frontend, name='frontend-catchall'),
]
```

The named-group regex `(?P<path>...)` is what passes the URL path to the
view as its `path` kwarg.

### 4.9 `backend/scripts/build_frontend.py`

**Why:** Cross-platform helper that installs node modules (when stale)
and runs `next build`, producing `frontend/out/`. Used by `run.py` and
callable on its own.

Highlights:

- Resolves `npm.cmd` on Windows.
- Uses `npm ci` when `package-lock.json` exists, else `npm install`.
- Skips the install when `node_modules/` is newer than the lockfile.
- Aborts with a clear message if `frontend/out/` is missing after the
  build (which indicates `output: "export"` was removed from
  `next.config.mjs`).

### 4.10 `run.py`

**Why:** Single entry-point so the user only needs one command. Located
at the project root.

What it does, in order:

1. Build the frontend (`backend/scripts/build_frontend.py`) unless
   `--no-build` is passed.
2. `python manage.py migrate --noinput` (skip with `--no-migrate`).
3. `python manage.py collectstatic --noinput` (skip with
   `--no-collectstatic`).
4. Start the server:
   - default → `python manage.py runserver <host>:<port> --insecure`
     using `config.settings.development`.
   - `--prod` → `gunicorn config.wsgi:application` using
     `config.settings.production`.

CLI flags:

| Flag | Purpose |
| --- | --- |
| `--host HOST` | Bind address (default `127.0.0.1`). |
| `--port PORT` | Port (default `8000`). |
| `--no-build` | Reuse the existing `frontend/out/`. |
| `--no-migrate` | Skip migrations. |
| `--no-collectstatic` | Skip collectstatic. |
| `--prod` | Production settings + gunicorn. |

---

## 5. How to Build and Run

### 5.1 First-time setup

```powershell
# From the repository root
pip install -r backend/requirements.txt
npm --prefix frontend ci

# Configure environment
copy backend\.env.example backend\.env   # then edit SECRET_KEY etc.
```

### 5.2 Start the entire application

```powershell
python run.py
```

This will:

1. Install npm dependencies if stale, then run `next build`.
2. Apply Django migrations.
3. Run `collectstatic` into `backend/staticfiles/`.
4. Start the server on `http://127.0.0.1:8000`.

Open `http://localhost:8000` — the login page loads from the Next.js
build, served by Django.

### 5.3 Common variations

```powershell
# Reuse the existing build (fastest restart)
python run.py --no-build

# Different port
python run.py --port 9000

# Bind on all interfaces (e.g. for LAN demos)
python run.py --host 0.0.0.0

# Skip the heavy bootstrap steps
python run.py --no-build --no-migrate --no-collectstatic
```

### 5.4 Building the frontend without starting the server

```powershell
python backend/scripts/build_frontend.py
```

The build output lives at `frontend/out/`. The next time you run
`python run.py --no-build`, Django will serve that build directly.

---

## 6. URL Resolution at Request Time

When a request reaches Django:

1. **Middleware chain** runs (CORS → Security → WhiteNoise → …). If the
   URL matches a file in `STATIC_ROOT`, WhiteNoise returns it
   immediately and the URL conf is never consulted. This is how
   `/static/admin/css/base.css` works.
2. **URL conf** dispatches the request:
   - `/admin/...` → Django admin.
   - `/api/auth/...`, `/api/inference/...`, `/api/monitoring/...` → DRF
     viewsets (JSON).
   - `/media/...` → served by `django.conf.urls.static` when
     `DEBUG=True`; in production, fronted by nginx.
   - Everything else → `serve_frontend(path)`.
3. **Catch-all view** resolves `path`:
   - `""` → `frontend/out/index.html` (the login redirect).
   - `"_next/static/<hash>.js"` → that file with immutable Cache-Control.
   - `"login"` or `"login/"` → `frontend/out/login/index.html`.
   - Unknown route → `frontend/out/404.html` with HTTP 404.

Verified examples (live server):

```
GET /                  -> 200 text/html
GET /login/  /login    -> 200 text/html
GET /register/         -> 200 text/html
GET /detection/        -> 200 text/html
GET /nonsense          -> 404 text/html  (404.html)
GET /_next/static/…css -> 200 text/css   Cache-Control: max-age=1y, immutable
POST /api/auth/login/  -> 400 application/json (validation error)
GET /admin/login/      -> 200 text/html
```

---

## 7. Production Deployment

For a real deployment behind HTTPS:

```bash
pip install gunicorn
python run.py --prod --host 0.0.0.0 --port 8000
```

Notes:

- `--prod` switches to `config.settings.production`, which enforces HSTS,
  `SECURE_SSL_REDIRECT=True`, and uses
  `CompressedManifestStaticFilesStorage` for hashed admin/DRF assets.
- Because of `SECURE_SSL_REDIRECT`, the gunicorn process must sit
  behind a TLS-terminating reverse proxy (nginx, Caddy, Cloudflare …)
  that forwards `X-Forwarded-Proto: https`. Otherwise every request
  enters a redirect loop.
- Tune workers via the environment variable `GUNICORN_WORKERS`
  (default `3`).
- `/media/` should be served by the reverse proxy directly, not Django
  (`urls.py` only wires it when `DEBUG=True`).

Suggested nginx skeleton:

```nginx
upstream visionpulse {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name visionpulse.example.com;

    ssl_certificate     /etc/letsencrypt/live/.../fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/.../privkey.pem;

    client_max_body_size 25m;

    location /media/ {
        alias /var/lib/visionpulse/media/;
    }

    location / {
        proxy_pass http://visionpulse;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 8. Troubleshooting

| Symptom | Cause / Fix |
| --- | --- |
| `Frontend build not found` error from Django | `frontend/out/` does not exist. Run `python run.py` (without `--no-build`) or `python backend/scripts/build_frontend.py`. |
| Visiting `/` shows a broken `__next_error__` page with a `NEXT_REDIRECT` digest | The root `page.tsx` is still using server-side `redirect()`. Use the client-side version shown in [4.2](#42-frontendsrcapppagetsx) and rebuild. |
| `next/image` errors during build | `images.unoptimized: true` missing in `next.config.mjs` ([4.1](#41-frontendnextconfigmjs)). |
| Admin loads but the CSS is missing | `collectstatic` has not been run. Either let `run.py` do it (default) or run `python manage.py collectstatic --noinput` from `backend/`. |
| API request returns the login HTML instead of JSON | The URL must start with `/api/`. Confirm the reserved-prefix list in [`config/urls.py`](#48-backendconfigurlspy) still includes `api/`. |
| Static asset gives 404 from `/_next/static/...` | Browser is holding onto an old hashed filename. Hard-refresh (Ctrl+F5). The HTML shell is served with `no-cache`, so the stale reference will not persist beyond one round-trip. |
| Endless `http→https` redirect in production | `--prod` enabled `SECURE_SSL_REDIRECT` but the reverse proxy is not forwarding `X-Forwarded-Proto: https`. Configure the proxy headers as shown in [§7](#7-production-deployment). |
| `gunicorn: command not found` | `pip install gunicorn`. It is not in `requirements.txt` because the default localhost flow uses `runserver`. |

---

**Last verified:** `python run.py` → all routes returned the expected
status codes against a live Django server on `http://127.0.0.1:8000`.
