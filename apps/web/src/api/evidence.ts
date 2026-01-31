import { api } from './client'

export interface Evidence {
  id: string
  job_id: string
  test_result_id?: string
  evidence_type: string
  original_filename: string
  file_size_bytes: number
  mime_type: string
  sha256_hash: string
  captured_at: string
  captured_by_name: string
  caption?: string
  download_url: string
}

export interface EvidenceListItem {
  id: string
  evidence_type: string
  original_filename: string
  file_size_bytes: number
  captured_at: string
  thumbnail_url?: string
}

export interface EvidenceUploadResponse {
  id: string
  job_id: string
  evidence_type: string
  original_filename: string
  file_size_bytes: number
  sha256_hash: string
  captured_at: string
  created_at: string
}

export const evidenceApi = {
  listForJob: (jobId: string) => api.get<EvidenceListItem[]>(`/jobs/${jobId}/evidence`),

  get: (id: string) => api.get<Evidence>(`/evidence/${id}`),

  upload: (jobId: string, file: File) =>
    api.upload<EvidenceUploadResponse>(`/jobs/${jobId}/evidence`, file),

  getDownloadUrl: (id: string) => `/api/v1/evidence/${id}/download`,

  getThumbnailUrl: (id: string) => `/api/v1/evidence/${id}/thumbnail`,
}
