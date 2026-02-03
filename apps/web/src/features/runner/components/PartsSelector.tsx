import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import { Plus, Package } from 'lucide-react'

// Types (Should ideally be in local types file or shared)
export interface Part {
    id: string
    sku: string
    name: string
    quantity_on_hand: number
}

export interface PartUsage {
    id: string
    part: Part
    quantity: number
}

interface PartsSelectorProps {
    jobId: string
    partsUsed: PartUsage[]
    onPartAdded: () => void
}

export function PartsSelector({ jobId, partsUsed, onPartAdded }: PartsSelectorProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [selectedPartId, setSelectedPartId] = useState('')
    const [quantity, setQuantity] = useState(1)

    // Fetch available parts
    const { data: parts = [] } = useQuery<Part[]>({
        queryKey: ['parts'],
        queryFn: () => api.get('/parts'),
        enabled: isOpen,
    })

    const addPartMutation = useMutation({
        mutationFn: () => api.post(`/parts/use?job_id=${jobId}`, {
            part_id: selectedPartId,
            quantity: Number(quantity)
        }),
        onSuccess: () => {
            setIsOpen(false)
            setSelectedPartId('')
            setQuantity(1)
            onPartAdded()
        }
    })

    return (
        <div className="bg-bg-primary rounded-lg shadow-sm border border-border p-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                    <Package className="w-5 h-5 text-text-secondary" />
                    Parts Used
                </h3>
                <button
                    onClick={() => setIsOpen(true)}
                    className="btn-secondary text-sm flex items-center gap-1"
                >
                    <Plus className="w-3 h-3" /> Add Part
                </button>
            </div>

            {partsUsed.length === 0 ? (
                <p className="text-text-secondary text-sm italic">No parts recorded for this job.</p>
            ) : (
                <div className="space-y-2">
                    {partsUsed.map((usage) => (
                        <div key={usage.id} className="flex items-center justify-between bg-bg-secondary p-2 rounded border border-border">
                            <div>
                                <div className="font-medium text-text-primary">{usage.part.name}</div>
                                <div className="text-xs text-text-secondary">SKU: {usage.part.sku}</div>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-sm font-semibold text-text-primary">x{usage.quantity}</span>
                                {/* Delete/Return part logic could go here */}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {isOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-bg-primary rounded-lg p-6 w-full max-w-md shadow-xl border border-border">
                        <h3 className="text-lg font-bold mb-4 text-text-primary">Add Part</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Part</label>
                                <select
                                    className="input w-full"
                                    value={selectedPartId}
                                    onChange={(e) => setSelectedPartId(e.target.value)}
                                >
                                    <option value="">Select a part...</option>
                                    {parts.map(part => (
                                        <option key={part.id} value={part.id} disabled={part.quantity_on_hand < 1}>
                                            {part.name} ({part.quantity_on_hand} in stock)
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Quantity</label>
                                <input
                                    type="number"
                                    min="1"
                                    className="input w-full"
                                    value={quantity}
                                    onChange={(e) => setQuantity(Number(e.target.value))}
                                />
                            </div>

                            <div className="flex justify-end gap-2 pt-2">
                                <button className="btn-secondary" onClick={() => setIsOpen(false)}>Cancel</button>
                                <button
                                    className="btn-primary"
                                    disabled={!selectedPartId || addPartMutation.isPending}
                                    onClick={() => addPartMutation.mutate()}
                                >
                                    {addPartMutation.isPending ? 'Adding...' : 'Add Part'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
