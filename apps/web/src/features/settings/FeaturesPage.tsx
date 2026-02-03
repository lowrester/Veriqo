import { useFeatureStore, FeatureKey } from '@/stores/featureStore'
import { ToggleLeft, ToggleRight, Sparkles } from 'lucide-react'

const FEATURE_DESCRIPTIONS: Record<FeatureKey, { title: string; description: string }> = {
    sla_management: {
        title: 'SLA Management',
        description: 'Track time-to-completion targets and show SLA timers on jobs.',
    },
    customer_portal: {
        title: 'Customer Portal',
        description: 'Allow customers to log in and view their job status.',
    },
    inventory_sync: {
        title: 'Inventory Sync',
        description: 'Track parts usage and sync with external inventory systems.',
    },
    automations: {
        title: 'Automations',
        description: 'Run automated actions (e.g., emails) when jobs change status.',
    },
}

export function FeaturesPage() {
    const { features, toggleFeature } = useFeatureStore()

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-xl font-semibold text-text-primary">Platform Features</h2>
                <p className="text-text-secondary">Enable or disable optional platform capabilities.</p>
            </div>

            <div className="grid gap-4">
                {(Object.keys(FEATURE_DESCRIPTIONS) as FeatureKey[]).map((key) => {
                    const isEnabled = features[key]
                    const info = FEATURE_DESCRIPTIONS[key]

                    return (
                        <div
                            key={key}
                            className={`flex items-start justify-between p-4 rounded-lg border transition-colors ${isEnabled ? 'bg-blue-50/50 border-blue-100 dark:bg-blue-900/10 dark:border-blue-900/30' : 'bg-bg-primary border-border'
                                }`}
                        >
                            <div className="flex gap-3">
                                <div className={`mt-1 p-2 rounded-lg ${isEnabled ? 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400' : 'bg-bg-secondary text-text-secondary'}`}>
                                    <Sparkles className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-text-primary">{info.title}</h3>
                                    <p className="text-sm text-text-secondary mt-1">{info.description}</p>
                                </div>
                            </div>

                            <button
                                onClick={() => toggleFeature(key)}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${isEnabled
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-bg-secondary text-text-secondary hover:bg-gray-200 dark:hover:bg-gray-700'
                                    }`}
                            >
                                {isEnabled ? (
                                    <>
                                        <ToggleRight className="w-4 h-4" />
                                        Enabled
                                    </>
                                ) : (
                                    <>
                                        <ToggleLeft className="w-4 h-4" />
                                        Disabled
                                    </>
                                )}
                            </button>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
