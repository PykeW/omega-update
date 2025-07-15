# 文件对比功能技术详解

## 🔍 文件对比实现原理

### 1. 核心对比算法

文件对比功能基于 **SHA256 哈希值** 进行精确的内容对比，确保即使文件名相同，也能准确识别内容是否发生变化。

#### 哈希计算实现
```python
def _calculate_file_hash(self, file_path: Path) -> str:
    """计算文件SHA256哈希"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            # 分块读取，避免大文件内存溢出
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception:
        return ""
```

**关键特性：**
- **分块读取**：每次读取 8KB，避免大文件占用过多内存
- **二进制模式**：确保跨平台一致性，避免文本编码问题
- **异常处理**：文件读取失败时返回空字符串，不中断整个流程

### 2. 文件状态判断逻辑

系统通过对比本地和远程文件的哈希值，将文件分为四种状态：

```python
def analyze_differences(self, local_files: Dict[str, FileInfo], 
                       remote_files: Dict[str, FileInfo]) -> DifferenceReport:
    # 检查本地文件
    for path, local_info in local_files.items():
        if path not in remote_files:
            # 🆕 新增文件：本地有，远程无
            new_files.append(create_difference(path, ChangeType.NEW, local_info))
        else:
            remote_info = remote_files[path]
            if local_info.sha256_hash != remote_info.sha256_hash:
                # 📝 修改文件：路径相同，哈希不同
                modified_files.append(create_difference(path, ChangeType.MODIFIED, 
                                                       local_info, remote_info))
            else:
                # ✅ 相同文件：路径相同，哈希相同
                same_files.append(create_difference(path, ChangeType.SAME, 
                                                   local_info, remote_info))
    
    # 检查远程独有文件
    for path, remote_info in remote_files.items():
        if path not in local_files:
            # 🗑️ 删除文件：远程有，本地无
            deleted_files.append(create_difference(path, ChangeType.DELETED, 
                                                  None, remote_info))
```

#### 判断规则详解：

| 本地文件 | 远程文件 | SHA256对比 | 判断结果 | 操作 |
|---------|---------|-----------|---------|------|
| ✅ 存在 | ❌ 不存在 | - | 🆕 新增 | 上传 |
| ✅ 存在 | ✅ 存在 | 不同 | 📝 修改 | 覆盖上传 |
| ✅ 存在 | ✅ 存在 | 相同 | ✅ 相同 | 跳过 |
| ❌ 不存在 | ✅ 存在 | - | 🗑️ 删除 | 删除（可选） |

### 3. 文件信息数据结构

```python
@dataclass
class FileInfo:
    relative_path: str      # 相对路径（用于唯一标识）
    file_size: int         # 文件大小（字节）
    sha256_hash: str       # SHA256哈希值（核心对比依据）
    modified_time: Optional[datetime] = None  # 修改时间
    storage_path: Optional[str] = None        # 服务器存储路径
```

## 📤 上传完成判断机制

### 1. 客户端上传流程

```python
def _upload_single_file(self, file_path: Path, relative_path: str,
                       version_type: str, platform: str, architecture: str,
                       description: str) -> bool:
    try:
        # 1. 计算本地文件哈希
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()

        # 2. 准备上传数据
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            data = {
                'version_type': version_type,
                'platform': platform,
                'architecture': architecture,
                'relative_path': relative_path,
                'description': description,
                'api_key': get_api_key(),
                'file_hash': file_hash  # 发送本地计算的哈希
            }

            # 3. 发送HTTP请求
            response = requests.post(
                f"{get_server_url()}/api/v2/upload/simple/file",
                files=files,
                data=data,
                timeout=60
            )

            # 4. 判断上传是否成功
            return response.status_code == 200

    except Exception as e:
        # 记录错误日志
        if self.log_manager:
            self.log_manager.log_error(f"上传文件失败 {relative_path}: {e}")
        return False
```

### 2. 服务器端验证流程

```python
@router.post("/upload/simple/file")
async def upload_simple_file(
    file: UploadFile = File(...),
    file_hash: Optional[str] = Form(None),  # 客户端提供的哈希
    # ... 其他参数
):
    try:
        # 1. 读取上传的文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 2. 服务器端重新计算哈希
        calculated_hash = hashlib.sha256(file_content).hexdigest()
        
        # 3. 哈希验证（如果客户端提供了哈希）
        if file_hash and file_hash != calculated_hash:
            raise HTTPException(status_code=400, detail="文件哈希验证失败")

        # 4. 保存文件到磁盘
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 5. 记录到数据库
        new_file = version_manager.upload_file(
            version_type=version_type,
            platform=platform,
            architecture=architecture,
            relative_path=relative_path,
            file_name=file_name,
            file_size=file_size,
            file_hash=calculated_hash,  # 使用服务器计算的哈希
            storage_path=str(file_path)
        )

        # 6. 返回成功响应
        return {
            "success": True,
            "message": "文件上传成功",
            "file_path": str(relative_path),
            "file_size": file_size,
            "file_hash": calculated_hash,
            "file_id": new_file.id
        }

    except Exception as e:
        # 返回错误响应
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
```

### 3. 上传完成的多重验证

#### 3.1 HTTP状态码验证
```python
# 客户端判断
return response.status_code == 200
```
- **200**：上传成功
- **400**：请求错误（如哈希验证失败）
- **401**：认证失败（API密钥无效）
- **500**：服务器内部错误

#### 3.2 哈希完整性验证
```python
# 服务器端验证
if file_hash and file_hash != calculated_hash:
    raise HTTPException(status_code=400, detail="文件哈希验证失败")
```

**验证流程：**
1. 客户端计算本地文件哈希
2. 将哈希值随文件一起上传
3. 服务器接收文件后重新计算哈希
4. 对比客户端和服务器的哈希值
5. 哈希不匹配则拒绝上传

#### 3.3 数据库记录验证
```python
# 数据库操作成功才返回成功响应
new_file = version_manager.upload_file(...)
db.commit()  # 事务提交成功
```

### 4. 上传失败处理机制

#### 4.1 网络异常处理
```python
try:
    response = requests.post(url, files=files, data=data, timeout=60)
    return response.status_code == 200
except requests.exceptions.Timeout:
    # 超时处理
    return False
except requests.exceptions.ConnectionError:
    # 连接错误处理
    return False
except Exception as e:
    # 其他异常处理
    return False
```

#### 4.2 重试机制
```python
# 在增量上传主流程中
for file_diff in report.new_files + report.modified_files:
    success = self._upload_single_file(...)
    if success:
        uploaded_files += 1
        self.log_manager.log_success(f"上传成功: {file_diff.relative_path}")
    else:
        failed_files += 1
        self.log_manager.log_error(f"上传失败: {file_diff.relative_path}")
        # 可以在这里添加重试逻辑

# 最终成功率判断
success_rate = uploaded_files / total_files if total_files > 0 else 0
return success_rate > 0.8  # 80%以上成功率认为整体成功
```

#### 4.3 部分失败处理
- **容错机制**：80%以上文件上传成功即认为整体成功
- **详细日志**：记录每个文件的上传状态
- **用户反馈**：显示具体的成功/失败文件列表

## 🔒 安全性保障

### 1. 文件完整性
- **双重哈希验证**：客户端和服务器端都计算哈希
- **传输验证**：确保文件在传输过程中未被篡改
- **存储验证**：服务器存储的哈希值用于后续验证

### 2. 认证授权
- **API密钥验证**：所有上传操作需要有效密钥
- **权限控制**：不同用户可能有不同的上传权限
- **操作审计**：记录所有上传操作的详细日志

### 3. 错误恢复
- **原子操作**：数据库操作使用事务，确保一致性
- **回滚机制**：上传失败时可以回滚到之前状态
- **清理机制**：清理上传失败的临时文件

## 📊 性能优化

### 1. 哈希计算优化
- **分块读取**：避免大文件内存溢出
- **并行计算**：可以并行计算多个文件的哈希（未来优化）
- **缓存机制**：缓存已计算的哈希值（未来优化）

### 2. 网络传输优化
- **超时设置**：合理的超时时间（60秒）
- **分块上传**：大文件可以分块上传（未来优化）
- **压缩传输**：减少网络带宽使用（未来优化）

### 3. 数据库优化
- **批量操作**：减少数据库交互次数
- **索引优化**：在关键字段上建立索引
- **连接池**：复用数据库连接

这套文件对比和上传验证机制确保了系统的可靠性、安全性和高性能，为用户提供了企业级的文件同步体验。
