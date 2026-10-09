export const ROLES = {
  buyer: 'Buyer',
  seller: 'Seller',
  moderator: 'Moderator',
  admin: 'Admin',
}

export const LISTING_STATUS = {
  draft: { label: 'Draft', tone: 'pale' },
  pending: { label: 'Pending review', tone: 'pink' },
  active: { label: 'Active', tone: 'green' },
  sold: { label: 'Sold', tone: 'red' },
  suspended: { label: 'Suspended', tone: 'red' },
  rejected: { label: 'Rejected', tone: 'red' },
  deleted: { label: 'Deleted', tone: 'black' },
}

export const ORDER_STATUS = {
  placed: { label: 'Placed', tone: 'pale' },
  accepted: { label: 'Accepted', tone: 'green' },
  rejected: { label: 'Rejected', tone: 'red' },
  fulfilled: { label: 'Fulfilled', tone: 'pink' },
  completed: { label: 'Completed', tone: 'black' },
  cancelled: { label: 'Cancelled', tone: 'black' },
}

export const UNITS = ['unit', 'kg', 'crate', 'bag', 'sack', 'basket', 'bunch', 'head', 'litre', 'seedling']

// Mirrors shared/roles.py — used for UI affordances only (security lives in the APIs).
const P = {
  buyer: [
    'profile.read',
    'profile.update',
    'listing.read',
    'favorite.manage',
    'message.send',
    'notification.read',
    'order.create',
    'order.read',
    'review.create',
    'bid.create',
  ],
  seller: [
    'profile.read',
    'profile.update',
    'listing.read',
    'favorite.manage',
    'message.send',
    'notification.read',
    'order.create',
    'order.read',
    'order.update',
    'review.create',
    'listing.manage',
    'bid.create',
    'bid.respond',
    'listing.sold',
  ],
  moderator: [
    'profile.read',
    'profile.update',
    'listing.read',
    'favorite.manage',
    'message.send',
    'notification.read',
    'order.create',
    'order.read',
    'order.update',
    'review.create',
    'bid.create',
    'bid.respond',
    'listing.manage',
    'listing.moderate',
    'user.read',
    'user.moderate',
    'stats.read',
    'category.manage',
  ],
  admin: [
    'profile.read',
    'profile.update',
    'listing.read',
    'favorite.manage',
    'message.send',
    'notification.read',
    'order.create',
    'order.read',
    'order.update',
    'review.create',
    'review.moderate',
    'listing.manage',
    'listing.moderate',
    'bid.create',
    'bid.respond',
    'user.read',
    'user.moderate',
    'user.roles',
    'category.manage',
    'stats.read',
    'notifications.send',
  ],
}

export function can(role, permission) {
  return (P[role] || []).includes(permission)
}

// Fallback for first paint before categories load from the API (mirrors shared/categories.py).
export const FALLBACK_CATEGORIES = [
  { slug: 'vegetables', name: 'Vegetables', emoji: '🥦', color: '#4CAF50' },
  { slug: 'fruits', name: 'Fruits', emoji: '🍉', color: '#F4435E' },
  { slug: 'grains', name: 'Grains & Cereals', emoji: '🌾', color: '#216E39' },
  { slug: 'livestock', name: 'Livestock', emoji: '🐄', color: '#FF758F' },
  { slug: 'poultry', name: 'Poultry', emoji: '🐔', color: '#F4435E' },
  { slug: 'dairy', name: 'Dairy', emoji: '🥛', color: '#4CAF50' },
  { slug: 'fisheries', name: 'Fisheries', emoji: '🐟', color: '#216E39' },
  { slug: 'herbs', name: 'Herbs & Spices', emoji: '🌿', color: '#4CAF50' },
  { slug: 'seeds', name: 'Seeds & Seedlings', emoji: '🌱', color: '#216E39' },
  { slug: 'processed', name: 'Processed Goods', emoji: '🧺', color: '#FF758F' },
]