import { Plus } from 'lucide-react'

// Placeholder for DeviceTypesPage - will communicate with backend /devices
export function DeviceTypesPage() {
    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Enhetstyper</h1>
                    <p className="text-gray-500 mt-1">Hantera plattformar och modeller</p>
                </div>
                <button className="btn-primary flex items-center gap-2">
                    <Plus className="w-4 h-4" />
                    Ny Enhetstyp
                </button>
            </div>

            <div className="card text-center py-12">
                <p className="text-gray-500">Kommer snart: Enhetshantering</p>
            </div>
        </div>
    )
}
