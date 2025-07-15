#!/usr/bin/env python3
"""
增量上传器
实现智能文件差异对比和增量上传功能
"""

import os
import hashlib
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import get_server_url, get_api_key, FileUtils, LogManager


class ChangeType(Enum):
    """文件变化类型"""
    NEW = "new"           # 新增文件
    MODIFIED = "modified" # 修改文件
    DELETED = "deleted"   # 删除文件
    SAME = "same"         # 相同文件


@dataclass
class FileInfo:
    """文件信息"""
    relative_path: str
    file_size: int
    sha256_hash: str
    modified_time: Optional[datetime] = None
    storage_path: Optional[str] = None


@dataclass
class FileDifference:
    """文件差异"""
    relative_path: str
    change_type: ChangeType
    local_info: Optional[FileInfo] = None
    remote_info: Optional[FileInfo] = None


@dataclass
class DifferenceReport:
    """差异报告"""
    new_files: List[FileDifference]
    modified_files: List[FileDifference]
    deleted_files: List[FileDifference]
    same_files: List[FileDifference]
    total_upload_size: int
    total_files_to_upload: int
    total_files_to_delete: int


class LocalFileScanner:
    """本地文件扫描器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        self.log_manager = log_manager

    def scan_folder(self, folder_path: str) -> Dict[str, FileInfo]:
        """
        扫描本地文件夹，生成文件信息字典

        Args:
            folder_path: 文件夹路径

        Returns:
            文件相对路径到文件信息的映射
        """
        folder_path_obj = Path(folder_path)
        if not folder_path_obj.exists() or not folder_path_obj.is_dir():
            if self.log_manager:
                self.log_manager.log_error(f"文件夹不存在或不是有效目录: {folder_path}")
            return {}

        file_map = {}

        for root, dirs, files in os.walk(folder_path_obj):
            for file in files:
                file_path = Path(root) / file
                try:
                    relative_path = file_path.relative_to(folder_path_obj)
                    relative_path_str = str(relative_path).replace('\\', '/')

                    # 计算文件哈希
                    sha256_hash = self._calculate_file_hash(file_path)

                    # 获取文件信息
                    stat = file_path.stat()
                    file_info = FileInfo(
                        relative_path=relative_path_str,
                        file_size=stat.st_size,
                        sha256_hash=sha256_hash,
                        modified_time=datetime.fromtimestamp(stat.st_mtime)
                    )

                    file_map[relative_path_str] = file_info

                except Exception as e:
                    if self.log_manager:
                        self.log_manager.log_warning(f"跳过文件 {file_path}: {e}")
                    continue

        if self.log_manager:
            self.log_manager.log_info(f"扫描完成，找到 {len(file_map)} 个文件")

        return file_map

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception:
            return ""


class RemoteFileRetriever:
    """远程文件信息获取器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        self.log_manager = log_manager

    def get_remote_files(self, version_type: str, platform: str = "windows",
                        architecture: str = "x64") -> Dict[str, FileInfo]:
        """
        获取远程文件列表

        Args:
            version_type: 版本类型
            platform: 平台
            architecture: 架构

        Returns:
            文件相对路径到文件信息的映射
        """
        try:
            url = f"{get_server_url()}/api/v2/files/simple/{version_type}"
            params = {
                "platform": platform,
                "architecture": architecture
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 404:
                # 版本不存在，返回空字典
                if self.log_manager:
                    self.log_manager.log_info(f"远程版本不存在: {version_type}")
                return {}

            if response.status_code != 200:
                raise Exception(f"获取远程文件列表失败: {response.status_code}")

            data = response.json()
            files = data.get("files", [])

            file_map = {}
            for file_data in files:
                file_info = FileInfo(
                    relative_path=file_data["relative_path"],
                    file_size=file_data["file_size"],
                    sha256_hash=file_data["file_hash"],
                    storage_path=file_data.get("storage_path")
                )
                file_map[file_data["relative_path"]] = file_info

            if self.log_manager:
                self.log_manager.log_info(f"获取远程文件列表成功，共 {len(file_map)} 个文件")

            return file_map

        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"获取远程文件列表失败: {e}")
            return {}


class DifferenceAnalyzer:
    """差异分析器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        self.log_manager = log_manager

    def analyze_differences(self, local_files: Dict[str, FileInfo],
                          remote_files: Dict[str, FileInfo]) -> DifferenceReport:
        """
        分析本地和远程文件的差异

        Args:
            local_files: 本地文件信息
            remote_files: 远程文件信息

        Returns:
            差异报告
        """
        new_files = []
        modified_files = []
        deleted_files = []
        same_files = []

        total_upload_size = 0

        # 检查本地文件
        for path, local_info in local_files.items():
            if path not in remote_files:
                # 新增文件
                diff = FileDifference(
                    relative_path=path,
                    change_type=ChangeType.NEW,
                    local_info=local_info
                )
                new_files.append(diff)
                total_upload_size += local_info.file_size
            else:
                remote_info = remote_files[path]
                if local_info.sha256_hash != remote_info.sha256_hash:
                    # 修改文件
                    diff = FileDifference(
                        relative_path=path,
                        change_type=ChangeType.MODIFIED,
                        local_info=local_info,
                        remote_info=remote_info
                    )
                    modified_files.append(diff)
                    total_upload_size += local_info.file_size
                else:
                    # 相同文件
                    diff = FileDifference(
                        relative_path=path,
                        change_type=ChangeType.SAME,
                        local_info=local_info,
                        remote_info=remote_info
                    )
                    same_files.append(diff)

        # 检查远程独有文件（需要删除）
        for path, remote_info in remote_files.items():
            if path not in local_files:
                diff = FileDifference(
                    relative_path=path,
                    change_type=ChangeType.DELETED,
                    remote_info=remote_info
                )
                deleted_files.append(diff)

        report = DifferenceReport(
            new_files=new_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            same_files=same_files,
            total_upload_size=total_upload_size,
            total_files_to_upload=len(new_files) + len(modified_files),
            total_files_to_delete=len(deleted_files)
        )

        if self.log_manager:
            self.log_manager.log_info(
                f"差异分析完成: 新增{len(new_files)}, 修改{len(modified_files)}, "
                f"删除{len(deleted_files)}, 相同{len(same_files)}"
            )

        return report


class IncrementalUploader:
    """增量上传器"""

    def __init__(self, log_manager: Optional[LogManager] = None):
        self.log_manager = log_manager
        self.local_scanner = LocalFileScanner(log_manager)
        self.remote_retriever = RemoteFileRetriever(log_manager)
        self.difference_analyzer = DifferenceAnalyzer(log_manager)
        self.is_cancelled = False

    def analyze_folder_differences(self, folder_path: str, version_type: str,
                                 platform: str = "windows", architecture: str = "x64") -> DifferenceReport:
        """
        分析文件夹与远程版本的差异

        Args:
            folder_path: 本地文件夹路径
            version_type: 版本类型
            platform: 平台
            architecture: 架构

        Returns:
            差异报告
        """
        if self.log_manager:
            self.log_manager.log_info(f"开始分析文件夹差异: {folder_path}")

        # 扫描本地文件
        local_files = self.local_scanner.scan_folder(folder_path)

        # 获取远程文件
        remote_files = self.remote_retriever.get_remote_files(version_type, platform, architecture)

        # 分析差异
        return self.difference_analyzer.analyze_differences(local_files, remote_files)

    def perform_incremental_upload(self, folder_path: str, version_type: str,
                                  platform: str = "windows", architecture: str = "x64",
                                  description: str = "", enable_sync: bool = True,
                                  progress_callback: Optional[Callable] = None) -> bool:
        """
        执行增量上传

        Args:
            folder_path: 本地文件夹路径
            version_type: 版本类型
            platform: 平台
            architecture: 架构
            description: 版本描述
            enable_sync: 是否启用云端文件同步（删除多余文件）
            progress_callback: 进度回调函数

        Returns:
            是否成功
        """
        try:
            # 分析差异
            if progress_callback:
                progress_callback(0, "分析文件差异...")

            report = self.analyze_folder_differences(folder_path, version_type, platform, architecture)

            if self.is_cancelled:
                return False

            total_operations = report.total_files_to_upload + (report.total_files_to_delete if enable_sync else 0)
            if total_operations == 0:
                if progress_callback:
                    progress_callback(100, "没有需要更新的文件")
                if self.log_manager:
                    self.log_manager.log_info("没有需要更新的文件")
                return True

            completed_operations = 0

            # 上传新增和修改的文件
            for file_diff in report.new_files + report.modified_files:
                if self.is_cancelled:
                    return False

                local_file_path = Path(folder_path) / file_diff.relative_path

                if progress_callback:
                    action = "新增" if file_diff.change_type == ChangeType.NEW else "更新"
                    progress_callback(
                        (completed_operations / total_operations) * 100,
                        f"{action}: {file_diff.relative_path}"
                    )

                success = self._upload_single_file(
                    local_file_path, file_diff.relative_path,
                    version_type, platform, architecture, description
                )

                if success:
                    if self.log_manager:
                        action = "新增" if file_diff.change_type == ChangeType.NEW else "更新"
                        self.log_manager.log_success(f"{action}文件成功: {file_diff.relative_path}")
                else:
                    if self.log_manager:
                        self.log_manager.log_error(f"上传文件失败: {file_diff.relative_path}")

                completed_operations += 1

            # 同步删除云端多余文件
            if enable_sync and report.deleted_files:
                if progress_callback:
                    progress_callback(
                        (completed_operations / total_operations) * 100,
                        "同步删除云端多余文件..."
                    )

                success = self._sync_remote_files(
                    version_type, platform, architecture,
                    [diff.local_info for diff in report.new_files + report.modified_files + report.same_files if diff.local_info]
                )

                if success:
                    if self.log_manager:
                        self.log_manager.log_success(f"同步删除了 {len(report.deleted_files)} 个多余文件")
                else:
                    if self.log_manager:
                        self.log_manager.log_warning("同步删除文件失败")

                completed_operations += len(report.deleted_files)

            if progress_callback:
                progress_callback(100, "增量上传完成")

            if self.log_manager:
                self.log_manager.log_success(
                    f"增量上传完成: 上传{report.total_files_to_upload}个文件, "
                    f"删除{report.total_files_to_delete if enable_sync else 0}个文件"
                )

            return True

        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"增量上传失败: {e}")
            return False

    def _upload_single_file(self, file_path: Path, relative_path: str,
                           version_type: str, platform: str, architecture: str,
                           description: str) -> bool:
        """上传单个文件"""
        try:
            # 计算文件哈希
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            file_hash = sha256_hash.hexdigest()

            # 准备上传数据
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {
                    'version_type': version_type,
                    'platform': platform,
                    'architecture': architecture,
                    'relative_path': relative_path,
                    'description': description,
                    'api_key': get_api_key(),
                    'file_hash': file_hash
                }

                # 发送请求
                response = requests.post(
                    f"{get_server_url()}/api/v2/upload/simple/file",
                    files=files,
                    data=data,
                    timeout=60
                )

                return response.status_code == 200

        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"上传文件失败 {relative_path}: {e}")
            return False

    def _sync_remote_files(self, version_type: str, platform: str, architecture: str,
                          local_files: List[FileInfo]) -> bool:
        """同步远程文件（删除多余文件）"""
        try:
            # 准备本地文件列表
            local_file_list = [
                {
                    "relative_path": file_info.relative_path,
                    "file_size": file_info.file_size,
                    "sha256_hash": file_info.sha256_hash
                }
                for file_info in local_files
            ]

            # 发送同步请求
            data = {
                'platform': platform,
                'architecture': architecture,
                'local_files': json.dumps(local_file_list),
                'api_key': get_api_key()
            }

            response = requests.post(
                f"{get_server_url()}/api/v2/sync/simple/{version_type}",
                data=data,
                timeout=60
            )

            return response.status_code == 200

        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"同步远程文件失败: {e}")
            return False

    def cancel_upload(self):
        """取消上传"""
        self.is_cancelled = True
