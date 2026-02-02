import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '@/api/client'
import { formatDate, type User, type UserRole } from '@/types'
import { Plus, Search, Trash2, Edit } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

const ROLE_LABELS: Record<UserRole, string> = {
    admin: 'Admin',
    supervisor: 'Supervisor',
    technician: 'Tekniker',
    viewer: 'Granskare',
}

const ROLE_COLORS: Record<UserRole, string> = {
    admin: 'red',
    supervisor: 'purple',
    technician: 'blue',
    viewer: 'gray',
}

export function UsersPage() {
    const [searchQuery, setSearchQuery] = useState('')
    const queryClient = useQueryClient()
    const currentUser = useAuthStore((state) => state.user)
    const isAdmin = currentUser?.role === 'admin'

    const { data: users = [], isLoading } = useQuery({
        queryKey: ['users'],
        queryFn: () => api.getUsers(),
    })

    const deleteMutation = useMutation({
        mutationFn: (userId: string) => api.deleteUser(userId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] })
        },
    })

    // Filter by search query
    const filteredUsers = users.filter(
        (user) =>
            user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
            user.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const handleDelete = async (userId: string, userName: string) => {
        if (
            !confirm(
                `Är du säker på att du vill ta bort användaren "${userName}"? Detta kan inte ångras.`
            )
        ) {
            return
        }

        try {
            await deleteMutation.mutateAsync(userId)
        } catch (error) {
            alert('Kunde inte ta bort användaren. Försök igen.')
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Användare</h1>
                    <p className="text-gray-500">Hantera systemanvändare och behörigheter</p>
                </div>
                {isAdmin && (
                    <Link to="/users/new" className="btn-primary flex items-center gap-2">
                        <Plus className="w-4 h-4" />
                        Ny användare
                    </Link>
                )}
            </div>

            {/* Search */}
            <div className="card">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Sök namn eller e-post..."
                        className="input pl-10"
                    />
                </div>
            </div>

            {/* Users list */}
            <div className="card p-0 overflow-hidden">
                {isLoading ? (
                    <div className="text-center py-12 text-gray-500">Laddar användare...</div>
                ) : filteredUsers.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        {searchQuery ? 'Inga användare matchar din sökning' : 'Inga användare ännu'}
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-200 bg-gray-50">
                                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                                        Namn
                                    </th>
                                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-500 hidden sm:table-cell">
                                        E-post
                                    </th>
                                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                                        Roll
                                    </th>
                                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-500 hidden md:table-cell">
                                        Status
                                    </th>
                                    <th className="text-left px-4 py-3 text-sm font-medium text-gray-500 hidden lg:table-cell">
                                        Skapad
                                    </th>
                                    {isAdmin && (
                                        <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">
                                            Åtgärder
                                        </th>
                                    )}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                                {filteredUsers.map((user) => (
                                    <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-4 py-3">
                                            <Link
                                                to={`/users/${user.id}`}
                                                className="font-medium text-blue-600 hover:text-blue-700"
                                            >
                                                {user.full_name}
                                            </Link>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">
                                            {user.email}
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className={`badge-${ROLE_COLORS[user.role]}`}>
                                                {ROLE_LABELS[user.role]}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                                            <span
                                                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${user.is_active
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-gray-100 text-gray-800'
                                                    }`}
                                            >
                                                {user.is_active ? 'Aktiv' : 'Inaktiv'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-500 hidden lg:table-cell">
                                            {formatDate(user.created_at)}
                                        </td>
                                        {isAdmin && (
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-2">
                                                    <Link
                                                        to={`/users/${user.id}`}
                                                        className="text-gray-600 hover:text-blue-600 transition-colors"
                                                        title="Redigera"
                                                    >
                                                        <Edit className="w-4 h-4" />
                                                    </Link>
                                                    {user.id !== currentUser?.id && (
                                                        <button
                                                            onClick={() => handleDelete(user.id, user.full_name)}
                                                            disabled={deleteMutation.isPending}
                                                            className="text-gray-600 hover:text-red-600 transition-colors disabled:opacity-50"
                                                            title="Ta bort"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    )}
                                                </div>
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
