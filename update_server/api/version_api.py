#!/usr/bin/env python3
"""
版本管理API
提供版本检查、文件下载等接口
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
from datetime import datetime

from ..models.database import get_db, Version, VersionFile, UpdatePackage, DownloadLog
from ..utils.version_utils import compare_versions, is_version_compatible
from ..utils.response_models import (
    VersionCheckResponse, VersionInfo, UpdateInfo, FileInfo
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["version"])

@router.get("/version/check", response_model=VersionCheckResponse)
async def check_version(
    current_version: str = Query(..., description="客户端当前版本"),
    platform: str = Query("windows", description="客户端平台"),
    arch: str = Query("x64", description="客户端架构"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    检查版本更新
    
    Args:
        current_version: 客户端当前版本
        platform: 客户端平台
        arch: 客户端架构
        request: HTTP请求对象
        db: 数据库会话
        
    Returns:
        VersionCheckResponse: 版本检查结果
    """
    try:
        # 记录检查请求
        await _log_request(request, db, "version_check", current_version)
        
        # 查找最新的稳定版本
        latest_version = db.query(Version).filter(
            Version.platform == platform,
            Version.architecture == arch,
            Version.is_stable == True
        ).order_by(Version.release_date.desc()).first()
        
        if not latest_version:
            raise HTTPException(status_code=404, detail="没有找到可用版本")
        
        # 比较版本
        has_update = compare_versions(current_version, latest_version.version) < 0
        
        response = VersionCheckResponse(
            has_update=has_update,
            current_version=current_version,
            latest_version=latest_version.version
        )
        
        if has_update:
            # 查找更新包
            update_package = db.query(UpdatePackage).filter(
                UpdatePackage.from_version == current_version,
                UpdatePackage.to_version_id == latest_version.id
            ).first()
            
            # 构建更新信息
            update_info = UpdateInfo(
                version=latest_version.version,
                description=latest_version.description or "",
                release_date=latest_version.release_date.isoformat(),
                is_critical=latest_version.is_critical,
                min_version=latest_version.min_version or "",
                file_size=latest_version.total_size,
                download_url=f"/api/v1/download/version/{latest_version.id}"
            )
            
            # 如果有增量更新包，优先使用
            if update_package:
                update_info.package_type = "incremental"
                update_info.package_size = update_package.package_size
                update_info.download_url = f"/api/v1/download/package/{update_package.id}"
                update_info.estimated_time = update_package.estimated_time
                
                # 添加文件变更信息
                update_info.files_info = {
                    "added": update_package.added_files,
                    "deleted": update_package.deleted_files,
                    "modified": update_package.modified_files,
                    "patched": update_package.patched_files
                }
            else:
                update_info.package_type = "full"
                update_info.package_size = latest_version.total_size
            
            response.update_info = update_info
        
        logger.info(f"版本检查: {current_version} -> {latest_version.version}, 有更新: {has_update}")
        return response
        
    except Exception as e:
        logger.error(f"版本检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本检查失败: {str(e)}")

@router.get("/version/list", response_model=List[VersionInfo])
async def list_versions(
    platform: str = Query("windows", description="平台"),
    arch: str = Query("x64", description="架构"),
    stable_only: bool = Query(True, description="仅显示稳定版本"),
    limit: int = Query(10, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取版本列表
    
    Args:
        platform: 平台
        arch: 架构
        stable_only: 是否仅显示稳定版本
        limit: 返回数量限制
        db: 数据库会话
        
    Returns:
        List[VersionInfo]: 版本信息列表
    """
    try:
        query = db.query(Version).filter(
            Version.platform == platform,
            Version.architecture == arch
        )
        
        if stable_only:
            query = query.filter(Version.is_stable == True)
        
        versions = query.order_by(Version.release_date.desc()).limit(limit).all()
        
        return [VersionInfo(
            version=v.version,
            description=v.description or "",
            release_date=v.release_date.isoformat(),
            is_stable=v.is_stable,
            is_critical=v.is_critical,
            file_size=v.total_size,
            file_count=v.file_count
        ) for v in versions]
        
    except Exception as e:
        logger.error(f"获取版本列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本列表失败: {str(e)}")

@router.get("/version/{version_id}/files", response_model=List[FileInfo])
async def get_version_files(
    version_id: int,
    db: Session = Depends(get_db)
):
    """
    获取版本文件列表
    
    Args:
        version_id: 版本ID
        db: 数据库会话
        
    Returns:
        List[FileInfo]: 文件信息列表
    """
    try:
        version = db.query(Version).filter(Version.id == version_id).first()
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")
        
        files = db.query(VersionFile).filter(VersionFile.version_id == version_id).all()
        
        return [FileInfo(
            file_path=f.file_path,
            file_name=f.file_name,
            file_size=f.file_size,
            sha256_hash=f.sha256_hash,
            is_executable=f.is_executable,
            file_type=f.file_type or "",
            download_url=f.download_url or f"/api/v1/download/file/{f.id}"
        ) for f in files]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取版本文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本文件失败: {str(e)}")

@router.get("/version/{version}/compatibility")
async def check_compatibility(
    version: str,
    target_version: str = Query(..., description="目标版本"),
    db: Session = Depends(get_db)
):
    """
    检查版本兼容性
    
    Args:
        version: 当前版本
        target_version: 目标版本
        db: 数据库会话
        
    Returns:
        dict: 兼容性检查结果
    """
    try:
        # 查找目标版本
        target_ver = db.query(Version).filter(Version.version == target_version).first()
        if not target_ver:
            raise HTTPException(status_code=404, detail="目标版本不存在")
        
        # 检查兼容性
        is_compatible = is_version_compatible(version, target_ver.min_version or "0.0.0")
        
        # 查找升级路径
        upgrade_path = []
        if not is_compatible:
            # 查找中间版本
            intermediate_versions = db.query(Version).filter(
                Version.version > version,
                Version.version <= target_version,
                Version.is_stable == True
            ).order_by(Version.version).all()
            
            upgrade_path = [v.version for v in intermediate_versions]
        
        return {
            "compatible": is_compatible,
            "current_version": version,
            "target_version": target_version,
            "min_required_version": target_ver.min_version,
            "upgrade_path": upgrade_path,
            "direct_upgrade": is_compatible
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"兼容性检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"兼容性检查失败: {str(e)}")

@router.get("/stats/downloads")
async def get_download_stats(
    days: int = Query(7, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取下载统计信息
    
    Args:
        days: 统计天数
        db: 数据库会话
        
    Returns:
        dict: 下载统计信息
    """
    try:
        from datetime import timedelta
        from sqlalchemy import func
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 总下载次数
        total_downloads = db.query(DownloadLog).filter(
            DownloadLog.created_at >= start_date,
            DownloadLog.status == "completed"
        ).count()
        
        # 按版本统计
        version_stats = db.query(
            Version.version,
            func.count(DownloadLog.id).label('download_count')
        ).join(DownloadLog, Version.id == DownloadLog.version_id).filter(
            DownloadLog.created_at >= start_date,
            DownloadLog.status == "completed"
        ).group_by(Version.version).all()
        
        # 按日期统计
        daily_stats = db.query(
            func.date(DownloadLog.created_at).label('date'),
            func.count(DownloadLog.id).label('download_count')
        ).filter(
            DownloadLog.created_at >= start_date,
            DownloadLog.status == "completed"
        ).group_by(func.date(DownloadLog.created_at)).all()
        
        return {
            "period_days": days,
            "total_downloads": total_downloads,
            "version_stats": [{"version": v.version, "downloads": v.download_count} 
                            for v in version_stats],
            "daily_stats": [{"date": str(d.date), "downloads": d.download_count} 
                          for d in daily_stats]
        }
        
    except Exception as e:
        logger.error(f"获取下载统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取下载统计失败: {str(e)}")

async def _log_request(request: Request, db: Session, download_type: str, 
                      version: str = None):
    """记录请求日志"""
    try:
        if request:
            log_entry = DownloadLog(
                client_ip=request.client.host,
                user_agent=request.headers.get("user-agent", ""),
                client_version=version,
                download_type=download_type,
                status="started"
            )
            db.add(log_entry)
            db.commit()
    except Exception as e:
        logger.warning(f"记录请求日志失败: {e}")
        db.rollback()
