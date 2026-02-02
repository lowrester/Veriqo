import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, FileText, Download, Loader2, Plus } from 'lucide-react'
import { api } from '@/api/client'
import { formatDate } from '@/types'

interface Report {
    id: string
    scope: string
    variant: string
    generated_at: string
    expires_at: string
    public_url: string
}

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
            alert('Kunde inte generera rapport. Försök igen.')
        },
    })

    const handleGenerate = (variant: 'standard' | 'detailed') => {
        setGenerating(true)
        generateMutation.mutate({ scope: 'public', variant })
    }

    if (jobLoading || !job) {
        return <div className="text-center py-12">Laddar...</div>
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
                        Ny Rapport
                    </h2>
                    <div className="space-y-3">
                        <button
                            onClick={() => handleGenerate('standard')}
                            disabled={generating}
                            className="w-full btn-white justify-between group"
                        >
                            <div className="text-left">
                                <p className="font-medium text-gray-900">Standard</p>
                                <p className="text-xs text-gray-500">Testresultat och sammanfattning</p>
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
                                <p className="font-medium text-gray-900">Detaljerad</p>
                                <p className="text-xs text-gray-500">Inkluderar alla bevis och loggar</p>
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
                        <h2 className="font-semibold text-gray-900 mb-4">Genererade Rapporter</h2>

                        {reportsLoading ? (
                            <div className="text-center py-8 text-gray-500">Laddar rapporter...</div>
                        ) : reports.length === 0 ? (
                            <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                                <p className="text-gray-500">Inga rapporter har skapats ännu.</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {reports.map((report) => (
                                    <div key={report.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100 hover:border-gray-200 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 bg-white rounded border border-gray-200">
                                                <FileText className="w-5 h-5 text-red-500" />
                                            </div>
                                            <div>
                                                <p className="font-medium text-gray-900 capitalize">
                                                    {report.variant} Report
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    {formatDate(report.generated_at)} • {report.scope}
                                                </p>
                                            </div>
                                        </div>

                                        <a
                                            href={report.public_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn-white text-sm flex items-center gap-2"
                                        >
                                            <Download className="w-4 h-4" />
                                            Ladda ner
                                        </a>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
