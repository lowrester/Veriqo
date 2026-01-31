import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/api/jobs'
import { evidenceApi } from '@/api/evidence'
import { STATUS_LABELS, formatDate, formatBytes, JobStatus } from '@/types'
import {
  ArrowLeft,
  Upload,
  FileText,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Camera,
  Loader2,
} from 'lucide-react'
import { useState, useRef } from 'react'

export function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => jobsApi.get(id!),
    enabled: !!id,
  })

  const { data: validTransitions = [] } = useQuery({
    queryKey: ['job', id, 'transitions'],
    queryFn: () => jobsApi.getValidTransitions(id!),
    enabled: !!id,
  })

  const { data: evidence = [] } = useQuery({
    queryKey: ['job', id, 'evidence'],
    queryFn: () => evidenceApi.listForJob(id!),
    enabled: !!id,
  })

  const { data: history = [] } = useQuery({
    queryKey: ['job', id, 'history'],
    queryFn: () => jobsApi.getHistory(id!),
    enabled: !!id,
  })

  const transitionMutation = useMutation({
    mutationFn: (targetStatus: string) =>
      jobsApi.transition(id!, { target_status: targetStatus }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job', id] })
      queryClient.invalidateQueries({ queryKey: ['job', id, 'transitions'] })
      queryClient.invalidateQueries({ queryKey: ['job', id, 'history'] })
    },
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !id) return

    setIsUploading(true)
    try {
      await evidenceApi.upload(id, file)
      queryClient.invalidateQueries({ queryKey: ['job', id, 'evidence'] })
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Jobb hittades inte</p>
        <button onClick={() => navigate('/jobs')} className="btn-secondary mt-4">
          Tillbaka till jobb
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate('/jobs')}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Tillbaka till jobb
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{job.serial_number}</h1>
          <p className="text-gray-500">
            {job.device?.platform} {job.device?.model}
          </p>
        </div>
        <span className={`badge-${job.status} text-sm`}>
          {STATUS_LABELS[job.status as JobStatus]}
        </span>
      </div>

      {/* Workflow actions */}
      {validTransitions.length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4">Arbetsflöde</h2>
          <div className="flex flex-wrap gap-3">
            {validTransitions.map((status) => (
              <button
                key={status}
                onClick={() => transitionMutation.mutate(status)}
                disabled={transitionMutation.isPending}
                className={getTransitionButtonClass(status)}
              >
                {transitionMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  getTransitionIcon(status)
                )}
                {STATUS_LABELS[status as JobStatus]}
              </button>
            ))}
          </div>
          {transitionMutation.isError && (
            <p className="mt-3 text-sm text-red-600">
              Kunde inte ändra status. Kontrollera att alla krav är uppfyllda.
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Job details */}
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4">Detaljer</h2>
          <dl className="space-y-3">
            <DetailRow label="Serienummer" value={job.serial_number} />
            <DetailRow label="Plattform" value={job.device?.platform || '-'} />
            <DetailRow label="Modell" value={job.device?.model || '-'} />
            <DetailRow label="Tekniker" value={job.assigned_technician?.full_name || '-'} />
            <DetailRow label="Kundreferens" value={job.customer_reference || '-'} />
            <DetailRow label="Batch" value={job.batch_id || '-'} />
            <DetailRow label="Skapad" value={formatDate(job.created_at)} />
            {job.completed_at && (
              <DetailRow label="Klar" value={formatDate(job.completed_at)} />
            )}
          </dl>
        </div>

        {/* Evidence */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Bevis</h2>
            <label className="btn-secondary flex items-center gap-2 cursor-pointer">
              {isUploading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              Ladda upp
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,video/*"
                onChange={handleFileUpload}
                className="hidden"
                disabled={isUploading}
              />
            </label>
          </div>

          {evidence.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Camera className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>Inga bevis uppladdade ännu</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {evidence.map((item) => (
                <a
                  key={item.id}
                  href={evidenceApi.getDownloadUrl(item.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {item.original_filename}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {formatBytes(item.file_size_bytes)} • {formatDate(item.captured_at)}
                  </p>
                </a>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* History */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4">Historik</h2>
        {history.length === 0 ? (
          <p className="text-gray-500">Ingen historik ännu</p>
        ) : (
          <div className="space-y-3">
            {history.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
              >
                <Clock className="w-4 h-4 text-gray-400 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    {entry.from_status ? (
                      <>
                        <span className={`status-${entry.from_status}`}>
                          {STATUS_LABELS[entry.from_status as JobStatus]}
                        </span>
                        {' → '}
                      </>
                    ) : null}
                    <span className={`status-${entry.to_status}`}>
                      {STATUS_LABELS[entry.to_status as JobStatus]}
                    </span>
                  </p>
                  {entry.notes && (
                    <p className="text-sm text-gray-500 mt-1">{entry.notes}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {entry.changed_by_name} • {formatDate(entry.changed_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
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

function getTransitionButtonClass(status: string): string {
  const base = 'btn flex items-center gap-2'
  switch (status) {
    case 'completed':
      return `${base} bg-green-600 text-white hover:bg-green-700`
    case 'failed':
      return `${base} bg-red-600 text-white hover:bg-red-700`
    case 'on_hold':
      return `${base} bg-gray-600 text-white hover:bg-gray-700`
    default:
      return `${base} bg-blue-600 text-white hover:bg-blue-700`
  }
}

function getTransitionIcon(status: string) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4" />
    case 'failed':
      return <XCircle className="w-4 h-4" />
    case 'on_hold':
      return <AlertTriangle className="w-4 h-4" />
    default:
      return null
  }
}
