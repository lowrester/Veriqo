import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { jobsApi, CreateJobRequest } from '@/api/jobs'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'

export function NewJobPage() {
  const navigate = useNavigate()

  const [formData, setFormData] = useState<CreateJobRequest>({
    serial_number: '',
    customer_reference: '',
    batch_id: '',
  })

  const createMutation = useMutation({
    mutationFn: (data: CreateJobRequest) => jobsApi.create(data),
    onSuccess: (job) => {
      navigate(`/jobs/${job.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/jobs')}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka till jobb
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Nytt jobb</h1>
        <p className="text-gray-500">Skapa ett nytt verifieringsjobb</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="card space-y-6">
        {createMutation.isError && (
          <div className="flex items-center gap-2 p-3 text-sm text-red-600 bg-red-50 rounded-lg">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            Kunde inte skapa jobb. Försök igen.
          </div>
        )}

        <div>
          <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700 mb-1">
            Serienummer *
          </label>
          <input
            id="serial_number"
            name="serial_number"
            type="text"
            value={formData.serial_number}
            onChange={handleChange}
            className="input"
            placeholder="T.ex. PS5-ABC123456"
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            Ange enhetens serienummer för identifiering
          </p>
        </div>

        <div>
          <label htmlFor="customer_reference" className="block text-sm font-medium text-gray-700 mb-1">
            Kundreferens
          </label>
          <input
            id="customer_reference"
            name="customer_reference"
            type="text"
            value={formData.customer_reference || ''}
            onChange={handleChange}
            className="input"
            placeholder="T.ex. Ordernummer eller kundnamn"
          />
        </div>

        <div>
          <label htmlFor="batch_id" className="block text-sm font-medium text-gray-700 mb-1">
            Batch-ID
          </label>
          <input
            id="batch_id"
            name="batch_id"
            type="text"
            value={formData.batch_id || ''}
            onChange={handleChange}
            className="input"
            placeholder="T.ex. BATCH-2024-001"
          />
          <p className="mt-1 text-sm text-gray-500">
            Gruppera flera enheter i samma batch
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={() => navigate('/jobs')}
            className="btn-secondary"
          >
            Avbryt
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending || !formData.serial_number}
            className="btn-primary flex items-center gap-2"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Skapar...
              </>
            ) : (
              'Skapa jobb'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
