import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { ArrowLeft, Save } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PrintLabelModal } from '../printing/components/PrintLabelModal'

export function IntakeNewPage() {
    const navigate = useNavigate()
    const [formData, setFormData] = useState({
        serial_number: '',
        imei: '',
        platform: '',
        model: '',
        customer_reference: '',
        batch_id: '',
        condition_notes: '',
    })
    const [showPrintModal, setShowPrintModal] = useState(false)
    const [createdJob, setCreatedJob] = useState<any>(null)
    const [submitAction, setSubmitAction] = useState<'create' | 'create_print'>('create')

    const createMutation = useMutation({
        mutationFn: (data: typeof formData) => api.post('/jobs', data),
        onSuccess: (job: any) => {
            if (submitAction === 'create_print') {
                setCreatedJob(job)
                setShowPrintModal(true)
            } else {
                navigate(`/job/${job.id}/run`)
            }
        },
    })

    const handleSubmit = (action: 'create' | 'create_print') => (e: React.MouseEvent) => {
        e.preventDefault()
        setSubmitAction(action)
        createMutation.mutate(formData)
    }

    const handlePrintClose = () => {
        setShowPrintModal(false)
        if (createdJob) {
            navigate(`/job/${createdJob.id}/run`)
        }
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Link to="/dashboard" className="btn-secondary">
                    <ArrowLeft className="w-4 h-4" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">New Job Intake</h1>
                    <p className="text-gray-500 dark:text-gray-400 mt-1">Register device and start verification</p>
                </div>
            </div>

            <form className="card space-y-4">
                <div>
                    <label className="label">Serial Number *</label>
                    <input
                        type="text"
                        required
                        value={formData.serial_number}
                        onChange={(e) =>
                            setFormData({ ...formData, serial_number: e.target.value })
                        }
                        className="input"
                        placeholder="e.g. ABC123456"
                    />
                </div>

                <div>
                    <label className="label">IMEI (Mobile/Tablet)</label>
                    <input
                        type="text"
                        value={formData.imei}
                        onChange={(e) =>
                            setFormData({ ...formData, imei: e.target.value })
                        }
                        className="input"
                        placeholder="e.g. 3548..."
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="label">Platform *</label>
                        <select
                            required
                            value={formData.platform}
                            onChange={(e) =>
                                setFormData({ ...formData, platform: e.target.value })
                            }
                            className="input"
                        >
                            <option value="">Select Platform</option>
                            <option value="playstation">PlayStation</option>
                            <option value="xbox">Xbox</option>
                            <option value="nintendo">Nintendo</option>
                            <option value="mobile">Mobile Phone</option>
                            <option value="tablet">Tablet</option>
                        </select>
                    </div>

                    <div>
                        <label className="label">Model *</label>
                        <input
                            type="text"
                            required
                            value={formData.model}
                            onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                            className="input"
                            placeholder="e.g. PS5 Digital"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="label">Customer Reference</label>
                        <input
                            type="text"
                            value={formData.customer_reference}
                            onChange={(e) =>
                                setFormData({ ...formData, customer_reference: e.target.value })
                            }
                            className="input"
                        />
                    </div>

                    <div>
                        <label className="label">Batch ID</label>
                        <input
                            type="text"
                            value={formData.batch_id}
                            onChange={(e) =>
                                setFormData({ ...formData, batch_id: e.target.value })
                            }
                            className="input"
                        />
                    </div>
                </div>

                <div>
                    <label className="label">Condition Notes (Intake)</label>
                    <textarea
                        value={formData.condition_notes}
                        onChange={(e) =>
                            setFormData({ ...formData, condition_notes: e.target.value })
                        }
                        className="input"
                        rows={3}
                        placeholder="Describe initial device condition..."
                    />
                </div>

                <div className="flex gap-3 pt-4">
                    <button
                        type="button"
                        onClick={handleSubmit('create')}
                        disabled={createMutation.isPending}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Save className="w-4 h-4" />
                        {createMutation.isPending && submitAction === 'create' ? 'Creating...' : 'Create Job'}
                    </button>

                    <button
                        type="button"
                        onClick={handleSubmit('create_print')}
                        disabled={createMutation.isPending}
                        className="btn-secondary flex items-center gap-2 border-brand-primary text-brand-primary hover:bg-brand-light"
                    >
                        <Save className="w-4 h-4" />
                        Create & Print Label
                    </button>

                    <Link to="/dashboard" className="btn-secondary ml-auto">
                        Cancel
                    </Link>
                </div>

                {createMutation.isError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                        An error occurred. Please try again.
                    </div>
                )}
            </form>

            {createdJob && (
                <PrintLabelModal
                    isOpen={showPrintModal}
                    onClose={handlePrintClose}
                    context={{
                        id: createdJob.id,
                        serial_number: createdJob.serial_number,
                        imei: createdJob.imei || formData.imei,
                        platform: createdJob.device?.platform || formData.platform,
                        model: createdJob.device?.model || formData.model
                    }}
                />
            )}
        </div>
    )
}
