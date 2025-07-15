#!/usr/bin/env python3
"""
存储处理器模块.

处理存储状态监控、清理、版本管理等功能.
"""

import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import (
    APIEndpoints, AppConstants, LogManager, get_api_key, get_server_url
)


class StorageMonitor:
    """存储监控器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化存储监控器

        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.last_stats = None

    def get_storage_stats(self, callback: Optional[Callable] = None) -> bool:
        """
        获取存储统计信息

        Args:
            callback: 结果回调函数，接收 (usage_percentage, status) 参数

        Returns:
            是否成功启动请求
        """
        def fetch_stats() -> None:
            try:
                response = requests.get(
                    f"{get_server_url()}{APIEndpoints.STORAGE_STATS}",
                    timeout=AppConstants.REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    stats = response.json()
                    usage = stats.get('usage_percentage', 0)
                    status = stats.get('status', 'unknown')

                    self.last_stats = stats

                    if callback:
                        callback(usage, status)

                    if self.log_manager:
                        self.log_manager.log_info(f"存储状态: {usage:.1f}% ({status})")
                else:
                    if callback:
                        callback(0, 'error')

                    if self.log_manager:
                        self.log_manager.log_error(f"获取存储统计失败: HTTP {response.status_code}")

            except Exception as e:
                if callback:
                    callback(0, 'error')

                if self.log_manager:
                    self.log_manager.log_error(f"获取存储统计失败: {e}")

        threading.Thread(target=fetch_stats, daemon=True).start()
        return True

    def get_last_stats(self) -> Optional[Dict[str, Any]]:
        """获取最后一次的统计信息"""
        return self.last_stats


class StorageCleaner:
    """存储清理器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化存储清理器

        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager

    def cleanup_storage(self, callback: Optional[Callable] = None) -> bool:
        """
        执行存储清理

        Args:
            callback: 结果回调函数，接收 (success, message) 参数

        Returns:
            是否成功启动清理
        """
        def cleanup_thread() -> None:
            try:
                if self.log_manager:
                    self.log_manager.log_info("开始清理存储...")

                response = requests.post(
                    f"{get_server_url()}{APIEndpoints.STORAGE_CLEANUP}",
                    data={'api_key': get_api_key()},
                    timeout=AppConstants.REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    result = response.json()
                    message = result.get('message', '清理完成')

                    if callback:
                        callback(True, message)

                    if self.log_manager:
                        self.log_manager.log_success(f"存储清理成功: {message}")
                else:
                    error_msg = f"清理失败: HTTP {response.status_code}"

                    if callback:
                        callback(False, error_msg)

                    if self.log_manager:
                        self.log_manager.log_error(error_msg)

            except Exception as e:
                error_msg = f"清理存储失败: {e}"

                if callback:
                    callback(False, error_msg)

                if self.log_manager:
                    self.log_manager.log_error(error_msg)

        threading.Thread(target=cleanup_thread, daemon=True).start()
        return True


class PackageManager:
    """包管理器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化包管理器

        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager

    def get_packages_list(self, platform: str = "windows", arch: str = "x64",
                          limit: int = 50, callback: Optional[Callable] = None) -> bool:
        """
        获取包列表

        Args:
            platform: 平台
            arch: 架构
            limit: 限制数量
            callback: 结果回调函数，接收包列表参数

        Returns:
            是否成功启动请求
        """
        def fetch_packages() -> None:
            try:
                response = requests.get(
                    f"{get_server_url()}{APIEndpoints.PACKAGES_LIST}",
                    params={
                        'platform': platform,
                        'arch': arch,
                        'limit': str(limit)
                    },
                    headers={
                        'X-API-Key': get_api_key()
                    },
                    timeout=AppConstants.REQUEST_TIMEOUT
                )

                if response.status_code == 200:
                    response_data = response.json()

                    # 处理不同的响应格式
                    if isinstance(response_data, list):
                        # 服务器直接返回包列表
                        packages = response_data
                    elif isinstance(response_data, dict):
                        # 服务器返回包含packages键的字典
                        packages = response_data.get('packages', [])
                    else:
                        packages = []

                    if callback:
                        callback(packages)

                    if self.log_manager:
                        self.log_manager.log_info(f"获取到 {len(packages)} 个包")
                else:
                    error_msg = f"获取包列表失败: HTTP {response.status_code}"

                    if callback:
                        callback([])

                    if self.log_manager:
                        self.log_manager.log_error(error_msg)

            except Exception as e:
                error_msg = f"获取包列表失败: {e}"

                if callback:
                    callback([])

                if self.log_manager:
                    self.log_manager.log_error(error_msg)

        threading.Thread(target=fetch_packages, daemon=True).start()
        return True


class StorageHandler:
    """存储处理器主类"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化存储处理器

        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.monitor = StorageMonitor(log_manager)
        self.cleaner = StorageCleaner(log_manager)
        self.package_manager = PackageManager(log_manager)

    def get_storage_stats(self, callback: Optional[Callable] = None) -> bool:
        """获取存储统计信息"""
        return self.monitor.get_storage_stats(callback)

    def cleanup_storage(self, callback: Optional[Callable] = None) -> bool:
        """执行存储清理"""
        return self.cleaner.cleanup_storage(callback)

    def get_packages_list(self, platform: str = "windows", arch: str = "x64",
                          limit: int = 50, callback: Optional[Callable] = None) -> bool:
        """获取包列表"""
        return self.package_manager.get_packages_list(platform, arch, limit, callback)
