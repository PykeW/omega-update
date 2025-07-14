# Omega 更新系统 - 开发指南

本指南详细介绍如何在重构后的模块化架构中进行开发。

## 🏗️ 架构概览

### 模块化设计
```
omega-update/
├── server/          # 服务器端模块 (FastAPI)
├── tools/           # 客户端工具模块
│   ├── upload/      # 上传功能
│   ├── download/    # 下载功能
│   └── common/      # 共享组件
├── config/          # 配置文件
└── docs/            # 文档
```

### 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: tkinter (GUI工具)
- **依赖管理**: pipenv
- **数据库**: SQLite (可扩展到 PostgreSQL)

## 🚀 开发环境设置

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd omega-update

# 安装依赖
pipenv install --dev
pipenv shell

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件
```

### 2. 启动开发服务器
```bash
# 启动后端服务器
python start_server.py

# 启动客户端工具 (在新终端)
python start_upload_tool.py
python start_download_tool.py
```

### 3. 开发工具
- **API文档**: http://localhost:8000/docs
- **数据库**: `server/omega_updates.db` (SQLite Browser)
- **日志**: `/var/log/omega-updates/server.log`

## 📝 编码规范

### 导入规范
```python
# 服务器端模块导入
from server.enhanced_database import Version, Package
from server.storage_manager import storage_manager
from server.server_config import ServerConfig

# 客户端工具导入
from tools.common.common_utils import get_config, LogManager
from tools.upload.upload_handler import UploadHandler
from tools.download.download_manager import DownloadManager

# 跨模块导入
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
```

### 文件组织
- **单一职责**: 每个文件专注一个功能
- **模块化**: 相关功能放在同一目录
- **配置分离**: 配置文件统一在 `config/` 目录
- **文档同步**: 代码变更时同步更新文档

### 命名约定
- **文件名**: 小写字母 + 下划线 (`upload_handler.py`)
- **类名**: 大驼峰 (`UploadHandler`)
- **函数名**: 小写字母 + 下划线 (`get_config`)
- **常量**: 大写字母 + 下划线 (`API_KEY`)

## 🔧 开发流程

### 1. 新功能开发

#### 服务器端功能
```bash
# 1. 在 server/ 目录下创建新模块
touch server/new_feature.py

# 2. 在 enhanced_main.py 中添加路由
# 3. 更新数据库模型 (如需要)
# 4. 编写测试
# 5. 更新API文档
```

#### 客户端功能
```bash
# 1. 在对应工具目录下创建新模块
touch tools/upload/new_feature.py

# 2. 在主工具文件中集成
# 3. 更新UI界面 (如需要)
# 4. 编写测试
# 5. 更新用户文档
```

### 2. 测试流程
```bash
# 单元测试
python -m pytest tests/

# 集成测试
python start_server.py &
python tests/integration_test.py

# 手动测试
python start_upload_tool.py
python start_download_tool.py
```

### 3. 代码审查
- 检查导入路径是否正确
- 确认模块化设计原则
- 验证错误处理和日志记录
- 检查配置文件更新

## 🗃️ 数据库开发

### 模型定义
```python
# server/enhanced_database.py
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewModel(Base):
    __tablename__ = 'new_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
```

### 数据库迁移
```python
# 在 enhanced_database.py 中添加新模型后
from server.enhanced_database import init_database
init_database()  # 自动创建新表
```

## 🎨 UI 开发

### GUI 组件
```python
# tools/common/ui_factory.py
from tools.common.ui_factory import UIComponentFactory

# 创建标准组件
frame = UIComponentFactory.create_labeled_frame(parent, "标题")
button = UIComponentFactory.create_button(parent, "按钮", callback)
progress = UIComponentFactory.create_progress_bar(parent)
```

### 事件处理
```python
# 使用线程避免UI阻塞
import threading

def long_running_task():
    # 耗时操作
    pass

def on_button_click():
    thread = threading.Thread(target=long_running_task)
    thread.daemon = True
    thread.start()
```

## 📦 配置管理

### 配置文件结构
```
config/
├── config.json              # 主配置
├── upload_config.json       # 上传工具配置
├── upload_config_sample.json # 配置模板
└── batch_config_sample.json  # 批量配置模板
```

### 配置读取
```python
from tools.common.common_utils import get_config

# 读取配置
config = get_config()
server_url = config.get('server_url', 'http://localhost:8000')
api_key = config.get('api_key', '')
```

## 🧪 测试指南

### 测试结构
```
tests/
├── test_server/         # 服务器端测试
├── test_upload/         # 上传工具测试
├── test_download/       # 下载工具测试
├── test_common/         # 共享组件测试
└── integration/         # 集成测试
```

### 测试示例
```python
# tests/test_server/test_api.py
import pytest
from fastapi.testclient import TestClient
from server.enhanced_main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## 🚀 部署准备

### 构建检查
```bash
# 检查导入
python -c "from server.enhanced_main import app; print('Server OK')"
python -c "from tools.upload.upload_tool import UploadToolRefactored; print('Upload OK')"
python -c "from tools.download.download_tool import DownloadToolRefactored; print('Download OK')"

# 检查配置
python -c "from server.server_config import ServerConfig; print('Config OK')"

# 运行测试
python -m pytest
```

### 打包工具
```bash
# 构建可执行文件
python scripts/build_download_tool.py

# 检查生成的文件
ls releases/OmegaDownloadTool_v*/
```

## 📚 文档维护

### 文档更新流程
1. **代码变更**: 修改代码时同步更新相关文档
2. **API变更**: 更新 `docs/API_DOCUMENTATION.md`
3. **部署变更**: 更新 `docs/DEPLOYMENT_GUIDE.md`
4. **结构变更**: 更新 `PROJECT_STRUCTURE.md`

### 文档规范
- 使用 Markdown 格式
- 包含代码示例
- 提供清晰的步骤说明
- 保持版本信息更新

---

**版本**: 2.0.0  
**最后更新**: 2025-07-14  
**相关文档**: [README.md](../README.md) | [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
