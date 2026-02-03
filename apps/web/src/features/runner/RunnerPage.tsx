import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle, Printer, Clock } from 'lucide-react'
import { api } from '@/api/client'
import { StepCard } from './components/StepCard'
import { PrintLabelModal } from '../printing/components/PrintLabelModal'
import { PartsSelector, type PartUsage } from './components/PartsSelector'
import { useFeatureStore } from '@/stores/featureStore'
import { useState } from 'react'
// Define types for Job and Step (mock)
interface Job {
    id: string
    ticket_id: number
    serial_number: string
    imei?: string
    device_platform: string
    device_model: string
    sla_due_at?: string // ISO date string
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

/**
 * SLATimer Component
 * Displays the time remaining until SLA breach, or time overdue.
 * Handles parsing errors gracefully.
 */
function SLATimer({ dueAt }: { dueAt?: string }) {
    if (!dueAt) return null;

    try {
        const due = new Date(dueAt);
        if (isNaN(due.getTime())) throw new Error("Invalid date");

        const now = new Date();
        const diffMs = due.getTime() - now.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

        const isOverdue = diffMs < 0;
        const isAtRisk = !isOverdue && diffHours < 2;

        let colorClass = "bg-green-100 text-green-800 border-green-200";
        if (isOverdue) colorClass = "bg-red-100 text-red-800 border-red-200";
        else if (isAtRisk) colorClass = "bg-yellow-100 text-yellow-800 border-yellow-200";

        return (
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium border ${colorClass}`} title={`SLA Due: ${due.toLocaleString()}`}>
                <Clock className="w-4 h-4" />
                {isOverdue ? "Overdue by" : "Due in"} {Math.abs(diffHours)}h {Math.abs(diffMinutes)}m
            </div>
        );
    } catch (e) {
        console.warn("Failed to parse SLA date:", dueAt, e);
        return null;
    }
}



export function RunnerPage() {
    const { id: jobId } = useParams<{ id: string }>()
    const queryClient = useQueryClient()
    const [showPrintModal, setShowPrintModal] = useState(false)
    const { features } = useFeatureStore()

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

    // Fetch used parts
    const { data: partsUsed = [] } = useQuery<PartUsage[]>({
        queryKey: ['job-parts', jobId],
        queryFn: () => api.get(`/parts/job/${jobId}`),
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
                        <span className="font-bold text-blue-600">#{job.ticket_id}</span>
                        <span className="text-gray-400">/</span>
                        <span className="font-mono text-gray-600 font-medium">
                            {job.serial_number}
                            {job.imei && <span className="text-gray-400 ml-2 text-sm">/ {job.imei}</span>}
                        </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1">
                        <h1 className="text-2xl font-bold text-gray-900">
                            {job.device_platform} {job.device_model}
                        </h1>
                        {features.sla_management && <SLATimer dueAt={job.sla_due_at} />}
                    </div>
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
            <div className="bg-bg-primary rounded-lg p-4 shadow-sm border border-border">
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

            {/* Parts Selector */}
            {features.inventory_sync && jobId && (
                <div className="mb-6">
                    <PartsSelector
                        jobId={jobId}
                        partsUsed={partsUsed}
                        onPartAdded={() => queryClient.invalidateQueries({ queryKey: ['job-parts', jobId] })}
                    />
                </div>
            )}

            {/* Steps List */}
            <div className="space-y-4">
                {steps.length === 0 ? (
                    <div className="text-center py-12 bg-bg-secondary rounded-lg border border-dashed border-border">
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
