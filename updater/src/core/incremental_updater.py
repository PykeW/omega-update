#!/usr/bin/env python3
"""
增量更新管理器
实现智能的增量更新策略，包括文件级和二进制级差分更新
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    from .config import config
    from ..utils.file_utils import (
        compare_directories, calculate_file_hash,
        copy_file, delete_file, verify_file_integrity
    )
    from ..utils.binary_diff import binary_diff
except ImportError:
    # 处理直接运行时的导入
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

    from core.config import UpdaterConfig
    from utils.file_utils import (
        compare_directories, calculate_file_hash,
        copy_file, delete_file, verify_file_integrity
    )
    from utils.binary_diff import BinaryDiff

    config = UpdaterConfig()
    binary_diff = BinaryDiff()

logger = logging.getLogger(__name__)

class UpdatePlan:
    """更新计划类"""
    
    def __init__(self):
        self.files_to_add: List[Dict] = []
        self.files_to_delete: List[str] = []
        self.files_to_replace: List[Dict] = []
        self.files_to_patch: List[Dict] = []
        self.total_download_size = 0
        self.estimated_time = 0
        self.compression_ratio = 0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'files_to_add': self.files_to_add,
            'files_to_delete': self.files_to_delete,
            'files_to_replace': self.files_to_replace,
            'files_to_patch': self.files_to_patch,
            'total_download_size': self.total_download_size,
            'estimated_time': self.estimated_time,
            'compression_ratio': self.compression_ratio
        }
    
    def get_summary(self) -> Dict:
        """获取更新摘要"""
        return {
            'add_count': len(self.files_to_add),
            'delete_count': len(self.files_to_delete),
            'replace_count': len(self.files_to_replace),
            'patch_count': len(self.files_to_patch),
            'total_files': len(self.files_to_add) + len(self.files_to_replace) + len(self.files_to_patch),
            'download_size_mb': self.total_download_size / 1024 / 1024,
            'estimated_minutes': self.estimated_time / 60
        }

class IncrementalUpdater:
    """增量更新管理器"""
    
    def __init__(self):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 配置参数
        self.max_patch_size = self.config.get("max_patch_size_mb", 100) * 1024 * 1024
        self.enable_binary_diff = self.config.get("enable_binary_diff", True)
        self.patch_threshold = 0.8  # 如果补丁大小超过原文件的80%，则直接替换
    
    def analyze_update_requirements(self, old_version_path: Path, 
                                  new_version_path: Path) -> UpdatePlan:
        """
        分析更新需求，生成更新计划
        
        Args:
            old_version_path: 旧版本路径
            new_version_path: 新版本路径
            
        Returns:
            UpdatePlan: 更新计划
        """
        self.logger.info("分析更新需求...")
        
        plan = UpdatePlan()
        
        # 比较目录差异
        diff_result = compare_directories(old_version_path, new_version_path)
        
        # 处理新增文件
        for file_path in diff_result['added']:
            new_file_path = new_version_path / file_path
            file_size = new_file_path.stat().st_size
            
            plan.files_to_add.append({
                'path': file_path,
                'size': file_size,
                'hash': calculate_file_hash(new_file_path),
                'action': 'add'
            })
            plan.total_download_size += file_size
        
        # 处理删除文件
        plan.files_to_delete.extend(diff_result['deleted'])
        
        # 处理修改文件
        for file_path in diff_result['modified']:
            old_file_path = old_version_path / file_path
            new_file_path = new_version_path / file_path
            
            # 决定使用补丁还是完整替换
            if self._should_use_patch(old_file_path, new_file_path):
                patch_info = self._analyze_patch_requirements(old_file_path, new_file_path)
                if patch_info:
                    plan.files_to_patch.append(patch_info)
                    plan.total_download_size += patch_info['patch_size']
                else:
                    # 补丁生成失败，使用完整替换
                    replace_info = self._create_replace_info(new_file_path, file_path)
                    plan.files_to_replace.append(replace_info)
                    plan.total_download_size += replace_info['size']
            else:
                # 直接替换
                replace_info = self._create_replace_info(new_file_path, file_path)
                plan.files_to_replace.append(replace_info)
                plan.total_download_size += replace_info['size']
        
        # 计算压缩比和预估时间
        original_size = sum(diff_result['new_files'][f]['size'] 
                          for f in diff_result['added'] + diff_result['modified'])
        
        if original_size > 0:
            plan.compression_ratio = 1 - (plan.total_download_size / original_size)
        
        # 预估下载时间（假设1MB/s的下载速度）
        plan.estimated_time = plan.total_download_size / (1024 * 1024)
        
        self.logger.info(f"更新计划生成完成: {plan.get_summary()}")
        return plan
    
    def _should_use_patch(self, old_file: Path, new_file: Path) -> bool:
        """
        判断是否应该使用补丁更新
        
        Args:
            old_file: 旧文件路径
            new_file: 新文件路径
            
        Returns:
            bool: 是否使用补丁
        """
        if not self.enable_binary_diff:
            return False
        
        old_size = old_file.stat().st_size
        new_size = new_file.stat().st_size
        
        # 文件太小不值得打补丁
        if old_size < 1024 or new_size < 1024:
            return False
        
        # 文件太大可能不适合二进制差分
        if old_size > self.max_patch_size or new_size > self.max_patch_size:
            return False
        
        # 大小变化太大可能不适合补丁
        size_change_ratio = abs(new_size - old_size) / old_size
        if size_change_ratio > 2.0:  # 大小变化超过200%
            return False
        
        # 特定文件类型更适合补丁
        patch_friendly_extensions = {'.exe', '.dll', '.pyd', '.so', '.dylib'}
        if old_file.suffix.lower() in patch_friendly_extensions:
            return True
        
        # 其他情况根据文件大小决定
        return old_size > 100 * 1024  # 大于100KB的文件考虑使用补丁
    
    def _analyze_patch_requirements(self, old_file: Path, new_file: Path) -> Optional[Dict]:
        """
        分析补丁需求
        
        Args:
            old_file: 旧文件路径
            new_file: 新文件路径
            
        Returns:
            Optional[Dict]: 补丁信息，如果不适合补丁则返回None
        """
        try:
            patch_info = binary_diff.get_patch_info(old_file, new_file)
            
            if not patch_info.get('recommended', False):
                return None
            
            estimated_patch_size = patch_info['estimated_patch_size']
            new_size = patch_info['new_size']
            
            # 如果补丁大小超过阈值，不使用补丁
            if estimated_patch_size > new_size * self.patch_threshold:
                return None
            
            return {
                'path': str(new_file.relative_to(new_file.parent.parent)),
                'old_size': patch_info['old_size'],
                'new_size': new_size,
                'patch_size': estimated_patch_size,
                'old_hash': calculate_file_hash(old_file),
                'new_hash': calculate_file_hash(new_file),
                'action': 'patch',
                'compression_ratio': patch_info['compression_ratio']
            }
            
        except Exception as e:
            self.logger.error(f"分析补丁需求失败 {old_file}: {e}")
            return None
    
    def _create_replace_info(self, new_file: Path, relative_path: str) -> Dict:
        """创建替换文件信息"""
        file_size = new_file.stat().st_size
        return {
            'path': relative_path,
            'size': file_size,
            'hash': calculate_file_hash(new_file),
            'action': 'replace'
        }
    
    def generate_patch_files(self, old_version_path: Path, new_version_path: Path, 
                           update_plan: UpdatePlan, output_dir: Path) -> bool:
        """
        生成补丁文件
        
        Args:
            old_version_path: 旧版本路径
            new_version_path: 新版本路径
            update_plan: 更新计划
            output_dir: 输出目录
            
        Returns:
            bool: 是否成功
        """
        self.logger.info("生成补丁文件...")
        
        try:
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            success_count = 0
            total_count = len(update_plan.files_to_patch)
            
            for patch_info in update_plan.files_to_patch:
                file_path = patch_info['path']
                old_file = old_version_path / file_path
                new_file = new_version_path / file_path
                patch_file = output_dir / f"{file_path}.patch"
                
                # 确保补丁文件目录存在
                patch_file.parent.mkdir(parents=True, exist_ok=True)
                
                self.logger.info(f"生成补丁: {file_path}")
                
                success, method = binary_diff.create_patch(old_file, new_file, patch_file)
                
                if success:
                    # 更新补丁信息
                    actual_patch_size = patch_file.stat().st_size
                    patch_info['actual_patch_size'] = actual_patch_size
                    patch_info['method'] = method
                    success_count += 1
                    
                    self.logger.info(f"补丁生成成功: {file_path} ({actual_patch_size} bytes)")
                else:
                    self.logger.error(f"补丁生成失败: {file_path}")
                    # 将失败的补丁转为完整替换
                    replace_info = self._create_replace_info(new_file, file_path)
                    update_plan.files_to_replace.append(replace_info)
            
            # 移除失败的补丁
            update_plan.files_to_patch = [p for p in update_plan.files_to_patch 
                                        if 'actual_patch_size' in p]
            
            self.logger.info(f"补丁生成完成: {success_count}/{total_count}")
            return success_count > 0 or total_count == 0
            
        except Exception as e:
            self.logger.error(f"生成补丁文件失败: {e}")
            return False
    
    def apply_incremental_update(self, update_plan: UpdatePlan, 
                               source_dir: Path, target_dir: Path, 
                               patch_dir: Path) -> bool:
        """
        应用增量更新
        
        Args:
            update_plan: 更新计划
            source_dir: 源目录（当前版本）
            target_dir: 目标目录（更新后版本）
            patch_dir: 补丁目录
            
        Returns:
            bool: 是否成功
        """
        self.logger.info("应用增量更新...")
        
        try:
            # 删除文件
            for file_path in update_plan.files_to_delete:
                target_file = target_dir / file_path
                if target_file.exists():
                    delete_file(target_file)
                    self.logger.debug(f"删除文件: {file_path}")
            
            # 添加新文件
            for file_info in update_plan.files_to_add:
                file_path = file_info['path']
                source_file = source_dir / file_path
                target_file = target_dir / file_path
                
                if copy_file(source_file, target_file):
                    self.logger.debug(f"添加文件: {file_path}")
                else:
                    self.logger.error(f"添加文件失败: {file_path}")
                    return False
            
            # 替换文件
            for file_info in update_plan.files_to_replace:
                file_path = file_info['path']
                source_file = source_dir / file_path
                target_file = target_dir / file_path
                
                if copy_file(source_file, target_file):
                    self.logger.debug(f"替换文件: {file_path}")
                else:
                    self.logger.error(f"替换文件失败: {file_path}")
                    return False
            
            # 应用补丁
            for patch_info in update_plan.files_to_patch:
                file_path = patch_info['path']
                old_file = target_dir / file_path
                patch_file = patch_dir / f"{file_path}.patch"
                new_file = target_dir / f"{file_path}.new"
                
                if binary_diff.apply_patch(old_file, patch_file, new_file):
                    # 验证补丁结果
                    if verify_file_integrity(new_file, 
                                           patch_info['new_size'], 
                                           patch_info['new_hash']):
                        # 替换原文件
                        old_file.unlink()
                        new_file.rename(old_file)
                        self.logger.debug(f"应用补丁: {file_path}")
                    else:
                        self.logger.error(f"补丁验证失败: {file_path}")
                        new_file.unlink()
                        return False
                else:
                    self.logger.error(f"应用补丁失败: {file_path}")
                    return False
            
            self.logger.info("增量更新应用完成")
            return True
            
        except Exception as e:
            self.logger.error(f"应用增量更新失败: {e}")
            return False
    
    def save_update_plan(self, update_plan: UpdatePlan, file_path: Path) -> bool:
        """保存更新计划到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(update_plan.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"保存更新计划失败: {e}")
            return False
    
    def load_update_plan(self, file_path: Path) -> Optional[UpdatePlan]:
        """从文件加载更新计划"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            plan = UpdatePlan()
            plan.files_to_add = data.get('files_to_add', [])
            plan.files_to_delete = data.get('files_to_delete', [])
            plan.files_to_replace = data.get('files_to_replace', [])
            plan.files_to_patch = data.get('files_to_patch', [])
            plan.total_download_size = data.get('total_download_size', 0)
            plan.estimated_time = data.get('estimated_time', 0)
            plan.compression_ratio = data.get('compression_ratio', 0)
            
            return plan
        except Exception as e:
            self.logger.error(f"加载更新计划失败: {e}")
            return None

# 全局实例
incremental_updater = IncrementalUpdater()
