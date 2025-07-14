#!/usr/bin/env python3
"""
文件差异检测器
用于对比本地文件与云端文件，识别需要更新的文件
"""

import json
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.download.local_file_scanner import FileInfo


class ChangeType(Enum):
    """变更类型枚举"""
    NEW = "new"           # 新增文件
    UPDATED = "updated"   # 更新文件
    DELETED = "deleted"   # 删除文件
    SAME = "same"         # 相同文件


@dataclass
class FileChange:
    """文件变更信息"""
    relative_path: str
    change_type: ChangeType
    file_size: int
    sha256_hash: str
    local_info: Optional[FileInfo] = None
    remote_info: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "relative_path": self.relative_path,
            "change_type": self.change_type.value,
            "file_size": self.file_size,
            "sha256": self.sha256_hash,
            "local_info": self.local_info.to_dict() if self.local_info else None,
            "remote_info": self.remote_info
        }


@dataclass
class UpdatePlan:
    """更新计划"""
    target_version: str
    platform: str
    architecture: str
    files_to_download: List[FileChange]
    files_to_delete: List[FileChange]
    files_same: List[FileChange]
    total_download_size: int
    total_file_count: int
    
    def get_summary(self) -> dict:
        """获取更新摘要"""
        return {
            "target_version": self.target_version,
            "platform": self.platform,
            "architecture": self.architecture,
            "files_to_download": len(self.files_to_download),
            "files_to_delete": len(self.files_to_delete),
            "files_same": len(self.files_same),
            "total_download_size": self.total_download_size,
            "total_file_count": self.total_file_count,
            "download_size_mb": round(self.total_download_size / 1024 / 1024, 2)
        }


class DifferenceDetector:
    """文件差异检测器"""
    
    def __init__(self, server_url: str, api_key: str):
        """
        初始化差异检测器
        
        Args:
            server_url: 服务器URL
            api_key: API密钥
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.timeout = 30
    
    def get_remote_file_list(self, version: str, platform: str = "windows", arch: str = "x64") -> Dict[str, dict]:
        """
        获取远程版本的文件列表
        
        Args:
            version: 版本号
            platform: 平台
            arch: 架构
            
        Returns:
            远程文件信息字典
        """
        try:
            response = self.session.get(
                f"{self.server_url}/api/v1/files/list",
                params={
                    "version": version,
                    "platform": platform,
                    "arch": arch,
                    "api_key": self.api_key
                }
            )
            
            if response.status_code == 401:
                raise Exception("API密钥无效")
            elif response.status_code == 404:
                raise Exception(f"版本 {version} 不存在")
            elif response.status_code != 200:
                raise Exception(f"获取远程文件列表失败: {response.status_code}")
            
            result = response.json()
            files = result.get("files", [])
            
            # 构建文件映射
            file_map = {}
            for file_info in files:
                file_map[file_info["relative_path"]] = file_info
            
            return file_map
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            raise Exception(f"获取远程文件列表失败: {e}")
    
    def compare_with_server(self, local_files: Dict[str, FileInfo], target_version: str, 
                          platform: str = "windows", arch: str = "x64") -> UpdatePlan:
        """
        使用服务器端比较API进行差异检测
        
        Args:
            local_files: 本地文件信息字典
            target_version: 目标版本
            platform: 平台
            arch: 架构
            
        Returns:
            更新计划
        """
        try:
            # 准备本地文件数据
            local_file_data = []
            for file_info in local_files.values():
                local_file_data.append(file_info.to_dict())
            
            # 发送比较请求
            response = self.session.post(
                f"{self.server_url}/api/v1/version/compare",
                data={
                    "target_version": target_version,
                    "platform": platform,
                    "arch": arch,
                    "local_files": json.dumps(local_file_data),
                    "api_key": self.api_key
                }
            )
            
            if response.status_code == 401:
                raise Exception("API密钥无效")
            elif response.status_code == 404:
                raise Exception(f"目标版本 {target_version} 不存在")
            elif response.status_code != 200:
                raise Exception(f"版本比较失败: {response.status_code}")
            
            result = response.json()
            
            # 解析结果
            changes = result.get("changes", {})
            summary = result.get("summary", {})
            
            files_to_download = []
            files_to_delete = []
            files_same = []
            
            # 处理需要下载的文件
            for file_data in changes.get("download", []):
                change_type = ChangeType.NEW if file_data.get("change_type") == "new" else ChangeType.UPDATED
                local_info = local_files.get(file_data["relative_path"])
                
                file_change = FileChange(
                    relative_path=file_data["relative_path"],
                    change_type=change_type,
                    file_size=file_data["file_size"],
                    sha256_hash=file_data["sha256"],
                    local_info=local_info,
                    remote_info=file_data
                )
                files_to_download.append(file_change)
            
            # 处理需要删除的文件
            for file_data in changes.get("delete", []):
                local_info = local_files.get(file_data["relative_path"])
                
                file_change = FileChange(
                    relative_path=file_data["relative_path"],
                    change_type=ChangeType.DELETED,
                    file_size=local_info.file_size if local_info else 0,
                    sha256_hash=local_info.sha256_hash if local_info else "",
                    local_info=local_info,
                    remote_info=None
                )
                files_to_delete.append(file_change)
            
            # 处理相同的文件
            for file_data in changes.get("same", []):
                local_info = local_files.get(file_data["relative_path"])
                
                file_change = FileChange(
                    relative_path=file_data["relative_path"],
                    change_type=ChangeType.SAME,
                    file_size=file_data["file_size"],
                    sha256_hash=file_data["sha256"],
                    local_info=local_info,
                    remote_info=file_data
                )
                files_same.append(file_change)
            
            return UpdatePlan(
                target_version=target_version,
                platform=platform,
                architecture=arch,
                files_to_download=files_to_download,
                files_to_delete=files_to_delete,
                files_same=files_same,
                total_download_size=summary.get("total_download_size", 0),
                total_file_count=summary.get("files_to_download", 0)
            )
            
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            raise Exception(f"版本比较失败: {e}")
    
    def compare_local(self, local_files: Dict[str, FileInfo], target_version: str,
                     platform: str = "windows", arch: str = "x64") -> UpdatePlan:
        """
        本地进行差异检测（备用方案）
        
        Args:
            local_files: 本地文件信息字典
            target_version: 目标版本
            platform: 平台
            arch: 架构
            
        Returns:
            更新计划
        """
        try:
            # 获取远程文件列表
            remote_files = self.get_remote_file_list(target_version, platform, arch)
            
            files_to_download = []
            files_to_delete = []
            files_same = []
            total_download_size = 0
            
            # 检查远程文件
            for path, remote_info in remote_files.items():
                if path not in local_files:
                    # 新文件
                    file_change = FileChange(
                        relative_path=path,
                        change_type=ChangeType.NEW,
                        file_size=remote_info["file_size"],
                        sha256_hash=remote_info["sha256"],
                        local_info=None,
                        remote_info=remote_info
                    )
                    files_to_download.append(file_change)
                    total_download_size += remote_info["file_size"]
                    
                elif local_files[path].sha256_hash != remote_info["sha256"]:
                    # 更新文件
                    file_change = FileChange(
                        relative_path=path,
                        change_type=ChangeType.UPDATED,
                        file_size=remote_info["file_size"],
                        sha256_hash=remote_info["sha256"],
                        local_info=local_files[path],
                        remote_info=remote_info
                    )
                    files_to_download.append(file_change)
                    total_download_size += remote_info["file_size"]
                    
                else:
                    # 相同文件
                    file_change = FileChange(
                        relative_path=path,
                        change_type=ChangeType.SAME,
                        file_size=remote_info["file_size"],
                        sha256_hash=remote_info["sha256"],
                        local_info=local_files[path],
                        remote_info=remote_info
                    )
                    files_same.append(file_change)
            
            # 检查本地独有文件（可能需要删除）
            for path, local_info in local_files.items():
                if path not in remote_files:
                    file_change = FileChange(
                        relative_path=path,
                        change_type=ChangeType.DELETED,
                        file_size=local_info.file_size,
                        sha256_hash=local_info.sha256_hash,
                        local_info=local_info,
                        remote_info=None
                    )
                    files_to_delete.append(file_change)
            
            return UpdatePlan(
                target_version=target_version,
                platform=platform,
                architecture=arch,
                files_to_download=files_to_download,
                files_to_delete=files_to_delete,
                files_same=files_same,
                total_download_size=total_download_size,
                total_file_count=len(files_to_download)
            )
            
        except Exception as e:
            raise Exception(f"本地差异检测失败: {e}")
    
    def detect_differences(self, local_files: Dict[str, FileInfo], target_version: str,
                          platform: str = "windows", arch: str = "x64", 
                          use_server_compare: bool = True) -> UpdatePlan:
        """
        检测文件差异
        
        Args:
            local_files: 本地文件信息字典
            target_version: 目标版本
            platform: 平台
            arch: 架构
            use_server_compare: 是否使用服务器端比较
            
        Returns:
            更新计划
        """
        if use_server_compare:
            try:
                return self.compare_with_server(local_files, target_version, platform, arch)
            except Exception as e:
                print(f"服务器端比较失败，使用本地比较: {e}")
                return self.compare_local(local_files, target_version, platform, arch)
        else:
            return self.compare_local(local_files, target_version, platform, arch)


# 测试代码
if __name__ == "__main__":
    from local_file_scanner import LocalFileScanner
    
    # 测试配置
    server_url = "http://106.14.28.97:8000"
    api_key = "dac450db3ec47d79196edb7a34defaed"
    
    detector = DifferenceDetector(server_url, api_key)
    
    try:
        # 测试获取远程文件列表
        print("测试获取远程文件列表...")
        remote_files = detector.get_remote_file_list("complete-test-1.0")
        print(f"远程文件数量: {len(remote_files)}")
        
        # 显示前几个文件
        for i, (path, info) in enumerate(remote_files.items()):
            if i >= 3:
                break
            print(f"  {path}: {info['file_size']} bytes - {info['sha256'][:16]}...")
            
    except Exception as e:
        print(f"测试失败: {e}")
