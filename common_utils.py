#!/usr/bin/env python3
"""
Omega更新系统 - 公共工具模块
包含上传和下载工具共享的配置、工具函数和常量
"""

import json
import os
from pathlib import Path
from datetime import datetime


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        # 优先使用本地配置
        local_config_file = Path("local_server_config.json")
        if local_config_file.exists():
            with open(local_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 其次使用部署配置
        config_file = Path("deployment/server_config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "server": {
                    "ip": "localhost",
                    "domain": "localhost",
                    "port": 8000
                },
                "api": {
                    "key": "dac450db3ec47d79196edb7a34defaed"
                }
            }
    
    def get_server_url(self):
        """获取完整的服务器URL"""
        server_config = self.config["server"]
        ip = server_config["ip"]
        port = server_config["port"]
        
        if ip in ["localhost", "127.0.0.1"]:
            return f"http://{ip}:{port}"
        else:
            return f"http://{ip}:{port}"
    
    def get_api_key(self):
        """获取API密钥"""
        return self.config["api"]["key"]


class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def format_file_size(size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    @staticmethod
    def get_timestamp():
        """获取当前时间戳字符串"""
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def get_datetime_string():
        """获取当前日期时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_widget=None, log_file=None):
        """
        初始化日志管理器
        
        Args:
            log_widget: tkinter Text组件，用于GUI显示
            log_file: 日志文件路径
        """
        self.log_widget = log_widget
        self.log_file = log_file
    
    def log_message(self, message, level="INFO"):
        """
        记录日志消息
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        timestamp = FileUtils.get_timestamp()
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # 输出到GUI
        if self.log_widget:
            self.log_widget.insert("end", f"{formatted_message}\n")
            self.log_widget.see("end")
        
        # 输出到文件
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_message}\n")
            except Exception as e:
                print(f"写入日志文件失败: {e}")
        
        # 输出到控制台
        print(formatted_message)
    
    def log_info(self, message):
        """记录信息日志"""
        self.log_message(message, "INFO")
    
    def log_warning(self, message):
        """记录警告日志"""
        self.log_message(message, "WARNING")
    
    def log_error(self, message):
        """记录错误日志"""
        self.log_message(message, "ERROR")
    
    def log_success(self, message):
        """记录成功日志"""
        self.log_message(message, "SUCCESS")


class APIEndpoints:
    """API端点常量"""
    
    # 上传相关API
    UPLOAD_PACKAGE = "/api/v1/upload/package"
    UPLOAD_FILE = "/api/v1/upload/file"
    
    # 下载相关API
    FILES_LIST = "/api/v1/files/list"
    DOWNLOAD_FILE = "/api/v1/download/file"
    VERSION_COMPARE = "/api/v1/version/compare"
    
    # 存储管理API
    STORAGE_STATS = "/api/v1/storage/stats"
    STORAGE_CLEANUP = "/api/v1/storage/cleanup"
    STORAGE_STRUCTURE = "/api/v1/storage/structure"
    
    # 版本管理API
    PACKAGES_LIST = "/api/v1/packages"
    VERSION_CHECK = "/api/v1/version/check"
    VERSION_CHANGES = "/api/v1/version/changes"
    VERSION_ROLLBACK = "/api/v1/version/rollback"
    
    # 保留策略API
    RETENTION_APPLY = "/api/v1/storage/retention/apply"
    RETENTION_CONFIGURE = "/api/v1/storage/retention/configure"
    
    # 文件验证API
    FILE_VERIFY = "/api/v1/file/verify"
    
    # 健康检查API
    HEALTH = "/health"
    API_HEALTH = "/api/v1/health"


class AppConstants:
    """应用常量"""
    
    # 应用信息
    UPLOAD_TOOL_TITLE = "Omega更新服务器 - 上传工具 v3.0"
    DOWNLOAD_TOOL_TITLE = "Omega更新服务器 - 下载工具 v3.0"
    
    # 窗口大小
    UPLOAD_WINDOW_SIZE = "800x700"
    DOWNLOAD_WINDOW_SIZE = "900x700"
    
    # 包类型
    PACKAGE_TYPES = ["full", "patch", "hotfix"]
    PACKAGE_TYPE_NAMES = {
        "full": "完整包",
        "patch": "增量包", 
        "hotfix": "热修复包"
    }
    
    # 平台和架构
    PLATFORMS = ["windows", "linux", "macos"]
    ARCHITECTURES = ["x64", "x86", "arm64"]
    
    # 文件过滤
    EXCLUDE_PATTERNS = [
        '*.tmp', '*.temp', '*.log', '*.bak',
        '.git', '.svn', '__pycache__', '*.pyc',
        'Thumbs.db', '.DS_Store'
    ]
    
    # 网络设置
    REQUEST_TIMEOUT = 30
    UPLOAD_CHUNK_SIZE = 8192
    DOWNLOAD_CHUNK_SIZE = 8192
    
    # 进度更新间隔
    PROGRESS_UPDATE_INTERVAL = 100  # 毫秒


class NetworkUtils:
    """网络工具类"""
    
    @staticmethod
    def setup_proxy_environment():
        """设置代理环境变量"""
        # 禁用所有代理
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''
        os.environ['http_proxy'] = ''
        os.environ['https_proxy'] = ''
    
    @staticmethod
    def get_request_headers():
        """获取请求头"""
        return {
            'User-Agent': 'Omega-Update-Tool/3.0',
            'Accept': 'application/json',
        }


class ValidationUtils:
    """验证工具类"""
    
    @staticmethod
    def validate_version_format(version):
        """验证版本号格式"""
        if not version or not version.strip():
            return False, "版本号不能为空"
        
        # 简单的版本号格式检查
        version = version.strip()
        if len(version) > 50:
            return False, "版本号过长"
        
        # 检查是否包含非法字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in version:
                return False, f"版本号不能包含字符: {char}"
        
        return True, ""
    
    @staticmethod
    def validate_description(description):
        """验证描述格式"""
        if len(description) > 500:
            return False, "描述过长（最多500字符）"
        return True, ""
    
    @staticmethod
    def validate_folder_path(folder_path):
        """验证文件夹路径"""
        if not folder_path or not folder_path.strip():
            return False, "请选择文件夹"
        
        path = Path(folder_path)
        if not path.exists():
            return False, "文件夹不存在"
        
        if not path.is_dir():
            return False, "路径不是文件夹"
        
        return True, ""


# 全局配置管理器实例
config_manager = ConfigManager()

# 设置网络环境
NetworkUtils.setup_proxy_environment()


def get_config():
    """获取全局配置"""
    return config_manager.config


def get_server_url():
    """获取服务器URL"""
    return config_manager.get_server_url()


def get_api_key():
    """获取API密钥"""
    return config_manager.get_api_key()


# 测试代码
if __name__ == "__main__":
    print("=== 公共工具模块测试 ===")
    
    # 测试配置管理
    print(f"服务器URL: {get_server_url()}")
    print(f"API密钥: {get_api_key()}")
    
    # 测试文件工具
    print(f"文件大小格式化: {FileUtils.format_file_size(1024*1024*1.5)}")
    print(f"当前时间: {FileUtils.get_timestamp()}")
    
    # 测试验证工具
    valid, msg = ValidationUtils.validate_version_format("v1.0.0")
    print(f"版本验证: {valid}, {msg}")
    
    print("=== 测试完成 ===")
