"""Vercel serverless entry — re-exports the FastAPI app from backend/."""
import os
import sys

_backend = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if _backend not in sys.path:
    sys.path.insert(0, _backend)

from main import app  # noqa: E402
