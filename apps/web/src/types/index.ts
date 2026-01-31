export type JobStatus =
  | 'intake'
  | 'reset'
  | 'functional'
  | 'qc'
  | 'completed'
  | 'failed'
  | 'on_hold'

export type UserRole = 'admin' | 'supervisor' | 'technician' | 'viewer'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export const STATUS_LABELS: Record<JobStatus, string> = {
  intake: 'Intake',
  reset: 'Reset',
  functional: 'Functional',
  qc: 'QC',
  completed: 'Completed',
  failed: 'Failed',
  on_hold: 'On Hold',
}

export const STATUS_COLORS: Record<JobStatus, string> = {
  intake: 'yellow',
  reset: 'orange',
  functional: 'blue',
  qc: 'purple',
  completed: 'green',
  failed: 'red',
  on_hold: 'gray',
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('sv-SE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
