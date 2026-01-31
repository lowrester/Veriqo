import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { jobsApi } from '@/api/jobs'
import { useAuthStore } from '@/stores/authStore'
import { STATUS_LABELS, formatDate } from '@/types'
import {
  Clipboard,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  ArrowRight,
} from 'lucide-react'

export function DashboardPage() {
  const user = useAuthStore((state) => state.user)

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs', 'recent'],
    queryFn: () => jobsApi.list({ limit: 10 }),
  })

  // Calculate stats
  const stats = {
    total: jobs.length,
    inProgress: jobs.filter((j) =>
      ['intake', 'reset', 'functional', 'qc'].includes(j.status)
    ).length,
    completed: jobs.filter((j) => j.status === 'completed').length,
    failed: jobs.filter((j) => j.status === 'failed').length,
  }

  return (
    <div className="space-y-6">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Välkommen, {user?.full_name}
        </h1>
        <p className="text-gray-500">Här är din översikt för idag.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Clipboard}
          label="Totalt jobb"
          value={stats.total}
          color="blue"
        />
        <StatCard
          icon={Clock}
          label="Pågående"
          value={stats.inProgress}
          color="yellow"
        />
        <StatCard
          icon={CheckCircle}
          label="Klara"
          value={stats.completed}
          color="green"
        />
        <StatCard
          icon={AlertCircle}
          label="Misslyckade"
          value={stats.failed}
          color="red"
        />
      </div>

      {/* Quick actions */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4">Snabbåtgärder</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/jobs/new" className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Nytt jobb
          </Link>
          <Link to="/jobs" className="btn-secondary flex items-center gap-2">
            Visa alla jobb
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Recent jobs */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Senaste jobb</h2>
          <Link
            to="/jobs"
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Visa alla
          </Link>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Laddar...</div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Inga jobb ännu.{' '}
            <Link to="/jobs/new" className="text-blue-600 hover:underline">
              Skapa ett nytt jobb
            </Link>
          </div>
        ) : (
          <div className="space-y-2">
            {jobs.slice(0, 5).map((job) => (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="flex items-center justify-between p-3 -mx-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900">
                      {job.serial_number}
                    </p>
                    <p className="text-sm text-gray-500">
                      {job.device_platform} {job.device_model}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`badge-${job.status}`}>
                    {STATUS_LABELS[job.status as keyof typeof STATUS_LABELS]}
                  </span>
                  <span className="text-sm text-gray-500 hidden sm:block">
                    {formatDate(job.created_at)}
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
  value: number
  color: 'blue' | 'yellow' | 'green' | 'red'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  }

  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  )
}
