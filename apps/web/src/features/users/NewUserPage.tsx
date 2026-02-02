import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { CreateUserData, UserRole, User } from '@/types'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'

const ROLES: { value: UserRole; label: string }[] = [
    { value: 'admin', label: 'Admin' },
    { value: 'supervisor', label: 'Supervisor' },
    { value: 'technician', label: 'Technician' },
    { value: 'viewer', label: 'Viewer' },
]

export function NewUserPage() {
    const navigate = useNavigate()

    const [formData, setFormData] = useState<CreateUserData>({
        email: '',
        full_name: '',
        role: 'technician',
        password: '',
    })

    const [passwordConfirm, setPasswordConfirm] = useState('')

    const createMutation = useMutation({
        mutationFn: (data: CreateUserData) => api.createUser(data),
        onSuccess: (user: User) => {
            navigate(`/users/${user.id}`)
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()

        if (formData.password !== passwordConfirm) {
            alert('Passwords do not match')
            return
        }

        if (formData.password.length < 8) {
            alert('Password must be at least 8 characters long')
            return
        }

        createMutation.mutate(formData)
    }

    const handleChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target
        setFormData((prev) => ({ ...prev, [name]: value }))
    }

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            {/* Header */}
            <div>
                <button
                    onClick={() => navigate('/users')}
                    className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Users
                </button>
                <h1 className="text-2xl font-bold text-gray-900">New User</h1>
                <p className="text-gray-500">Create a new system user</p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="card space-y-6">
                {createMutation.isError && (
                    <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 rounded-lg">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        Could not create user. Email address might already be in use.
                    </div>
                )}

                <div>
                    <label
                        htmlFor="email"
                        className="block text-sm font-medium text-gray-700 mb-1"
                    >
                        Email Address *
                    </label>
                    <input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleChange}
                        className="input"
                        placeholder="user@example.com"
                        required
                    />
                </div>

                <div>
                    <label
                        htmlFor="full_name"
                        className="block text-sm font-medium text-gray-700 mb-1"
                    >
                        Full Name *
                    </label>
                    <input
                        id="full_name"
                        name="full_name"
                        type="text"
                        value={formData.full_name}
                        onChange={handleChange}
                        className="input"
                        placeholder="First Last"
                        required
                    />
                </div>

                <div>
                    <label
                        htmlFor="role"
                        className="block text-sm font-medium text-gray-700 mb-1"
                    >
                        Role *
                    </label>
                    <select
                        id="role"
                        name="role"
                        value={formData.role}
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
                    <p className="mt-1 text-sm text-gray-500">
                        Determines the user's permission level in the system
                    </p>
                </div>

                <div>
                    <label
                        htmlFor="password"
                        className="block text-sm font-medium text-gray-700 mb-1"
                    >
                        Password *
                    </label>
                    <input
                        id="password"
                        name="password"
                        type="password"
                        value={formData.password}
                        onChange={handleChange}
                        className="input"
                        placeholder="Min 8 characters"
                        minLength={8}
                        required
                    />
                </div>

                <div>
                    <label
                        htmlFor="password_confirm"
                        className="block text-sm font-medium text-gray-700 mb-1"
                    >
                        Confirm Password *
                    </label>
                    <input
                        id="password_confirm"
                        name="password_confirm"
                        type="password"
                        value={passwordConfirm}
                        onChange={(e) => setPasswordConfirm(e.target.value)}
                        className="input"
                        placeholder="Re-enter password"
                        minLength={8}
                        required
                    />
                </div>

                <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
                    <button
                        type="button"
                        onClick={() => navigate('/users')}
                        className="btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={
                            createMutation.isPending ||
                            !formData.email ||
                            !formData.full_name ||
                            !formData.password
                        }
                        className="btn-primary flex items-center gap-2"
                    >
                        {createMutation.isPending ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Creating...
                            </>
                        ) : (
                            'Create User'
                        )}
                    </button>
                </div>
            </form>
        </div>
    )
}
