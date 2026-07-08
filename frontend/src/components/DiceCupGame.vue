<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { gsap } from 'gsap';
import Dice from './Dice.vue';
import Icon from './Icon.vue';

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

// 重置为初始待摇状态（新一轮开始时调用）
function resetIdle() {
  state.value = 'idle';
  closeCup();
}

// 直接标记为已静置（重连补发时调用，跳过摇盅动画）
function markSettled() {
  if (state.value === 'idle') state.value = 'settled';
}

// 当前状态名（供外部只读判断）
function currentState(): State {
  return state.value;
}

defineExpose({ shake, closeCup, resetIdle, markSettled, currentState });
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
          <div class="cup-metal"></div>
          <div class="cup-highlight"></div>
          <div class="cup-rim"></div>
          <div v-if="state === 'settled'" class="cup-grip">
            <Icon name="lift" :size="26" />
            <span>上滑掀开</span>
          </div>
          <div v-else-if="state === 'shaking'" class="cup-status">摇 盅 中</div>
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
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  width: 320px;
  height: 90px;
}
.tray-surface {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  /* 毡布桌面承托：深墨绿绒面 + 香槟金描边圈 */
  background: radial-gradient(
    ellipse at 50% 38%,
    #1c4636 0%,
    #123328 50%,
    #081812 100%
  );
  border: 1px solid rgba(201, 162, 75, 0.28);
  box-shadow:
    inset 0 6px 34px rgba(0, 0, 0, 0.65),
    inset 0 0 0 6px rgba(201, 162, 75, 0.06),
    0 16px 36px rgba(0, 0, 0, 0.55);
}

/* 骰子 */
.dice-tray {
  position: absolute;
  bottom: 18px;
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
  bottom: 10px;
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
  /* 描金金属骰盅：深绿金属胎 + 竖向拉丝高光 */
  background: linear-gradient(
    100deg,
    #0c1f18 0%,
    #1a3a2c 16%,
    #2f5a45 38%,
    #1e4232 60%,
    #12281f 82%,
    #081611 100%
  );
  border: 1px solid rgba(201, 162, 75, 0.4);
  box-shadow:
    inset 0 12px 28px rgba(230, 200, 119, 0.15),
    inset 0 -28px 54px rgba(0, 0, 0, 0.7),
    inset 22px 0 44px rgba(0, 0, 0, 0.4),
    inset -22px 0 44px rgba(0, 0, 0, 0.4),
    0 26px 58px rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
/* 金属拉丝：斜向细高光条纹 */
.cup-metal {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: repeating-linear-gradient(
    98deg,
    transparent 0px,
    transparent 6px,
    rgba(255, 255, 255, 0.025) 7px,
    transparent 9px
  );
  pointer-events: none;
}
/* 口沿描金：底部椭圆金边，模拟盅口（进一步降低可见度） */
.cup-rim {
  position: absolute;
  left: 50%;
  bottom: 6%;
  width: 74%;
  height: 16%;
  transform: translateX(-50%);
  border-radius: 50%;
  background: radial-gradient(
    ellipse at 50% 45%,
    transparent 55%,
    rgba(201, 162, 75, 0.06) 72%,
    rgba(230, 200, 119, 0.09) 85%,
    transparent 92%
  );
  pointer-events: none;
}
.cup-highlight {
  position: absolute;
  top: 6%;
  left: 26%;
  width: 14%;
  height: 78%;
  border-radius: 50%;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.35),
    rgba(230, 200, 119, 0.12) 55%,
    transparent
  );
  filter: blur(5px);
  pointer-events: none;
}
.cup-grip,
.cup-status {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  text-align: center;
  color: rgba(201, 162, 75, 0.75);
  font-size: 13px;
  letter-spacing: 3px;
  z-index: 2;
}
.cup-status {
  color: rgba(230, 200, 119, 0.85);
  letter-spacing: 4px;
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
