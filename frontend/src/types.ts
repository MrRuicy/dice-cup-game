// WebSocket 消息类型定义，与后端 protocol.py 对应

// 玩家公共状态（广播，不含点数）
export interface PublicPlayer {
  id: string;
  nickname: string;
  status: 'waiting' | 'rolled' | 'inactive';
}

// 服务端 → 客户端 消息
export type ServerMessage =
  | {
      type: 'joined';
      playerId: string;
      token: string;
      isHost: boolean;
      roomCode: string;
      diceCount: number;
    }
  | {
      type: 'room_state';
      hostId: string;
      round: number;
      phase: 'waiting' | 'rolling' | 'ended';
      diceCount: number;
      players: PublicPlayer[];
    }
  | { type: 'roll_result'; dice: number[]; isLucky?: boolean }
  | { type: 'lucky_notice' }
  | {
      type: 'round_result';
      results: Record<string, number[]>;
      stats: Record<string, number>;
    }
  | { type: 'room_dismissed' }
  | { type: 'error'; code: string; msg: string };

// 客户端 → 服务端 消息
export type ClientMessage =
  | {
      type: 'create_room';
      nickname: string;
      roomCode: string;
      password: string;
      diceCount: number;
    }
  | { type: 'join_room'; nickname: string; roomCode: string; password: string }
  | { type: 'reconnect'; token: string }
  | { type: 'start_round' }
  | { type: 'roll' }
  | { type: 'end_round' }
  | { type: 'set_lucky'; playerIds: string[]; count: number }
  | { type: 'next_round' }
  | { type: 'leave' }
  | { type: 'dismiss' };
