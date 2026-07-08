# -*- coding: utf-8 -*-
"""房间管理器：房间增删查、玩家进出、消息广播/单发、TTL 回收。

所有对房间状态的写操作都在 asyncio.Lock 保护下进行，防止并发竞争。
广播只发公共状态（不含点数/幸运标记），点数与幸运提示走点对点单发。
"""
from __future__ import annotations

import asyncio
import random
import time
import uuid

import protocol
from room import Player, Room, Round

# 房间空闲多久后回收（秒）
ROOM_TTL = 30 * 60
# 回收扫描间隔（秒）
SWEEP_INTERVAL = 60


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._lock = asyncio.Lock()

    # ---------- 房间生命周期 ----------

    async def create_room(
        self, nickname: str, room_code: str, password: str, dice_count: int, ws
    ) -> tuple[Room, Player]:
        """创建房间。room_code 为空则随机生成；已存在则抛错。昵称为空时自动生成。"""
        async with self._lock:
            if room_code:
                if room_code in self._rooms:
                    raise GameError(protocol.ERR_ROOM_EXISTS, "房间号已存在")
            else:
                room_code = self._gen_room_code()

            # 创建临时房间用于生成昵称
            temp_room = Room(
                code=room_code,
                host_id="",
                dice_count=dice_count,
                password=password,
            )
            # 昵称为空时自动生成
            if not nickname:
                nickname = self._gen_nickname(temp_room)

            host = self._new_player(nickname, ws)
            room = Room(
                code=room_code,
                host_id=host.id,
                dice_count=dice_count,
                password=password,
            )
            room.players[host.id] = host
            self._rooms[room_code] = room
            return room, host

    async def join_room(
        self, nickname: str, room_code: str, ws
    ) -> tuple[Room, Player]:
        """加入房间。校验房间存在、昵称唯一（为空时自动生成）。"""
        async with self._lock:
            room = self._rooms.get(room_code)
            if room is None:
                raise GameError(protocol.ERR_ROOM_NOT_FOUND, "房间不存在")

            # 昵称为空时自动生成"玩家1"、"玩家2"...
            if not nickname:
                nickname = self._gen_nickname(room)
            elif any(p.nickname == nickname for p in room.players.values()):
                raise GameError(protocol.ERR_NICKNAME_TAKEN, "昵称已被占用")

            player = self._new_player(nickname, ws)
            room.players[player.id] = player
            room.touch()
            return room, player

    async def reconnect(self, token: str, ws) -> tuple[Room, Player]:
        """凭 token 断线重连，恢复身份与连接。"""
        async with self._lock:
            for room in self._rooms.values():
                for p in room.players.values():
                    if p.token == token:
                        p.ws = ws
                        room.touch()
                        return room, p
            raise GameError(protocol.ERR_INVALID_TOKEN, "重连凭证无效")

    async def get_room(self, room_code: str) -> Room | None:
        return self._rooms.get(room_code)

    async def remove_player(self, room: Room, player_id: str) -> bool:
        """移除玩家。返回房间是否因此被销毁（房主退出或房间空）。"""
        async with self._lock:
            room.players.pop(player_id, None)
            if room.is_host(player_id) or not room.players:
                self._rooms.pop(room.code, None)
                return True
            room.touch()
            return False

    async def dismiss_room(self, room_code: str) -> None:
        async with self._lock:
            self._rooms.pop(room_code, None)

    def mark_offline(self, room: Room, player_id: str) -> None:
        """标记玩家离线（不移除，保留 token 供重连）。"""
        p = room.players.get(player_id)
        if p:
            p.ws = None
            p.status = protocol.STATUS_INACTIVE

    # ---------- 消息发送 ----------

    async def send(self, player: Player, message: dict) -> None:
        """向单个玩家发送消息（点对点，用于 roll_result / lucky_notice）。"""
        if player.ws is None:
            return
        try:
            await player.ws.send_json(message)
        except Exception:
            player.ws = None

    async def broadcast(self, room: Room, message: dict) -> None:
        """向房间所有在线玩家广播（仅公共状态）。"""
        for p in list(room.players.values()):
            await self.send(p, message)

    async def broadcast_state(self, room: Room) -> None:
        """广播房间公共状态：只含玩家状态，绝不含点数或幸运标记。"""
        rnd = room.current_round
        message = {
            "type": protocol.S_ROOM_STATE,
            "hostId": room.host_id,
            "round": rnd.index if rnd else 0,
            "phase": rnd.phase if rnd else protocol.PHASE_WAITING,
            "diceCount": room.dice_count,
            "players": room.public_players(),
        }
        await self.broadcast(room, message)

    # ---------- 内部工具 ----------

    def _new_player(self, nickname: str, ws) -> Player:
        return Player(
            id=uuid.uuid4().hex[:8],
            nickname=nickname,
            token=uuid.uuid4().hex,
            ws=ws,
        )

    def _gen_room_code(self) -> str:
        """生成不重复的 4 位数字房间号。"""
        for _ in range(100):
            code = f"{random.randint(0, 9999):04d}"
            if code not in self._rooms:
                return code
        raise GameError(protocol.ERR_ROOM_EXISTS, "房间已满，请稍后再试")

    def _gen_nickname(self, room: Room) -> str:
        """生成不重复的昵称：玩家1、玩家2..."""
        existing = {p.nickname for p in room.players.values()}
        for i in range(1, 1000):
            nickname = f"玩家{i}"
            if nickname not in existing:
                return nickname
        raise GameError(protocol.ERR_INVALID_INPUT, "无法生成昵称")

    # ---------- TTL 回收 ----------

    async def sweep_loop(self) -> None:
        """后台任务：定期回收空闲房间。"""
        while True:
            await asyncio.sleep(SWEEP_INTERVAL)
            now = time.time()
            async with self._lock:
                stale = [
                    code for code, r in self._rooms.items()
                    if now - r.last_active > ROOM_TTL
                ]
                for code in stale:
                    self._rooms.pop(code, None)


class GameError(Exception):
    """携带错误码的业务异常，供 main.py 转成 error 消息下发。"""

    def __init__(self, code: str, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg
