import { api } from '@/api/client'

export interface LabelTemplate {
    id: string
    name: string
    description?: string
    zpl_code: string
    dimensions?: string
    is_default: boolean
    created_at: string
    updated_at: string
}

export interface CreateLabelTemplateData {
    name: string
    description?: string
    zpl_code: string
    dimensions?: string
    is_default?: boolean
}

export const printingApi = {
    // Label Templates
    getTemplates: async (): Promise<LabelTemplate[]> => {
        return api.get<LabelTemplate[]>('/printing/templates')
    },

    createTemplate: async (data: CreateLabelTemplateData): Promise<LabelTemplate> => {
        return api.post<LabelTemplate>('/printing/templates', data)
    },

    getTemplate: async (id: string): Promise<LabelTemplate> => {
        return api.get<LabelTemplate>(`/printing/templates/${id}`)
    },

    // Placeholder for future frontend-side ZPL generation/manipulation
    generateZpl: (template: LabelTemplate, data: Record<string, string>): string => {
        let zpl = template.zpl_code
        // Simple variable replacement logic: {{ variable_name }}
        Object.entries(data).forEach(([key, value]) => {
            const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g')
            zpl = zpl.replace(regex, value)
        })
        return zpl
    }
}
