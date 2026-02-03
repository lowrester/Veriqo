import { Moon, Sun, Monitor, Palette, ChevronDown } from 'lucide-react'
import { useTheme, Theme, ColorScheme } from './ThemeContext'
import { useState, useRef, useEffect } from 'react'

export function ThemeSwitcher() {
    const { theme, setTheme, colorScheme, setColorScheme } = useTheme()
    const [isOpen, setIsOpen] = useState(false)
    const ref = useRef<HTMLDivElement>(null)

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (ref.current && !ref.current.contains(event.target as Node)) {
                setIsOpen(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const themes: { value: Theme; icon: any; label: string }[] = [
        { value: 'light', icon: Sun, label: 'Light' },
        { value: 'dark', icon: Moon, label: 'Dark' },
        { value: 'system', icon: Monitor, label: 'System' },
    ]

    const schemes: { value: ColorScheme; label: string; color: string }[] = [
        { value: 'default', label: 'Blue (Default)', color: 'bg-blue-600' },
        { value: 'purple', label: 'Purple', color: 'bg-purple-600' },
        { value: 'green', label: 'Green', color: 'bg-green-600' },
        { value: 'orange', label: 'Orange', color: 'bg-orange-600' },
    ]

    return (
        <div className="relative" ref={ref}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 rounded-lg transition-colors flex items-center gap-2"
                title="Theme Settings"
            >
                <Palette className="w-5 h-5" />
                <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-50 animate-in fade-in slide-in-from-top-2">
                    <div className="space-y-4">
                        {/* Mode Selection */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 block">
                                Appearance
                            </label>
                            <div className="grid grid-cols-3 gap-1 bg-gray-100 dark:bg-gray-900 p-1 rounded-lg">
                                {themes.map((t) => (
                                    <button
                                        key={t.value}
                                        onClick={() => setTheme(t.value)}
                                        className={`flex items-center justify-center p-2 rounded-md transition-all ${theme === t.value
                                                ? 'bg-white dark:bg-gray-700 text-brand-primary shadow-sm'
                                                : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                                            }`}
                                        title={t.label}
                                    >
                                        <t.icon className="w-4 h-4" />
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Color Scheme Selection */}
                        <div>
                            <label className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 block">
                                Accent Color
                            </label>
                            <div className="space-y-1">
                                {schemes.map((s) => (
                                    <button
                                        key={s.value}
                                        onClick={() => setColorScheme(s.value)}
                                        className={`w-full flex items-center px-3 py-2 rounded-lg text-sm transition-colors ${colorScheme === s.value
                                                ? 'bg-brand-light/20 text-brand-primary font-medium'
                                                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                                            }`}
                                    >
                                        <span className={`w-3 h-3 rounded-full mr-3 ${s.color}`} />
                                        {s.label}
                                        {colorScheme === s.value && (
                                            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-brand-primary" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
