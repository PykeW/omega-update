# Omega软件自动更新系统 - 服务器端部署指南

## 概述

本指南详细说明如何在阿里云ECS实例上部署Omega软件自动更新系统的服务器端。

## 服务器信息

- **服务器IP**: 106.14.28.97
- **操作系统**: Linux (Ubuntu/CentOS)
- **访问方式**: SSH (端口22，用户名root)
- **服务架构**: Nginx + FastAPI + SQLite

## 目录结构

```
/opt/omega-update-server/          # 应用程序目录
├── main.py                        # FastAPI主程序
├── server_config.py               # 服务器配置
├── .env                          # 环境变量配置
├── venv/                         # Python虚拟环境
├── update_server/                # 更新服务器模块
└── omega_updates.db              # SQLite数据库

/var/www/omega-updates/           # Web文件目录
├── uploads/                      # 上传文件存储
│   ├── versions/                 # 版本文件
│   ├── packages/                 # 更新包
│   └── patches/                  # 补丁文件
└── static/                       # 静态文件

/var/log/omega-updates/           # 日志目录
├── server.log                    # 应用日志
└── access.log                    # 访问日志

/etc/nginx/sites-available/       # Nginx配置
└── omega-update-server           # 站点配置文件

/etc/systemd/system/              # 系统服务
└── omega-update-server.service   # 服务配置文件
```

## 部署步骤

### 1. 准备工作

#### 1.1 配置SSH密钥（推荐）

```bash
# 在本地生成SSH密钥对（如果还没有）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 将公钥复制到服务器
ssh-copy-id root@106.14.28.97

# 测试连接
ssh root@106.14.28.97
```

#### 1.2 检查服务器环境

```bash
# 连接到服务器
ssh root@106.14.28.97

# 检查操作系统版本
cat /etc/os-release

# 检查可用空间
df -h

# 检查内存
free -h

# 检查网络
ping -c 3 google.com
```

### 2. 上传文件

#### 2.1 使用上传脚本

```bash
# 在本地项目目录中运行
chmod +x deployment/upload_files.sh
./deployment/upload_files.sh
```

#### 2.2 手动上传（备选方案）

```bash
# 创建远程目录
ssh root@106.14.28.97 "mkdir -p /tmp/omega-deployment"

# 上传部署文件
scp -r deployment/* root@106.14.28.97:/tmp/omega-deployment/

# 上传项目文件
scp -r update_server root@106.14.28.97:/tmp/omega-deployment/
scp generate_update_package.py root@106.14.28.97:/tmp/omega-deployment/
scp simple_update_generator.py root@106.14.28.97:/tmp/omega-deployment/
scp version_analyzer.py root@106.14.28.97:/tmp/omega-deployment/
```

### 3. 执行部署

#### 3.1 连接到服务器

```bash
ssh root@106.14.28.97
cd /tmp/omega-deployment
```

#### 3.2 运行部署脚本

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 执行完整安装
./deploy.sh install
```

部署脚本将自动执行以下操作：
- 安装系统依赖（Python3、Nginx、SQLite等）
- 创建服务用户（omega）
- 创建目录结构
- 设置Python虚拟环境
- 安装Python依赖
- 配置Nginx
- 配置systemd服务
- 配置防火墙
- 启动服务

#### 3.3 检查部署状态

```bash
# 检查服务状态
./deploy.sh status

# 或者手动检查
systemctl status omega-update-server
systemctl status nginx
```

### 4. 配置验证

#### 4.1 检查服务运行状态

```bash
# 检查端口监听
netstat -tlnp | grep -E ':80|:8000'

# 检查进程
ps aux | grep -E 'nginx|python'

# 检查日志
tail -f /var/log/omega-updates/server.log
tail -f /var/log/nginx/omega-update-access.log
```

#### 4.2 测试API接口

```bash
# 健康检查
curl http://106.14.28.97/health

# 获取服务器信息
curl http://106.14.28.97/

# 获取统计信息
curl http://106.14.28.97/api/v1/stats

# 检查版本更新
curl "http://106.14.28.97/api/v1/version/check?current_version=1.0.0"
```

#### 4.3 访问Web界面

在浏览器中访问：
- 主页: http://106.14.28.97
- API文档: http://106.14.28.97/docs
- 健康检查: http://106.14.28.97/health

### 5. 环境变量配置

编辑环境变量文件：

```bash
sudo nano /opt/omega-update-server/.env
```

重要配置项：

```env
# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///./omega_updates.db

# 文件存储配置
UPLOAD_DIR=/var/www/omega-updates/uploads
STATIC_DIR=/var/www/omega-updates/static
LOG_DIR=/var/log/omega-updates

# 安全配置（请修改为随机值）
SECRET_KEY=your-secret-key-change-this
API_KEY=your-api-key-change-this

# 文件上传配置
MAX_FILE_SIZE=104857600

# 日志配置
LOG_LEVEL=INFO
```

修改配置后重启服务：

```bash
sudo systemctl restart omega-update-server
```

## 更新包管理

### 1. 上传新版本

#### 1.1 使用管理工具

```bash
# 在本地使用管理工具
python deployment/manage_updates.py upload 2.3.0 /path/to/update.zip \
    --description "新版本更新" \
    --stable \
    --api-key YOUR_API_KEY
```

#### 1.2 使用curl命令

```bash
curl -X POST "http://106.14.28.97/api/v1/upload/version" \
    -F "version=2.3.0" \
    -F "description=新版本更新" \
    -F "is_stable=true" \
    -F "is_critical=false" \
    -F "platform=windows" \
    -F "arch=x64" \
    -F "file=@/path/to/update.zip" \
    -F "api_key=YOUR_API_KEY"
```

### 2. 管理版本

```bash
# 列出所有版本
python deployment/manage_updates.py list

# 检查版本更新
python deployment/manage_updates.py check 2.2.5

# 获取统计信息
python deployment/manage_updates.py stats

# 健康检查
python deployment/manage_updates.py health
```

## 维护操作

### 1. 服务管理

```bash
# 启动服务
sudo systemctl start omega-update-server

# 停止服务
sudo systemctl stop omega-update-server

# 重启服务
sudo systemctl restart omega-update-server

# 查看服务状态
sudo systemctl status omega-update-server

# 查看服务日志
sudo journalctl -u omega-update-server -f
```

### 2. 日志管理

```bash
# 查看应用日志
tail -f /var/log/omega-updates/server.log

# 查看Nginx访问日志
tail -f /var/log/nginx/omega-update-access.log

# 查看Nginx错误日志
tail -f /var/log/nginx/omega-update-error.log

# 清理旧日志
sudo logrotate -f /etc/logrotate.d/nginx
```

### 3. 数据库管理

```bash
# 备份数据库
sudo cp /opt/omega-update-server/omega_updates.db \
    /opt/omega-update-server/omega_updates.db.backup.$(date +%Y%m%d)

# 查看数据库信息
sudo sqlite3 /opt/omega-update-server/omega_updates.db ".tables"
sudo sqlite3 /opt/omega-update-server/omega_updates.db "SELECT * FROM versions;"
```

### 4. 更新应用

```bash
# 上传新的应用文件后
cd /tmp/omega-deployment
./deploy.sh update
```

## 安全配置

### 1. 防火墙设置

```bash
# 检查防火墙状态
sudo ufw status

# 允许必要端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# 启用防火墙
sudo ufw enable
```

### 2. SSL证书配置（可选）

如果需要HTTPS支持：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. 访问控制

编辑Nginx配置以限制API访问：

```nginx
# 限制上传API访问
location /api/v1/upload/ {
    allow 192.168.1.0/24;  # 允许内网访问
    deny all;              # 拒绝其他访问
    proxy_pass http://127.0.0.1:8000;
}
```

## 故障排除

### 1. 常见问题

#### 服务无法启动
```bash
# 检查配置文件
sudo nginx -t
sudo systemctl status omega-update-server

# 检查端口占用
sudo netstat -tlnp | grep :8000
```

#### 文件上传失败
```bash
# 检查目录权限
ls -la /var/www/omega-updates/uploads/
sudo chown -R omega:omega /var/www/omega-updates/

# 检查磁盘空间
df -h
```

#### 数据库连接失败
```bash
# 检查数据库文件权限
ls -la /opt/omega-update-server/omega_updates.db
sudo chown omega:omega /opt/omega-update-server/omega_updates.db
```

### 2. 性能监控

```bash
# 监控系统资源
htop
iotop
nethogs

# 监控服务性能
sudo systemctl status omega-update-server
curl -w "@curl-format.txt" -o /dev/null -s http://106.14.28.97/health
```

## 联系信息

如有问题，请联系系统管理员或查看项目文档。

- 项目地址: [GitHub Repository]
- 文档地址: [Documentation]
- 问题反馈: [Issues]
