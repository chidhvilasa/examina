import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const API_TARGET = 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/analyze': API_TARGET,
      '/report': API_TARGET,
      '/status': API_TARGET,
      '/health': API_TARGET,
      '/feedback': API_TARGET,
      '/admin': API_TARGET,
    },
  },
})
