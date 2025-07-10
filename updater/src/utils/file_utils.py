#!/usr/bin/env python3
"""
文件处理工具模块
提供文件哈希计算、文件比较等功能
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

logger = logging.getLogger(__name__)

def calculate_file_hash(file_path: Path, algorithm: str = 'sha256', chunk_size: int = 8192) -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法，支持'md5', 'sha1', 'sha256'等
        chunk_size: 读取块大小
        
    Returns:
        str: 哈希值字符串
    """
    if not file_path.exists():
        logger.error(f"文件不存在: {file_path}")
        return ""
    
    try:
        hash_obj = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败 {file_path}: {e}")
        return ""

def get_file_info(file_path: Path) -> Dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict: 包含文件大小、修改时间等信息的字典
    """
    try:
        stat = file_path.stat()
        return {
            'path': str(file_path),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'exists': True
        }
    except Exception as e:
        logger.error(f"获取文件信息失败 {file_path}: {e}")
        return {
            'path': str(file_path),
            'size': 0,
            'mtime': 0,
            'exists': False
        }

def scan_directory(directory: Path, relative_to: Optional[Path] = None) -> Dict[str, Dict]:
    """
    扫描目录，获取所有文件信息
    
    Args:
        directory: 要扫描的目录
        relative_to: 相对路径的基准目录，如果为None则使用directory
        
    Returns:
        Dict[str, Dict]: 文件路径到文件信息的映射
    """
    if not directory.exists():
        logger.error(f"目录不存在: {directory}")
        return {}
    
    if relative_to is None:
        relative_to = directory
    
    files_info = {}
    
    try:
        for root, _, files in os.walk(directory):
            root_path = Path(root)
            
            for file_name in files:
                file_path = root_path / file_name
                relative_path = file_path.relative_to(relative_to)
                
                files_info[str(relative_path)] = get_file_info(file_path)
        
        return files_info
    except Exception as e:
        logger.error(f"扫描目录失败 {directory}: {e}")
        return {}

def compare_directories(old_dir: Path, new_dir: Path) -> Dict:
    """
    比较两个目录的差异
    
    Args:
        old_dir: 旧目录
        new_dir: 新目录
        
    Returns:
        Dict: 包含新增、删除、修改和未变更文件的字典
    """
    old_files = scan_directory(old_dir)
    new_files = scan_directory(new_dir)
    
    old_paths = set(old_files.keys())
    new_paths = set(new_files.keys())
    
    added = new_paths - old_paths
    deleted = old_paths - new_paths
    common = old_paths & new_paths
    
    modified = []
    unchanged = []
    
    for path in common:
        old_info = old_files[path]
        new_info = new_files[path]
        
        if old_info['size'] != new_info['size'] or old_info['mtime'] != new_info['mtime']:
            modified.append(path)
        else:
            unchanged.append(path)
    
    return {
        'added': list(added),
        'deleted': list(deleted),
        'modified': modified,
        'unchanged': unchanged,
        'old_files': old_files,
        'new_files': new_files
    }

def ensure_directory(directory: Path) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        bool: 是否成功
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory}: {e}")
        return False

def copy_file(source: Path, destination: Path) -> bool:
    """
    复制文件
    
    Args:
        source: 源文件路径
        destination: 目标文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        # 确保目标目录存在
        ensure_directory(destination.parent)
        
        # 复制文件
        import shutil
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(f"复制文件失败 {source} -> {destination}: {e}")
        return False

def delete_file(file_path: Path) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        if file_path.exists():
            file_path.unlink()
        return True
    except Exception as e:
        logger.error(f"删除文件失败 {file_path}: {e}")
        return False

def verify_file_integrity(file_path: Path, expected_size: int = 0, expected_hash: str = "") -> bool:
    """
    验证文件完整性
    
    Args:
        file_path: 文件路径
        expected_size: 预期文件大小
        expected_hash: 预期哈希值
        
    Returns:
        bool: 是否完整
    """
    if not file_path.exists():
        logger.error(f"文件不存在: {file_path}")
        return False
    
    # 验证文件大小
    if expected_size > 0:
        actual_size = file_path.stat().st_size
        if actual_size != expected_size:
            logger.error(f"文件大小不匹配: {file_path}, 预期 {expected_size}, 实际 {actual_size}")
            return False
    
    # 验证哈希值
    if expected_hash:
        actual_hash = calculate_file_hash(file_path)
        if actual_hash.lower() != expected_hash.lower():
            logger.error(f"文件哈希不匹配: {file_path}")
            return False
    
    return True
