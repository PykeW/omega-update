# Omega更新服务器 - 模块化架构版 v3.1

一个功能完整的软件更新服务器，支持完整包、增量包和智能存储管理。采用模块化架构设计，提供更好的维护性和扩展性。

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

### 模块化架构 (v3.1新特性)
- **代码模块化**: 清晰的职责分离，每个模块不超过500行
- **工厂模式**: 统一的GUI组件创建和管理
- **类型安全**: 完整的类型注解和错误处理
- **易于维护**: 便于扩展、测试和调试

### 高级管理功能
- **独立GUI工具**: 上传工具和下载工具完全独立
- **RESTful API**: 完整的API接口，支持自动化集成
- **版本管理**: 智能版本检查，优先推荐增量更新
- **下载统计**: 详细的下载和使用统计

## 📁 项目结构 (v3.1 模块化架构)

```
omega-update/
├── 🏗️ 核心模块 (新架构)
│   ├── ui_factory.py             # GUI组件工厂 (345行)
│   ├── upload_handler.py         # 上传业务逻辑 (388行)
│   ├── download_handler.py       # 下载业务逻辑 (363行)
│   └── storage_handler.py        # 存储管理逻辑 (239行)
├── 🖥️ 客户端工具
│   ├── upload_tool.py            # 上传工具 (418行)
│   ├── download_tool.py          # 下载工具 (405行)
│   ├── start_upload_tool.sh      # Linux/macOS启动脚本
│   └── start_download_tool.sh    # Linux/macOS启动脚本
├── 🔧 支持模块
│   ├── common_utils.py           # 共享工具函数
│   ├── local_file_scanner.py     # 本地文件扫描
│   ├── difference_detector.py    # 差异检测
│   └── download_manager.py       # 下载管理
├── 🗄️ 服务器端
│   ├── enhanced_database.py      # 增强数据库模型
│   ├── storage_manager.py        # 存储管理器
│   ├── enhanced_main.py          # 增强版API服务
│   └── deploy_enhanced_version.ps1 # 部署脚本
├── 📚 文档
│   ├── README.md                 # 项目说明 (本文件)
│   ├── REFACTORING_COMPLETE_SUMMARY.md # 重构总结
│   ├── MIGRATION_GUIDE.md        # 迁移指南
│   └── API_DOCUMENTATION.md      # API文档
├── 🚀 部署文件
│   └── deployment/               # 部署相关文件
│       ├── server_config.json   # 服务器配置
│       ├── nginx.conf           # Nginx配置
│       ├── deploy.sh            # Linux部署脚本
│       └── quick_deploy.sh      # 快速部署脚本
└── 📦 原始模块 (兼容性保留)
    └── update_server/           # 原始服务器模块
        ├── api/                 # API模块
        ├── models/              # 数据模型
        └── utils/               # 工具函数
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

### 3. 使用客户端工具 (v3.1 新版)

#### 上传工具
```bash
# Linux/macOS (推荐)
./start_upload_tool.sh

# 直接启动
python upload_tool.py
```

#### 下载工具
```bash
# Linux/macOS (推荐)
./start_download_tool.sh

# 直接启动
python download_tool.py
```

#### 功能特性
- **独立运行**: 两个工具完全独立，可单独使用
- **模块化设计**: 基于工厂模式的组件架构
- **类型安全**: 完整的类型注解和错误处理
- **用户友好**: 直观的界面和详细的进度显示

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

### v3.1.0 (模块化架构版) - 2025-07-13
- 🎯 **代码重构**: 完成模块化重构，每个文件不超过500行
- 🏗️ **架构优化**: 采用工厂模式和依赖注入设计
- 🔧 **类型安全**: 添加完整的类型注解和错误处理
- 📦 **工具分离**: 上传和下载工具完全独立
- 🚀 **性能提升**: 优化内存使用和响应速度
- 📚 **文档完善**: 新增迁移指南和重构总结
- 🧪 **测试覆盖**: 全面的功能测试验证

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

## 🔧 开发指南 (v3.1 新增)

### 模块化架构说明

#### 核心设计原则
- **单一职责**: 每个模块专注特定功能
- **依赖注入**: 通过构造函数注入依赖
- **工厂模式**: 统一的组件创建和配置
- **类型安全**: 完整的类型注解

#### 模块职责分工
```python
# UI组件工厂 - 负责界面组件创建
from ui_factory import UIComponentFactory, WindowFactory

# 业务逻辑处理器 - 负责核心业务逻辑
from upload_handler import UploadHandler
from download_handler import DownloadHandler
from storage_handler import StorageHandler

# 主应用程序 - 负责协调和界面管理
from upload_tool import UploadToolRefactored
from download_tool import DownloadToolRefactored
```

#### 扩展新功能
```python
# 1. 扩展UI组件
class CustomUIFactory(UIComponentFactory):
    @staticmethod
    def create_custom_component():
        # 自定义组件逻辑
        pass

# 2. 扩展业务逻辑
class CustomUploadHandler(UploadHandler):
    def custom_upload_logic(self):
        # 自定义业务逻辑
        pass

# 3. 在主工具中使用
class CustomUploadTool(UploadToolRefactored):
    def __init__(self, root):
        super().__init__(root)
        self.custom_handler = CustomUploadHandler(self.log_manager)
```

### 代码质量要求
- **文件大小**: 每个文件不超过500行
- **函数复杂度**: 每个函数不超过50行
- **类型注解**: 所有公共接口必须有类型注解
- **错误处理**: 完善的异常处理和日志记录

### 测试指南
```bash
# 运行模块测试
python -m pytest tests/

# 功能测试
python test_upload_tool.py
python test_download_tool.py

# 集成测试
python test_integration.py
```

## 🤝 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 遵循代码质量要求
4. 添加相应的测试
5. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
6. 推送到分支 (`git push origin feature/AmazingFeature`)
7. 创建 Pull Request

### 代码规范
- 遵循PEP 8代码风格
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 保持模块化设计原则

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

### 文档资源
- **使用指南**: 本README文件
- **迁移指南**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
- **重构总结**: [REFACTORING_COMPLETE_SUMMARY.md](REFACTORING_COMPLETE_SUMMARY.md)
- **API文档**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **部署指南**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### 获取帮助
- 问题反馈: [Issues](issues)
- 功能讨论: [Discussions](discussions)
- 技术支持: 查看相关文档或提交Issue

---

**Omega更新服务器 v3.1** - 模块化架构，让软件更新变得简单高效 🚀
