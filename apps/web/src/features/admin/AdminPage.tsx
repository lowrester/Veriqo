import { Link } from 'react-router-dom'
import { Users, Settings, Shield } from 'lucide-react'

const adminSections = [
    {
        title: 'Användarhantering',
        description: 'Hantera användare, roller och behörigheter',
        icon: Users,
        href: '/users',
        color: 'blue',
    },
    {
        title: 'Systeminställningar',
        description: 'Konfigurera systemparametrar och inställningar',
        icon: Settings,
        href: '/settings',
        color: 'gray',
        disabled: true,
    },
    {
        title: 'Säkerhet & Audit',
        description: 'Granska säkerhetsloggar och användaraktivitet',
        icon: Shield,
        href: '/audit',
        color: 'green',
        disabled: true,
    },
]

export function AdminPage() {
    return (
        <div className="max-w-4xl space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
                <p className="text-gray-500 mt-1">
                    Hantera användare, inställningar och systemkonfiguration
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {adminSections.map((section) => {
                    const Icon = section.icon
                    const isDisabled = section.disabled

                    const card = (
                        <div
                            className={`card hover:shadow-md transition-shadow ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                                }`}
                        >
                            <div className="flex items-start gap-4">
                                <div
                                    className={`p-3 rounded-lg ${section.color === 'blue'
                                            ? 'bg-blue-100 text-blue-600'
                                            : section.color === 'green'
                                                ? 'bg-green-100 text-green-600'
                                                : 'bg-gray-100 text-gray-600'
                                        }`}
                                >
                                    <Icon className="w-6 h-6" />
                                </div>
                                <div className="flex-1">
                                    <h3 className="font-semibold text-gray-900 mb-1">
                                        {section.title}
                                        {isDisabled && (
                                            <span className="ml-2 text-xs text-gray-400 font-normal">
                                                (Kommer snart)
                                            </span>
                                        )}
                                    </h3>
                                    <p className="text-sm text-gray-500">{section.description}</p>
                                </div>
                            </div>
                        </div>
                    )

                    if (isDisabled) {
                        return <div key={section.title}>{card}</div>
                    }

                    return (
                        <Link key={section.title} to={section.href}>
                            {card}
                        </Link>
                    )
                })}
            </div>
        </div>
    )
}
