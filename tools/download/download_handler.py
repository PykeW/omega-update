#!/usr/bin/env python3
"""
下载业务逻辑处理器
处理文件下载、更新检查等核心业务逻辑
"""

import threading
from typing import Dict, List, Optional, Callable
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import (
    get_server_url, get_api_key, LogManager, ValidationUtils
)
from tools.download.local_file_scanner import LocalFileScanner, FileInfo
from tools.common.difference_detector import DifferenceDetector, UpdatePlan
from tools.download.download_manager import DownloadManager, DownloadStatus


class LocalFileScanHandler:
    """本地文件扫描处理器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化扫描处理器
        
        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.scanner = None
        self.scan_results = {}
    
    def start_scan(self, folder_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """
        开始扫描本地文件
        
        Args:
            folder_path: 文件夹路径
            progress_callback: 进度回调函数
            
        Returns:
            是否成功启动扫描
        """
        # 验证文件夹路径
        valid, msg = ValidationUtils.validate_folder_path(folder_path)
        if not valid:
            if self.log_manager:
                self.log_manager.log_error(f"文件夹路径无效: {msg}")
            return False
        
        if self.log_manager:
            self.log_manager.log_info("开始扫描本地文件...")
        
        # 在新线程中扫描文件
        def scan_thread():
            try:
                def internal_progress_callback(current, total, current_file):
                    if progress_callback:
                        progress_callback(current, total, current_file)
                    if self.log_manager:
                        self.log_manager.log_info(f"扫描进度: {current}/{total} - {current_file}")
                
                self.scanner = LocalFileScanner(internal_progress_callback)
                self.scan_results = self.scanner.scan_directory(folder_path)
                
                if self.log_manager:
                    self.log_manager.log_info(f"扫描完成，共找到 {len(self.scan_results)} 个文件")
                
            except Exception as e:
                if self.log_manager:
                    self.log_manager.log_error(f"扫描本地文件失败: {e}")
        
        threading.Thread(target=scan_thread, daemon=True).start()
        return True
    
    def cancel_scan(self):
        """取消扫描"""
        if self.scanner:
            self.scanner.cancel_scan()
    
    def get_scan_results(self) -> Dict[str, FileInfo]:
        """获取扫描结果"""
        return self.scan_results
    
    def clear_results(self):
        """清空扫描结果"""
        self.scan_results = {}


class UpdateChecker:
    """更新检查器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化更新检查器
        
        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.detector = DifferenceDetector(get_server_url(), get_api_key())
        self.update_plan = None
    
    def check_for_updates(self, local_files: Dict[str, FileInfo], target_version: str,
                         platform: str = "windows", arch: str = "x64",
                         result_callback: Optional[Callable] = None) -> bool:
        """
        检查更新
        
        Args:
            local_files: 本地文件信息
            target_version: 目标版本
            platform: 平台
            arch: 架构
            result_callback: 结果回调函数
            
        Returns:
            是否成功启动检查
        """
        if not local_files:
            if self.log_manager:
                self.log_manager.log_error("没有本地文件信息")
            return False
        
        if not target_version.strip():
            if self.log_manager:
                self.log_manager.log_error("目标版本号不能为空")
            return False
        
        if self.log_manager:
            self.log_manager.log_info(f"检查版本 {target_version} 的更新...")
        
        # 在新线程中检查更新
        def check_thread():
            try:
                self.update_plan = self.detector.detect_differences(
                    local_files, target_version, platform, arch
                )
                
                if result_callback:
                    result_callback(self.update_plan)
                
                if self.log_manager:
                    summary = self.update_plan.get_summary()
                    summary_text = (f"目标版本: {summary['target_version']} | "
                                   f"需要下载: {summary['files_to_download']} 个文件 "
                                   f"({summary['download_size_mb']} MB) | "
                                   f"相同文件: {summary['files_same']} 个 | "
                                   f"需要删除: {summary['files_to_delete']} 个")
                    self.log_manager.log_info(f"更新检查完成: {summary_text}")
                
            except Exception as e:
                if self.log_manager:
                    self.log_manager.log_error(f"检查更新失败: {e}")
        
        threading.Thread(target=check_thread, daemon=True).start()
        return True
    
    def get_update_plan(self) -> Optional[UpdatePlan]:
        """获取更新计划"""
        return self.update_plan
    
    def clear_update_plan(self):
        """清空更新计划"""
        self.update_plan = None


class DownloadController:
    """下载控制器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化下载控制器
        
        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.download_manager = None
        self.is_downloading = False
    
    def start_download(self, update_plan: UpdatePlan, target_directory: str,
                      selected_files: Optional[List[str]] = None,
                      progress_callback: Optional[Callable] = None) -> bool:
        """
        开始下载
        
        Args:
            update_plan: 更新计划
            target_directory: 目标目录
            selected_files: 选择的文件列表
            progress_callback: 进度回调函数
            
        Returns:
            是否成功启动下载
        """
        if self.is_downloading:
            if self.log_manager:
                self.log_manager.log_warning("已有下载任务在进行")
            return False
        
        if not update_plan:
            if self.log_manager:
                self.log_manager.log_error("没有可用的更新计划")
            return False
        
        # 验证目标目录
        valid, msg = ValidationUtils.validate_folder_path(target_directory)
        if not valid:
            if self.log_manager:
                self.log_manager.log_error(f"目标目录无效: {msg}")
            return False
        
        try:
            self.download_manager = DownloadManager(
                get_server_url(), get_api_key(), progress_callback
            )
            
            success = self.download_manager.start_download(
                update_plan, target_directory, selected_files
            )
            
            if success:
                self.is_downloading = True
                if self.log_manager:
                    self.log_manager.log_info("开始下载...")
                return True
            else:
                if self.log_manager:
                    self.log_manager.log_error("无法开始下载")
                return False
                
        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"启动下载失败: {e}")
            return False
    
    def pause_download(self):
        """暂停下载"""
        if self.download_manager:
            self.download_manager.pause_download()
            if self.log_manager:
                self.log_manager.log_info("下载已暂停")
    
    def resume_download(self):
        """恢复下载"""
        if self.download_manager:
            self.download_manager.resume_download()
            if self.log_manager:
                self.log_manager.log_info("下载已恢复")
    
    def cancel_download(self):
        """取消下载"""
        if self.download_manager:
            self.download_manager.cancel_download()
            self.is_downloading = False
            if self.log_manager:
                self.log_manager.log_info("下载已取消")
    
    def is_download_active(self) -> bool:
        """检查是否有活跃的下载"""
        return self.is_downloading and self.download_manager and self.download_manager.is_downloading
    
    def get_download_manager(self) -> Optional[DownloadManager]:
        """获取下载管理器"""
        return self.download_manager


class DownloadHandler:
    """下载业务逻辑处理器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化下载处理器
        
        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.scan_handler = LocalFileScanHandler(log_manager)
        self.update_checker = UpdateChecker(log_manager)
        self.download_controller = DownloadController(log_manager)
    
    def scan_local_files(self, folder_path: str, 
                        progress_callback: Optional[Callable] = None) -> bool:
        """
        扫描本地文件
        
        Args:
            folder_path: 文件夹路径
            progress_callback: 进度回调函数
            
        Returns:
            是否成功启动扫描
        """
        return self.scan_handler.start_scan(folder_path, progress_callback)
    
    def get_local_files(self) -> Dict[str, FileInfo]:
        """获取本地文件扫描结果"""
        return self.scan_handler.get_scan_results()
    
    def check_for_updates(self, target_version: str, platform: str = "windows", 
                         arch: str = "x64", result_callback: Optional[Callable] = None) -> bool:
        """
        检查更新
        
        Args:
            target_version: 目标版本
            platform: 平台
            arch: 架构
            result_callback: 结果回调函数
            
        Returns:
            是否成功启动检查
        """
        local_files = self.scan_handler.get_scan_results()
        return self.update_checker.check_for_updates(
            local_files, target_version, platform, arch, result_callback
        )
    
    def get_update_plan(self) -> Optional[UpdatePlan]:
        """获取更新计划"""
        return self.update_checker.get_update_plan()
    
    def start_download(self, target_directory: str, selected_files: Optional[List[str]] = None,
                      progress_callback: Optional[Callable] = None) -> bool:
        """
        开始下载
        
        Args:
            target_directory: 目标目录
            selected_files: 选择的文件列表
            progress_callback: 进度回调函数
            
        Returns:
            是否成功启动下载
        """
        update_plan = self.update_checker.get_update_plan()
        return self.download_controller.start_download(
            update_plan, target_directory, selected_files, progress_callback
        )
    
    def pause_download(self):
        """暂停下载"""
        self.download_controller.pause_download()
    
    def resume_download(self):
        """恢复下载"""
        self.download_controller.resume_download()
    
    def cancel_download(self):
        """取消下载"""
        self.download_controller.cancel_download()
    
    def is_download_active(self) -> bool:
        """检查是否有活跃的下载"""
        return self.download_controller.is_download_active()
    
    def clear_all_data(self):
        """清空所有数据"""
        self.scan_handler.clear_results()
        self.update_checker.clear_update_plan()
        self.download_controller.cancel_download()
