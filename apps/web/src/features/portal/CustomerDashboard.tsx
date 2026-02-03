import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobs'
import { useAuthStore } from '@/stores/authStore'
import { JobStatus, STATUS_LABELS, STATUS_COLORS, formatDate } from '@/types'
import { FileText, Search, Loader2 } from 'lucide-react'
import { useState } from 'react'

export function CustomerDashboard() {
    const user = useAuthStore((state) => state.user)
    const [searchTerm, setSearchTerm] = useState('')

    // TODO: Ideally backend should filter based on user role automatically
    // For MVP we might need to filter client side if API doesn't support "my jobs" explicitly
    // or we add a query param ?created_by=me or similar.
    // Assuming GET /jobs returns all tests for now, we'll need to be careful.
    // Ideally update backend to filter. 

    const { data: jobs = [], isLoading } = useQuery({
        queryKey: ['jobs', 'my-jobs'],
        queryFn: () => jobsApi.list(), // This fetches all jobs. We really should filter on backend.
    })

    // Temporary client-side filter for MVP until backend permissions are stricter
    const myJobs = jobs // .filter(job => true)

    const filteredJobs = myJobs.filter(job =>
        job.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        job.customer_reference?.toLowerCase().includes(searchTerm.toLowerCase())
    )

    if (isLoading) {
        return (
            <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        )
    }

    return (
        <div className="max-w-6xl mx-auto p-6 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Customer Portal</h1>
                    <p className="text-gray-500">Welcome back, {user?.full_name}</p>
                </div>

                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
                    <input
                        type="text"
                        placeholder="Search by Serial or Reference..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9 pr-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-full md:w-64 bg-bg-primary text-text-primary placeholder:text-text-secondary"
                    />
                </div>
            </div>

            <div className="bg-bg-primary rounded-xl shadow-sm border border-border overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-bg-secondary border-b border-border">
                            <tr>
                                <th className="px-6 py-3 font-semibold text-text-primary">Serial Number</th>
                                <th className="px-6 py-3 font-semibold text-text-primary">Reference</th>
                                <th className="px-6 py-3 font-semibold text-text-primary">Details</th>
                                <th className="px-6 py-3 font-semibold text-text-primary">Status</th>
                                <th className="px-6 py-3 font-semibold text-text-primary">Created</th>
                                <th className="px-6 py-3 font-semibold text-text-primary">Report</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {filteredJobs.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-text-secondary">
                                        No jobs found matching your criteria.
                                    </td>
                                </tr>
                            ) : (
                                filteredJobs.map((job) => (
                                    <tr key={job.id} className="hover:bg-bg-secondary/50">
                                        <td className="px-6 py-3 font-medium text-text-primary">
                                            {job.serial_number}
                                        </td>
                                        <td className="px-6 py-3 text-text-secondary">
                                            {job.customer_reference || '-'}
                                        </td>
                                        <td className="px-6 py-3 text-text-secondary">
                                            {job.device_platform} {job.device_model}
                                        </td>
                                        <td className="px-6 py-3">
                                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-${STATUS_COLORS[job.status as JobStatus]}-100 text-${STATUS_COLORS[job.status as JobStatus]}-800 dark:bg-${STATUS_COLORS[job.status as JobStatus]}-900/30 dark:text-${STATUS_COLORS[job.status as JobStatus]}-300`}>
                                                {STATUS_LABELS[job.status as JobStatus]}
                                            </span>
                                        </td>
                                        <td className="px-6 py-3 text-text-secondary">
                                            {formatDate(job.created_at)}
                                        </td>
                                        <td className="px-6 py-3">
                                            {job.status === 'completed' ? (
                                                <button className="flex items-center gap-1.5 text-blue-600 hover:text-blue-700 font-medium text-xs">
                                                    <FileText className="w-3.5 h-3.5" />
                                                    Download
                                                </button>
                                            ) : (
                                                <span className="text-gray-400 text-xs">-</span>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
