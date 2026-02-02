import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { AppShell } from '@/components/layout/AppShell'
import { RequireRole } from '@/components/guards/RequireRole'
import { LoginPage } from '@/features/auth/LoginPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { JobsPage } from '@/features/jobs/JobsPage'
import { JobDetailPage } from '@/features/jobs/JobDetailPage'
import { NewJobPage } from '@/features/jobs/NewJobPage'
import { RunnerPage } from '@/features/runner/RunnerPage'
import { QcPage } from '@/features/qc/QcPage'
import { ReportsPage } from '@/features/reports/ReportsPage'
import { IntakeNewPage } from '@/features/intake/IntakeNewPage'
import { SearchPage } from '@/features/search/SearchPage'
import { OpsPage } from '@/features/ops/OpsPage'
import { UsersPage } from '@/features/users/UsersPage'
import { NewUserPage } from '@/features/users/NewUserPage'
import { UserDetailPage } from '@/features/users/UserDetailPage'
import { AdminPage } from '@/features/admin/AdminPage'
import { StationsPage } from '@/features/admin/StationsPage'
import { TemplatesPage } from '@/features/admin/TemplatesPage'
import { DeviceTypesPage } from '@/features/admin/DeviceTypesPage'

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
        path="/*"
        element={
          <PrivateRoute>
            <AppShell />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<DashboardPage />} />

        {/* Jobs */}
        <Route path="jobs" element={<JobsPage />} />
        <Route path="jobs/new" element={<NewJobPage />} />
        <Route path="jobs/:id" element={<JobDetailPage />} />

        {/* Workflow */}
        <Route
          path="intake/new"
          element={
            <RequireRole anyOf={['admin', 'supervisor', 'technician']}>
              <IntakeNewPage />
            </RequireRole>
          }
        />
        <Route
          path="job/:id/run"
          element={
            <RequireRole anyOf={['admin', 'supervisor', 'technician']}>
              <RunnerPage />
            </RequireRole>
          }
        />
        <Route
          path="job/:id/qc"
          element={
            <RequireRole anyOf={['admin', 'supervisor']}>
              <QcPage />
            </RequireRole>
          }
        />
        <Route
          path="job/:id/reports"
          element={
            <RequireRole anyOf={['admin', 'supervisor', 'technician', 'viewer']}>
              <ReportsPage />
            </RequireRole>
          }
        />

        {/* Search & Ops */}
        <Route path="search" element={<SearchPage />} />
        <Route
          path="ops"
          element={
            <RequireRole anyOf={['admin', 'supervisor']}>
              <OpsPage />
            </RequireRole>
          }
        />

        {/* Admin */}
        <Route path="admin" element={<AdminPage />} />
        <Route path="admin/stations" element={<StationsPage />} />
        <Route path="admin/templates" element={<TemplatesPage />} />
        <Route path="admin/devices" element={<DeviceTypesPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="users/new" element={<NewUserPage />} />
        <Route path="users/:id" element={<UserDetailPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
