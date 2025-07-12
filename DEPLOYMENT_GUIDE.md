# Omega更新服务器 - 详细部署指南

本指南将详细介绍如何部署Omega更新服务器增强版。

## 📋 部署前准备

### 1. 服务器要求

**最低配置:**
- CPU: 2核心
- 内存: 4GB RAM
- 存储: 40GB SSD
- 网络: 100Mbps带宽
- 操作系统: Ubuntu 22.04 LTS

**推荐配置:**
- CPU: 4核心
- 内存: 8GB RAM
- 存储: 80GB SSD
- 网络: 1Gbps带宽

### 2. 客户端要求

**Windows客户端:**
- Windows 10/11
- PowerShell 5.0+
- Python 3.8+
- Git (可选)

### 3. 网络配置

**防火墙端口:**
```bash
# HTTP服务
80/tcp

# HTTPS服务 (可选)
443/tcp

# SSH管理
22/tcp
```

**域名配置 (可选):**
- A记录: update.yourdomain.com → 服务器IP
- CNAME记录: api.yourdomain.com → update.yourdomain.com

## 🚀 自动部署 (推荐)

### 1. 准备工作

```powershell
# 克隆项目
git clone <repository-url>
cd omega-update

# 检查必要文件
ls enhanced_database.py, storage_manager.py, enhanced_main.py
```

### 2. 配置服务器信息

编辑 `deployment/server_config.json`:
```json
{
  "server": {
    "ip": "YOUR_SERVER_IP",
    "domain": "update.yourdomain.com"
  },
  "api": {
    "key": "your-secure-api-key-here"
  }
}
```

### 3. 执行自动部署

```powershell
# 运行部署脚本
.\deploy_enhanced_version.ps1 -ServerIP "YOUR_SERVER_IP"

# 等待部署完成 (约5-10分钟)
```

### 4. 验证部署

```powershell
# 测试健康检查
curl http://YOUR_SERVER_IP/health

# 测试API接口
curl http://YOUR_SERVER_IP/api/v1/storage/stats
```

## 🔧 手动部署

### 1. 服务器环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础软件
sudo apt install -y python3 python3-pip python3-venv nginx curl wget unzip

# 创建服务用户
sudo useradd -r -s /bin/false omega
sudo mkdir -p /opt/omega-update-server
sudo chown omega:omega /opt/omega-update-server
```

### 2. 上传项目文件

```powershell
# 从Windows客户端上传文件
scp enhanced_database.py root@YOUR_SERVER_IP:/opt/omega-update-server/
scp storage_manager.py root@YOUR_SERVER_IP:/opt/omega-update-server/
scp enhanced_main.py root@YOUR_SERVER_IP:/opt/omega-update-server/
scp deployment/server_config.py root@YOUR_SERVER_IP:/opt/omega-update-server/
```

### 3. 配置Python环境

```bash
# 进入项目目录
cd /opt/omega-update-server

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn python-multipart sqlalchemy python-dotenv requests

# 设置权限
chown -R omega:omega /opt/omega-update-server
```

### 4. 配置数据库

```bash
# 创建环境变量文件
cat > .env << EOF
API_KEY=your-secure-api-key-here
DATABASE_URL=sqlite:///./omega_updates.db
MAX_FILE_SIZE=1073741824
LOG_LEVEL=INFO
EOF

# 初始化数据库
python enhanced_database.py
```

### 5. 配置存储目录

```bash
# 创建存储目录结构
mkdir -p /var/www/updates/{full,patches,hotfixes,temp}
chown -R omega:omega /var/www/updates
chmod -R 755 /var/www/updates
```

### 6. 配置systemd服务

```bash
# 创建服务文件
cat > /etc/systemd/system/omega-update-server.service << EOF
[Unit]
Description=Omega Update Server Enhanced
After=network.target

[Service]
Type=simple
User=omega
Group=omega
WorkingDirectory=/opt/omega-update-server
Environment=PATH=/opt/omega-update-server/venv/bin
ExecStart=/opt/omega-update-server/venv/bin/python enhanced_main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
systemctl daemon-reload
systemctl enable omega-update-server
systemctl start omega-update-server
```

### 7. 配置Nginx

```bash
# 创建Nginx配置
cat > /etc/nginx/sites-available/omega-update-server << EOF
server {
    listen 80;
    server_name YOUR_SERVER_IP update.yourdomain.com;
    
    client_max_body_size 1200M;
    client_body_timeout 1800s;
    client_header_timeout 1800s;
    proxy_connect_timeout 1800s;
    proxy_send_timeout 1800s;
    proxy_read_timeout 1800s;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /downloads/ {
        alias /var/www/updates/;
        autoindex off;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/omega-update-server /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试并重启Nginx
nginx -t
systemctl restart nginx
```

## 🔒 SSL配置 (可选)

### 使用Let's Encrypt

```bash
# 安装certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d update.yourdomain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 监控配置

### 1. 日志配置

```bash
# 创建日志目录
mkdir -p /opt/omega-update-server/logs
chown omega:omega /opt/omega-update-server/logs

# 配置日志轮转
cat > /etc/logrotate.d/omega-update-server << EOF
/opt/omega-update-server/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 omega omega
}
EOF
```

### 2. 监控脚本

```bash
# 创建健康检查脚本
cat > /opt/omega-update-server/health_check.sh << EOF
#!/bin/bash
HEALTH_URL="http://localhost/health"
RESPONSE=\$(curl -s \$HEALTH_URL)

if [[ \$RESPONSE == *"healthy"* ]]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy"
    systemctl restart omega-update-server
    exit 1
fi
EOF

chmod +x /opt/omega-update-server/health_check.sh

# 添加到crontab
echo "*/5 * * * * /opt/omega-update-server/health_check.sh" | crontab -
```

## 🧪 部署验证

### 1. 服务状态检查

```bash
# 检查服务状态
systemctl status omega-update-server
systemctl status nginx

# 检查端口监听
netstat -tlnp | grep :80
netstat -tlnp | grep :8000
```

### 2. 功能测试

```bash
# 健康检查
curl http://YOUR_SERVER_IP/health

# API测试
curl http://YOUR_SERVER_IP/api/v1/storage/stats

# 包列表
curl http://YOUR_SERVER_IP/api/v1/packages
```

### 3. 上传测试

```powershell
# 使用GUI工具测试
python advanced_upload_gui.py

# 或使用curl测试小文件上传
curl -X POST "http://YOUR_SERVER_IP/api/v1/upload/package" \
  -F "version=test-1.0.0" \
  -F "package_type=hotfix" \
  -F "description=Test upload" \
  -F "is_stable=true" \
  -F "is_critical=false" \
  -F "platform=windows" \
  -F "arch=x64" \
  -F "api_key=your-api-key" \
  -F "file=@test-file.zip"
```

## 🔧 故障排除

### 常见问题

**1. 服务启动失败**
```bash
# 查看详细错误
journalctl -u omega-update-server -f

# 检查配置文件
python -c "import enhanced_main"
```

**2. 上传失败**
```bash
# 检查Nginx错误日志
tail -f /var/log/nginx/error.log

# 检查文件权限
ls -la /var/www/updates/
```

**3. 数据库问题**
```bash
# 重新初始化数据库
cd /opt/omega-update-server
source venv/bin/activate
python enhanced_database.py
```

### 性能优化

**1. 数据库优化**
```bash
# 定期清理数据库
sqlite3 omega_updates.db "VACUUM;"
```

**2. 存储优化**
```bash
# 监控磁盘使用
df -h /var/www/updates/

# 手动清理
curl -X POST "http://localhost/api/v1/storage/cleanup" \
  -F "api_key=your-api-key"
```

## 📈 扩展配置

### 负载均衡 (多服务器)

```nginx
upstream omega_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}

server {
    location / {
        proxy_pass http://omega_backend;
    }
}
```

### 数据库迁移 (PostgreSQL)

```bash
# 安装PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 修改DATABASE_URL
DATABASE_URL=postgresql://username:password@localhost/omega_updates
```

## 🔄 升级指南

### 从v1.0升级到v2.0

```bash
# 备份当前版本
cp -r /opt/omega-update-server /opt/omega-update-server-backup

# 停止服务
systemctl stop omega-update-server

# 上传新文件
# ... (上传enhanced_*.py文件)

# 数据库迁移
python enhanced_database.py

# 启动服务
systemctl start omega-update-server
```

---

部署完成后，您的Omega更新服务器就可以开始为您的软件提供强大的更新服务了！ 🎉
