import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Monitor, Activity, Trash2, Save, X } from 'lucide-react'
import { api } from '@/api/client'
import { formatDate } from '@/types'

interface Station {
    id: string
    name: string
    station_type: 'intake' | 'reset' | 'test' | 'qc'
    is_active: boolean
    last_active_at: string
}

export function StationsPage() {
    const queryClient = useQueryClient()
    const [isCreating, setIsCreating] = useState(false)
    const [formData, setFormData] = useState({
        name: '',
        station_type: 'test',
    })

    // Fetch stations
    const { data: stations = [], isLoading } = useQuery<Station[]>({
        queryKey: ['stations'],
        queryFn: () => api.get('/admin/stations'), // Assuming this endpoint exists/will exist
    })

    // Create Station
    const createMutation = useMutation({
        mutationFn: (data: typeof formData) => api.post('/admin/stations', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['stations'] })
            setIsCreating(false)
            setFormData({ name: '', station_type: 'test' })
        },
    })

    // Delete Station
    const deleteMutation = useMutation({
        mutationFn: (id: string) => api.delete(`/admin/stations/${id}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['stations'] })
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        createMutation.mutate(formData)
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Stationer</h1>
                    <p className="text-gray-500 mt-1">Hantera arbetsstationer och deras roller</p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Ny Station
                </button>
            </div>

            {isCreating && (
                <div className="card border-2 border-blue-100 animate-in slide-in-from-top-2">
                    <h2 className="font-semibold text-gray-900 mb-4">Lägg till ny station</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="label">Stationsnamn</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="input"
                                    placeholder="t.ex. Workbench 1"
                                />
                            </div>
                            <div>
                                <label className="label">Typ</label>
                                <select
                                    required
                                    value={formData.station_type}
                                    onChange={(e) => setFormData({ ...formData, station_type: e.target.value })}
                                    className="input"
                                >
                                    <option value="intake">Intag</option>
                                    <option value="reset">Återställning</option>
                                    <option value="test">Testning</option>
                                    <option value="qc">Kvalitetskontroll</option>
                                </select>
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <button
                                type="submit"
                                disabled={createMutation.isPending}
                                className="btn-primary flex items-center gap-2"
                            >
                                <Save className="w-4 h-4" />
                                Spara
                            </button>
                            <button
                                type="button"
                                onClick={() => setIsCreating(false)}
                                className="btn-secondary flex items-center gap-2"
                            >
                                <X className="w-4 h-4" />
                                Avbryt
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="card">
                {isLoading ? (
                    <div className="text-center py-8 text-gray-500">Laddar stationer...</div>
                ) : stations.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">Inga stationer konfigurerade.</div>
                ) : (
                    <div className="space-y-2">
                        {stations.map((station) => (
                            <div
                                key={station.id}
                                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                            >
                                <div className="flex items-center gap-4">
                                    <div className={`p-2 rounded-lg ${station.is_active ? 'bg-green-100 text-green-600' : 'bg-gray-200 text-gray-400'
                                        }`}>
                                        <Monitor className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-medium text-gray-900">{station.name}</h3>
                                        <div className="flex items-center gap-2 text-sm text-gray-500">
                                            <span className="capitalize">{station.station_type}</span>
                                            <span>•</span>
                                            <span className="flex items-center gap-1">
                                                <Activity className="w-3 h-3" />
                                                Aktiv: {station.last_active_at ? formatDate(station.last_active_at) : 'Aldrig'}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <button
                                    onClick={() => {
                                        if (window.confirm('Är du säker på att du vill ta bort denna station?')) {
                                            deleteMutation.mutate(station.id)
                                        }
                                    }}
                                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
