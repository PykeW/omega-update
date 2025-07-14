#!/usr/bin/env python3
"""
简化版本管理系统 - 数据库模型
实现三版本类型系统：稳定版、测试版、新功能测试版
"""

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class VersionType(Enum):
    """版本类型枚举"""
    STABLE = "stable"    # 稳定版
    BETA = "beta"        # 测试版
    ALPHA = "alpha"      # 新功能测试版


class Platform(Enum):
    """平台枚举"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class Architecture(Enum):
    """架构枚举"""
    X64 = "x64"
    X86 = "x86"
    ARM64 = "arm64"


class SimplifiedVersion(Base):
    """简化版本表 - 每个版本类型只保存最新版本"""
    __tablename__ = 'simplified_versions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_type = Column(String(20), nullable=False)  # stable, beta, alpha
    platform = Column(String(50), nullable=False)     # windows, linux, macos
    architecture = Column(String(20), nullable=False) # x64, x86, arm64
    description = Column(Text)
    upload_date = Column(DateTime, default=func.now())
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_hash = Column(String(64), nullable=False)
    uploader_info = Column(Text)  # JSON格式的上传者信息

    # 确保每个平台/架构/类型组合唯一
    __table_args__ = (
        UniqueConstraint('version_type', 'platform', 'architecture',
                        name='uq_version_platform_arch'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'version_type': self.version_type,
            'platform': self.platform,
            'architecture': self.architecture,
            'description': self.description,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'uploader_info': self.uploader_info
        }


class VersionHistory(Base):
    """版本历史表 - 用于审计和回滚"""
    __tablename__ = 'version_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_type = Column(String(20), nullable=False)
    platform = Column(String(50), nullable=False)
    architecture = Column(String(20), nullable=False)
    description = Column(Text)
    upload_date = Column(DateTime)
    file_path = Column(String(500))
    file_size = Column(BigInteger)
    file_hash = Column(String(64))
    action = Column(String(20), nullable=False)  # 'uploaded', 'replaced', 'deleted'
    created_at = Column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'version_type': self.version_type,
            'platform': self.platform,
            'architecture': self.architecture,
            'description': self.description,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'action': self.action,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SimplifiedVersionManager:
    """简化版本管理器"""

    def __init__(self, db_session):
        self.db = db_session

    def upload_version(self, version_type: str, platform: str, architecture: str,
                      file_path: str, file_size: int, file_hash: str,
                      description: Optional[str] = None,
                      uploader_info: Optional[str] = None) -> SimplifiedVersion:
        """
        上传新版本，自动覆盖同类型的旧版本

        Args:
            version_type: 版本类型 (stable, beta, alpha)
            platform: 平台
            architecture: 架构
            file_path: 文件路径
            file_size: 文件大小
            file_hash: 文件哈希
            description: 版本描述
            uploader_info: 上传者信息

        Returns:
            新创建的版本记录
        """
        # 检查是否存在同类型版本
        existing_version = self.db.query(SimplifiedVersion).filter(
            SimplifiedVersion.version_type == version_type,
            SimplifiedVersion.platform == platform,
            SimplifiedVersion.architecture == architecture
        ).first()

        # 如果存在旧版本，记录到历史表并删除
        if existing_version:
            # 记录到历史表
            history_record = VersionHistory(
                version_type=existing_version.version_type,
                platform=existing_version.platform,
                architecture=existing_version.architecture,
                description=existing_version.description,
                upload_date=existing_version.upload_date,
                file_path=existing_version.file_path,
                file_size=existing_version.file_size,
                file_hash=existing_version.file_hash,
                action='replaced'
            )
            self.db.add(history_record)

            # 删除旧版本
            self.db.delete(existing_version)

        # 创建新版本记录
        new_version = SimplifiedVersion(
            version_type=version_type,
            platform=platform,
            architecture=architecture,
            description=description,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            uploader_info=uploader_info
        )

        self.db.add(new_version)

        # 记录上传历史
        upload_history = VersionHistory(
            version_type=version_type,
            platform=platform,
            architecture=architecture,
            description=description,
            upload_date=new_version.upload_date,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            action='uploaded'
        )
        self.db.add(upload_history)

        self.db.commit()
        return new_version

    def get_versions(self, platform: str = "windows",
                    architecture: str = "x64") -> Dict[str, Optional[SimplifiedVersion]]:
        """
        获取指定平台和架构的所有版本类型

        Args:
            platform: 平台
            architecture: 架构

        Returns:
            版本类型到版本记录的映射
        """
        versions = self.db.query(SimplifiedVersion).filter(
            SimplifiedVersion.platform == platform,
            SimplifiedVersion.architecture == architecture
        ).all()

        result = {
            'stable': None,
            'beta': None,
            'alpha': None
        }

        for version in versions:
            result[version.version_type] = version

        return result

    def get_version(self, version_type: str, platform: str = "windows",
                   architecture: str = "x64") -> Optional[SimplifiedVersion]:
        """
        获取指定版本类型的版本

        Args:
            version_type: 版本类型
            platform: 平台
            architecture: 架构

        Returns:
            版本记录或None
        """
        return self.db.query(SimplifiedVersion).filter(
            SimplifiedVersion.version_type == version_type,
            SimplifiedVersion.platform == platform,
            SimplifiedVersion.architecture == architecture
        ).first()

    def delete_version(self, version_type: str, platform: str = "windows",
                      architecture: str = "x64") -> bool:
        """
        删除指定版本

        Args:
            version_type: 版本类型
            platform: 平台
            architecture: 架构

        Returns:
            是否删除成功
        """
        version = self.get_version(version_type, platform, architecture)
        if not version:
            return False

        # 记录删除历史
        delete_history = VersionHistory(
            version_type=version.version_type,
            platform=version.platform,
            architecture=version.architecture,
            description=version.description,
            upload_date=version.upload_date,
            file_path=version.file_path,
            file_size=version.file_size,
            file_hash=version.file_hash,
            action='deleted'
        )
        self.db.add(delete_history)

        # 删除版本记录
        self.db.delete(version)
        self.db.commit()

        return True

    def get_history(self, version_type: Optional[str] = None,
                   platform: str = "windows", architecture: str = "x64",
                   limit: int = 50) -> list:
        """
        获取版本历史记录

        Args:
            version_type: 版本类型（可选）
            platform: 平台
            architecture: 架构
            limit: 返回记录数限制

        Returns:
            历史记录列表
        """
        query = self.db.query(VersionHistory).filter(
            VersionHistory.platform == platform,
            VersionHistory.architecture == architecture
        )

        if version_type:
            query = query.filter(VersionHistory.version_type == version_type)

        return query.order_by(VersionHistory.created_at.desc()).limit(limit).all()


# 数据库初始化函数
def create_simplified_tables(engine):
    """创建简化版本管理系统的数据库表"""
    Base.metadata.create_all(engine)
