<script setup lang="ts">
import { computed } from 'vue';

// 单颗 CSS 3D 骰子:象牙白骰身 + 凹陷红点
const props = defineProps<{ value: number; size?: number }>();

const px = computed(() => props.size ?? 56);

// 世界坐标:从斜上方俯视,主看顶面(点数面),略露侧棱
const WORLD_TILT = 'rotateX(-56deg) rotateY(-14deg)';
const baseRotate = computed(() => WORLD_TILT);

// 点数在顶面;其余面按真骰子规则(对面和为 7)填充,仅作侧壁点缀
const layout = computed(() => {
  const v = props.value;
  const opp = 7 - v;
  const rest = [1, 2, 3, 4, 5, 6].filter((x) => x !== v && x !== opp);
  return { top: v, bottom: opp, front: rest[0], right: rest[1], left: rest[2], back: rest[3] };
});

// 每个面的点位布局(九宫格索引 1-9),对应骰子 1-6 点
const pipLayout: Record<number, number[]> = {
  1: [5],
  2: [1, 9],
  3: [1, 5, 9],
  4: [1, 3, 7, 9],
  5: [1, 3, 5, 7, 9],
  6: [1, 3, 4, 6, 7, 9],
};

const faces = computed(() => [
  { key: 'top', n: layout.value.top, t: 'rotateX(90deg)' },
  { key: 'bottom', n: layout.value.bottom, t: 'rotateX(-90deg)' },
  { key: 'front', n: layout.value.front, t: 'rotateY(0deg)' },
  { key: 'back', n: layout.value.back, t: 'rotateY(180deg)' },
  { key: 'right', n: layout.value.right, t: 'rotateY(90deg)' },
  { key: 'left', n: layout.value.left, t: 'rotateY(-90deg)' },
]);

// 真实骰子规则：1 点与 4 点为红色，其余为黑色
function isRed(n: number): boolean {
  return n === 1 || n === 4;
}
</script>

<template>
  <div class="dice-scene" :style="{ width: px + 'px', height: px + 'px' }">
    <div
      class="dice"
      :style="{ '--base-rotate': baseRotate, width: px + 'px', height: px + 'px' }"
    >
      <div
        v-for="f in faces"
        :key="f.key"
        class="face"
        :style="{ transform: `${f.t} translateZ(${px / 2}px)`, width: px + 'px', height: px + 'px' }"
      >
        <span v-for="cell in 9" :key="cell" class="pip-cell">
          <i
            v-if="pipLayout[f.n].includes(cell)"
            class="pip"
            :class="{ red: isRed(f.n) }"
          ></i>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dice-scene {
  perspective: 700px;
}
.dice {
  position: relative;
  transform-style: preserve-3d;
  transform: var(--base-rotate);
}
.face {
  position: absolute;
  border-radius: 14px;
  /* 象牙骰身：温润珠光渐变，比纯白更高级 */
  background:
    radial-gradient(circle at 30% 22%, rgba(255, 255, 255, 0.9), transparent 45%),
    linear-gradient(150deg, #fdfaf2 0%, #f3ecdc 55%, #e6dcc4 100%);
  box-shadow:
    inset 0 4px 7px rgba(255, 255, 255, 0.9),
    inset 0 -3px 10px rgba(120, 100, 60, 0.22),
    inset 3px 0 6px rgba(255, 255, 255, 0.4),
    inset -3px 0 8px rgba(120, 100, 60, 0.15),
    0 5px 14px rgba(0, 0, 0, 0.28);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(3, 1fr);
  padding: 14%;
  box-sizing: border-box;
}
.pip-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}
.pip {
  width: 62%;
  height: 62%;
  border-radius: 50%;
  /* 凹陷黑点：径向渐变 + 内阴影，模拟钻孔 */
  background: radial-gradient(circle at 38% 32%, #4a4a4a, #111 70%);
  box-shadow:
    inset 0 2px 3px rgba(0, 0, 0, 0.7),
    inset 0 -1px 2px rgba(255, 255, 255, 0.15),
    0 1px 1px rgba(255, 255, 255, 0.5);
}
.pip.red {
  /* 红点（1、4 点）：经典中式骰子 */
  background: radial-gradient(circle at 38% 32%, #e24a3f, #9c1610 72%);
  box-shadow:
    inset 0 2px 3px rgba(80, 0, 0, 0.65),
    inset 0 -1px 2px rgba(255, 200, 190, 0.3),
    0 1px 1px rgba(255, 255, 255, 0.5);
}
</style>
