import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// 开发时把 /ws 代理到本地后端，生产由 FastAPI 同域托管
export default defineConfig({
  plugins: [vue()],
  server: {
    host: true, // 允许手机同局域网访问
    allowedHosts: true, // 放行隧道域名（localtunnel/cloudflare 等）
    proxy: {
      '/ws': { target: 'ws://127.0.0.1:8000', ws: true },
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
