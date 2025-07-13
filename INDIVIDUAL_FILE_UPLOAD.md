# 逐个文件上传功能说明

## 功能概述

Omega更新服务器现在支持逐个文件上传到云端，而不是压缩包上传。这种方式可以保持文件的原始结构，支持增量上传和断点续传，提供更好的上传体验。

## 主要特性

### 1. 逐个文件上传
- 遍历文件夹中的所有文件
- 逐个上传到服务器，保持目录结构
- 支持任意深度的文件夹嵌套
- 实时显示上传进度

### 2. 断点续传支持
- 自动检测已上传的文件
- 通过SHA256哈希值验证文件完整性
- 跳过已存在且相同的文件
- 只上传新增或修改的文件

### 3. 详细进度跟踪
- 总体进度条显示
- 当前文件上传状态
- 实时统计：已上传、跳过、失败
- 详细日志记录每个文件的处理结果

### 4. 错误处理和恢复
- 单个文件失败不影响其他文件
- 网络中断后可重新上传
- 详细的错误信息和日志
- 支持用户取消操作

## 技术实现

### 服务器端新增API

#### 1. 单文件上传API
```
POST /api/v1/upload/file
```

**参数:**
- `file`: 文件内容
- `version`: 版本号
- `platform`: 平台 (windows/linux/macos)
- `arch`: 架构 (x64/x86/arm64)
- `relative_path`: 文件在文件夹中的相对路径
- `file_hash`: 文件SHA256哈希值（可选）
- `api_key`: API密钥

**响应:**
```json
{
    "success": true,
    "message": "文件上传成功",
    "file_path": "config/settings.json",
    "file_size": 1024,
    "sha256": "abc123...",
    "action": "uploaded"  // 或 "skipped"
}
```

#### 2. 文件列表API
```
GET /api/v1/files/list
```

**参数:**
- `version`: 版本号
- `platform`: 平台
- `arch`: 架构
- `api_key`: API密钥

**响应:**
```json
{
    "files": [
        {
            "relative_path": "app.exe",
            "file_name": "app.exe",
            "file_size": 1048576,
            "sha256": "def456...",
            "created_at": "2025-07-13T20:00:00",
            "updated_at": "2025-07-13T20:00:00"
        }
    ],
    "total_count": 10,
    "total_size": 10485760,
    "version": "2.0.0",
    "platform": "windows",
    "architecture": "x64"
}
```

### 数据库模型

#### SingleFile表
```sql
CREATE TABLE single_files (
    id INTEGER PRIMARY KEY,
    version_id INTEGER NOT NULL,
    relative_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (version_id) REFERENCES versions(id)
);
```

### 客户端实现

#### 上传流程
1. **文件夹分析**: 递归扫描所有文件
2. **哈希计算**: 为每个文件计算SHA256哈希
3. **逐个上传**: 按顺序上传每个文件
4. **进度更新**: 实时更新进度和统计
5. **错误处理**: 记录失败文件，继续处理其他文件

#### 核心代码片段
```python
def upload_files_thread():
    # 获取所有文件
    all_files = []
    for file_path in folder_path.rglob('*'):
        if file_path.is_file():
            relative_path = file_path.relative_to(folder_path)
            all_files.append((file_path, str(relative_path).replace('\\', '/')))
    
    # 逐个上传
    for file_path, relative_path in all_files:
        # 计算哈希
        file_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        
        # 上传文件
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{server_url}/api/v1/upload/file",
                files={'file': f},
                data={
                    'version': version,
                    'relative_path': relative_path,
                    'file_hash': file_hash.hexdigest(),
                    'api_key': api_key
                }
            )
```

## 用户界面

### 进度窗口
- **总体进度条**: 显示整体上传进度
- **当前文件**: 显示正在处理的文件名
- **统计信息**: 已上传、跳过、失败的文件数量
- **详细日志**: 每个文件的处理结果和时间戳
- **控制按钮**: 取消和关闭按钮

### 日志格式
```
[20:00:01] INFO: 开始上传 10 个文件到版本 2.0.0
[20:00:02] INFO: 上传: app.exe (1048576 字节)
[20:00:03] INFO: 跳过: config.ini (文件已存在)
[20:00:04] ERROR: 失败: data.db - 网络超时
[20:00:05] INFO: 上传完成! 总计: 10, 成功: 8, 跳过: 1, 失败: 1
```

## 优势对比

### 与压缩包上传对比

| 特性 | 压缩包上传 | 逐个文件上传 |
|------|------------|--------------|
| 文件结构 | 需要解压 | 直接保持 |
| 断点续传 | 不支持 | 完全支持 |
| 增量更新 | 需要重新上传整个包 | 只上传变更文件 |
| 存储效率 | 需要临时压缩文件 | 直接存储 |
| 上传进度 | 只有整体进度 | 文件级别进度 |
| 错误恢复 | 需要重新上传整个包 | 只需重传失败文件 |
| 网络要求 | 需要稳定长连接 | 容错性更好 |

### 性能优化

1. **并发控制**: 单线程上传避免服务器压力
2. **内存管理**: 分块读取大文件，避免内存溢出
3. **网络优化**: 每个文件独立连接，失败不影响其他文件
4. **存储优化**: 服务器端直接存储，无需临时文件

## 使用场景

### 适用场景
- 大型软件项目的版本发布
- 频繁更新的应用程序
- 需要增量更新的系统
- 网络不稳定的环境

### 典型工作流
1. 开发完成后，将构建输出放在文件夹中
2. 运行上传工具，选择输出文件夹
3. 填写版本信息，开始上传
4. 系统自动跳过未变更的文件
5. 只上传新增或修改的文件
6. 完成后可立即进行下一次增量更新

## 安全考虑

### 文件完整性
- SHA256哈希验证确保文件完整性
- 上传前后哈希对比检测传输错误
- 损坏文件自动删除并重新上传

### 访问控制
- API密钥验证所有请求
- 文件路径验证防止目录遍历攻击
- 上传大小限制防止资源耗尽

### 审计日志
- 详细记录每个文件的上传操作
- 包含时间戳、用户、文件路径等信息
- 便于问题追踪和安全审计

## 监控和维护

### 存储监控
- 实时显示存储使用情况
- 按版本统计文件数量和大小
- 自动清理策略管理存储空间

### 性能监控
- 上传速度统计
- 错误率监控
- 服务器资源使用情况

## 未来扩展

### 可能的改进
- 多线程并发上传
- 文件压缩传输
- 增量文件对比算法
- 云存储集成
- 分布式存储支持

---

**版本**: 3.0.0  
**更新日期**: 2025-07-13  
**测试状态**: 全部通过 ✅  
**兼容性**: 完全向后兼容
