import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Printer, X, Download } from 'lucide-react'
import { printingApi, LabelTemplate } from './printingService'

interface PrintLabelModalProps {
    isOpen: boolean
    onClose: () => void
    context: {
        id: string
        serial_number: string
        imei?: string
        platform: string
        model: string
    }
}

export function PrintLabelModal({ isOpen, onClose, context }: PrintLabelModalProps) {
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
    const [previewZpl, setPreviewZpl] = useState<string>('')

    // Fetch templates
    const { data: templates, isLoading } = useQuery({
        queryKey: ['label-templates'],
        queryFn: printingApi.getTemplates,
    })

    useEffect(() => {
        if (templates && templates.length > 0 && !selectedTemplateId) {
            // Default to first or designated default
            const def = templates.find((t) => t.is_default) || templates[0]
            setSelectedTemplateId(def.id)
        }
    }, [templates])

    useEffect(() => {
        if (!selectedTemplateId || !templates) return
        const template = templates.find((t) => t.id === selectedTemplateId)
        if (template) {
            const zpl = printingApi.generateZpl(template, {
                serial_number: context.serial_number,
                imei: context.imei,
                platform: context.platform,
                model: context.model,
                id: context.id
            })
            setPreviewZpl(zpl)
        }
    }, [selectedTemplateId, context, templates])

    // Mock print function (Simulating Zebra Browser Print)
    const handlePrint = async () => {
        // Todo: Integrate with Zebra Browser Print SDK
        console.log("Printing ZPL:", previewZpl)
        alert("Sending ZPL to printer (Simulation)\n\n" + previewZpl.substring(0, 100) + "...")
        onClose()
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-lg rounded-xl bg-white dark:bg-gray-800 p-6 shadow-xl border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
                        <Printer className="w-6 h-6" />
                        Print Label
                    </h2>
                    <button onClick={onClose} className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="space-y-4">
                    {/* Template Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Select Template
                        </label>
                        <select
                            value={selectedTemplateId}
                            onChange={(e) => setSelectedTemplateId(e.target.value)}
                            disabled={isLoading}
                            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        >
                            {templates?.map((t) => (
                                <option key={t.id} value={t.id}>
                                    {t.name} ({t.dimensions || 'Unknown size'})
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Preview Area (Mock) */}
                    <div className="rounded-lg bg-gray-100 dark:bg-gray-900 p-4 border border-gray-200 dark:border-gray-700">
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                            ZPL Preview (Raw)
                        </h3>
                        <pre className="text-[10px] font-mono whitespace-pre-wrap text-gray-600 dark:text-gray-400 max-h-32 overflow-y-auto">
                            {previewZpl || "No preview available"}
                        </pre>
                    </div>

                    {/* Context Info */}
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                        Printing for <strong>{context.serial_number}</strong> ({context.platform} {context.model})
                        {context.imei && <span> [IMEI: {context.imei}]</span>}
                    </div>

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 rounded-lg text-gray-700 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600 font-medium transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handlePrint}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-primary text-white hover:bg-brand-secondary font-medium transition-colors shadow-sm"
                        >
                            <Printer className="w-4 h-4" />
                            Print Now
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
