import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileText, Loader2, Plus } from 'lucide-react'
import { api } from '@/api/client'
import { Report } from '@/types'
import { ReportList } from './components/ReportList'

interface Job {
    id: string
    serial_number: string
    device_platform: string
    device_model: string
}

export function ReportsPage() {
    const { id: jobId } = useParams<{ id: string }>()
    const queryClient = useQueryClient()
    const [generating, setGenerating] = useState(false)

    // Fetch job details
    const { data: job, isLoading: jobLoading } = useQuery<Job>({
        queryKey: ['job', jobId],
        queryFn: () => api.get(`/jobs/${jobId}`),
        enabled: !!jobId,
    })

    // Fetch reports
    const { data: reports = [], isLoading: reportsLoading } = useQuery<Report[]>({
        queryKey: ['job', jobId, 'reports'],
        queryFn: () => api.get(`/jobs/${jobId}/reports`),
        enabled: !!jobId,
    })

    // Generate Report Mutation
    const generateMutation = useMutation({
        mutationFn: ({ scope, variant }: { scope: string; variant: string }) =>
            api.post(`/jobs/${jobId}/reports`, { scope, variant }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', jobId, 'reports'] })
            setGenerating(false)
        },
        onError: () => {
            setGenerating(false)
            alert('Could not generate report. Please try again.')
        },
    })

    const handleGenerate = (variant: 'standard' | 'detailed') => {
        setGenerating(true)
        generateMutation.mutate({ scope: 'public', variant })
    }

    if (jobLoading || !job) {
        return <div className="text-center py-12">Loading...</div>
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link to="/dashboard" className="btn-secondary">
                    <ArrowLeft className="w-4 h-4" />
                </Link>
                <div className="flex-1">
                    <div className="flex items-center gap-2">
                        <span className="badge-green text-xs uppercase tracking-wider">Reports</span>
                        <span className="text-gray-400">/</span>
                        <span className="font-mono text-gray-600 font-medium">{job.serial_number}</span>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 mt-1">
                        {job.device_platform} {job.device_model}
                    </h1>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Generator Card */}
                <div className="card h-fit">
                    <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Plus className="w-4 h-4" />
                        New Report
                    </h2>
                    <div className="space-y-3">
                        <button
                            onClick={() => handleGenerate('standard')}
                            disabled={generating}
                            className="w-full btn-white justify-between group"
                        >
                            <div className="text-left">
                                <p className="font-medium text-gray-900">Standard</p>
                                <p className="text-xs text-gray-500">Test results and summary</p>
                            </div>
                            {generating ? (
                                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                            ) : (
                                <FileText className="w-4 h-4 text-gray-400 group-hover:text-blue-600" />
                            )}
                        </button>

                        <button
                            onClick={() => handleGenerate('detailed')}
                            disabled={generating}
                            className="w-full btn-white justify-between group"
                        >
                            <div className="text-left">
                                <p className="font-medium text-gray-900">Detailed</p>
                                <p className="text-xs text-gray-500">Includes all evidence and logs</p>
                            </div>
                            {generating ? (
                                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                            ) : (
                                <FileText className="w-4 h-4 text-gray-400 group-hover:text-blue-600" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Existing Reports List */}
                <div className="md:col-span-2">
                    <div className="card">
                        <h2 className="font-semibold text-gray-900 mb-4">Generated Reports</h2>

                        <ReportList reports={reports} isLoading={reportsLoading} />
                    </div>
                </div>
            </div>
        </div>
    )
}
