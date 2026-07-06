import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import checker from 'vite-plugin-checker'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    checker({
      vueTsc: true,
      eslint: {
        lintCommand: 'eslint . --ext .vue,.ts,.tsx',
        useFlatConfig: false
      }
    })
  ],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    port: 5173,
    proxy: {
      // 代理所有 /api 请求到 FastAPI
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // FastAPI 已经以 /api 为前缀，保持路径不变
      },
      // OAuth 回调与认证相关路由
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // SSE 实时通知流
      '/notifications': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // SSE 需要关闭缓冲
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            proxyRes.headers['cache-control'] = 'no-cache'
          })
        },
      },
    },
  },

  build: {
    // 构建产物直接输出到后端 static 目录，FastAPI StaticFiles 热挂载
    outDir: '../static',
    emptyOutDir: false,         // 避免清空已有的其他静态资源
    assetsDir: 'vue-assets',    // 与原有 static/css, static/js 命名空间隔离
    rollupOptions: {
      output: {
        // 代码分割：vendor 单独 chunk，利于长效缓存
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'ui-vendor': ['naive-ui', '@vicons/ionicons5'],
          'chart-vendor': ['echarts', 'vue-echarts'],
        },
      },
    },
  },

  // 优化：预构建大型依赖
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'naive-ui', 'echarts'],
  },
})
