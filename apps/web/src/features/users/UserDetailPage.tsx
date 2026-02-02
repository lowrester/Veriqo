import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { UpdateUserData, UserRole, User } from '@/types'
import { formatDate } from '@/types'
import { ArrowLeft, Edit2, Save, X, Loader2, AlertCircle } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

const ROLES: { value: UserRole; label: string }[] = [
    { value: 'admin', label: 'Admin' },
    { value: 'supervisor', label: 'Supervisor' },
    { value: 'technician', label: 'Technician' },
    { value: 'viewer', label: 'Viewer' },
]

const ROLE_LABELS: Record<UserRole, string> = {
    admin: 'Admin',
    supervisor: 'Supervisor',
    technician: 'Technician',
    viewer: 'Viewer',
}

export function UserDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const currentUser = useAuthStore((state) => state.user)
    const isAdmin = currentUser?.role === 'admin'

    const [isEditing, setIsEditing] = useState(false)
    const [formData, setFormData] = useState<UpdateUserData>({})

    const { data: user, isLoading } = useQuery<User>({
        queryKey: ['user', id],
        queryFn: () => api.getUser(id!),
        enabled: !!id,
    })

    const updateMutation = useMutation({
        mutationFn: (data: UpdateUserData) => api.updateUser(id!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['user', id] })
            queryClient.invalidateQueries({ queryKey: ['users'] })
            setIsEditing(false)
        },
    })

    const handleEdit = () => {
        if (!user) return
        setFormData({
            full_name: user.full_name,
            email: user.email,
            role: user.role,
            is_active: user.is_active,
        })
        setIsEditing(true)
    }

    const handleCancel = () => {
        setFormData({})
        setIsEditing(false)
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        updateMutation.mutate(formData)
    }

    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value, type } = e.target
        if (type === 'checkbox') {
            const checked = (e.target as HTMLInputElement).checked
            setFormData((prev) => ({ ...prev, [name]: checked }))
        } else {
            setFormData((prev) => ({ ...prev, [name]: value }))
        }
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        )
    }

    if (!user) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-500">User not found</p>
                <button onClick={() => navigate('/users')} className="btn-secondary mt-4">
                    Back to Users
                </button>
            </div>
        )
    }

    return (
        <div className="max-w-2xl space-y-6">
            {/* Header */}
            <div>
                <button
                    onClick={() => navigate('/users')}
                    className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Users
                </button>
                <div className="flex items-start justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">{user.full_name}</h1>
                        <p className="text-gray-500">{user.email}</p>
                    </div>
                    {isAdmin && !isEditing && (
                        <button onClick={handleEdit} className="btn-secondary flex items-center gap-2">
                            <Edit2 className="w-4 h-4" />
                            Edit
                        </button>
                    )}
                </div>
            </div>

            {/* Form / Details */}
            {isEditing ? (
                <form onSubmit={handleSubmit} className="card space-y-6">
                    {updateMutation.isError && (
                        <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 rounded-lg">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            Could not update user. Please try again.
                        </div>
                    )}

                    <div>
                        <label
                            htmlFor="full_name"
                            className="block text-sm font-medium text-gray-700 mb-1"
                        >
                            Full Name
                        </label>
                        <input
                            id="full_name"
                            name="full_name"
                            type="text"
                            value={formData.full_name || ''}
                            onChange={handleChange}
                            className="input"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                            Email Address
                        </label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email || ''}
                            onChange={handleChange}
                            className="input"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
                            Role
                        </label>
                        <select
                            id="role"
                            name="role"
                            value={formData.role || ''}
                            onChange={handleChange}
                            className="input"
                            required
                        >
                            {ROLES.map((role) => (
                                <option key={role.value} value={role.value}>
                                    {role.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-2">
                        <input
                            id="is_active"
                            name="is_active"
                            type="checkbox"
                            checked={formData.is_active ?? true}
                            onChange={handleChange}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
                            Active User
                        </label>
                    </div>

                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
                        <button
                            type="button"
                            onClick={handleCancel}
                            className="btn-secondary flex items-center gap-2"
                        >
                            <X className="w-4 h-4" />
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={updateMutation.isPending}
                            className="btn-primary flex items-center gap-2"
                        >
                            {updateMutation.isPending ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    Save
                                </>
                            )}
                        </button>
                    </div>
                </form>
            ) : (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">Details</h2>
                    <dl className="space-y-3">
                        <DetailRow label="Name" value={user.full_name} />
                        <DetailRow label="Email" value={user.email} />
                        <DetailRow label="Role" value={ROLE_LABELS[user.role]} />
                        <DetailRow label="Status" value={user.is_active ? 'Active' : 'Inactive'} />
                        <DetailRow label="Created" value={formatDate(user.created_at)} />
                    </dl>
                </div>
            )}
        </div>
    )
}

function DetailRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex justify-between">
            <dt className="text-sm text-gray-500">{label}</dt>
            <dd className="text-sm font-medium text-gray-900">{value}</dd>
        </div>
    )
}
