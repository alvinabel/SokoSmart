# 01 · Architecture

## 1. System at a glance

AgroBasket is a **mono-repo** with three deployable services plus a shared Python library.
Requests fan out from the React PWA to two independent backends that share one PostgreSQL database.

```
                        ┌──────────────────────────────┐
                        │   React PWA (Vite)           │
                        │   installable, offline shell  │
                        └───────────────┬──────────────┘
                   HTTPS                   │                 HTTPS
        ┌──────────────────────────────────┼──────────────────────────────────┐
        │                                  │                                  │
        ▼                                  ▼                                  ▼
┌───────────────────────┐      ┌───────────────────────┐         ┌─────────────────────┐
│  Flask  (backend/)    │      │  FastAPI (api/)        │         │  Static assets       │
│  Identity + Admin     │      │  Marketplace REST      │         │  (Vercel CDN)        │
│  /api/auth/*          │      │  /api/v1/*             │         └─────────────────────┘
│  /api/admin/*         │      │                        │
└───────────┬───────────┘      └───────────┬───────────┘
            │        shared/ (config, jwt, roles, errors, categories)
            │                              │
            └──────────────┬───────────────┘
                           ▼
                 ┌───────────────────┐
                 │   PostgreSQL       │
                 │   db: agrobasket   │
                 └───────────────────┘
```

### Why two Python backends?

The task specifies **both Flask and FastAPI**. Splitting so each does what it is best at keeps
each module small, testable and independently deployable:

| Service | Responsibility | Why this framework |
|---|---|---|
| **`backend/` (Flask)** | Authentication & sessions (register/login/refresh/logout), RBAC primitives, **admin dashboard** (KPIs, user & listing moderation, categories), audit logging. | Flask's minimal surface + blueprints is ideal for a focused identity/admin service; easy to run behind gunicorn. |
| **`api/` (FastAPI)** | The high-traffic **marketplace REST API**: listings, search, favorites, bids, orders, reviews, notifications, chat. | Async I/O, Pydantic validation, automatic OpenAPI/Swagger docs. |
| **`shared/`** | Config, JWT minting/verification, password hashing, RBAC matrix, domain errors, canonical seed data, Mongo index definitions. | Guarantees the two backends agree on contracts. |

Both backends are stateless (all state lives in MongoDB), which makes horizontal scaling and
serverless/container deploys trivial.

---

## 2. Module map

```
shared/
  config.py        env → typed config object (singleton)
  jwt_token.py     create_access_token / create_refresh_token / decode_token
  passwords.py     hash_password / verify_password (PBKDF2-SHA256)
  roles.py         Role enum + PERMISSIONS matrix + user_has()
  errors.py        ApiError hierarchy → consistent JSON
  categories.py    canonical agri categories (seed + UI fallback)
  db.py            psycopg3 connection pool + query helpers (fetch/execute)
  schema.py        idempotent Postgres DDL + ensure_schema()/truncate_all()

backend/
  app.py                 WSGI entry (gunicorn: `app:app`)
  apps/factories.py      create_app() — app factory + blueprint registration
  apps/common/           decorators (jwt_required, require_permission), helpers
  apps/auth/             routes.py · service.py · schemas.py
  apps/admin/            routes.py · service.py   (dashboard + moderation)
  seed.py                roles + admin + demo users + categories

api/
  main.py                ASGI entry (`main:app`)
  app/api.py             create_app() — routers, CORS, exception handlers
  app/core/db.py         pooled psycopg connection + get_db dependency
  app/core/types.py      shared enum/constant strings
  app/dependencies.py    get_current_user, require_permission
  app/schemas/*.py       Pydantic request/response models
  app/routers/*.py       thin HTTP layer
  app/services/*.py      business logic operating on Postgres tables (SQL)
  seed.py                demo listings/orders (uses shared categories)

frontend/
  src/theme            design tokens (watermelon palette) + global styles
  src/lib              api client (axios + interceptors), auth context, toasts
  src/components/ui    generic primitives (Button, Input, Modal…)
  src/components/layout app shell, navbar, sidebar, route guards
  src/components/features domain widgets (ListingCard, OrderCard…)
  src/pages            route-level screens (+ src/pages/admin/*)
  vite.config.js       vite-plugin-pwa manifest + Workbox caching
```

**Rule of thumb:** routers/controllers never talk to the database directly in FastAPI — they call a
*service*. In Flask the auth/admin services play the same role. This keeps HTTP concerns
(auth, serialization, status codes) separate from business rules.

---

## 3. Authentication & authorization flow

Identity is owned by the **Flask** service; FastAPI trusts the same signed JWT.

```
 Register ─▶ POST /api/auth/register ─▶ hash pwd ─▶ users.insert {role: "buyer"}
 Login    ─▶ POST /api/auth/login    ─▶ verify pwd ─┐
                                                    ├─▶ access token  (30 min, HS256)
                                                    └─▶ refresh token (7 d, stored w/ jti)
 Access protected API ─▶ Authorization: Bearer <access> ─▶ decode (shared secret)
 401 expired?         ─▶ POST /api/auth/refresh (with refresh) ─▶ new access token
 Logout               ─▶ POST /api/auth/logout ─▶ delete refresh jti (revoked)
```

**Token payload (access):** `sub` (user id), `typ="access"`, `role`, `email`, `name`, `exp`, `iat`, `iss`, `aud`.

**Enforcement points**

1. **Flask** — `@jwt_required` + `@require_permission("x")` decorators in `apps/common/decorators.py`.
2. **FastAPI** — `Depends(get_current_user)` and `require_permission("x")` in `app/dependencies.py`.
3. **UI** — `useAuth().can("x")` hides/disable controls (defence-in-depth; *not* a security boundary).

A single `JWT_SECRET` (env) is shared by both backends, so an access token minted by Flask is
accepted by FastAPI without a network call.

---

## 4. Data model (PostgreSQL tables)

| Table | Purpose | Key fields |
|---|---|---|
| `users` | accounts + role + profile | `email`(unique), `password_hash`, `role`, `name`, `phone`, `location`, `status` |
| `refresh_tokens` | revocable refresh registry | `jti`(unique, TTL), `user`, `revoked` |
| `listings` | classified ads | `title`, `description`, `category`, `price`, `unit`, `quantity`, `images[]`, `location{}`, `seller`, `status`, `views` |
| `categories` | agri categories | `slug`(unique), `name`, `emoji`, `color` |
| `orders` | buyer→seller requests | `listing`, `buyer`, `seller`, `quantity`, `total`, `status`, `history[]` |
| `bids` | price negotiations | `listing`, `bidder`, `amount`, `status` |
| `reviews` | post-order ratings | `listing`, `author`, `seller`, `rating`, `comment` |
| `favorites` | saved listings | `user`, `listing` (unique pair) |
| `notifications` | event feed | `recipient`, `type`, `read`, `data{}` |
| `messages` | chat | `conversation` (sorted id pair), `sender`, `recipient`, `body`, `created_at` |
| `audit_logs` | admin actions | `actor`, `action`, `target`, `created_at` |

Schema and indexes are declared once in `shared/schema.py` (`ensure_schema()`, applied on service
boot, by seeders and by the test harness) and mirrored in `supabase/schema.sql`.

---

## 5. Request lifecycle (example: create a listing)

```
PWA                     FastAPI                     PostgreSQL
 │  POST /api/v1/listings  │                             │
 │  Bearer <access>        │                             │
 ├────────────────────────▶│                             │
 │                         │ get_current_user() → decode JWT, load user
 │                         │ require_permission("listing.manage")
 │                         │ validate body (Pydantic ListingCreate)
 │                         │ services.listings.create() ─▶ INSERT INTO listings
 │                         │ create notification (optional) ─▶ notifications
 │◀──────── 201 listing ───┤                             │
```

---

## 6. Reproducibility & environments

- **Config** is 100% environment-driven (`shared/config.py`); every service ships a `.env.example`.
- **Seeds** are idempotent (`backend/seed.py`, `api/seed.py`, `infra/seed_all.py`) — safe to re-run.
- **Docker Compose** brings the whole stack up with one command; `seed` runs as a one-shot profile.
- **CI** (`.github/workflows/ci.yml`) compiles all Python, runs both pytest suites and builds the PWA.
- **Environments:** `development` (compose), `staging`, `production` — only env vars differ.

---

## 7. PWA architecture

- `vite-plugin-pwa` generates a **Workbox service worker** (`generateSW`) + `manifest.webmanifest`.
- **Precache:** app shell (JS/CSS/HTML/fonts/icons).
- **Runtime caching:** images `CacheFirst`, GET API `NetworkFirst` with short TTL, others `StaleWhileRevalidate`.
- **Offline:** SPA navigation fallback to `index.html`; a friendly offline notice for failed API calls.
- **Installability:** manifest with 192/512 + maskable icons, `theme_color #F4435E`, `display: standalone`.
- **Upgrade path to push:** the service worker + notification feed are ready for Web Push (add VAPID keys + a push router).

See `docs/06-deployment.md` for hosting each piece.