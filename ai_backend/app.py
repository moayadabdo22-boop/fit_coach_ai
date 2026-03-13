from __future__ import annotations

"""
Week-3 backend entrypoint.

This file exposes the FastAPI app required in the deliverables.
All route definitions live in main.py and are imported here.
"""

from main import app

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8010, reload=False)
