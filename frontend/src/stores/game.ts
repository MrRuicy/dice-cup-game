// 游戏状态中枢：房间/玩家/回合，以及所有服务端消息的处理
import { defineStore } from 'pinia';
import { wsClient } from '../services/ws';
import type { ClientMessage, PublicPlayer, ServerMessage } from '../types';

interface GameState {
  connected: boolean;
  playerId: string;
  token: string;
  isHost: boolean;
  roomCode: string;
  diceCount: number;
  players: PublicPlayer[];
  hostId: string;
  round: number;
  phase: 'waiting' | 'rolling' | 'ended';
  myDice: number[] | null; // 本轮我的点数
  isReconnect: boolean; // 是否是重连恢复（用于跳过动画）
  isLucky: boolean; // 是否被施魔法（仅本人可见）
  results: Record<string, number[]> | null; // 结束本轮的全场结果
  stats: Record<string, number> | null;
  errorMsg: string; // 最近一次错误提示
  dismissed: boolean; // 房间是否已解散
}

export const useGameStore = defineStore('game', {
  state: (): GameState => ({
    connected: false,
    playerId: '',
    token: '',
    isHost: false,
    roomCode: '',
    diceCount: 3,
    players: [],
    hostId: '',
    round: 0,
    phase: 'waiting',
    myDice: null,
    isReconnect: false,
    isLucky: false,
    results: null,
    stats: null,
    errorMsg: '',
    dismissed: false,
  }),

  getters: {
    // 我在玩家列表中的信息
    me: (s): PublicPlayer | undefined => s.players.find((p) => p.id === s.playerId),
    // 已投掷人数 / 总人数
    rolledCount: (s) => s.players.filter((p) => p.status === 'rolled').length,
  },

  actions: {
    // ---- 连接管理 ----
    ensureConnected() {
      wsClient.connect(
        (msg) => this.handleMessage(msg),
        () => {
          // 重连成功后，用 token 恢复身份
          if (this.token) this.send({ type: 'reconnect', token: this.token });
        }
      );
    },

    send(msg: ClientMessage) {
      wsClient.send(msg);
    },

    // ---- 发起动作 ----
    createRoom(nickname: string, roomCode: string, password: string, diceCount: number) {
      this.ensureConnected();
      this.send({ type: 'create_room', nickname, roomCode, password, diceCount });
    },
    joinRoom(nickname: string, roomCode: string, password: string) {
      this.ensureConnected();
      this.send({ type: 'join_room', nickname, roomCode, password });
    },
    startRound() {
      this.send({ type: 'start_round' });
    },
    roll() {
      this.send({ type: 'roll' });
    },
    endRound() {
      this.send({ type: 'end_round' });
    },
    setLucky(playerIds: string[], count: number) {
      this.send({ type: 'set_lucky', playerIds, count });
    },
    nextRound() {
      this.send({ type: 'next_round' });
    },
    leave() {
      this.send({ type: 'leave' });
      wsClient.close();
      this.reset();
    },

    // ---- 消息处理 ----
    handleMessage(msg: ServerMessage) {
      console.log('[STORE] 收到消息:', msg.type, msg);
      switch (msg.type) {
        case 'joined':
          this.connected = true;
          this.playerId = msg.playerId;
          this.token = msg.token;
          this.isHost = msg.isHost;
          this.roomCode = msg.roomCode;
          this.diceCount = msg.diceCount;
          // 使用 sessionStorage 存储 token，实现标签页隔离
          sessionStorage.setItem('dice_token', msg.token);
          sessionStorage.setItem('dice_room', msg.roomCode);
          console.log('[STORE] joined - roomCode:', msg.roomCode, 'isHost:', msg.isHost);
          break;
        case 'room_state':
          console.log('[STORE] room_state - phase:', msg.phase, 'round:', msg.round);
          console.log('[STORE] room_state - 当前 prevPhase:', this.phase, '→ 新 phase:', msg.phase);
          console.log('[STORE] room_state - 当前 round:', this.round, '→ 新 round:', msg.round);
          this.hostId = msg.hostId;
          this.diceCount = msg.diceCount;
          this.players = msg.players;

          // 延迟更新 phase，确保 round_result 先被处理
          // 这样在 ended 阶段刷新时，results 能先到达
          const prevPhase = this.phase;
          const prevRound = this.round;
          this.round = msg.round;

          if (msg.phase === 'ended') {
            setTimeout(() => {
              console.log('[STORE] 延迟设置 phase = ended');
              this.phase = msg.phase;
            }, 50);
          } else {
            this.phase = msg.phase;
          }

          // 新一轮开始的判断：round 增加（但排除刷新重连的情况）
          // prevRound === 0 表示刚初始化，不应该清空数据
          const isNewRound = msg.round > prevRound && prevRound !== 0;
          if (isNewRound) {
            console.log('[STORE] 检测到新一轮开始 (round 增加)，清空统计数据');
            this.results = null;
            this.stats = null;
            // myDice 由 roll_result 消息管理，这里不清空
          } else {
            console.log('[STORE] 同一轮内的状态更新，保留所有数据');
          }
          break;
        case 'roll_result':
          console.log('[STORE] 收到 roll_result:', msg);
          console.log('[STORE] 设置前 myDice:', this.myDice);
          this.myDice = msg.dice;
          console.log('[STORE] 设置后 myDice:', this.myDice);
          this.isReconnect = msg.isReconnect || false;
          console.log('[STORE] isReconnect:', this.isReconnect);
          // 如果是幸运嘉宾，显示提示，1秒后自动关闭
          if (msg.isLucky) {
            console.log('[STORE] 设置 isLucky = true');
            this.isLucky = true;
            const store = this;
            setTimeout(() => {
              console.log('[STORE] 自动关闭 isLucky');
              store.isLucky = false;
            }, 1000);
          }
          break;
        case 'lucky_notice':
          // 已废弃，改用 roll_result 里的 isLucky 字段
          break;
        case 'round_result':
          console.log('[STORE] round_result - results:', Object.keys(msg.results), 'stats:', msg.stats);
          this.results = msg.results;
          this.stats = msg.stats;
          break;
        case 'room_dismissed':
          this.dismissed = true;
          wsClient.close();
          break;
        case 'error':
          this.errorMsg = msg.msg;
          break;
      }
    },

    // 新一轮：清空本地投掷视图状态（供 RoomView 调用）
    resetRoundView() {
      this.myDice = null;
      // 不清除 isLucky - 幸运提示应该在投掷后保留到用户点击关闭
    },

    reset() {
      // 清除 sessionStorage 中的 token
      sessionStorage.removeItem('dice_token');
      sessionStorage.removeItem('dice_room');
      this.$reset();
    },
  },
});
