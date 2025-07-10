#!/usr/bin/env python3
"""
数据库模型定义
使用SQLAlchemy定义版本管理相关的数据模型
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()

class Version(Base):
    """版本信息表"""
    __tablename__ = 'versions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    release_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 版本属性
    is_stable = Column(Boolean, default=True)
    is_critical = Column(Boolean, default=False)
    min_version = Column(String(50))  # 最低兼容版本
    
    # 文件信息
    total_size = Column(BigInteger, default=0)
    file_count = Column(Integer, default=0)
    
    # 平台信息
    platform = Column(String(20), default='windows')
    architecture = Column(String(20), default='x64')
    
    # 关联关系
    files = relationship("VersionFile", back_populates="version", cascade="all, delete-orphan")
    update_packages = relationship("UpdatePackage", 
                                 foreign_keys="UpdatePackage.to_version_id",
                                 back_populates="to_version")
    
    def __repr__(self):
        return f"<Version(version='{self.version}', release_date='{self.release_date}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'description': self.description,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'is_stable': self.is_stable,
            'is_critical': self.is_critical,
            'min_version': self.min_version,
            'total_size': self.total_size,
            'file_count': self.file_count,
            'platform': self.platform,
            'architecture': self.architecture
        }

class VersionFile(Base):
    """版本文件表"""
    __tablename__ = 'version_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    # 文件信息
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    
    # 文件属性
    is_executable = Column(Boolean, default=False)
    is_critical = Column(Boolean, default=False)
    file_type = Column(String(50))  # 文件类型：executable, library, data, config等
    
    # 存储信息
    storage_path = Column(String(500))  # 在服务器上的存储路径
    download_url = Column(String(500))  # 下载URL
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联关系
    version = relationship("Version", back_populates="files")
    
    def __repr__(self):
        return f"<VersionFile(file_path='{self.file_path}', size={self.file_size})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'version_id': self.version_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'sha256_hash': self.sha256_hash,
            'is_executable': self.is_executable,
            'is_critical': self.is_critical,
            'file_type': self.file_type,
            'download_url': self.download_url
        }

class UpdatePackage(Base):
    """更新包表"""
    __tablename__ = 'update_packages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 版本信息
    from_version = Column(String(50), nullable=False)
    to_version_id = Column(Integer, ForeignKey('versions.id'), nullable=False)
    
    # 包信息
    package_type = Column(String(20), default='incremental')  # full, incremental
    package_size = Column(BigInteger, nullable=False)
    package_path = Column(String(500), nullable=False)
    download_url = Column(String(500))
    
    # 统计信息
    added_files = Column(Integer, default=0)
    deleted_files = Column(Integer, default=0)
    modified_files = Column(Integer, default=0)
    patched_files = Column(Integer, default=0)
    
    # 压缩信息
    compression_ratio = Column(String(10))  # 压缩比例
    estimated_time = Column(Integer, default=0)  # 预估下载时间（秒）
    
    # 校验信息
    sha256_hash = Column(String(64))
    
    created_at = Column(DateTime, default=func.now())
    
    # 关联关系
    to_version = relationship("Version", back_populates="update_packages")
    
    def __repr__(self):
        return f"<UpdatePackage(from='{self.from_version}', to='{self.to_version_id}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'from_version': self.from_version,
            'to_version_id': self.to_version_id,
            'package_type': self.package_type,
            'package_size': self.package_size,
            'download_url': self.download_url,
            'added_files': self.added_files,
            'deleted_files': self.deleted_files,
            'modified_files': self.modified_files,
            'patched_files': self.patched_files,
            'compression_ratio': self.compression_ratio,
            'estimated_time': self.estimated_time,
            'sha256_hash': self.sha256_hash
        }

class DownloadLog(Base):
    """下载日志表"""
    __tablename__ = 'download_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 客户端信息
    client_ip = Column(String(45))  # 支持IPv6
    user_agent = Column(String(500))
    client_version = Column(String(50))
    
    # 下载信息
    version_id = Column(Integer, ForeignKey('versions.id'))
    package_id = Column(Integer, ForeignKey('update_packages.id'))
    file_id = Column(Integer, ForeignKey('version_files.id'))
    
    # 下载状态
    download_type = Column(String(20))  # version_check, file_download, package_download
    status = Column(String(20))  # started, completed, failed, cancelled
    bytes_downloaded = Column(BigInteger, default=0)
    download_time = Column(Integer, default=0)  # 下载耗时（秒）
    
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
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # 默认使用SQLite数据库
            database_url = f"sqlite:///./update_server.db"
        
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
db_manager = DatabaseManager()

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
                ServerConfig(key="max_file_size", value="104857600", 
                           description="最大文件大小（字节）"),
                ServerConfig(key="enable_logging", value="true", 
                           description="是否启用日志记录"),
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
    print("数据库初始化完成")
