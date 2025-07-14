# Omega 更新系统 - 文档中心

欢迎使用 Omega 更新系统！这是一个功能完整的软件更新管理系统，支持完整包、增量包和智能存储管理。采用模块化架构设计，提供更好的维护性和扩展性。

## 📚 文档导航

### 🚀 快速开始
- **[项目主页](../README.md)** - 项目概览和快速开始指南
- **[项目结构](../PROJECT_STRUCTURE.md)** - 详细的项目结构说明
- **[部署指南](DEPLOYMENT_GUIDE.md)** - 完整的部署和配置指南

### 🛠️ 开发文档
- **[开发指南](DEVELOPMENT_GUIDE.md)** - 开发环境设置和编码规范
- **[API 文档](API_DOCUMENTATION.md)** - 完整的 API 接口文档
- **[故障排除](TROUBLESHOOTING.md)** - 常见问题和解决方案

## 🎯 主要特性

### 多类型更新包支持
- **完整包 (FULL)**: 支持大文件上传（8GB+），适用于全新安装
- **增量包 (PATCH)**: 版本间增量更新，节省带宽和存储空间
- **热修复包 (HOTFIX)**: 紧急bug修复，快速部署
- **单文件上传**: 支持文件夹级别的增量更新

### 智能存储管理
- **自动清理**: 存储使用率达到85%时自动清理旧版本
- **版本保护**: 关键版本和最新稳定版本受保护
- **存储监控**: 实时监控存储使用情况和健康状态
- **空间优化**: 智能分配策略，支持大容量存储

### 模块化架构 (v2.0)
- **代码模块化**: 清晰的职责分离，模块化设计
- **启动脚本**: 简化的启动方式，自动路径管理
- **类型安全**: 完整的类型注解和错误处理
- **易于维护**: 便于扩展、测试和调试

### 高级管理功能
- **独立GUI工具**: 上传工具和下载工具完全独立
- **RESTful API**: 完整的API接口，支持自动化集成
- **版本管理**: 智能版本检查，优先推荐增量更新
- **文件级更新**: 支持文件级别的差异检测和更新

## 📁 项目结构 (v2.0 模块化架构)

```
omega-update/
├── 📁 server/                     # 🖥️ 服务器核心模块
│   ├── enhanced_main.py           # FastAPI 主应用
│   ├── enhanced_database.py       # SQLAlchemy 数据库模型
│   ├── server_config.py           # 服务器配置管理
│   ├── storage_manager.py         # 存储空间管理器
│   └── omega_updates.db           # SQLite 数据库文件
├── 📁 tools/                      # 🛠️ 客户端工具模块
│   ├── 📁 upload/                 # 📤 上传工具
│   │   ├── upload_tool.py         # GUI 上传工具
│   │   ├── auto_upload.py         # 自动上传工具
│   │   ├── auto_upload_batch.py   # 批量上传工具
│   │   └── upload_handler.py      # 上传业务逻辑
│   ├── 📁 download/               # 📥 下载工具
│   │   ├── download_tool.py       # GUI 下载工具
│   │   ├── download_manager.py    # 下载管理器
│   │   ├── download_handler.py    # 下载业务逻辑
│   │   └── local_file_scanner.py  # 本地文件扫描器
│   └── 📁 common/                 # 🔧 通用工具
│       ├── common_utils.py        # 通用工具函数
│       ├── ui_factory.py          # GUI 组件工厂
│       ├── storage_handler.py     # 存储处理器
│       └── difference_detector.py # 文件差异检测器
├── 📁 config/                     # ⚙️ 配置文件
│   ├── config.json                # 主配置文件
│   ├── upload_config.json         # 上传工具配置
│   └── *.json                     # 其他配置文件
├── 📁 deployment/                 # 🚀 部署相关文件
├── 📁 releases/                   # 📦 发布版本
├── 📁 docs/                       # 📚 项目文档
├── 📁 scripts/                    # 📜 构建和部署脚本
├── 🐍 start_server.py             # 服务器启动脚本
├── 🐍 start_upload_tool.py        # 上传工具启动脚本
├── 🐍 start_download_tool.py      # 下载工具启动脚本
├── ⚙️ .env                        # 环境变量配置
├── ⚙️ .env.example                # 环境变量配置模板
└── 📦 Pipfile                     # Python 依赖管理
```

## 🛠️ 快速开始

### 1. 环境要求

**服务器端:**
- Ubuntu 22.04 LTS / CentOS 8+ / Windows Server
- Python 3.8+
- pipenv (推荐) 或 pip
- 至少40GB存储空间

**客户端:**
- Windows 10/11 / Linux / macOS
- Python 3.8+
- tkinter (GUI支持)

### 2. 安装和启动

#### 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd omega-update

# 安装依赖
pipenv install
pipenv shell

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置 API_KEY 等配置
```

#### 启动系统
```bash
# 启动服务器
python start_server.py

# 启动上传工具 (新终端)
python start_upload_tool.py

# 启动下载工具 (新终端)
python start_download_tool.py
```

#### 访问服务
- **服务器**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 3. 详细部署指南
- **生产部署**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **开发指南**: [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)
- **故障排除**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

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

## 📚 完整文档

### 核心文档
- **[API 文档](API_DOCUMENTATION.md)** - 完整的 REST API 接口说明
- **[部署指南](DEPLOYMENT_GUIDE.md)** - 生产环境部署和配置
- **[开发指南](DEVELOPMENT_GUIDE.md)** - 开发环境设置和编码规范
- **[故障排除](TROUBLESHOOTING.md)** - 常见问题和解决方案

### 项目信息
- **[项目结构](../PROJECT_STRUCTURE.md)** - 详细的项目结构说明
- **[主页](../README.md)** - 项目概览和快速开始

## 🤝 贡献指南

### 开发流程
1. Fork 项目并创建功能分支
2. 遵循模块化设计原则
3. 添加相应的测试和文档
4. 提交 Pull Request

### 代码规范
- 遵循 PEP 8 代码风格
- 使用有意义的变量和函数名
- 添加适当的类型注解和文档字符串
- 保持模块化设计原则

详细开发指南请参考 [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)

## 📄 许可证

本项目采用 MIT 许可证

## 📞 获取帮助

### 问题排查
1. 查看 [故障排除指南](TROUBLESHOOTING.md)
2. 检查相关日志文件
3. 访问 API 文档页面进行调试

### 技术支持
- 查看完整文档
- 提交 Issue 反馈问题
- 参与社区讨论

---

**Omega 更新系统 v2.0** - 模块化架构，让软件更新变得简单高效 🚀
