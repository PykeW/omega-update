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
from server.enhanced_database import (
    Package, Version, StorageStats, CleanupHistory,
    PackageType, PackageStatus, get_db
)
from server.server_config import ServerConfig

logger = logging.getLogger(__name__)

class StorageManager:
    """存储空间管理器"""
    
    def __init__(self, base_path: str = "/var/www/omega-updates/uploads"):
        self.base_path = Path(base_path)
        self.full_path = self.base_path / "full"
        self.patch_path = self.base_path / "patches"
        self.hotfix_path = self.base_path / "hotfixes"
        self.temp_path = self.base_path / "temp"
        self.backup_path = self.base_path / "backups"

        # 版本保留配置
        self.max_versions_per_platform = {
            PackageType.FULL: 2,      # 保留2个完整版本
            PackageType.PATCH: 5,     # 保留5个增量版本
            PackageType.HOTFIX: 10    # 保留10个热修复版本
        }

        # 确保目录存在
        for path in [self.full_path, self.patch_path, self.hotfix_path, self.temp_path, self.backup_path]:
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
            
            backup_size = self._get_directory_size(self.backup_path)
            updates_total = full_size + patch_size + hotfix_size + temp_size + backup_size
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

    def get_storage_structure(self, db: Session) -> Dict:
        """获取存储目录结构和版本文件信息"""
        try:
            structure = {
                "base_path": str(self.base_path),
                "directories": {},
                "total_files": 0,
                "total_size": 0
            }

            # 遍历各个目录
            for dir_name, dir_path in [
                ("full", self.full_path),
                ("patches", self.patch_path),
                ("hotfixes", self.hotfix_path),
                ("backups", self.backup_path),
                ("temp", self.temp_path)
            ]:
                dir_info = self._analyze_directory(dir_path, db)
                structure["directories"][dir_name] = dir_info
                structure["total_files"] += dir_info["file_count"]
                structure["total_size"] += dir_info["total_size"]

            logger.info(f"存储结构分析完成: {structure['total_files']} 个文件, {structure['total_size']} 字节")
            return structure

        except Exception as e:
            logger.error(f"获取存储结构失败: {e}")
            return {"error": str(e)}

    def _analyze_directory(self, dir_path: Path, db: Session) -> Dict:
        """分析目录内容"""
        try:
            if not dir_path.exists():
                return {"path": str(dir_path), "file_count": 0, "total_size": 0, "versions": []}

            versions = []
            total_size = 0
            file_count = 0

            # 遍历版本目录
            for version_dir in dir_path.iterdir():
                if version_dir.is_dir():
                    version_info = {
                        "version": version_dir.name,
                        "path": str(version_dir),
                        "files": [],
                        "size": 0
                    }

                    # 遍历版本目录中的文件
                    for file_path in version_dir.iterdir():
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            file_info = {
                                "name": file_path.name,
                                "size": file_size,
                                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                "sha256": self._calculate_file_hash(file_path)
                            }

                            # 从数据库获取包信息
                            package = db.query(Package).filter(
                                Package.package_name == file_path.name
                            ).first()

                            if package:
                                file_info.update({
                                    "package_id": package.id,
                                    "package_type": package.package_type.value,
                                    "download_count": package.download_count,
                                    "status": package.status.value
                                })

                            version_info["files"].append(file_info)
                            version_info["size"] += file_size
                            total_size += file_size
                            file_count += 1

                    versions.append(version_info)

            return {
                "path": str(dir_path),
                "file_count": file_count,
                "total_size": total_size,
                "versions": sorted(versions, key=lambda x: x["version"], reverse=True)
            }

        except Exception as e:
            logger.error(f"分析目录失败 {dir_path}: {e}")
            return {"path": str(dir_path), "error": str(e), "file_count": 0, "total_size": 0, "versions": []}

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希值"""
        import hashlib
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败 {file_path}: {e}")
            return ""

    def apply_version_retention_policy(self, db: Session) -> Dict:
        """应用版本保留策略，清理旧版本"""
        try:
            cleanup_result = {
                "success": True,
                "cleaned_packages": [],
                "space_freed": 0,
                "errors": []
            }

            # 按平台和架构分组处理
            platforms_archs = db.query(Version.platform, Version.architecture).distinct().all()

            for platform, arch in platforms_archs:
                for package_type in [PackageType.FULL, PackageType.PATCH, PackageType.HOTFIX]:
                    result = self._cleanup_old_versions(db, platform, arch, package_type)
                    cleanup_result["cleaned_packages"].extend(result["cleaned_packages"])
                    cleanup_result["space_freed"] += result["space_freed"]
                    cleanup_result["errors"].extend(result["errors"])

            # 记录清理历史
            if cleanup_result["cleaned_packages"]:
                cleanup_history = CleanupHistory(
                    cleanup_type="version_retention",
                    packages_deleted=len(cleanup_result["cleaned_packages"]),
                    space_freed=cleanup_result["space_freed"],
                    details=json.dumps({
                        "cleaned_packages": cleanup_result["cleaned_packages"],
                        "policy": self.max_versions_per_platform
                    })
                )
                db.add(cleanup_history)
                db.commit()

            logger.info(f"版本保留策略执行完成: 清理了 {len(cleanup_result['cleaned_packages'])} 个包, 释放 {cleanup_result['space_freed']} 字节")
            return cleanup_result

        except Exception as e:
            logger.error(f"版本保留策略执行失败: {e}")
            return {"success": False, "error": str(e)}

    def _cleanup_old_versions(self, db: Session, platform: str, arch: str, package_type: PackageType) -> Dict:
        """清理指定平台架构的旧版本"""
        try:
            max_versions = self.max_versions_per_platform.get(package_type, 1)

            # 获取该平台架构的所有版本，按创建时间排序
            versions = db.query(Version).filter(
                Version.platform == platform,
                Version.architecture == arch
            ).order_by(Version.created_at.desc()).all()

            cleanup_result = {
                "cleaned_packages": [],
                "space_freed": 0,
                "errors": []
            }

            # 找出需要清理的版本
            versions_to_cleanup = versions[max_versions:]

            for version in versions_to_cleanup:
                # 获取该版本的指定类型包
                packages = db.query(Package).filter(
                    Package.version_id == version.id,
                    Package.package_type == package_type,
                    Package.status == PackageStatus.AVAILABLE
                ).all()

                for package in packages:
                    try:
                        # 备份文件
                        backup_result = self._backup_package_file(package)
                        if not backup_result["success"]:
                            cleanup_result["errors"].append(f"备份失败: {package.package_name}")
                            continue

                        # 删除文件
                        file_path = Path(package.storage_path)
                        if file_path.exists():
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleanup_result["space_freed"] += file_size

                        # 更新数据库状态
                        package.status = PackageStatus.DELETED
                        cleanup_result["cleaned_packages"].append({
                            "package_id": package.id,
                            "package_name": package.package_name,
                            "version": version.version,
                            "platform": platform,
                            "arch": arch,
                            "type": package_type.value,
                            "size": package.package_size,
                            "backup_path": backup_result.get("backup_path")
                        })

                    except Exception as e:
                        error_msg = f"清理包失败 {package.package_name}: {e}"
                        logger.error(error_msg)
                        cleanup_result["errors"].append(error_msg)

            db.commit()
            return cleanup_result

        except Exception as e:
            logger.error(f"清理旧版本失败 {platform}-{arch}-{package_type.value}: {e}")
            return {"cleaned_packages": [], "space_freed": 0, "errors": [str(e)]}

    def _backup_package_file(self, package: Package) -> Dict:
        """备份包文件"""
        try:
            source_path = Path(package.storage_path)
            if not source_path.exists():
                return {"success": False, "error": "源文件不存在"}

            # 创建备份目录结构
            backup_dir = self.backup_path / package.package_type.value / datetime.now().strftime("%Y%m%d")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 生成备份文件名（包含时间戳）
            timestamp = datetime.now().strftime("%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = backup_dir / backup_filename

            # 复制文件
            shutil.copy2(source_path, backup_path)

            logger.info(f"文件备份成功: {source_path} -> {backup_path}")
            return {
                "success": True,
                "backup_path": str(backup_path),
                "original_path": str(source_path)
            }

        except Exception as e:
            logger.error(f"备份文件失败 {package.package_name}: {e}")
            return {"success": False, "error": str(e)}

    def verify_file_integrity(self, file_path: Path, expected_hash: str) -> Dict:
        """验证文件完整性"""
        try:
            if not file_path.exists():
                return {"valid": False, "error": "文件不存在"}

            actual_hash = self._calculate_file_hash(file_path)
            if not actual_hash:
                return {"valid": False, "error": "无法计算文件哈希"}

            is_valid = actual_hash.lower() == expected_hash.lower()

            return {
                "valid": is_valid,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size
            }

        except Exception as e:
            logger.error(f"文件完整性验证失败 {file_path}: {e}")
            return {"valid": False, "error": str(e)}

    def get_file_changes(self, db: Session, version: str, platform: str, arch: str) -> Dict:
        """获取版本间的文件变化信息"""
        try:
            # 获取指定版本的包
            current_version = db.query(Version).filter(
                Version.version == version,
                Version.platform == platform,
                Version.architecture == arch
            ).first()

            if not current_version:
                return {"error": "版本不存在"}

            packages = db.query(Package).filter(
                Package.version_id == current_version.id,
                Package.status == PackageStatus.AVAILABLE
            ).all()

            file_changes = []
            for package in packages:
                file_path = Path(package.storage_path)
                if file_path.exists():
                    file_info = {
                        "package_id": package.id,
                        "package_name": package.package_name,
                        "package_type": package.package_type.value,
                        "file_path": str(file_path),
                        "file_size": package.package_size,
                        "sha256": package.sha256_hash,
                        "download_url": package.download_url,
                        "created_at": package.created_at.isoformat() if package.created_at else None
                    }
                    file_changes.append(file_info)

            return {
                "version": version,
                "platform": platform,
                "architecture": arch,
                "files": file_changes,
                "total_files": len(file_changes),
                "total_size": sum(f["file_size"] for f in file_changes)
            }

        except Exception as e:
            logger.error(f"获取文件变化信息失败: {e}")
            return {"error": str(e)}

    def rollback_version(self, db: Session, package_id: int) -> Dict:
        """回滚到备份版本"""
        try:
            package = db.query(Package).filter(Package.id == package_id).first()
            if not package:
                return {"success": False, "error": "包不存在"}

            # 查找最新的备份文件
            backup_pattern = f"{Path(package.package_name).stem}_*{Path(package.package_name).suffix}"
            backup_dir = self.backup_path / package.package_type.value

            backup_files = []
            if backup_dir.exists():
                for date_dir in backup_dir.iterdir():
                    if date_dir.is_dir():
                        for backup_file in date_dir.glob(backup_pattern):
                            backup_files.append({
                                "path": backup_file,
                                "mtime": backup_file.stat().st_mtime
                            })

            if not backup_files:
                return {"success": False, "error": "没有找到备份文件"}

            # 选择最新的备份文件
            latest_backup = max(backup_files, key=lambda x: x["mtime"])
            backup_path = latest_backup["path"]

            # 备份当前文件
            current_path = Path(package.storage_path)
            if current_path.exists():
                temp_backup = self._backup_package_file(package)
                if not temp_backup["success"]:
                    return {"success": False, "error": "无法备份当前文件"}

            # 恢复备份文件
            current_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, current_path)

            # 更新数据库中的哈希值
            new_hash = self._calculate_file_hash(current_path)
            package.sha256_hash = new_hash
            package.status = PackageStatus.AVAILABLE
            db.commit()

            logger.info(f"版本回滚成功: {package.package_name} 从 {backup_path} 恢复")
            return {
                "success": True,
                "package_name": package.package_name,
                "backup_used": str(backup_path),
                "new_hash": new_hash
            }

        except Exception as e:
            logger.error(f"版本回滚失败: {e}")
            return {"success": False, "error": str(e)}

    def configure_retention_policy(self, package_type: PackageType, max_versions: int) -> Dict:
        """配置版本保留策略"""
        try:
            if max_versions < 1:
                return {"success": False, "error": "保留版本数量必须大于0"}

            old_value = self.max_versions_per_platform.get(package_type, 1)
            self.max_versions_per_platform[package_type] = max_versions

            logger.info(f"版本保留策略已更新: {package_type.value} {old_value} -> {max_versions}")
            return {
                "success": True,
                "package_type": package_type.value,
                "old_max_versions": old_value,
                "new_max_versions": max_versions
            }

        except Exception as e:
            logger.error(f"配置版本保留策略失败: {e}")
            return {"success": False, "error": str(e)}

# 全局存储管理器实例
storage_manager = StorageManager()
