# 🍉 AgroBasket — Agricultural Produce Marketplace (PWA)

AgroBasket is a **Progressive Web App (PWA)** marketplace for agricultural produce. Farmers
and producers list crops, livestock and farm goods; buyers search, negotiate, order and chat —
exactly like an OLX-style classified marketplace — but purpose-built for agri-produce.

Built with a **modular, mono-repo** architecture that is **reproducible** (Docker + seeds) and
**explainable** (every domain is its own module with docs).

---

## ✨ Feature Overview (guided by the OLX-clone blueprint)

| Area | Capabilities |
|---|---|
| **Auth & Identity** | Register, login, JWT access + refresh tokens, logout, password reset scaffold |
| **Roles (RBAC)** | `buyer`, `seller`, `moderator`, `admin` — enforced at both API layers and in the UI |
| **Listings** | Create/edit/delete classified ads (price, quantity, unit, category, location, images), views counter, mark as sold |
| **Search & Filters** | Keyword, category, price range, location, sort, pagination (mirrors OLX search) |
| **Favorites** | Save / unsave listings, "My favorites" page |
| **Bids & Negotiation** | Buyers place price bids on listings; sellers accept |
| **Orders** | Buyer→seller order requests with a status state machine (placed → accepted → fulfilled → completed / rejected / cancelled) |
| **Reviews & Ratings** | Post-order reviews, aggregate seller rating |
| **Chat (Messages)** | Buyer↔seller inbox + threaded chat (REST + polling scaffold, upgradeable to WebSockets) |
| **Notifications** | Server-generated events (new order, bid, message, moderation) + read/unread |
| **Admin Dashboard** *(blueprint GIF)* | KPI stats, listings moderation (approve/reject/suspend), user management (suspend, change role), category management |
| **PWA** | Installable (manifest), offline app shell & caching (Workbox), theme-color, push-ready |

---

## 🧱 Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend (PWA) | **React 18 + Vite + vite-plugin-pwa** | Fast builds, first-class PWA plugin, tiny bundle |
| Identity / Admin backend | **Python Flask** | Lightweight, battle-tested HTTP layer for auth + admin ops |
| Marketplace API | **Python FastAPI** | Async, auto OpenAPI docs, Pydantic validation for the public API |
| Database | **MongoDB** | Flexible document model for listings/orders/notifications, natural fit for a classifieds schema |
| Deployment | **Vercel** (frontend) · Render/Railway/Docker (APIs) · MongoDB Atlas | See [`docs/06-deployment.md`](docs/06-deployment.md) |

> **⚠️ About "backend on Supabase":** Supabase is a *PostgreSQL* BaaS and **cannot run Flask,
> FastAPI or MongoDB**. This repo ships MongoDB-first (per the stack above). `docs/06-deployment.md`
> explains both options: **(A)** deploy Python APIs on Render/Railway + MongoDB Atlas (recommended),
> or **(B)** swap the data layer to Supabase (Postgres + Supabase Auth) if you prefer managed auth/DB.

---

## 🗂 Repository Layout (mono-repo)

```
agri-marketplace/
├── docs/                  # Architecture, features, roles, API, design system, deployment
├── shared/                # Reusable Python lib (config, JWT, passwords, RBAC, errors, seed data)
├── backend/               # Flask service — Identity (auth) + Admin (dashboard/moderation)
├── api/                   # FastAPI service — Marketplace REST API (listings, orders, chat…)
├── frontend/              # React PWA — Vite + design system + app shell + pages
├── scripts/               # Dev/setup assistants + PWA icon generator
├── docker-compose.yml     # One-command local environment (postgres + backend + api + frontend)
└── Makefile               # Makefile + .ps1 shortcuts
```

---

## 🚀 Quickstart (Docker — recommended)

Prerequisites: **Docker + Docker Compose v2**.

```bash
# optional: configure secrets / admin credentials
cp .env.example .env

# build & run everything (postgres, flask, fastapi, vite)
docker compose up --build

# seed roles, admin user, categories and demo listings (idempotent — safe to re-run)
docker compose run --rm seed
```

Apps once running:

| Service | URL | Docs |
|---|---|---|
| Frontend (PWA) | http://localhost:5173 | — |
| Flask API (auth/admin) | http://localhost:5001 | `/api/health` |
| FastAPI marketplace | http://localhost:8000 | Swagger at `/docs`, OpenAPI at `/openapi.json` |
| PostgreSQL | postgresql://localhost:5432/agrobasket | database `agrobasket` |

**Default admin** (created by seed): `admin@agrobasket.test` / `Admin@12345` — *change in `.env` before production.*
Demo accounts: `seller@agrobasket.test` / `buyer@agrobasket.test` (same password).

### Quickstart without Docker

```bash
# backend (flask)
cd backend && python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt -r requirements-dev.txt
python seed.py && python app.py            # http://localhost:5001

# api (fastapi) — needs its own venv or reuse
cd api && pip install -r requirements.txt -r requirements-dev.txt
python seed.py && uvicorn main:app --reload --port 8000

# frontend (pwa)
cd frontend && npm install
npm run generate:icons && npm run dev     # http://localhost:5173
```

> Each service needs `DATABASE_URL` (see its `.env.example`). Copy `.env.example` → `.env`.

---

## 🔁 Common workflows

```bash
make dev          # docker compose up --build
make seed         # run idempotent seeders
make logs         # compose logs -f
make test         # run backend + api pytest suites
make frontend     # cd frontend && npm run dev
make deploy-check # CI-style build: frontend build + python compile + tests
```

Windows PowerShell equivalents live in [`scripts/`](scripts/) (`setup.ps1`, `dev.ps1`, `seed.ps1`).

---

## 📚 Documentation index

| Doc | Contents |
|---|---|
| [`docs/01-architecture.md`](docs/01-architecture.md) | System diagram, service responsibilities, auth flow, module map |
| [`docs/02-features.md`](docs/02-features.md) | Feature matrix mapped to endpoints/pages |
| [`docs/03-roles.md`](docs/03-roles.md) | RBAC model, permission matrix, how roles are enforced |
| [`docs/04-api.md`](docs/04-api.md) | Full REST reference (Flask + FastAPI), status codes, pagination shape |
| [`docs/05-design-system.md`](docs/05-design-system.md) | Watermelon palette tokens, typography, spacing, components |
| [`docs/06-deployment.md`](docs/06-deployment.md) | Vercel, Render/Railway, MongoDB Atlas, Docker, Supabase comparison, PWA checklist |

---

## 🔐 Security baseline

- Passwords hashed with **PBKDF2-SHA256** (Werkzeug) — no plaintext, no bcrypt native builds.
- **Short-lived access tokens** (30 min) + **revocable refresh tokens** (7 d, stored in Mongo).
- Scoped permissions per role enforced in **both** API layers (`backend` decorators + `api` dependencies).
- Admin endpoints require `moderator` or `admin`; moderation actions are logged to the `audit_logs` collection.
- CORS locked to frontend origin(s); secrets live in env / `.env` only.

---

## 📄 License

MIT © 2026 — see `LICENSE` (add before publishing).