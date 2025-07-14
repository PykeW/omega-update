#!/usr/bin/env python3
"""
下载管理器
支持最小化下载策略、断点续传和增量更新
"""

import os
import hashlib
import requests
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.difference_detector import FileChange, UpdatePlan, ChangeType


class DownloadStatus(Enum):
    """下载状态枚举"""
    PENDING = "pending"       # 等待下载
    DOWNLOADING = "downloading"  # 正在下载
    COMPLETED = "completed"   # 下载完成
    FAILED = "failed"         # 下载失败
    CANCELLED = "cancelled"   # 已取消
    SKIPPED = "skipped"       # 已跳过


@dataclass
class DownloadProgress:
    """下载进度信息"""
    current_file: str
    current_file_progress: float  # 0.0 - 1.0
    current_file_size: int
    current_file_downloaded: int
    overall_progress: float  # 0.0 - 1.0
    overall_size: int
    overall_downloaded: int
    download_speed: float  # bytes/sec
    eta_seconds: int
    files_completed: int
    files_total: int
    files_failed: int
    files_skipped: int
    status: DownloadStatus


class DownloadManager:
    """下载管理器"""
    
    def __init__(self, server_url: str, api_key: str, progress_callback: Optional[Callable] = None):
        """
        初始化下载管理器
        
        Args:
            server_url: 服务器URL
            api_key: API密钥
            progress_callback: 进度回调函数，接收DownloadProgress参数
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.progress_callback = progress_callback
        
        # 下载状态
        self.is_downloading = False
        self.is_cancelled = False
        self.is_paused = False
        
        # 进度跟踪
        self.current_file = ""
        self.current_file_size = 0
        self.current_file_downloaded = 0
        self.overall_size = 0
        self.overall_downloaded = 0
        self.files_completed = 0
        self.files_total = 0
        self.files_failed = 0
        self.files_skipped = 0
        
        # 速度计算
        self.speed_samples = []
        self.last_update_time = 0
        self.last_downloaded = 0
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 网络会话
        self.session = requests.Session()
        self.session.timeout = 30
    
    def start_download(self, update_plan: UpdatePlan, target_directory: str, 
                      selected_files: Optional[List[str]] = None) -> bool:
        """
        开始下载更新
        
        Args:
            update_plan: 更新计划
            target_directory: 目标目录
            selected_files: 选择下载的文件列表（相对路径），None表示下载所有
            
        Returns:
            是否成功开始下载
        """
        if self.is_downloading:
            return False
        
        with self._lock:
            self.is_downloading = True
            self.is_cancelled = False
            self.is_paused = False
            
            # 重置进度
            self._reset_progress()
            
            # 过滤要下载的文件
            files_to_download = update_plan.files_to_download
            if selected_files is not None:
                files_to_download = [f for f in files_to_download if f.relative_path in selected_files]
            
            self.files_total = len(files_to_download)
            self.overall_size = sum(f.file_size for f in files_to_download)
        
        # 在新线程中执行下载
        download_thread = threading.Thread(
            target=self._download_files,
            args=(files_to_download, target_directory, update_plan)
        )
        download_thread.daemon = True
        download_thread.start()
        
        return True
    
    def pause_download(self):
        """暂停下载"""
        with self._lock:
            self.is_paused = True
    
    def resume_download(self):
        """恢复下载"""
        with self._lock:
            self.is_paused = False
    
    def cancel_download(self):
        """取消下载"""
        with self._lock:
            self.is_cancelled = True
            self.is_paused = False
    
    def _reset_progress(self):
        """重置进度信息"""
        self.current_file = ""
        self.current_file_size = 0
        self.current_file_downloaded = 0
        self.overall_downloaded = 0
        self.files_completed = 0
        self.files_failed = 0
        self.files_skipped = 0
        self.speed_samples = []
        self.last_update_time = time.time()
        self.last_downloaded = 0
    
    def _download_files(self, files_to_download: List[FileChange], target_directory: str, update_plan: UpdatePlan):
        """
        下载文件列表（在单独线程中运行）
        
        Args:
            files_to_download: 要下载的文件列表
            target_directory: 目标目录
            update_plan: 更新计划
        """
        try:
            target_path = Path(target_directory)
            target_path.mkdir(parents=True, exist_ok=True)
            
            for file_change in files_to_download:
                # 检查是否被取消
                with self._lock:
                    if self.is_cancelled:
                        break
                
                # 等待暂停结束
                while True:
                    with self._lock:
                        if not self.is_paused or self.is_cancelled:
                            break
                    time.sleep(0.1)
                
                if self.is_cancelled:
                    break
                
                # 下载单个文件
                success = self._download_single_file(file_change, target_path, update_plan)
                
                with self._lock:
                    if success:
                        self.files_completed += 1
                    else:
                        self.files_failed += 1
                
                # 更新进度
                self._update_progress()
        
        finally:
            with self._lock:
                self.is_downloading = False
                # 最终进度更新
                self._update_progress()
    
    def _download_single_file(self, file_change: FileChange, target_path: Path, update_plan: UpdatePlan) -> bool:
        """
        下载单个文件
        
        Args:
            file_change: 文件变更信息
            target_path: 目标路径
            update_plan: 更新计划
            
        Returns:
            是否下载成功
        """
        try:
            # 更新当前文件信息
            with self._lock:
                self.current_file = file_change.relative_path
                self.current_file_size = file_change.file_size
                self.current_file_downloaded = 0
            
            # 构建目标文件路径
            file_path = target_path / file_change.relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查是否需要断点续传
            resume_pos = 0
            if file_path.exists():
                # 检查已下载部分的完整性
                existing_size = file_path.stat().st_size
                if existing_size < file_change.file_size:
                    # 验证已下载部分
                    if self._verify_partial_file(file_path, file_change.sha256_hash):
                        resume_pos = existing_size
                        with self._lock:
                            self.current_file_downloaded = resume_pos
                            self.overall_downloaded += resume_pos
                    else:
                        # 已下载部分损坏，重新下载
                        file_path.unlink()
                elif existing_size == file_change.file_size:
                    # 文件已存在，验证完整性
                    if self._verify_file_integrity(file_path, file_change.sha256_hash):
                        with self._lock:
                            self.current_file_downloaded = file_change.file_size
                            self.overall_downloaded += file_change.file_size
                            self.files_skipped += 1
                        return True
                    else:
                        # 文件损坏，重新下载
                        file_path.unlink()
            
            # 下载文件
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            response = self.session.get(
                f"{self.server_url}/api/v1/download/file",
                params={
                    "version": update_plan.target_version,
                    "platform": update_plan.platform,
                    "arch": update_plan.architecture,
                    "relative_path": file_change.relative_path,
                    "api_key": self.api_key
                },
                headers=headers,
                stream=True
            )
            
            if response.status_code not in [200, 206]:  # 206 for partial content
                raise Exception(f"下载失败: HTTP {response.status_code}")
            
            # 写入文件
            mode = 'ab' if resume_pos > 0 else 'wb'
            with open(file_path, mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # 检查是否被取消
                    with self._lock:
                        if self.is_cancelled:
                            return False
                    
                    # 等待暂停结束
                    while True:
                        with self._lock:
                            if not self.is_paused or self.is_cancelled:
                                break
                        time.sleep(0.1)
                    
                    if chunk:
                        f.write(chunk)
                        
                        # 更新进度
                        with self._lock:
                            self.current_file_downloaded += len(chunk)
                            self.overall_downloaded += len(chunk)
                        
                        # 更新进度回调
                        self._update_progress()
            
            # 验证下载的文件
            if not self._verify_file_integrity(file_path, file_change.sha256_hash):
                raise Exception("文件完整性验证失败")
            
            return True
            
        except Exception as e:
            print(f"下载文件失败 {file_change.relative_path}: {e}")
            return False
    
    def _verify_file_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """
        验证文件完整性
        
        Args:
            file_path: 文件路径
            expected_hash: 期望的SHA256哈希值
            
        Returns:
            是否验证通过
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest() == expected_hash
            
        except Exception:
            return False
    
    def _verify_partial_file(self, file_path: Path, expected_hash: str) -> bool:
        """
        验证部分下载文件的完整性（简化版本，实际应该更复杂）
        
        Args:
            file_path: 文件路径
            expected_hash: 期望的完整文件SHA256哈希值
            
        Returns:
            是否可以续传
        """
        # 简化实现：假设部分文件是有效的
        # 实际实现中应该有更复杂的验证逻辑
        return file_path.exists() and file_path.stat().st_size > 0
    
    def _calculate_speed_and_eta(self) -> tuple:
        """
        计算下载速度和预估剩余时间
        
        Returns:
            (速度 bytes/sec, 预估剩余时间 seconds)
        """
        current_time = time.time()
        
        # 计算速度
        if self.last_update_time > 0:
            time_diff = current_time - self.last_update_time
            bytes_diff = self.overall_downloaded - self.last_downloaded
            
            if time_diff > 0:
                current_speed = bytes_diff / time_diff
                
                # 保持最近10个样本的平均值
                self.speed_samples.append(current_speed)
                if len(self.speed_samples) > 10:
                    self.speed_samples.pop(0)
        
        # 更新记录
        self.last_update_time = current_time
        self.last_downloaded = self.overall_downloaded
        
        # 计算平均速度
        if self.speed_samples:
            avg_speed = sum(self.speed_samples) / len(self.speed_samples)
        else:
            avg_speed = 0
        
        # 计算ETA
        remaining_bytes = self.overall_size - self.overall_downloaded
        if avg_speed > 0:
            eta = int(remaining_bytes / avg_speed)
        else:
            eta = 0
        
        return avg_speed, eta
    
    def _update_progress(self):
        """更新进度并调用回调函数"""
        if not self.progress_callback:
            return
        
        with self._lock:
            # 计算进度
            if self.current_file_size > 0:
                current_file_progress = self.current_file_downloaded / self.current_file_size
            else:
                current_file_progress = 0.0
            
            if self.overall_size > 0:
                overall_progress = self.overall_downloaded / self.overall_size
            else:
                overall_progress = 0.0
            
            # 计算速度和ETA
            speed, eta = self._calculate_speed_and_eta()
            
            # 确定状态
            if self.is_cancelled:
                status = DownloadStatus.CANCELLED
            elif not self.is_downloading:
                status = DownloadStatus.COMPLETED
            elif self.is_paused:
                status = DownloadStatus.PENDING
            else:
                status = DownloadStatus.DOWNLOADING
            
            progress = DownloadProgress(
                current_file=self.current_file,
                current_file_progress=current_file_progress,
                current_file_size=self.current_file_size,
                current_file_downloaded=self.current_file_downloaded,
                overall_progress=overall_progress,
                overall_size=self.overall_size,
                overall_downloaded=self.overall_downloaded,
                download_speed=speed,
                eta_seconds=eta,
                files_completed=self.files_completed,
                files_total=self.files_total,
                files_failed=self.files_failed,
                files_skipped=self.files_skipped,
                status=status
            )
        
        # 调用回调函数
        try:
            self.progress_callback(progress)
        except Exception as e:
            print(f"进度回调函数错误: {e}")


# 测试代码
if __name__ == "__main__":
    def progress_callback(progress: DownloadProgress):
        print(f"进度: {progress.overall_progress:.1%} - "
              f"{progress.current_file} - "
              f"速度: {progress.download_speed/1024:.1f} KB/s")
    
    # 这里可以添加测试代码
    print("下载管理器模块已加载")
