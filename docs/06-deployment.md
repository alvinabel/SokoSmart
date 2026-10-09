# 06 · Deployment Guide

Verified target: **Vercel** for the frontend PWA + container-friendly hosts for the Python APIs +
**MongoDB Atlas** for data. Detailed instructions below, plus how to run **Docker**, and an
honest breakdown of the "**backend on Supabase**" option.

---

## ⚠️ First: the Supabase + MongoDB question

Your stack says **MongoDB**, your deployment note says **backend Supabase**. These conflict:

> Supabase is a managed **PostgreSQL** backend-as-a-service (DB + Auth + Storage + Edge Functions).
> It **cannot** run Flask/FastAPI, and it is **not** MongoDB.

Two clean paths:

### Path A — Keep MongoDB + Python APIs (recommended, matches this codebase)
- **Frontend** → Vercel (static build from `frontend/dist`).
- **Flask + FastAPI** → any container/Python host: Render, Railway, Fly.io, Google Cloud Run, AWS.
- **Database** → MongoDB Atlas (free M0 tier).

### Path B — Adopt Supabase (Postgres)
- Replace Mongo access in `api/app/core/mongo.py` / `shared/mongo.py` with `supabase-py`.
- Use **Supabase Auth** (email/password, OAuth) instead of the Flask JWT service, or keep Flask and
  just swap the DB. Supabase Storage for listing images; PostgREST for CRUD; Realtime for chat.
- This is a **rewrite of the persistence layer**, not a config change. Keep `shared/roles.py`
  logic but enforce at Postgres level (RLS) too.

This doc focuses on **Path A**; §5 gives Supabase specifics if you choose Path B.

---

## 0. Prereqs (all paths)

- GitHub repo + [Vercel](https://vercel.com) account + [MongoDB Atlas](https://www.mongodb.com/atlas) account.
- Set `JWT_SECRET` to a long random value (e.g. `openssl rand -hex 32`) — **never** the dev default in prod.
- Whichever host you use, after first boot run the **seeder** to create roles/admin/categories/demo data.

---

## 1. MongoDB Atlas

1. **Create cluster** → free `M0` → choose region near your hosts.
2. **Database access**: create a user with a strong password.
3. **Network access**: `0.0.0.0/0` (or your host IPs) — use the "Cloud Provider" option when the host is predictable.
4. Copy the **connection string**: `mongodb+srv://<user>:<pass>@<cluster>/agrobasket?retryWrites=true&w=majority`.
5. Shared env vars for both APIs:

```env
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/agrobasket?retryWrites=true&w=majority
MONGO_DB=agrobasket
JWT_SECRET=<your-long-secret>
CORS_ORIGINS=https://<your-app>.vercel.app
ACCESS_TOKEN_TTL_MINUTES=30
REFRESH_TOKEN_TTL_DAYS=7
```

---

## 2. Frontend → Vercel (PWA)

1. **Build locally to confirm:** `cd frontend && npm install && npm run generate:icons && npm run build` → outputs `dist/` (includes `sw.js` + `manifest.webmanifest`).
2. Push the repo to GitHub and click **Import** in Vercel → pick `agri-marketplace/frontend`.
3. Settings:

| Setting | Value |
|---|---|
| Framework preset | `Vite` |
| Root directory | `frontend` |
| Build command | `npm run build` |
| Install command | `npm install` |
| Output directory | `dist` |
| Node version | `20.x` |

4. **Environment variables** (Vercel project → Settings → Environment Variables):

```env
VITE_AUTH_API_URL=https://<flask-host>/api
VITE_MARKET_API_URL=https://<api-host>/api/v1
```

5. **Deploy.** Two live URLs will work: the service worker requires the app to be served over
   HTTPS — Vercel gives you that free.

> **Vercel CLI alternative:** `npx vercel --prod` from `frontend/` (uses the same settings once linked).

---

## 3. Python APIs → Render (or Railway)

Both backends are plain WSGI/ASGI apps; this example uses **Render web services** (free/paid).
Railway is nearly identical — choose a "Docker" or "Python" template and add the same env vars.

### 3.1 Flask (`backend/`)

1. Render → New Web Service → point at repo → **Root directory:** `backend`.
2. Build: `pip install -r requirements.txt` • Start command: `gunicorn app:app -b 0.0.0.0:$PORT` (Render injects `$PORT`; our Docker port override is `5001`).
   If using Docker deploys, render uses `backend/Dockerfile` which already runs gunicorn on `$PORT`.
3. Add env vars from §1.

### 3.2 FastAPI (`api/`)

1. New Web Service → root dir `api`.
2. Build: `pip install -r requirements.txt` • Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (Dockerfile also works).
3. Add env vars from §1.
4. Enable the **health check** at `/api/health` and `/docs` to confirm boot.

### 3.3 Seed production data

```bash
# after each API is live, run (once) from your machine or a one-off container:
MONGO_URI="mongodb+srv://..." ADMIN_EMAIL="..." ADMIN_PASSWORD="..." python infra/seed_all.py
```

Rotate the admin password afterwards, or keep it safe in a password manager — it's the superuser.

---

## 4. Docker deployment (self-hosted alternative)

Ships the full stack via `docker-compose.yml`. For a server (e.g. a VPS with 1–2 GB RAM):

```bash
git clone <repo> agri-marketplace && cd agri-marketplace
cp .env.example .env   # set real secrets + MONGO_URI to Atlas (the mongo service is optional)
docker compose up -d --build
```

To run without a local Mongo (Atlas at the edge): remove/scale the `mongo` block and point
`MONGO_URI` at Atlas.

Behind a reverse proxy (Caddy/Nginx/Traefik) add TLS; set `CORS_ORIGINS` to the real frontend URL.

---

## 5. Supabase alternative (Path B, summary)

| Concern | Trade-off vs MongoDB path |
|---|---|
| Auth | Use Supabase Auth (JWT `sub` = Supabase user) — adapt `shared/jwt_token.py` to verify Supabase JWTs (`anon/public` key), or keep Flask minting its own tokens and store user rows in Postgres. |
| DB | Tables `users, listings, orders, bids, reviews, messages, notifications`. Enable **Row Level Security**: sellers edit their rows, buyers read active listings. Port index logic to Postgres indexes. |
| Realtime chat | `supabase-js` channels replace the REST polling in `pages/Inbox.jsx`. |
| Storage (listings images) | Supabase Storage public bucket + signed URLs instead of image-URL fields. |
| Python | Use `supabase-py` (sync, PostgREST) in FastAPI; Flask admin stays but reads Postgres. |
| Deploy | Frontend still Vercel; Edge Functions/PG can host lightweight logic, but Flask+FastAPI still need a host (Render/Railway). |

**Recommendation:** unless you specifically want managed Postgres + PostgREST, Path A is far less work.

---

## 6. PWA release checklist

- [ ] `npm run generate:icons` ran → `/public/icons/{192,512,maskable,apple-touch}.png` exist.
- [ ] Production build served over **HTTPS** (Vercel default).
- [ ] Manifest ✓ (`name`, `short_name`, `start_url /`, `display standalone`, `theme_color #F4435E`, icons incl. `purpose: any` + maskable).
- [ ] Lighthouse PWA audit ≥ 90 on installability + offline.
- [ ] Test install on iOS Safari (add-to-home-screen) and Android Chrome (beforeinstallprompt).
- [ ] Service worker auto-update confirmed (`registerType: autoUpdate`) + an update toast.
- [ ] Push notifications: add VAPID keys + `/api/v1/push` subscription endpoint (scaffold-ready).

---

## 7. Environment matrix

| Env | Frontend (Vercel) | Flask | FastAPI | Mongo |
|---|---|---|---|---|
| `development` | http://localhost:5173 | localhost:5001 | localhost:8000 | docker `mongo:7` |
| `staging` | vercel preview | Render .internal | Render .internal | Atlas shared |
| `production` | vercel.com domain | Render | Render | Atlas M0+ |

Keep `JWT_SECRET` identical across Flask and FastAPI **in the same environment** and different
between environments.