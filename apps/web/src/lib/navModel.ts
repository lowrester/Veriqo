/**
 * Navigation model - role-based menu configuration
 */

export type UserRole = 'admin' | 'supervisor' | 'technician' | 'viewer'
export type StationType = 'intake' | 'reset' | 'functional' | 'qc'

export interface NavItem {
    label: string
    path: string
    icon: string
    roles: UserRole[]
    stationTypes?: StationType[]
}

export const NAV_ITEMS: NavItem[] = [
    {
        label: 'Dashboard',
        path: '/dashboard',
        icon: 'LayoutDashboard',
        roles: ['admin', 'supervisor', 'technician', 'viewer'],
    },
    {
        label: 'New Job',
        path: '/intake/new',
        icon: 'Plus',
        roles: ['admin', 'supervisor', 'technician'],
        stationTypes: ['intake'],
    },
    {
        label: 'Search',
        path: '/search',
        icon: 'Search',
        roles: ['admin', 'supervisor', 'technician', 'viewer'],
    },
    {
        label: 'Live Floor',
        path: '/ops',
        icon: 'BarChart3',
        roles: ['admin', 'supervisor'],
    },
    {
        label: 'Administration',
        path: '/admin',
        icon: 'Settings',
        roles: ['admin'],
    },
]

/**
 * Filter navigation items based on user role and station type
 */
export function filterNavItems(
    items: NavItem[],
    userRole: UserRole,
    stationType?: StationType
): NavItem[] {
    return items.filter((item) => {
        // Check role permission
        if (!item.roles.includes(userRole)) {
            return false
        }

        // Check station type if specified
        if (item.stationTypes && stationType) {
            return item.stationTypes.includes(stationType)
        }

        return true
    })
}
