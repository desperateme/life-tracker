# 人生修仙录 — 部署指南

## 方案对比

| 方案 | 难度 | 月费 | 适合 |
|------|------|------|------|
| 🟢 方案一：Railway/Render | ⭐ 最简单 | 免费/低 | 快速上线，免运维 |
| 🟡 方案二：阿里云/腾讯云 VPS | ⭐⭐ 中等 | ~50-100元 | 国内访问快，完全掌控 |
| 🔵 方案三：Docker 部署 | ⭐⭐⭐ 进阶 | 灵活 | 可迁移，专业运维 |

---

## 方案一：Railway（5 分钟上线，免费额度够用）

> Railway 支持从 GitHub 自动部署 Python 应用

### 步骤

1. **把项目上传到 GitHub**
```bash
cd C:\Users\CoolMoonDes\life-tracker
git init
git add .
git commit -m "init: 人生修仙录 v1"
# 在 GitHub 创建仓库后：
git remote add origin https://github.com/你的用户名/life-tracker.git
git push -u origin main
```

2. **在 Railway 部署**
- 打开 [railway.app](https://railway.app)，用 GitHub 登录
- 点击 「New Project」→「Deploy from GitHub repo」
- 选择 `life-tracker` 仓库
- Railway 自动检测 Python 项目并部署

3. **Railway 会自动读 `requirements.txt` 安装依赖，用 `uvicorn app:app` 启动**

4. **得到网址**：Railway 会给你一个 `xxx.railway.app` 的域名

> ⚠️ 注意：SQLite 在 Railway 上重启会丢失数据。建议改用 Railway 自带的 PostgreSQL（免费额度包含），我下面会说明怎么切换。

---

## 方案二：阿里云/腾讯云轻量应用服务器（国内推荐）

### 买服务器
- 阿里云「轻量应用服务器」或腾讯云「轻量应用服务器」
- 选 **2核2G, CentOS 7/8 或 Ubuntu 20.04**，月费约 50-80 元
- 系统选 **Ubuntu 22.04**（新手友好）

### 连接服务器
```bash
ssh root@你的服务器IP
```

### 一键部署脚本

把下面内容保存为 `deploy.sh`，上传到服务器执行：

```bash
#!/bin/bash
# 人生修仙录 - 服务器部署脚本 (Ubuntu/Debian)

set -e

echo "=== 1. 安装 Python 和依赖 ==="
apt update
apt install -y python3 python3-pip python3-venv nginx

echo "=== 2. 创建应用目录 ==="
mkdir -p /opt/life-tracker
cd /opt/life-tracker

echo "=== 3. 上传代码 ==="
# (手动把项目文件上传到 /opt/life-tracker/)
# 方式 A: git clone
# git clone https://github.com/你的用户名/life-tracker.git .

echo "=== 4. 创建虚拟环境并安装依赖 ==="
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

echo "=== 5. 创建 systemd 服务 ==="
cat > /etc/systemd/system/life-tracker.service << 'EOF'
[Unit]
Description=Life Tracker - 人生修仙录
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/life-tracker
ExecStart=/opt/life-tracker/venv/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "=== 6. 配置 Nginx 反向代理 ==="
cat > /etc/nginx/sites-available/life-tracker << 'EOF'
server {
    listen 80;
    server_name 你的域名或IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /opt/life-tracker/static;
    }
}
EOF

ln -sf /etc/nginx/sites-available/life-tracker /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t

echo "=== 7. 启动服务 ==="
systemctl daemon-reload
systemctl enable life-tracker
systemctl start life-tracker
systemctl restart nginx

echo "=== 部署完成！==="
echo "访问 http://你的服务器IP"
echo ""
echo "查看日志: journalctl -u life-tracker -f"
echo "重启服务: systemctl restart life-tracker"
```

### 手动部署步骤（如果不用脚本）

```bash
# 1. SSH 连接服务器
ssh root@你的IP

# 2. 安装依赖
apt update && apt install -y python3 python3-pip python3-venv nginx git

# 3. 拉取代码
cd /opt
git clone https://github.com/你的用户名/life-tracker.git
cd life-tracker

# 4. 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 5. 测试运行
python app.py
# 看到 "Uvicorn running on..." 说明 OK，Ctrl+C 停掉

# 6. 用 systemd 保持后台运行
nano /etc/systemd/system/life-tracker.service
# 粘贴上面的 service 配置

systemctl daemon-reload
systemctl enable --now life-tracker

# 7. 配置 Nginx
# 编辑 /etc/nginx/sites-available/life-tracker，粘贴上面的 nginx 配置
nginx -t && systemctl restart nginx

# 8. 访问 http://你的IP
```

### 绑定域名（可选）

1. 买个域名（阿里云/腾讯云都行，一年几十块）
2. DNS 解析添加 A 记录指向服务器 IP
3. 申请免费 SSL 证书：
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d 你的域名.com
```
4. 之后就可以用 `https://你的域名.com` 访问了！

---

## 方案三：Docker 部署

### 创建 Dockerfile

项目里我已经放了 `Dockerfile`，构建和运行：

```bash
# 在服务器上
docker build -t life-tracker .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --restart always --name life-tracker life-tracker
```

`-v $(pwd)/data:/app/data` 把 SQLite 数据库挂载到宿主机，容器重启不丢数据。

---

## 关于 SQLite 的说明

当前用 SQLite 单文件存储，**数据库文件在项目目录下的 `life_tracker.db`**。

- ✅ **优点**：零配置，备份只需复制这个文件
- ⚠️ **注意**：部署到 Railway/Render 等 PaaS 平台时，容器重启可能丢失数据

### 数据备份（重要！）

在服务器上设置定时备份：
```bash
# 每天凌晨 3 点备份到 /backup
crontab -e
# 添加：
0 3 * * * cp /opt/life-tracker/life_tracker.db /backup/life_tracker_$(date +\%Y\%m\%d).db
```

---

## 快速选择建议

| 你的情况 | 推荐方案 |
|---------|---------|
| 只想快点上线，免费最好 | **Railway** |
| 国内访问要快，长期用 | **阿里云轻量服务器 + 部署脚本** |
| 已有服务器 | 直接用上面的 systemd + nginx 配置 |
| 想学运维 | Docker 方案 |
