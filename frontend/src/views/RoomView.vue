<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '../stores/game';
import DiceCupGame from '../components/DiceCupGame.vue';
import Dice from '../components/Dice.vue';

const router = useRouter();
const store = useGameStore();
const cupRef = ref<InstanceType<typeof DiceCupGame> | null>(null);

// 调试：暴露 store 到 window
if (typeof window !== 'undefined') {
  (window as any).$store = store;
}

// 幸运嘉宾选择(在统计弹窗里)
const selectedPlayers = ref<string[]>([]);
const randomCount = ref(0); // 随机选择人数

// 调试：监听关键状态变化
watch(
  () => [store.isHost, store.phase, store.playerId, store.hostId, store.myDice],
  ([isHost, phase, playerId, hostId, myDice]) => {
    console.log('[ROOM DEBUG]', {
      isHost,
      phase,
      playerId,
      hostId,
      myDice,
      shouldShowEndButton: isHost && phase === 'rolling' && myDice,
      shouldShowRollButton: phase === 'rolling' && !myDice
    });
  },
  { immediate: true }
);

// 计算全场点数分布
function getDiceStats() {
  if (!store.results) return [];
  const counts = [0, 0, 0, 0, 0, 0]; // 1-6点的个数
  Object.values(store.results).forEach(dice => {
    dice.forEach(v => {
      if (v >= 1 && v <= 6) counts[v - 1]++;
    });
  });
  return counts.map((count, i) => ({ value: i + 1, count }));
}

// 页面加载时尝试重连（如果有 token）
onMounted(() => {
  // 从 sessionStorage 获取 token（标签页隔离）
  const token = sessionStorage.getItem('dice_token');
  const roomCode = sessionStorage.getItem('dice_room');

  if (token && roomCode && !store.roomCode) {
    // 有 token 但 store 为空，尝试重连
    store.token = token;
    store.ensureConnected();
    // 给重连一些时间，2秒后如果仍未恢复房间状态，则返回首页
    setTimeout(() => {
      if (!store.roomCode) {
        router.replace('/');
      }
    }, 2000);
  } else if (!store.roomCode) {
    // 没有 token 或 store 状态，回到首页
    router.replace('/');
  }
});

// 房间解散 → 回首页
watch(
  () => store.dismissed,
  (v) => {
    if (v) {
      alert('房间已解散');
      store.reset();
      router.replace('/');
    }
  }
);

// 新一轮开始时清空本地投掷视图 + 重置骰盅
// 使用 phase 和 round 组合判断：进入 rolling 阶段且 round 变化
let lastRound = 0;
watch(
  () => [store.phase, store.round] as const,
  ([phase, round], [prevPhase, prevRound]) => {
    console.log('[ROOM WATCH] phase:', prevPhase, '→', phase, ', round:', prevRound, '→', round);

    // 进入 rolling 阶段，且 round 增加（真正的新一轮）
    if (phase === 'rolling' && round !== lastRound && lastRound !== 0) {
      console.log('[ROOM] 检测到新一轮（round 变化），清空本地数据');
      store.resetRoundView();
      store.isLucky = false;
      if (cupRef.value) {
        if (cupRef.value.state.value !== 'idle') {
          cupRef.value.state.value = 'idle';
        }
        cupRef.value.closeCup();
      }
    }

    // 更新 lastRound
    if (round > 0) {
      lastRound = round;
    }
  }
);

// 投掷后收到点数 → 触发摇盅动画（重连时跳过）
watch(
  () => store.myDice,
  (dice) => {
    if (dice && dice.length > 0) {
      // 判断是重连补发还是正常投掷
      if (store.isReconnect) {
        // 重连补发，跳过动画，直接设为 settled
        console.log('[ROOM] 重连恢复，跳过动画');
        setTimeout(() => {
          if (cupRef.value && cupRef.value.state.value === 'idle') {
            cupRef.value.state.value = 'settled';
          }
        }, 50);
      } else {
        // 正常投掷，触发摇盅动画
        console.log('[ROOM] 正常投掷，触发动画');
        setTimeout(() => {
          cupRef.value?.shake();
        }, 50);
      }
    }
  }
);

// 监听 isLucky 变化
watch(
  () => store.isLucky,
  (val) => {
    console.log('[ROOM] isLucky 变化:', val);
  }
);

function statusIcon(status: string): string {
  if (status === 'rolled') return '✓';
  if (status === 'waiting') return '⏳';
  return '—';
}

function onLeave() {
  if (confirm(store.isHost ? '确定解散房间？' : '确定退出房间？')) {
    store.leave();
    router.replace('/');
  }
}

// 投掷:调后端(摇盅动画由 watch myDice 触发)
function roll() {
  if (store.myDice) return; // 已投掷
  store.roll();
}

// 切换玩家选中状态(幸运嘉宾)
function togglePlayer(playerId: string) {
  const idx = selectedPlayers.value.indexOf(playerId);
  if (idx >= 0) {
    selectedPlayers.value.splice(idx, 1);
  } else {
    selectedPlayers.value.push(playerId);
  }
}

// 开始下一轮(房主确认统计弹窗)
function startNextRound() {
  // 计算最终幸运人数：手动指定 vs 随机选择，取最大值
  const manualCount = selectedPlayers.value.length;
  const finalCount = Math.max(manualCount, randomCount.value);

  // 如果有幸运嘉宾设置（手动或随机），发送给后端
  if (finalCount > 0) {
    store.setLucky(selectedPlayers.value, finalCount);
  }

  // 清空选择
  selectedPlayers.value = [];
  randomCount.value = 0;
  store.nextRound();
}
</script>

<template>
  <div class="room">
    <!-- 顶部导航 -->
    <header class="topbar">
      <span class="room-code">房间 {{ store.roomCode }}</span>
      <span class="round-badge">第 {{ store.round || '-' }} 轮</span>
      <button class="menu-btn" @click="onLeave">⋯</button>
    </header>

    <!-- 玩家状态条 -->
    <div class="player-bar">
      <span
        v-for="p in store.players"
        :key="p.id"
        class="player-chip"
        :class="{ me: p.id === store.playerId, host: p.id === store.hostId }"
      >
        👤{{ p.nickname }}<b>{{ statusIcon(p.status) }}</b>
      </span>
    </div>

    <!-- 中央场景:骰盅 -->
    <main class="stage">
      <!-- rolling 阶段始终显示骰盅，根据是否投掷改变状态 -->
      <template v-if="store.phase === 'rolling'">
        <DiceCupGame ref="cupRef" :dice="store.myDice || []" />
      </template>

      <!-- waiting 阶段:占位提示 -->
      <div v-else-if="store.phase === 'waiting'" class="cup-placeholder">
        <div class="hint">等待房主开始本轮</div>
      </div>

      <!-- 其他状态:占位 -->
      <div v-else class="cup-placeholder">
        <div class="hint">—</div>
      </div>
    </main>

    <!-- 底部操作区 -->
    <footer class="actions">
      <!-- 房主控制 -->
      <template v-if="store.isHost">
        <button
          v-if="store.phase === 'waiting'"
          class="glass-btn primary"
          @click="store.startRound()"
        >
          开始本轮
        </button>
        <!-- 房主在 rolling 阶段：已投掷后才显示"结束本轮"，否则显示"投掷" -->
        <button
          v-if="store.phase === 'rolling' && store.myDice"
          class="glass-btn"
          @click="store.endRound()"
        >
          结束本轮
        </button>
      </template>

      <!-- 投掷按钮（所有人，rolling 阶段且未投掷） -->
      <button
        v-if="store.phase === 'rolling' && !store.myDice"
        class="glass-btn primary"
        @click="roll"
      >
        🎲 投掷
      </button>
    </footer>

    <!-- 幸运提示遮罩(1秒后自动消失) -->
    <div v-if="store.isLucky" class="lucky-overlay">
      ✨ 嘘！房主大大为你施加了魔法 ✨
    </div>

    <!-- 统计结果弹窗(ended 阶段) -->
    <div v-if="store.phase === 'ended' && store.results" class="result-overlay">
      <div class="result-panel">
        <h3>🎲 本轮结果</h3>

        <!-- 全场点数统计 -->
        <div class="dice-stats">
          <div class="stats-title">全场统计</div>
          <div class="stats-row">
            <span v-for="stat in getDiceStats()" :key="stat.value" class="stat-item">
              {{ stat.value }}点×{{ stat.count }}
            </span>
          </div>
        </div>

        <!-- 所有玩家的点数展示 -->
        <div class="result-list">
          <div v-for="p in store.players" :key="p.id" class="result-item">
            <div class="player-info">
              <span class="player-name">{{ p.nickname }}</span>
              <span v-if="p.id === store.hostId" class="host-badge">👑</span>
            </div>
            <div v-if="store.results[p.id]" class="dice-display">
              <Dice v-for="(v, i) in store.results[p.id]" :key="i" :value="v" :size="32" />
            </div>
            <div v-else class="no-roll">未投掷</div>
          </div>
        </div>

        <!-- 房主选择下一轮幸运嘉宾 -->
        <div v-if="store.isHost" class="lucky-select-section">
          <div class="section-title">🎁 选择下一轮幸运嘉宾（可选）</div>

          <!-- 随机选择人数 -->
          <div class="random-count-selector">
            <label>随机选择</label>
            <input
              type="number"
              v-model.number="randomCount"
              min="0"
              :max="store.players.length"
              class="count-input"
            />
            <label>人（0 = 不随机）</label>
          </div>

          <!-- 手动指定玩家 -->
          <div class="manual-select-label">或手动指定玩家：</div>
          <div class="lucky-checkbox-list">
            <label
              v-for="p in store.players"
              :key="p.id"
              class="lucky-checkbox-item"
            >
              <input
                type="checkbox"
                :checked="selectedPlayers.includes(p.id)"
                @change="togglePlayer(p.id)"
              />
              <span>{{ p.nickname }}</span>
            </label>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="result-actions">
          <button v-if="store.isHost" class="glass-btn primary full-width" @click="startNextRound">
            {{
              Math.max(selectedPlayers.length, randomCount) > 0
                ? `✨ 施加魔法(${Math.max(selectedPlayers.length, randomCount)}人)并开始下一轮`
                : '开始下一轮'
            }}
          </button>
          <button v-else class="glass-btn full-width" disabled>
            等待房主开始下一轮
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.room {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.room-code {
  font-size: 18px;
  font-weight: 600;
}
.round-badge {
  color: var(--text-dim);
  font-size: 14px;
}
.menu-btn {
  background: transparent;
  color: var(--text-main);
  font-size: 24px;
  padding: 0 8px;
}
.player-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.player-chip {
  font-size: 13px;
  padding: 5px 10px;
  border-radius: 20px;
  background: var(--bg-card);
  color: var(--text-dim);
}
.player-chip b {
  margin-left: 4px;
  color: var(--accent);
}
.player-chip.me {
  border: 1px solid var(--primary);
  color: var(--text-main);
}
.player-chip.host::before {
  content: '👑';
  margin-right: 2px;
}
.stage {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 20px;
  background: radial-gradient(
      circle at 50% 42%,
      rgba(79, 124, 255, 0.16),
      transparent 55%
    ),
    radial-gradient(circle at 50% 80%, rgba(56, 211, 159, 0.08), transparent 50%);
}
.cup-placeholder {
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle at 40% 30%, #2a3350, #121830);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 4px 20px rgba(0, 0, 0, 0.5), 0 8px 30px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.hint {
  color: var(--text-dim);
  font-size: 15px;
  padding: 0 20px;
}
.result-box {
  width: 100%;
  max-width: 340px;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 16px;
}
.result-box h3 {
  margin: 0 0 12px;
  text-align: center;
  font-size: 16px;
}
.result-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
}
.result-row .dim {
  color: var(--text-dim);
}
.actions {
  padding: 16px 24px calc(16px + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.lucky-overlay {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, rgba(212, 175, 55, 0.35), rgba(212, 175, 55, 0.08));
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
  font-size: 22px;
  font-weight: 700;
  color: var(--gold);
  text-shadow: 0 0 20px rgba(212, 175, 55, 0.8);
  animation: luckyIn 0.5s ease;
  z-index: 200;
}
@keyframes luckyIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 统计结果弹窗 */
.result-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}
.result-panel {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 24px;
  width: 100%;
  max-width: 420px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 12px 50px rgba(0, 0, 0, 0.7);
  animation: slideUp 0.4s ease;
}
.result-panel h3 {
  margin: 0 0 20px;
  font-size: 22px;
  text-align: center;
}
.dice-stats {
  background: rgba(79, 124, 255, 0.08);
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
}
.stats-title {
  font-size: 13px;
  color: var(--text-dim);
  margin-bottom: 8px;
  text-align: center;
}
.stats-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.stat-item {
  font-size: 14px;
  color: var(--text-main);
  font-weight: 600;
}
.result-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}
.result-item {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 14px 16px;
}
.player-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}
.player-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-main);
}
.host-badge {
  font-size: 14px;
}
.dice-display {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.no-roll {
  font-size: 14px;
  color: var(--text-dim);
}
.lucky-select-section {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 20px;
  margin-bottom: 20px;
}
.section-title {
  font-size: 14px;
  color: var(--gold);
  margin-bottom: 12px;
  text-align: center;
}
.random-count-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--text-dim);
}
.count-input {
  width: 60px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  color: var(--text-main);
  font-size: 15px;
  text-align: center;
  outline: none;
}
.count-input:focus {
  border-color: var(--primary);
  background: rgba(255, 255, 255, 0.12);
}
.manual-select-label {
  font-size: 13px;
  color: var(--text-dim);
  margin-bottom: 8px;
  text-align: center;
}
.lucky-checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.lucky-checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.lucky-checkbox-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.lucky-checkbox-item input[type='checkbox'] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
.result-actions {
  display: flex;
  gap: 12px;
}
.full-width {
  width: 100%;
}
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
