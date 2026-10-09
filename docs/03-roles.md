# 03 · Roles & Permissions (RBAC)

## Roles

| Role | Description | Typical account |
|---|---|---|
| `buyer` | Browses, saves, bids, orders, reviews, chats. Default role on registration. | Consumer / market trader |
| `seller` | Everything a buyer can do **plus** manage their own listings, orders and bids. | Farmer / producer / co-op |
| `moderator` | Moderation: approve/reject/suspend listings, suspend users, manage categories, read stats. | Platform staff |
| `admin` | Full control including assigning roles, deleting anything, sending broadcasts. | Owner |

`buyer` is the default. A user can be upgraded to `seller` at any time (from the UI "become a
seller" action or by an admin).

## Permission matrix

The authoritative list lives in [`shared/roles.py`](../shared/roles.py). Summary:

| Permission | buyer | seller | moderator | admin |
|---|:--:|:--:|:--:|:--:|
| `profile.read` / `profile.update` | ✅ | ✅ | ✅ | ✅ |
| `listing.read` | ✅ | ✅ | ✅ | ✅ |
| `favorite.manage` | ✅ | ✅ | ✅ | ✅ |
| `message.send` | ✅ | ✅ | ✅ | ✅ |
| `notification.read` | ✅ | ✅ | ✅ | ✅ |
| `bid.create` | ✅ | ✅ | ✅ | ✅ |
| `order.create` / `order.read` | ✅ | ✅ | ✅ | ✅ |
| `review.create` | ✅ | ✅ | ✅ | ✅ |
| `listing.manage` (own) | — | ✅ | ✅ | ✅ |
| `order.update` (fulfil/cancel) | — | ✅ | ✅ | ✅ |
| `bid.respond` (accept) | — | ✅ | ✅ | ✅ |
| `listing.sold` | — | ✅ | ✅ | ✅ |
| `listing.moderate` | — | — | ✅ | ✅ |
| `user.read` | — | — | ✅ | ✅ |
| `user.moderate` | — | — | ✅ | ✅ |
| `category.manage` | — | — | ✅ | ✅ |
| `stats.read` | — | — | ✅ | ✅ |
| `review.moderate` | — | — | — | ✅ |
| `user.roles` | — | — | — | ✅ |
| `notifications.send` | — | — | — | ✅ |

## How it is enforced (three layers)

### 1. Flask — decorators (`backend/apps/common/decorators.py`)

```python
@admin_bp.get("/dashboard/stats")
@jwt_required
@require_permission("stats.read")
def dashboard_stats():
    ...
```

- `@jwt_required` decodes the Bearer token and loads the user into `flask.g.user`.
- `@require_permission("x")` checks `shared.roles.user_has(g.user["role"], "x")` → 403 otherwise.

### 2. FastAPI — dependencies (`api/app/dependencies.py`)

```python
@router.post("/listings", dependencies=[Depends(require_permission("listing.manage"))])
async def create_listing(payload: ListingCreate, user=Depends(get_current_user), db=Depends(get_db)):
    ...
```

`get_current_user` is dependency-injectable and also used where the handler needs the user object.

### 3. UI — `useAuth()` (`frontend/src/lib/auth.jsx`)

```jsx
const { can } = useAuth();
{can("listing.manage") && <Link to="/sell">Sell produce</Link>}
```

Route-level guards: `<ProtectedRoute>` (must be logged in) and `<RoleRoute allow={["admin","moderator"]}>`.
**UI checks are UX only** — never the security boundary. The APIs are always the source of truth.

## Role assignment rules

- Registration always creates a `buyer`.
- A **buyer upgrades to seller** via `POST /api/v1/profile/become-seller` (self-service, audited).
- Only `admin` may set `moderator`/`admin` roles (`PATCH /api/admin/users/{id}`), and cannot
  demote the last remaining admin (guarded in `backend/apps/admin/service.py`).
- Every role/status change writes an `audit_logs` document.

## Account status

`users.status` ∈ `active | suspended | pending`. Suspended users are blocked at `get_current_user`
(401/403) even with a valid token. New accounts start `active` (email verification scaffold can
flip them to `pending` when enabled).