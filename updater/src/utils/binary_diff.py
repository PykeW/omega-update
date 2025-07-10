#!/usr/bin/env python3
"""
二进制差分工具模块
实现文件的二进制差分和补丁应用功能
"""

import os
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import shutil

logger = logging.getLogger(__name__)

class BinaryDiff:
    """二进制差分工具类"""
    
    def __init__(self):
        self.bsdiff_available = self._check_bsdiff_availability()
        self.xdelta_available = self._check_xdelta_availability()
        
        if not (self.bsdiff_available or self.xdelta_available):
            logger.warning("没有可用的二进制差分工具")
    
    def _check_bsdiff_availability(self) -> bool:
        """检查bsdiff工具是否可用"""
        try:
            # 尝试导入bsdiff4库
            import bsdiff4
            return True
        except ImportError:
            logger.debug("bsdiff4库不可用")
            return False
    
    def _check_xdelta_availability(self) -> bool:
        """检查xdelta工具是否可用"""
        try:
            # 检查xdelta3命令是否存在
            result = subprocess.run(['xdelta3', '-h'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            logger.debug("xdelta3工具不可用")
            return False
    
    def create_patch_bsdiff(self, old_file: Path, new_file: Path, patch_file: Path) -> bool:
        """
        使用bsdiff创建二进制补丁
        
        Args:
            old_file: 旧文件路径
            new_file: 新文件路径
            patch_file: 补丁文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self.bsdiff_available:
            logger.error("bsdiff4库不可用")
            return False
        
        try:
            import bsdiff4
            
            # 读取文件内容
            with open(old_file, 'rb') as f:
                old_data = f.read()
            
            with open(new_file, 'rb') as f:
                new_data = f.read()
            
            # 生成补丁
            patch_data = bsdiff4.diff(old_data, new_data)
            
            # 保存补丁
            patch_file.parent.mkdir(parents=True, exist_ok=True)
            with open(patch_file, 'wb') as f:
                f.write(patch_data)
            
            logger.info(f"bsdiff补丁创建成功: {patch_file}")
            return True
            
        except Exception as e:
            logger.error(f"bsdiff补丁创建失败: {e}")
            return False
    
    def apply_patch_bsdiff(self, old_file: Path, patch_file: Path, new_file: Path) -> bool:
        """
        使用bsdiff应用二进制补丁
        
        Args:
            old_file: 旧文件路径
            patch_file: 补丁文件路径
            new_file: 新文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self.bsdiff_available:
            logger.error("bsdiff4库不可用")
            return False
        
        try:
            import bsdiff4
            
            # 读取旧文件和补丁
            with open(old_file, 'rb') as f:
                old_data = f.read()
            
            with open(patch_file, 'rb') as f:
                patch_data = f.read()
            
            # 应用补丁
            new_data = bsdiff4.patch(old_data, patch_data)
            
            # 保存新文件
            new_file.parent.mkdir(parents=True, exist_ok=True)
            with open(new_file, 'wb') as f:
                f.write(new_data)
            
            logger.info(f"bsdiff补丁应用成功: {new_file}")
            return True
            
        except Exception as e:
            logger.error(f"bsdiff补丁应用失败: {e}")
            return False
    
    def create_patch_xdelta(self, old_file: Path, new_file: Path, patch_file: Path) -> bool:
        """
        使用xdelta创建二进制补丁
        
        Args:
            old_file: 旧文件路径
            new_file: 新文件路径
            patch_file: 补丁文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self.xdelta_available:
            logger.error("xdelta3工具不可用")
            return False
        
        try:
            # 确保补丁目录存在
            patch_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行xdelta3命令
            cmd = [
                'xdelta3',
                '-e',  # encode (create patch)
                '-s', str(old_file),  # source file
                str(new_file),  # target file
                str(patch_file)  # patch file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"xdelta补丁创建成功: {patch_file}")
                return True
            else:
                logger.error(f"xdelta补丁创建失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("xdelta补丁创建超时")
            return False
        except Exception as e:
            logger.error(f"xdelta补丁创建失败: {e}")
            return False
    
    def apply_patch_xdelta(self, old_file: Path, patch_file: Path, new_file: Path) -> bool:
        """
        使用xdelta应用二进制补丁
        
        Args:
            old_file: 旧文件路径
            patch_file: 补丁文件路径
            new_file: 新文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self.xdelta_available:
            logger.error("xdelta3工具不可用")
            return False
        
        try:
            # 确保输出目录存在
            new_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 执行xdelta3命令
            cmd = [
                'xdelta3',
                '-d',  # decode (apply patch)
                '-s', str(old_file),  # source file
                str(patch_file),  # patch file
                str(new_file)  # output file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"xdelta补丁应用成功: {new_file}")
                return True
            else:
                logger.error(f"xdelta补丁应用失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("xdelta补丁应用超时")
            return False
        except Exception as e:
            logger.error(f"xdelta补丁应用失败: {e}")
            return False
    
    def create_patch(self, old_file: Path, new_file: Path, patch_file: Path, 
                    method: str = 'auto') -> Tuple[bool, str]:
        """
        创建二进制补丁
        
        Args:
            old_file: 旧文件路径
            new_file: 新文件路径
            patch_file: 补丁文件路径
            method: 使用的方法 ('auto', 'bsdiff', 'xdelta')
            
        Returns:
            Tuple[bool, str]: (是否成功, 使用的方法)
        """
        if not old_file.exists():
            logger.error(f"旧文件不存在: {old_file}")
            return False, ""
        
        if not new_file.exists():
            logger.error(f"新文件不存在: {new_file}")
            return False, ""
        
        # 检查文件大小，如果文件太大可能不适合二进制差分
        old_size = old_file.stat().st_size
        new_size = new_file.stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB
        
        if old_size > max_size or new_size > max_size:
            logger.warning(f"文件过大，不建议使用二进制差分: {old_size}, {new_size}")
        
        # 选择方法
        if method == 'auto':
            if self.bsdiff_available:
                method = 'bsdiff'
            elif self.xdelta_available:
                method = 'xdelta'
            else:
                logger.error("没有可用的二进制差分工具")
                return False, ""
        
        # 创建补丁
        if method == 'bsdiff':
            success = self.create_patch_bsdiff(old_file, new_file, patch_file)
        elif method == 'xdelta':
            success = self.create_patch_xdelta(old_file, new_file, patch_file)
        else:
            logger.error(f"不支持的方法: {method}")
            return False, ""
        
        return success, method if success else ""
    
    def apply_patch(self, old_file: Path, patch_file: Path, new_file: Path, 
                   method: str = 'auto') -> bool:
        """
        应用二进制补丁
        
        Args:
            old_file: 旧文件路径
            patch_file: 补丁文件路径
            new_file: 新文件路径
            method: 使用的方法 ('auto', 'bsdiff', 'xdelta')
            
        Returns:
            bool: 是否成功
        """
        if not old_file.exists():
            logger.error(f"旧文件不存在: {old_file}")
            return False
        
        if not patch_file.exists():
            logger.error(f"补丁文件不存在: {patch_file}")
            return False
        
        # 自动检测方法
        if method == 'auto':
            # 可以通过补丁文件的扩展名或内容来判断
            if patch_file.suffix.lower() in ['.bsdiff', '.patch']:
                method = 'bsdiff' if self.bsdiff_available else 'xdelta'
            else:
                method = 'bsdiff' if self.bsdiff_available else 'xdelta'
        
        # 应用补丁
        if method == 'bsdiff':
            return self.apply_patch_bsdiff(old_file, patch_file, new_file)
        elif method == 'xdelta':
            return self.apply_patch_xdelta(old_file, patch_file, new_file)
        else:
            logger.error(f"不支持的方法: {method}")
            return False
    
    def get_patch_info(self, old_file: Path, new_file: Path) -> dict:
        """
        获取补丁信息（不实际创建补丁）

        Args:
            old_file: 旧文件路径
            new_file: 新文件路径

        Returns:
            dict: 补丁信息
        """
        if not old_file.exists() or not new_file.exists():
            return {}

        old_size = old_file.stat().st_size
        new_size = new_file.stat().st_size

        # 估算补丁大小（粗略估计）
        size_diff = abs(new_size - old_size)
        estimated_patch_size = min(size_diff, min(old_size, new_size) * 0.5)

        return {
            'old_size': old_size,
            'new_size': new_size,
            'size_diff': size_diff,
            'estimated_patch_size': int(estimated_patch_size),
            'compression_ratio': estimated_patch_size / new_size if new_size > 0 else 0,
            'recommended': old_size > 1024 * 1024 and size_diff < old_size * 0.8  # 推荐条件
        }

# 全局实例
binary_diff = BinaryDiff()
