# Omega 更新系统 - 项目结构说明

## 📁 项目目录结构

```
omega-update/
├── 📁 server/                     # 🖥️ 服务器核心模块
│   ├── enhanced_main.py           # 主服务器应用 (FastAPI)
│   ├── enhanced_database.py       # 数据库模型 (SQLAlchemy)
│   ├── server_config.py           # 服务器配置管理
│   ├── storage_manager.py         # 存储管理器
│   ├── omega_updates.db           # SQLite 数据库文件
│   └── __init__.py
│
├── 📁 tools/                      # 🛠️ 客户端工具模块
│   ├── 📁 upload/                 # 📤 上传工具
│   │   ├── upload_tool.py         # GUI 上传工具
│   │   ├── auto_upload.py         # 自动上传工具
│   │   ├── auto_upload_batch.py   # 批量上传工具
│   │   ├── upload_handler.py      # 上传处理器
│   │   └── __init__.py
│   │
│   ├── 📁 download/               # 📥 下载工具
│   │   ├── download_tool.py       # GUI 下载工具
│   │   ├── download_manager.py    # 下载管理器
│   │   ├── download_handler.py    # 下载处理器
│   │   ├── local_file_scanner.py  # 本地文件扫描器
│   │   └── __init__.py
│   │
│   ├── 📁 common/                 # 🔧 通用工具
│   │   ├── common_utils.py        # 通用工具函数
│   │   ├── ui_factory.py          # UI 组件工厂
│   │   ├── storage_handler.py     # 存储处理器
│   │   ├── difference_detector.py # 差异检测器
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── 📁 config/                     # ⚙️ 配置文件
│   ├── config.json                # 主配置文件
│   ├── upload_config.json         # 上传配置
│   ├── upload_config_sample.json  # 上传配置示例
│   └── batch_config_sample.json   # 批量配置示例
│
├── 📁 deployment/                 # 🚀 部署相关
│   ├── deploy.sh                  # Linux 部署脚本
│   ├── nginx.conf                 # Nginx 配置
│   ├── auto_server_setup.ps1      # Windows 自动部署
│   └── ...                        # 其他部署文件
│
├── 📁 releases/                   # 📦 发布版本
│   └── OmegaDownloadTool_v3.1.0/  # 打包好的下载工具
│
├── 📁 docs/                       # 📚 文档
│   ├── README.md                  # 项目说明
│   ├── API_DOCUMENTATION.md       # API 文档
│   └── DEPLOYMENT_GUIDE.md        # 部署指南
│
├── 📁 scripts/                    # 📜 脚本文件
│   ├── build_download_tool.py     # 构建下载工具
│   ├── deploy_enhanced_version.ps1 # 部署脚本
│   ├── start_download_tool.sh     # 启动下载工具 (Linux)
│   └── start_upload_tool.sh       # 启动上传工具 (Linux)
│
├── 🐍 start_server.py             # 服务器启动脚本
├── 🐍 start_upload_tool.py        # 上传工具启动脚本
├── 🐍 start_download_tool.py      # 下载工具启动脚本
├── 📄 README.md                   # 项目主说明文档
├── 📄 PROJECT_STRUCTURE.md        # 本文档
├── ⚙️ .env                        # 环境变量配置
├── ⚙️ .env.example                # 环境变量配置示例
├── 📦 Pipfile                     # Python 依赖管理
├── 📦 Pipfile.lock                # 依赖锁定文件
└── 🚫 .gitignore                  # Git 忽略文件
```

## 🚀 快速启动

### 环境准备
```bash
# 安装依赖
pipenv install
pipenv shell

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置必要配置
```

### 启动组件
```bash
# 启动服务器（后端 API）
python start_server.py

# 启动上传工具（GUI）
python start_upload_tool.py

# 启动下载工具（GUI）
python start_download_tool.py
```

### 访问服务
- **服务器**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 📝 重要说明

1. **模块化设计**：项目采用模块化设计，各功能独立且可复用
2. **路径管理**：所有启动脚本会自动设置正确的 Python 路径
3. **配置管理**：配置文件统一放在 `config/` 目录
4. **文档齐全**：详细文档在 `docs/` 目录
5. **部署简化**：部署相关文件在 `deployment/` 目录

## 🔧 开发指南

### 代码组织原则
- **server/** - 服务器端开发，基于 FastAPI 框架
- **tools/upload/** - 上传功能开发，包含 GUI 和业务逻辑
- **tools/download/** - 下载功能开发，包含更新检查和文件管理
- **tools/common/** - 共享组件开发，可被多个模块复用

### 开发流程
1. **新功能开发**：在对应模块目录下添加新文件
2. **配置修改**：编辑 `config/` 目录下的配置文件
3. **文档更新**：同步更新 `docs/` 目录下的文档
4. **测试验证**：使用启动脚本测试功能

### 导入规范
```python
# 服务器端模块导入
from server.enhanced_database import Version, Package
from server.storage_manager import storage_manager

# 工具模块导入
from tools.common.common_utils import get_config
from tools.upload.upload_handler import UploadHandler
from tools.download.download_manager import DownloadManager
```

## 🧪 测试指南

### 单元测试
```bash
# 运行所有测试
python -m pytest

# 运行特定模块测试
python -m pytest tests/test_server.py
python -m pytest tests/test_upload.py
```

### 集成测试
```bash
# 启动服务器
python start_server.py

# 在另一个终端测试上传功能
python start_upload_tool.py

# 测试下载功能
python start_download_tool.py
```

## 🔍 故障排除

### 常见问题
1. **ModuleNotFoundError**: 使用提供的启动脚本，确保 Python 路径正确
2. **配置错误**: 检查 `.env` 文件和 `config/` 目录下的配置
3. **端口冲突**: 修改 `.env` 中的 `SERVER_PORT` 设置
4. **数据库问题**: 检查 `server/omega_updates.db` 文件权限

### 调试技巧
- 查看服务器日志：`/var/log/omega-updates/server.log`
- 使用 API 文档页面测试接口
- 检查网络连接和防火墙设置
