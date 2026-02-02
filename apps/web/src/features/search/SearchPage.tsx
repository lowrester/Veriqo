import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search as SearchIcon, Loader2 } from 'lucide-react'
import { api } from '@/api/client'
import { formatDate } from '@/types'

export function SearchPage() {
    const [searchTerm, setSearchTerm] = useState('')
    const [debouncedTerm, setDebouncedTerm] = useState('')

    // Debounce search
    const handleSearch = (value: string) => {
        setSearchTerm(value)
        setTimeout(() => setDebouncedTerm(value), 300)
    }

    const { data: results = [], isLoading } = useQuery<any[]>({
        queryKey: ['search', debouncedTerm],
        queryFn: () => api.get(`/jobs?search=${debouncedTerm}`),
        enabled: debouncedTerm.length >= 3,
    })

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Sök jobb</h1>
                <p className="text-gray-500 mt-1">
                    Sök efter serienummer, batch-ID eller kundreferens
                </p>
            </div>

            {/* Search input */}
            <div className="card">
                <div className="relative">
                    <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => handleSearch(e.target.value)}
                        placeholder="Ange minst 3 tecken..."
                        className="input pl-10 w-full"
                    />
                </div>
            </div>

            {/* Results */}
            {isLoading && debouncedTerm.length >= 3 && (
                <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                </div>
            )}

            {!isLoading && debouncedTerm.length >= 3 && results.length === 0 && (
                <div className="card text-center py-12">
                    <SearchIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">Inga resultat hittades</p>
                </div>
            )}

            {!isLoading && results.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">
                        {results.length} resultat
                    </h2>
                    <div className="space-y-2">
                        {results.map((job: any) => (
                            <Link
                                key={job.id}
                                to={`/job/${job.id}/run`}
                                className="flex items-center justify-between p-3 -mx-3 rounded-lg hover:bg-gray-50 transition-colors"
                            >
                                <div>
                                    <p className="font-medium text-gray-900">{job.serial_number}</p>
                                    <p className="text-sm text-gray-500">
                                        {job.device_platform} {job.device_model}
                                    </p>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className={`badge-${job.status}`}>{job.status}</span>
                                    <span className="text-sm text-gray-500">
                                        {formatDate(job.created_at)}
                                    </span>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
