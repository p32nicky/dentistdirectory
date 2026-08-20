"""Vercel serverless entrypoint. Vercel's @vercel/python runtime detects the
WSGI callable named `app` and serves it. All routes are rewritten here via
vercel.json."""
import sys
from pathlib import Path

# repo root on path so `import web.app` works inside the function bundle
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.app import app  # noqa: E402,F401  (Vercel serves this WSGI app)
