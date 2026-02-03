import { api } from '@/api/client'

export interface DashboardStats {
    counts: {
        total: number
        completed: number
        failed: number
        in_progress: number
    }
    metrics: {
        yield_rate: number
    }
    recent_activity: {
        id: string
        serial_number: string
        status: string
        platform: string
        model: string
        updated_at: string
    }[]
}

export const statsApi = {
    getDashboardStats: async (): Promise<DashboardStats> => {
        return api.get<DashboardStats>('/stats/dashboard')
    },

    getFloorStatus: async (): Promise<any[]> => {
        return api.get<any[]>('/stats/floor')
    },
}
