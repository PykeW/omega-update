# Omega 更新系统 - 故障排除指南

本指南帮助您解决在使用重构后的 Omega 更新系统时可能遇到的常见问题。

## 🚨 常见问题

### 1. 导入错误 (ModuleNotFoundError)

#### 问题描述
```
ModuleNotFoundError: No module named 'common_utils'
ModuleNotFoundError: No module named 'server.enhanced_database'
```

#### 解决方案
```bash
# ✅ 正确方式：使用启动脚本
python start_server.py
python start_upload_tool.py
python start_download_tool.py

# ❌ 错误方式：直接运行模块文件
python server/enhanced_main.py
python tools/upload/upload_tool.py
```

#### 原因说明
启动脚本会自动设置正确的 Python 路径，确保模块能够正确导入。

### 2. 服务器启动失败

#### 问题描述
```
FileNotFoundError: [Errno 2] No such file or directory: '.env'
PermissionError: [Errno 13] Permission denied: '/var/log/omega-updates'
```

#### 解决方案
```bash
# 1. 检查环境变量文件
ls -la .env
# 如果不存在，复制模板
cp .env.example .env

# 2. 检查目录权限
sudo mkdir -p /var/log/omega-updates
sudo chown $USER:$USER /var/log/omega-updates

# 3. 检查端口占用
netstat -tulpn | grep :8000
# 如果端口被占用，修改 .env 中的 SERVER_PORT
```

### 3. 数据库问题

#### 问题描述
```
sqlite3.OperationalError: database is locked
sqlite3.OperationalError: no such table: versions
```

#### 解决方案
```bash
# 1. 检查数据库文件权限
ls -la server/omega_updates.db
chmod 664 server/omega_updates.db

# 2. 重新初始化数据库
python -c "from server.enhanced_database import init_database; init_database()"

# 3. 检查数据库完整性
sqlite3 server/omega_updates.db "PRAGMA integrity_check;"
```

### 4. GUI 工具无法启动

#### 问题描述
```
ModuleNotFoundError: No module named 'tkinter'
_tkinter.TclError: no display name and no $DISPLAY environment variable
```

#### 解决方案
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter

# macOS
brew install python-tk

# Windows (通常已包含)
# 重新安装 Python 时选择 "tcl/tk and IDLE"

# Linux 服务器 (无图形界面)
export DISPLAY=:0  # 如果有 X11 转发
# 或使用 X11 转发
ssh -X user@server
```

### 5. 网络连接问题

#### 问题描述
```
requests.exceptions.ConnectionError: Failed to establish a new connection
ConnectionRefusedError: [Errno 111] Connection refused
```

#### 解决方案
```bash
# 1. 检查服务器状态
curl http://localhost:8000/health

# 2. 检查防火墙
sudo ufw status
sudo ufw allow 8000

# 3. 检查配置文件
cat config/upload_config.json
# 确认 server_url 正确

# 4. 测试网络连通性
ping server-ip
telnet server-ip 8000
```

## 🔧 调试技巧

### 1. 启用详细日志
```bash
# 修改 .env 文件
LOG_LEVEL=DEBUG

# 查看日志
tail -f /var/log/omega-updates/server.log
```

### 2. 使用 API 文档调试
```bash
# 访问交互式 API 文档
http://localhost:8000/docs

# 测试具体接口
curl -X GET "http://localhost:8000/health"
curl -X GET "http://localhost:8000/api/v1/storage/stats?api_key=your-key"
```

### 3. 检查进程状态
```bash
# 查看 Python 进程
ps aux | grep python

# 查看端口占用
netstat -tulpn | grep :8000

# 查看系统资源
top
df -h
```

## 🐛 错误代码参考

### HTTP 状态码
| 状态码 | 含义 | 常见原因 |
|--------|------|----------|
| 401 | 未授权 | API 密钥错误或缺失 |
| 404 | 未找到 | 路径错误或资源不存在 |
| 413 | 请求实体过大 | 上传文件超过大小限制 |
| 500 | 服务器内部错误 | 服务器代码错误 |
| 507 | 存储空间不足 | 磁盘空间不够 |

### 应用错误代码
| 错误代码 | 描述 | 解决方案 |
|----------|------|----------|
| INVALID_API_KEY | API 密钥无效 | 检查 .env 文件中的 API_KEY |
| UNSUPPORTED_FILE_TYPE | 不支持的文件类型 | 检查文件扩展名 |
| INSUFFICIENT_STORAGE | 存储空间不足 | 清理磁盘空间或执行存储清理 |
| DATABASE_ERROR | 数据库错误 | 检查数据库文件权限和完整性 |

## 📊 性能问题

### 1. 上传/下载速度慢
```bash
# 检查网络带宽
speedtest-cli

# 检查磁盘 I/O
iostat -x 1

# 调整上传块大小 (在配置文件中)
"chunk_size": 8192  # 增加块大小
```

### 2. 内存使用过高
```bash
# 监控内存使用
free -h
ps aux --sort=-%mem | head

# 调整配置
# 在 .env 中设置较小的文件处理大小
MAX_FILE_SIZE=536870912  # 512MB
```

### 3. 数据库性能
```bash
# 优化数据库
sqlite3 server/omega_updates.db "VACUUM;"
sqlite3 server/omega_updates.db "ANALYZE;"

# 检查数据库大小
ls -lh server/omega_updates.db
```

## 🔍 日志分析

### 服务器日志位置
```bash
# 主日志文件
/var/log/omega-updates/server.log

# 系统日志
journalctl -u omega-update-server

# 应用日志
tail -f /var/log/omega-updates/server.log | grep ERROR
```

### 常见日志模式
```bash
# 查找错误
grep "ERROR" /var/log/omega-updates/server.log

# 查找特定 API 调用
grep "POST /api/v1/upload" /var/log/omega-updates/server.log

# 查找性能问题
grep "slow" /var/log/omega-updates/server.log
```

## 🆘 获取帮助

### 1. 收集诊断信息
```bash
# 创建诊断报告
cat > diagnostic_info.txt << EOF
=== 系统信息 ===
$(uname -a)
$(python --version)
$(pip list | grep -E "(fastapi|sqlalchemy|requests)")

=== 项目结构 ===
$(ls -la)
$(ls -la server/)
$(ls -la tools/)

=== 配置信息 ===
$(cat .env | grep -v API_KEY)

=== 日志摘要 ===
$(tail -20 /var/log/omega-updates/server.log)
EOF
```

### 2. 检查清单
在报告问题前，请确认：

- [ ] 使用了正确的启动脚本
- [ ] `.env` 文件已正确配置
- [ ] 所有依赖已安装 (`pipenv install`)
- [ ] 防火墙和网络配置正确
- [ ] 查看了相关日志文件
- [ ] 尝试了本指南中的解决方案

### 3. 联系支持
提供以下信息：
- 操作系统和版本
- Python 版本
- 错误的完整堆栈跟踪
- 相关的日志片段
- 重现步骤

---

**版本**: 2.0.0  
**最后更新**: 2025-07-14  
**相关文档**: [README.md](../README.md) | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
