#!/usr/bin/env python3
"""
增强版Omega更新服务器主程序
支持完整包、增量包和存储管理
"""

import sys
import logging
import hashlib
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from server.server_config import ServerConfig
from server.enhanced_database import (
    init_database, get_db, Version, Package,
    PackageType, PackageStatus, SingleFile
)
from server.storage_manager import storage_manager
from server.simplified_api import router as simplified_router
from sqlalchemy.orm import Session

# 初始化配置
config = ServerConfig()
config.ensure_directories()

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_DIR / "server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Omega更新服务器启动中...")
    init_database()
    logger.info("数据库初始化完成")
    yield
    # 关闭时执行（如果需要）

# 初始化FastAPI应用
app = FastAPI(
    title="Omega更新服务器 - 增强版",
    description="支持完整包、增量包和智能存储管理的更新系统",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }

# 添加简化API路由
app.include_router(simplified_router)

# 配置静态文件服务
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.mount("/downloads", StaticFiles(directory=str(config.UPLOAD_DIR)), name="downloads")



@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Omega更新服务器 - 增强版",
        "version": "2.0.0",
        "status": "running",
        "features": ["完整包", "增量包", "智能存储管理"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health")
async def api_health_check():
    """API健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.post("/api/v1/upload/package")
async def upload_package(
    version: str = Form(...),
    package_type: str = Form(...),  # full, patch, hotfix
    description: str = Form(""),
    is_stable: bool = Form(True),
    is_critical: bool = Form(False),
    platform: str = Form("windows"),
    arch: str = Form("x64"),
    from_version: Optional[str] = Form(None),  # 仅增量包需要
    file: UploadFile = File(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传更新包（支持完整包、增量包、热修复包）"""

    logger.info(f"收到上传请求: version={version}, type={package_type}, platform={platform}, arch={arch}")

    # 验证API密钥
    if api_key != config.API_KEY:
        logger.warning(f"API密钥验证失败: 收到={api_key}, 期望={config.API_KEY}")
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 验证包类型
        try:
            pkg_type = PackageType(package_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的包类型: {package_type}")

        # 验证增量包参数
        if pkg_type == PackageType.PATCH and not from_version:
            raise HTTPException(status_code=400, detail="增量包必须指定源版本")

        # 检查存储空间
        storage_health = storage_manager.check_storage_health(db)
        if storage_health["status"] == "critical":
            # 尝试自动清理
            cleanup_result = storage_manager.execute_cleanup(db, "emergency")
            if not cleanup_result["success"]:
                raise HTTPException(status_code=507, detail="存储空间不足，清理失败")

        # 检查文件扩展名
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 计算文件哈希
        sha256_hash = hashlib.sha256(content).hexdigest()

        # 确定存储路径
        storage_subdir = {
            PackageType.FULL: "full",
            PackageType.PATCH: "patches", 
            PackageType.HOTFIX: "hotfixes"
        }[pkg_type]
        
        # 创建版本目录
        version_dir = config.UPLOAD_DIR / storage_subdir / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        if pkg_type == PackageType.PATCH:
            filename = f"omega-v{from_version}-to-v{version}-patch-{platform}-{arch}{file_ext}"
        elif pkg_type == PackageType.HOTFIX:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"omega-v{version}-hotfix-{timestamp}-{platform}-{arch}{file_ext}"
        else:  # FULL
            filename = f"omega-v{version}-full-{platform}-{arch}{file_ext}"

        # 保存文件
        file_path = version_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)

        # 查找或创建版本记录
        db_version = db.query(Version).filter(
            Version.version == version,
            Version.platform == platform,
            Version.architecture == arch
        ).first()

        if not db_version:
            db_version = Version(
                version=version,
                description=description,
                is_stable=is_stable,
                is_critical=is_critical,
                platform=platform,
                architecture=arch
            )
            db.add(db_version)
            db.commit()
            db.refresh(db_version)

        # 创建包记录
        db_package = Package(
            version_id=db_version.id,
            package_type=pkg_type,
            package_name=filename,
            package_size=file_size,
            sha256_hash=sha256_hash,
            storage_path=str(file_path),
            download_url=f"/downloads/{storage_subdir}/{version}/{filename}",
            from_version=from_version,
            status=PackageStatus.AVAILABLE
        )

        db.add(db_package)
        db.commit()
        db.refresh(db_package)

        # 更新版本统计
        if pkg_type == PackageType.FULL:
            db_version.total_size = int(file_size)  # type: ignore
            db_version.file_count = 1  # type: ignore
            db.commit()

        # 记录存储统计
        storage_manager.record_storage_stats(db)

        logger.info(f"包上传成功: {pkg_type.value} - {version} - {file_size} bytes")
        
        return {
            "message": "包上传成功",
            "package_id": db_package.id,
            "version": version,
            "package_type": pkg_type.value,
            "file_size": file_size,
            "sha256": sha256_hash,
            "download_url": db_package.download_url
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"包上传失败: {e}")
        logger.error(f"详细错误信息: {error_details}")
        raise HTTPException(status_code=500, detail=f"包上传失败: {str(e)}")

@app.get("/api/v1/version/check")
async def check_version(
    current_version: str,
    platform: str = "windows",
    arch: str = "x64",
    db: Session = Depends(get_db)
):
    """检查版本更新"""
    try:
        # 查找最新稳定版本
        latest_version = db.query(Version).filter(
            Version.platform == platform,
            Version.architecture == arch,
            Version.is_stable == True
        ).order_by(Version.release_date.desc()).first()

        if not latest_version:
            raise HTTPException(status_code=404, detail="没有找到可用版本")

        has_update = current_version != latest_version.version

        response = {
            "has_update": has_update,
            "current_version": current_version,
            "latest_version": latest_version.version
        }

        if has_update:
            # 查找完整包
            full_package = db.query(Package).filter(
                Package.version_id == latest_version.id,
                Package.package_type == PackageType.FULL,
                Package.status == PackageStatus.AVAILABLE
            ).first()

            # 查找增量包
            patch_package = db.query(Package).filter(
                Package.from_version == current_version,
                Package.version_id == latest_version.id,
                Package.package_type == PackageType.PATCH,
                Package.status == PackageStatus.AVAILABLE
            ).first()

            update_options = []
            
            if patch_package:
                update_options.append({
                    "type": "patch",
                    "package_id": patch_package.id,
                    "file_size": patch_package.package_size,
                    "download_url": patch_package.download_url,
                    "recommended": True
                })

            if full_package:
                update_options.append({
                    "type": "full",
                    "package_id": full_package.id,
                    "file_size": full_package.package_size,
                    "download_url": full_package.download_url,
                    "recommended": not bool(patch_package)
                })

            response["update_info"] = {
                "version": latest_version.version,
                "description": latest_version.description or "",
                "release_date": latest_version.release_date.isoformat(),
                "is_critical": latest_version.is_critical,
                "update_options": update_options
            }

        logger.info(f"版本检查: {current_version} -> {latest_version.version}, 有更新: {has_update}")
        return response

    except Exception as e:
        logger.error(f"版本检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本检查失败: {str(e)}")

@app.get("/api/v1/storage/stats")
async def get_storage_stats(db: Session = Depends(get_db)):
    """获取存储统计信息"""
    try:
        health = storage_manager.check_storage_health(db)
        return health
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")

@app.post("/api/v1/storage/cleanup")
async def manual_cleanup(
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """手动执行存储清理"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")
    
    try:
        result = storage_manager.execute_cleanup(db, "manual")
        return result
    except Exception as e:
        logger.error(f"手动清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"手动清理失败: {str(e)}")

@app.get("/api/v1/packages")
async def list_packages(
    package_type: Optional[str] = None,
    platform: str = "windows",
    arch: str = "x64",
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取包列表"""
    try:
        query = db.query(Package).join(Version).filter(
            Version.platform == platform,
            Version.architecture == arch,
            Package.status == PackageStatus.AVAILABLE
        )
        
        if package_type:
            try:
                pkg_type = PackageType(package_type.lower())
                query = query.filter(Package.package_type == pkg_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"不支持的包类型: {package_type}")
        
        packages = query.order_by(Package.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": p.id,
                "version": p.version.version,
                "package_type": p.package_type.value,
                "package_name": p.package_name,
                "package_size": p.package_size,
                "from_version": p.from_version,
                "download_url": p.download_url,
                "created_at": p.created_at.isoformat(),
                "download_count": p.download_count
            }
            for p in packages
        ]
    except Exception as e:
        logger.error(f"获取包列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取包列表失败: {str(e)}")

@app.get("/api/v1/storage/structure")
async def get_storage_structure(
    api_key: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取存储目录结构和版本文件信息"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        structure = storage_manager.get_storage_structure(db)
        return structure
    except Exception as e:
        logger.error(f"获取存储结构失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取存储结构失败: {str(e)}")

@app.post("/api/v1/storage/retention/apply")
async def apply_retention_policy(
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """应用版本保留策略"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        result = storage_manager.apply_version_retention_policy(db)
        return result
    except Exception as e:
        logger.error(f"应用版本保留策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"应用版本保留策略失败: {str(e)}")

@app.post("/api/v1/storage/retention/configure")
async def configure_retention_policy(
    package_type: str = Form(...),  # full, patch, hotfix
    max_versions: int = Form(...),
    api_key: str = Form(...)
):
    """配置版本保留策略"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 验证包类型
        pkg_type = PackageType(package_type.lower())
        result = storage_manager.configure_retention_policy(pkg_type, max_versions)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的包类型: {package_type}")
    except Exception as e:
        logger.error(f"配置版本保留策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置版本保留策略失败: {str(e)}")

@app.get("/api/v1/version/changes")
async def get_version_changes(
    version: str = Query(...),
    platform: str = Query("windows"),
    arch: str = Query("x64"),
    api_key: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取版本文件变化信息"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        changes = storage_manager.get_file_changes(db, version, platform, arch)
        return changes
    except Exception as e:
        logger.error(f"获取版本变化信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本变化信息失败: {str(e)}")

@app.post("/api/v1/file/verify")
async def verify_file_integrity(
    file_path: str = Form(...),
    expected_hash: str = Form(...),
    api_key: str = Form(...)
):
    """验证文件完整性"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        from pathlib import Path
        result = storage_manager.verify_file_integrity(Path(file_path), expected_hash)
        return result
    except Exception as e:
        logger.error(f"文件完整性验证失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件完整性验证失败: {str(e)}")

@app.post("/api/v1/version/rollback")
async def rollback_version(
    package_id: int = Form(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """回滚到备份版本"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        result = storage_manager.rollback_version(db, package_id)
        return result
    except Exception as e:
        logger.error(f"版本回滚失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本回滚失败: {str(e)}")

@app.post("/api/v1/upload/file")
async def upload_single_file(
    file: UploadFile = File(...),
    version: str = Form(...),
    platform: str = Form("windows"),
    arch: str = Form("x64"),
    relative_path: str = Form(...),  # 文件在文件夹中的相对路径
    file_hash: str = Form(None),     # 文件SHA256哈希值
    conflict_action: str = Form("skip"),  # 冲突处理: skip, overwrite, ask
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传单个文件到指定版本目录"""

    logger.info(f"收到单文件上传请求: version={version}, platform={platform}, arch={arch}, path={relative_path}")

    # 验证API密钥
    if api_key != config.API_KEY:
        logger.warning(f"API密钥验证失败: 收到={api_key}, 期望={config.API_KEY}")
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 检查或创建版本记录
        version_record = db.query(Version).filter(
            Version.version == version,
            Version.platform == platform,
            Version.architecture == arch
        ).first()

        if not version_record:
            # 创建新版本记录
            version_record = Version(
                version=version,
                platform=platform,
                architecture=arch,
                description=f"文件夹上传版本 {version}",
                is_stable=True,
                is_critical=False
            )
            db.add(version_record)
            db.commit()
            db.refresh(version_record)
            logger.info(f"创建新版本记录: {version}-{platform}-{arch}")

        # 构建存储路径
        storage_path = storage_manager.full_path / version / platform / arch / relative_path
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查文件是否已存在
        if storage_path.exists():
            existing_hash = storage_manager._calculate_file_hash(storage_path)

            # 如果提供了哈希值，检查文件是否相同
            if file_hash and existing_hash == file_hash:
                logger.info(f"文件已存在且哈希匹配，跳过: {relative_path}")
                return {
                    "success": True,
                    "message": "文件已存在且内容相同，跳过上传",
                    "file_path": relative_path,
                    "existing_hash": existing_hash,
                    "action": "skipped"
                }

            # 处理文件冲突
            if conflict_action == "skip":
                logger.info(f"文件已存在，根据策略跳过: {relative_path}")
                return {
                    "success": True,
                    "message": "文件已存在，根据策略跳过",
                    "file_path": relative_path,
                    "existing_hash": existing_hash,
                    "action": "skipped"
                }
            elif conflict_action == "ask":
                # 返回冲突信息，让客户端决定
                return {
                    "success": False,
                    "message": "文件冲突需要用户决定",
                    "file_path": relative_path,
                    "existing_hash": existing_hash,
                    "new_hash": file_hash,
                    "action": "conflict",
                    "conflict_info": {
                        "existing_size": storage_path.stat().st_size,
                        "existing_modified": storage_path.stat().st_mtime
                    }
                }
            # conflict_action == "overwrite" 时继续执行，覆盖文件

        # 保存文件
        file_content = await file.read()

        # 如果之前读取过文件（冲突检查），需要重新读取
        if file.file.tell() > 0:
            await file.seek(0)
            file_content = await file.read()

        with open(storage_path, "wb") as f:
            f.write(file_content)

        # 计算文件哈希
        actual_hash = storage_manager._calculate_file_hash(storage_path)

        # 验证哈希（如果提供）
        if file_hash and actual_hash != file_hash:
            storage_path.unlink()  # 删除损坏的文件
            raise HTTPException(status_code=400, detail="文件哈希验证失败")

        # 检查是否已有此文件的记录
        existing_file = db.query(SingleFile).filter(
            SingleFile.version_id == version_record.id,
            SingleFile.relative_path == relative_path
        ).first()

        if existing_file:
            # 更新现有记录
            setattr(existing_file, 'file_size', len(file_content))
            setattr(existing_file, 'sha256_hash', actual_hash)
            setattr(existing_file, 'storage_path', str(storage_path))
            # updated_at 会由 SQLAlchemy 自动更新（onupdate=func.now()）
            logger.info(f"更新文件记录: {relative_path}")
        else:
            # 创建新文件记录
            file_record = SingleFile(
                version_id=version_record.id,
                relative_path=relative_path,
                file_name=Path(relative_path).name,
                file_size=len(file_content),
                sha256_hash=actual_hash,
                storage_path=str(storage_path)
            )
            db.add(file_record)
            logger.info(f"创建新文件记录: {relative_path}")

        db.commit()

        logger.info(f"单文件上传成功: {relative_path} ({len(file_content)} 字节)")

        return {
            "success": True,
            "message": "文件上传成功",
            "file_path": relative_path,
            "file_size": len(file_content),
            "sha256": actual_hash,
            "action": "uploaded"
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"单文件上传失败: {e}")
        logger.error(f"详细错误信息: {error_details}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.get("/api/v1/files/list")
async def list_version_files(
    version: str = Query(...),
    platform: str = Query("windows"),
    arch: str = Query("x64"),
    api_key: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取指定版本的文件列表"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 查找版本记录
        version_record = db.query(Version).filter(
            Version.version == version,
            Version.platform == platform,
            Version.architecture == arch
        ).first()

        if not version_record:
            return {"files": [], "total_count": 0, "total_size": 0}

        # 获取文件列表
        files = db.query(SingleFile).filter(
            SingleFile.version_id == version_record.id
        ).all()

        file_list = []
        total_size = 0

        for file_record in files:
            file_info = {
                "relative_path": file_record.relative_path,
                "file_name": file_record.file_name,
                "file_size": file_record.file_size,
                "sha256": file_record.sha256_hash,
                "created_at": file_record.created_at.isoformat() if getattr(file_record, 'created_at', None) else None,
                "updated_at": file_record.updated_at.isoformat() if getattr(file_record, 'updated_at', None) else None
            }
            file_list.append(file_info)
            total_size += file_record.file_size

        return {
            "files": file_list,
            "total_count": len(file_list),
            "total_size": total_size,
            "version": version,
            "platform": platform,
            "architecture": arch
        }

    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.get("/api/v1/download/file")
async def download_file(
    version: str = Query(...),
    platform: str = Query("windows"),
    arch: str = Query("x64"),
    relative_path: str = Query(...),
    api_key: str = Query(...),
    db: Session = Depends(get_db)
):
    """下载指定文件"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 查找版本记录
        version_record = db.query(Version).filter(
            Version.version == version,
            Version.platform == platform,
            Version.architecture == arch
        ).first()

        if not version_record:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 查找文件记录
        file_record = db.query(SingleFile).filter(
            SingleFile.version_id == version_record.id,
            SingleFile.relative_path == relative_path
        ).first()

        if not file_record:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 构建文件路径
        file_path = Path(config.UPLOAD_DIR) / platform / arch / version / relative_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在于服务器")

        # 返回文件流
        return FileResponse(
            path=str(file_path),
            filename=str(file_record.file_name),
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件下载失败: {str(e)}")

@app.post("/api/v1/version/compare")
async def compare_versions(
    target_version: str = Form(...),
    platform: str = Form("windows"),
    arch: str = Form("x64"),
    local_files: str = Form(...),  # JSON string of local file info
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """比较本地文件与目标版本的差异"""
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        import json

        # 解析本地文件信息
        try:
            local_file_data = json.loads(local_files)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="本地文件信息格式错误")

        # 查找目标版本记录
        version_record = db.query(Version).filter(
            Version.version == target_version,
            Version.platform == platform,
            Version.architecture == arch
        ).first()

        if not version_record:
            raise HTTPException(status_code=404, detail="目标版本不存在")

        # 获取远程文件列表
        remote_files = db.query(SingleFile).filter(
            SingleFile.version_id == version_record.id
        ).all()

        # 构建远程文件映射
        remote_file_map = {}
        for file_record in remote_files:
            remote_file_map[file_record.relative_path] = {
                "relative_path": file_record.relative_path,
                "file_name": file_record.file_name,
                "file_size": file_record.file_size,
                "sha256": file_record.sha256_hash,
                "created_at": file_record.created_at.isoformat() if getattr(file_record, 'created_at', None) else None
            }

        # 构建本地文件映射
        local_file_map = {}
        for file_info in local_file_data:
            local_file_map[file_info["relative_path"]] = file_info

        # 分析差异
        files_to_download = []  # 需要下载的文件
        files_to_delete = []    # 需要删除的文件（可选）
        files_same = []         # 相同的文件

        total_download_size = 0

        # 检查远程文件
        for path, remote_info in remote_file_map.items():
            if path not in local_file_map:
                # 新文件
                files_to_download.append({
                    **remote_info,
                    "change_type": "new"
                })
                total_download_size += remote_info["file_size"]
            elif local_file_map[path].get("sha256") != remote_info["sha256"]:
                # 更新文件
                files_to_download.append({
                    **remote_info,
                    "change_type": "updated"
                })
                total_download_size += remote_info["file_size"]
            else:
                # 相同文件
                files_same.append({
                    **remote_info,
                    "change_type": "same"
                })

        # 检查本地独有文件（可能需要删除）
        for path in local_file_map.keys():
            if path not in remote_file_map:
                files_to_delete.append({
                    "relative_path": path,
                    "change_type": "deleted"
                })

        return {
            "target_version": target_version,
            "platform": platform,
            "architecture": arch,
            "summary": {
                "files_to_download": len(files_to_download),
                "files_to_delete": len(files_to_delete),
                "files_same": len(files_same),
                "total_download_size": total_download_size
            },
            "changes": {
                "download": files_to_download,
                "delete": files_to_delete,
                "same": files_same
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"版本比较失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本比较失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
