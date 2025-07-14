#!/usr/bin/env python3
"""
Omega更新服务器配置文件
"""

import os
from pathlib import Path

class ServerConfig:
    """服务器配置类"""
    
    # 基础配置
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omega_updates.db")
    
    # 文件存储配置
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/var/www/omega-updates/uploads"))
    STATIC_DIR = Path(os.getenv("STATIC_DIR", "/var/www/omega-updates/static"))
    LOG_DIR = Path(os.getenv("LOG_DIR", "/var/log/omega-updates"))
    
    # 安全配置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    API_KEY = os.getenv("API_KEY", "dac450db3ec47d79196edb7a34defaed")
    
    # 更新包配置
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
    ALLOWED_EXTENSIONS = {'.zip', '.tar.gz', '.exe', '.msi'}
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Nginx配置
    NGINX_CONF_DIR = Path("/etc/nginx/sites-available")
    NGINX_ENABLED_DIR = Path("/etc/nginx/sites-enabled")
    
    # 服务配置
    SERVICE_NAME = "omega-update-server"
    SERVICE_USER = "omega"
    SERVICE_GROUP = "omega"
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        directories = [
            cls.UPLOAD_DIR,
            cls.STATIC_DIR,
            cls.LOG_DIR,
            cls.UPLOAD_DIR / "packages",
            cls.UPLOAD_DIR / "patches",
            cls.UPLOAD_DIR / "versions"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"确保目录存在: {directory}")
    
    @classmethod
    def get_env_template(cls):
        """获取环境变量模板"""
        return """# Omega更新服务器环境变量配置
# 复制此文件为 .env 并修改相应的值

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///./omega_updates.db
# 或使用PostgreSQL: postgresql://user:password@localhost/omega_updates

# 文件存储配置
UPLOAD_DIR=/var/www/omega-updates/uploads
STATIC_DIR=/var/www/omega-updates/static
LOG_DIR=/var/log/omega-updates

# 安全配置 (请修改为随机值)
SECRET_KEY=your-secret-key-change-this-to-random-string
API_KEY=your-api-key-change-this-to-random-string

# 文件上传配置
MAX_FILE_SIZE=104857600

# 日志配置
LOG_LEVEL=INFO
"""

if __name__ == "__main__":
    # 创建目录结构
    ServerConfig.ensure_directories()
    
    # 生成环境变量模板
    env_template = ServerConfig.get_env_template()
    with open(".env.template", "w", encoding="utf-8") as f:
        f.write(env_template)
    
    print("服务器配置初始化完成")
    print("请复制 .env.template 为 .env 并修改相应的配置值")
