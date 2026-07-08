# -*- coding: utf-8 -*-
"""M1/M2 联调脚本：模拟房主 + 玩家跑完整回合，并验证幸运嘉宾隐蔽性。

用法：先启动后端，再运行本脚本。
"""
import asyncio
import json

import websockets

URL = "ws://127.0.0.1:8000/ws"


async def recv_until(ws, want_type, timeout=3.0):
    """收消息直到拿到指定 type，返回该消息；沿途消息也返回列表。"""
    seen = []
    while True:
        raw = await asyncio.wait_for(ws.recv(), timeout)
        msg = json.loads(raw)
        seen.append(msg)
        if msg["type"] == want_type:
            return msg, seen


async def drain(ws, timeout=0.5):
    """清空当前缓冲的消息，返回收到的列表。"""
    out = []
    try:
        while True:
            raw = await asyncio.wait_for(ws.recv(), timeout)
            out.append(json.loads(raw))
    except asyncio.TimeoutError:
        return out


async def main():
    host = await websockets.connect(URL)
    guest = await websockets.connect(URL)

    # 1. 房主建房
    await host.send(json.dumps({
        "type": "create_room", "nickname": "房主", "roomCode": "",
        "password": "", "diceCount": 3,
    }))
    joined, _ = await recv_until(host, "joined")
    code = joined["roomCode"]
    host_id = joined["playerId"]
    assert joined["isHost"] is True
    print(f"[OK] 建房成功，房间号={code}，房主id={host_id}")

    # 2. 玩家加入
    await guest.send(json.dumps({
        "type": "join_room", "nickname": "小美", "roomCode": code, "password": "",
    }))
    gjoined, _ = await recv_until(guest, "joined")
    guest_id = gjoined["playerId"]
    assert gjoined["isHost"] is False
    print(f"[OK] 玩家加入成功，id={guest_id}")

    # 3. 房主应收到含 2 人的 room_state
    await drain(host)
    await drain(guest)

    # 4. 房主设幸运嘉宾：指定小美下轮必豹子
    await host.send(json.dumps({
        "type": "set_lucky", "playerIds": [guest_id], "count": 1,
    }))
    await asyncio.sleep(0.2)

    # 5. 房主开始本轮
    await host.send(json.dumps({"type": "start_round"}))
    # 小美应单独收到 lucky_notice，房主不应收到
    gmsgs = await drain(guest)
    hmsgs = await drain(host)
    guest_lucky = any(m["type"] == "lucky_notice" for m in gmsgs)
    host_lucky = any(m["type"] == "lucky_notice" for m in hmsgs)
    assert guest_lucky, "小美应收到幸运提示"
    assert not host_lucky, "房主不应收到幸运提示"
    print("[OK] 幸运提示仅小美收到，房主未收到（隐蔽性 1/2）")

    # 6. 双方投掷
    await host.send(json.dumps({"type": "roll"}))
    hroll, hall = await recv_until(host, "roll_result")
    await guest.send(json.dumps({"type": "roll"}))
    groll, gall = await recv_until(guest, "roll_result")
    print(f"[OK] 房主点数={hroll['dice']}，小美点数={groll['dice']}")
    assert len(set(groll["dice"])) == 1, "小美应为豹子"
    print("[OK] 小美投出豹子（幸运生效）")

    # 关键隐蔽性：房主投掷时收到的任何消息都不含小美的点数
    for m in hall:
        assert "dice" not in m or m["type"] == "roll_result", "广播不应含点数"
    # 房主在小美投掷期间收到的广播 room_state 不含点数字段
    hmid = await drain(host)
    for m in hmid:
        if m["type"] == "room_state":
            for p in m["players"]:
                assert "dice" not in p, "room_state 玩家不应含点数"
    print("[OK] 广播的 room_state 不含任何点数（隐蔽性 2/2）")

    # 7. 房主结束本轮，双方收到 round_result（此时才含全场点数，且无幸运标识）
    await host.send(json.dumps({"type": "end_round"}))
    rr, _ = await recv_until(host, "round_result")
    assert guest_id in rr["results"] and host_id in rr["results"]
    assert "lucky" not in json.dumps(rr), "结果不应含幸运标识"
    print(f"[OK] 结束本轮，全场结果={rr['results']}，统计={rr['stats']}")
    print("[OK] 结果无任何幸运标识")

    await host.close()
    await guest.close()
    print("\n=== 全部联调通过 ===")


asyncio.run(main())
