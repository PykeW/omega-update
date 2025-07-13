#!/usr/bin/env python3
"""
本地文件扫描器
用于扫描本地文件夹，计算文件哈希值，为下载更新提供基础数据
"""

import os
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class FileInfo:
    """文件信息数据类"""
    relative_path: str
    absolute_path: str
    file_name: str
    file_size: int
    sha256_hash: str
    last_modified: datetime
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "relative_path": self.relative_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "sha256": self.sha256_hash,
            "last_modified": self.last_modified.isoformat()
        }


class LocalFileScanner:
    """本地文件扫描器"""
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        初始化扫描器
        
        Args:
            progress_callback: 进度回调函数，接收 (current, total, current_file) 参数
        """
        self.progress_callback = progress_callback
        self.is_cancelled = False
        self._lock = threading.Lock()
        
    def cancel_scan(self):
        """取消扫描"""
        with self._lock:
            self.is_cancelled = True
    
    def calculate_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        计算文件的SHA256哈希值
        
        Args:
            file_path: 文件路径
            chunk_size: 读取块大小
            
        Returns:
            SHA256哈希值
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    # 检查是否被取消
                    with self._lock:
                        if self.is_cancelled:
                            return ""
                    
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            print(f"计算文件哈希失败 {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: Path, base_path: Path) -> Optional[FileInfo]:
        """
        获取单个文件的信息
        
        Args:
            file_path: 文件绝对路径
            base_path: 基础路径（用于计算相对路径）
            
        Returns:
            文件信息对象
        """
        try:
            # 检查是否被取消
            with self._lock:
                if self.is_cancelled:
                    return None
            
            if not file_path.exists() or not file_path.is_file():
                return None
            
            # 计算相对路径
            relative_path = str(file_path.relative_to(base_path)).replace('\\', '/')
            
            # 获取文件统计信息
            stat = file_path.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # 计算哈希值
            sha256_hash = self.calculate_file_hash(file_path)
            
            if not sha256_hash:  # 哈希计算失败或被取消
                return None
            
            return FileInfo(
                relative_path=relative_path,
                absolute_path=str(file_path),
                file_name=file_path.name,
                file_size=file_size,
                sha256_hash=sha256_hash,
                last_modified=last_modified
            )
            
        except Exception as e:
            print(f"获取文件信息失败 {file_path}: {e}")
            return None
    
    def scan_directory(self, directory_path: str, exclude_patterns: Optional[List[str]] = None) -> Dict[str, FileInfo]:
        """
        扫描目录并返回所有文件信息
        
        Args:
            directory_path: 要扫描的目录路径
            exclude_patterns: 排除的文件模式列表
            
        Returns:
            文件信息字典，键为相对路径，值为FileInfo对象
        """
        base_path = Path(directory_path)
        if not base_path.exists() or not base_path.is_dir():
            raise ValueError(f"目录不存在或不是有效目录: {directory_path}")
        
        # 重置取消状态
        with self._lock:
            self.is_cancelled = False
        
        # 默认排除模式
        if exclude_patterns is None:
            exclude_patterns = [
                '*.tmp', '*.temp', '*.log', '*.bak',
                '.git', '.svn', '__pycache__', '*.pyc',
                'Thumbs.db', '.DS_Store'
            ]
        
        # 收集所有文件
        all_files = []
        for root, dirs, files in os.walk(base_path):
            # 检查是否被取消
            with self._lock:
                if self.is_cancelled:
                    return {}
            
            # 过滤目录
            dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
            
            for file in files:
                if not self._should_exclude(file, exclude_patterns):
                    file_path = Path(root) / file
                    all_files.append(file_path)
        
        total_files = len(all_files)
        file_info_dict = {}
        
        # 处理每个文件
        for i, file_path in enumerate(all_files):
            # 检查是否被取消
            with self._lock:
                if self.is_cancelled:
                    return {}
            
            # 更新进度
            if self.progress_callback:
                self.progress_callback(i + 1, total_files, str(file_path.relative_to(base_path)))
            
            # 获取文件信息
            file_info = self.get_file_info(file_path, base_path)
            if file_info:
                file_info_dict[file_info.relative_path] = file_info
        
        return file_info_dict
    
    def _should_exclude(self, name: str, exclude_patterns: List[str]) -> bool:
        """
        检查文件或目录是否应该被排除
        
        Args:
            name: 文件或目录名
            exclude_patterns: 排除模式列表
            
        Returns:
            是否应该排除
        """
        import fnmatch
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    
    def get_directory_summary(self, directory_path: str) -> dict:
        """
        获取目录摘要信息（不计算哈希值，用于快速预览）
        
        Args:
            directory_path: 目录路径
            
        Returns:
            目录摘要信息
        """
        base_path = Path(directory_path)
        if not base_path.exists() or not base_path.is_dir():
            raise ValueError(f"目录不存在或不是有效目录: {directory_path}")
        
        total_files = 0
        total_size = 0
        file_types = {}
        
        for root, dirs, files in os.walk(base_path):
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size = file_path.stat().st_size
                    total_files += 1
                    total_size += file_size
                    
                    # 统计文件类型
                    ext = file_path.suffix.lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                    else:
                        file_types['无扩展名'] = file_types.get('无扩展名', 0) + 1
                        
                except Exception:
                    continue
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "file_types": file_types,
            "directory_path": str(base_path)
        }


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


# 测试代码
if __name__ == "__main__":
    def progress_callback(current, total, current_file):
        print(f"进度: {current}/{total} - {current_file}")
    
    scanner = LocalFileScanner(progress_callback)
    
    # 测试目录摘要
    test_dir = "."
    try:
        summary = scanner.get_directory_summary(test_dir)
        print(f"目录摘要:")
        print(f"  文件数量: {summary['total_files']}")
        print(f"  总大小: {format_file_size(summary['total_size'])}")
        print(f"  文件类型: {summary['file_types']}")
        
        # 测试文件扫描（只扫描几个文件）
        print(f"\n开始扫描文件...")
        files = scanner.scan_directory(test_dir)
        print(f"扫描完成，共找到 {len(files)} 个文件")
        
        # 显示前几个文件
        for i, (path, info) in enumerate(files.items()):
            if i >= 3:  # 只显示前3个
                break
            print(f"  {path}: {format_file_size(info.file_size)} - {info.sha256_hash[:16]}...")
            
    except Exception as e:
        print(f"测试失败: {e}")
