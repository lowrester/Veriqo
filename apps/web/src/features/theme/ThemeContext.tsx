import React, { createContext, useContext, useEffect, useState } from 'react'

export type Theme = 'light' | 'dark' | 'system'
export type ColorScheme = 'default' | 'purple' | 'green' | 'orange' | 'matrix'

interface ThemeAccess {
    theme: Theme
    setTheme: (theme: Theme) => void
    colorScheme: ColorScheme
    setColorScheme: (scheme: ColorScheme) => void
}

const ThemeContext = createContext<ThemeAccess | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setTheme] = useState<Theme>(
        () => (localStorage.getItem('ui-theme') as Theme) || 'system'
    )
    const [colorScheme, setColorScheme] = useState<ColorScheme>(
        () => (localStorage.getItem('ui-color-scheme') as ColorScheme) || 'default'
    )

    useEffect(() => {
        const root = window.document.documentElement

        // Remove old classes
        root.classList.remove('light', 'dark')

        if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'dark'
                : 'light'
            root.classList.add(systemTheme)
        } else {
            root.classList.add(theme)
        }

        localStorage.setItem('ui-theme', theme)
    }, [theme])

    useEffect(() => {
        const body = window.document.body
        body.setAttribute('data-color-scheme', colorScheme)
        localStorage.setItem('ui-color-scheme', colorScheme)
    }, [colorScheme])

    return (
        <ThemeContext.Provider value={{ theme, setTheme, colorScheme, setColorScheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    const context = useContext(ThemeContext)
    if (context === undefined)
        throw new Error('useTheme must be used within a ThemeProvider')
    return context
}
