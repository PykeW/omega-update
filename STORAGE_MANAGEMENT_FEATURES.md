# Omega更新服务器存储管理功能文档

## 功能概述

本次更新为Omega更新服务器添加了全面的存储管理功能，包括版本保留策略、智能备份机制、文件完整性验证和增强的GUI管理界面。

## 新增功能

### 1. 存储状态查看功能

#### 功能描述
- 显示服务器上保存的版本文件存储位置和目录结构
- 列出当前存储的所有版本文件及其占用空间
- 提供详细的文件信息包括SHA256哈希值

#### API端点
- `GET /api/v1/storage/structure` - 获取存储目录结构

#### GUI界面
- 新增"存储管理"按钮
- 存储结构标签页显示树形目录结构
- 实时显示文件大小和版本信息

### 2. 版本保留策略

#### 功能描述
- 自动清理旧版本文件以节省存储空间
- 可配置每个包类型的保留版本数量
- 默认保留策略：
  - 完整包：2个版本
  - 增量包：5个版本
  - 热修复包：10个版本

#### API端点
- `POST /api/v1/storage/retention/apply` - 应用版本保留策略
- `POST /api/v1/storage/retention/configure` - 配置保留策略

#### 实现细节
```python
# 默认配置
self.max_versions_per_platform = {
    PackageType.FULL: 2,      # 保留2个完整版本
    PackageType.PATCH: 5,     # 保留5个增量版本
    PackageType.HOTFIX: 10    # 保留10个热修复版本
}
```

### 3. 智能备份机制

#### 功能描述
- 在替换文件前自动备份原文件
- 创建按日期组织的备份目录结构
- 提供回滚功能，允许恢复到上一个版本

#### 备份目录结构
```
/var/www/omega-updates/uploads/backups/
├── full/
│   └── 20250713/
│       └── omega-v1.0.0-full-windows-x64_143022.zip
├── patches/
└── hotfixes/
```

#### API端点
- `POST /api/v1/version/rollback` - 回滚到备份版本

### 4. 文件完整性验证

#### 功能描述
- 基于SHA256哈希值的文件完整性验证
- 在下载前对比本地文件和服务器文件的哈希值
- 只下载发生变化的文件，跳过未修改的文件

#### API端点
- `POST /api/v1/file/verify` - 验证文件完整性
- `GET /api/v1/version/changes` - 获取版本文件变化信息

#### 使用示例
```python
# 验证文件完整性
result = storage_manager.verify_file_integrity(file_path, expected_hash)
if result['valid']:
    print("文件验证通过")
else:
    print(f"文件验证失败: {result['error']}")
```

### 5. 增强的GUI界面

#### 新增界面元素
- **存储管理窗口**：包含三个标签页
  - 存储结构：显示目录树和文件信息
  - 版本管理：配置和应用保留策略
  - 文件验证：验证文件完整性

#### 操作功能
- 实时查看存储结构
- 配置版本保留策略
- 应用清理策略并查看结果
- 验证文件完整性

## 技术实现

### 核心类扩展

#### StorageManager类新增方法
```python
def get_storage_structure(self, db: Session) -> Dict
def apply_version_retention_policy(self, db: Session) -> Dict
def verify_file_integrity(self, file_path: Path, expected_hash: str) -> Dict
def rollback_version(self, db: Session, package_id: int) -> Dict
def configure_retention_policy(self, package_type: PackageType, max_versions: int) -> Dict
```

#### 数据库集成
- 与现有数据库模型完全兼容
- 自动记录清理历史
- 更新包状态和统计信息

### 向后兼容性

- 所有现有API端点保持不变
- 现有GUI功能完全保留
- 数据库结构无破坏性更改
- 配置文件格式兼容

## 部署说明

### 服务器端部署
1. 更新服务器文件：
   ```bash
   scp storage_manager.py enhanced_main.py root@server:/opt/omega-update-server/
   ```

2. 重启服务：
   ```bash
   systemctl restart omega-update-server
   ```

### 客户端更新
- 直接运行更新的 `advanced_upload_gui.py`
- 无需额外配置，自动连接到生产服务器

## 测试验证

### 自动化测试
运行测试脚本验证所有功能：
```bash
python test_storage_features.py
```

### 测试覆盖
- ✅ 存储管理器初始化和配置
- ✅ API端点响应和功能
- ✅ GUI组件和方法存在性
- ✅ 文件完整性验证算法

## 使用指南

### 管理员操作
1. 打开GUI工具
2. 点击"存储管理"按钮
3. 在"版本管理"标签页配置保留策略
4. 点击"应用保留策略"清理旧版本
5. 在"存储结构"标签页查看清理结果

### 开发者集成
```python
from storage_manager import storage_manager

# 应用版本保留策略
result = storage_manager.apply_version_retention_policy(db)

# 验证文件完整性
integrity = storage_manager.verify_file_integrity(file_path, hash_value)

# 配置保留策略
storage_manager.configure_retention_policy(PackageType.FULL, 3)
```

## 性能优化

- 异步文件操作避免阻塞
- 增量哈希计算减少内存使用
- 智能清理策略最小化磁盘I/O
- GUI多线程操作保持响应性

## 安全考虑

- 所有API端点需要API密钥验证
- 备份文件权限控制
- 文件路径验证防止目录遍历
- 操作日志记录便于审计

## 监控和维护

### 日志记录
- 详细的操作日志
- 错误追踪和调试信息
- 清理历史记录

### 存储监控
- 实时使用率显示
- 自动清理阈值警告
- 备份空间管理

## 未来扩展

- 支持更多文件格式
- 分布式存储集成
- 自动化清理调度
- 高级文件对比算法
- CDN集成支持

---

**版本**: 2.0.0  
**更新日期**: 2025-07-13  
**兼容性**: 向后兼容所有现有功能
