# Omega更新系统项目结构

## 项目概述

Omega更新系统是一个完整的软件自动更新解决方案，包括客户端更新器、服务器端API和增量更新包生成工具。

## 目录结构

```
omega-update/
├── README.md                          # 项目说明文档
├── PROJECT_STRUCTURE.md               # 项目结构说明（本文件）
├── Pipfile                            # Python依赖管理
├── Pipfile.lock                       # 锁定的依赖版本
├── .gitignore                         # Git忽略规则
├── 软件更新器参考资料.md                # 开发参考资料
├── version_analyzer.py                # 版本分析工具
├── version_diff.json                  # 版本差异数据
├── version_report.txt                 # 版本分析报告
├── generate_update_package.py         # 更新包生成工具（主要）
├── simple_update_generator.py         # 简化版更新包生成工具
│
├── updater/                           # 更新器主模块
│   ├── __init__.py                    # 包初始化文件
│   ├── src/                           # 源代码目录
│   │   ├── __init__.py
│   │   ├── main.py                    # 更新器主入口
│   │   ├── core/                      # 核心功能模块
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # 配置管理
│   │   │   ├── app_manager.py         # 应用程序管理
│   │   │   ├── update_manager.py      # 更新管理器
│   │   │   └── incremental_updater.py # 增量更新器
│   │   ├── utils/                     # 工具模块
│   │   │   ├── __init__.py
│   │   │   ├── file_utils.py          # 文件操作工具
│   │   │   └── binary_diff.py         # 二进制差分工具
│   │   └── gui/                       # 图形界面模块
│   │       └── __init__.py
│   ├── resources/                     # 资源文件
│   ├── build/                         # 构建输出（被忽略）
│   └── dist/                          # 分发文件（被忽略）
│
├── update_server/                     # 服务器端模块
│   ├── api/                           # API接口
│   │   └── version_api.py             # 版本管理API
│   ├── models/                        # 数据模型
│   │   └── database.py                # 数据库模型
│   ├── utils/                         # 服务器工具
│   ├── static/                        # 静态文件
│   └── config/                        # 服务器配置
│
├── update_packages/                   # 生成的更新包（被忽略）
│   └── update_2.2.5/                 # 示例更新包
│       ├── update_info.json          # 更新元数据
│       ├── file_manifest.json        # 文件清单
│       ├── checksums.json            # 校验文件
│       └── files/                     # 更新文件
│
└── omega_dist/                        # 测试版本文件（被忽略）
    ├── omega_1_7_3/                  # 旧版本
    └── omega_2_2_5/                  # 新版本
```

## 核心模块说明

### 1. 更新器客户端 (`updater/`)

- **config.py**: 配置管理，支持JSON配置文件
- **app_manager.py**: 管理主应用程序的启动、关闭、版本检测
- **update_manager.py**: 核心更新逻辑，处理下载和应用更新
- **incremental_updater.py**: 增量更新算法，支持文件级和二进制级差分
- **file_utils.py**: 文件操作工具，包括哈希计算、文件比较等
- **binary_diff.py**: 二进制差分工具，支持bsdiff和xdelta算法

### 2. 服务器端 (`update_server/`)

- **database.py**: 数据库模型定义，使用SQLAlchemy ORM
- **version_api.py**: 版本管理API，提供版本检查、文件下载等接口

### 3. 工具脚本

- **generate_update_package.py**: 主要的更新包生成工具
- **simple_update_generator.py**: 简化版生成工具，避免复杂依赖
- **version_analyzer.py**: 版本分析工具，生成详细的差异报告

## 导入规则

### 绝对导入（推荐）

```python
from updater.src.core.incremental_updater import IncrementalUpdater
from updater.src.utils.file_utils import calculate_file_hash
```

### 相对导入（模块内部）

```python
from .config import config
from ..utils.file_utils import calculate_file_hash
```

## 开发指南

### 1. 环境设置

```bash
# 安装依赖
pipenv install

# 激活虚拟环境
pipenv shell

# 运行工具
python generate_update_package.py --help
```

### 2. 添加新模块

1. 在相应目录创建Python文件
2. 在 `__init__.py` 中添加导出
3. 更新相关的导入语句

### 3. 测试

```bash
# 测试导入
python -c "from updater.src.core import IncrementalUpdater; print('OK')"

# 生成更新包
python generate_update_package.py --old-version old/ --new-version new/ --output out/ --version 1.0.0
```

## 依赖管理

主要依赖包：
- `bsdiff4`: 二进制差分算法
- `requests`: HTTP请求库
- `psutil`: 进程管理
- `fastapi`: Web API框架
- `sqlalchemy`: 数据库ORM

## 注意事项

1. 所有 `__pycache__` 目录和 `.pyc` 文件都被忽略
2. 临时文件和构建产物不会被提交到版本控制
3. 敏感配置文件（如密钥）被忽略
4. 大型测试文件（如omega_dist）被忽略，但保留更新包示例
