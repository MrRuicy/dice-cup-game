<script setup lang="ts">
import { computed } from 'vue';

// 统一线描 SVG 图标：替换所有 emoji，保持描金优雅风格
// 用法：<Icon name="crown" :size="18" />
const props = defineProps<{ name: string; size?: number }>();

const px = computed(() => props.size ?? 20);
</script>

<template>
  <svg
    class="icon"
    :width="px"
    :height="px"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- 骰子 logo -->
    <template v-if="name === 'dice'">
      <rect x="3" y="3" width="18" height="18" rx="4" />
      <circle cx="8.5" cy="8.5" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="8.5" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="8.5" cy="15.5" r="1.1" fill="currentColor" stroke="none" />
      <circle cx="15.5" cy="15.5" r="1.1" fill="currentColor" stroke="none" />
    </template>

    <!-- 皇冠（房主） -->
    <template v-else-if="name === 'crown'">
      <path d="M3 8l3.5 3L12 5l5.5 6L21 8l-1.5 10h-15L3 8z" />
      <line x1="4.8" y1="18" x2="19.2" y2="18" />
    </template>

    <!-- 人物（玩家） -->
    <template v-else-if="name === 'user'">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20c0-3.6 3.1-6 7-6s7 2.4 7 6" />
    </template>

    <!-- 星芒（幸运/魔法） -->
    <template v-else-if="name === 'sparkle'">
      <path d="M12 3c.4 3.9 1.1 4.6 5 5-3.9.4-4.6 1.1-5 5-.4-3.9-1.1-4.6-5-5 3.9-.4 4.6-1.1 5-5z" fill="currentColor" stroke="none" />
      <path d="M19 13c.2 1.6.5 1.9 2 2-1.5.2-1.8.4-2 2-.2-1.6-.5-1.9-2-2 1.5-.2 1.8-.4 2-2z" fill="currentColor" stroke="none" />
    </template>

    <!-- 对勾（已投掷） -->
    <template v-else-if="name === 'check'">
      <path d="M4.5 12.5l5 5 10-11" />
    </template>

    <!-- 沙漏（等待） -->
    <template v-else-if="name === 'hourglass'">
      <path d="M7 3h10M7 21h10" />
      <path d="M7 3c0 5 5 6 5 9s-5 4-5 9" />
      <path d="M17 3c0 5-5 6-5 9s5 4 5 9" />
    </template>

    <!-- 菜单（更多） -->
    <template v-else-if="name === 'menu'">
      <circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none" />
    </template>

    <!-- 加号（创建） -->
    <template v-else-if="name === 'plus'">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </template>

    <!-- 箭头（加入/进入） -->
    <template v-else-if="name === 'arrow'">
      <line x1="4" y1="12" x2="19" y2="12" />
      <path d="M13 6l6 6-6 6" />
    </template>

    <!-- 上滑掀盅提示 -->
    <template v-else-if="name === 'lift'">
      <path d="M7 14l5-6 5 6" />
      <path d="M7 19l5-6 5 6" opacity="0.45" />
    </template>

    <!-- 礼物（幸运嘉宾选择） -->
    <template v-else-if="name === 'gift'">
      <rect x="4" y="9" width="16" height="11" rx="1.5" />
      <path d="M4 13h16M12 9v11" />
      <path d="M12 9C10 9 8 8 8 6.2 8 5 9 4 10 4c1.5 0 2 2.5 2 5zM12 9c2 0 4-1 4-2.8C16 5 15 4 14 4c-1.5 0-2 2.5-2 5z" />
    </template>
  </svg>
</template>

<style scoped>
.icon {
  display: inline-block;
  vertical-align: -0.18em;
  flex-shrink: 0;
}
</style>
