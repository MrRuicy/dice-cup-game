<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { gsap } from 'gsap';
import Dice from './Dice.vue';

// 完整游戏版骰盅:摇盅动画 → 掀盅手势 → 查看点数
const props = defineProps<{ dice: number[] }>();

// 状态机
type State = 'idle' | 'shaking' | 'settled' | 'revealed';
const state = ref<State>('idle');

// 掀盅手势参数
const THRESHOLD = 120;
const MAX_LIFT = 180;

const cupEl = ref<HTMLElement | null>(null);
const shakeWrapEl = ref<HTMLElement | null>(null);
let startY = 0;
let dragging = false;
let currentLift = 0;

// 是否允许掀盅手势(只在 settled/revealed 状态可用)
const canLift = computed(() => state.value === 'settled' || state.value === 'revealed');

function setLift(v: number) {
  currentLift = v;
  if (cupEl.value) {
    const ratio = v / MAX_LIFT;
    const scale = 1 + ratio * 0.08;
    const tilt = ratio * 12;
    cupEl.value.style.transform = `translateY(${-v}px) rotateX(${tilt}deg) scale(${scale})`;
    cupEl.value.style.opacity = String(1 - ratio * 0.12);
  }
}

function onStart(e: TouchEvent | MouseEvent) {
  console.log('[CUP] onStart 触发', 'canLift:', canLift.value, 'state:', state.value);
  if (!canLift.value) return;
  dragging = true;
  startY = getY(e);
}

function onMove(e: TouchEvent | MouseEvent) {
  if (!dragging) return;
  const dy = startY - getY(e);
  let lift = Math.max(0, dy);
  if (lift > MAX_LIFT) lift = MAX_LIFT + (lift - MAX_LIFT) * 0.2;
  setLift(Math.min(lift, MAX_LIFT + 40));
}

function onEnd() {
  if (!dragging) return;
  dragging = false;
  if (currentLift >= THRESHOLD) {
    openCup();
  } else {
    closeCup();
  }
}

function openCup() {
  state.value = 'revealed';
  gsap.to(
    { v: currentLift },
    {
      v: MAX_LIFT,
      duration: 0.35,
      ease: 'power2.out',
      onUpdate() {
        setLift((this.targets()[0] as { v: number }).v);
      },
    }
  );
}

function closeCup() {
  if (state.value === 'revealed') state.value = 'settled';
  gsap.to(
    { v: currentLift },
    {
      v: 0,
      duration: 0.7,
      ease: 'elastic.out(1, 0.5)',
      onUpdate() {
        setLift((this.targets()[0] as { v: number }).v);
      },
    }
  );
}

function toggle() {
  if (state.value === 'revealed') closeCup();
}

function getY(e: TouchEvent | MouseEvent): number {
  if ('touches' in e && e.touches.length) return e.touches[0].clientY;
  if ('changedTouches' in e && e.changedTouches.length)
    return e.changedTouches[0].clientY;
  return (e as MouseEvent).clientY;
}

// 摇盅动画
function shake() {
  if (state.value !== 'idle') return;
  state.value = 'shaking';

  const tl = gsap.timeline({
    onComplete: () => {
      console.log('[CUP] 摇盅动画完成,切换到 settled');
      state.value = 'settled';
    },
  });

  // 摇盅:左右摇晃 + 轻微位移,持续 2.5 秒
  tl.to(shakeWrapEl.value, {
    rotateZ: 8,
    x: 6,
    y: -4,
    duration: 0.15,
    ease: 'power2.inOut',
  })
    .to(shakeWrapEl.value, {
      rotateZ: -10,
      x: -7,
      y: 3,
      duration: 0.18,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: 12,
      x: 8,
      y: -5,
      duration: 0.16,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: -9,
      x: -6,
      y: 4,
      duration: 0.17,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: 11,
      x: 7,
      y: -3,
      duration: 0.15,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: -8,
      x: -5,
      y: 2,
      duration: 0.16,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: 10,
      x: 6,
      y: -4,
      duration: 0.14,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: -7,
      x: -4,
      y: 3,
      duration: 0.15,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: 9,
      x: 5,
      y: -2,
      duration: 0.13,
      ease: 'power2.inOut',
    })
    .to(shakeWrapEl.value, {
      rotateZ: -6,
      x: -3,
      y: 2,
      duration: 0.14,
      ease: 'power2.inOut',
    })
    // 回正静止
    .to(shakeWrapEl.value, {
      rotateZ: 0,
      x: 0,
      y: 0,
      duration: 0.4,
      ease: 'back.out(1.2)',
    });
}

onMounted(() => setLift(0));

defineExpose({ shake, closeCup, state });
</script>

<template>
  <div class="cup-wrap">
    <!-- 摇盅动画外层:承载旋转和位移 -->
    <div ref="shakeWrapEl" class="shake-wrap">
      <!-- 托盘底座 -->
      <div class="tray">
        <div class="tray-surface"></div>
      </div>

      <!-- 骰子:摇盅时隐藏(被盅完全盖住,看不见),settled/revealed 才显示 -->
      <div class="dice-tray" :class="{ hidden: state === 'idle' || state === 'shaking' }">
        <Dice v-for="(v, i) in props.dice" :key="i" :value="v" :size="46" />
      </div>

      <!-- 骰盅(碗) -->
      <div
        ref="cupEl"
        class="cup"
        :class="{ 'no-interact': !canLift }"
        @touchstart.prevent="onStart"
        @touchmove.prevent="onMove"
        @touchend.prevent="onEnd"
        @mousedown.prevent="onStart"
        @mousemove="onMove"
        @mouseup="onEnd"
        @mouseleave="onEnd"
        @click="toggle"
      >
        <div class="cup-dome">
          <div class="cup-highlight"></div>
          <div v-if="state === 'settled'" class="cup-grip">▲<br />上滑掀开</div>
          <div v-else-if="state === 'shaking'" class="cup-status">摇盅中...</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cup-wrap {
  position: relative;
  width: 340px;
  height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 1000px;
}
.shake-wrap {
  width: 100%;
  height: 100%;
  position: relative;
  transform-origin: 50% 70%;
}

/* 托盘底座 */
.tray {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  width: 320px;
  height: 90px;
}
.tray-surface {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(
    ellipse at 50% 40%,
    #2a3350 0%,
    #1a2038 55%,
    #10152a 100%
  );
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow:
    inset 0 4px 30px rgba(0, 0, 0, 0.6),
    0 12px 30px rgba(0, 0, 0, 0.5);
}

/* 骰子 */
.dice-tray {
  position: absolute;
  bottom: 58px;
  left: 50%;
  transform: translateX(-50%);
  width: 240px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: opacity 0.3s;
}
.dice-tray.hidden {
  opacity: 0;
  pointer-events: none;
}

/* 骰盅(碗) */
.cup {
  position: absolute;
  bottom: 50px;
  left: 50%;
  width: 300px;
  height: 250px;
  margin-left: -150px;
  z-index: 10;
  touch-action: none;
  cursor: grab;
  will-change: transform, opacity;
  transform-origin: 50% 100%;
}
.cup:active {
  cursor: grabbing;
}
.cup.no-interact {
  cursor: default;
  pointer-events: none;
}

.cup-dome {
  position: absolute;
  inset: 0;
  border-radius: 44% 44% 40% 40% / 56% 56% 20% 20%;
  background: linear-gradient(
    100deg,
    #171d2e 0%,
    #2c3448 18%,
    #464f6c 40%,
    #2e3650 62%,
    #1b2133 82%,
    #10141f 100%
  );
  border: 1px solid rgba(255, 255, 255, 0.14);
  box-shadow:
    inset 0 10px 24px rgba(255, 255, 255, 0.12),
    inset 0 -26px 50px rgba(0, 0, 0, 0.65),
    inset 20px 0 40px rgba(0, 0, 0, 0.35),
    inset -20px 0 40px rgba(0, 0, 0, 0.35),
    0 24px 55px rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.cup-highlight {
  position: absolute;
  top: 5%;
  left: 27%;
  width: 15%;
  height: 82%;
  border-radius: 50%;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.3),
    rgba(255, 255, 255, 0.05) 60%,
    transparent
  );
  filter: blur(4px);
}
.cup-grip,
.cup-status {
  position: relative;
  text-align: center;
  color: rgba(230, 233, 240, 0.5);
  font-size: 14px;
  line-height: 1.8;
  letter-spacing: 1px;
  z-index: 2;
}
.cup-status {
  color: rgba(230, 233, 240, 0.7);
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}
</style>
