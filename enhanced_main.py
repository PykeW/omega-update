#!/usr/bin/env python3
"""
增强版Omega更新服务器主程序
支持完整包、增量包和存储管理
"""

import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from datetime import datetime
from typing import Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from server_config import ServerConfig
from enhanced_database import (
    init_database, get_db, Version, Package, PackageFile, 
    PackageType, PackageStatus, StorageStats, CleanupHistory
)
from storage_manager import storage_manager
from sqlalchemy.orm import Session

# 初始化配置
config = ServerConfig()
config.ensure_directories()

# 初始化FastAPI应用
app = FastAPI(
    title="Omega更新服务器 - 增强版",
    description="支持完整包、增量包和智能存储管理的更新系统",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.mount("/downloads", StaticFiles(directory=str(config.UPLOAD_DIR)), name="downloads")

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

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Omega更新服务器启动中...")
    init_database()
    logger.info("数据库初始化完成")

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
async def health_check():
    """健康检查"""
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

if __name__ == "__main__":
    uvicorn.run(
        "enhanced_main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
