# 下载更新系统架构设计

## 系统概述

基于现有的逐个文件上传系统，设计并实现一个完整的嵌入式下载更新程序，提供智能的文件差异检测和最小化下载功能。

## 核心架构

### 1. 服务器端扩展

#### 新增API端点
```
GET /api/v1/version/{version}/files
- 功能：获取指定版本的所有文件列表及哈希值
- 参数：version, platform, arch, api_key
- 返回：文件列表，包含路径、大小、哈希值、修改时间

GET /api/v1/download/file
- 功能：下载单个文件
- 参数：version, platform, arch, relative_path, api_key
- 返回：文件内容流

GET /api/v1/version/compare
- 功能：版本比较和差异分析
- 参数：local_files (JSON), target_version, platform, arch, api_key
- 返回：差异分析结果
```

#### 数据库复用
- 复用现有的 `SingleFile` 表
- 利用现有的文件存储结构
- 保持与上传系统的完全兼容

### 2. 客户端核心组件

#### LocalFileScanner (本地文件扫描器)
```python
class LocalFileScanner:
    def scan_directory(self, path: str) -> Dict[str, FileInfo]
    def calculate_file_hash(self, file_path: str) -> str
    def get_file_info(self, file_path: str) -> FileInfo
```

#### DifferenceDetector (差异检测器)
```python
class DifferenceDetector:
    def compare_versions(self, local_files: Dict, remote_files: Dict) -> UpdatePlan
    def categorize_differences(self) -> Tuple[List, List, List]  # new, updated, deleted
```

#### DownloadManager (下载管理器)
```python
class DownloadManager:
    def download_file(self, file_info: FileInfo, target_path: str) -> bool
    def download_batch(self, file_list: List[FileInfo]) -> None
    def resume_download(self, file_path: str) -> bool
```

#### ProgressTracker (进度跟踪器)
```python
class ProgressTracker:
    def update_file_progress(self, file_path: str, bytes_downloaded: int)
    def update_overall_progress(self)
    def calculate_speed_and_eta(self) -> Tuple[float, int]
```

### 3. 数据结构设计

#### FileInfo
```python
@dataclass
class FileInfo:
    relative_path: str
    size: int
    sha256_hash: str
    last_modified: datetime
    download_url: str = None
```

#### UpdatePlan
```python
@dataclass
class UpdatePlan:
    files_to_download: List[FileInfo]
    files_to_delete: List[str]
    total_download_size: int
    total_file_count: int
    estimated_time: int
```

#### DownloadProgress
```python
@dataclass
class DownloadProgress:
    current_file: str
    current_file_progress: float
    overall_progress: float
    download_speed: float  # bytes/sec
    eta_seconds: int
    files_completed: int
    files_total: int
```

## 工作流程设计

### 1. 版本检查流程
```
用户输入目标版本 → 扫描本地文件夹 → 获取远程版本信息 → 计算差异 → 显示更新计划
```

### 2. 文件差异分析
```python
def analyze_differences(local_files, remote_files):
    new_files = []      # 远程有，本地无
    updated_files = []  # 两边都有，但哈希不同
    deleted_files = []  # 本地有，远程无
    same_files = []     # 哈希匹配，跳过
    
    for path, remote_info in remote_files.items():
        if path not in local_files:
            new_files.append(remote_info)
        elif local_files[path].sha256_hash != remote_info.sha256_hash:
            updated_files.append(remote_info)
        else:
            same_files.append(remote_info)
    
    for path, local_info in local_files.items():
        if path not in remote_files:
            deleted_files.append(path)
    
    return UpdatePlan(
        files_to_download=new_files + updated_files,
        files_to_delete=deleted_files,
        total_download_size=sum(f.size for f in new_files + updated_files),
        total_file_count=len(new_files + updated_files)
    )
```

### 3. 下载执行流程
```
用户确认更新计划 → 创建下载任务 → 并行下载文件 → 实时更新进度 → 验证文件完整性 → 完成更新
```

## GUI集成设计

### 1. 新增标签页
在现有GUI中添加"检查更新"标签页，包含：
- 本地文件夹选择
- 目标版本输入
- 平台和架构选择
- 检查更新按钮

### 2. 更新预览界面
显示差异分析结果：
- 文件变更列表（树形结构）
- 下载大小统计
- 预估下载时间
- 选择性下载选项

### 3. 下载进度界面
复用现有的进度显示组件：
- 总体进度条
- 当前文件进度
- 下载速度和ETA
- 详细日志显示
- 暂停/继续/取消按钮

## 技术特性

### 1. 最小化下载策略
- 基于SHA256哈希的精确差异检测
- 只下载变化的文件
- 智能跳过相同文件
- 支持增量更新

### 2. 断点续传机制
- 记录下载进度
- 网络中断后自动恢复
- 文件级别的续传支持
- 完整性验证

### 3. 性能优化
- 多线程并行下载
- 连接池复用
- 内存优化管理
- 智能重试机制

### 4. 错误处理
- 网络错误自动重试
- 文件权限检查
- 磁盘空间预检查
- 详细错误日志

### 5. 安全机制
- API密钥验证
- 文件路径安全检查
- 下载内容完整性验证
- 防止路径遍历攻击

## 实现计划

### 阶段1：服务器端API扩展
- 实现版本文件列表查询API
- 实现文件下载API
- 实现版本比较API

### 阶段2：客户端核心组件
- 实现本地文件扫描器
- 实现差异检测器
- 实现基础下载管理器

### 阶段3：GUI集成
- 添加检查更新界面
- 集成下载进度显示
- 实现用户交互逻辑

### 阶段4：高级功能
- 实现选择性下载
- 完善断点续传
- 添加性能优化

### 阶段5：测试验证
- 功能测试
- 性能测试
- 用户体验测试

## 兼容性保证

- 完全向后兼容现有上传功能
- 不影响现有API端点
- 数据库结构保持兼容
- 配置文件格式不变

## 预期效果

- 🔄 **智能更新检查** - 精确识别文件差异
- ⚡ **最小化下载** - 只下载变化的文件
- 📊 **详细进度跟踪** - 实时显示下载状态
- 🛡️ **断点续传** - 网络中断后可恢复
- 🎯 **选择性下载** - 用户可选择下载内容
- 🔧 **无缝集成** - 与现有系统完美融合
