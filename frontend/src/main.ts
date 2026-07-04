import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHashHistory } from 'vue-router';
import App from './App.vue';
import HomeView from './views/HomeView.vue';
import RoomView from './views/RoomView.vue';
import './style.css';

// 清理旧版本的全局 token（迁移到按房间号存储）
// 这会在应用启动时执行，清除所有旧的 dice_token
try {
  // 清理旧的全局 token
  localStorage.removeItem('dice_token');
  // 也清理所有可能存在的旧 token
  for (let i = localStorage.length - 1; i >= 0; i--) {
    const key = localStorage.key(i);
    if (key === 'dice_token') {
      localStorage.removeItem(key);
    }
  }
  console.log('[MAIN] 已清理旧版本 token，请重新加入房间');
} catch (e) {
  console.warn('[MAIN] 无法清理 localStorage:', e);
}

// 用 hash 路由，静态托管无需服务端 rewrite
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/room', name: 'room', component: RoomView },
  ],
});

createApp(App).use(createPinia()).use(router).mount('#app');
