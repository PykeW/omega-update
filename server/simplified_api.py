#!/usr/bin/env python3
"""
简化版本管理系统 - API端点
实现新的简化上传和下载API
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .simplified_database import (
    SimplifiedVersion, VersionHistory, SimplifiedVersionManager,
    VersionType, Platform, Architecture
)

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v2", tags=["simplified-version"])

# 配置常量（应该从配置文件读取）
API_KEY = "dac450db3ec47d79196edb7a34defaed"
UPLOAD_DIR = Path("uploads/simplified")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    """获取数据库会话（需要根据实际项目配置）"""
    # 这里需要根据实际的数据库配置来实现
    pass


def verify_api_key(api_key: str):
    """验证API密钥"""
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="无效的API密钥")


@router.post("/upload/simple")
async def upload_simple_version(
    file: UploadFile = File(...),
    version_type: str = Form(...),
    platform: str = Form("windows"),
    architecture: str = Form("x64"),
    description: Optional[str] = Form(None),
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    上传简化版本
    自动覆盖同类型的旧版本
    """
    logger.info(f"收到简化上传请求: type={version_type}, platform={platform}, arch={architecture}")
    
    # 验证API密钥
    verify_api_key(api_key)
    
    # 验证版本类型
    if version_type not in ['stable', 'beta', 'alpha']:
        raise HTTPException(status_code=400, detail=f"不支持的版本类型: {version_type}")
    
    # 验证平台和架构
    if platform not in ['windows', 'linux', 'macos']:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")
    
    if architecture not in ['x64', 'x86', 'arm64']:
        raise HTTPException(status_code=400, detail=f"不支持的架构: {architecture}")
    
    try:
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 计算文件哈希
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 构建文件存储路径
        file_dir = UPLOAD_DIR / platform / architecture / version_type
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用原始文件名，但确保唯一性
        file_name = file.filename or f"{version_type}.zip"
        file_path = file_dir / file_name
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 准备上传者信息
        uploader_info = json.dumps({
            "upload_time": datetime.now().isoformat(),
            "file_name": file_name,
            "content_type": file.content_type
        })
        
        # 使用版本管理器上传
        version_manager = SimplifiedVersionManager(db)
        new_version = version_manager.upload_version(
            version_type=version_type,
            platform=platform,
            architecture=architecture,
            file_path=str(file_path),
            file_size=file_size,
            file_hash=file_hash,
            description=description,
            uploader_info=uploader_info
        )
        
        logger.info(f"简化版本上传成功: {version_type}/{platform}/{architecture}")
        
        return {
            "success": True,
            "message": "版本上传成功",
            "version": new_version.to_dict(),
            "download_url": f"/api/v2/download/simple/{version_type}/{platform}/{architecture}"
        }
        
    except Exception as e:
        logger.error(f"简化版本上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/versions/simple")
async def get_simple_versions(
    platform: str = "windows",
    architecture: str = "x64",
    db: Session = Depends(get_db)
):
    """
    获取简化版本列表
    返回指定平台和架构的所有版本类型
    """
    try:
        version_manager = SimplifiedVersionManager(db)
        versions = version_manager.get_versions(platform, architecture)
        
        result = {}
        for version_type, version in versions.items():
            if version:
                result[version_type] = {
                    "description": version.description,
                    "upload_date": version.upload_date.isoformat() if version.upload_date else None,
                    "file_size": version.file_size,
                    "file_hash": version.file_hash,
                    "download_url": f"/api/v2/download/simple/{version_type}/{platform}/{architecture}"
                }
            else:
                result[version_type] = None
        
        return result
        
    except Exception as e:
        logger.error(f"获取简化版本列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本列表失败: {str(e)}")


@router.get("/download/simple/{version_type}/{platform}/{architecture}")
async def download_simple_version(
    version_type: str,
    platform: str = "windows",
    architecture: str = "x64",
    db: Session = Depends(get_db)
):
    """
    下载简化版本
    """
    try:
        version_manager = SimplifiedVersionManager(db)
        version = version_manager.get_version(version_type, platform, architecture)
        
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        file_path = Path(version.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 构建下载文件名
        file_name = f"{version_type}_{platform}_{architecture}.zip"
        
        return FileResponse(
            path=str(file_path),
            filename=file_name,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载简化版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


@router.get("/version/simple/{version_type}")
async def get_simple_version_info(
    version_type: str,
    platform: str = "windows",
    architecture: str = "x64",
    db: Session = Depends(get_db)
):
    """
    获取指定版本类型的详细信息
    """
    try:
        version_manager = SimplifiedVersionManager(db)
        version = version_manager.get_version(version_type, platform, architecture)
        
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        return version.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取版本信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本信息失败: {str(e)}")


@router.delete("/version/simple/{version_type}")
async def delete_simple_version(
    version_type: str,
    platform: str = "windows",
    architecture: str = "x64",
    api_key: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    删除指定版本类型
    """
    # 验证API密钥
    verify_api_key(api_key)
    
    try:
        version_manager = SimplifiedVersionManager(db)
        success = version_manager.delete_version(version_type, platform, architecture)
        
        if not success:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        return {
            "success": True,
            "message": f"版本 {version_type} 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/history/simple")
async def get_simple_version_history(
    version_type: Optional[str] = None,
    platform: str = "windows",
    architecture: str = "x64",
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取版本历史记录
    """
    try:
        version_manager = SimplifiedVersionManager(db)
        history = version_manager.get_history(version_type, platform, architecture, limit)
        
        return [record.to_dict() for record in history]
        
    except Exception as e:
        logger.error(f"获取版本历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.get("/status/simple")
async def get_simple_system_status(db: Session = Depends(get_db)):
    """
    获取简化系统状态
    """
    try:
        version_manager = SimplifiedVersionManager(db)
        
        # 统计各平台版本数量
        platforms = ['windows', 'linux', 'macos']
        architectures = ['x64', 'x86', 'arm64']
        version_types = ['stable', 'beta', 'alpha']
        
        stats = {}
        total_versions = 0
        
        for platform in platforms:
            stats[platform] = {}
            for arch in architectures:
                versions = version_manager.get_versions(platform, arch)
                available_types = [vt for vt, v in versions.items() if v is not None]
                stats[platform][arch] = {
                    'available_types': available_types,
                    'count': len(available_types)
                }
                total_versions += len(available_types)
        
        return {
            "system": "simplified_version_management",
            "status": "running",
            "total_versions": total_versions,
            "platforms": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")
