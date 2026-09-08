"""Build the Next.js frontend so the Django backend can serve it.

Run from anywhere:

    python backend/scripts/build_frontend.py

The script:
  1. Installs node dependencies (idempotent — only when needed).
  2. Runs `next build`, producing `frontend/out/`.

The Django URL conf reads from `frontend/out/` at request time, so no
copy step is required.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _npm() -> str:
    """Resolve the npm executable, accounting for `npm.cmd` on Windows."""
    candidate = shutil.which("npm")
    if candidate:
        return candidate
    if os.name == "nt":
        for name in ("npm.cmd", "npm.exe"):
            found = shutil.which(name)
            if found:
                return found
    raise SystemExit(
        "npm was not found on PATH. Install Node.js (https://nodejs.org) "
        "before building the frontend."
    )


def _run(cmd: list[str], *, cwd: Path) -> None:
    print(f"\n$ {' '.join(cmd)}   (cwd={cwd})", flush=True)
    result = subprocess.run(cmd, cwd=cwd, check=False, shell=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _node_modules_fresh() -> bool:
    """Return True if `node_modules/` is newer than `package-lock.json`."""
    node_modules = FRONTEND_DIR / "node_modules"
    lockfile = FRONTEND_DIR / "package-lock.json"
    if not node_modules.exists():
        return False
    if not lockfile.exists():
        return True
    try:
        return node_modules.stat().st_mtime >= lockfile.stat().st_mtime
    except OSError:
        return False


def main() -> int:
    if not FRONTEND_DIR.exists():
        raise SystemExit(f"Frontend directory not found: {FRONTEND_DIR}")

    npm = _npm()

    if not _node_modules_fresh():
        print("Installing frontend dependencies…", flush=True)
        # `npm ci` is reproducible but requires package-lock.json; fall
        # back to `npm install` if the lockfile is missing.
        install_cmd = (
            [npm, "ci"]
            if (FRONTEND_DIR / "package-lock.json").exists()
            else [npm, "install"]
        )
        _run(install_cmd, cwd=FRONTEND_DIR)
    else:
        print("Frontend dependencies already up to date — skipping install.")

    print("\nBuilding Next.js static export…", flush=True)
    _run([npm, "run", "build"], cwd=FRONTEND_DIR)

    out_dir = FRONTEND_DIR / "out"
    if not out_dir.exists():
        raise SystemExit(
            f"Build completed but {out_dir} is missing. Check next.config.mjs "
            "still has `output: 'export'`."
        )

    print(f"\nFrontend build ready at {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
