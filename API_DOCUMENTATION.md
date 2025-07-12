# Omega更新服务器 - API文档

本文档详细描述了Omega更新服务器增强版的所有API接口。

## 📋 基本信息

- **Base URL**: `http://your-server-ip` 或 `https://update.yourdomain.com`
- **API版本**: v1
- **认证方式**: API Key
- **数据格式**: JSON / multipart/form-data

## 🔐 认证

所有需要认证的API都需要在请求中包含API密钥：

```http
# 表单数据中包含
api_key: your-api-key-here

# 或在Header中包含
Authorization: Bearer your-api-key-here
```

## 📊 响应格式

### 成功响应
```json
{
  "message": "操作成功",
  "data": { ... },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 错误响应
```json
{
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔌 API接口

### 1. 系统信息

#### 1.1 健康检查
```http
GET /health
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "2.0.0"
}
```

#### 1.2 服务信息
```http
GET /
```

**响应示例:**
```json
{
  "message": "Omega更新服务器 - 增强版",
  "version": "2.0.0",
  "status": "running",
  "features": ["完整包", "增量包", "智能存储管理"],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. 更新包管理

#### 2.1 上传更新包
```http
POST /api/v1/upload/package
Content-Type: multipart/form-data
```

**请求参数:**
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| version | string | ✅ | 版本号 (如: 2.2.5) |
| package_type | string | ✅ | 包类型: full/patch/hotfix |
| description | string | ❌ | 版本描述 |
| is_stable | boolean | ❌ | 是否稳定版本 (默认: true) |
| is_critical | boolean | ❌ | 是否关键更新 (默认: false) |
| platform | string | ❌ | 平台: windows/linux/macos (默认: windows) |
| arch | string | ❌ | 架构: x64/x86/arm64 (默认: x64) |
| from_version | string | ❌ | 源版本 (仅增量包需要) |
| file | file | ✅ | 更新包文件 |
| api_key | string | ✅ | API密钥 |

**响应示例:**
```json
{
  "message": "包上传成功",
  "package_id": 123,
  "version": "2.2.5",
  "package_type": "full",
  "file_size": 8589934592,
  "sha256": "abc123...",
  "download_url": "/downloads/full/2.2.5/omega-v2.2.5-full-windows-x64.zip"
}
```

**错误码:**
- `401`: API密钥无效
- `400`: 参数错误或文件类型不支持
- `507`: 存储空间不足
- `500`: 服务器内部错误

#### 2.2 获取包列表
```http
GET /api/v1/packages
```

**查询参数:**
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| package_type | string | ❌ | 过滤包类型: full/patch/hotfix |
| platform | string | ❌ | 过滤平台 (默认: windows) |
| arch | string | ❌ | 过滤架构 (默认: x64) |
| limit | integer | ❌ | 返回数量限制 (默认: 20) |

**响应示例:**
```json
[
  {
    "id": 123,
    "version": "2.2.5",
    "package_type": "full",
    "package_name": "omega-v2.2.5-full-windows-x64.zip",
    "package_size": 8589934592,
    "from_version": null,
    "download_url": "/downloads/full/2.2.5/omega-v2.2.5-full-windows-x64.zip",
    "created_at": "2024-01-01T12:00:00Z",
    "download_count": 150
  },
  {
    "id": 124,
    "version": "2.2.6",
    "package_type": "patch",
    "package_name": "omega-v2.2.5-to-v2.2.6-patch-windows-x64.zip",
    "package_size": 52428800,
    "from_version": "2.2.5",
    "download_url": "/downloads/patches/2.2.6/omega-v2.2.5-to-v2.2.6-patch-windows-x64.zip",
    "created_at": "2024-01-02T10:30:00Z",
    "download_count": 89
  }
]
```

### 3. 版本管理

#### 3.1 版本检查
```http
GET /api/v1/version/check
```

**查询参数:**
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| current_version | string | ✅ | 当前版本号 |
| platform | string | ❌ | 平台 (默认: windows) |
| arch | string | ❌ | 架构 (默认: x64) |

**响应示例 (有更新):**
```json
{
  "has_update": true,
  "current_version": "2.2.5",
  "latest_version": "2.2.6",
  "update_info": {
    "version": "2.2.6",
    "description": "修复了若干bug，提升了性能",
    "release_date": "2024-01-02T10:30:00Z",
    "is_critical": false,
    "update_options": [
      {
        "type": "patch",
        "package_id": 124,
        "file_size": 52428800,
        "download_url": "/downloads/patches/2.2.6/omega-v2.2.5-to-v2.2.6-patch-windows-x64.zip",
        "recommended": true
      },
      {
        "type": "full",
        "package_id": 125,
        "file_size": 8589934592,
        "download_url": "/downloads/full/2.2.6/omega-v2.2.6-full-windows-x64.zip",
        "recommended": false
      }
    ]
  }
}
```

**响应示例 (无更新):**
```json
{
  "has_update": false,
  "current_version": "2.2.6",
  "latest_version": "2.2.6"
}
```

### 4. 存储管理

#### 4.1 存储统计
```http
GET /api/v1/storage/stats
```

**响应示例:**
```json
{
  "status": "healthy",
  "usage_percentage": 67.5,
  "recommendations": ["监控存储使用情况"],
  "stats": {
    "total_size": 42949672960,
    "used_size": 29024092160,
    "available_size": 13925580800,
    "usage_percentage": 67.5,
    "updates_total_size": 25769803776,
    "full_packages_size": 20401094656,
    "patch_packages_size": 4294967296,
    "hotfix_packages_size": 1073741824,
    "temp_size": 0,
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "thresholds": {
    "warning": 80.0,
    "cleanup": 85.0,
    "critical": 90.0
  }
}
```

#### 4.2 手动清理存储
```http
POST /api/v1/storage/cleanup
Content-Type: multipart/form-data
```

**请求参数:**
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| api_key | string | ✅ | API密钥 |

**响应示例:**
```json
{
  "success": true,
  "space_freed": 5368709120,
  "packages_deleted": 15,
  "before_usage": 89.2,
  "after_usage": 76.8,
  "deleted_packages": [
    {
      "id": 100,
      "type": "hotfix",
      "version": "2.1.0",
      "size": 104857600
    }
  ]
}
```

### 5. 文件下载

#### 5.1 下载更新包
```http
GET /downloads/{package_type}/{version}/{filename}
```

**路径参数:**
- `package_type`: full/patches/hotfixes
- `version`: 版本号
- `filename`: 文件名

**示例:**
```http
GET /downloads/full/2.2.5/omega-v2.2.5-full-windows-x64.zip
```

**响应:** 文件流下载

## 📝 使用示例

### Python示例

```python
import requests

# 配置
SERVER_URL = "http://your-server-ip"
API_KEY = "your-api-key"

# 检查版本更新
def check_update(current_version):
    response = requests.get(
        f"{SERVER_URL}/api/v1/version/check",
        params={
            "current_version": current_version,
            "platform": "windows",
            "arch": "x64"
        }
    )
    return response.json()

# 上传更新包
def upload_package(file_path, version, package_type):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'version': version,
            'package_type': package_type,
            'description': f'{package_type} package for version {version}',
            'is_stable': 'true',
            'platform': 'windows',
            'arch': 'x64',
            'api_key': API_KEY
        }
        
        response = requests.post(
            f"{SERVER_URL}/api/v1/upload/package",
            files=files,
            data=data
        )
    return response.json()

# 获取存储统计
def get_storage_stats():
    response = requests.get(f"{SERVER_URL}/api/v1/storage/stats")
    return response.json()
```

### PowerShell示例

```powershell
# 配置
$ServerURL = "http://your-server-ip"
$ApiKey = "your-api-key"

# 检查版本更新
function Check-Update {
    param($CurrentVersion)
    
    $response = Invoke-RestMethod -Uri "$ServerURL/api/v1/version/check" -Method Get -Body @{
        current_version = $CurrentVersion
        platform = "windows"
        arch = "x64"
    }
    return $response
}

# 上传更新包
function Upload-Package {
    param($FilePath, $Version, $PackageType)
    
    $response = Invoke-RestMethod -Uri "$ServerURL/api/v1/upload/package" -Method Post -Form @{
        version = $Version
        package_type = $PackageType
        description = "$PackageType package for version $Version"
        is_stable = "true"
        platform = "windows"
        arch = "x64"
        api_key = $ApiKey
        file = Get-Item $FilePath
    }
    return $response
}
```

### cURL示例

```bash
# 检查版本更新
curl -X GET "http://your-server-ip/api/v1/version/check?current_version=2.2.5&platform=windows&arch=x64"

# 上传更新包
curl -X POST "http://your-server-ip/api/v1/upload/package" \
  -F "version=2.2.6" \
  -F "package_type=patch" \
  -F "description=Bug fixes and improvements" \
  -F "is_stable=true" \
  -F "platform=windows" \
  -F "arch=x64" \
  -F "from_version=2.2.5" \
  -F "api_key=your-api-key" \
  -F "file=@update-package.zip"

# 获取存储统计
curl -X GET "http://your-server-ip/api/v1/storage/stats"

# 手动清理存储
curl -X POST "http://your-server-ip/api/v1/storage/cleanup" \
  -F "api_key=your-api-key"
```

## 🚨 错误处理

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 认证失败 |
| 404 | 资源不存在 |
| 507 | 存储空间不足 |
| 500 | 服务器内部错误 |

### 常见错误

**1. API密钥错误**
```json
{
  "detail": "无效的API密钥",
  "error_code": "INVALID_API_KEY"
}
```

**2. 文件类型不支持**
```json
{
  "detail": "不支持的文件类型: .txt",
  "error_code": "UNSUPPORTED_FILE_TYPE"
}
```

**3. 存储空间不足**
```json
{
  "detail": "存储空间不足，清理失败",
  "error_code": "INSUFFICIENT_STORAGE"
}
```

## 📈 速率限制

- **上传接口**: 每小时最多10次上传
- **查询接口**: 每分钟最多100次请求
- **下载接口**: 无限制

## 🔄 API版本控制

当前API版本为v1，未来版本更新时会保持向后兼容。新版本将通过URL路径区分：

- v1: `/api/v1/...`
- v2: `/api/v2/...` (未来)

---

更多信息请参考 [README.md](README.md) 和 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)。
