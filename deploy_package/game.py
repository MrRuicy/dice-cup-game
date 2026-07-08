# -*- coding: utf-8 -*-
"""纯游戏逻辑：掷骰、豹子替换、统计、幸运名单计算。

全部为无副作用的纯函数，便于单元测试。核心的隐蔽性靠这里的 roll_dice：
幸运玩家暗中返回豹子，其他人正常随机，调用方无从区分。
"""
import random


def roll_dice(player_id: str, dice_count: int, lucky_set: set[str]) -> list[int]:
    """掷骰。幸运玩家暗中替换为随机豹子（全部点数相同）。

    Args:
        player_id: 投掷者 id
        dice_count: 骰子数量
        lucky_set: 本轮幸运名单
    Returns:
        点数列表，如 [3, 5, 4]；幸运玩家得到如 [5, 5, 5]
    """
    if player_id in lucky_set:
        v = random.randint(1, 6)
        return [v] * dice_count
    return [random.randint(1, 6) for _ in range(dice_count)]


def calc_stats(rolls: dict[str, list[int]]) -> dict[str, int]:
    """全场点数分布统计。

    Returns:
        形如 {"1": 0, "2": 1, ..., "6": 4}
    """
    stats = {str(i): 0 for i in range(1, 7)}
    for dice in rolls.values():
        for d in dice:
            stats[str(d)] += 1
    return stats


def compute_lucky_set(
    all_ids: list[str], manual_ids: list[str], count: int
) -> set[str]:
    """计算下轮幸运名单：手动指定优先，不足人数从剩余玩家随机补齐。

    Args:
        all_ids: 当前所有玩家 id
        manual_ids: 房主手动指定的 id
        count: 幸运嘉宾总人数（0 ~ 玩家数）
    Returns:
        最终幸运名单
    """
    count = max(0, min(count, len(all_ids)))
    # 手动指定只取合法且不超过总数的部分
    valid_manual = [i for i in manual_ids if i in all_ids]
    lucky = set(valid_manual[:count])
    need = count - len(lucky)
    if need > 0:
        remaining = [i for i in all_ids if i not in lucky]
        lucky |= set(random.sample(remaining, min(need, len(remaining))))
    return lucky
