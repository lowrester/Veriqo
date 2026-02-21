import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle, Printer, Clock, RotateCw, ShieldAlert, ShieldCheck, Trash2, FileText, AlertTriangle } from 'lucide-react'
import { api } from '@/api/client'
import { jobsApi } from '@/api/jobs'
import { useToastStore } from '@/stores/toastStore'
import { StepCard } from './components/StepCard'
import { PrintLabelModal } from '../printing/components/PrintLabelModal'
import { PartsSelector, type PartUsage } from './components/PartsSelector'
import { useFeatureStore } from '@/stores/featureStore'
import { useState } from 'react'
interface Job {
    id: string
    ticket_id: number
    serial_number: string
    status: string // Added status
    imei?: string
    device?: {
        brand: string
        device_type: string
        model: string
    }
    sla_due_at?: string // ISO date string
    picea_verify_status?: string
    picea_mdm_locked?: boolean
    picea_erase_confirmed?: boolean
    picea_erase_certificate?: string
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
    const [showManualCompleteModal, setShowManualCompleteModal] = useState(false)
    const [manualReason, setManualReason] = useState('')
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

    const addToast = useToastStore((state) => state.addToast)

    // Submit result mutation
    const resultMutation = useMutation({
        mutationFn: ({ stepId, status, notes }: { stepId: string, status: string, notes?: string }) =>
            api.post(`/jobs/${jobId}/steps/${stepId}/result`, { status, notes }), // Mock endpoint
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', jobId, 'steps'] })
        },
        onError: () => {
            addToast('Kunde inte spara testresultat.', 'error')
        }
    })

    // Upload evidence mutation
    const evidenceMutation = useMutation({
        mutationFn: ({ stepId, file }: { stepId: string, file: File }) => {
            return api.upload(`/jobs/${jobId}/results/${stepId}/evidence`, file)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', jobId, 'steps'] })
            addToast('Fil har laddats upp.', 'success')
        },
        onError: () => {
            addToast('Kunde inte ladda upp fil.', 'error')
        }
    })

    // Picea sync mutation
    const piceaMutation = useMutation({
        mutationFn: () => jobsApi.syncPicea(jobId!),
        onSuccess: (data) => {
            addToast(data.message, 'success')
            queryClient.invalidateQueries({ queryKey: ['job', jobId] })
            queryClient.invalidateQueries({ queryKey: ['job', jobId, 'steps'] })
        },
        onError: () => {
            addToast('Misslyckades att hämta diagnosdata från Picea.', 'error')
        }
    })

    // Transition mutation (for Complete Job)
    const transitionMutation = useMutation({
        mutationFn: (data: { targetStatus: string, isFullyTested?: boolean, reason?: string }) =>
            jobsApi.transition(jobId!, {
                target_status: data.targetStatus,
                is_fully_tested: data.isFullyTested ?? true,
                reason: data.reason
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', jobId] })
            addToast('Jobbet har uppdaterats.', 'success')
            setShowManualCompleteModal(false)
            setManualReason('')
        },
        onError: (error: any) => {
            addToast(`Misslyckades att uppdatera status: ${error.message || 'Okänt fel'}`, 'error')
        }
    })

    if (jobLoading || stepsLoading || !job) {
        return <div className="text-center py-12">Loading job data...</div>
    }

    const completedSteps = steps.filter((s) => s.status === 'pass' || s.status === 'fail').length
    const mandatorySteps = steps.filter((s) => s.is_mandatory)
    const allMandatoryDone = mandatorySteps.every((s) => s.status === 'pass' || s.status === 'fail' || s.status === 'skip')
    const progress = steps.length > 0 ? (completedSteps / steps.length) * 100 : 0

    // Determine next transition
    const getNextStatus = () => {
        const current = job.status
        if (current === 'intake') return 'reset'
        if (current === 'reset') return 'functional'
        if (current === 'functional') return 'qc'
        if (current === 'qc') return 'completed'
        return null
    }

    const nextStatus = getNextStatus()
    const isPiceaSuccess = job.picea_verify_status === 'SUCCESS' && job.picea_erase_confirmed
    const canComplete = allMandatoryDone && nextStatus && !transitionMutation.isPending

    const handleTransition = () => {
        if (!nextStatus) return

        // If it's the final completion and Picea isn't a success, ask for a reason
        if (nextStatus === 'completed' && !isPiceaSuccess) {
            setShowManualCompleteModal(true)
            return
        }

        transitionMutation.mutate({ targetStatus: nextStatus })
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            {/* Picea Security Alerts */}
            {job.picea_mdm_locked && (
                <div className="bg-red-50 border-2 border-red-200 p-4 rounded-xl flex items-center gap-4 animate-pulse">
                    <div className="bg-red-100 p-3 rounded-full text-red-600">
                        <ShieldAlert className="w-8 h-8" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-red-800">MDM LOCK DETECTED</h2>
                        <p className="text-red-700">This device is managed by an external organization. Factory reset may fail or require credentials.</p>
                    </div>
                </div>
            )}

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
                            {job.device?.brand} {job.device?.model}
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
                <button
                    onClick={() => piceaMutation.mutate()}
                    disabled={piceaMutation.isPending}
                    className="btn-secondary flex items-center gap-2 mr-2 border-purple-200 hover:border-purple-300 text-purple-700"
                >
                    <RotateCw className={`w-4 h-4 ${piceaMutation.isPending ? 'animate-spin' : ''}`} />
                    {piceaMutation.isPending ? 'Diagnostics' : 'Fetch diagnostics'}
                </button>
                <button
                    onClick={handleTransition}
                    disabled={!canComplete}
                    className={`btn-primary flex items-center gap-2 ${!canComplete ? 'opacity-50 cursor-not-allowed' : ''}`}
                    title={!allMandatoryDone ? "Alla obligatoriska steg måste vara klara" : ""}
                >
                    <CheckCircle className="w-4 h-4" />
                    {transitionMutation.isPending ? 'Processing...' : nextStatus ? `Finish ${job.status}` : 'Completed'}
                </button>
            </div>

            {/* Diagnostics Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card p-4 flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${job.picea_verify_status === 'SUCCESS' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                        <ShieldCheck className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-xs text-text-secondary uppercase font-bold tracking-wider">Picea Verify</div>
                        <div className="font-bold">{job.picea_verify_status || 'NOT RUN'}</div>
                    </div>
                </div>

                <div className="card p-4 flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${job.picea_erase_confirmed ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                        <Trash2 className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-xs text-text-secondary uppercase font-bold tracking-wider">Data Erasure</div>
                        <div className="font-bold flex items-center gap-2">
                            {job.picea_erase_confirmed ? 'CONFIRMED' : 'REQD'}
                            {job.picea_erase_certificate && (
                                <a href={job.picea_erase_certificate} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800">
                                    <FileText className="w-4 h-4" />
                                </a>
                            )}
                        </div>
                    </div>
                </div>

                <div className="card p-4 flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${job.picea_mdm_locked ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                        <AlertTriangle className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-xs text-text-secondary uppercase font-bold tracking-wider">MDM Status</div>
                        <div className="font-bold">{job.picea_mdm_locked ? 'LOCKED' : 'CLEAN'}</div>
                    </div>
                </div>
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
                        brand: job.device?.brand || 'Unknown',
                        device_type: job.device?.device_type || 'Unknown',
                        model: job.device?.model || 'Unknown'
                    }}
                />
            )}

            {/* Manual Complete Modal */}
            {showManualCompleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
                        <div className="flex items-center gap-3 mb-4 text-amber-600">
                            <ShieldAlert className="w-6 h-6" />
                            <h2 className="text-xl font-bold">Manual Certification</h2>
                        </div>
                        <p className="text-gray-600 mb-6">
                            This unit is missing full Picea verification (Diagnostics or Data Erasure).
                            By proceeding, you certify that manual verification has been completed.
                        </p>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Reason for manual bypass <span className="text-red-500">*</span>
                                </label>
                                <textarea
                                    className="w-full rounded-xl border-gray-200 focus:ring-amber-500 focus:border-amber-500 min-h-[100px]"
                                    placeholder="e.g. Device incompatible with Picea, Sync timeout, etc..."
                                    value={manualReason}
                                    onChange={(e) => setManualReason(e.target.value)}
                                />
                            </div>

                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowManualCompleteModal(false)}
                                    className="flex-1 px-4 py-2.5 rounded-xl border border-gray-200 text-gray-600 font-medium hover:bg-gray-50 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => nextStatus && transitionMutation.mutate({
                                        targetStatus: nextStatus,
                                        isFullyTested: false,
                                        reason: manualReason
                                    })}
                                    disabled={!manualReason.trim() || transitionMutation.isPending}
                                    className="flex-1 px-4 py-2.5 rounded-xl bg-amber-600 text-white font-medium hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {transitionMutation.isPending ? 'Processing...' : 'Certify & Complete'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
