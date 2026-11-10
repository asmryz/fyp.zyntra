/** @type {import('tailwindcss').Config} */
// The app is styled with plain CSS in src/styles. Tailwind provides the CSS
// reset (preflight) and the ZYNTRA palette below is available as utilities.
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        zyntra: {
          blue: '#2563EB',
          'blue-light': '#3B82F6',
          navy: '#0F172A',
          'navy-2': '#1E3A8A',
          card: '#1E293B',
          orange: '#F97316',
          'orange-hover': '#EA580C',
          cyan: '#06B6D4',
        },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', 'Segoe UI', 'sans-serif'],
        body: ['Manrope', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
