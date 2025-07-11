# 🚀 Omega更新服务器 - 5分钟快速部署

## 📋 您的配置信息
- **服务器IP**: 106.14.28.97
- **域名**: update.chpyke.cn
- **目标**: 部署Omega软件自动更新系统

---

## ⚡ 一键部署（推荐）

### 步骤1：上传并部署
```bash
# 在本地项目目录执行
./deployment/quick_deploy.sh

# 整个过程大约需要3-5分钟
# 脚本会自动完成所有配置
```

### 步骤2：验证部署
```bash
# 在浏览器中访问
http://update.chpyke.cn
http://update.chpyke.cn/docs
http://update.chpyke.cn/health
```

---

## 🔧 手动部署（如果一键部署失败）

### 步骤1：上传文件
```bash
./deployment/upload_files.sh
```

### 步骤2：连接服务器并部署
```bash
ssh root@106.14.28.97
cd /tmp/omega-deployment
chmod +x *.sh
./deploy.sh install
```

### 步骤3：配置域名
```bash
# 修改Nginx配置
nano /etc/nginx/sites-available/omega-update-server

# 找到这行：
server_name update.chpyke.cn;

# 确保域名正确，然后重启服务
nginx -t
systemctl restart nginx omega-update-server
```

---

## 🔍 问题诊断

### 如果部署失败：
```bash
# 连接到服务器
ssh root@106.14.28.97
cd /tmp/omega-deployment

# 运行诊断脚本
chmod +x diagnose.sh
./diagnose.sh

# 运行修复脚本
chmod +x fix_common_issues.sh
./fix_common_issues.sh
```

### 常见问题快速解决：

#### 1. 服务无法启动
```bash
# 查看详细错误
journalctl -u omega-update-server -f

# 重启服务
systemctl restart omega-update-server nginx
```

#### 2. 域名无法访问
```bash
# 检查DNS解析
nslookup update.chpyke.cn

# 检查防火墙
ufw status
ufw allow 80/tcp
ufw allow 443/tcp
```

#### 3. 权限问题
```bash
# 修复权限
chown -R omega:omega /opt/omega-update-server
chown -R omega:omega /var/www/omega-updates
```

---

## ✅ 部署成功验证

### 1. 检查服务状态
```bash
systemctl status omega-update-server nginx
```

### 2. 检查端口监听
```bash
netstat -tlnp | grep -E ':80|:8000'
```

### 3. 测试HTTP接口
```bash
curl http://update.chpyke.cn/health
```

### 4. 浏览器访问
- 主页: http://update.chpyke.cn
- API文档: http://update.chpyke.cn/docs
- 健康检查: http://update.chpyke.cn/health

---

## 🔐 配置SSL（可选）

```bash
# 安装Certbot
apt install certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d update.chpyke.cn

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

---

## 📊 上传第一个更新包

### 1. 获取API密钥
```bash
ssh root@106.14.28.97
grep API_KEY /opt/omega-update-server/.env
```

### 2. 使用管理工具上传
```bash
# 在本地执行
python deployment/manage_updates.py upload 2.2.5 /path/to/your/update.zip \
    --description "初始版本" \
    --stable \
    --server http://update.chpyke.cn \
    --api-key YOUR_API_KEY
```

---

## 📞 获取帮助

### 查看日志
```bash
# 应用日志
tail -f /var/log/omega-updates/server.log

# Nginx日志
tail -f /var/log/nginx/omega-update-access.log

# 系统日志
journalctl -u omega-update-server -f
```

### 重新部署
```bash
ssh root@106.14.28.97
cd /tmp/omega-deployment
./deploy.sh restart
```

### 完全重置
```bash
ssh root@106.14.28.97
cd /tmp/omega-deployment
./fix_common_issues.sh --all
```

---

## 🎉 部署完成！

如果一切正常，您现在可以：

1. ✅ 访问 http://update.chpyke.cn 查看服务器状态
2. ✅ 访问 http://update.chpyke.cn/docs 查看API文档
3. ✅ 使用API上传和管理更新包
4. ✅ 客户端可以检查和下载更新

**下一步**: 配置您的Omega客户端连接到 `http://update.chpyke.cn` 进行更新检查！
