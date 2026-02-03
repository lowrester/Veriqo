import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Save, X, Search } from 'lucide-react'
import { api } from '@/api/client'

interface Device {
    id: string
    platform: string
    model: string
    model_number?: string
    test_config: Record<string, any>
}

export function DeviceTypesPage() {
    const queryClient = useQueryClient()
    const [isCreating, setIsCreating] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [formData, setFormData] = useState({
        platform: '',
        model: '',
        model_number: '',
    })

    // Fetch devices
    const { data: devices = [], isLoading } = useQuery<Device[]>({
        queryKey: ['devices'],
        queryFn: () => api.get('/admin/devices'),
    })

    // Create Device
    const createMutation = useMutation({
        mutationFn: (data: typeof formData) => api.post('/admin/devices', data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['devices'] })
            setIsCreating(false)
            setFormData({ platform: '', model: '', model_number: '' })
        },
    })

    // Delete Device
    const deleteMutation = useMutation({
        mutationFn: (id: string) => api.delete(`/admin/devices/${id}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['devices'] })
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        createMutation.mutate(formData)
    }

    const filteredDevices = devices.filter(d =>
        d.platform.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.model.toLowerCase().includes(searchTerm.toLowerCase())
    )

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Device Types</h1>
                    <p className="text-gray-500 mt-1">Manage platforms and models</p>
                </div>
                <button
                    onClick={() => setIsCreating(true)}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    New Device Type
                </button>
            </div>

            {isCreating && (
                <div className="card border-2 border-orange-100 animate-in slide-in-from-top-2">
                    <h2 className="font-semibold text-gray-900 mb-4">Add New Device Type</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-3 gap-4">
                            <div>
                                <label className="label">Platform</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.platform}
                                    onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                                    className="input"
                                    placeholder="e.g. PlayStation"
                                />
                            </div>
                            <div>
                                <label className="label">Model</label>
                                <input
                                    type="text"
                                    required
                                    value={formData.model}
                                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                                    className="input"
                                    placeholder="e.g. PS5 Digital"
                                />
                            </div>
                            <div>
                                <label className="label">Model Number (Optional)</label>
                                <input
                                    type="text"
                                    value={formData.model_number}
                                    onChange={(e) => setFormData({ ...formData, model_number: e.target.value })}
                                    className="input"
                                    placeholder="e.g. CFI-1000"
                                />
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <button
                                type="submit"
                                disabled={createMutation.isPending}
                                className="btn-primary flex items-center gap-2"
                            >
                                <Save className="w-4 h-4" />
                                Save
                            </button>
                            <button
                                type="button"
                                onClick={() => setIsCreating(false)}
                                className="btn-secondary flex items-center gap-2"
                            >
                                <X className="w-4 h-4" />
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search platform or model..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="input pl-10"
                />
            </div>

            <div className="card p-0 overflow-hidden">
                {isLoading ? (
                    <div className="text-center py-12 text-gray-500">Loading devices...</div>
                ) : filteredDevices.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        {searchTerm ? 'No devices found.' : 'No devices added yet.'}
                    </div>
                ) : (
                    <table className="w-full text-left text-sm">
                        <thead className="bg-bg-secondary text-text-secondary font-medium border-b border-border">
                            <tr>
                                <th className="px-6 py-4">Platform</th>
                                <th className="px-6 py-4">Model</th>
                                <th className="px-6 py-4">Model Number</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {filteredDevices.map((device) => (
                                <tr key={device.id} className="hover:bg-bg-secondary/50 transition-colors group">
                                    <td className="px-6 py-4 font-medium text-gray-900">{device.platform}</td>
                                    <td className="px-6 py-4">{device.model}</td>
                                    <td className="px-6 py-4 text-gray-500 font-mono text-xs">
                                        {device.model_number || '-'}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => {
                                                if (window.confirm('Are you sure you want to delete this device type?')) {
                                                    deleteMutation.mutate(device.id)
                                                }
                                            }}
                                            className="text-gray-400 hover:text-red-500 hover:bg-red-50 p-2 rounded transition-colors opacity-0 group-hover:opacity-100"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
