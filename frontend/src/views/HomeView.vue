<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '../stores/game';

const router = useRouter();
const store = useGameStore();

// 面板模式：home 首页 / create 创建 / join 加入
const mode = ref<'home' | 'create' | 'join'>('home');

const nickname = ref('');
const roomCode = ref('');
const password = ref('');
const diceCount = ref(3);

// joined 成功后（roomCode 被赋值）跳转房间页
watch(
  () => store.roomCode,
  (code) => {
    if (code) router.push('/room');
  }
);

function submitCreate() {
  // 昵称可选，为空时后端自动生成
  // 口令由用户输入，后端验证
  store.createRoom(nickname.value.trim(), roomCode.value.trim(), password.value.trim(), diceCount.value);
}

function submitJoin() {
  if (roomCode.value.trim().length !== 4) {
    store.errorMsg = '请输入 4 位房间号';
    return;
  }
  // 昵称可选，为空时后端自动生成
  // 加入房间不需要口令
  store.joinRoom(nickname.value.trim(), roomCode.value.trim(), '');
}
</script>

<template>
  <div class="home">
    <div class="hero">
      <div class="dice-float">🎲</div>
      <h1>骰盅</h1>
      <p class="tagline">摇一摇，掀开你的运气</p>
    </div>

    <div class="panel">
      <!-- 首页两个入口 -->
      <template v-if="mode === 'home'">
        <button class="glass-btn primary" @click="mode = 'create'">+ 创建房间</button>
        <button class="glass-btn" @click="mode = 'join'">→ 加入房间</button>
      </template>

      <!-- 创建房间表单 -->
      <template v-else-if="mode === 'create'">
        <input v-model="nickname" class="field" placeholder="你的昵称（留空自动生成）" maxlength="12" />
        <input v-model="roomCode" class="field" placeholder="房间号（4 位数字，留空随机）" maxlength="4" inputmode="numeric" />
        <input v-model="password" class="field" type="password" placeholder="创建口令" maxlength="20" />
        <div class="dice-select">
          <span>骰子数量</span>
          <div class="stepper">
            <button @click="diceCount = Math.max(1, diceCount - 1)">−</button>
            <span class="num">{{ diceCount }}</span>
            <button @click="diceCount = Math.min(12, diceCount + 1)">+</button>
          </div>
        </div>
        <button class="glass-btn primary" @click="submitCreate">创建</button>
        <button class="glass-btn ghost" @click="mode = 'home'">返回</button>
      </template>

      <!-- 加入房间表单 -->
      <template v-else>
        <input v-model="nickname" class="field" placeholder="你的昵称（留空自动生成）" maxlength="12" />
        <input v-model="roomCode" class="field" placeholder="房间号（4 位数字）" maxlength="4" inputmode="numeric" />
        <button class="glass-btn primary" @click="submitJoin">加入</button>
        <button class="glass-btn ghost" @click="mode = 'home'">返回</button>
      </template>

      <p v-if="store.errorMsg" class="error">{{ store.errorMsg }}</p>
    </div>
  </div>
</template>

<style scoped>
.home {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10vh 28px 8vh;
}
.hero {
  text-align: center;
}
.dice-float {
  font-size: 64px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-14px); }
}
h1 {
  font-size: 44px;
  font-weight: 700;
  letter-spacing: 6px;
  margin: 12px 0 8px;
}
.tagline {
  color: var(--text-dim);
  font-size: 15px;
  margin: 0;
}
.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.field {
  width: 100%;
  padding: 15px 16px;
  font-size: 16px;
  border-radius: var(--radius);
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-main);
  outline: none;
}
.field:focus {
  border-color: var(--primary);
}
.field::placeholder {
  color: var(--text-dim);
}
.dice-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 4px;
  color: var(--text-dim);
  font-size: 15px;
}
.stepper {
  display: flex;
  align-items: center;
  gap: 18px;
}
.stepper button {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--bg-card-2);
  color: var(--text-main);
  font-size: 22px;
}
.stepper .num {
  color: var(--text-main);
  font-size: 20px;
  font-weight: 600;
  min-width: 24px;
  text-align: center;
}
.glass-btn.ghost {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.12);
}
.error {
  text-align: center;
  color: var(--danger);
  font-size: 14px;
  margin: 4px 0 0;
}
</style>
