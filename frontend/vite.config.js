import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // The 3D hero (three.js) is one ~930 kB chunk. It is lazy-loaded after the
    // page renders, so it does not delay the first paint.
    chunkSizeWarningLimit: 1000,
  },
  server: {
    // Requests to /api go to the FastAPI backend, so the browser sees one
    // origin and the HttpOnly login cookie works without CORS issues.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
