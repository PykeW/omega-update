# Omega 更新系统

一个完整的软件更新管理系统，支持完整包、增量包和智能存储管理。采用模块化架构设计，提供服务器端和客户端工具的完整解决方案。

## 🚀 快速开始

### 环境准备

1. **安装 Python 依赖**：
   ```bash
   pipenv install
   pipenv shell
   ```

2. **配置环境变量**：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置 API_KEY 等必要配置
   ```

### 启动系统

使用新的启动脚本，一键启动各个组件：

```bash
# 启动服务器（后端 API）
python start_server.py

# 启动上传工具（GUI）
python start_upload_tool.py

# 启动下载工具（GUI）
python start_download_tool.py
```

### 服务器访问

- **服务器地址**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 📁 项目结构

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
├── 📦 Pipfile                     # Python 依赖管理
└── 📄 PROJECT_STRUCTURE.md        # 详细项目结构说明
```

## ✨ 功能特性

### 服务器端功能
- ✅ **RESTful API 接口** - 完整的 HTTP API，支持 OpenAPI 文档
- ✅ **完整包管理** - 支持完整软件包的上传、存储和分发
- ✅ **增量包支持** - 智能增量更新，减少下载量
- ✅ **热修复包** - 紧急修复包的快速分发
- ✅ **智能存储管理** - 自动清理、版本保留策略
- ✅ **文件完整性验证** - SHA256 哈希验证
- ✅ **版本回滚功能** - 支持版本回退和恢复

### 客户端工具功能
- ✅ **图形化上传工具** - 直观的 GUI 界面，支持文件和文件夹上传
- ✅ **图形化下载工具** - 智能更新检查和下载管理
- ✅ **批量处理** - 支持批量上传和自动化操作
- ✅ **断点续传** - 网络中断后可继续传输
- ✅ **进度监控** - 实时显示传输进度和状态
- ✅ **差异检测** - 智能识别需要更新的文件

## 🛠️ 开发指南

### 模块化架构

项目采用模块化设计，各模块职责清晰：

- **server/** - 服务器端核心逻辑，基于 FastAPI
- **tools/upload/** - 上传相关功能模块
- **tools/download/** - 下载相关功能模块
- **tools/common/** - 共享工具和组件

### 开发环境设置

1. **克隆项目**：
   ```bash
   git clone <repository-url>
   cd omega-update
   ```

2. **安装开发依赖**：
   ```bash
   pipenv install --dev
   pipenv shell
   ```

3. **配置开发环境**：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件设置开发配置
   ```

### 添加新功能

1. **服务器端**：在 `server/` 目录下修改相应模块
2. **客户端工具**：在 `tools/` 对应子目录下开发
3. **共享功能**：在 `tools/common/` 目录下添加通用组件

## 📚 文档

详细文档请查看 `docs/` 目录：

- [📖 API 文档](docs/API_DOCUMENTATION.md) - 完整的 API 接口说明
- [🚀 部署指南](docs/DEPLOYMENT_GUIDE.md) - 生产环境部署指南
- [🏗️ 项目结构](PROJECT_STRUCTURE.md) - 详细的项目结构说明

## 🔧 故障排除

### 常见问题

1. **导入错误**：确保使用提供的启动脚本，它们会自动设置正确的 Python 路径
2. **配置问题**：检查 `.env` 文件是否正确配置
3. **端口冲突**：默认端口 8000，可在 `.env` 中修改 `SERVER_PORT`

### 获取帮助

- 查看 `docs/` 目录下的详细文档
- 检查日志文件（默认在 `/var/log/omega-updates/`）
- 使用 API 文档页面测试接口：http://localhost:8000/docs

## 📄 许可证

MIT License

---

**版本**: 2.0.0
**最后更新**: 2025-07-14
**维护状态**: 积极维护
