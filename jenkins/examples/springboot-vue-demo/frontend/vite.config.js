import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 开发时把 /api 代理到本地后端，避免跨域
    proxy: {
      '/api': {
        target: 'http://localhost:9090',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    // 生产环境去掉 sourcemap，构建更快、体积更小
    sourcemap: false
  }
})
