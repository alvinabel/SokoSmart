"""One-shot idempotent seeder used by ``docker compose --profile tools run seed``.

Runs every seed module in order:
  1. Mongo indexes (shared/mongo.py)
  2. backend/seed.py   -> admin, demo users, categories
  3. api/seed.py       -> demo listings

Returns non-zero on failure so CI/scripts can rely on it.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import backend.seed  # noqa: E402
import api.seed  # noqa: E402
from shared.mongo import ensure_indexes, get_db  # noqa: E402


def main() -> int:
    db = get_db()
    ensure_indexes(db)

    identity = backend.seed.run(db, demo_users=os.getenv("SEED_DEMO_USERS", "true").lower() in ("1", "true"))
    print("[backend.seed]", identity)

    market = api.seed.run(db)
    print("[api.seed]", market)

    for key, result in (("backend", identity), ("api", market)):
        if isinstance(result, dict) and result.get("reason"):
            print(f"  notice[{key}]:", result["reason"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())