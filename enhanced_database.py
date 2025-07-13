#!/usr/bin/env python3
"""
增强版数据库模型定义
支持完整包、增量包和存储管理
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, BigInteger, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
import enum

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omega_updates.db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PackageType(enum.Enum):
    """包类型枚举"""
    FULL = "full"           # 完整包
    PATCH = "patch"         # 增量包
    HOTFIX = "hotfix"       # 热修复包

class PackageStatus(enum.Enum):
    """包状态枚举"""
    UPLOADING = "uploading"     # 上传中
    PROCESSING = "processing"   # 处理中
    AVAILABLE = "available"     # 可用
    DEPRECATED = "deprecated"   # 已弃用
    DELETED = "deleted"         # 已删除

class Version(Base):
    """版本信息表"""
    __tablename__ = 'versions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    release_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 版本属性
    is_stable = Column(Boolean, default=True)
    is_critical = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)  # 受保护版本，不会被自动清理
    min_version = Column(String(50))  # 最低兼容版本
    
    # 文件信息
    total_size = Column(BigInteger, default=0)
    file_count = Column(Integer, default=0)

    # 平台信息
    platform = Column(String(20), default='windows')
    architecture = Column(String(20), default='x64')

    # 统计信息
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime)

    # 关联关系
    packages = relationship("Package", back_populates="version", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Version(version='{self.version}', release_date='{self.release_date}')>"

class Package(Base):
    """更新包表（统一管理所有类型的包）"""
    __tablename__ = 'packages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    # 包基本信息
    package_type = Column(Enum(PackageType), nullable=False)
    package_name = Column(String(255), nullable=False)
    package_size = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    
    # 存储信息
    storage_path = Column(String(500), nullable=False)
    download_url = Column(String(500))
    
    # 包状态
    status = Column(Enum(PackageStatus), default=PackageStatus.UPLOADING)
    
    # 增量包特有信息
    from_version = Column(String(50))  # 源版本（仅增量包）
    
    # 包统计信息
    added_files = Column(Integer, default=0)
    deleted_files = Column(Integer, default=0)
    modified_files = Column(Integer, default=0)
    
    # 压缩信息
    compression_ratio = Column(Float)
    estimated_download_time = Column(Integer, default=0)  # 预估下载时间（秒）
    
    # 统计信息
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关联关系
    version = relationship("Version", back_populates="packages")
    files = relationship("PackageFile", back_populates="package", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Package(type='{self.package_type}', version='{self.version_id}')>"

class PackageFile(Base):
    """包文件表"""
    __tablename__ = 'package_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    package_id = Column(Integer, ForeignKey('packages.id'), nullable=False)

    # 文件信息
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False)

    # 文件属性
    is_executable = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    file_type = Column(String(50))  # 文件类型
    
    # 操作类型（用于增量包）
    operation = Column(String(20), default='add')  # add, modify, delete, patch

    created_at = Column(DateTime, default=func.now())

    # 关联关系
    package = relationship("Package", back_populates="files")

    def __repr__(self):
        return f"<PackageFile(file_path='{self.file_path}', size={self.file_size})>"

class StorageStats(Base):
    """存储统计表"""
    __tablename__ = 'storage_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 存储统计
    total_size = Column(BigInteger, default=0)
    used_size = Column(BigInteger, default=0)
    available_size = Column(BigInteger, default=0)
    usage_percentage = Column(Float, default=0.0)
    
    # 分类统计
    full_packages_count = Column(Integer, default=0)
    full_packages_size = Column(BigInteger, default=0)
    patch_packages_count = Column(Integer, default=0)
    patch_packages_size = Column(BigInteger, default=0)
    hotfix_packages_count = Column(Integer, default=0)
    hotfix_packages_size = Column(BigInteger, default=0)
    
    # 记录时间
    recorded_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<StorageStats(usage={self.usage_percentage}%, recorded_at='{self.recorded_at}')>"

class CleanupHistory(Base):
    """清理历史表"""
    __tablename__ = 'cleanup_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 清理信息
    cleanup_type = Column(String(50), nullable=False)  # auto, manual, emergency
    trigger_reason = Column(String(200))  # 触发原因
    
    # 清理前状态
    before_usage_percentage = Column(Float)
    before_used_size = Column(BigInteger)
    
    # 清理结果
    packages_deleted = Column(Integer, default=0)
    files_deleted = Column(Integer, default=0)
    space_freed = Column(BigInteger, default=0)
    
    # 清理后状态
    after_usage_percentage = Column(Float)
    after_used_size = Column(BigInteger)
    
    # 清理详情
    deleted_packages = Column(Text)  # JSON格式的删除包列表
    
    # 状态
    status = Column(String(20), default='completed')  # running, completed, failed
    error_message = Column(Text)
    
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<CleanupHistory(type='{self.cleanup_type}', freed={self.space_freed})>"

class DownloadLog(Base):
    """下载日志表"""
    __tablename__ = 'download_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 客户端信息
    client_ip = Column(String(45))
    user_agent = Column(String(500))
    client_version = Column(String(50))

    # 下载信息
    package_id = Column(Integer, ForeignKey('packages.id'))
    download_type = Column(String(20))  # version_check, package_download
    
    # 下载状态
    status = Column(String(20))  # started, completed, failed, cancelled
    bytes_downloaded = Column(BigInteger, default=0)
    download_time = Column(Integer, default=0)  # 下载耗时（秒）
    download_speed = Column(Float, default=0.0)  # 下载速度（MB/s）

    # 错误信息
    error_message = Column(Text)

    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<DownloadLog(client_ip='{self.client_ip}', status='{self.status}')>"

class ServerConfig(Base):
    """服务器配置表"""
    __tablename__ = 'server_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ServerConfig(key='{self.key}', value='{self.value}')>"

# 数据库连接和会话管理
class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str | None = None):
        if database_url is None:
            database_url = DATABASE_URL

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()

# 全局数据库管理器实例
db_manager = DatabaseManager(DATABASE_URL)

def get_db():
    """获取数据库会话的依赖注入函数"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """初始化数据库"""
    db_manager.create_tables()

    # 创建默认配置
    db = db_manager.get_session()
    try:
        # 检查是否已有配置
        existing_config = db.query(ServerConfig).first()
        if not existing_config:
            default_configs = [
                ServerConfig(key="server_name", value="Omega Update Server",
                           description="服务器名称"),
                ServerConfig(key="max_total_storage", value="32212254720",
                           description="最大总存储空间（30GB）"),
                ServerConfig(key="max_full_packages", value="3",
                           description="最大完整包数量"),
                ServerConfig(key="max_patch_packages", value="10",
                           description="最大增量包数量"),
                ServerConfig(key="max_hotfix_packages", value="20",
                           description="最大热修复包数量"),
                ServerConfig(key="cleanup_threshold", value="0.75",
                           description="自动清理阈值"),
                ServerConfig(key="warning_threshold", value="0.70",
                           description="存储警告阈值"),
                ServerConfig(key="critical_threshold", value="0.85",
                           description="存储严重阈值"),
                ServerConfig(key="enable_auto_cleanup", value="true",
                           description="是否启用自动清理"),
                ServerConfig(key="current_stable_version", value="2.2.5",
                           description="当前稳定版本"),
            ]

            for config in default_configs:
                db.add(config)

            db.commit()
            print("默认配置已创建")
    except Exception as e:
        print(f"初始化数据库配置失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # 初始化数据库
    init_database()
    print("增强版数据库初始化完成")
