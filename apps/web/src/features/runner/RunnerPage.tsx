import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle, Printer } from 'lucide-react'
import { api } from '@/api/client'
import { StepCard } from './components/StepCard'
import { PrintLabelModal } from '../printing/components/PrintLabelModal'
import { useState } from 'react'

// Define types for Job and Step (mock)
interface Job {
    id: string
    serial_number: string
    imei?: string
    device_platform: string
    device_model: string
}

interface Step {
    id: string
    name: string
    status: string
    description?: string
    is_mandatory: boolean
    requires_evidence: boolean
    notes?: string
    evidence?: any[]
    [key: string]: any
}

export function RunnerPage() {
    const { id: jobId } = useParams<{ id: string }>()
    const queryClient = useQueryClient()
    const [showPrintModal, setShowPrintModal] = useState(false)

    // Fetch job details
    const { data: job, isLoading: jobLoading } = useQuery<Job>({
        queryKey: ['job', jobId],
        queryFn: () => api.get(`/jobs/${jobId}`),
        enabled: !!jobId,
    })

    // Fetch test steps for the current station/device
    // Note: This endpoint might need to be created/verified on backend
    const { data: steps = [], isLoading: stepsLoading } = useQuery<Step[]>({
        queryKey: ['job', jobId, 'steps'],
        queryFn: () => api.get(`/jobs/${jobId}/steps`), // Mock endpoint for now
        enabled: !!jobId,
    })

    // Submit result mutation
    const resultMutation = useMutation({
        mutationFn: ({ stepId, status, notes }: { stepId: string, status: string, notes?: string }) =>
            api.post(`/jobs/${jobId}/steps/${stepId}/result`, { status, notes }), // Mock endpoint
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', jobId, 'steps'] })
        }
    })

    // Upload evidence mutation
    const evidenceMutation = useMutation({
        mutationFn: ({ stepId, file }: { stepId: string, file: File }) => {
            const formData = new FormData()
            formData.append('file', file)
            return api.post(`/jobs/${jobId}/steps/${stepId}/evidence`, formData) // Mock endpoint
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', jobId, 'steps'] })
        }
    })

    if (jobLoading || stepsLoading || !job) {
        return <div className="text-center py-12">Loading job data...</div>
    }

    const completedSteps = steps.filter((s) => s.status === 'pass' || s.status === 'fail').length
    const progress = steps.length > 0 ? (completedSteps / steps.length) * 100 : 0

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link to="/dashboard" className="btn-secondary">
                    <ArrowLeft className="w-4 h-4" />
                </Link>
                <div className="flex-1">
                    <div className="flex items-center gap-2">
                        <span className="badge-blue text-xs uppercase tracking-wider">Runner</span>
                        <span className="text-gray-400">/</span>
                        <span className="font-mono text-gray-600 font-medium">
                            {job.serial_number}
                            {job.imei && <span className="text-gray-400 ml-2 text-sm">/ {job.imei}</span>}
                        </span>
                    </div>
                    <h1 className="text-2xl font-bold text-gray-900 mt-1">
                        {job.device_platform} {job.device_model}
                    </h1>
                </div>
                <button
                    onClick={() => setShowPrintModal(true)}
                    className="btn-secondary flex items-center gap-2 mr-2"
                >
                    <Printer className="w-4 h-4" />
                    Print Label
                </button>
                <button className="btn-primary flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    Complete Job
                </button>
            </div>

            {/* Progress */}
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600 font-medium">{completedSteps} of {steps.length} steps complete</span>
                    <span className="text-blue-600 font-bold">{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2.5">
                    <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                    ></div>
                </div>
            </div>

            {/* Steps List */}
            <div className="space-y-4">
                {steps.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                        <p className="text-gray-500">No test steps configured for this device type.</p>
                    </div>
                ) : (
                    steps.map((step) => (
                        <StepCard
                            key={step.id}
                            step={{
                                id: step.id,
                                name: step.name,
                                description: step.description,
                                is_mandatory: step.is_mandatory,
                                requires_evidence: step.requires_evidence,
                                status: step.status as 'pass' | 'fail' | 'skip' | 'pending' | undefined,
                                notes: step.notes
                            }}
                            evidence={step.evidence || []}
                            onResult={(status, notes) => resultMutation.mutate({ stepId: step.id, status, notes })}
                            onUploadEvidence={async (file) => {
                                await evidenceMutation.mutateAsync({ stepId: step.id, file })
                            }}
                        />
                    ))
                )}
            </div>

            {job && (
                <PrintLabelModal
                    isOpen={showPrintModal}
                    onClose={() => setShowPrintModal(false)}
                    context={{
                        id: job.id,
                        serial_number: job.serial_number,
                        imei: job.imei,
                        platform: job.device_platform,
                        model: job.device_model
                    }}
                />
            )}
        </div>
    )
}
