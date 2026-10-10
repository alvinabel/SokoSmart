# 06 · Deployment Guide

Verified target: **Vercel** for the frontend PWA + **Supabase** (Auth, Postgres, Storage,
Realtime, Edge Functions) for everything else. This replaces the Python APIs + MongoDB stack;
the old path is kept at the end as a **legacy appendix** (Path A).

> **Free tier:** the entire Supabase-native path runs on free plans. See §1 for the exact
> limits and the guardrails that keep you inside them.

---

## 0. Target architecture

```
        React PWA  ──▶  Vercel (static, HTTPS)
             │
             │  @supabase/supabase-js  (anon key)
             ▼
        Supabase  ──▶  Auth (GoTrue)      ← identity; issues the JWT
                  ──▶  Postgres + RLS     ← data; enforced per-user via auth.uid()
                  ──▶  Storage            ← `listings` image bucket
                  ──▶  Realtime           ← `messages` chat channels
                  ──▶  Edge Functions     ← business logic (orders/bids/reviews/notify)
```

- **Auth** is the only identity source: no password hashing, no refresh-token table. The access
  token carries `app_metadata.role`, which RLS reads via `auth.jwt()`.
- **Data** lives in Postgres. `supabase/schema.sql` defines the tables, indexes, RLS policies and
  the seed categories — mirroring the shapes the Python services used.
- **Business logic** moves to Edge Functions (Deno/TS) + PostgREST (Phase B of the migration).
- **Python (Flask/FastAPI) and MongoDB are retired** on this path.

---

## 1. Free-tier limits & guardrails

| Service | Plan | Key limits | Notes |
|---|---|---|---|
| Supabase | Free ($0) | 500 MB DB, 1 GB Storage, 50k MAU, 5 GB egress/mo, 500k Edge-Fn calls/mo, 2M Realtime msgs, **200 Realtime peak connections**, 2 projects | **Project is paused after 7 days of inactivity**; no automated backups |
| Vercel | Hobby ($0) | 100 GB transfer/mo, 1M edge requests, 1M function invocations | ⚠️ **Hobby is licensed for non-commercial / personal use only** |

**Guardrails to stay free:**

1. **Never hit the 7-day pause.** Add a tiny keep-alive. A free scheduled GitHub Actions workflow
   (`.github/workflows/keepalive.yml`) that calls a Supabase health endpoint daily is enough:
   ```yaml
   on:
     schedule: [{ cron: '0 6 * * *' }]
   jobs:
     ping:
       runs-on: ubuntu-latest
       steps:
         - run: curl -fsS "${{ secrets.SUPABASE_URL }}/auth/v1/health"
   ```
2. **Keep images in Storage, not the DB.** Store public URLs in `listings.images`; never base64
   blobs in Postgres. That keeps the DB well under 500 MB and uses the 1 GB Storage budget.
3. **Stay under 200 concurrent Realtime connections** — fine for a single `messages` channel per
   active user at MVP scale.
4. **Commercial use:** a marketplace is commercial. Vercel Hobby does **not** permit that — for a
   real launch either upgrade Vercel to Pro ($20/mo) **or** move the static build to
   **Cloudflare Pages** (free, unlimited bandwidth, commercial use allowed). Supabase's free tier
   *does* allow commercial use. `frontend/vercel.json` still works on Cloudflare only if converted
   to `_redirects`/`_headers`; the config below is for Vercel.

---

## 2. Supabase project setup

1. Create a project at [supabase.com](https://supabase.com) (free). Note the **project ref**,
   **anon key** and **service-role key** from *Settings → API*.
2. Open **SQL Editor** and run the entire `supabase/schema.sql`. It creates all tables, RLS
   policies, the `handle_new_user` trigger, the seed categories, the `listings` storage bucket and
   adds `messages` to Realtime. It is safe to re-run for the seed, but the DDL is one-time — for a
   clean re-run, reset the project or drop the objects first.
3. **Auth → Providers:** keep Email enabled. (Add Google/etc. later if desired.)
4. **Auth → URL configuration:** set *Site URL* and *Redirect URLs* to your frontend origin
   (`http://localhost:5173` for dev, `https://<app>.vercel.app` for prod).
5. **Create the demo users** in *Authentication → Users* (or via the Admin API), passing metadata
   so the `handle_new_user` trigger assigns the role:

   | Email | Password | `user_metadata` |
   |---|---|---|
   | `admin@agrobasket.test` | `Admin@12345` | `{ "name": "AgroBasket Admin", "role": "admin" }` |
   | `seller@agrobasket.test` | `Demo@12345` | `{ "name": "Demo Seller", "role": "seller", "farm_name": "Green Acres" }` |
   | `buyer@agrobasket.test` | `Demo@12345` | `{ "name": "Demo Buyer", "role": "buyer" }` |

   If a user was created without metadata, promote them afterward (the trigger syncs the role into
   the JWT on the next sign-in):
   ```sql
   update public.profiles set role = 'admin' where name = 'AgroBasket Admin';
   ```
   **Rotate the admin password** after first login.

---

## 3. Environment variables

**Root `.env` / server side** (Edge Functions, scripts):

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<anon-public-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_STORAGE_BUCKET=listings
```

**Frontend (Vercel → Settings → Environment Variables), public:**

```env
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-public-key>
```

`VITE_AUTH_API_URL` / `VITE_MARKET_API_URL` are **legacy** (used only by the Python stack below).

---

## 4. Frontend → Vercel (PWA)

1. **Build locally to confirm:** `cd frontend && npm install && npm run generate:icons && npm run build` → `dist/` (with `sw.js` + `manifest.webmanifest`).
2. Push the repo to GitHub and **Import** in Vercel → pick the repo → **Root directory: `frontend`**.
3. Settings:

   | Setting | Value |
   |---|---|
   | Framework preset | `Vite` |
   | Root directory | `frontend` |
   | Build command | `npm run build` |
   | Install command | `npm install` |
   | Output directory | `dist` |
   | Node version | `20.x` |

4. Add the frontend env vars from §3, then **Deploy**. The service worker needs HTTPS — Vercel
   provides it. `frontend/vercel.json` handles the SPA fallback rewrite and cache headers
   (`/assets/*` immutable; `index.html` + `sw.js` revalidated).
5. **Vercel CLI alternative:** `npx vercel --prod` from `frontend/` (uses the same settings once linked).

---

## 5. Edge Functions & API surface (migration target)

- **CRUD + authz** — read/write via `@supabase/supabase-js` (PostgREST) directly from the client;
  RLS enforces ownership/participants so no trusted middleware is needed for simple reads/writes.
- **Business logic** — port the state machines from `api/app/services/*` into Edge Functions:
  - `orders` (`placed→accepted→fulfilled→completed`; reject/cancel) — see the transition table in
    `api/app/services/orders.py`.
  - `bids` (accept ⇒ decline siblings, create order, mark listing `sold`) — `api/app/services/bids.py`.
  - `reviews` (require a completed order; one per listing) — `api/app/services/reviews.py`.
  - `notifications` fan-out (types in `api/app/services/notifications.py`).
  These run with the **service role** to bypass RLS where cross-party writes are required.
- **Realtime chat** — subscribe to `public.messages` inserts filtered by `conversation`; replaces
  the REST polling in `pages/Inbox.jsx`.

---

## 6. Legacy appendix — Path A (Python + MongoDB)

Kept for reference if you ever need to run the original stack. Both APIs are plain WSGI/ASGI apps;
the example below uses **Render** (free tier spins down after 15 min idle) and **MongoDB Atlas**.

### 6.1 MongoDB Atlas
1. Create a free `M0` cluster near your hosts; create a DB user; allow access (`0.0.0.0/0` or host IPs).
2. Connection string: `mongodb+srv://<user>:<pass>@<cluster>/agrobasket?retryWrites=true&w=majority`.
3. Shared env for both APIs:
   ```env
   MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/agrobasket?retryWrites=true&w=majority
   MONGO_DB=agrobasket
   JWT_SECRET=<your-long-secret>
   CORS_ORIGINS=https://<your-app>.vercel.app
   ACCESS_TOKEN_TTL_MINUTES=30
   REFRESH_TOKEN_TTL_DAYS=7
   ```

### 6.2 Flask (`backend/`)
Render → New Web Service → repo → **Root directory `backend`**; build `pip install -r requirements.txt`;
start `gunicorn app:app -b 0.0.0.0:$PORT` (or use `backend/Dockerfile`). Add the env vars above.

### 6.3 FastAPI (`api/`)
New Web Service → root dir `api`; build `pip install -r requirements.txt`;
start `uvicorn main:app --host 0.0.0.0 --port $PORT`. Health check `/api/health`, docs at `/docs`.

### 6.4 Seed
```bash
MONGO_URI="mongodb+srv://..." ADMIN_EMAIL="..." ADMIN_PASSWORD="..." python infra/seed_all.py
```

### 6.5 Docker (self-hosted)
```bash
git clone <repo> agri-marketplace && cd agri-marketplace
cp .env.example .env   # set real secrets; point MONGO_URI at Atlas (the mongo service is optional)
docker compose up -d --build
```

---

## 7. PWA release checklist

- [ ] `npm run generate:icons` ran → `/public/icons/{192,512,maskable,apple-touch}.png` exist.
- [ ] Production build served over **HTTPS** (Vercel default).
- [ ] Manifest ✓ (`name`, `short_name`, `start_url /`, `display standalone`, `theme_color #F4435E`, icons incl. maskable).
- [ ] Lighthouse PWA audit ≥ 90 on installability + offline.
- [ ] Test install on iOS Safari (add-to-home-screen) and Android Chrome (beforeinstallprompt).
- [ ] Service worker auto-update confirmed (`registerType: autoUpdate`) + an update toast.
- [ ] Push notifications: add VAPID keys + a subscription endpoint (scaffold-ready).

---

## 8. Environment matrix

| Env | Frontend | Supabase | Legacy Flask | Legacy FastAPI | Legacy Mongo |
|---|---|---|---|---|---|
| `development` | http://localhost:5173 | cloud project (free) | localhost:5001 | localhost:8000 | docker `mongo:7` |
| `staging` | Vercel preview | staging project | — | — | — |
| `production` | Vercel domain (or Cloudflare Pages) | prod project | — | — | — |

On the Supabase-native path, `JWT_SECRET` is only relevant to the legacy Python stack; the new
identity layer is Supabase Auth and its JWT signing keys.
