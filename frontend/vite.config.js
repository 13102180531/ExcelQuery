// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173, // Your frontend dev server port (optional, Vite defaults to this)
    proxy: {
      // String shorthand: '/foo' -> 'http://localhost:4567/foo'
      // '/api': 'http://localhost:8000', // Simpler if no rewrite needed

      // With options:
      '/api': { // Any request to /api/... will be proxied
        target: 'http://localhost:8000', // Your FastAPI backend address
        changeOrigin: true, // Needed for virtual hosted sites and to avoid some CORS issues
        // Optional: rewrite path if your backend expects different paths
        // rewrite: (path) => path.replace(/^\/api/, ''), // Example: /api/v1/users -> /v1/users on backend
                                                        // In your case, your backend already expects /api/v1/...
                                                        // so a direct proxy without rewrite is likely what you need
                                                        // if your backend routes *don't* start with /api.
                                                        // BUT, your backend routes DO start with /api/v1/...
                                                        // So, you should proxy a prefix that ISN'T part of the backend route itself,
                                                        // or use a rewrite if you want to keep /api in frontend calls.

        // Let's assume your backend routes are already /api/v1/...
        // If you make calls like fetch('/api/v1/excel/upload') from frontend,
        // and your backend listens at http://localhost:8000/api/v1/excel/upload,
        // then this proxy configuration should work:
      }
    }
  }
})