import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Printer, FileText, Users, Monitor, Network } from 'lucide-react';

export const SettingsLayout: React.FC = () => {
    const navItems = [
        { to: '/settings/features', label: 'Platform Features', icon: <Monitor className="w-4 h-4" /> },
        { to: '/settings/printers', label: 'Printers', icon: <Printer className="w-4 h-4" /> },
        { to: '/settings/labels', label: 'Label Layouts', icon: <FileText className="w-4 h-4" /> },
        { to: '/settings/integrations', label: 'Integrations', icon: <Network className="w-4 h-4" /> },
        { to: '/settings/users', label: 'Users', icon: <Users className="w-4 h-4" /> },
        { to: '/settings/devices', label: 'Device Types', icon: <Monitor className="w-4 h-4" /> },
    ];

    return (
        <div className="flex flex-col md:flex-row gap-6 h-[calc(100vh-100px)]">
            {/* Sidebar Navigation */}
            <aside className="w-full md:w-64 shrink-0">
                <nav className="flex flex-col gap-1">
                    <div className="px-3 py-2 text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">
                        Configuration
                    </div>
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
                                    ? 'bg-brand-light/10 text-brand-primary'
                                    : 'text-text-secondary hover:bg-bg-secondary hover:text-text-primary'
                                }`
                            }
                        >
                            {item.icon}
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
            </aside>

            {/* Content Area */}
            <main className="flex-1 bg-bg-secondary/50 rounded-xl border border-dashed border-border p-6 overflow-y-auto">
                <Outlet />
            </main>
        </div>
    );
};
