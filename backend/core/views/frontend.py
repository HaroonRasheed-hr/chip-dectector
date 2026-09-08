"""Serve the Next.js static export from inside the Django process.

The Next.js build is configured with `output: "export"` and
`trailingSlash: true`, producing a directory layout like:

    frontend/out/
        index.html
        login/index.html
        register/index.html
        detection/index.html
        _next/static/...
        favicon.ico

This module exposes a single catch-all view that resolves any non-API
URL to a file inside that directory, so a user hitting
`http://localhost:8000/login` lands on the static `login/index.html`
served directly by Django — no separate Node.js server required.
"""

from __future__ import annotations

import mimetypes
import posixpath
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe


# Hashed Next.js chunks live under `_next/static/` and are content-addressed,
# so they are safe to cache aggressively in browsers and intermediaries.
_IMMUTABLE_PREFIX = "_next/static/"
_IMMUTABLE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


def _resolve_safe(root: Path, relative: str) -> Path | None:
    """Resolve `relative` against `root`, rejecting any escape attempts."""
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _build_root() -> Path:
    root = Path(settings.FRONTEND_BUILD_DIR)
    if not root.exists():
        raise Http404(
            "Frontend build not found. Run `npm --prefix frontend run build` "
            "or `python backend/scripts/build_frontend.py` before starting "
            "the server."
        )
    return root


def _file_response(path: Path, *, status: int = 200) -> HttpResponse:
    content_type, _ = mimetypes.guess_type(str(path))
    response = FileResponse(
        path.open("rb"),
        content_type=content_type or "application/octet-stream",
    )
    response.status_code = status
    return response


def _serve_404(root: Path) -> HttpResponse:
    not_found = root / "404.html"
    if not_found.exists():
        response = _file_response(not_found, status=404)
        response["Cache-Control"] = "no-cache"
        return response
    return HttpResponse("Not Found", status=404, content_type="text/plain")


@require_safe
def serve_frontend(request, path: str = "") -> HttpResponse:
    """Resolve a URL path to a file inside the Next.js export."""
    root = _build_root()

    # Normalise — strip a leading slash and collapse `..` segments.
    clean = posixpath.normpath("/" + path).lstrip("/")
    if clean == ".":
        clean = ""

    # Try a direct file hit first (e.g. `_next/static/chunks/foo.js`,
    # `favicon.ico`, or an image under `/images/`).
    if clean:
        direct = _resolve_safe(root, clean)
        if direct is not None and direct.is_file():
            response = _file_response(direct)
            if clean.startswith(_IMMUTABLE_PREFIX):
                response["Cache-Control"] = (
                    f"public, max-age={_IMMUTABLE_MAX_AGE}, immutable"
                )
            return response

    # Fall back to an HTML route: `<path>/index.html` for client-side
    # routes built by Next.js (e.g. `/login` → `login/index.html`).
    html_candidate = _resolve_safe(root, posixpath.join(clean, "index.html"))
    if html_candidate is not None and html_candidate.is_file():
        response = _file_response(html_candidate)
        # HTML shells must never be cached — they reference hashed chunks
        # that change on every deploy.
        response["Cache-Control"] = "no-cache"
        return response

    return _serve_404(root)


@cache_control(no_cache=True)
def serve_index(request) -> HttpResponse:
    """Convenience entry-point for the root URL."""
    return serve_frontend(request, path="")
