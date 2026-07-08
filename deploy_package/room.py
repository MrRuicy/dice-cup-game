# -*- coding: utf-8 -*-
"""房间领域模型：Player / Round / Room。

纯数据结构 + 少量与自身状态相关的方法，不含广播/网络逻辑（那些在 manager.py）。
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import protocol

if TYPE_CHECKING:
    from fastapi import WebSocket


@dataclass
class Player:
    """房间内的玩家。"""
    id: str                              # 服务端生成的 uuid
    nickname: str
    token: str                           # 断线重连凭证
    ws: "WebSocket | None" = None        # 当前连接，断线时置 None
    status: str = protocol.STATUS_WAITING

    @property
    def online(self) -> bool:
        return self.ws is not None


@dataclass
class Round:
    """一个回合。"""
    index: int
    phase: str = protocol.PHASE_WAITING
    rolls: dict[str, list[int]] = field(default_factory=dict)   # pid -> 点数列表
    lucky_set: set[str] = field(default_factory=set)            # 本轮幸运名单
    stats: dict | None = None                                    # 结束时的统计数据

    def has_rolled(self, player_id: str) -> bool:
        return player_id in self.rolls


@dataclass
class Room:
    """一个游戏房间。"""
    code: str                            # 4 位数字房间号
    host_id: str
    dice_count: int
    password: str = ""                   # 创建口令，可空
    players: dict[str, Player] = field(default_factory=dict)
    current_round: Round | None = None
    next_lucky_set: set[str] = field(default_factory=set)       # 房主设的下轮名单
    last_active: float = field(default_factory=time.time)

    def touch(self) -> None:
        """更新活跃时间，用于 TTL 回收。"""
        self.last_active = time.time()

    def is_host(self, player_id: str) -> bool:
        return player_id == self.host_id

    def public_players(self) -> list[dict]:
        """对外广播的玩家列表：只含 id/昵称/状态，绝不含点数或幸运标记。"""
        return [
            {"id": p.id, "nickname": p.nickname, "status": p.status}
            for p in self.players.values()
        ]
