/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Veriqo brand colors (configurable via CSS variables)
        brand: {
          primary: 'var(--brand-primary, #2563eb)',
          secondary: 'var(--brand-secondary, #1e40af)',
        },
      },
      // Tablet-first touch targets
      spacing: {
        'touch': '44px',
      },
    },
  },
  plugins: [],
}
