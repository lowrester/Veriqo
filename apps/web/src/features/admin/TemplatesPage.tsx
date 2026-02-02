import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FileText, Save, X, ChevronRight, GripVertical, Trash2 } from 'lucide-react'
import { api } from '@/api/client'

interface Device {
    id: string
    platform: string
    model: string
}

interface TestStep {
    id: string
    name: string
    description?: string
    station_type: string
    sequence_order: number
    is_mandatory: boolean
    requires_evidence: boolean
}

const STATION_TYPES = [
    { value: 'intake', label: 'Intake' },
    { value: 'reset', label: 'Reset' },
    { value: 'functional', label: 'Functional Test' },
    { value: 'qc', label: 'Quality Control' },
]

export function TemplatesPage() {
    const queryClient = useQueryClient()
    const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
    const [selectedStation, setSelectedStation] = useState<string>('functional')
    const [isCreating, setIsCreating] = useState(false)

    const [formData, setFormData] = useState({
        name: '',
        description: '',
        station_type: 'functional',
        sequence_order: 1,
        is_mandatory: true,
        requires_evidence: false,
    })

    // Fetch Devices
    const { data: devices = [] } = useQuery<Device[]>({
        queryKey: ['devices'],
        queryFn: () => api.get('/admin/devices'),
    })

    // Fetch Templates (filtered)
    const { data: templates = [], isLoading } = useQuery<TestStep[]>({
        queryKey: ['templates', selectedDeviceId, selectedStation],
        queryFn: () => api.get(`/admin/templates?device_id=${selectedDeviceId}&station_type=${selectedStation}`),
        enabled: !!selectedDeviceId,
    })

    // Create Template
    const createMutation = useMutation({
        mutationFn: (data: any) => api.post('/admin/templates', { ...data, device_id: selectedDeviceId }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['templates'] })
            setIsCreating(false)
            // Reset form but keep station type
            setFormData({
                name: '',
                description: '',
                station_type: selectedStation,
                sequence_order: (templates?.length || 0) + 1,
                is_mandatory: true,
                requires_evidence: false,
            })
        },
    })

    // Delete Template
    const deleteMutation = useMutation({
        mutationFn: (id: string) => api.delete(`/admin/templates/${id}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['templates'] })
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        createMutation.mutate(formData)
    }

    // Auto-select first device if none selected
    if (!selectedDeviceId && devices.length > 0) {
        setSelectedDeviceId(devices[0].id)
    }

    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Test Templates</h1>
                    <p className="text-gray-500 mt-1">Configure test workflows for devices</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Sidebar: Device Selection */}
                <div className="card p-0 overflow-hidden h-fit">
                    <div className="bg-gray-50 p-4 border-b border-gray-200">
                        <h2 className="font-semibold text-gray-900">Devices</h2>
                    </div>
                    <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
                        {devices.map((device) => (
                            <button
                                key={device.id}
                                onClick={() => setSelectedDeviceId(device.id)}
                                className={`w-full text-left px-4 py-3 text-sm flex items-center justify-between hover:bg-gray-50 transition-colors ${selectedDeviceId === device.id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'
                                    }`}
                            >
                                <span>{device.platform} {device.model}</span>
                                {selectedDeviceId === device.id && <ChevronRight className="w-4 h-4" />}
                            </button>
                        ))}
                        {devices.length === 0 && (
                            <div className="p-4 text-center text-gray-500 text-sm">
                                No devices found. Add types first.
                            </div>
                        )}
                    </div>
                </div>

                {/* Main Content: Steps Editor */}
                <div className="md:col-span-3 space-y-6">
                    {/* Station Tabs */}
                    <div className="flex border-b border-gray-200 space-x-1 overflow-x-auto">
                        {STATION_TYPES.map((type) => (
                            <button
                                key={type.value}
                                onClick={() => {
                                    setSelectedStation(type.value)
                                    // Update form data to match current tab for new entries
                                    setFormData(prev => ({ ...prev, station_type: type.value }))
                                }}
                                className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${selectedStation === type.value
                                        ? 'border-blue-600 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                            >
                                {type.label}
                            </button>
                        ))}
                    </div>

                    {!selectedDeviceId ? (
                        <div className="card py-12 text-center text-gray-500">
                            Select a device to view templates.
                        </div>
                    ) : (
                        <>
                            {/* Toolbar */}
                            <div className="flex justify-end">
                                <button
                                    onClick={() => setIsCreating(true)}
                                    className="btn-primary flex items-center gap-2"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add Step
                                </button>
                            </div>

                            {/* Create Form */}
                            {isCreating && (
                                <div className="card border-2 border-purple-100 animate-in slide-in-from-top-2">
                                    <h3 className="font-semibold text-gray-900 mb-4">Add Test Step</h3>
                                    <form onSubmit={handleSubmit} className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="col-span-2">
                                                <label className="label">Step Name</label>
                                                <input
                                                    type="text"
                                                    required
                                                    value={formData.name}
                                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                                    className="input"
                                                    placeholder="e.g. Check Wi-Fi Connection"
                                                />
                                            </div>
                                            <div className="col-span-2">
                                                <label className="label">Description / Instructions</label>
                                                <textarea
                                                    value={formData.description}
                                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                                    className="input"
                                                    rows={2}
                                                    placeholder="Instructions for the technician..."
                                                />
                                            </div>
                                            <div>
                                                <label className="label">Sequence Order</label>
                                                <input
                                                    type="number"
                                                    required
                                                    value={formData.sequence_order}
                                                    onChange={(e) => setFormData({ ...formData, sequence_order: parseInt(e.target.value) })}
                                                    className="input"
                                                />
                                            </div>
                                            <div className="flex items-center gap-6 pt-6">
                                                <label className="flex items-center gap-2 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={formData.is_mandatory}
                                                        onChange={(e) => setFormData({ ...formData, is_mandatory: e.target.checked })}
                                                        className="w-4 h-4 text-blue-600 rounded"
                                                    />
                                                    <span className="text-sm font-medium text-gray-700">Mandatory</span>
                                                </label>
                                                <label className="flex items-center gap-2 cursor-pointer">
                                                    <input
                                                        type="checkbox"
                                                        checked={formData.requires_evidence}
                                                        onChange={(e) => setFormData({ ...formData, requires_evidence: e.target.checked })}
                                                        className="w-4 h-4 text-blue-600 rounded"
                                                    />
                                                    <span className="text-sm font-medium text-gray-700">Requires Evidence</span>
                                                </label>
                                            </div>
                                        </div>
                                        <div className="flex gap-3 justify-end">
                                            <button
                                                type="button"
                                                onClick={() => setIsCreating(false)}
                                                className="btn-secondary flex items-center gap-2"
                                            >
                                                <X className="w-4 h-4" />
                                                Cancel
                                            </button>
                                            <button
                                                type="submit"
                                                disabled={createMutation.isPending}
                                                className="btn-primary flex items-center gap-2"
                                            >
                                                <Save className="w-4 h-4" />
                                                Save Step
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            )}

                            {/* List */}
                            <div className="space-y-3">
                                {isLoading ? (
                                    <div className="text-center py-8 text-gray-500">Loading templates...</div>
                                ) : templates.length === 0 ? (
                                    <div className="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                                        <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                                        <p className="text-gray-500">No steps defined for this station.</p>
                                    </div>
                                ) : (
                                    templates.map((step) => (
                                        <div
                                            key={step.id}
                                            className="flex items-center p-4 bg-white rounded-lg border border-gray-200 shadow-sm group hover:border-gray-300 transition-all"
                                        >
                                            <div className="text-gray-400 mr-4 cursor-grab active:cursor-grabbing">
                                                <GripVertical className="w-5 h-5" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="badge-gray w-8 h-8 flex items-center justify-center rounded-full">
                                                        {step.sequence_order}
                                                    </span>
                                                    <h3 className="font-medium text-gray-900 truncate">{step.name}</h3>
                                                </div>
                                                {step.description && (
                                                    <p className="text-sm text-gray-500 truncate ml-10">{step.description}</p>
                                                )}
                                                <div className="flex items-center gap-3 mt-2 ml-10">
                                                    {step.is_mandatory && (
                                                        <span className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded border border-red-100">
                                                            Mandatory
                                                        </span>
                                                    )}
                                                    {step.requires_evidence && (
                                                        <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-100">
                                                            Evidence Required
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => {
                                                        if (window.confirm('Delete this test step?')) {
                                                            deleteMutation.mutate(step.id)
                                                        }
                                                    }}
                                                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
