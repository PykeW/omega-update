# Omega更新服务器 - 增强版

一个功能完整的软件更新服务器，支持完整包、增量包和智能存储管理。

## 🚀 主要特性

### 多类型更新包支持
- **完整包 (FULL)**: 支持大文件上传（8GB+），适用于全新安装
- **增量包 (PATCH)**: 版本间增量更新，节省带宽和存储空间
- **热修复包 (HOTFIX)**: 紧急bug修复，快速部署

### 智能存储管理
- **自动清理**: 存储使用率达到85%时自动清理旧版本
- **版本保护**: 关键版本和最新稳定版本受保护
- **存储监控**: 实时监控存储使用情况和健康状态
- **空间优化**: 针对40GB存储空间的智能分配策略

### 高级管理功能
- **GUI管理工具**: 直观的图形界面，支持所有操作
- **RESTful API**: 完整的API接口，支持自动化集成
- **版本管理**: 智能版本检查，优先推荐增量更新
- **下载统计**: 详细的下载和使用统计

## 📁 项目结构

```
omega-update/
├── enhanced_database.py          # 增强数据库模型
├── storage_manager.py            # 存储管理器
├── enhanced_main.py              # 增强版API服务
├── advanced_upload_gui.py        # 高级GUI工具
├── deploy_enhanced_version.ps1   # 部署脚本
├── storage_management_strategy.md # 存储管理策略
├── deployment/                   # 部署相关文件
│   ├── server_config.json       # 服务器配置
│   ├── server_config.py         # 服务器配置模块
│   ├── nginx.conf               # Nginx配置
│   ├── omega-update-server.service # systemd服务文件
│   ├── deploy.sh                # Linux部署脚本
│   └── quick_deploy.sh          # 快速部署脚本
└── update_server/               # 原始服务器模块
    ├── api/                     # API模块
    ├── models/                  # 数据模型
    ├── config/                  # 配置文件
    └── utils/                   # 工具函数
```

## 🛠️ 快速开始

### 1. 环境要求

**服务器端:**
- Ubuntu 22.04 LTS
- Python 3.8+
- Nginx
- 至少40GB存储空间

**客户端:**
- Windows 10/11
- Python 3.8+
- PowerShell 5.0+

### 2. 服务器部署

#### 自动部署（推荐）
```powershell
# 克隆项目
git clone <repository-url>
cd omega-update

# 执行自动部署
.\deploy_enhanced_version.ps1
```

#### 手动部署
详见 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### 3. 使用GUI工具

```powershell
# 启动GUI管理工具
python advanced_upload_gui.py
```

## 📊 存储管理策略

### 存储分配
- **总存储**: 40GB
- **完整包**: 最多3个版本 (24GB)
- **增量包**: 最多10个版本 (4GB)  
- **热修复包**: 最多20个版本 (1GB)
- **临时文件**: 1GB

### 自动清理规则
1. **触发条件**: 存储使用率 > 85%
2. **清理优先级**:
   - 临时文件和失败上传
   - 超量热修复包
   - 超量增量包
   - 非关键完整包
3. **保护规则**: 最新稳定版本和关键版本永不删除

## 🔌 API接口

### 核心接口

#### 上传更新包
```http
POST /api/v1/upload/package
Content-Type: multipart/form-data

version: string          # 版本号
package_type: string     # full/patch/hotfix
description: string      # 描述
is_stable: boolean       # 是否稳定版本
is_critical: boolean     # 是否关键更新
platform: string        # 平台 (windows/linux/macos)
arch: string            # 架构 (x64/x86/arm64)
from_version: string    # 源版本 (仅增量包)
file: file              # 更新包文件
api_key: string         # API密钥
```

#### 版本检查
```http
GET /api/v1/version/check?current_version=2.2.5&platform=windows&arch=x64
```

#### 存储统计
```http
GET /api/v1/storage/stats
```

#### 包列表
```http
GET /api/v1/packages?package_type=full&limit=20
```

详细API文档: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🎯 使用场景

### 1. 软件发布流程
```
开发完成 → 打包 → 上传完整包 → 测试 → 发布稳定版
```

### 2. 增量更新流程  
```
版本A → 开发变更 → 生成增量包 → 上传增量包 → 客户端增量更新
```

### 3. 紧急修复流程
```
发现bug → 快速修复 → 打包热修复 → 上传热修复包 → 立即推送
```

## 📈 监控和维护

### 存储监控
- **警告阈值**: 80%使用率
- **清理阈值**: 85%使用率  
- **严重阈值**: 90%使用率

### 日志管理
- 服务器日志: `/opt/omega-update-server/logs/`
- Nginx日志: `/var/log/nginx/`
- 系统日志: `journalctl -u omega-update-server`

### 备份策略
- 数据库定期备份
- 关键版本文件备份
- 配置文件版本控制

## 🔧 配置说明

### 服务器配置
```json
{
  "server": {
    "ip": "106.14.28.97",
    "domain": "update.chpyke.cn"
  },
  "api": {
    "key": "your-api-key-here"
  },
  "storage": {
    "max_full_packages": 3,
    "max_patch_packages": 10,
    "max_hotfix_packages": 20,
    "cleanup_threshold": 0.85
  }
}
```

### 环境变量
```bash
API_KEY=your-api-key
DATABASE_URL=sqlite:///./omega_updates.db
MAX_FILE_SIZE=1073741824
LOG_LEVEL=INFO
```

## 🚨 故障排除

### 常见问题

**1. 上传失败**
- 检查文件大小限制
- 验证API密钥
- 检查网络连接

**2. 存储空间不足**
- 执行手动清理
- 检查清理配置
- 考虑扩展存储

**3. 服务无法启动**
- 检查端口占用
- 验证配置文件
- 查看错误日志

详细故障排除: [TROUBLESHOOTING.md](deployment/TROUBLESHOOTING.md)

## 📝 更新日志

### v2.0.0 (增强版)
- ✅ 支持多类型更新包 (完整包/增量包/热修复包)
- ✅ 智能存储管理和自动清理
- ✅ 高级GUI管理工具
- ✅ 增强的API接口
- ✅ 大文件上传支持 (1GB+)

### v1.0.0 (基础版)
- ✅ 基础更新服务器功能
- ✅ 简单文件上传下载
- ✅ 版本管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

- 文档: [项目Wiki](wiki)
- 问题反馈: [Issues](issues)
- 讨论: [Discussions](discussions)

---

**Omega更新服务器** - 让软件更新变得简单高效 🚀
