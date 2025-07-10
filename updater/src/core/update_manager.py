#!/usr/bin/env python3
"""
Omega更新管理器核心模块
负责版本检查、下载更新、应用补丁等核心更新功能
"""

import json
import hashlib
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import threading
import time

from .config import config
from .app_manager import ApplicationManager

class UpdateInfo:
    """更新信息类"""
    
    def __init__(self, data: Dict):
        self.version = data.get("version", "")
        self.description = data.get("description", "")
        self.release_date = data.get("release_date", "")
        self.file_size = data.get("file_size", 0)
        self.download_url = data.get("download_url", "")
        self.checksum = data.get("checksum", "")
        self.is_critical = data.get("is_critical", False)
        self.min_version = data.get("min_version", "")
        self.files = data.get("files", [])
        self.patches = data.get("patches", [])
        self.raw_data = data
    
    def __str__(self):
        return f"UpdateInfo(version={self.version}, size={self.file_size})"

class DownloadProgress:
    """下载进度信息"""
    
    def __init__(self):
        self.total_size = 0
        self.downloaded_size = 0
        self.speed = 0
        self.eta = 0
        self.current_file = ""
        self.completed_files = 0
        self.total_files = 0
        self.status = "准备中"
        self.error = None

class UpdateManager:
    """更新管理器"""
    
    def __init__(self):
        self.config = config
        self.app_manager = ApplicationManager()
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.timeout = self.config.get("timeout", 30)
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': f'OmegaUpdater/{self.config.get("current_version", "1.0")}',
            'Accept': 'application/json'
        })
        
        # 进度回调
        self.progress_callback: Optional[Callable[[DownloadProgress], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None
        
        # 下载状态
        self.is_downloading = False
        self.download_cancelled = False
    
    def set_progress_callback(self, callback: Callable[[DownloadProgress], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """设置状态回调函数"""
        self.status_callback = callback
    
    def _update_status(self, status: str):
        """更新状态"""
        self.logger.info(status)
        if self.status_callback:
            self.status_callback(status)
    
    def check_for_updates(self) -> Tuple[bool, Optional[UpdateInfo]]:
        """
        检查是否有可用更新
        
        Returns:
            Tuple[bool, Optional[UpdateInfo]]: (是否有更新, 更新信息)
        """
        try:
            self._update_status("检查更新...")
            
            current_version = self.app_manager.get_app_version()
            api_url = f"{self.config.api_base_url}/version/check"
            
            params = {
                'current_version': current_version,
                'platform': 'windows',
                'arch': 'x64'
            }
            
            self.logger.info(f"检查更新: {api_url}")
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("has_update", False):
                update_info = UpdateInfo(data.get("update_info", {}))
                self.logger.info(f"发现新版本: {update_info.version}")
                return True, update_info
            else:
                self.logger.info("已是最新版本")
                return False, None
                
        except requests.RequestException as e:
            self.logger.error(f"网络请求失败: {e}")
            return False, None
        except Exception as e:
            self.logger.error(f"检查更新失败: {e}")
            return False, None
    
    def download_file(self, url: str, local_path: Path, 
                     expected_size: int = 0, checksum: str = "") -> bool:
        """
        下载单个文件
        
        Args:
            url: 下载URL
            local_path: 本地保存路径
            expected_size: 预期文件大小
            checksum: 预期校验和
            
        Returns:
            bool: 是否下载成功
        """
        try:
            # 确保目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查是否支持断点续传
            resume_pos = 0
            if local_path.exists() and self.config.get("enable_resume", True):
                resume_pos = local_path.stat().st_size
                if resume_pos >= expected_size:
                    self.logger.info(f"文件已存在，跳过下载: {local_path.name}")
                    return True
            
            # 设置请求头
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
                self.logger.info(f"断点续传，从位置 {resume_pos} 开始")
            
            # 开始下载
            response = self.session.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # 获取文件大小
            content_length = response.headers.get('content-length')
            if content_length:
                total_size = int(content_length) + resume_pos
            else:
                total_size = expected_size
            
            # 下载文件
            mode = 'ab' if resume_pos > 0 else 'wb'
            downloaded = resume_pos
            start_time = time.time()
            
            with open(local_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.download_cancelled:
                        self.logger.info("下载已取消")
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if self.progress_callback:
                            progress = DownloadProgress()
                            progress.total_size = total_size
                            progress.downloaded_size = downloaded
                            progress.current_file = local_path.name
                            
                            # 计算速度和ETA
                            elapsed = time.time() - start_time
                            if elapsed > 0:
                                progress.speed = downloaded / elapsed
                                if progress.speed > 0:
                                    remaining = (total_size - downloaded) / progress.speed
                                    progress.eta = remaining
                            
                            self.progress_callback(progress)
            
            # 验证文件大小
            if expected_size > 0:
                actual_size = local_path.stat().st_size
                if actual_size != expected_size:
                    self.logger.error(f"文件大小不匹配: 期望 {expected_size}, 实际 {actual_size}")
                    return False
            
            # 验证校验和
            if checksum and self.config.get("verify_checksums", True):
                if not self._verify_checksum(local_path, checksum):
                    self.logger.error(f"文件校验失败: {local_path.name}")
                    return False
            
            self.logger.info(f"文件下载成功: {local_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"下载文件失败 {url}: {e}")
            return False
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """验证文件校验和"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
            
        except Exception as e:
            self.logger.error(f"计算校验和失败: {e}")
            return False
    
    def download_update(self, update_info: UpdateInfo) -> bool:
        """
        下载更新包
        
        Args:
            update_info: 更新信息
            
        Returns:
            bool: 是否下载成功
        """
        try:
            self.is_downloading = True
            self.download_cancelled = False
            
            self._update_status(f"开始下载版本 {update_info.version}")
            
            # 清理临时目录
            temp_dir = self.config.temp_path
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载文件列表
            success = True
            for file_info in update_info.files:
                file_url = file_info.get("url", "")
                file_name = file_info.get("name", "")
                file_size = file_info.get("size", 0)
                file_checksum = file_info.get("checksum", "")
                
                if not file_url or not file_name:
                    continue
                
                local_path = temp_dir / file_name
                
                self.logger.info(f"下载文件: {file_name}")
                if not self.download_file(file_url, local_path, file_size, file_checksum):
                    success = False
                    break
            
            # 下载补丁文件
            if success and update_info.patches:
                for patch_info in update_info.patches:
                    patch_url = patch_info.get("url", "")
                    patch_name = patch_info.get("name", "")
                    patch_size = patch_info.get("size", 0)
                    patch_checksum = patch_info.get("checksum", "")
                    
                    if not patch_url or not patch_name:
                        continue
                    
                    local_path = temp_dir / patch_name
                    
                    self.logger.info(f"下载补丁: {patch_name}")
                    if not self.download_file(patch_url, local_path, patch_size, patch_checksum):
                        success = False
                        break
            
            if success:
                self._update_status("下载完成")
                self.logger.info("更新包下载成功")
            else:
                self._update_status("下载失败")
                self.logger.error("更新包下载失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"下载更新失败: {e}")
            return False
        finally:
            self.is_downloading = False
    
    def cancel_download(self):
        """取消下载"""
        self.download_cancelled = True
        self._update_status("正在取消下载...")
    
    def apply_update(self, update_info: UpdateInfo) -> bool:
        """
        应用更新
        
        Args:
            update_info: 更新信息
            
        Returns:
            bool: 是否应用成功
        """
        try:
            self._update_status("准备应用更新...")
            
            # 创建备份
            backup_path = self.app_manager.create_backup(f"before_{update_info.version}")
            if not backup_path:
                self.logger.error("创建备份失败")
                return False
            
            # 关闭应用程序
            self._update_status("关闭应用程序...")
            if not self.app_manager.close_app_gracefully():
                self.logger.error("无法关闭应用程序")
                return False
            
            # 应用更新文件
            self._update_status("应用更新文件...")
            if not self._apply_files(update_info):
                self.logger.error("应用文件更新失败")
                # 尝试恢复备份
                self.app_manager.restore_from_backup(backup_path)
                return False
            
            # 应用补丁
            if update_info.patches:
                self._update_status("应用补丁...")
                if not self._apply_patches(update_info):
                    self.logger.error("应用补丁失败")
                    # 尝试恢复备份
                    self.app_manager.restore_from_backup(backup_path)
                    return False
            
            # 更新版本信息
            version_info = {
                "version": update_info.version,
                "build_time": datetime.now().isoformat(),
                "description": update_info.description,
                "update_time": datetime.now().isoformat()
            }
            self.config.update_version_info(version_info)
            
            self._update_status("更新完成")
            self.logger.info(f"更新应用成功: {update_info.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"应用更新失败: {e}")
            return False
    
    def _apply_files(self, update_info: UpdateInfo) -> bool:
        """应用文件更新"""
        try:
            temp_dir = self.config.temp_path
            app_dir = Path(self.config.get("app_directory"))
            
            for file_info in update_info.files:
                file_name = file_info.get("name", "")
                target_path = file_info.get("path", "")
                
                if not file_name:
                    continue
                
                source_file = temp_dir / file_name
                if not source_file.exists():
                    self.logger.warning(f"源文件不存在: {file_name}")
                    continue
                
                # 确定目标路径
                if target_path:
                    dest_file = app_dir / target_path
                else:
                    dest_file = app_dir / file_name
                
                # 确保目标目录存在
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                import shutil
                shutil.copy2(source_file, dest_file)
                self.logger.debug(f"文件已更新: {dest_file}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"应用文件更新失败: {e}")
            return False
    
    def _apply_patches(self, update_info: UpdateInfo) -> bool:
        """应用补丁文件"""
        try:
            # 这里需要实现二进制补丁应用逻辑
            # 暂时返回True，在下一个任务中实现
            self.logger.info("补丁应用功能将在增量更新模块中实现")
            return True
            
        except Exception as e:
            self.logger.error(f"应用补丁失败: {e}")
            return False
    
    def perform_update(self, update_info: UpdateInfo) -> bool:
        """
        执行完整的更新流程
        
        Args:
            update_info: 更新信息
            
        Returns:
            bool: 是否更新成功
        """
        try:
            self.logger.info(f"开始更新到版本: {update_info.version}")
            
            # 下载更新
            if not self.download_update(update_info):
                return False
            
            # 应用更新
            if not self.apply_update(update_info):
                return False
            
            self.logger.info("更新流程完成")
            return True
            
        except Exception as e:
            self.logger.error(f"更新流程失败: {e}")
            return False
