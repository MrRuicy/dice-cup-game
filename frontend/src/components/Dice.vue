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
          <i v-if="pipLayout[f.n].includes(cell)" class="pip"></i>
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
  border-radius: 12px;
  /* 亚克力白 + 珠光质感:更现代,不旧气 */
  background: linear-gradient(145deg, #ffffff, #f0f2f5);
  box-shadow:
    inset 0 3px 6px rgba(255, 255, 255, 0.95),
    inset 0 -2px 8px rgba(0, 0, 0, 0.12),
    0 4px 12px rgba(0, 0, 0, 0.15);
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
  width: 60%;
  height: 60%;
  border-radius: 50%;
  /* 凹陷红点:径向渐变 + 内阴影 */
  background: radial-gradient(circle at 35% 30%, #ff5a5a, #b81d1d);
  box-shadow: inset 0 2px 3px rgba(0, 0, 0, 0.5), 0 1px 1px rgba(255, 255, 255, 0.3);
}
</style>
