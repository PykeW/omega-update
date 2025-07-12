# Omega更新系统项目结构 - 增强版

本文档描述了Omega更新系统增强版的完整项目结构和各个组件的功能。

## 📁 项目根目录结构

```
omega-update/
├── README.md                    # 项目说明文档
├── PROJECT_STRUCTURE.md         # 项目结构说明（本文件）
├── DEPLOYMENT_GUIDE.md          # 详细部署指南
├── API_DOCUMENTATION.md         # 完整API文档
├── Pipfile                      # Python依赖管理文件
├── Pipfile.lock                 # 锁定的依赖版本
├── enhanced_database.py         # 增强数据库模型
├── storage_manager.py           # 存储管理器
├── enhanced_main.py             # 增强版API服务
├── advanced_upload_gui.py       # 高级GUI工具
├── deploy_enhanced_version.ps1  # 部署脚本
├── storage_management_strategy.md # 存储管理策略
├── deployment/                  # 部署相关文件
└── update_server/               # 原始服务器端代码
```

## 🔧 核心组件详解

### 1. 增强版核心文件

#### enhanced_database.py
- **功能**: 增强的数据库模型定义
- **特性**:
  - 支持多种包类型 (FULL/PATCH/HOTFIX)
  - 存储统计和清理历史
  - 下载日志和服务器配置
  - 自动初始化和配置管理

#### storage_manager.py
- **功能**: 智能存储空间管理
- **特性**:
  - 实时存储监控
  - 自动清理策略
  - 版本保护机制
  - 存储健康检查

#### enhanced_main.py
- **功能**: 增强版FastAPI服务器
- **特性**:
  - 多类型包上传支持
  - 智能版本检查
  - 存储管理API
  - 大文件上传优化

#### advanced_upload_gui.py
- **功能**: 高级图形界面管理工具
- **特性**:
  - 包类型选择界面
  - 存储状态监控
  - 批量操作支持
  - 实时日志显示

### 2. 部署和配置

#### deploy_enhanced_version.ps1
- **功能**: 自动化部署脚本
- **特性**:
  - 一键部署到服务器
  - 自动备份和回滚
  - 服务配置和启动
  - 功能验证测试

#### storage_management_strategy.md
- **功能**: 存储管理策略文档
- **内容**:
  - 40GB存储分配策略
  - 版本保留规则
  - 自动清理机制
  - 监控和告警配置

### 3. 部署目录 (deployment/)

```
deployment/
├── server_config.json           # 服务器配置文件
├── server_config.py            # 服务器配置模块
├── nginx.conf                  # Nginx配置文件
├── omega-update-server.service # systemd服务文件
├── deploy.sh                   # Linux部署脚本
├── quick_deploy.sh             # 快速部署脚本
├── auto_server_setup.ps1       # 自动服务器设置
├── auto_server_config.ps1      # 自动服务器配置
├── diagnose.sh                 # 诊断脚本
├── fix_common_issues.sh        # 常见问题修复
├── fix_server_limits.sh        # 服务器限制修复
├── set_permissions.ps1         # 权限设置脚本
├── manual_commands.txt         # 手动命令参考
├── gui_config.json             # GUI配置文件
└── 文档目录/
    ├── DEPLOYMENT_CHECKLIST.md # 部署检查清单
    ├── GUI_USAGE.md            # GUI使用指南
    ├── MANUAL_UPLOAD.md        # 手动上传指南
    ├── QUICK_START.md          # 快速开始指南
    ├── README.md               # 部署说明
    ├── SIMPLE_DEPLOY_GUIDE.md  # 简化部署指南
    └── WINDOWS_DEPLOY.md       # Windows部署指南
```

### 4. 原始服务器代码 (update_server/)

```
update_server/
├── api/                        # API接口模块
│   ├── __init__.py
│   ├── routes.py              # 路由定义
│   └── middleware.py          # 中间件
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── database.py            # 数据库模型
│   └── schemas.py             # 数据模式
├── config/                     # 配置模块
│   ├── __init__.py
│   └── settings.py            # 设置文件
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── file_utils.py          # 文件工具
│   └── version_utils.py       # 版本工具
└── static/                     # 静态文件
    ├── css/
    ├── js/
    └── images/
```

## 🔄 数据流架构

### 1. 上传流程
```
GUI工具 → enhanced_main.py → storage_manager.py → enhanced_database.py
    ↓
文件存储 (/var/www/updates/)
```

### 2. 下载流程
```
客户端 → Nginx → enhanced_main.py → 文件系统
```

### 3. 存储管理流程
```
定时任务 → storage_manager.py → 清理策略 → 文件删除 → 数据库更新
```

## 📊 数据库架构

### 主要表结构

1. **versions** - 版本信息
2. **packages** - 更新包信息
3. **package_files** - 包文件详情
4. **storage_stats** - 存储统计
5. **cleanup_history** - 清理历史
6. **download_logs** - 下载日志
7. **server_config** - 服务器配置

### 关系图
```
versions (1) ←→ (N) packages (1) ←→ (N) package_files
    ↓
storage_stats
    ↓
cleanup_history
```

## 🚀 部署架构

### 生产环境
```
Internet → Nginx (80/443) → FastAPI (8000) → SQLite/PostgreSQL
                ↓
        文件存储 (/var/www/updates/)
```

### 开发环境
```
本地 → Python直接运行 (8000) → SQLite
```

## 📝 配置文件说明

### 1. server_config.json
```json
{
  "server": {
    "ip": "服务器IP",
    "domain": "域名"
  },
  "api": {
    "key": "API密钥"
  }
}
```

### 2. .env文件
```bash
API_KEY=api密钥
DATABASE_URL=数据库连接
MAX_FILE_SIZE=最大文件大小
LOG_LEVEL=日志级别
```

### 3. Nginx配置要点
- client_max_body_size: 1200M
- 超时设置: 1800s
- 代理配置: 转发到8000端口

## 🔧 开发指南

### 1. 本地开发环境设置
```bash
# 安装依赖
pipenv install

# 激活环境
pipenv shell

# 运行服务器
python enhanced_main.py
```

### 2. 添加新功能
1. 修改数据库模型 (enhanced_database.py)
2. 更新存储管理 (storage_manager.py)
3. 添加API接口 (enhanced_main.py)
4. 更新GUI界面 (advanced_upload_gui.py)

### 3. 测试流程
1. 单元测试
2. 集成测试
3. GUI功能测试
4. 部署测试

## 📈 扩展计划

### 短期目标
- [ ] 支持更多文件格式
- [ ] 增加用户权限管理
- [ ] 优化大文件上传性能

### 长期目标
- [ ] 支持分布式存储
- [ ] 添加CDN集成
- [ ] 实现负载均衡

## 🔍 监控和维护

### 1. 日志文件位置
- 应用日志: `/opt/omega-update-server/logs/`
- Nginx日志: `/var/log/nginx/`
- 系统日志: `journalctl -u omega-update-server`

### 2. 监控指标
- 存储使用率
- API响应时间
- 错误率统计
- 下载统计

### 3. 维护任务
- 定期数据库清理
- 日志轮转
- 存储空间监控
- 安全更新

---

这个项目结构支持从简单的文件更新到复杂的企业级部署需求。通过模块化设计，可以根据具体需求选择使用相应的组件。
