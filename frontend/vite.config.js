import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/videos': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/frames': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/exports': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
