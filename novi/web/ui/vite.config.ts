/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The Python server (novi/web/server.py) owns the API on :8080. In dev, Vite
// serves the UI on :5173 and proxies /api to the running server.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8080',
      '/healthz': 'http://127.0.0.1:8080',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
})
