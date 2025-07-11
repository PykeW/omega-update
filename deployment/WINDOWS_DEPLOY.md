# 🚀 Windows环境下的Omega更新服务器部署指南

## 📋 您的配置信息
- **本地环境**: Windows
- **服务器IP**: 106.14.28.97
- **域名**: update.chpyke.cn
- **部署方式**: 远程SSH部署

---

## ⚡ 快速部署（推荐方案）

### 方案一：使用PowerShell脚本

```powershell
# 在PowerShell中执行（以管理员身份运行）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\deployment\upload_files.ps1
```

然后按照脚本提示连接到服务器完成部署。

### 方案二：使用Git Bash

如果您安装了Git for Windows：

```bash
# 打开Git Bash（不是PowerShell）
./deployment/quick_deploy.sh
```

---

## 🔧 手动部署步骤

### 步骤1：上传文件到服务器

```powershell
# 创建远程目录
ssh root@106.14.28.97 "mkdir -p /tmp/omega-deployment"

# 上传部署文件
scp deployment\*.py root@106.14.28.97:/tmp/omega-deployment/
scp deployment\*.sh root@106.14.28.97:/tmp/omega-deployment/
scp deployment\*.conf root@106.14.28.97:/tmp/omega-deployment/
scp deployment\*.service root@106.14.28.97:/tmp/omega-deployment/
scp deployment\*.md root@106.14.28.97:/tmp/omega-deployment/

# 上传项目文件
scp -r update_server root@106.14.28.97:/tmp/omega-deployment/
scp generate_update_package.py root@106.14.28.97:/tmp/omega-deployment/
scp simple_update_generator.py root@106.14.28.97:/tmp/omega-deployment/
scp version_analyzer.py root@106.14.28.97:/tmp/omega-deployment/
```

### 步骤2：连接服务器并部署

```powershell
# 连接到服务器
ssh root@106.14.28.97

# 在服务器上执行以下命令：
cd /tmp/omega-deployment
chmod +x *.sh
./deploy.sh install
```

### 步骤3：验证部署

在服务器上执行：
```bash
# 检查服务状态
./deploy.sh status

# 测试HTTP接口
curl http://localhost/health
```

在本地浏览器中访问：
- http://update.chpyke.cn
- http://update.chpyke.cn/docs
- http://update.chpyke.cn/health

---

## 🔍 常见问题解决

### 问题1：SSH连接失败

**错误信息**: `ssh: connect to host 106.14.28.97 port 22: Connection refused`

**解决方案**:
```powershell
# 检查网络连接
ping 106.14.28.97

# 检查SSH服务
telnet 106.14.28.97 22
```

### 问题2：权限被拒绝

**错误信息**: `Permission denied (publickey)`

**解决方案**:
```powershell
# 使用密码认证
ssh -o PreferredAuthentications=password root@106.14.28.97

# 或配置SSH密钥
ssh-keygen -t rsa -b 4096
ssh-copy-id root@106.14.28.97
```

### 问题3：PowerShell执行策略限制

**错误信息**: `execution of scripts is disabled on this system`

**解决方案**:
```powershell
# 以管理员身份运行PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题4：SCP命令不存在

**错误信息**: `scp : The term 'scp' is not recognized`

**解决方案**:
1. 安装OpenSSH客户端：
   - Windows 10/11: 设置 → 应用 → 可选功能 → 添加功能 → OpenSSH客户端
2. 或使用WinSCP等图形化工具
3. 或使用Git Bash

---

## 🛠️ 部署后管理

### 查看服务状态
```powershell
ssh root@106.14.28.97 "systemctl status omega-update-server nginx"
```

### 查看日志
```powershell
ssh root@106.14.28.97 "tail -f /var/log/omega-updates/server.log"
```

### 重启服务
```powershell
ssh root@106.14.28.97 "systemctl restart omega-update-server nginx"
```

### 运行诊断
```powershell
ssh root@106.14.28.97 "cd /tmp/omega-deployment && ./diagnose.sh"
```

### 修复问题
```powershell
ssh root@106.14.28.97 "cd /tmp/omega-deployment && ./fix_common_issues.sh"
```

---

## 📊 上传更新包

### 获取API密钥
```powershell
ssh root@106.14.28.97 "grep API_KEY /opt/omega-update-server/.env"
```

### 使用管理工具上传
```powershell
# 在本地执行
python deployment\manage_updates.py upload 2.2.5 C:\path\to\your\update.zip --description "初始版本" --stable --server http://update.chpyke.cn --api-key YOUR_API_KEY
```

---

## 🔐 配置SSL证书（可选）

```powershell
# 连接到服务器
ssh root@106.14.28.97

# 在服务器上执行
apt install certbot python3-certbot-nginx
certbot --nginx -d update.chpyke.cn

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

---

## 📞 获取帮助

### 实时监控
```powershell
# 监控服务日志
ssh root@106.14.28.97 "journalctl -u omega-update-server -f"

# 监控Nginx日志
ssh root@106.14.28.97 "tail -f /var/log/nginx/omega-update-access.log"
```

### 完全重新部署
```powershell
# 如果需要重新开始
ssh root@106.14.28.97 "cd /tmp/omega-deployment && ./fix_common_issues.sh --all"
```

---

## ✅ 部署成功检查清单

- [ ] SSH连接正常
- [ ] 文件上传成功
- [ ] 服务器部署完成
- [ ] 服务运行正常
- [ ] HTTP接口响应正常
- [ ] 浏览器可以访问 http://update.chpyke.cn
- [ ] API文档可以访问 http://update.chpyke.cn/docs
- [ ] 健康检查正常 http://update.chpyke.cn/health

**恭喜！您的Omega更新服务器已成功部署！** 🎉

---

## 🎯 推荐操作流程

1. **使用PowerShell脚本上传文件**:
   ```powershell
   .\deployment\upload_files.ps1
   ```

2. **连接服务器部署**:
   ```powershell
   ssh root@106.14.28.97
   cd /tmp/omega-deployment
   ./deploy.sh install
   ```

3. **验证部署结果**:
   - 浏览器访问 http://update.chpyke.cn
   - 检查API文档 http://update.chpyke.cn/docs

4. **配置SSL（可选）**:
   ```bash
   certbot --nginx -d update.chpyke.cn
   ```

5. **上传第一个更新包**:
   ```powershell
   python deployment\manage_updates.py upload ...
   ```
