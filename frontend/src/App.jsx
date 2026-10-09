import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './lib/auth'
import { ToastProvider } from './lib/toast'
import { ProtectedRoute, RoleRoute } from './components/layout/Guards'
import AppLayout from './components/layout/AppLayout'
import AdminLayout from './components/layout/AdminLayout'
import Home from './pages/Home'
import Listings from './pages/Listings'
import ListingDetail from './pages/ListingDetail'
import NewListing from './pages/NewListing'
import EditListing from './pages/EditListing'
import MyListings from './pages/MyListings'
import Orders from './pages/Orders'
import Favorites from './pages/Favorites'
import Inbox from './pages/Inbox'
import Profile from './pages/Profile'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'
import Dashboard from './pages/admin/Dashboard'
import AdminUsers from './pages/admin/Users'
import Moderation from './pages/admin/Moderation'
import AdminCategories from './pages/admin/Categories'

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Home />} />
              <Route path="/listings" element={<Listings />} />
              <Route path="/listings/:id" element={<ListingDetail />} />
              <Route path="/u/:id" element={<Profile />} />

              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              <Route path="/me" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              <Route path="/sell" element={<ProtectedRoute><NewListing /></ProtectedRoute>} />
              <Route path="/sell/:id/edit" element={<ProtectedRoute><EditListing /></ProtectedRoute>} />
              <Route path="/mylistings" element={<ProtectedRoute><MyListings /></ProtectedRoute>} />
              <Route path="/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
              <Route path="/favorites" element={<ProtectedRoute><Favorites /></ProtectedRoute>} />
              <Route path="/inbox" element={<ProtectedRoute><Inbox /></ProtectedRoute>} />
            </Route>

            <Route
              path="/admin"
              element={
                <RoleRoute role={['admin', 'moderator']}>
                  <AdminLayout />
                </RoleRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="listings" element={<Moderation />} />
              <Route path="categories" element={<AdminCategories />} />
            </Route>

            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  )
}