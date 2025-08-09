import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@services': path.resolve(__dirname, './src/services'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@types': path.resolve(__dirname, './src/types'),
      '@store': path.resolve(__dirname, './src/store'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 2000, // Allow larger chunks for diagram libraries
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // React ecosystem
          if (id.includes('react') || id.includes('react-dom')) {
            return 'react-vendor';
          }
          
          // Mermaid and its dependencies - split into smaller chunks
          if (id.includes('mermaid')) {
            if (id.includes('cytoscape') || id.includes('dagre')) {
              return 'mermaid-graph';
            }
            if (id.includes('katex')) {
              return 'mermaid-math';
            }
            return 'mermaid-core';
          }
          
          // State management
          if (id.includes('zustand') || id.includes('@tanstack/react-query')) {
            return 'state-vendor';
          }
          
          // Form handling
          if (id.includes('react-hook-form') || id.includes('zod')) {
            return 'form-vendor';
          }
          
          // UI libraries
          if (id.includes('lucide-react') || id.includes('framer-motion')) {
            return 'ui-vendor';
          }
          
          // Other large dependencies
          if (id.includes('lodash') || id.includes('date-fns')) {
            return 'utils-vendor';
          }
          
          // Node modules
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
  },
});
