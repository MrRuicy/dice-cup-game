# 🎲 骰盅游戏 (Dice Cup Game)

一个基于 WebSocket 的实时多人在线骰盅游戏，支持房间管理、多轮投掷、幸运嘉宾机制等功能。

## ✨ 特性

- 🎮 **实时多人对战** - 基于 WebSocket 的低延迟实时通信
- 🏠 **房间系统** - 支持创建/加入房间，房主控制游戏流程
- 🎲 **骰盅动画** - 流畅的摇晃动画和掀盅交互
- ✨ **幸运嘉宾** - 房主可秘密指定幸运玩家，修改其点数
- 📊 **统计面板** - 实时展示各玩家投掷结果和点数统计
- 🔄 **断线重连** - 刷新页面自动恢复游戏状态
- 📱 **响应式设计** - 支持桌面和移动端

## 🎯 游戏流程

1. **创建/加入房间**
   - 房主创建房间并设置口令（可选）
   - 其他玩家通过房间号加入（加入无需口令）
   - 支持 3-12 个骰子数量配置

2. **开始游戏**
   - 房主点击"开始本轮"进入投掷阶段
   - 所有玩家看到静置的骰盅

3. **投掷骰子**
   - 每位玩家点击"投掷"按钮
   - 骰盅播放摇晃动画（约2.5秒）
   - 动画完成后骰子封存在盅内

4. **结束回合**
   - 房主点击"结束本轮"
   - 系统展示统计面板，显示所有玩家点数
   - 可掀盅查看自己的骰子

5. **幸运嘉宾机制**（可选）
   - 房主在统计面板中勾选幸运玩家
   - 下一轮开始时，幸运玩家的点数自动调整为"豹子6"
   - 仅幸运玩家本人知道（显示魔法提示）

## 🛠️ 技术栈

### 前端
- **Vue 3** - 渐进式前端框架
- **TypeScript** - 类型安全
- **Pinia** - 状态管理
- **GSAP** - 高性能动画
- **WebSocket** - 实时通信

### 后端
- **FastAPI** - 现代异步 Web 框架
- **Python 3.10+** - 后端语言
- **WebSocket** - 实时推送

## 📦 安装与运行

### 前置要求
- Node.js 18+
- Python 3.10+
- npm 或 pnpm

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 开始游戏。

## 🚀 生产部署

详细部署文档请查看 [DEPLOY.md](./DEPLOY.md)，包含：
- Systemd + Nginx 部署
- Docker 部署
- HTTPS 配置
- 性能优化建议

## 📁 项目结构

```
.
├── backend/              # 后端代码
│   ├── main.py          # FastAPI 入口
│   ├── game.py          # 游戏逻辑
│   ├── room.py          # 房间管理
│   ├── manager.py       # WebSocket 连接管理
│   ├── protocol.py      # 消息协议定义
│   └── smoke_test.py    # 集成测试
│
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── components/  # Vue 组件
│   │   │   ├── Dice.vue           # 骰子组件
│   │   │   └── DiceCupGame.vue    # 骰盅游戏组件
│   │   ├── views/       # 页面视图
│   │   │   ├── HomeView.vue       # 首页
│   │   │   └── RoomView.vue       # 游戏房间
│   │   ├── stores/      # Pinia 状态管理
│   │   │   └── game.ts            # 游戏状态
│   │   ├── services/    # 服务层
│   │   │   └── ws.ts              # WebSocket 客户端
│   │   └── types.ts     # TypeScript 类型定义
│   │
│   ├── package.json
│   └── vite.config.ts
│
└── README.md            # 本文档
```

## 🎮 核心功能说明

### 断线重连机制
- 使用 `sessionStorage` 存储 token，实现标签页隔离
- 刷新页面自动重连，恢复房间状态
- 已投掷的骰盅直接显示settled状态，跳过动画

### 幸运嘉宾机制
- 房主在统计面板中可勾选1-N个幸运玩家
- 支持随机选择N人
- 下一轮开始时，幸运玩家的点数自动调整为[6,6,6,...]
- 仅幸运玩家本人看到"✨你被施了魔法"提示

### 房间口令
- 创建房间时可设置口令（用于防止房主误操作）
- 加入房间无需口令（便于快速加入）
- 房主操作（开始/结束本轮、解散房间、调整骰子数）需要验证口令

## 📝 开发说明

### 消息协议
前后端通过 WebSocket 交换 JSON 消息，主要消息类型：
- `create_room` / `join_room` - 房间操作
- `start_round` / `end_round` - 回合控制
- `roll` - 投掷骰子
- `room_state` - 房间状态同步
- `roll_result` - 投掷结果
- `round_result` - 回合结束统计

### 状态管理
使用 Pinia 集中管理游戏状态：
- 房间信息（房间号、房主、玩家列表）
- 回合状态（轮次、阶段、已投掷人数）
- 个人数据（我的点数、是否幸运玩家）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🎉 致谢

感谢所有为这个项目做出贡献的开发者！
