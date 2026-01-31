import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { jobsApi } from '@/api/jobs'
import { STATUS_LABELS, formatDate, JobStatus } from '@/types'
import { Plus, Search, Filter } from 'lucide-react'

const STATUSES: JobStatus[] = [
  'intake',
  'reset',
  'functional',
  'qc',
  'completed',
  'failed',
  'on_hold',
]

export function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['jobs', statusFilter],
    queryFn: () => jobsApi.list({ status: statusFilter || undefined, limit: 100 }),
  })

  // Filter by search query
  const filteredJobs = jobs.filter(
    (job) =>
      job.serial_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.device_platform?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.device_model?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jobb</h1>
          <p className="text-gray-500">Hantera alla verifieringsjobb</p>
        </div>
        <Link to="/jobs/new" className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Nytt jobb
        </Link>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Sök serienummer, plattform..."
              className="input pl-10"
            />
          </div>

          {/* Status filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input pl-10 pr-8 appearance-none"
            >
              <option value="">Alla statusar</option>
              {STATUSES.map((status) => (
                <option key={status} value={status}>
                  {STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Jobs list */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Laddar jobb...</div>
        ) : filteredJobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            {searchQuery || statusFilter
              ? 'Inga jobb matchar dina filter'
              : 'Inga jobb ännu'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                    Serienummer
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-500 hidden sm:table-cell">
                    Enhet
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                    Status
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-500 hidden md:table-cell">
                    Tekniker
                  </th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-gray-500 hidden lg:table-cell">
                    Skapad
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredJobs.map((job) => (
                  <tr
                    key={job.id}
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/jobs/${job.id}`}
                        className="font-medium text-blue-600 hover:text-blue-700"
                      >
                        {job.serial_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">
                      {job.device_platform} {job.device_model}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge-${job.status}`}>
                        {STATUS_LABELS[job.status as JobStatus]}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                      {job.assigned_technician_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 hidden lg:table-cell">
                      {formatDate(job.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
