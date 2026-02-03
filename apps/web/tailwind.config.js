/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Veriqo brand colors (dynamic)
        brand: {
          primary: 'rgb(var(--brand-primary) / <alpha-value>)',
          secondary: 'rgb(var(--brand-secondary) / <alpha-value>)',
          light: 'rgb(var(--brand-light) / <alpha-value>)',
        },
        // Semantic Application Colors
        bg: {
          primary: 'rgb(var(--color-bg-primary) / <alpha-value>)',
          secondary: 'rgb(var(--color-bg-secondary) / <alpha-value>)',
        },
        text: {
          primary: 'rgb(var(--color-text-primary) / <alpha-value>)',
          secondary: 'rgb(var(--color-text-secondary) / <alpha-value>)',
        },
        border: {
          DEFAULT: 'rgb(var(--color-border) / <alpha-value>)',
        }
      },
      spacing: {
        'touch': '44px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
