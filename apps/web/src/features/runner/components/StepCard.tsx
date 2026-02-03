import { useState } from 'react'
import { Check, X, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react'
import { EvidenceUploader } from './EvidenceUploader'
import { EvidenceGallery } from './EvidenceGallery'

interface TestStep {
    id: string
    name: string
    description?: string
    is_mandatory: boolean
    requires_evidence: boolean
    status?: 'pass' | 'fail' | 'skip' | 'pending'
    notes?: string
}

interface StepCardProps {
    step: TestStep
    onResult: (status: 'pass' | 'fail' | 'skip', notes?: string) => void
    onUploadEvidence: (file: File) => Promise<void>
    evidence: any[]
}

export function StepCard({ step, onResult, onUploadEvidence, evidence }: StepCardProps) {
    const [expanded, setExpanded] = useState(true)
    const [notes, setNotes] = useState(step.notes || '')

    const statusColors = {
        pass: 'bg-green-50 border-green-200 dark:bg-green-900/10 dark:border-green-900/30',
        fail: 'bg-red-50 border-red-200 dark:bg-red-900/10 dark:border-red-900/30',
        skip: 'bg-gray-50 border-border dark:bg-gray-800/50',
        pending: 'bg-bg-primary border-border',
    }

    return (
        <div className={`card border-2 ${statusColors[step.status || 'pending']} transition-all`}>
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step.status === 'pass' ? 'bg-green-600 text-white' :
                        step.status === 'fail' ? 'bg-red-600 text-white' :
                            'bg-gray-200 text-gray-600'
                        }`}>
                        {step.status === 'pass' ? <Check className="w-5 h-5" /> :
                            step.status === 'fail' ? <X className="w-5 h-5" /> :
                                <span className="font-bold">{step.name.charAt(0)}</span>}
                    </div>
                    <div>
                        <h3 className="font-semibold text-text-primary">{step.name}</h3>
                        {step.is_mandatory && <span className="text-xs text-red-600 font-medium">Obligatorisk</span>}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {expanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                </div>
            </div>

            {expanded && (
                <div className="mt-4 space-y-4 border-t border-gray-200/50 pt-4">
                    {step.description && (
                        <p className="text-text-secondary text-sm">{step.description}</p>
                    )}

                    {step.requires_evidence && (
                        <div className="bg-blue-50 p-3 rounded-lg border border-blue-100 dark:bg-blue-900/20 dark:border-blue-900/30">
                            <div className="flex items-center gap-2 text-blue-800 mb-2">
                                <AlertCircle className="w-4 h-4" />
                                <span className="text-sm font-medium text-blue-800 dark:text-blue-300">Bevis krävs för detta steg</span>
                            </div>
                            <EvidenceUploader onUpload={onUploadEvidence} />
                            <div className="mt-3">
                                <EvidenceGallery items={evidence} />
                            </div>
                        </div>
                    )}

                    <div className="flex gap-4">
                        <div className="flex-1">
                            <textarea
                                placeholder="Noteringar (valfritt vid godkännande)"
                                className="input w-full text-sm"
                                rows={2}
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                            />
                        </div>
                        <div className="flex flex-col gap-2">
                            <button
                                onClick={() => onResult('pass', notes)}
                                className={`btn flex items-center gap-2 justify-center ${step.status === 'pass'
                                    ? 'bg-green-600 text-white hover:bg-green-700'
                                    : 'bg-bg-primary border border-border text-text-secondary hover:bg-green-50 hover:text-green-700 hover:border-green-200 dark:hover:bg-green-900/20 dark:hover:text-green-400'
                                    }`}
                            >
                                <Check className="w-4 h-4" />
                                Godkänn
                            </button>
                            <button
                                onClick={() => onResult('fail', notes)}
                                className={`btn flex items-center gap-2 justify-center ${step.status === 'fail'
                                    ? 'bg-red-600 text-white hover:bg-red-700'
                                    : 'bg-bg-primary border border-border text-text-secondary hover:bg-red-50 hover:text-red-700 hover:border-red-200 dark:hover:bg-red-900/20 dark:hover:text-red-400'
                                    }`}
                            >
                                <X className="w-4 h-4" />
                                Underkänn
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
