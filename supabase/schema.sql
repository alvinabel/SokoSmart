-- ============================================================================
-- AgroBasket — Supabase schema (managed Postgres)
-- ============================================================================
-- Run in the Supabase SQL editor (or `supabase db push`).
--
-- Design notes
--   * This project keeps its own Python services (Flask identity + FastAPI
--     marketplace) and talks to Postgres directly with psycopg3. Supabase is used
--     as a managed Postgres, NOT as an auth provider: credentials live in
--     `users.password_hash` and sessions are tracked in `refresh_tokens`, exactly
--     as defined in `shared/schema.py`.
--   * The DDL below is the authoritative schema (kept in sync with
--     `shared/schema.py`). Ids are `text` UUID strings (`gen_random_uuid()::text`)
--     because the services treat ids as opaque strings.
--   * Row Level Security is intentionally NOT used here: the app connects with a
--     single server-side role and enforces authorization in the services
--     (see `shared/roles.py`). The public read paths are already unauthenticated.
--   * `storage.buckets` provisioning for listing images is kept for convenience.
-- ============================================================================

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- users + sessions
-- ---------------------------------------------------------------------------
create table if not exists public.users (
    id            text primary key default gen_random_uuid()::text,
    name          text not null default '',
    email         text not null unique,
    password_hash text not null default '',
    role          text not null default 'buyer',
    phone         text not null default '',
    bio           text not null default '',
    location      jsonb not null default '{}'::jsonb,
    status        text not null default 'active',
    verified      boolean not null default false,
    rating        jsonb not null default '{"avg": 0, "count": 0}'::jsonb,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz
);

create table if not exists public.refresh_tokens (
    jti        text primary key,
    user_id    text not null,
    revoked    boolean not null default false,
    created_at timestamptz not null default now(),
    revoked_at timestamptz
);

-- ---------------------------------------------------------------------------
-- categories
-- ---------------------------------------------------------------------------
create table if not exists public.categories (
    slug       text primary key,
    name       text not null,
    emoji      text not null default '🥬',
    color      text not null default '#4CAF50',
    created_at timestamptz not null default now(),
    updated_at timestamptz
);

-- Idempotent seed — matches shared/categories.py exactly.
insert into public.categories (slug, name, emoji, color) values
  ('vegetables', 'Vegetables',        '🥦', '#4CAF50'),
  ('fruits',     'Fruits',            '🍉', '#F4435E'),
  ('grains',     'Grains & Cereals',  '🌾', '#216E39'),
  ('livestock',  'Livestock',         '🐄', '#FF758F'),
  ('poultry',    'Poultry',           '🐔', '#F4435E'),
  ('dairy',      'Dairy',             '🥛', '#4CAF50'),
  ('fisheries',  'Fisheries',         '🐟', '#216E39'),
  ('herbs',      'Herbs & Spices',    '🌿', '#4CAF50'),
  ('seeds',      'Seeds & Seedlings', '🌱', '#216E39'),
  ('processed',  'Processed Goods',   '🧺', '#FF758F')
on conflict (slug) do update
  set name = excluded.name, emoji = excluded.emoji, color = excluded.color;

-- ---------------------------------------------------------------------------
-- listings
-- ---------------------------------------------------------------------------
create table if not exists public.listings (
    id           text primary key default gen_random_uuid()::text,
    title        text not null,
    description  text not null default '',
    category     text not null,
    price        double precision not null default 0,
    unit         text not null default 'unit',
    quantity     double precision not null default 0,
    quality      text,
    location     jsonb not null default '{}'::jsonb,
    images       jsonb not null default '[]'::jsonb,
    seller_id    text not null,
    status       text not null default 'active',
    views        integer not null default 0,
    sold_price   double precision,
    moderated_at timestamptz,
    moderated_by text,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz
);

-- ---------------------------------------------------------------------------
-- orders
-- ---------------------------------------------------------------------------
create table if not exists public.orders (
    id         text primary key default gen_random_uuid()::text,
    listing_id text not null,
    buyer_id   text not null,
    seller_id  text not null,
    quantity   double precision not null default 1,
    unit_price double precision not null default 0,
    total      double precision not null default 0,
    note       text not null default '',
    status     text not null default 'placed',
    history    jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz
);

-- ---------------------------------------------------------------------------
-- bids
-- ---------------------------------------------------------------------------
create table if not exists public.bids (
    id          text primary key default gen_random_uuid()::text,
    listing_id  text not null,
    bidder_id   text not null,
    amount      double precision not null default 0,
    status      text not null default 'pending',
    created_at  timestamptz not null default now(),
    updated_at  timestamptz,
    accepted_at timestamptz
);

-- ---------------------------------------------------------------------------
-- reviews
-- ---------------------------------------------------------------------------
create table if not exists public.reviews (
    id         text primary key default gen_random_uuid()::text,
    listing_id text not null,
    author_id  text not null,
    seller_id  text not null,
    rating     integer not null default 0,
    comment    text not null default '',
    created_at timestamptz not null default now(),
    unique (listing_id, author_id)
);

-- ---------------------------------------------------------------------------
-- favorites
-- ---------------------------------------------------------------------------
create table if not exists public.favorites (
    id         text primary key default gen_random_uuid()::text,
    user_id    text not null,
    listing_id text not null,
    created_at timestamptz not null default now(),
    unique (user_id, listing_id)
);

-- ---------------------------------------------------------------------------
-- notifications
-- ---------------------------------------------------------------------------
create table if not exists public.notifications (
    id           text primary key default gen_random_uuid()::text,
    recipient_id text not null,
    type         text not null default 'system',
    read         boolean not null default false,
    data         jsonb not null default '{}'::jsonb,
    created_at   timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- messages  (1:1 chat keyed by the deterministic conversation id)
-- ---------------------------------------------------------------------------
create table if not exists public.messages (
    id           text primary key default gen_random_uuid()::text,
    conversation text not null,
    sender_id    text not null,
    recipient_id text not null,
    body         text not null default '',
    listing_id   text,
    read         boolean not null default false,
    created_at   timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- audit_logs  (admin trail)
-- ---------------------------------------------------------------------------
create table if not exists public.audit_logs (
    id          text primary key default gen_random_uuid()::text,
    actor       text,
    actor_email text,
    action      text not null,
    target      jsonb not null default '{}'::jsonb,
    meta        jsonb not null default '{}'::jsonb,
    created_at  timestamptz not null default now()
);

-- Indexes --------------------------------------------------------------------
create index if not exists idx_users_role on public.users (role);
create index if not exists idx_refresh_tokens_user on public.refresh_tokens (user_id);
create index if not exists idx_listings_category on public.listings (category);
create index if not exists idx_listings_seller on public.listings (seller_id);
create index if not exists idx_listings_status on public.listings (status);
create index if not exists idx_listings_price on public.listings (price);
create index if not exists idx_listings_created on public.listings (created_at desc);
create index if not exists idx_orders_buyer on public.orders (buyer_id);
create index if not exists idx_orders_seller on public.orders (seller_id);
create index if not exists idx_orders_listing on public.orders (listing_id);
create index if not exists idx_orders_status on public.orders (status);
create index if not exists idx_bids_listing on public.bids (listing_id);
create index if not exists idx_bids_bidder on public.bids (bidder_id);
create index if not exists idx_reviews_listing on public.reviews (listing_id);
create index if not exists idx_reviews_seller on public.reviews (seller_id);
create index if not exists idx_favorites_listing on public.favorites (listing_id);
create index if not exists idx_notifications_recipient on public.notifications (recipient_id, read);
create index if not exists idx_messages_conversation on public.messages (conversation, created_at);
create index if not exists idx_audit_logs_created on public.audit_logs (created_at desc);

-- ============================================================================
-- Realtime (chat) + grants + storage
-- ============================================================================
do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    alter publication supabase_realtime add table public.messages;
  end if;
end $$;

do $$
begin
  if exists (select 1 from pg_roles where rolname = 'authenticated') then
    grant usage on schema public to anon, authenticated, service_role;
    grant all on all tables in schema public to anon, authenticated, service_role;
    grant all on all sequences in schema public to anon, authenticated, service_role;
    grant all on all functions in schema public to anon, authenticated, service_role;
  end if;
end $$;

-- Public `listings` image bucket (5 MB max per file, images only).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('listings', 'listings', true, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set public = true;
