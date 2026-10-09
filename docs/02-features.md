# 02 · Feature Matrix

Features are derived from the **OLX/Jiji-clone blueprint** (classified ads: auth, listings,
search, favorites, chat, orders, reviews, notifications, admin) and adapted to **agricultural
produce** (units like kg/crate/head, agri categories, produce quality notes).

Legend — **API** = implemented endpoint(s) · **UI** = React screen/component · **Role** = who can use it.

## Authentication & accounts

| # | Feature | API | UI | Role |
|---|---|---|---|---|
| 1 | Register | `POST /api/auth/register` | `pages/Register.jsx` | public |
| 2 | Login (JWT) | `POST /api/auth/login` | `pages/Login.jsx` | public |
| 3 | Silent refresh | `POST /api/auth/refresh` | axios interceptor | authed |
| 4 | Logout (revoke) | `POST /api/auth/logout` | Navbar menu | authed |
| 5 | Current user | `GET /api/auth/me` | `AuthProvider` | authed |
| 6 | View/update profile | `GET/PATCH /api/v1/profile` | `pages/Profile.jsx` | authed |
| 7 | Password reset scaffold | `POST /api/auth/forgot-password` | Login link | public |

## Listings (classified ads)

| # | Feature | API | UI | Role |
|---|---|---|---|---|
| 8 | Create listing | `POST /api/v1/listings` | `pages/NewListing.jsx` | seller, admin |
| 9 | Browse/paginate | `GET /api/v1/listings` | `pages/Listings.jsx` | public |
| 10 | Search + filters (q, category, price, city, sort) | `GET /api/v1/listings` | `FilterPanel`, `SearchBar` | public |
| 11 | Listing detail (+ view counter) | `GET /api/v1/listings/{id}` | `pages/ListingDetail.jsx` | public |
| 12 | Edit / delete own | `PATCH/DELETE /api/v1/listings/{id}` | `pages/EditListing.jsx`, `MyListings` | owner/admin |
| 13 | Mark sold / re-activate | `PATCH /api/v1/listings/{id}` | `MyListings` | owner |
| 14 | My listings | `GET /api/v1/listings/mine` | `pages/MyListings.jsx` | seller |
| 15 | Report a listing | `POST /api/v1/listings/{id}/report` | `ReportModal` | authed |
| 16 | Moderation (approve/reject/suspend) | `GET/PATCH /api/admin/listings/*` | `admin/Moderation.jsx` | moderator/admin |

## Discovery & engagement

| # | Feature | API | UI | Role |
|---|---|---|---|---|
| 17 | Categories list | `GET /api/v1/categories` | `CategoryChips`, Home grid | public |
| 18 | Categories CRUD | `POST/PATCH/DELETE /api/v1/categories` | `admin/Categories.jsx` | moderator/admin |
| 19 | Favorites toggle | `POST /api/v1/favorites/{listingId}` | `ListingCard` heart | buyer+ |
| 20 | Favorites list | `GET /api/v1/favorites` | `pages/Favorites.jsx` | buyer+ |
| 21 | Bids / negotiate | `POST /api/v1/bids`, `GET /api/v1/bids/mine` | `ListingDetail` bid box | buyer; seller responds |
| 22 | Reviews & ratings | `POST/GET /api/v1/reviews` | `RatingStars`, reviews list | buyer+ |

## Transactions

| # | Feature | API | UI | Role |
|---|---|---|---|---|
| 23 | Place order | `POST /api/v1/orders` | `ListingDetail` order box | buyer |
| 24 | Order list (buying/selling) | `GET /api/v1/orders?role=` | `pages/Orders.jsx` | buyer/seller |
| 25 | Status transitions | `PATCH /api/v1/orders/{id}` | `OrderCard` actions | buyer/seller |
| 26 | Order state machine | placed→accepted→fulfilled→completed (+rejected/cancelled) | status badges | both |

## Communication

| # | Feature | API | UI | Role |
|---|---|---|---|---|
| 27 | Inbox (conversations) | `GET /api/v1/messages` | `pages/Inbox.jsx` | authed |
| 28 | Thread + send | `GET/POST /api/v1/messages/{userId}` | `ChatWindow` | authed |
| 29 | Notifications feed | `GET /api/v1/notifications` | `NotificationBell` | authed |
| 30 | Mark read / clear | `PATCH /api/v1/notifications/{id}`, `DELETE` | bell dropdown | authed |

## Admin dashboard (blueprint `admin-dashboard.gif`)

| # | Feature | API | UI |
|---|---|---|---|
| 31 | KPI stats (users, listings, orders, revenue) | `GET /api/admin/dashboard/stats` | `admin/Dashboard.jsx` |
| 32 | Category distribution + recent activity | `GET /api/admin/dashboard/stats` | `admin/Dashboard.jsx` |
| 33 | User management (suspend, change role) | `GET /api/admin/users`, `PATCH /api/admin/users/{id}` | `admin/Users.jsx` |
| 34 | Listing moderation queue | `GET /api/admin/listings`, `PATCH /api/admin/listings/{id}` | `admin/Moderation.jsx` |
| 35 | Category management | via `api` categories endpoints | `admin/Categories.jsx` |
| 36 | Audit log | `GET /api/admin/audit-logs` | `admin/Dashboard.jsx` (table) |

## Platform (PWA)

| # | Feature | Implementation |
|---|---|---|
| 37 | Installable app | `manifest.webmanifest` (auto-generated) |
| 38 | Offline app shell | Workbox precache + navigation fallback |
| 39 | Runtime caching | images CacheFirst · GET API NetworkFirst |
| 40 | Theme color & icons | Watermelon palette, generated 192/512/maskable |
| 41 | Auto-update | `registerType: "autoUpdate"` + update toast |
| 42 | Push-ready | SW present; add VAPID + `/api/v1/push` to enable |

---

## Explicitly out of scope (v1) / future roadmap

- Payments/escrow (orders are requests; add Stripe/Paystack later).
- Real-time chat transport (v1 uses REST polling; upgrade to Socket.IO / WebSocket).
- Image uploads to object storage (v1 accepts image URLs; add S3/Supabase Storage + `python-multipart`).
- Email/SMS verification and delivery (Resend/Twilio hooks are scaffolded).
- Logistics & delivery tracking.
- Multi-currency and tax handling.