import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // Allow access from any IP on the network
    port: 5173,      // Default Vite port
    strictPort: true, // Fail if port is already in use
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '192.168.1.176',
      'projectariapa.atharvahumar.com'
    ]
  }
})
