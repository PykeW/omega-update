# Omega更新系统部署指南

## 📋 概述

本指南详细说明如何部署和配置Omega更新系统的简化版本管理功能。

## 🚀 部署步骤

### 1. 问题修复部署

#### 1.1 修复上传问题
```bash
# 运行修复脚本
python scripts/fix_upload_issues.py

# 测试修复效果
python scripts/test_upload_fix.py
```

#### 1.2 更新配置文件
确保以下配置文件包含正确的API密钥：
- `config/config.json`
- `config/upload_config.json`
- `local_server_config.json`

正确的API密钥：`dac450db3ec47d79196edb7a34defaed`

### 2. 服务器端部署

#### 2.1 数据库迁移
```bash
# 备份现有数据库
cp omega_updates.db omega_updates_backup.db

# 运行迁移脚本
python scripts/migrate_to_simplified_system.py

# 检查迁移结果
cat migration_report.json
```

#### 2.2 部署新API端点
将以下文件部署到服务器：
- `server/simplified_database.py` - 新数据库模型
- `server/simplified_api.py` - 新API端点

在服务器主应用中添加：
```python
from server.simplified_api import router as simplified_router
app.include_router(simplified_router)
```

#### 2.3 创建数据库表
```python
from server.simplified_database import create_simplified_tables
from sqlalchemy import create_engine

engine = create_engine('sqlite:///omega_updates.db')
create_simplified_tables(engine)
```

### 3. 客户端工具部署

#### 3.1 简化上传工具
```bash
# 启动简化上传工具
python start_simplified_upload_tool.py
```

特性：
- 三版本类型选择（稳定版/测试版/新功能测试版）
- 自动文件打包
- 进度显示
- 错误处理

#### 3.2 简化下载工具
```bash
# 启动简化下载工具
python start_simplified_download_tool.py
```

特性：
- 版本类型下拉选择
- 实时版本信息显示
- 下载进度显示
- 自动文件命名

### 4. 配置更新

#### 4.1 上传配置优化
在 `config/upload_config.json` 中：
```json
{
  "upload": {
    "timeout": 600,
    "chunk_size": 65536,
    "retry_count": 5,
    "retry_delay": 10
  }
}
```

#### 4.2 文件过滤配置
创建 `config/file_filter.json`：
```json
{
  "exclude_patterns": [
    "*.tmp", "*.temp", "*.log", "*.bak",
    ".git", ".svn", "__pycache__", "*.pyc",
    "api-ms-win-*.dll",
    "vcruntime*.dll",
    "*.pdb"
  ],
  "max_file_size": 104857600,
  "skip_large_files": true
}
```

## 🔧 故障排除

### 常见问题

#### 1. 上传失败
**症状**：文件上传时出现错误
**解决方案**：
1. 检查API密钥是否正确
2. 增加上传超时时间
3. 排除大文件或系统文件
4. 检查网络连接

#### 2. 服务器连接失败
**症状**：无法连接到服务器
**解决方案**：
1. 检查服务器URL配置
2. 验证防火墙设置
3. 确认服务器运行状态

#### 3. 版本信息不显示
**症状**：下载工具中版本信息为空
**解决方案**：
1. 确认服务器端API已部署
2. 检查数据库迁移是否成功
3. 验证API端点响应

### 日志检查

#### 服务器日志
```bash
# 检查服务器日志
tail -f /var/log/omega-server.log

# 检查API访问日志
grep "api/v2" /var/log/nginx/access.log
```

#### 客户端日志
```bash
# 启用详细日志
export OMEGA_DEBUG=1
python start_simplified_upload_tool.py
```

## 📊 监控和维护

### 1. 系统状态监控
```bash
# 检查系统状态
curl http://106.14.28.97:8000/api/v2/status/simple
```

### 2. 数据库维护
```bash
# 清理历史记录（保留最近100条）
sqlite3 omega_updates.db "DELETE FROM version_history WHERE id NOT IN (SELECT id FROM version_history ORDER BY created_at DESC LIMIT 100);"

# 优化数据库
sqlite3 omega_updates.db "VACUUM;"
```

### 3. 存储空间管理
```bash
# 检查存储使用情况
du -sh uploads/simplified/

# 清理临时文件
find uploads/temp -type f -mtime +7 -delete
```

## 🔄 回滚计划

如果新系统出现问题，可以按以下步骤回滚：

### 1. 恢复数据库
```bash
# 停止服务器
systemctl stop omega-server

# 恢复备份
cp omega_updates_backup.db omega_updates.db

# 重启服务器
systemctl start omega-server
```

### 2. 使用原始工具
```bash
# 使用原始上传工具
python start_upload_tool.py

# 使用原始下载工具
python start_download_tool.py
```

## 📈 性能优化建议

### 1. 服务器端优化
- 使用Redis缓存版本信息
- 启用gzip压缩
- 配置CDN加速下载

### 2. 客户端优化
- 实现断点续传
- 添加并发上传
- 优化文件打包算法

### 3. 网络优化
- 增加上传超时时间
- 使用更大的数据块
- 实现重试机制

## 📞 支持联系

如果在部署过程中遇到问题，请：
1. 检查本指南的故障排除部分
2. 查看系统日志文件
3. 运行诊断脚本：`python scripts/diagnose_upload_issue.py`
4. 联系技术支持团队

## 📝 更新日志

### v2.0.0 - 简化版本管理系统
- 新增三版本类型系统
- 简化上传下载界面
- 自动版本覆盖功能
- 改进错误处理和日志记录

### v1.1.0 - 上传问题修复
- 修复API密钥认证问题
- 增加上传超时时间
- 添加文件过滤功能
- 改进错误诊断工具
