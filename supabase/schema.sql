-- ============================================================================
-- AgroBasket — Supabase schema (managed Postgres)
-- ============================================================================
-- Run in the Supabase SQL editor (or `supabase db push`). Requires the hosted
-- Supabase project: `auth` (GoTrue), `storage` and `supabase_realtime` must exist.
--
-- Design notes
--   * Supabase Auth is the SINGLE identity source. There is NO password_hash and
--     NO refresh_tokens table here — GoTrue owns credentials + refresh/session
--     management. This supersedes the Flask JWT layer (shared/jwt_token.py).
--   * `profiles` is keyed 1:1 to auth.users(id). A trigger provisions the row on
--     signup and mirrors `role` into raw_app_meta_data so the role rides inside
--     the JWT and is usable in RLS via auth.jwt().
--   * Column/constraint shapes mirror api/app/services/* and shared/mongo.py so a
--     PostgREST/Edge-Function backend can consume data without a migration.
--   * Everything is protected by Row Level Security using auth.uid() + role.
-- ============================================================================

-- Extensions ------------------------------------------------------------------
create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- Helpers
-- ---------------------------------------------------------------------------

-- Keep `updated_at` fresh on every row update.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

-- Current user's role. Falls back to 'buyer' when the claim is absent so anon
-- users are treated as the weakest role (RLS still blocks them via uid checks).
create or replace function public.current_role()
returns text
language sql
stable
security invoker
as $$
  select coalesce(auth.jwt() -> 'app_metadata' ->> 'role', 'buyer');
$$;

create or replace function public.is_staff()
returns boolean
language sql
stable
security invoker
as $$
  select public.current_role() in ('moderator', 'admin');
$$;

create or replace function public.is_admin()
returns boolean
language sql
stable
security invoker
as $$
  select public.current_role() = 'admin';
$$;

-- Provision a profile on signup and mirror the chosen role into app_metadata
-- (so it lands in the access token). Name/role/farm_name come from the signUp
-- `options.data` payload (raw_user_meta_data).
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  meta      jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
  role_text text  := lower(coalesce(meta ->> 'role', 'buyer'));
  name_text text  := coalesce(meta ->> 'name', split_part(coalesce(new.email, ''), '@', 1));
begin
  if role_text not in ('buyer', 'seller', 'moderator', 'admin') then
    role_text := 'buyer';
  end if;

  insert into public.profiles (id, name, farm_name, role)
  values (new.id, name_text, meta ->> 'farm_name', role_text)
  on conflict (id) do nothing;

  update auth.users
     set raw_app_meta_data =
           coalesce(raw_app_meta_data, '{}'::jsonb) || jsonb_build_object('role', role_text)
   where id = new.id;

  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Keep app_metadata in sync whenever an admin changes a profile role.
create or replace function public.sync_profile_role_metadata()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update auth.users
     set raw_app_meta_data =
           coalesce(raw_app_meta_data, '{}'::jsonb) || jsonb_build_object('role', new.role)
   where id = new.id;
  return new;
end;
$$;

create trigger on_profile_role_changed
  after insert or update of role on public.profiles
  for each row execute function public.sync_profile_role_metadata();

-- ---------------------------------------------------------------------------
-- profiles  (identity lives in auth.users)
-- ---------------------------------------------------------------------------
create table public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  name         text not null default '',
  farm_name    text,
  phone        text,
  bio          text not null default '',
  role         text not null default 'buyer'
                 check (role in ('buyer', 'seller', 'moderator', 'admin')),
  status       text not null default 'active'
                 check (status in ('active', 'suspended')),
  location     jsonb not null default '{}'::jsonb,          -- mirrors {city: …}
  city         text generated always as (nullif(location ->> 'city', '')) stored,
  rating_avg   numeric(3,2) not null default 0,
  rating_count integer not null default 0,
  verified     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create index profiles_role_idx on public.profiles (role);
create index profiles_status_idx on public.profiles (status);
create index profiles_city_idx on public.profiles (city);

create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- categories
-- ---------------------------------------------------------------------------
create table public.categories (
  slug       text primary key check (slug ~ '^[a-z0-9-]+$'),
  name       text not null,
  emoji      text not null default '🥬',
  color      text not null default '#4CAF50',               -- watermelon palette
  created_at timestamptz not null default now()
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
create table public.listings (
  id              uuid primary key default gen_random_uuid(),
  seller_id       uuid not null references public.profiles(id) on delete cascade,
  title           text not null check (char_length(title) between 3 and 120),
  description     text not null default '' check (char_length(description) <= 5000),
  category        text not null references public.categories(slug),
  price           numeric(12,2) not null check (price > 0),
  unit            text not null default 'unit' check (char_length(unit) <= 20),
  quantity        numeric(12,2) not null check (quantity > 0 and quantity <= 1000000),
  quality         text check (char_length(quality) <= 120),
  location        jsonb not null default '{}'::jsonb,
  city            text generated always as (nullif(location ->> 'city', '')) stored,
  images          text[] not null default '{}',           -- public storage URLs
  status          text not null default 'active'
                    check (status in ('active', 'sold', 'rejected', 'suspended', 'deleted')),
  views           integer not null default 0,
  reported        boolean not null default false,
  reported_reason text,
  reported_by     uuid references public.profiles(id) on delete set null,
  sold_price      numeric(12,2),
  moderated_at    timestamptz,
  moderated_by    text,                                   -- staff id (string, as stored in code)
  search          tsvector generated always as
                    (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))) stored,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index listings_search_idx        on public.listings using gin (search);
create index listings_category_idx      on public.listings (category);
create index listings_seller_id_idx     on public.listings (seller_id);
create index listings_status_idx        on public.listings (status);
create index listings_price_idx         on public.listings (price);
create index listings_city_idx          on public.listings (city);
create index listings_created_at_idx    on public.listings (created_at desc);
create index listings_reported_idx      on public.listings (reported) where reported;

create trigger listings_set_updated_at
  before update on public.listings
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- orders
-- ---------------------------------------------------------------------------
create table public.orders (
  id         uuid primary key default gen_random_uuid(),
  listing_id uuid not null references public.listings(id) on delete cascade,
  buyer_id   uuid not null references public.profiles(id) on delete cascade,
  seller_id  uuid not null references public.profiles(id) on delete cascade,
  quantity   numeric(12,2) not null check (quantity > 0),
  unit_price numeric(12,2) not null check (unit_price >= 0),
  total      numeric(14,2) not null check (total >= 0),
  note       text not null default '',
  status     text not null default 'placed'
               check (status in ('placed', 'accepted', 'fulfilled', 'completed', 'rejected', 'cancelled')),
  history    jsonb not null default '[]'::jsonb,          -- [{status, at, by}]
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index orders_buyer_id_idx  on public.orders (buyer_id);
create index orders_seller_id_idx on public.orders (seller_id);
create index orders_listing_id_idx on public.orders (listing_id);
create index orders_status_idx    on public.orders (status);

create trigger orders_set_updated_at
  before update on public.orders
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- bids
-- ---------------------------------------------------------------------------
create table public.bids (
  id          uuid primary key default gen_random_uuid(),
  listing_id  uuid not null references public.listings(id) on delete cascade,
  bidder_id   uuid not null references public.profiles(id) on delete cascade,
  amount      numeric(12,2) not null check (amount > 0),
  status      text not null default 'pending'
                check (status in ('pending', 'accepted', 'declined')),
  accepted_at timestamptz,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index bids_listing_id_idx on public.bids (listing_id);
create index bids_bidder_id_idx  on public.bids (bidder_id);
create index bids_status_idx     on public.bids (status);

create trigger bids_set_updated_at
  before update on public.bids
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- reviews
-- ---------------------------------------------------------------------------
create table public.reviews (
  id         uuid primary key default gen_random_uuid(),
  listing_id uuid not null references public.listings(id) on delete cascade,
  author_id  uuid not null references public.profiles(id) on delete cascade,
  seller_id  uuid not null references public.profiles(id) on delete cascade,
  rating     integer not null check (rating between 1 and 5),
  comment    text not null default '' check (char_length(comment) <= 1000),
  created_at timestamptz not null default now(),
  unique (listing_id, author_id)                          -- one review per listing
);

create index reviews_listing_id_idx on public.reviews (listing_id);
create index reviews_seller_id_idx  on public.reviews (seller_id);

-- Keep aggregated seller rating fresh (mirrors reviews._recompute_seller_rating).
create or replace function public.recompute_seller_rating()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.profiles p
     set rating_avg = agg.avg_rating,
         rating_count = agg.cnt
    from (select r.seller_id,
                 round(avg(r.rating), 2) as avg_rating,
                 count(*)                 as cnt
            from public.reviews r
           where r.seller_id = coalesce(new.seller_id, old.seller_id)
           group by r.seller_id) agg
   where p.id = agg.seller_id;

  update public.profiles p
     set rating_avg = 0, rating_count = 0
   where p.id = coalesce(new.seller_id, old.seller_id)
     and not exists (select 1 from public.reviews r where r.seller_id = p.id);

  return null;
end;
$$;

create trigger reviews_recompute_rating
  after insert or update of rating or delete on public.reviews
  for each row execute function public.recompute_seller_rating();

-- ---------------------------------------------------------------------------
-- favorites
-- ---------------------------------------------------------------------------
create table public.favorites (
  user_id    uuid not null references public.profiles(id) on delete cascade,
  listing_id uuid not null references public.listings(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, listing_id)
);

create index favorites_listing_id_idx on public.favorites (listing_id);

-- ---------------------------------------------------------------------------
-- notifications
-- ---------------------------------------------------------------------------
create table public.notifications (
  id           uuid primary key default gen_random_uuid(),
  recipient_id uuid not null references public.profiles(id) on delete cascade,
  type         text not null check (type in (
                 'order.new', 'order.accepted', 'order.rejected', 'order.fulfilled',
                 'order.completed', 'order.cancelled', 'bid.new', 'bid.accepted',
                 'bid.declined', 'message.new', 'review.new', 'listing.moderated',
                 'system'
               )),
  read         boolean not null default false,
  data         jsonb not null default '{}'::jsonb,
  created_at   timestamptz not null default now()
);

create index notifications_recipient_read_idx on public.notifications (recipient_id, read);
create index notifications_created_at_idx     on public.notifications (created_at desc);

create trigger notifications_set_updated_at
  before update on public.notifications
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- messages  (1:1 chat keyed by the deterministic conversation id)
-- ---------------------------------------------------------------------------
create table public.messages (
  id           uuid primary key default gen_random_uuid(),
  conversation text not null,                             -- sorted "a:b" key
  sender_id    uuid not null references public.profiles(id) on delete cascade,
  recipient_id uuid not null references public.profiles(id) on delete cascade,
  body         text not null check (char_length(body) between 1 and 2000),
  listing_id   uuid references public.listings(id) on delete set null,
  read         boolean not null default false,
  created_at   timestamptz not null default now()
);

create index messages_conversation_created_idx on public.messages (conversation, created_at);
create index messages_sender_id_idx            on public.messages (sender_id);
create index messages_recipient_id_idx         on public.messages (recipient_id);

-- ---------------------------------------------------------------------------
-- audit_logs  (admin trail; written by Edge Functions via service role)
-- ---------------------------------------------------------------------------
create table public.audit_logs (
  id          uuid primary key default gen_random_uuid(),
  actor_id    text,                                       -- string uid or null
  actor_email text,
  action      text not null,
  target      jsonb not null default '{}'::jsonb,
  meta        jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now()
);

create index audit_logs_created_at_idx on public.audit_logs (created_at desc);

-- ============================================================================
-- Row Level Security
-- ============================================================================
alter table public.profiles      enable row level security;
alter table public.categories    enable row level security;
alter table public.listings      enable row level security;
alter table public.orders        enable row level security;
alter table public.bids          enable row level security;
alter table public.reviews       enable row level security;
alter table public.favorites     enable row level security;
alter table public.notifications enable row level security;
alter table public.messages      enable row level security;
alter table public.audit_logs    enable row level security;

-- profiles: publicly readable storefront identity; edits limited to the owner
create policy "profiles are public"
  on public.profiles for select using (true);

create policy "users insert own profile"
  on public.profiles for insert with check (auth.uid() = id);

create policy "users update own profile"
  on public.profiles for update
  using (auth.uid() = id) with check (auth.uid() = id or public.is_staff());

create policy "staff manage profiles"
  on public.profiles for all using (public.is_staff());

-- categories: public read, staff-managed
create policy "categories are public"
  on public.categories for select using (true);

create policy "staff manage categories"
  on public.categories for all using (public.is_staff());

-- listings: public read of active; owner/staff read & write everything
create policy "public reads active listings"
  on public.listings for select using (status = 'active');

create policy "owners and staff read all listings"
  on public.listings for select using (auth.uid() = seller_id or public.is_staff());

create policy "users create own listings"
  on public.listings for insert with check (auth.uid() = seller_id);

create policy "owners and staff update listings"
  on public.listings for update
  using (auth.uid() = seller_id or public.is_staff())
  with check (auth.uid() = seller_id or public.is_staff());

create policy "owners and staff delete listings"
  on public.listings for delete using (auth.uid() = seller_id or public.is_staff());

-- orders: only the two parties (or staff), buyer books the order
create policy "participants read orders"
  on public.orders for select using (auth.uid() in (buyer_id, seller_id) or public.is_staff());

create policy "buyers create orders"
  on public.orders for insert with check (auth.uid() = buyer_id);

create policy "participants update orders"
  on public.orders for update
  using (auth.uid() in (buyer_id, seller_id) or public.is_staff())
  with check (auth.uid() in (buyer_id, seller_id) or public.is_staff());

create policy "staff delete orders"
  on public.orders for delete using (public.is_staff());

-- bids: bidder + listing owner + staff
create policy "bids visible to bidder, owner and staff"
  on public.bids for select using (
    auth.uid() = bidder_id
    or public.is_staff()
    or exists (select 1 from public.listings l where l.id = bids.listing_id and l.seller_id = auth.uid())
  );

create policy "bidders place bids"
  on public.bids for insert with check (auth.uid() = bidder_id);

create policy "bids updated by bidder or listing owner"
  on public.bids for update using (
    auth.uid() = bidder_id
    or public.is_staff()
    or exists (select 1 from public.listings l where l.id = bids.listing_id and l.seller_id = auth.uid())
  );

create policy "staff delete bids"
  on public.bids for delete using (public.is_staff());

-- reviews: public (storefront trust signals); author/maintainer writes
create policy "reviews are public"
  on public.reviews for select using (true);

create policy "authors create reviews"
  on public.reviews for insert with check (auth.uid() = author_id);

create policy "authors edit own reviews"
  on public.reviews for update
  using (auth.uid() = author_id or public.is_admin())
  with check (auth.uid() = author_id or public.is_admin());

create policy "authors and admins delete reviews"
  on public.reviews for delete using (auth.uid() = author_id or public.is_admin());

-- favorites: strictly personal
create policy "users manage own favorites"
  on public.favorites for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- notifications: recipient-only read/update; server-generated inserts via service role
create policy "recipients read notifications"
  on public.notifications for select using (auth.uid() = recipient_id or public.is_staff());

create policy "recipients update own notifications"
  on public.notifications for update
  using (auth.uid() = recipient_id or public.is_staff())
  with check (auth.uid() = recipient_id or public.is_staff());

create policy "recipients delete own notifications"
  on public.notifications for delete using (auth.uid() = recipient_id or public.is_staff());

-- messages: conversation participants only (Realtime pushes to the same set)
create policy "participants read conversations"
  on public.messages for select using (auth.uid() in (sender_id, recipient_id) or public.is_staff());

create policy "users send messages"
  on public.messages for insert with check (auth.uid() = sender_id);

create policy "participants mark messages read"
  on public.messages for update
  using (auth.uid() in (sender_id, recipient_id) or public.is_staff())
  with check (auth.uid() in (sender_id, recipient_id) or public.is_staff());

create policy "staff delete messages"
  on public.messages for delete using (public.is_staff());

-- audit trail: staff only (writes happen with the service role)
create policy "staff access audit logs"
  on public.audit_logs for all using (public.is_staff());

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

-- Public `listings` image bucket (5 MB max per file, images only). Uploads must
-- be namespaced under their own uid folder: <uid>/<image>.webp
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('listings', 'listings', true, 5242880, array['image/jpeg', 'image/png', 'image/webp'])
on conflict (id) do update set public = true;

create policy "public read listings images"
  on storage.objects for select using (bucket_id = 'listings');

create policy "authenticated upload own listings images"
  on storage.objects for insert with check (
    bucket_id = 'listings' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "authenticated update own listings images"
  on storage.objects for update using (
    bucket_id = 'listings' and (storage.foldername(name))[1] = auth.uid()::text
  ) with check (
    bucket_id = 'listings' and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "owners delete own listings images"
  on storage.objects for delete using (
    bucket_id = 'listings' and (storage.foldername(name))[1] = auth.uid()::text
  );