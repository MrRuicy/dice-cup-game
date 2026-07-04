# -*- coding: utf-8 -*-
"""FastAPI 入口：WebSocket 路由 + 消息分发 + 静态前端托管。

服务端权威：所有掷骰、豹子替换、统计都在此裁决，客户端只收展示数据。
每个 action 都做阶段校验与权限校验，前端隐藏按钮不作数。
"""
from __future__ import annotations

import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

import game
import protocol
from manager import GameError, RoomManager
from room import Player, Room, Round

manager = RoomManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动 TTL 回收后台任务。"""
    sweep = asyncio.create_task(manager.sweep_loop())
    yield
    sweep.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    # 当前连接绑定的房间与玩家，握手成功后赋值
    ctx: dict[str, Room | Player | None] = {"room": None, "player": None}
    try:
        while True:
            data = await ws.receive_json()
            await handle_message(ws, ctx, data)
    except WebSocketDisconnect:
        await handle_disconnect(ctx)
    except Exception:
        await handle_disconnect(ctx)


async def handle_message(ws: WebSocket, ctx: dict, data: dict) -> None:
    """按 type 分发消息。"""
    msg_type = data.get("type")
    room: Room | None = ctx["room"]
    player: Player | None = ctx["player"]

    try:
        # ---- 握手类消息（无需已在房间内）----
        if msg_type == protocol.C_CREATE_ROOM:
            await _do_create(ws, ctx, data)
            return
        if msg_type == protocol.C_JOIN_ROOM:
            await _do_join(ws, ctx, data)
            return
        if msg_type == protocol.C_RECONNECT:
            await _do_reconnect(ws, ctx, data)
            return

        # ---- 其余消息要求已在房间内 ----
        if room is None or player is None:
            raise GameError(protocol.ERR_INVALID_INPUT, "尚未加入房间")

        if msg_type == protocol.C_START_ROUND:
            await _do_start_round(room, player)
        elif msg_type == protocol.C_ROLL:
            await _do_roll(room, player)
        elif msg_type == protocol.C_END_ROUND:
            await _do_end_round(room, player)
        elif msg_type == protocol.C_SET_LUCKY:
            await _do_set_lucky(room, player, data)
        elif msg_type == protocol.C_NEXT_ROUND:
            await _do_next_round(room, player)
        elif msg_type == protocol.C_LEAVE:
            await _do_leave(ctx)
        elif msg_type == protocol.C_DISMISS:
            await _do_dismiss(room, player)
        else:
            raise GameError(protocol.ERR_INVALID_INPUT, f"未知消息类型: {msg_type}")
    except GameError as e:
        await ws.send_json({"type": protocol.S_ERROR, "code": e.code, "msg": e.msg})


# ---------------- 握手 ----------------

def _validate_join_input(nickname: str) -> None:
    if not nickname or len(nickname) > protocol.NICKNAME_MAX_LEN:
        raise GameError(protocol.ERR_INVALID_INPUT, "昵称长度非法")


async def _do_create(ws: WebSocket, ctx: dict, data: dict) -> None:
    nickname = (data.get("nickname") or "").strip()
    room_code = (data.get("roomCode") or "").strip()
    if room_code and (len(room_code) != protocol.ROOM_CODE_LEN or not room_code.isdigit()):
        raise GameError(protocol.ERR_INVALID_INPUT, "房间号需为 4 位数字")

    # 验证创建口令（硬编码）
    password = (data.get("password") or "").strip()
    if password != protocol.CREATE_PASSWORD:
        raise GameError(protocol.ERR_WRONG_PASSWORD, "创建口令错误")

    dice_count = int(data.get("diceCount") or 3)
    if not protocol.DICE_COUNT_MIN <= dice_count <= protocol.DICE_COUNT_MAX:
        raise GameError(protocol.ERR_INVALID_INPUT, "骰子数量非法")

    room, player = await manager.create_room(
        nickname, room_code, password, dice_count, ws
    )
    ctx["room"], ctx["player"] = room, player
    await _send_joined(room, player)
    await manager.broadcast_state(room)


async def _do_join(ws: WebSocket, ctx: dict, data: dict) -> None:
    nickname = (data.get("nickname") or "").strip()
    room_code = (data.get("roomCode") or "").strip()
    room, player = await manager.join_room(
        nickname, room_code, ws
    )
    ctx["room"], ctx["player"] = room, player
    await _send_joined(room, player)
    await manager.broadcast_state(room)


async def _do_reconnect(ws: WebSocket, ctx: dict, data: dict) -> None:
    token = (data.get("token") or "").strip()
    print(f"[RECONNECT] token={token[:8]}...", file=sys.stderr, flush=True)
    room, player = await manager.reconnect(token, ws)
    ctx["room"], ctx["player"] = room, player
    await _send_joined(room, player)

    # 重连后恢复当前回合状态
    rnd = room.current_round
    print(f"[RECONNECT] room={room.code}, player={player.nickname}, round={rnd.index if rnd else None}, phase={rnd.phase if rnd else None}", file=sys.stderr, flush=True)
    if rnd:
        # 补发本人的投掷结果（若已投掷）
        if rnd.has_rolled(player.id):
            is_lucky = player.id in rnd.lucky_set
            print(f"[RECONNECT] 补发投掷结果: dice={rnd.rolls[player.id]}, isLucky={is_lucky}", file=sys.stderr, flush=True)
            await manager.send(player, {
                "type": protocol.S_ROLL_RESULT,
                "dice": rnd.rolls[player.id],
                "isLucky": is_lucky,
            })

        # 如果当前在 ended 阶段，补发统计结果
        if rnd.phase == protocol.PHASE_ENDED:
            print(f"[RECONNECT] 补发统计结果: results={list(rnd.rolls.keys())}, stats={rnd.stats}", file=sys.stderr, flush=True)
            await manager.send(player, {
                "type": protocol.S_ROUND_RESULT,
                "results": rnd.rolls,
                "stats": rnd.stats or {},
            })

    # 只向重连的玩家单发房间状态，不广播
    await manager.send(player, {
        "type": protocol.S_ROOM_STATE,
        "hostId": room.host_id,
        "round": rnd.index if rnd else 0,
        "phase": rnd.phase if rnd else protocol.PHASE_WAITING,
        "diceCount": room.dice_count,
        "players": room.public_players(),
    })


async def _send_joined(room: Room, player: Player) -> None:
    is_host = room.is_host(player.id)
    print(f"[_send_joined] player={player.nickname}, player.id={player.id}, room.host_id={room.host_id}, isHost={is_host}", file=sys.stderr, flush=True)
    await manager.send(player, {
        "type": protocol.S_JOINED,
        "playerId": player.id,
        "token": player.token,
        "isHost": is_host,
        "roomCode": room.code,
        "diceCount": room.dice_count,
    })


# ---------------- 游戏动作 ----------------

def _require_host(room: Room, player: Player) -> None:
    if not room.is_host(player.id):
        raise GameError(protocol.ERR_NOT_HOST, "仅房主可操作")


async def _do_start_round(room: Room, player: Player) -> None:
    _require_host(room, player)
    idx = (room.current_round.index + 1) if room.current_round else 1
    # 本轮幸运名单来自房主上一轮设置的 next_lucky_set
    lucky = set(room.next_lucky_set)
    room.current_round = Round(index=idx, phase=protocol.PHASE_ROLLING, lucky_set=lucky)
    room.next_lucky_set = set()
    for p in room.players.values():
        p.status = protocol.STATUS_WAITING
    room.touch()
    # 先广播房间状态,再向幸运玩家单发提示(避免前端 resetRoundView 清除 isLucky)
    await manager.broadcast_state(room)
    for pid in lucky:
        lp = room.players.get(pid)
        if lp:
            await manager.send(lp, {"type": protocol.S_LUCKY_NOTICE})


async def _do_roll(room: Room, player: Player) -> None:
    rnd = room.current_round
    if rnd is None or rnd.phase != protocol.PHASE_ROLLING:
        raise GameError(protocol.ERR_INVALID_PHASE, "当前不可投掷")
    if rnd.has_rolled(player.id):
        # 幂等：重复投掷返回已有结果，不重新掷
        is_lucky = player.id in rnd.lucky_set
        await manager.send(player, {
            "type": protocol.S_ROLL_RESULT, "dice": rnd.rolls[player.id], "isLucky": is_lucky,
        })
        return
    dice = game.roll_dice(player.id, room.dice_count, rnd.lucky_set)
    rnd.rolls[player.id] = dice
    player.status = protocol.STATUS_ROLLED
    room.touch()
    # 点数只发本人，并告知是否是幸运嘉宾
    is_lucky = player.id in rnd.lucky_set
    await manager.send(player, {"type": protocol.S_ROLL_RESULT, "dice": dice, "isLucky": is_lucky})
    # 广播只更新状态（不含点数）
    await manager.broadcast_state(room)


async def _do_end_round(room: Room, player: Player) -> None:
    _require_host(room, player)
    rnd = room.current_round
    if rnd is None or rnd.phase != protocol.PHASE_ROLLING:
        raise GameError(protocol.ERR_INVALID_PHASE, "当前无进行中的回合")
    rnd.phase = protocol.PHASE_ENDED
    # 计算并存储统计数据，供重连时使用
    rnd.stats = game.calc_stats(rnd.rolls)
    room.touch()
    # 结束本轮才下发全场结果 + 统计，所有人平等，无幸运标识
    await manager.broadcast(room, {
        "type": protocol.S_ROUND_RESULT,
        "results": rnd.rolls,
        "stats": rnd.stats,
    })
    await manager.broadcast_state(room)


async def _do_set_lucky(room: Room, player: Player, data: dict) -> None:
    _require_host(room, player)
    manual = data.get("playerIds") or []
    count = int(data.get("count") or 0)
    all_ids = list(room.players.keys())
    room.next_lucky_set = game.compute_lucky_set(all_ids, manual, count)
    room.touch()
    # 仅房主本地暂存，不广播（保持隐蔽）


async def _do_next_round(room: Room, player: Player) -> None:
    _require_host(room, player)
    await _do_start_round(room, player)


async def _do_leave(ctx: dict) -> None:
    room: Room = ctx["room"]
    player: Player = ctx["player"]
    destroyed = await manager.remove_player(room, player.id)
    if destroyed:
        await manager.broadcast(room, {"type": protocol.S_ROOM_DISMISSED})
    else:
        await manager.broadcast_state(room)
    ctx["room"], ctx["player"] = None, None


async def _do_dismiss(room: Room, player: Player) -> None:
    _require_host(room, player)
    await manager.broadcast(room, {"type": protocol.S_ROOM_DISMISSED})
    await manager.dismiss_room(room.code)


async def handle_disconnect(ctx: dict) -> None:
    """连接断开：标记离线，30s 后若未重连则踢出（房主断线解散房间）。"""
    room: Room | None = ctx["room"]
    player: Player | None = ctx["player"]
    if room is None or player is None:
        return

    # 标记离线
    manager.mark_offline(room, player.id)
    await manager.broadcast_state(room)

    # 启动 30 秒延迟任务：若仍离线，则踢出
    asyncio.create_task(_delayed_kick(room.code, player.id, room.is_host(player.id)))


async def _delayed_kick(room_code: str, player_id: str, is_host: bool) -> None:
    """30 秒后检查玩家是否仍然离线，若是则踢出（房主解散房间）。"""
    await asyncio.sleep(30)

    room = await manager.get_room(room_code)
    if room is None:
        return  # 房间已不存在

    player = room.players.get(player_id)
    if player is None:
        return  # 玩家已被移除

    if player.ws is not None:
        return  # 玩家已重连，不踢出

    # 玩家仍然离线，执行踢出
    if is_host:
        # 房主断线：解散房间
        await manager.broadcast(room, {"type": protocol.S_ROOM_DISMISSED})
        await manager.dismiss_room(room_code)
    else:
        # 普通玩家：移除玩家
        await manager.remove_player(room, player_id)
        await manager.broadcast_state(room)


# ---------------- 前端静态托管（放最后，避免通配符覆盖 /ws 与 /health）----------------

_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="static")
