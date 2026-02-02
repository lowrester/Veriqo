import { Plus } from 'lucide-react'

// Placeholder for TemplatesPage - will communicate with backend /templates
export function TemplatesPage() {
    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Testmallar</h1>
                    <p className="text-gray-500 mt-1">Skapa och redigera testflöden</p>
                </div>
                <button className="btn-primary flex items-center gap-2">
                    <Plus className="w-4 h-4" />
                    Ny Mall
                </button>
            </div>

            <div className="card text-center py-12">
                <p className="text-gray-500">Kommer snart: Mallbyggare</p>
            </div>
        </div>
    )
}
