"""ASGI entrypoint for the AgroBasket marketplace service.

Run locally:   uvicorn main:app --reload --port 8000
Run directly:  python main.py
Docs:          http://localhost:8000/docs
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.api import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    import uvicorn

    reload = os.getenv("RELOAD", "0") == "1"
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=reload)