import { api } from './client'

export interface Job {
  id: string
  serial_number: string
  status: string
  device?: {
    id: string
    platform: string
    model: string
  }
  assigned_technician?: {
    id: string
    full_name: string
    email: string
  }
  current_station?: {
    id: string
    name: string
    station_type: string
  }
  customer_reference?: string
  batch_id?: string
  intake_condition?: Record<string, unknown>
  qc_initials?: string
  qc_notes?: string
  intake_started_at?: string
  intake_completed_at?: string
  reset_started_at?: string
  reset_completed_at?: string
  functional_started_at?: string
  functional_completed_at?: string
  qc_started_at?: string
  qc_completed_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface JobListItem {
  id: string
  serial_number: string
  status: string
  device_platform?: string
  device_model?: string
  assigned_technician_name?: string
  created_at: string
}

export interface CreateJobRequest {
  device_id?: string
  serial_number: string
  customer_reference?: string
  batch_id?: string
  intake_condition?: Record<string, unknown>
}

export interface UpdateJobRequest {
  serial_number?: string
  customer_reference?: string
  batch_id?: string
  intake_condition?: Record<string, unknown>
  qc_initials?: string
  qc_notes?: string
}

export interface TransitionRequest {
  target_status: string
  notes?: string
}

export interface TransitionResponse {
  job: Job
  from_status: string
  to_status: string
  timestamp: string
  warnings: string[]
}

export interface JobHistory {
  id: string
  from_status?: string
  to_status: string
  changed_by_name: string
  changed_at: string
  notes?: string
}

export const jobsApi = {
  list: (params?: { status?: string; technician_id?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.technician_id) searchParams.set('technician_id', params.technician_id)
    if (params?.limit) searchParams.set('limit', params.limit.toString())
    if (params?.offset) searchParams.set('offset', params.offset.toString())

    const query = searchParams.toString()
    return api.get<JobListItem[]>(`/jobs${query ? `?${query}` : ''}`)
  },

  get: (id: string) => api.get<Job>(`/jobs/${id}`),

  create: (data: CreateJobRequest) => api.post<Job>('/jobs', data),

  update: (id: string, data: UpdateJobRequest) => api.patch<Job>(`/jobs/${id}`, data),

  transition: (id: string, data: TransitionRequest) =>
    api.post<TransitionResponse>(`/jobs/${id}/transition`, data),

  getValidTransitions: (id: string) => api.get<string[]>(`/jobs/${id}/valid-transitions`),

  getHistory: (id: string) => api.get<JobHistory[]>(`/jobs/${id}/history`),
}
