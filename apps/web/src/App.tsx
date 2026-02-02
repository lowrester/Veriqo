import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Layout } from '@/components/layout/Layout'
import { LoginPage } from '@/features/auth/LoginPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { JobsPage } from '@/features/jobs/JobsPage'
import { JobDetailPage } from '@/features/jobs/JobDetailPage'
import { NewJobPage } from '@/features/jobs/NewJobPage'
import { UsersPage } from '@/features/users/UsersPage'
import { NewUserPage } from '@/features/users/NewUserPage'
import { UserDetailPage } from '@/features/users/UserDetailPage'
import { AdminPage } from '@/features/admin/AdminPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="jobs/new" element={<NewJobPage />} />
        <Route path="jobs/:id" element={<JobDetailPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="users/new" element={<NewUserPage />} />
        <Route path="users/:id" element={<UserDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
