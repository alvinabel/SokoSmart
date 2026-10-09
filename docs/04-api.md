# 04 · API Reference

Two API surfaces. Authentication: add `Authorization: Bearer <access_token>` to protected routes.

- **Flask** (`backend/`, port `5001`) — identity + admin.
- **FastAPI** (`api/`, port `8000`) — marketplace, live docs at `http://localhost:8000/docs`.

## Conventions

- Errors always have the shape `{"error": {"code": "...", "message": "..."}}`.
- Pagination: `GET ...?page=1&page_size=20` → `{ "items": [...], "total": N, "page": 1, "page_size": 20, "pages": M }`.
- Listings statuses: `draft | pending | active | sold | suspended | rejected`.
- Order statuses: `placed → accepted → fulfilled → completed` (also `rejected`, `cancelled`).
- Bid statuses: `pending | accepted | declined`.
- Auth errors: `401` invalid/expired token · `403` missing permission · `409` conflict · `422` validation · `404` missing.

---

## Flask — `/api` (identity + admin)

### Auth

| Method | Path | Auth | Body / params | Returns |
|---|---|---|---|---|
| GET | `/api/health` | — | — | `{status, service, version}` |
| POST | `/api/auth/register` | — | `{name, email, password, phone?, role?="buyer"}` | `201 {user, access_token, refresh_token}` |
| POST | `/api/auth/login` | — | `{email, password}` | `200 {user, access_token, refresh_token}` |
| POST | `/api/auth/refresh` | refresh token | `{refresh_token}` | `{access_token, refresh_token}` |
| POST | `/api/auth/logout` | access | `{refresh_token}` | `204` revokes jti |
| GET | `/api/auth/me` | access | — | `{user}` |
| POST | `/api/auth/forgot-password` | — | `{email}` | `204` (scaffold) |

`user` serialized as `{id, name, email, role, phone, location, status, rating, created_at}` (no password).

### Admin (require `moderator`/`admin` permission checks per route)

| Method | Path | Permission | Returns |
|---|---|---|---|
| GET | `/api/admin/dashboard/stats` | `stats.read` | KPIs + breakdowns (see §Admin stats) |
| GET | `/api/admin/users` | `user.read` | paginated users (`?q=&role=&page=`) |
| PATCH | `/api/admin/users/{id}` | `user.moderate` | `{action: suspend/activate/role, value}` |
| GET | `/api/admin/listings` | `listing.moderate` | paginated listings (`?q=&status=`) |
| PATCH | `/api/admin/listings/{id}` | `listing.moderate` | `{action: approve/reject/suspend/activate}` |
| GET | `/api/admin/audit-logs` | `stats.read` | recent admin actions |
| DELETE | `/api/admin/users/{id}` | `user.roles` | `204` (guards last-admin) |

**Admin stats payload:**

```json
{
  "users": { "total": 120, "by_role": {"buyer": 90, "seller": 25, "admin": 2, "moderator": 3}, "active": 118, "suspended": 2 },
  "listings": { "total": 340, "by_status": {"active": 300, "pending": 30, "suspended": 10}, "by_category": [{"slug":"vegetables","count":120,"name":"Vegetables"}] },
  "orders": { "total": 45, "by_status": {"placed": 5, "accepted": 8, "completed": 30, "rejected": 2} },
  "revenue": 48250.0,
  "recent_users": [ {user...} ],
  "recent_activity": [ {listing...} ]
}
```

---

## FastAPI — `/api/v1` (marketplace)

### Listings

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/listings` | — | List. Query: `q, category, min_price, max_price, city, status(=active), seller, sort(price_asc/price_desc/newest/most_viewed), page, page_size` |
| GET | `/api/v1/listings/mine` | access | List own listings (all statuses) |
| GET | `/api/v1/listings/{id}` | — | Detail (increments `views`; includes `seller`, `category_meta`) |
| POST | `/api/v1/listings` | `listing.manage` | Create `{title, description, category, price, unit, quantity, location:{city,district?}, images[], quality?}` |
| PATCH | `/api/v1/listings/{id}` | owner/admin | Partial update; own status transitions `active→sold`, `sold→active` |
| DELETE | `/api/v1/listings/{id}` | owner/admin | Soft delete (`status: deleted`) |

### Categories

`GET /api/v1/categories` — all (slug, name, emoji, color). Admin (moderator+): `POST`, `PATCH /{slug}`, `DELETE /{slug}`.

### Favorites (`favorite.manage`)

- `GET /api/v1/favorites` → own favorites w/ listing snapshot
- `POST /api/v1/favorites/{listingId}` → toggle (idempotent) → `{favorited: bool}`
- `DELETE /api/v1/favorites/{listingId}`

### Bids

| Method | Path | Permission | Purpose |
|---|---|---|---|
| POST | `/api/v1/bids` | `bid.create` | `{listing_id, amount}` (buyer, not on own listing) |
| GET | `/api/v1/bids/mine` | `bid.create` | my bids |
| GET | `/api/v1/bids/listing/{listingId}` | `bid.respond`/owner | bids on my listing |
| PATCH | `/api/v1/bids/{id}` | `bid.respond`/owner | `{action: "accept"/"decline"}` |

### Orders

| Method | Path | Permission | Purpose |
|---|---|---|---|
| POST | `/api/v1/orders` | `order.create` | `{listing_id, quantity?, note?}` (not on own listing, listing must be `active` or `sold`) |
| GET | `/api/v1/orders` | `order.read` | `?role=buying|selling&status=&page=` |
| GET | `/api/v1/orders/{id}` | parties | detail incl. history |
| PATCH | `/api/v1/orders/{id}` | parties | `{action}` buyer: `cancel`; seller: `accept`, `reject`, `fulfill`; both: `complete` (record review eligibility) |

### Reviews (`review.create` after a `completed` order)

- `POST /api/v1/reviews` — `{listing_id, rating(1-5), comment?}` (one per listing+author)
- `GET /api/v1/reviews/listing/{listingId}`
- `GET /api/v1/reviews/seller/{userId}` → `{avg_rating, count, items}`
- `DELETE /api/v1/reviews/{id}` — author or admin

### Notifications (`notification.read`)

- `GET /api/v1/notifications?unread_only=&page=`
- `GET /api/v1/notifications/unread-count`
- `PATCH /api/v1/notifications/{id}` → `{read: true}` ; `PATCH /api/v1/notifications/read-all`
- `DELETE /api/v1/notifications` → clear read notifications

### Messages (`message.send`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/messages` | inbox — conversations (other party, last message, unread count, listing ref) |
| GET | `/api/v1/messages/{userId}` | thread with a user (`?listingId=`) |
| POST | `/api/v1/messages/{userId}` | `{body, listing_id?}` — conversation id is `sorted(user_id, other_id)` |

---

## Example flow (happy path)

```
1  POST  /api/auth/register                      → {user(role=buyer), access_token, refresh_token}
2  POST  /api/v1/listings                        (seller) → listing {id}
3  GET   /api/v1/listings?q=maize&category=grains → page of listings
4  POST  /api/v1/favorites/{listingId}           → {favorited:true}
5  POST  /api/v1/bids  {listing_id, amount:1200} → bid
6  PATCH /api/v1/bids/{id} {action:"accept"}     (seller)
7  POST  /api/v1/orders {listing_id, quantity:3} → placed
8  PATCH /api/v1/orders/{id} {action:"accept"}   (seller) → accepted
9  PATCH /api/v1/orders/{id} {action:"fulfill"}  (seller) → fulfilled
10 PATCH /api/v1/orders/{id} {action:"complete"} (buyer)  → completed
11 POST  /api/v1/reviews {listing_id, rating:5}  → review
12 POST /api/v1/messages/{sellerId} {body:"...", listing_id}
```