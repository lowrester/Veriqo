import { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface RequireRoleProps {
    children: ReactNode
    anyOf: string[]
}

export function RequireRole({ children, anyOf }: RequireRoleProps) {
    const user = useAuthStore((state) => state.user)

    if (!user) {
        return <Navigate to="/login" replace />
    }

    if (!anyOf.includes(user.role)) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">Åtkomst nekad</h1>
                    <p className="text-gray-600">
                        Du har inte behörighet att visa denna sida.
                    </p>
                </div>
            </div>
        )
    }

    return <>{children}</>
}
