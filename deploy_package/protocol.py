# -*- coding: utf-8 -*-
"""WebSocket 消息类型常量与校验。

前后端共同的通信契约。客户端消息类型以 C_ 前缀，服务端消息类型以 S_ 前缀。
"""

# ---- 客户端 → 服务端 ----
C_CREATE_ROOM = "create_room"    # 创建房间
C_JOIN_ROOM = "join_room"        # 加入房间
C_RECONNECT = "reconnect"        # 断线重连
C_START_ROUND = "start_round"    # 开始本轮（仅房主）
C_ROLL = "roll"                  # 投掷
C_END_ROUND = "end_round"        # 结束本轮（仅房主）
C_SET_LUCKY = "set_lucky"        # 设置下轮幸运嘉宾（仅房主）
C_NEXT_ROUND = "next_round"      # 开始下一轮（仅房主）
C_LEAVE = "leave"                # 玩家退出
C_DISMISS = "dismiss"            # 解散房间（仅房主）

# ---- 服务端 → 客户端 ----
S_JOINED = "joined"              # 加入成功，下发身份凭证
S_ROOM_STATE = "room_state"      # 房间状态广播（不含点数、不含幸运标记）
S_ROLL_RESULT = "roll_result"    # 掷骰结果（仅发投掷者本人）
S_LUCKY_NOTICE = "lucky_notice"  # 幸运提示（仅发被选中玩家）
S_ROUND_RESULT = "round_result"  # 结束本轮，下发全场结果 + 统计（广播）
S_ROOM_DISMISSED = "room_dismissed"  # 房间已解散
S_ERROR = "error"                # 错误

# ---- 回合阶段 ----
PHASE_WAITING = "waiting"        # 等待房主开始
PHASE_ROLLING = "rolling"        # 投掷中
PHASE_ENDED = "ended"            # 已结束，展示统计

# ---- 玩家状态 ----
STATUS_WAITING = "waiting"       # 等待投掷
STATUS_ROLLED = "rolled"         # 已投掷
STATUS_INACTIVE = "inactive"     # 未参与本轮 / 断线

# ---- 错误码 ----
ERR_ROOM_NOT_FOUND = "ROOM_NOT_FOUND"      # 房间不存在
ERR_ROOM_EXISTS = "ROOM_EXISTS"            # 房间号已存在
ERR_WRONG_PASSWORD = "WRONG_PASSWORD"      # 口令错误
ERR_NOT_HOST = "NOT_HOST"                  # 非房主，无权限
ERR_INVALID_PHASE = "INVALID_PHASE"        # 当前阶段不允许该操作
ERR_ALREADY_ROLLED = "ALREADY_ROLLED"      # 本轮已投掷
ERR_INVALID_INPUT = "INVALID_INPUT"        # 输入非法
ERR_NICKNAME_TAKEN = "NICKNAME_TAKEN"      # 昵称已被占用
ERR_INVALID_TOKEN = "INVALID_TOKEN"        # 重连凭证无效

# ---- 输入约束 ----
NICKNAME_MAX_LEN = 12            # 昵称最大长度
ROOM_CODE_LEN = 4                # 房间号位数
DICE_COUNT_MIN = 1               # 骰子数下限
DICE_COUNT_MAX = 12              # 骰子数上限
CREATE_PASSWORD = "rui"          # 创建房间的口令（硬编码）
