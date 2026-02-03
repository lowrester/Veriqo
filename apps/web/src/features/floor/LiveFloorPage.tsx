import { useQuery } from '@tanstack/react-query'
import { statsApi } from '@/features/stats/statsService'
import { STATUS_LABELS, formatDate } from '@/types'
import { RotateCw, Monitor, Gamepad2, Box } from 'lucide-react'
import { Link } from 'react-router-dom'

export function LiveFloorPage() {
    const { data: stations = [], isLoading, refetch, isRefetching } = useQuery({
        queryKey: ['stats', 'floor'],
        queryFn: statsApi.getFloorStatus,
        refetchInterval: 15000, // Poll every 15 seconds for live view
    })

    const getStationIcon = (type: string) => {
        switch (type) {
            case 'intake': return <Box className="w-4 h-4" />
            case 'functional': return <Gamepad2 className="w-4 h-4" />
            case 'qc': return <Monitor className="w-4 h-4" />
            default: return <Box className="w-4 h-4" />
        }
    }

    if (isLoading && stations.length === 0) {
        return <div className="p-12 text-center text-gray-500">Loading floor status...</div>
    }

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <Monitor className="w-6 h-6 text-brand-primary" />
                        Live Floor View
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400">Real-time device tracking across stations</p>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-400 font-mono">
                        Auto-refresh: 15s
                    </span>
                    <button
                        onClick={() => refetch()}
                        className={`p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-all ${isRefetching ? 'animate-spin' : ''}`}
                        title="Refresh Now"
                    >
                        <RotateCw className="w-5 h-5 text-gray-500" />
                    </button>
                </div>
            </div>

            {/* Kanban Board Container */}
            <div className="flex-1 overflow-x-auto overflow-y-hidden pb-4">
                <div className="flex h-full gap-4 min-w-max px-1">
                    {stations.map((station: any) => (
                        <div
                            key={station.id}
                            className="w-80 flex flex-col bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700"
                        >
                            {/* Column Header */}
                            <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-t-xl sticky top-0">
                                <div className="flex items-center justify-between mb-1">
                                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                                        {getStationIcon(station.type)}
                                        {station.name}
                                    </h3>
                                    <span className="badge-gray text-xs">
                                        {station.jobs.length}
                                    </span>
                                </div>
                                <div className="w-full bg-gray-200 dark:bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                                    <div className={`h-full ${station.jobs.length > 0 ? 'bg-brand-primary' : 'bg-transparent'} w-full opacity-50`} />
                                </div>
                            </div>

                            {/* Job Cards */}
                            <div className="flex-1 p-2 overflow-y-auto space-y-2 custom-scrollbar">
                                {station.jobs.length === 0 ? (
                                    <div className="text-center py-8 text-gray-400 text-sm border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-lg m-2">
                                        Station Empty
                                    </div>
                                ) : (
                                    station.jobs.map((job: any) => (
                                        <Link
                                            key={job.id}
                                            to={`/job/${job.id}/run`}
                                            className="block p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm hover:shadow-md hover:border-brand-primary transition-all group"
                                        >
                                            <div className="flex justify-between items-start mb-2">
                                                <span className="font-mono font-medium text-brand-primary group-hover:text-brand-secondary transition-colors">
                                                    {job.serial_number}
                                                </span>
                                                <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${job.status === 'qc' ? 'bg-purple-100 text-purple-700' :
                                                        job.status === 'failed' ? 'bg-red-100 text-red-700' :
                                                            'bg-gray-100 text-gray-600'
                                                    }`}>
                                                    {job.status}
                                                </span>
                                            </div>
                                            <div className="text-sm text-gray-600 dark:text-gray-300 mb-1">
                                                {job.platform}
                                            </div>
                                            <div className="text-xs text-gray-500 mb-2 truncate">
                                                {job.model}
                                            </div>
                                            <div className="flex justify-between items-center pt-2 border-t border-gray-100 dark:border-gray-700">
                                                <span className="text-[10px] text-gray-400">
                                                    {new Date(job.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </span>
                                                {job.batches && (
                                                    <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 rounded">
                                                        Batch: {job.batches}
                                                    </span>
                                                )}
                                            </div>
                                        </Link>
                                    ))
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}
