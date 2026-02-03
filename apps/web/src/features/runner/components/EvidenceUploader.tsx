import { useRef, useState } from 'react'
import { Upload, Loader2 } from 'lucide-react'

interface EvidenceUploaderProps {
    onUpload: (file: File) => Promise<void>
}

export function EvidenceUploader({ onUpload }: EvidenceUploaderProps) {
    const fileInputRef = useRef<HTMLInputElement>(null)
    const [isUploading, setIsUploading] = useState(false)

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setIsUploading(true)
        try {
            await onUpload(file)
        } finally {
            setIsUploading(false)
            if (fileInputRef.current) {
                fileInputRef.current.value = ''
            }
        }
    }

    return (
        <div>
            <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept="image/*,video/*"
                onChange={handleFileChange}
            />
            <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center gap-2 px-3 py-2 bg-bg-primary border border-border rounded-lg shadow-sm text-sm font-medium text-text-primary hover:bg-bg-secondary disabled:opacity-50 transition-colors"
            >
                {isUploading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                    <Upload className="w-4 h-4" />
                )}
                {isUploading ? 'Laddar upp...' : 'Ladda upp bevis'}
            </button>
        </div>
    )
}
