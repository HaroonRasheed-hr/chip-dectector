# Chip Detector — Full-Stack Setup & Run Guide

Complete guide for cloning, configuring, and running the Chip Detector full-stack
application (Next.js frontend + Django backend) from scratch.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Project Structure](#3-project-structure)
4. [Backend Setup](#4-backend-setup)
   - 4.1 [Create a Python Virtual Environment](#41-create-a-python-virtual-environment)
   - 4.2 [Install Python Dependencies](#42-install-python-dependencies)
   - 4.3 [Configure Environment Variables](#43-configure-environment-variables)
5. [Frontend Setup](#5-frontend-setup)
6. [Run the Full Stack (One Command)](#6-run-the-full-stack-one-command)
7. [Run Frontend and Backend Separately (Development)](#7-run-frontend-and-backend-separately-development)
8. [All Available Run Commands](#8-all-available-run-commands)
9. [Environment Variables Reference](#9-environment-variables-reference)
10. [Production Deployment](#10-production-deployment)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

Install the following tools before you begin.

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| **Git** | 2.x | Clone the repository |
| **Python** | 3.10+ | Django backend runtime |
| **pip** | 23+ | Python package installer |
| **Node.js** | 18.x LTS or 20.x LTS | Build the Next.js frontend |
| **npm** | 9+ | Node package manager (bundled with Node.js) |

> **Windows users:** All commands below use PowerShell. The Python executable
> may be `python` or `py` depending on your installation.

Verify your installations:

```powershell
python --version     # Python 3.10+
node --version       # v18.x or v20.x
npm --version        # 9.x or higher
git --version
```

---

## 2. Clone the Repository

```powershell
git clone https://github.com/HaroonRasheed-hr/chip-dectector.git
cd chip-dectector
```

To pull the latest changes after an initial clone:

```powershell
git pull origin main
```

To switch to the active development branch:

```powershell
git checkout feature/backend-development
git pull origin feature/backend-development
```

---

## 3. Project Structure

```
chip-dectector/
├── backend/                  # Django REST API
│   ├── apps/
│   │   ├── users/            # Authentication (JWT)
│   │   ├── inference/        # AI inference endpoints
│   │   ├── monitoring/       # System metrics
│   │   ├── calibration/      # Sensor calibration
│   │   ├── mqtt_manager/     # MQTT client
│   │   └── websocket/        # WebSocket support
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py       # Shared settings
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── core/                 # Shared middleware, views, utilities
│   ├── scripts/              # Helper scripts
│   │   ├── build_frontend.py # Builds Next.js frontend
│   │   └── gpu_check.py      # GPU availability check
│   ├── manage.py
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Environment variable template
│   └── db.sqlite3            # SQLite database (auto-created)
│
├── frontend/                 # Next.js 14 application
│   ├── src/
│   │   ├── app/              # Next.js App Router pages
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── detection/
│   │   └── components/
│   ├── public/               # Static assets
│   ├── out/                  # Built static export (generated)
│   ├── package.json
│   └── next.config.mjs
│
├── Docs/                     # Project documentation
├── run.py                    # Single entry-point to run everything
└── README.md
```

---

## 4. Backend Setup

### 4.1 Create a Python Virtual Environment

Using a virtual environment keeps project dependencies isolated.

**Windows (PowerShell):**
```powershell
cd chip-dectector
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux (bash):**
```bash
cd chip-dectector
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your prompt after activation.

### 4.2 Install Python Dependencies

```powershell
pip install -r backend/requirements.txt
```

**What gets installed:**

| Package | Version | Purpose |
|---------|---------|---------|
| `Django` | 4.2.13 | Web framework |
| `djangorestframework` | 3.15.2 | REST API toolkit |
| `djangorestframework-simplejwt` | 5.3.1 | JWT authentication |
| `django-cors-headers` | 4.3.1 | Cross-Origin Resource Sharing |
| `django-environ` | 0.11.2 | `.env` file support |
| `Pillow` | 10.4.0 | Image processing |
| `whitenoise` | 6.7.0 | Static file serving (serves the built frontend) |
| `paho-mqtt` | 2.1.0 | MQTT client for Mosquitto broker |
| `psutil` | 6.0.0 | System performance monitoring |
| `nvidia-ml-py` | 12.560.30 | NVIDIA GPU monitoring |

### 4.3 Configure Environment Variables

Copy the example file and edit it:

**Windows (PowerShell):**
```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

**macOS / Linux:**
```bash
cp backend/.env.example backend/.env
nano backend/.env
```

The minimum required change is setting a unique `SECRET_KEY`:

```env
# backend/.env

SECRET_KEY=replace-this-with-a-long-random-string-50-chars-minimum
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
REFRESH_COOKIE_SECURE=False
```

Generate a strong `SECRET_KEY` with:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 5. Frontend Setup

Install Node.js dependencies for the frontend:

```powershell
npm --prefix frontend ci
```

> `npm ci` installs exact versions from `package-lock.json` for reproducible
> builds. Use `npm install` only if you want to update dependencies.

**Frontend dependencies installed:**

| Package | Version | Purpose |
|---------|---------|---------|
| `next` | 14.2.29 | React framework |
| `react` | ^18 | UI library |
| `react-dom` | ^18 | DOM rendering |
| `lucide-react` | ^0.378.0 | Icon library |
| `@iconify/react` | ^6.0.2 | Extended icon set |
| `tailwindcss` | ^3.4.1 | Utility-first CSS framework |
| `typescript` | ^5 | Type-safe JavaScript |

---

## 6. Run the Full Stack (One Command)

From the **project root** (where `run.py` lives), run:

```powershell
python run.py
```

This single command does everything in sequence:

1. Installs npm dependencies if stale, then builds the Next.js frontend into `frontend/out/`
2. Applies Django database migrations (`manage.py migrate`)
3. Collects Django static files (`manage.py collectstatic`)
4. Starts the Django development server on `http://127.0.0.1:8000`

Open your browser at **`http://localhost:8000`** — the full application is running.

| URL | What you see |
|-----|-------------|
| `http://localhost:8000/` | Login page (Next.js) |
| `http://localhost:8000/login/` | Login page |
| `http://localhost:8000/register/` | Registration page |
| `http://localhost:8000/detection/` | Detection dashboard |
| `http://localhost:8000/api/auth/` | Auth API (JSON) |
| `http://localhost:8000/api/inference/` | Inference API (JSON) |
| `http://localhost:8000/api/monitoring/` | Monitoring API (JSON) |
| `http://localhost:8000/admin/` | Django admin panel |

---

## 7. Run Frontend and Backend Separately (Development)

Use this approach when you are actively developing the frontend and want
hot-reload (instant browser refresh on file save).

### Terminal 1 — Django backend

```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

cd backend
$env:DJANGO_SETTINGS_MODULE = "config.settings.development"
python manage.py migrate
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`.

### Terminal 2 — Next.js frontend (hot-reload)

```powershell
cd frontend
npm run dev
```

Frontend dev server runs at `http://localhost:3000` with hot-reload enabled.

> When running separately, the frontend calls the Django API at `localhost:8000`.
> CORS is pre-configured to allow `http://localhost:3000`.

---

## 8. All Available Run Commands

### `run.py` (Full-Stack Launcher)

Run from the project root:

```powershell
# Standard start (build + migrate + collectstatic + serve)
python run.py

# Skip rebuilding the frontend (fastest restart after code-only changes)
python run.py --no-build

# Skip migrations (useful when no model changes were made)
python run.py --no-migrate

# Skip collectstatic
python run.py --no-collectstatic

# Skip all setup steps — just start the server
python run.py --no-build --no-migrate --no-collectstatic

# Custom port
python run.py --port 9000

# Bind on all network interfaces (e.g. for LAN access)
python run.py --host 0.0.0.0

# Production mode (requires gunicorn installed)
python run.py --prod
```

### Django Management Commands

Run from the `backend/` directory with venv activated:

```powershell
cd backend

# Apply database migrations
python manage.py migrate

# Create a superuser (for Django admin)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver

# Run development server on a specific port
python manage.py runserver 0.0.0.0:8080

# Run tests
python manage.py test
```

### Frontend npm Commands

Run from the `frontend/` directory:

```powershell
cd frontend

# Development server with hot-reload
npm run dev

# Production build (outputs to frontend/out/)
npm run build

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Lint the codebase
npm run lint
```

### Build Frontend Only (without starting the server)

```powershell
python backend/scripts/build_frontend.py
```

---

## 9. Environment Variables Reference

All variables go in `backend/.env`. Only `SECRET_KEY` is required; all others
have sensible defaults for development.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | **(required)** | Django secret key — use a 50+ char random string |
| `DEBUG` | `False` | Set to `True` for development |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection string |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Allowed CORS origins for the API |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | Access token expiry in minutes |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Refresh token expiry in days |
| `REFRESH_COOKIE_SECURE` | `False` | Set to `True` in production (requires HTTPS) |
| `MQTT_ENABLED` | `False` | Enable MQTT client |
| `MQTT_HOST` | `localhost` | MQTT broker hostname |
| `MQTT_PORT` | `1883` | MQTT broker port |
| `MQTT_USERNAME` | *(empty)* | MQTT broker username |
| `MQTT_PASSWORD` | *(empty)* | MQTT broker password |
| `MONITORING_ENABLED` | `True` | Enable system metrics collection |
| `MONITORING_INTERVAL_SECONDS` | `5` | Metrics polling interval |
| `INFERENCE_DEFAULT_PROVIDER` | `stub` | Inference backend (`stub` for testing) |

---

## 10. Production Deployment

### Install Gunicorn

```bash
pip install gunicorn
```

### Set Production Environment Variables

```env
DEBUG=False
SECRET_KEY=<long-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
REFRESH_COOKIE_SECURE=True
DATABASE_URL=postgres://user:pass@localhost:5432/visionpulse
```

### Start in Production Mode

```bash
python run.py --prod --host 0.0.0.0 --port 8000
```

Production mode:
- Uses `config.settings.production` (HSTS, SSL redirect, hashed static files)
- Serves via **gunicorn** with 3 workers (override with `GUNICORN_WORKERS=<n>`)
- Requires a TLS-terminating reverse proxy (nginx, Caddy, Cloudflare)

### Suggested nginx Configuration

```nginx
upstream visionpulse {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 25m;

    location /media/ {
        alias /path/to/visionpulse/backend/media/;
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

## 11. Troubleshooting

| Symptom | Cause & Fix |
|---------|-------------|
| `SECRET_KEY` missing error on start | `backend/.env` does not exist or `SECRET_KEY` is not set. Copy `.env.example` to `.env` and fill in a key. |
| `No module named 'django'` | Virtual environment is not activated. Run `.\venv\Scripts\Activate.ps1` (Windows) or `source venv/bin/activate` (Linux/Mac). |
| `npm: command not found` | Node.js is not installed or not on PATH. Download from [nodejs.org](https://nodejs.org). |
| `Frontend build not found` error | `frontend/out/` does not exist. Run `python run.py` without `--no-build`, or run `python backend/scripts/build_frontend.py`. |
| `--no-build` fails immediately | `frontend/out/` was deleted or never built. Remove `--no-build` and run `python run.py` to build it. |
| Login page shows `__next_error__` | Root `page.tsx` uses server-side `redirect()`. It should use a client-side `useEffect` redirect — see `Build-doc.md §4.2`. |
| Admin loads but CSS is missing | `collectstatic` has not been run. Either run `python run.py` (it runs it by default) or run `python manage.py collectstatic --noinput` from `backend/`. |
| API returns HTML instead of JSON | The request URL must start with `/api/`. Confirm you are hitting `/api/auth/`, `/api/inference/`, etc. |
| Port 8000 already in use | Another process is using the port. Run `python run.py --port 9000` to use a different port, or stop the conflicting process. |
| `gunicorn: command not found` | Install it: `pip install gunicorn`. It is not in `requirements.txt` because development uses `runserver`. |
| Endless `http → https` redirect in production | `SECURE_SSL_REDIRECT=True` is active but the reverse proxy is not forwarding `X-Forwarded-Proto: https`. Add the proxy header as shown in §10. |
| CORS error in browser during separate dev mode | The frontend dev server (port 3000) must be listed in `CORS_ALLOWED_ORIGINS` in `backend/.env`. Default value covers this. |

---

## Quick-Start Checklist

```
[ ] Git clone: git clone https://github.com/HaroonRasheed-hr/chip-dectector.git
[ ] Create venv: python -m venv venv && .\venv\Scripts\Activate.ps1
[ ] Install Python deps: pip install -r backend/requirements.txt
[ ] Install Node deps: npm --prefix frontend ci
[ ] Create .env: Copy-Item backend\.env.example backend\.env
[ ] Set SECRET_KEY in backend/.env
[ ] Run everything: python run.py
[ ] Open browser: http://localhost:8000
```
