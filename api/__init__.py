"""AgroBasket marketplace API package.

The FastAPI app factory lives in ``api.app.api.create_app``; keep this marker
import-free so importing ``api`` (e.g. ``import api.seed``) has no side effects
such as eagerly constructing the database client.
"""