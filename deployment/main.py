#!/usr/bin/env python3
"""
Omega更新服务器主程序 - 遗留版本
基于FastAPI的更新服务器

⚠️ 警告：此文件已弃用！
请使用 start_integrated_server.py 作为主服务器文件。
此文件仅用于部署参考，不应在生产环境中使用。
"""

# 此文件已弃用，请使用 start_integrated_server.py
import sys
print("⚠️ 警告：deployment/main.py 已弃用！")
print("请使用 start_integrated_server.py 作为主服务器文件。")
sys.exit(1)

import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
from datetime import datetime
import hashlib
import json

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from server_config import ServerConfig
from sqlalchemy.orm import Session
# 注意：这是一个遗留的部署文件，使用旧的数据库模型
# 主服务器文件是 start_integrated_server.py
from server.simplified_database import SimplifiedVersion, SimplifiedVersionFile, SimplifiedVersionManager
from server.enhanced_database import init_database, get_db, Version, Package as VersionFile, PackageType

# 初始化配置
config = ServerConfig()
config.ensure_directories()

# 初始化FastAPI应用
app = FastAPI(
    title="Omega更新服务器",
    description="Omega软件自动更新系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
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
        "message": "Omega更新服务器",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/version/check")
async def check_version(
    current_version: str,
    platform: str = "windows",
    arch: str = "x64",
    db: Session = Depends(get_db)
):
    """检查版本更新"""
    try:
        # 查找最新版本
        latest_version = db.query(Version).filter(
            Version.platform == platform,
            Version.architecture == arch,
            Version.is_stable == True
        ).order_by(Version.release_date.desc()).first()

        if not latest_version:
            raise HTTPException(status_code=404, detail="没有找到可用版本")

        # 简单的版本比较 (实际应用中应该使用更复杂的版本比较逻辑)
        has_update = current_version != latest_version.version

        response = {
            "has_update": has_update,
            "current_version": current_version,
            "latest_version": latest_version.version
        }

        if has_update:
            response["update_info"] = {
                "version": latest_version.version,
                "description": latest_version.description or "",
                "release_date": latest_version.release_date.isoformat(),
                "is_critical": latest_version.is_critical,
                "file_size": latest_version.total_size,
                "download_url": f"/api/v1/download/version/{latest_version.id}"
            }

        logger.info(f"版本检查: {current_version} -> {latest_version.version}, 有更新: {has_update}")
        return response

    except Exception as e:
        logger.error(f"版本检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本检查失败: {str(e)}")

@app.get("/api/v1/versions")
async def list_versions(
    platform: str = "windows",
    arch: str = "x64",
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取版本列表"""
    try:
        versions = db.query(Version).filter(
            Version.platform == platform,
            Version.architecture == arch
        ).order_by(Version.release_date.desc()).limit(limit).all()

        return [
            {
                "version": v.version,
                "description": v.description or "",
                "release_date": v.release_date.isoformat(),
                "is_stable": v.is_stable,
                "is_critical": v.is_critical,
                "file_size": v.total_size
            }
            for v in versions
        ]

    except Exception as e:
        logger.error(f"获取版本列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本列表失败: {str(e)}")

@app.post("/api/v1/upload/version")
async def upload_version(
    version: str = Form(...),
    description: str = Form(""),
    is_stable: bool = Form(True),
    is_critical: bool = Form(False),
    platform: str = Form("windows"),
    arch: str = Form("x64"),
    file: UploadFile = File(...),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传新版本"""
    # 验证API密钥
    if api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")

    try:
        # 检查文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

        # 创建版本目录
        version_dir = config.UPLOAD_DIR / "versions" / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = version_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # 计算文件哈希
        sha256_hash = hashlib.sha256(content).hexdigest()

        # 保存到数据库
        db_version = Version(
            version=version,
            description=description,
            is_stable=is_stable,
            is_critical=is_critical,
            platform=platform,
            architecture=arch,
            total_size=len(content),
            file_count=1
        )

        db.add(db_version)
        db.commit()
        db.refresh(db_version)

        # 保存文件信息 (使用Package模型作为文件记录)
        db_file = VersionFile(
            version_id=db_version.id,
            package_type=PackageType.FULL,
            package_name=file.filename,
            package_size=len(content),
            sha256_hash=sha256_hash,
            storage_path=str(file_path),
            download_url=f"/downloads/versions/{version}/{file.filename}"
        )

        db.add(db_file)
        db.commit()

        logger.info(f"版本上传成功: {version}")
        return {
            "message": "版本上传成功",
            "version": version,
            "file_size": len(content),
            "sha256": sha256_hash
        }

    except Exception as e:
        logger.error(f"版本上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本上传失败: {str(e)}")

@app.get("/api/v1/download/version/{version_id}")
async def download_version(version_id: int, db: Session = Depends(get_db)):
    """下载版本文件"""
    try:
        version = db.query(Version).filter(Version.id == version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 获取主文件
        main_file = db.query(VersionFile).filter(
            VersionFile.version_id == version_id
        ).first()

        if not main_file or not Path(str(main_file.storage_path)).exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=str(main_file.storage_path),
            filename=str(main_file.package_name),
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

@app.get("/api/v1/stats")
async def get_stats(db: Session = Depends(get_db)):
    """获取统计信息"""
    try:
        total_versions = db.query(Version).count()
        stable_versions = db.query(Version).filter(Version.is_stable == True).count()

        return {
            "total_versions": total_versions,
            "stable_versions": stable_versions,
            "server_status": "running",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
