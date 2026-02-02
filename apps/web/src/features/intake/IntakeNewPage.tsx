import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '@/api/client'
import { ArrowLeft, Save } from 'lucide-react'
import { Link } from 'react-router-dom'

export function IntakeNewPage() {
    const navigate = useNavigate()
    const [formData, setFormData] = useState({
        serial_number: '',
        platform: '',
        model: '',
        customer_reference: '',
        batch_id: '',
        condition_notes: '',
    })

    const createMutation = useMutation({
        mutationFn: (data: typeof formData) => api.post('/jobs', data),
        onSuccess: (job: any) => {
            navigate(`/job/${job.id}/run`)
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        createMutation.mutate(formData)
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="flex items-center gap-4">
                <Link to="/dashboard" className="btn-secondary">
                    <ArrowLeft className="w-4 h-4" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Skapa nytt jobb</h1>
                    <p className="text-gray-500 mt-1">Registrera enhet och starta verifiering</p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="card space-y-4">
                <div>
                    <label className="label">Serienummer *</label>
                    <input
                        type="text"
                        required
                        value={formData.serial_number}
                        onChange={(e) =>
                            setFormData({ ...formData, serial_number: e.target.value })
                        }
                        className="input"
                        placeholder="t.ex. ABC123456"
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="label">Plattform *</label>
                        <select
                            required
                            value={formData.platform}
                            onChange={(e) =>
                                setFormData({ ...formData, platform: e.target.value })
                            }
                            className="input"
                        >
                            <option value="">Välj plattform</option>
                            <option value="playstation">PlayStation</option>
                            <option value="xbox">Xbox</option>
                            <option value="nintendo">Nintendo</option>
                        </select>
                    </div>

                    <div>
                        <label className="label">Modell *</label>
                        <input
                            type="text"
                            required
                            value={formData.model}
                            onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                            className="input"
                            placeholder="t.ex. PS5 Digital"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="label">Kundreferens</label>
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
                        <label className="label">Batch-ID</label>
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
                    <label className="label">Skicknot vid intag</label>
                    <textarea
                        value={formData.condition_notes}
                        onChange={(e) =>
                            setFormData({ ...formData, condition_notes: e.target.value })
                        }
                        className="input"
                        rows={3}
                        placeholder="Beskriv enhetens skick..."
                    />
                </div>

                <div className="flex gap-3 pt-4">
                    <button
                        type="submit"
                        disabled={createMutation.isPending}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Save className="w-4 h-4" />
                        {createMutation.isPending ? 'Skapar...' : 'Skapa jobb'}
                    </button>
                    <Link to="/dashboard" className="btn-secondary">
                        Avbryt
                    </Link>
                </div>

                {createMutation.isError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                        Ett fel uppstod. Försök igen.
                    </div>
                )}
            </form>
        </div>
    )
}
