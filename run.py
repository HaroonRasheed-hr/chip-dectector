"""Single entry-point that builds the frontend and starts the backend.

Usage:

    python run.py                  # build frontend + serve on :8000
    python run.py --no-build       # reuse existing frontend/out/
    python run.py --port 9000      # override port
    python run.py --host 0.0.0.0   # bind on all interfaces
    python run.py --prod           # production settings + gunicorn

After boot, the entire app is reachable at http://<host>:<port>/:
the Next.js UI on `/` and `/login/`, `/register/`, `/detection/`,
and the JSON API under `/api/`.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_BUILD = PROJECT_ROOT / "frontend" / "out"


def _run(cmd: list[str], *, env: dict[str, str] | None = None,
         cwd: Path | None = None) -> None:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=cwd, env=env, check=False, shell=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _python() -> str:
    return sys.executable or "python"


def _build_frontend() -> None:
    _run([_python(), str(BACKEND_DIR / "scripts" / "build_frontend.py")])


def _manage(args: list[str], env: dict[str, str]) -> None:
    _run([_python(), "manage.py", *args], env=env, cwd=BACKEND_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default="8000")
    parser.add_argument("--no-build", action="store_true",
                        help="Skip rebuilding the Next.js frontend.")
    parser.add_argument("--no-migrate", action="store_true",
                        help="Skip `manage.py migrate`.")
    parser.add_argument("--no-collectstatic", action="store_true",
                        help="Skip `manage.py collectstatic`.")
    parser.add_argument(
        "--prod",
        action="store_true",
        help=(
            "Run with config.settings.production via gunicorn. Requires "
            "HTTPS-terminating reverse proxy (production settings enforce "
            "SSL redirects). For a local prod-like check on plain HTTP, "
            "omit this flag — the default already serves the production "
            "frontend build."
        ),
    )
    args = parser.parse_args()

    settings_module = (
        "config.settings.production" if args.prod
        else "config.settings.development"
    )
    env = os.environ.copy()
    env["DJANGO_SETTINGS_MODULE"] = settings_module

    # 1. Build (or reuse) the Next.js static export.
    if args.no_build:
        if not FRONTEND_BUILD.exists():
            raise SystemExit(
                "--no-build was passed but frontend/out/ does not exist. "
                "Run without --no-build first, or build manually."
            )
        print(f"Using existing frontend build at {FRONTEND_BUILD}")
    else:
        _build_frontend()

    # 2. Apply migrations.
    if not args.no_migrate:
        _manage(["migrate", "--noinput"], env)

    # 3. Collect Django's own static assets (admin CSS, DRF, …) into
    # STATIC_ROOT so WhiteNoise can serve them with hashed filenames.
    if not args.no_collectstatic:
        _manage(["collectstatic", "--noinput"], env)

    # 4. Serve.
    if args.prod:
        gunicorn = shutil.which("gunicorn")
        if not gunicorn:
            raise SystemExit(
                "gunicorn is not installed. Run `pip install gunicorn` or "
                "drop --prod to use the development server."
            )
        print(
            f"\nStarting gunicorn on http://{args.host}:{args.port}/  "
            f"(settings={settings_module})\n"
        )
        _run(
            [
                gunicorn,
                "config.wsgi:application",
                "--bind", f"{args.host}:{args.port}",
                "--workers", os.environ.get("GUNICORN_WORKERS", "3"),
            ],
            env=env,
            cwd=BACKEND_DIR,
        )
    else:
        print(
            f"\nStarting Django on http://{args.host}:{args.port}/  "
            f"(settings={settings_module})\n"
        )
        _manage(["runserver", f"{args.host}:{args.port}", "--insecure"], env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
