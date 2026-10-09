# 05 · Design System — "Watermelon"

## Palette

| Token | Hex | Best use |
|---|---|---|
| `--wm-red` 🍉 | `#F4435E` | Primary: buttons, CTAs, highlights, active states |
| `--wm-pink` 🌸 | `#FF758F` | Secondary accents, illustrations, badges |
| `--wm-green` 🍃 | `#4CAF50` | Secondary elements, icons, success |
| `--wm-deep-green` 🌿 | `#216E39` | Headings, contrast, borders, links |
| `--wm-pale` 🤍 | `#E8F5C8` | Backgrounds, cards, soft surfaces |
| `--wm-black` 🖤 | `#252525` | Text, icons, outlines |

### Derived tokens

| Token | Value |
|---|---|
| `--wm-bg` | `#FDFBF3` (warm paper, sits on pale rind) |
| `--wm-surface` | `#FFFFFF` |
| `--wm-surface-soft` | `#E8F5C8` (pale) |
| `--wm-text` | `#252525` |
| `--wm-text-muted` | `rgba(37,37,37,.62)` |
| `--wm-focus` | `#FF758F` ring |
| `--wm-danger` / `--wm-success` | `#F4435E` / `#4CAF50` |

All tokens are declared as CSS custom properties in
[`frontend/src/theme/tokens.css`](../frontend/src/theme/tokens.css) and consumed across every
component via `var(--wm-*)`. No hard-coded colors in components.

## Typography

| Level | Size | Weight | Color |
|---|---|---|---|
| Display (`h1`) | `clamp(1.75rem, 3.2vw, 2.5rem)` | 800 | `--wm-deep-green` |
| Heading (`h2/h3`) | `1.25–1.5rem` | 700 | `--wm-deep-green` |
| Body | `0.9375rem` | 400 | `--wm-text` |
| Caption / meta | `0.8125rem` | 500 | `--wm-text-muted` |

System stack: `Inter, -apple-system, "Segoe UI", Roboto, sans-serif`. For CJK/agri app store copy
keep fallbacks to local fonts.

## Spacing & radius

- Spacing scale: `4 · 8 · 12 · 16 · 24 · 32 · 48` (px) — `--space-*` tokens.
- Radius: `--radius-sm: 8px`, `--radius-md: 14px`, `--radius-xl: 24px` (cards, modals), `--radius-pill: 999px`.
- Shadows: `--shadow-1` (12% black, 4px) for cards; `--shadow-2` for dropdowns/modals.

## Components gallery (all in `frontend/src/components/ui`)

| Component | Purpose |
|---|---|
| `Button` | `variant: primary / secondary / ghost / danger / outline` · `size` · loading spinner · `asChild` link support |
| `Input / Textarea / Select / Field` | Form primitives + label + error + hint |
| `Card` | Surface container w/ optional header/footer |
| `Badge / StatusBadge` | Tones: `red / pink / green / deep / black / pale`; status→tone mapping |
| `Modal` | Dialog w/ backdrop, ESC + overlay close, focus trap-ish |
| `Tabs` | Underline tabs for Orders/Profile sections |
| `Pagination` | Prev/next + page numbers driven by API page object |
| `RatingStars` | Read-only + interactive ratings |
| `Spinner / Skeleton / EmptyState` | Loading & empty UX |
| `Toast` | Success/error/info toasts (top-right, auto-dismiss) |

## Layout

- **Guest/marketplace shell** (`AppLayout`): sticky navbar (search + nav + auth), footer, content max-width `1200px`.
- **App shell** (authed): same navbar, plus heavier nav when admin.
- **Admin shell** (`AdminLayout`): left sidebar (Dashboard, Users, Listings, Categories, Audit) + content.
- **Responsive:** mobile-first; grid `repeat(auto-fill, minmax(240px, 1fr))` for listing cards; navbar collapses to drawer on < 768px.

## Accessibility & PWA notes

- Target contrast ≥ 4.5:1 on text (deep green on pale passes; red is reserved for large/emphasis text).
- Focus ring `--wm-focus` on all interactive elements.
- Semantic landmarks (`header/nav/main/footer`), `aria` labels on icon buttons.
- PWA theme color `#F4435E`; SVG/PNG icons match the palette (see `scripts/generate-icons.mjs`).