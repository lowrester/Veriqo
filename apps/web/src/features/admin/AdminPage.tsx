import { Link } from 'react-router-dom'
import { Users, Monitor, FileText, Database } from 'lucide-react'

const adminSections = [
    {
        title: 'Users',
        description: 'Manage users and permissions',
        icon: Users,
        color: 'bg-blue-100 text-blue-600',
        hoverColor: 'group-hover:bg-blue-200',
        path: '/users',
    },
    {
        title: 'Stations',
        description: 'Manage workflow stations and flows',
        icon: Monitor,
        color: 'bg-green-100 text-green-600',
        hoverColor: 'group-hover:bg-green-200',
        path: '/admin/stations',
    },
    {
        title: 'Test Templates',
        description: 'Create and edit test sequences',
        icon: FileText,
        color: 'bg-purple-100 text-purple-600',
        hoverColor: 'group-hover:bg-purple-200',
        path: '/admin/templates',
    },
    {
        title: 'Device Types',
        description: 'Configure platforms and models',
        icon: Database,
        color: 'bg-orange-100 text-orange-600',
        hoverColor: 'group-hover:bg-orange-200',
        path: '/admin/devices',
    },
]

export function AdminPage() {
    return (
        <div className="max-w-6xl mx-auto space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
                <p className="text-gray-500 mt-1">
                    Manage global settings and registries for Veriqo.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {adminSections.map((section) => (
                    <Link
                        key={section.path}
                        to={section.path}
                        className="card hover:shadow-md transition-shadow cursor-pointer group"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div
                                className={`p-3 rounded-lg transition-colors ${section.color} ${section.hoverColor}`}
                            >
                                <section.icon className="w-6 h-6" />
                            </div>
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-1">{section.title}</h3>
                        <p className="text-sm text-gray-500">{section.description}</p>
                    </Link>
                ))}
            </div>
        </div>
    )
}
