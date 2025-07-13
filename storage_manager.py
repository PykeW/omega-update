#!/usr/bin/env python3
"""
存储空间管理模块
实现存储监控、自动清理和版本管理功能
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from enhanced_database import (
    Package, Version, StorageStats, CleanupHistory, 
    PackageType, PackageStatus, ServerConfig, get_db
)

logger = logging.getLogger(__name__)

class StorageManager:
    """存储空间管理器"""
    
    def __init__(self, base_path: str = "/var/www/omega-updates/uploads"):
        self.base_path = Path(base_path)
        self.full_path = self.base_path / "full"
        self.patch_path = self.base_path / "patches"
        self.hotfix_path = self.base_path / "hotfixes"
        self.temp_path = self.base_path / "temp"
        
        # 确保目录存在
        for path in [self.full_path, self.patch_path, self.hotfix_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_storage_stats(self) -> Dict:
        """获取存储统计信息"""
        try:
            # 获取磁盘使用情况
            total, used, free = shutil.disk_usage(self.base_path)
            
            # 计算各类型包的使用情况
            full_size = self._get_directory_size(self.full_path)
            patch_size = self._get_directory_size(self.patch_path)
            hotfix_size = self._get_directory_size(self.hotfix_path)
            temp_size = self._get_directory_size(self.temp_path)
            
            updates_total = full_size + patch_size + hotfix_size + temp_size
            usage_percentage = (used / total) * 100 if total > 0 else 0
            
            return {
                "total_size": total,
                "used_size": used,
                "available_size": free,
                "usage_percentage": usage_percentage,
                "updates_total_size": updates_total,
                "full_packages_size": full_size,
                "patch_packages_size": patch_size,
                "hotfix_packages_size": hotfix_size,
                "temp_size": temp_size,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {}
    
    def _get_directory_size(self, path: Path) -> int:
        """计算目录大小"""
        total_size = 0
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"计算目录大小失败 {path}: {e}")
        return total_size
    
    def check_storage_health(self, db: Session) -> Dict:
        """检查存储健康状况"""
        stats = self.get_storage_stats()
        
        # 获取配置阈值 (优化版 - 更积极的清理策略)
        warning_threshold = float(self._get_config(db, "warning_threshold", "0.70"))
        critical_threshold = float(self._get_config(db, "critical_threshold", "0.85"))
        cleanup_threshold = float(self._get_config(db, "cleanup_threshold", "0.75"))
        
        usage_percentage = stats.get("usage_percentage", 0) / 100
        
        health_status = "healthy"
        recommendations = []
        
        if usage_percentage >= critical_threshold:
            health_status = "critical"
            recommendations.append("立即执行清理操作")
            recommendations.append("考虑扩展存储空间")
        elif usage_percentage >= cleanup_threshold:
            health_status = "warning"
            recommendations.append("建议执行自动清理")
        elif usage_percentage >= warning_threshold:
            health_status = "caution"
            recommendations.append("监控存储使用情况")
        
        return {
            "status": health_status,
            "usage_percentage": usage_percentage * 100,
            "recommendations": recommendations,
            "stats": stats,
            "thresholds": {
                "warning": warning_threshold * 100,
                "cleanup": cleanup_threshold * 100,
                "critical": critical_threshold * 100
            }
        }
    
    def should_cleanup(self, db: Session) -> bool:
        """检查是否需要执行清理"""
        stats = self.get_storage_stats()
        cleanup_threshold = float(self._get_config(db, "cleanup_threshold", "0.75"))
        usage_percentage = stats.get("usage_percentage", 0) / 100
        
        return usage_percentage >= cleanup_threshold
    
    def execute_cleanup(self, db: Session, cleanup_type: str = "auto") -> Dict:
        """执行存储清理"""
        logger.info(f"开始执行{cleanup_type}清理")
        
        # 记录清理前状态
        before_stats = self.get_storage_stats()
        before_usage = before_stats.get("usage_percentage", 0)
        before_used = before_stats.get("used_size", 0)
        
        # 创建清理历史记录
        cleanup_record = CleanupHistory(
            cleanup_type=cleanup_type,
            trigger_reason=f"存储使用率达到{before_usage:.1f}%",
            before_usage_percentage=before_usage,
            before_used_size=before_used,
            status="running"
        )
        db.add(cleanup_record)
        db.commit()
        
        deleted_packages = []
        total_freed = 0
        
        try:
            # 1. 清理临时文件
            temp_freed = self._cleanup_temp_files()
            total_freed += temp_freed
            
            # 2. 清理过期的热修复包
            hotfix_freed, hotfix_deleted = self._cleanup_hotfix_packages(db)
            total_freed += hotfix_freed
            deleted_packages.extend(hotfix_deleted)
            
            # 3. 清理多余的增量包
            patch_freed, patch_deleted = self._cleanup_patch_packages(db)
            total_freed += patch_freed
            deleted_packages.extend(patch_deleted)
            
            # 4. 如果仍然空间不足，清理旧的完整包
            if self.should_cleanup(db):
                full_freed, full_deleted = self._cleanup_full_packages(db)
                total_freed += full_freed
                deleted_packages.extend(full_deleted)
            
            # 记录清理后状态
            after_stats = self.get_storage_stats()
            after_usage = after_stats.get("usage_percentage", 0)
            after_used = after_stats.get("used_size", 0)
            
            # 更新清理记录
            cleanup_record.packages_deleted = len(deleted_packages)
            cleanup_record.space_freed = total_freed
            cleanup_record.after_usage_percentage = after_usage
            cleanup_record.after_used_size = after_used
            cleanup_record.deleted_packages = json.dumps(deleted_packages)
            cleanup_record.status = "completed"
            cleanup_record.completed_at = datetime.now()
            
            db.commit()
            
            logger.info(f"清理完成: 释放{total_freed / (1024*1024*1024):.2f}GB空间")
            
            return {
                "success": True,
                "space_freed": total_freed,
                "packages_deleted": len(deleted_packages),
                "before_usage": before_usage,
                "after_usage": after_usage,
                "deleted_packages": deleted_packages
            }
            
        except Exception as e:
            logger.error(f"清理过程失败: {e}")
            cleanup_record.status = "failed"
            cleanup_record.error_message = str(e)
            cleanup_record.completed_at = datetime.now()
            db.commit()
            
            return {
                "success": False,
                "error": str(e),
                "space_freed": total_freed,
                "packages_deleted": len(deleted_packages)
            }
    
    def _cleanup_temp_files(self) -> int:
        """清理临时文件"""
        freed_space = 0
        try:
            for file_path in self.temp_path.rglob('*'):
                if file_path.is_file():
                    # 删除超过24小时的临时文件
                    if datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime) > timedelta(hours=24):
                        freed_space += file_path.stat().st_size
                        file_path.unlink()
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
        
        return freed_space
    
    def _cleanup_hotfix_packages(self, db: Session) -> Tuple[int, List[Dict]]:
        """清理热修复包"""
        max_hotfix = int(self._get_config(db, "max_hotfix_packages", "20"))
        
        # 获取所有热修复包，按创建时间排序
        hotfix_packages = db.query(Package).filter(
            Package.package_type == PackageType.HOTFIX,
            Package.status == PackageStatus.AVAILABLE
        ).order_by(Package.created_at.desc()).all()
        
        freed_space = 0
        deleted_packages = []
        
        # 删除超出数量限制的热修复包
        for package in hotfix_packages[max_hotfix:]:
            try:
                file_path = Path(package.storage_path)
                if file_path.exists():
                    freed_space += file_path.stat().st_size
                    file_path.unlink()
                
                package.status = PackageStatus.DELETED
                deleted_packages.append({
                    "id": package.id,
                    "type": "hotfix",
                    "version": package.version.version,
                    "size": package.package_size
                })
                
            except Exception as e:
                logger.error(f"删除热修复包失败 {package.id}: {e}")
        
        db.commit()
        return freed_space, deleted_packages
    
    def _cleanup_patch_packages(self, db: Session) -> Tuple[int, List[Dict]]:
        """清理增量包"""
        max_patch = int(self._get_config(db, "max_patch_packages", "10"))
        
        # 获取所有增量包，按创建时间排序
        patch_packages = db.query(Package).filter(
            Package.package_type == PackageType.PATCH,
            Package.status == PackageStatus.AVAILABLE
        ).order_by(Package.created_at.desc()).all()
        
        freed_space = 0
        deleted_packages = []
        
        # 删除超出数量限制的增量包
        for package in patch_packages[max_patch:]:
            try:
                file_path = Path(package.storage_path)
                if file_path.exists():
                    freed_space += file_path.stat().st_size
                    file_path.unlink()
                
                package.status = PackageStatus.DELETED
                deleted_packages.append({
                    "id": package.id,
                    "type": "patch",
                    "from_version": package.from_version,
                    "to_version": package.version.version,
                    "size": package.package_size
                })
                
            except Exception as e:
                logger.error(f"删除增量包失败 {package.id}: {e}")
        
        db.commit()
        return freed_space, deleted_packages
    
    def _cleanup_full_packages(self, db: Session) -> Tuple[int, List[Dict]]:
        """清理完整包"""
        max_full = int(self._get_config(db, "max_full_packages", "3"))
        
        # 获取所有完整包，排除受保护的版本
        full_packages = db.query(Package).join(Version).filter(
            Package.package_type == PackageType.FULL,
            Package.status == PackageStatus.AVAILABLE,
            Version.is_protected == False
        ).order_by(Package.created_at.desc()).all()
        
        freed_space = 0
        deleted_packages = []
        
        # 删除超出数量限制的完整包（保留最新的几个）
        for package in full_packages[max_full:]:
            try:
                file_path = Path(package.storage_path)
                if file_path.exists():
                    freed_space += file_path.stat().st_size
                    file_path.unlink()
                
                package.status = PackageStatus.DELETED
                deleted_packages.append({
                    "id": package.id,
                    "type": "full",
                    "version": package.version.version,
                    "size": package.package_size
                })
                
            except Exception as e:
                logger.error(f"删除完整包失败 {package.id}: {e}")
        
        db.commit()
        return freed_space, deleted_packages
    
    def _get_config(self, db: Session, key: str, default: str) -> str:
        """获取配置值"""
        config = db.query(ServerConfig).filter(ServerConfig.key == key).first()
        return config.value if config else default
    
    def record_storage_stats(self, db: Session):
        """记录存储统计信息"""
        stats = self.get_storage_stats()
        
        # 获取包数量统计
        full_count = db.query(Package).filter(
            Package.package_type == PackageType.FULL,
            Package.status == PackageStatus.AVAILABLE
        ).count()
        
        patch_count = db.query(Package).filter(
            Package.package_type == PackageType.PATCH,
            Package.status == PackageStatus.AVAILABLE
        ).count()
        
        hotfix_count = db.query(Package).filter(
            Package.package_type == PackageType.HOTFIX,
            Package.status == PackageStatus.AVAILABLE
        ).count()
        
        # 创建统计记录
        storage_stats = StorageStats(
            total_size=stats.get("total_size", 0),
            used_size=stats.get("used_size", 0),
            available_size=stats.get("available_size", 0),
            usage_percentage=stats.get("usage_percentage", 0),
            full_packages_count=full_count,
            full_packages_size=stats.get("full_packages_size", 0),
            patch_packages_count=patch_count,
            patch_packages_size=stats.get("patch_packages_size", 0),
            hotfix_packages_count=hotfix_count,
            hotfix_packages_size=stats.get("hotfix_packages_size", 0)
        )
        
        db.add(storage_stats)
        db.commit()

# 全局存储管理器实例
storage_manager = StorageManager()
