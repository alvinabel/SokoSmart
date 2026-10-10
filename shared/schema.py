"""PostgreSQL schema — the single source of truth for the relational store.

The DDL is idempotent (``CREATE TABLE IF NOT EXISTS``), so :func:`ensure_schema`
is safe to call on every boot, from the test harness and from the seeders. It is
also mirrored verbatim in ``supabase/schema.sql`` for provisioning Supabase.
"""

from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name          text NOT NULL DEFAULT '',
    email         text NOT NULL UNIQUE,
    password_hash text NOT NULL DEFAULT '',
    role          text NOT NULL DEFAULT 'buyer',
    phone         text NOT NULL DEFAULT '',
    bio           text NOT NULL DEFAULT '',
    location      jsonb NOT NULL DEFAULT '{}'::jsonb,
    status        text NOT NULL DEFAULT 'active',
    verified      boolean NOT NULL DEFAULT false,
    rating        jsonb NOT NULL DEFAULT '{"avg": 0, "count": 0}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    jti         text PRIMARY KEY,
    user_id     text NOT NULL,
    revoked     boolean NOT NULL DEFAULT false,
    created_at  timestamptz NOT NULL DEFAULT now(),
    revoked_at  timestamptz
);

CREATE TABLE IF NOT EXISTS categories (
    slug        text PRIMARY KEY,
    name        text NOT NULL,
    emoji       text NOT NULL DEFAULT '🥬',
    color       text NOT NULL DEFAULT '#4CAF50',
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz
);

CREATE TABLE IF NOT EXISTS listings (
    id            text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title         text NOT NULL,
    description   text NOT NULL DEFAULT '',
    category      text NOT NULL,
    price         double precision NOT NULL DEFAULT 0,
    unit          text NOT NULL DEFAULT 'unit',
    quantity      double precision NOT NULL DEFAULT 0,
    quality       text,
    location      jsonb NOT NULL DEFAULT '{}'::jsonb,
    images        jsonb NOT NULL DEFAULT '[]'::jsonb,
    seller_id     text NOT NULL,
    status        text NOT NULL DEFAULT 'active',
    views         integer NOT NULL DEFAULT 0,
    sold_price    double precision,
    moderated_at  timestamptz,
    moderated_by  text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz
);

CREATE TABLE IF NOT EXISTS orders (
    id          text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    listing_id  text NOT NULL,
    buyer_id    text NOT NULL,
    seller_id   text NOT NULL,
    quantity    double precision NOT NULL DEFAULT 1,
    unit_price  double precision NOT NULL DEFAULT 0,
    total       double precision NOT NULL DEFAULT 0,
    note        text NOT NULL DEFAULT '',
    status      text NOT NULL DEFAULT 'placed',
    history     jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz
);

CREATE TABLE IF NOT EXISTS bids (
    id          text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    listing_id  text NOT NULL,
    bidder_id   text NOT NULL,
    amount      double precision NOT NULL DEFAULT 0,
    status      text NOT NULL DEFAULT 'pending',
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz,
    accepted_at timestamptz
);

CREATE TABLE IF NOT EXISTS reviews (
    id          text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    listing_id  text NOT NULL,
    author_id   text NOT NULL,
    seller_id   text NOT NULL,
    rating      integer NOT NULL DEFAULT 0,
    comment     text NOT NULL DEFAULT '',
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (listing_id, author_id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id          text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id     text NOT NULL,
    listing_id  text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, listing_id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id            text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    recipient_id  text NOT NULL,
    type          text NOT NULL DEFAULT 'system',
    read          boolean NOT NULL DEFAULT false,
    data          jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id            text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    conversation  text NOT NULL,
    sender_id     text NOT NULL,
    recipient_id  text NOT NULL,
    body          text NOT NULL DEFAULT '',
    listing_id    text,
    read          boolean NOT NULL DEFAULT false,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id           text PRIMARY KEY DEFAULT gen_random_uuid()::text,
    actor        text,
    actor_email  text,
    action       text NOT NULL,
    target       jsonb NOT NULL DEFAULT '{}'::jsonb,
    meta         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_listings_category ON listings (category);
CREATE INDEX IF NOT EXISTS idx_listings_seller ON listings (seller_id);
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings (status);
CREATE INDEX IF NOT EXISTS idx_listings_price ON listings (price);
CREATE INDEX IF NOT EXISTS idx_listings_created ON listings (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_buyer ON orders (buyer_id);
CREATE INDEX IF NOT EXISTS idx_orders_seller ON orders (seller_id);
CREATE INDEX IF NOT EXISTS idx_orders_listing ON orders (listing_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_bids_listing ON bids (listing_id);
CREATE INDEX IF NOT EXISTS idx_bids_bidder ON bids (bidder_id);
CREATE INDEX IF NOT EXISTS idx_reviews_listing ON reviews (listing_id);
CREATE INDEX IF NOT EXISTS idx_reviews_seller ON reviews (seller_id);
CREATE INDEX IF NOT EXISTS idx_favorites_listing ON favorites (listing_id);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications (recipient_id, read);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs (created_at DESC);
"""

# Order matters for TRUNCATE ... CASCADE, but CASCADE handles dependencies anyway.
TABLES = (
    "audit_logs",
    "messages",
    "notifications",
    "favorites",
    "reviews",
    "bids",
    "orders",
    "listings",
    "categories",
    "refresh_tokens",
    "users",
)


def ensure_schema(conn) -> None:
    """Create tables/indexes if they do not exist yet (idempotent)."""
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)


def truncate_all(conn) -> None:
    """Empty every table — used by the test suite between cases."""
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
