import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { statsApi } from '@/features/stats/statsService'
import { useAuthStore } from '@/stores/authStore'
import { STATUS_LABELS, formatDate } from '@/types'
import {
  Clipboard,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  ArrowRight,
  TrendingUp,
  RotateCw
} from 'lucide-react'

export function DashboardPage() {
  const user = useAuthStore((state) => state.user)

  const { data: dashboardData, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: statsApi.getDashboardStats,
    refetchInterval: 30000, // Poll every 30 seconds
  })

  // Default empty state
  const stats = dashboardData?.counts || { total: 0, in_progress: 0, completed: 0, failed: 0 }
  const metrics = dashboardData?.metrics || { yield_rate: 0 }
  const recentJobs = dashboardData?.recent_activity || []

  return (
    <div className="space-y-6">
      {/* Welcome & Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Welcome, {user?.full_name}
          </h1>
          <p className="text-gray-500 dark:text-gray-400">Here is your overview for today.</p>
        </div>
        <button
          onClick={() => refetch()}
          className={`p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-all ${isRefetching ? 'animate-spin' : ''}`}
          title="Refresh Data"
        >
          <RotateCw className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={Clipboard}
          label="Total Jobs"
          value={stats.total}
          color="blue"
        />
        <StatCard
          icon={Clock}
          label="In Progress"
          value={stats.in_progress}
          color="yellow"
        />
        <StatCard
          icon={CheckCircle}
          label="Completed"
          value={stats.completed}
          color="green"
        />
        <StatCard
          icon={AlertCircle}
          label="Failed"
          value={stats.failed}
          color="red"
        />
        <StatCard
          icon={TrendingUp}
          label="Pass Rate"
          value={`${metrics.yield_rate}%`}
          color="purple"
        />
      </div>

      {/* Quick actions */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/jobs/new" className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Job
          </Link>
          <Link to="/jobs" className="btn-secondary flex items-center gap-2">
            View All Jobs
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900 dark:text-gray-100">Recent Activity</h2>
          <Link
            to="/jobs"
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            View All
          </Link>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : recentJobs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No activity yet.{' '}
            <Link to="/jobs/new" className="text-blue-600 hover:underline">
              Start processing
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {recentJobs.map((job) => (
              <Link
                key={job.id}
                to={`/job/${job.id}/run`}
                className="flex items-center justify-between p-3 -mx-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-full">
                    <Clock className="w-4 h-4 text-gray-500" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 dark:text-gray-200">
                      {job.serial_number}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {job.platform} {job.model}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`badge-${job.status}`}>
                    {STATUS_LABELS[job.status as keyof typeof STATUS_LABELS] || job.status}
                  </span>
                  <span className="text-sm text-gray-500 hidden sm:block">
                    {formatDate(job.updated_at)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}


function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType
  label: string
  value: number | string
  color: 'blue' | 'yellow' | 'green' | 'red' | 'purple'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        </div>
      </div>
    </div>
  )
}
