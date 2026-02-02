import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import { BarChart3, TrendingUp, CheckCircle, XCircle } from 'lucide-react'

export function OpsPage() {
    const { data: stats = {}, isLoading } = useQuery<any>({
        queryKey: ['ops', 'stats'],
        queryFn: () => api.get('/jobs/stats'),
    })

    if (isLoading) {
        return <div className="text-center py-12">Laddar statistik...</div>
    }

    return (
        <div className="max-w-6xl space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Statistik & KPI</h1>
                <p className="text-gray-500 mt-1">
                    Översikt över genomströmning och kvalitet
                </p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <KpiCard
                    icon={BarChart3}
                    label="Totalt genomförda"
                    value={stats?.total_completed || 0}
                    color="blue"
                />
                <KpiCard
                    icon={TrendingUp}
                    label="Genomsnittlig tid"
                    value={`${stats?.avg_completion_time || 0}h`}
                    color="green"
                />
                <KpiCard
                    icon={CheckCircle}
                    label="Godkända (%)"
                    value={`${stats?.pass_rate || 0}%`}
                    color="green"
                />
                <KpiCard
                    icon={XCircle}
                    label="Misslyckade (%)"
                    value={`${stats?.fail_rate || 0}%`}
                    color="red"
                />
            </div>

            {/* Throughput by station */}
            <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4">
                    Genomströmning per station
                </h2>
                <div className="space-y-3">
                    {['intake', 'reset', 'test', 'qc'].map((station) => (
                        <div key={station} className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-700 capitalize">
                                {station}
                            </span>
                            <div className="flex items-center gap-3">
                                <div className="w-48 bg-gray-200 rounded-full h-2">
                                    <div
                                        className="bg-blue-600 h-2 rounded-full"
                                        style={{
                                            width: `${Math.random() * 100}%`,
                                        }}
                                    />
                                </div>
                                <span className="text-sm text-gray-600 w-12 text-right">
                                    {Math.floor(Math.random() * 100)}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Recent activity */}
            <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4">Senaste aktivitet</h2>
                <div className="space-y-2">
                    <p className="text-sm text-gray-500">
                        Aktivitetslogg kommer snart...
                    </p>
                </div>
            </div>
        </div>
    )
}

function KpiCard({
    icon: Icon,
    label,
    value,
    color,
}: {
    icon: React.ElementType
    label: string
    value: string | number
    color: 'blue' | 'green' | 'red'
}) {
    const colorClasses = {
        blue: 'bg-blue-100 text-blue-600',
        green: 'bg-green-100 text-green-600',
        red: 'bg-red-100 text-red-600',
    }

    return (
        <div className="card">
            <div className="flex items-center gap-3">
                <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
                    <Icon className="w-6 h-6" />
                </div>
                <div>
                    <p className="text-sm text-gray-500">{label}</p>
                    <p className="text-2xl font-bold text-gray-900">{value}</p>
                </div>
            </div>
        </div>
    )
}
