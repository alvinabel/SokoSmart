"""WSGI entrypoint for the AgroBasket Identity + Admin service.

Run locally:   python app.py          -> http://localhost:5001
Run w/ gunicorn: gunicorn app:app -b 0.0.0.0:$PORT
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from apps.factories import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True)