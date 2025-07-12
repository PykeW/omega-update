# 🔧 手动上传指南 - 解决SSH连接问题

## 🚨 当前问题
SSH连接出现 "Invalid SSH identification string" 错误，这通常是由于：
- SSH客户端版本兼容性问题
- 网络代理干扰
- SSH配置问题

## 🛠️ 解决方案

### 方案1：使用Git Bash（推荐）

1. **打开Git Bash**（不是PowerShell）
2. **测试连接**：
   ```bash
   ssh root@106.14.28.97
   ```
3. **如果成功，运行上传脚本**：
   ```bash
   ./deployment/upload_files.sh
   ```

### 方案2：使用PuTTY + WinSCP

#### 步骤1：下载工具
- PuTTY: https://www.putty.org/
- WinSCP: https://winscp.net/

#### 步骤2：使用PuTTY连接
1. 打开PuTTY
2. Host Name: `106.14.28.97`
3. Port: `22`
4. Connection type: `SSH`
5. 点击 `Open`
6. 输入用户名: `root`
7. 输入密码

#### 步骤3：使用WinSCP上传文件
1. 打开WinSCP
2. 协议: `SFTP`
3. 主机名: `106.14.28.97`
4. 用户名: `root`
5. 密码: (您的密码)
6. 连接后，将以下文件上传到 `/tmp/omega-deployment/`：

**需要上传的文件**：
```
deployment/
├── deploy.sh
├── main.py
├── server_config.py
├── nginx.conf
├── omega-update-server.service
├── diagnose.sh
├── fix_common_issues.sh
├── fix_server_limits.sh
├── simple_package_maker.py
├── omega_update_gui.py
└── *.md (所有文档文件)

项目根目录/
├── update_server/ (整个目录)
├── generate_update_package.py
├── simple_update_generator.py
└── version_analyzer.py
```

### 方案3：修复Windows SSH

#### 重新安装OpenSSH客户端
```powershell
# 以管理员身份运行PowerShell
# 卸载现有SSH客户端
Remove-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0

# 重新安装
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0

# 重启PowerShell
```

#### 清理SSH配置
```powershell
# 删除已知主机
Remove-Item ~/.ssh/known_hosts -ErrorAction SilentlyContinue

# 重新连接
ssh -o "StrictHostKeyChecking=no" root@106.14.28.97
```

### 方案4：使用WSL（Windows Subsystem for Linux）

如果您安装了WSL：
```bash
# 在WSL中
cd /mnt/d/Project/omega-update
ssh root@106.14.28.97
```

## 🚀 上传完成后的操作

无论使用哪种方法上传文件，完成后请：

### 1. 连接到服务器
```bash
# 使用任何可用的SSH客户端
ssh root@106.14.28.97
```

### 2. 进入部署目录
```bash
cd /tmp/omega-deployment
ls -la  # 检查文件是否上传成功
```

### 3. 设置文件权限
```bash
chmod +x *.sh
```

### 4. 修复服务器文件大小限制
```bash
./fix_server_limits.sh
```

### 5. 检查服务状态
```bash
./diagnose.sh
```

### 6. 如有问题，运行修复
```bash
./fix_common_issues.sh
```

## 🔍 验证上传成功

在服务器上检查文件：
```bash
cd /tmp/omega-deployment
echo "=== 部署文件 ==="
ls -la *.sh *.py *.conf *.service

echo "=== 项目文件 ==="
ls -la update_server/
ls -la generate_update_package.py simple_update_generator.py version_analyzer.py
```

应该看到所有必要的文件都已上传。

## 📞 如果仍有问题

1. **检查防火墙**：确保22端口开放
2. **检查网络**：尝试使用手机热点
3. **联系服务器提供商**：可能是服务器端SSH配置问题
4. **使用Web界面**：如果服务器提供商有Web文件管理界面

## 🎯 推荐操作顺序

1. **首先尝试Git Bash**（最简单）
2. **如果失败，使用PuTTY + WinSCP**（最可靠）
3. **上传完成后，按照上述步骤操作**
4. **修复服务器限制，然后测试GUI工具**

完成文件上传后，您就可以继续使用GUI工具制作和上传更新包了！
