"""AgroBasket identity + admin service package.

The Flask app factory lives in ``backend.apps.factories.create_app``; keep this
marker import-free so importing ``backend`` (e.g. ``import backend.seed``) has no
side effects such as eagerly constructing the database client.
"""