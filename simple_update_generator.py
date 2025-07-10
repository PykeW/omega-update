#!/usr/bin/env python3
"""
简化的更新包生成工具
避免复杂的模块导入，直接实现核心功能
"""

import sys
import json
import argparse
import shutil
import hashlib
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

class SimpleUpdateGenerator:
    """简化的更新包生成器"""
    
    def __init__(self):
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希值"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"计算哈希失败 {file_path}: {e}")
            return ""
    
    def scan_directory(self, directory: Path) -> Dict[str, Dict]:
        """扫描目录，获取所有文件信息"""
        if not directory.exists():
            self.logger.error(f"目录不存在: {directory}")
            return {}
        
        files_info = {}
        
        try:
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                
                for file_name in files:
                    file_path = root_path / file_name
                    relative_path = file_path.relative_to(directory)
                    
                    try:
                        stat = file_path.stat()
                        files_info[str(relative_path)] = {
                            'path': str(relative_path),
                            'size': stat.st_size,
                            'mtime': stat.st_mtime,
                            'hash': self.calculate_file_hash(file_path)
                        }
                    except Exception as e:
                        self.logger.error(f"处理文件失败 {file_path}: {e}")
            
            return files_info
        except Exception as e:
            self.logger.error(f"扫描目录失败 {directory}: {e}")
            return {}
    
    def compare_directories(self, old_dir: Path, new_dir: Path) -> Dict:
        """比较两个目录的差异"""
        self.logger.info("扫描旧版本目录...")
        old_files = self.scan_directory(old_dir)
        
        self.logger.info("扫描新版本目录...")
        new_files = self.scan_directory(new_dir)
        
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
            
            # 比较哈希值来确定文件是否修改
            if old_info['hash'] != new_info['hash']:
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
    
    def generate_package(self, old_version_dir: Path, new_version_dir: Path, 
                        output_dir: Path, version: str) -> bool:
        """
        生成更新包
        
        Args:
            old_version_dir: 旧版本目录
            new_version_dir: 新版本目录
            output_dir: 输出目录
            version: 新版本号
            
        Returns:
            bool: 是否成功
        """
        try:
            self.logger.info(f"开始生成更新包: {version}")
            self.logger.info(f"旧版本: {old_version_dir}")
            self.logger.info(f"新版本: {new_version_dir}")
            self.logger.info(f"输出目录: {output_dir}")
            
            # 验证输入目录
            if not old_version_dir.exists():
                self.logger.error(f"旧版本目录不存在: {old_version_dir}")
                return False
            
            if not new_version_dir.exists():
                self.logger.error(f"新版本目录不存在: {new_version_dir}")
                return False
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 分析版本差异
            self.logger.info("分析版本差异...")
            diff_result = self.compare_directories(old_version_dir, new_version_dir)
            
            # 显示更新摘要
            self.logger.info("更新摘要:")
            self.logger.info(f"  新增文件: {len(diff_result['added'])} 个")
            self.logger.info(f"  删除文件: {len(diff_result['deleted'])} 个")
            self.logger.info(f"  修改文件: {len(diff_result['modified'])} 个")
            self.logger.info(f"  未变更文件: {len(diff_result['unchanged'])} 个")
            
            # 计算大小统计
            added_size = sum(diff_result['new_files'][f]['size'] for f in diff_result['added'])
            modified_size = sum(diff_result['new_files'][f]['size'] for f in diff_result['modified'])
            total_download_size = added_size + modified_size
            
            self.logger.info(f"  预计下载大小: {total_download_size / 1024 / 1024:.1f} MB")
            
            # 创建更新包目录结构
            package_dir = output_dir / f"update_{version}"
            files_dir = package_dir / "files"
            
            package_dir.mkdir(exist_ok=True)
            files_dir.mkdir(exist_ok=True)
            
            # 复制新增和修改的文件
            self.logger.info("复制更新文件...")
            files_to_copy = diff_result['added'] + diff_result['modified']
            
            for file_path in files_to_copy:
                source_file = new_version_dir / file_path
                target_file = files_dir / file_path
                
                if source_file.exists():
                    # 确保目标目录存在
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(source_file, target_file)
                    self.logger.debug(f"复制文件: {file_path}")
                else:
                    self.logger.warning(f"源文件不存在: {file_path}")
            
            # 生成更新元数据
            self.logger.info("生成更新元数据...")
            metadata = self._create_update_metadata(diff_result, version, total_download_size)
            
            # 保存元数据
            metadata_file = package_dir / "update_info.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 生成文件清单
            manifest = self._create_file_manifest(diff_result)
            manifest_file = package_dir / "file_manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # 生成校验文件
            self.logger.info("生成校验文件...")
            self._generate_checksums(package_dir)
            
            # 创建压缩包
            self.logger.info("创建压缩包...")
            archive_path = output_dir / f"update_{version}.zip"
            self._create_archive(package_dir, archive_path)
            
            self.logger.info(f"更新包生成完成: {package_dir}")
            self.logger.info(f"压缩包: {archive_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成更新包失败: {e}")
            return False
    
    def _create_update_metadata(self, diff_result: Dict, version: str, download_size: int) -> Dict:
        """创建更新元数据"""
        return {
            "version": version,
            "generated_at": datetime.now().isoformat(),
            "update_type": "incremental",
            "summary": {
                "added_files": len(diff_result['added']),
                "deleted_files": len(diff_result['deleted']),
                "modified_files": len(diff_result['modified']),
                "unchanged_files": len(diff_result['unchanged']),
                "total_download_size": download_size,
                "download_size_mb": download_size / 1024 / 1024
            },
            "requirements": {
                "min_version": "1.7.3",
                "platform": "windows",
                "arch": "x64"
            }
        }
    
    def _create_file_manifest(self, diff_result: Dict) -> Dict:
        """创建文件清单"""
        return {
            "added_files": [
                {
                    "path": path,
                    "size": diff_result['new_files'][path]['size'],
                    "hash": diff_result['new_files'][path]['hash']
                }
                for path in diff_result['added']
            ],
            "deleted_files": diff_result['deleted'],
            "modified_files": [
                {
                    "path": path,
                    "old_size": diff_result['old_files'][path]['size'],
                    "new_size": diff_result['new_files'][path]['size'],
                    "old_hash": diff_result['old_files'][path]['hash'],
                    "new_hash": diff_result['new_files'][path]['hash']
                }
                for path in diff_result['modified']
            ]
        }
    
    def _generate_checksums(self, package_dir: Path):
        """生成校验文件"""
        checksums = {}
        
        for file_path in package_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "checksums.json":
                relative_path = file_path.relative_to(package_dir)
                checksums[str(relative_path)] = self.calculate_file_hash(file_path)
        
        checksum_file = package_dir / "checksums.json"
        with open(checksum_file, 'w', encoding='utf-8') as f:
            json.dump(checksums, f, indent=2, ensure_ascii=False)
    
    def _create_archive(self, source_dir: Path, archive_path: Path):
        """创建压缩包"""
        try:
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'zip',
                str(source_dir.parent),
                str(source_dir.name)
            )
            self.logger.info(f"压缩包创建成功: {archive_path}")
        except Exception as e:
            self.logger.error(f"创建压缩包失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成Omega增量更新包")
    parser.add_argument("--old-version", required=True, help="旧版本目录路径")
    parser.add_argument("--new-version", required=True, help="新版本目录路径")
    parser.add_argument("--output", required=True, help="输出目录路径")
    parser.add_argument("--version", required=True, help="新版本号")
    
    args = parser.parse_args()
    
    # 转换为Path对象
    old_version_dir = Path(args.old_version)
    new_version_dir = Path(args.new_version)
    output_dir = Path(args.output)
    
    # 生成更新包
    generator = SimpleUpdateGenerator()
    success = generator.generate_package(
        old_version_dir, new_version_dir, output_dir, args.version
    )
    
    if success:
        print(f"更新包生成成功!")
        print(f"输出目录: {output_dir}")
    else:
        print("更新包生成失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
