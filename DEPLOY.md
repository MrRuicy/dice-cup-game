# 部署指南

## 📦 生产环境部署

### 一、环境要求

- **服务器**：Ubuntu 20.04+ / CentOS 7+
- **Python**：3.9+
- **Node.js**：18+
- **Nginx**：1.18+
- **域名**：可选，建议配置 HTTPS

---

## 二、部署步骤

### 1. 克隆代码

```bash
git clone https://github.com/your-username/playing-dice.git
cd playing-dice
```

### 2. 后端部署

#### 安装依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 配置环境变量（可选）

```bash
# 创建 .env 文件
cat > .env << EOF
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://yourdomain.com
EOF
```

#### 使用 Systemd 守护进程

```bash
sudo nano /etc/systemd/system/dice-backend.service
```

写入以下内容：

```ini
[Unit]
Description=Playing Dice Backend
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/playing-dice/backend
Environment="PATH=/path/to/playing-dice/backend/venv/bin"
ExecStart=/path/to/playing-dice/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --ws websockets

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable dice-backend
sudo systemctl start dice-backend
sudo systemctl status dice-backend
```

### 3. 前端部署

#### 构建生产版本

```bash
cd frontend
npm install
npm run build
```

构建产物在 `frontend/dist/` 目录。

#### Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/playing-dice
```

写入以下内容：

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 前端静态文件
    root /path/to/playing-dice/frontend/dist;
    index index.html;

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/playing-dice /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. HTTPS 配置（推荐）

使用 Let's Encrypt 免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

证书会自动续期。

---

## 三、Docker 部署（可选）

### Dockerfile 后端

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--ws", "websockets"]
```

### Dockerfile 前端

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

启动：

```bash
docker-compose up -d
```

---

## 四、性能优化

### 1. 前端优化

- ✅ 已启用 Vite 生产构建（自动压缩、Tree-shaking）
- ✅ 静态资源 CDN（可选）
- ✅ Gzip/Brotli 压缩

Nginx 开启 Gzip：

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

### 2. 后端优化

- ✅ WebSocket 连接复用
- ✅ 内存存储（适合小规模）
- 扩展：Redis 作为房间状态存储（大规模）

### 3. 负载均衡（可选）

多后端实例需要共享状态，推荐使用 Redis + Sticky Session。

---

## 五、监控与日志

### 查看后端日志

```bash
sudo journalctl -u dice-backend -f
```

### 查看 Nginx 日志

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 监控工具（可选）

- **Sentry**：前端错误监控
- **Prometheus + Grafana**：服务器指标
- **UptimeRobot**：服务可用性监控

---

## 六、安全建议

1. **CORS 配置**：限制允许的域名
   ```python
   # backend/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **限流**：防止 API 滥用
   ```bash
   # Nginx 限流
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
   ```

3. **防火墙**：只开放必要端口
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

---

## 七、快速启动脚本

创建 `deploy.sh`：

```bash
#!/bin/bash
set -e

echo "🚀 开始部署骰盅游戏..."

# 拉取最新代码
git pull origin main

# 后端
echo "📦 部署后端..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart dice-backend

# 前端
echo "🎨 构建前端..."
cd ../frontend
npm install
npm run build

# 更新 Nginx 静态文件
sudo cp -r dist/* /var/www/playing-dice/

echo "✅ 部署完成！"
echo "访问: http://yourdomain.com"
```

使用：

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 八、故障排查

### WebSocket 连接失败

1. 检查 Nginx WebSocket 配置
2. 检查防火墙是否开放端口
3. 查看后端日志：`journalctl -u dice-backend -f`

### 前端白屏

1. 检查 Nginx 路径配置
2. 查看浏览器控制台错误
3. 确认 API 地址正确

### 房间状态丢失

- 重启后端会清空内存数据
- 生产环境建议使用 Redis 持久化

---

## 九、更新部署

```bash
# 1. 备份（可选）
tar -czf backup-$(date +%Y%m%d).tar.gz backend frontend

# 2. 拉取更新
git pull

# 3. 重新部署
./deploy.sh
```

---

## 十、卸载

```bash
# 停止服务
sudo systemctl stop dice-backend
sudo systemctl disable dice-backend

# 删除文件
sudo rm /etc/systemd/system/dice-backend.service
sudo rm /etc/nginx/sites-enabled/playing-dice
sudo systemctl daemon-reload
sudo systemctl reload nginx

# 删除项目
cd ..
rm -rf playing-dice
```

---

## 🎯 快速部署（最小配置）

如果只是想快速上线测试：

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --ws websockets &

# 前端
cd ../frontend
npm install
npm run build
npx serve -s dist -p 3000
```

访问：`http://your-server-ip:3000`

---

需要帮助？提交 Issue：https://github.com/your-username/playing-dice/issues
