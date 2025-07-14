#!/usr/bin/env python3
"""
上传业务逻辑处理器
处理文件上传、文件夹分析等核心业务逻辑
"""

import os
import hashlib
import requests
import threading
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import (
    get_server_url, get_api_key, FileUtils, LogManager,
    APIEndpoints, AppConstants, ValidationUtils
)


class FolderAnalyzer:
    """文件夹分析器"""
    
    @staticmethod
    def analyze_folder(folder_path: str) -> Optional[Dict[str, Any]]:
        """
        分析文件夹内容
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            分析结果字典或None
        """
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists() or not folder_path.is_dir():
                return None
            
            # 统计文件信息
            total_files = 0
            total_size = 0
            file_types = {}
            
            for root, dirs, files in os.walk(folder_path):
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
                'path': str(folder_path),
                'total_files': total_files,
                'total_size': total_size,
                'file_types': file_types
            }
            
        except Exception:
            return None
    
    @staticmethod
    def format_analysis_result(analysis: Dict[str, Any]) -> str:
        """格式化分析结果为显示文本"""
        if not analysis:
            return "分析失败"
        
        size_str = FileUtils.format_file_size(analysis['total_size'])
        info_text = f"文件数量: {analysis['total_files']}, 总大小: {size_str}"
        
        # 显示主要文件类型
        file_types = analysis.get('file_types', {})
        if file_types:
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
            types_str = ", ".join([f"{ext}({count})" for ext, count in top_types])
            info_text += f", 主要类型: {types_str}"
        
        return info_text


class FileUploader:
    """文件上传器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None, 
                 progress_callback: Optional[Callable] = None):
        """
        初始化文件上传器
        
        Args:
            log_manager: 日志管理器
            progress_callback: 进度回调函数
        """
        self.log_manager = log_manager
        self.progress_callback = progress_callback
        self.is_cancelled = False
    
    def cancel_upload(self):
        """取消上传"""
        self.is_cancelled = True
    
    def upload_folder(self, folder_path: str, upload_config: Dict[str, Any]) -> bool:
        """
        上传文件夹
        
        Args:
            folder_path: 文件夹路径
            upload_config: 上传配置
            
        Returns:
            是否成功
        """
        try:
            folder_path = Path(folder_path)
            
            # 收集所有文件
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(folder_path)
                    all_files.append((file_path, relative_path))
            
            total_files = len(all_files)
            uploaded_files = 0
            failed_files = 0
            
            if self.log_manager:
                self.log_manager.log_info(f"找到 {total_files} 个文件")
            
            for i, (file_path, relative_path) in enumerate(all_files):
                if self.is_cancelled:
                    break
                
                try:
                    # 更新进度
                    progress = (i / total_files) * 100
                    if self.progress_callback:
                        self.progress_callback(progress, f"上传: {relative_path}")
                    
                    # 上传单个文件
                    success = self._upload_single_file(file_path, relative_path, upload_config)
                    
                    if success:
                        uploaded_files += 1
                        if self.log_manager:
                            self.log_manager.log_success(f"上传成功: {relative_path}")
                    else:
                        failed_files += 1
                        if self.log_manager:
                            self.log_manager.log_error(f"上传失败: {relative_path}")
                    
                except Exception as e:
                    failed_files += 1
                    if self.log_manager:
                        self.log_manager.log_error(f"上传异常 {relative_path}: {e}")
            
            # 返回结果
            success_rate = uploaded_files / total_files if total_files > 0 else 0
            return success_rate > 0.8  # 80%以上成功率认为成功
            
        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"上传过程异常: {e}")
            return False
    
    def _upload_single_file(self, file_path: Path, relative_path: Path, 
                           upload_config: Dict[str, Any]) -> bool:
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
                    'version': upload_config['version'],
                    'platform': upload_config['platform'],
                    'arch': upload_config['architecture'],
                    'relative_path': str(relative_path).replace('\\', '/'),
                    'package_type': upload_config['package_type'],
                    'description': upload_config['description'],
                    'is_stable': str(upload_config['is_stable']).lower(),
                    'is_critical': str(upload_config['is_critical']).lower(),
                    'api_key': get_api_key(),
                    'file_hash': file_hash
                }
                
                # 添加来源版本（如果是增量包）
                if upload_config['package_type'] == "patch" and upload_config.get('from_version'):
                    data['from_version'] = upload_config['from_version']
                
                # 发送请求
                response = requests.post(
                    f"{get_server_url()}{APIEndpoints.UPLOAD_FILE}",
                    files=files,
                    data=data,
                    timeout=AppConstants.REQUEST_TIMEOUT * 3
                )
                
                return response.status_code == 200
                
        except Exception:
            return False


class ZipCreator:
    """压缩包创建器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None):
        self.log_manager = log_manager
    
    def create_zip_from_folder(self, folder_path: str, 
                              progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        将文件夹压缩为zip文件
        
        Args:
            folder_path: 文件夹路径
            progress_callback: 进度回调函数
            
        Returns:
            临时zip文件路径或None
        """
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists():
                raise ValueError("文件夹不存在")
            
            # 创建临时zip文件
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip.close()
            
            # 收集所有文件
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    all_files.append(file_path)
            
            total_files = len(all_files)
            
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for i, file_path in enumerate(all_files):
                    try:
                        # 计算相对路径
                        arcname = file_path.relative_to(folder_path)
                        zipf.write(file_path, arcname)
                        
                        # 更新进度
                        if progress_callback:
                            progress = (i + 1) / total_files * 100
                            progress_callback(progress, f"压缩: {arcname}")
                            
                    except Exception as e:
                        if self.log_manager:
                            self.log_manager.log_warning(f"跳过文件 {file_path}: {e}")
                        continue
            
            return temp_zip.name
            
        except Exception as e:
            if self.log_manager:
                self.log_manager.log_error(f"创建压缩包失败: {e}")
            return None


class UploadHandler:
    """上传业务逻辑处理器"""
    
    def __init__(self, log_manager: Optional[LogManager] = None):
        """
        初始化上传处理器
        
        Args:
            log_manager: 日志管理器
        """
        self.log_manager = log_manager
        self.folder_analyzer = FolderAnalyzer()
        self.file_uploader = FileUploader(log_manager)
        self.zip_creator = ZipCreator(log_manager)
        self.folder_analysis = None
    
    def analyze_folder(self, folder_path: str) -> Optional[str]:
        """
        分析文件夹并返回格式化结果
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            格式化的分析结果文本
        """
        self.folder_analysis = self.folder_analyzer.analyze_folder(folder_path)
        result_text = self.folder_analyzer.format_analysis_result(self.folder_analysis)
        
        if self.folder_analysis and self.log_manager:
            self.log_manager.log_info(f"文件夹分析完成: {result_text}")
        elif self.log_manager:
            self.log_manager.log_error("分析文件夹失败")
        
        return result_text
    
    def validate_upload_config(self, config: Dict[str, Any]) -> tuple:
        """
        验证上传配置
        
        Args:
            config: 上传配置字典
            
        Returns:
            (是否有效, 错误消息)
        """
        # 验证版本号
        valid, msg = ValidationUtils.validate_version_format(config.get('version', ''))
        if not valid:
            return False, msg
        
        # 验证描述
        valid, msg = ValidationUtils.validate_description(config.get('description', ''))
        if not valid:
            return False, msg
        
        # 验证文件夹路径
        valid, msg = ValidationUtils.validate_folder_path(config.get('folder_path', ''))
        if not valid:
            return False, msg
        
        # 检查增量包的来源版本
        if config.get('package_type') == "patch":
            from_version = config.get('from_version', '').strip()
            if not from_version:
                return False, "增量包需要指定来源版本"
        
        return True, ""
    
    def start_upload(self, config: Dict[str, Any], 
                    progress_callback: Optional[Callable] = None) -> bool:
        """
        开始上传
        
        Args:
            config: 上传配置
            progress_callback: 进度回调函数
            
        Returns:
            是否成功
        """
        # 验证配置
        valid, error_msg = self.validate_upload_config(config)
        if not valid:
            if self.log_manager:
                self.log_manager.log_error(f"配置验证失败: {error_msg}")
            return False
        
        # 设置进度回调
        self.file_uploader.progress_callback = progress_callback
        
        # 开始上传
        if self.log_manager:
            self.log_manager.log_info("开始上传文件夹...")
        
        return self.file_uploader.upload_folder(config['folder_path'], config)
    
    def cancel_upload(self):
        """取消上传"""
        self.file_uploader.cancel_upload()
    
    def get_folder_analysis(self) -> Optional[Dict[str, Any]]:
        """获取文件夹分析结果"""
        return self.folder_analysis
