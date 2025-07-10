#!/usr/bin/env python3
"""
Omega更新器配置管理模块
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class UpdaterConfig:
    """更新器配置管理类"""
    
    def __init__(self, config_file: str = "updater_config.json"):
        self.config_file = Path(config_file)
        self.config = {}
        self.load_config()
        self.setup_logging()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            # 服务器配置
            "server_url": "https://your-update-server.com",
            "api_version": "v1",
            "timeout": 30,
            "max_retries": 3,
            "retry_delay": 2,
            
            # 应用配置
            "app_executable": "omega.exe",
            "app_directory": "./omega",
            "app_name": "Omega",
            "current_version": "1.7.3",
            
            # 更新配置
            "temp_directory": "./temp_update",
            "backup_directory": "./backup",
            "patch_directory": "./patches",
            "enable_incremental_update": True,
            "enable_binary_diff": True,
            "max_patch_size_mb": 100,
            
            # 下载配置
            "max_download_threads": 4,
            "chunk_size_kb": 1024,
            "enable_resume": True,
            "verify_checksums": True,
            
            # 自动更新配置
            "auto_check_interval": 3600,  # 秒
            "enable_auto_update": False,
            "enable_silent_update": False,
            "update_check_on_startup": True,
            
            # 日志配置
            "log_level": "INFO",
            "log_file": "updater.log",
            "max_log_size_mb": 10,
            "log_backup_count": 5,
            
            # 安全配置
            "verify_signatures": True,
            "public_key_file": "public_key.pem",
            "enable_https_only": True,
            
            # UI配置
            "show_progress": True,
            "show_details": False,
            "window_width": 500,
            "window_height": 300,
            "theme": "default"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logging.info(f"配置文件加载成功: {self.config_file}")
            except Exception as e:
                logging.error(f"配置文件加载失败: {e}")
        else:
            self.save_config(default_config)
            logging.info(f"创建默认配置文件: {self.config_file}")
        
        self.config = default_config
    
    def save_config(self, config: Dict[str, Any] = None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logging.info("配置文件保存成功")
        except Exception as e:
            logging.error(f"配置文件保存失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(updates)
    
    def setup_logging(self):
        """设置日志配置"""
        log_level = getattr(logging, self.get("log_level", "INFO").upper())
        log_file = self.get("log_file", "updater.log")
        
        # 创建日志目录
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.get("max_log_size_mb", 10) * 1024 * 1024,
            backupCount=self.get("log_backup_count", 5),
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    @property
    def server_url(self) -> str:
        """服务器URL"""
        return self.get("server_url")
    
    @property
    def api_base_url(self) -> str:
        """API基础URL"""
        return f"{self.server_url}/api/{self.get('api_version', 'v1')}"
    
    @property
    def app_path(self) -> Path:
        """应用程序路径"""
        return Path(self.get("app_directory")) / self.get("app_executable")
    
    @property
    def temp_path(self) -> Path:
        """临时目录路径"""
        return Path(self.get("temp_directory"))
    
    @property
    def backup_path(self) -> Path:
        """备份目录路径"""
        return Path(self.get("backup_directory"))
    
    @property
    def patch_path(self) -> Path:
        """补丁目录路径"""
        return Path(self.get("patch_directory"))
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.temp_path,
            self.backup_path,
            self.patch_path,
            Path(self.get("app_directory"))
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logging.debug(f"确保目录存在: {directory}")
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        required_keys = [
            "server_url", "app_executable", "app_directory"
        ]
        
        for key in required_keys:
            if not self.get(key):
                logging.error(f"缺少必需的配置项: {key}")
                return False
        
        # 验证URL格式
        server_url = self.get("server_url")
        if not (server_url.startswith("http://") or server_url.startswith("https://")):
            logging.error(f"无效的服务器URL: {server_url}")
            return False
        
        # 验证数值配置
        numeric_configs = {
            "timeout": (1, 300),
            "max_retries": (0, 10),
            "max_download_threads": (1, 16),
            "chunk_size_kb": (1, 10240)
        }
        
        for key, (min_val, max_val) in numeric_configs.items():
            value = self.get(key)
            if not isinstance(value, (int, float)) or not (min_val <= value <= max_val):
                logging.error(f"配置项 {key} 值无效: {value} (应在 {min_val}-{max_val} 范围内)")
                return False
        
        logging.info("配置验证通过")
        return True
    
    def get_version_info(self) -> Dict[str, str]:
        """获取版本信息"""
        version_file = Path(self.get("app_directory")) / "version.json"
        
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"读取版本文件失败: {e}")
        
        return {
            "version": self.get("current_version", "unknown"),
            "build_time": "unknown",
            "description": "Unknown version"
        }
    
    def update_version_info(self, version_info: Dict[str, str]):
        """更新版本信息"""
        version_file = Path(self.get("app_directory")) / "version.json"
        
        try:
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2, ensure_ascii=False)
            
            # 同时更新配置中的当前版本
            self.set("current_version", version_info.get("version", "unknown"))
            self.save_config()
            
            logging.info(f"版本信息更新成功: {version_info.get('version')}")
        except Exception as e:
            logging.error(f"更新版本信息失败: {e}")
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        if self.config_file.exists():
            backup_file = self.config_file.with_suffix('.bak')
            self.config_file.rename(backup_file)
            logging.info(f"配置文件已备份到: {backup_file}")
        
        self.load_config()
        logging.info("配置已重置为默认值")

# 全局配置实例
config = UpdaterConfig()
