# 🚀 Omega更新服务器 - 简化部署指南

## 📋 您的服务器信息
- **IP地址**: 106.14.28.97
- **域名**: update.chpyke.cn
- **操作系统**: Linux

---

## 🎯 第一步：连接服务器并上传文件

### 1.1 测试SSH连接
```bash
# 测试连接（在本地终端执行）
ssh root@106.14.28.97

# 如果连接成功，会看到类似输出：
# Welcome to Ubuntu 20.04.x LTS (GNU/Linux ...)
# root@hostname:~#
```

**如果连接失败：**
- 检查IP地址是否正确
- 确认SSH服务是否运行
- 检查防火墙是否允许22端口

### 1.2 上传部署文件
```bash
# 在本地项目目录执行
./deployment/upload_files.sh

# 预期输出：
# [INFO] 检查SSH连接...
# [INFO] SSH连接正常
# [INFO] 上传部署文件...
# [INFO] 部署文件上传完成
```

**如果上传失败：**
- 确认SSH连接正常
- 检查本地文件是否存在
- 确认服务器磁盘空间充足

---

## 🔧 第二步：执行自动部署

### 2.1 连接到服务器
```bash
ssh root@106.14.28.97
cd /tmp/omega-deployment
ls -la

# 应该看到以下文件：
# deploy.sh
# main.py
# server_config.py
# nginx.conf
# omega-update-server.service
```

### 2.2 执行部署脚本
```bash
chmod +x deploy.sh
./deploy.sh install

# 部署过程会显示：
# [INFO] 开始安装Omega更新服务器...
# [INFO] 安装系统依赖...
# [INFO] 创建服务用户...
# [INFO] 创建目录结构...
# [INFO] 设置Python虚拟环境...
# [INFO] 部署应用程序...
# [INFO] 配置Nginx...
# [INFO] 配置systemd服务...
# [INFO] 配置防火墙...
# [INFO] 启动服务...
# [INFO] 安装完成！
```

**部署过程中可能的错误及解决方案：**

#### 错误1：包管理器更新失败
```
错误信息: 更新包列表失败
解决方案: 
sudo apt update --fix-missing
sudo apt install -f
```

#### 错误2：Python依赖安装失败
```
错误信息: 升级pip失败
解决方案:
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
```

#### 错误3：权限问题
```
错误信息: Permission denied
解决方案:
确保以root用户执行，或使用sudo
```

---

## ⚙️ 第三步：配置域名和环境变量

### 3.1 修改Nginx配置
```bash
# 编辑Nginx配置文件
nano /etc/nginx/sites-available/omega-update-server

# 找到这一行：
server_name 106.14.28.97;

# 修改为：
server_name update.chpyke.cn;

# 保存并退出（Ctrl+X, Y, Enter）
```

### 3.2 修改环境变量
```bash
# 编辑环境变量文件
nano /opt/omega-update-server/.env

# 修改以下配置：
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

# 生成新的密钥（重要！）
SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 16)

# 保存文件
```

### 3.3 重启服务
```bash
# 测试Nginx配置
nginx -t

# 如果配置正确，会显示：
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 重启服务
systemctl restart nginx
systemctl restart omega-update-server

# 检查服务状态
systemctl status nginx
systemctl status omega-update-server
```

**预期输出：**
```
● nginx.service - A high performance web server
   Active: active (running)

● omega-update-server.service - Omega Update Server
   Active: active (running)
```

---

## ✅ 第四步：验证部署

### 4.1 检查端口监听
```bash
netstat -tlnp | grep -E ':80|:8000'

# 预期输出：
# tcp 0 0 0.0.0.0:80 0.0.0.0:* LISTEN 1234/nginx
# tcp 0 0 127.0.0.1:8000 0.0.0.0:* LISTEN 5678/python
```

### 4.2 测试HTTP接口
```bash
# 测试本地接口
curl http://localhost/health

# 预期输出：
# {"status":"healthy","timestamp":"2025-01-XX...","version":"1.0.0"}

# 测试外部访问
curl http://update.chpyke.cn/health
```

### 4.3 检查日志
```bash
# 查看应用日志
tail -f /var/log/omega-updates/server.log

# 查看Nginx日志
tail -f /var/log/nginx/omega-update-access.log
```

---

## 🌐 第五步：浏览器验证

在浏览器中访问以下地址：

1. **主页**: http://update.chpyke.cn
   - 应该显示服务器信息

2. **API文档**: http://update.chpyke.cn/docs
   - 应该显示FastAPI自动生成的文档

3. **健康检查**: http://update.chpyke.cn/health
   - 应该返回JSON格式的健康状态

4. **统计信息**: http://update.chpyke.cn/api/v1/stats
   - 应该返回服务器统计信息

---

## 🔐 第六步：安全配置（可选但推荐）

### 6.1 配置SSL证书
```bash
# 安装Certbot
apt install certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d update.chpyke.cn

# 按提示输入邮箱地址，同意条款
# 选择是否重定向HTTP到HTTPS（推荐选择2）
```

### 6.2 设置自动续期
```bash
# 添加自动续期任务
crontab -e

# 添加以下行：
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 第七步：上传第一个更新包

### 7.1 获取API密钥
```bash
grep API_KEY /opt/omega-update-server/.env

# 输出类似：
# API_KEY=abc123def456...
```

### 7.2 使用管理工具上传
```bash
# 在本地执行（替换YOUR_API_KEY为实际密钥）
python deployment/manage_updates.py upload 2.2.5 /path/to/your/update.zip \
    --description "初始版本" \
    --stable \
    --server http://update.chpyke.cn \
    --api-key YOUR_API_KEY
```

---

## 🔍 故障排除

### 问题1：服务无法启动
```bash
# 检查详细错误信息
journalctl -u omega-update-server -f

# 常见原因：
# - 端口被占用：netstat -tlnp | grep 8000
# - 配置文件错误：检查.env文件格式
# - 权限问题：chown -R omega:omega /opt/omega-update-server
```

### 问题2：Nginx配置错误
```bash
# 测试配置
nginx -t

# 查看错误日志
tail -f /var/log/nginx/error.log

# 常见原因：
# - 语法错误：检查nginx.conf文件
# - 端口冲突：确保80端口未被占用
```

### 问题3：域名无法访问
```bash
# 检查DNS解析
nslookup update.chpyke.cn

# 检查防火墙
ufw status
iptables -L

# 检查服务监听
netstat -tlnp | grep :80
```

### 问题4：SSL证书申请失败
```bash
# 检查域名解析是否正确
dig update.chpyke.cn

# 确保80端口可访问
curl -I http://update.chpyke.cn

# 手动申请证书
certbot certonly --webroot -w /var/www/html -d update.chpyke.cn
```

---

## 📞 获取帮助

如果遇到问题，可以：

1. **查看详细日志**：
   ```bash
   # 应用日志
   tail -100 /var/log/omega-updates/server.log
   
   # 系统日志
   journalctl -u omega-update-server --no-pager -l
   ```

2. **检查服务状态**：
   ```bash
   ./deploy.sh status
   ```

3. **重新部署**：
   ```bash
   ./deploy.sh restart
   ```

---

## ✅ 部署完成检查清单

- [ ] SSH连接正常
- [ ] 文件上传成功
- [ ] 自动部署完成
- [ ] 域名配置正确
- [ ] 服务运行正常
- [ ] HTTP接口响应正常
- [ ] 浏览器可以访问
- [ ] SSL证书配置（可选）
- [ ] 第一个更新包上传成功

**恭喜！您的Omega更新服务器已成功部署！** 🎉
