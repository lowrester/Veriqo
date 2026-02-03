import React, { useState } from 'react';
import { Plus, Settings } from 'lucide-react';

export const IntegrationsPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'api-keys' | 'webhooks'>('api-keys');

    // Mock API Keys
    const apiKeys = [
        { id: '1', name: 'ERP System', prefix: 'vq_live_', created: '2023-10-01', lastUsed: '2023-10-05 14:30' },
        { id: '2', name: 'Logistics Provider', prefix: 'vq_live_', created: '2023-09-15', lastUsed: 'Never' },
    ];

    // Mock Webhooks
    const webhooks = [
        { id: '1', url: 'https://api.erp.com/webhooks/veriqo', events: ['job.completed'], status: 'active', failures: 0 },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-bold text-text-primary">Integrations</h2>
                    <p className="text-text-secondary">Manage API access and event subscriptions.</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border">
                <button
                    onClick={() => setActiveTab('api-keys')}
                    className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${activeTab === 'api-keys'
                        ? 'border-brand-primary text-brand-primary'
                        : 'border-transparent text-text-secondary hover:text-text-primary'
                        }`}
                >
                    API Keys
                </button>
                <button
                    onClick={() => setActiveTab('webhooks')}
                    className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${activeTab === 'webhooks'
                        ? 'border-brand-primary text-brand-primary'
                        : 'border-transparent text-text-secondary hover:text-text-primary'
                        }`}
                >
                    Webhooks
                </button>
            </div>

            {/* API Keys Content */}
            {activeTab === 'api-keys' && (
                <div className="space-y-4">
                    <div className="flex justify-end">
                        <button className="flex items-center gap-2 px-3 py-2 bg-brand-primary text-white rounded-lg text-sm hover:bg-brand-secondary transition-colors">
                            <Plus className="w-4 h-4" />
                            Generate New Key
                        </button>
                    </div>

                    <div className="bg-bg-primary border border-border rounded-xl overflow-hidden">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-bg-secondary border-b border-border">
                                <tr>
                                    <th className="px-4 py-3 font-medium text-text-secondary">Name</th>
                                    <th className="px-4 py-3 font-medium text-text-secondary">Key Prefix</th>
                                    <th className="px-4 py-3 font-medium text-text-secondary">Created</th>
                                    <th className="px-4 py-3 font-medium text-text-secondary">Last Used</th>
                                    <th className="px-4 py-3 font-medium text-text-secondary w-20">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                {apiKeys.map((key) => (
                                    <tr key={key.id} className="hover:bg-bg-secondary/50">
                                        <td className="px-4 py-3 font-medium text-text-primary">{key.name}</td>
                                        <td className="px-4 py-3 font-mono text-text-secondary">{key.prefix}********</td>
                                        <td className="px-4 py-3 text-text-secondary">{key.created}</td>
                                        <td className="px-4 py-3 text-text-secondary">{key.lastUsed}</td>
                                        <td className="px-4 py-3">
                                            <button className="text-red-500 hover:text-red-700 font-medium text-xs">Revoke</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Webhooks Content */}
            {activeTab === 'webhooks' && (
                <div className="space-y-4">
                    <div className="flex justify-end">
                        <button className="flex items-center gap-2 px-3 py-2 bg-brand-primary text-white rounded-lg text-sm hover:bg-brand-secondary transition-colors">
                            <Plus className="w-4 h-4" />
                            Add Webhook
                        </button>
                    </div>

                    <div className="grid gap-4">
                        {webhooks.map((hook) => (
                            <div key={hook.id} className="bg-bg-primary border border-border rounded-xl p-4 flex items-start justify-between">
                                <div>
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="font-mono text-sm font-medium text-brand-primary bg-brand-light/10 px-2 py-0.5 rounded">POST</span>
                                        <span className="font-medium text-text-primary">{hook.url}</span>
                                    </div>
                                    <div className="flex gap-2 mt-2">
                                        {hook.events.map(event => (
                                            <span key={event} className="text-xs bg-bg-secondary text-text-secondary px-2 py-1 rounded-full border border-border">
                                                {event}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="flex items-center gap-1.5 text-xs font-medium text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400 px-2.5 py-1 rounded-full">
                                        <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                        Active
                                    </span>
                                    <button className="text-text-secondary hover:text-text-primary">
                                        <Settings className="w-4 h-4" /> {/* Settings icon reused from import? No, need to import it if used, or use another icon */}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
