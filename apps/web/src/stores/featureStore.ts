import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type FeatureKey = 'sla_management' | 'customer_portal' | 'inventory_sync' | 'automations'

interface FeatureState {
    features: Record<FeatureKey, boolean>
    toggleFeature: (key: FeatureKey) => void
    setFeature: (key: FeatureKey, enabled: boolean) => void
}

export const useFeatureStore = create<FeatureState>()(
    persist(
        (set) => ({
            features: {
                sla_management: true,
                customer_portal: true,
                inventory_sync: true,
                automations: false,
            },
            toggleFeature: (key) =>
                set((state) => ({
                    features: { ...state.features, [key]: !state.features[key] },
                })),
            setFeature: (key, enabled) =>
                set((state) => ({
                    features: { ...state.features, [key]: enabled },
                })),
        }),
        {
            name: 'veriqo-features',
        }
    )
)
