#!/usr/bin/env python3
"""
增量更新包生成工具
基于两个版本的差异生成增量更新包
"""

import sys
import json
import argparse
import shutil
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入updater模块
try:
    from updater.src.core.incremental_updater import IncrementalUpdater
    from updater.src.utils.file_utils import calculate_file_hash
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保updater模块已正确安装")
    print("当前Python路径:", sys.path)
    sys.exit(1)

class UpdatePackageGenerator:
    """更新包生成器"""

    def __init__(self):
        self._setup_logging()
        self.incremental_updater = IncrementalUpdater()

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 确保logger不为None
        if self.logger is None:
            self.logger = logging.getLogger('UpdatePackageGenerator')
    
    def generate_package(self, old_version_dir: Path, new_version_dir: Path, 
                        output_dir: Path, version: str) -> bool:
        """
        生成增量更新包
        
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
            
            # 分析更新需求
            self.logger.info("分析版本差异...")
            update_plan = self.incremental_updater.analyze_update_requirements(
                old_version_dir, new_version_dir
            )
            
            # 显示更新摘要
            summary = update_plan.get_summary()
            self.logger.info("更新摘要:")
            self.logger.info(f"  新增文件: {summary['add_count']} 个")
            self.logger.info(f"  删除文件: {summary['delete_count']} 个")
            self.logger.info(f"  替换文件: {summary['replace_count']} 个")
            self.logger.info(f"  补丁文件: {summary['patch_count']} 个")
            self.logger.info(f"  下载大小: {summary['download_size_mb']:.1f} MB")
            self.logger.info(f"  预估时间: {summary['estimated_minutes']:.1f} 分钟")
            
            # 创建更新包目录结构
            package_dir = output_dir / f"update_{version}"
            files_dir = package_dir / "files"
            patches_dir = package_dir / "patches"
            
            package_dir.mkdir(exist_ok=True)
            files_dir.mkdir(exist_ok=True)
            patches_dir.mkdir(exist_ok=True)
            
            # 复制新增和替换的文件
            self.logger.info("复制文件...")
            self._copy_update_files(new_version_dir, files_dir, 
                                  update_plan.files_to_add + update_plan.files_to_replace)
            
            # 生成补丁文件
            if update_plan.files_to_patch:
                self.logger.info("生成补丁文件...")
                self.incremental_updater.generate_patch_files(
                    old_version_dir, new_version_dir, update_plan, patches_dir
                )
            
            # 生成更新元数据
            self.logger.info("生成更新元数据...")
            metadata = self._create_update_metadata(update_plan, version)
            
            # 保存元数据
            metadata_file = package_dir / "update_info.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 保存更新计划
            plan_file = package_dir / "update_plan.json"
            self.incremental_updater.save_update_plan(update_plan, plan_file)
            
            # 生成校验文件
            self.logger.info("生成校验文件...")
            self._generate_checksums(package_dir)
            
            # 创建压缩包（可选）
            if self._should_create_archive():
                self.logger.info("创建压缩包...")
                self._create_archive(package_dir, output_dir / f"update_{version}.zip")
            
            self.logger.info(f"更新包生成完成: {package_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成更新包失败: {e}")
            return False
    
    def _copy_update_files(self, source_dir: Path, target_dir: Path, file_list: list):
        """复制更新文件"""
        for file_info in file_list:
            file_path = file_info['path']
            source_file = source_dir / file_path
            target_file = target_dir / file_path
            
            if source_file.exists():
                # 确保目标目录存在
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                shutil.copy2(source_file, target_file)
                self.logger.debug(f"复制文件: {file_path}")
            else:
                self.logger.warning(f"源文件不存在: {file_path}")
    
    def _create_update_metadata(self, update_plan, version: str) -> dict:
        """创建更新元数据"""
        summary = update_plan.get_summary()
        
        return {
            "version": version,
            "generated_at": datetime.now().isoformat(),
            "update_type": "incremental",
            "summary": summary,
            "files": {
                "added": len(update_plan.files_to_add),
                "deleted": len(update_plan.files_to_delete),
                "replaced": len(update_plan.files_to_replace),
                "patched": len(update_plan.files_to_patch)
            },
            "download_info": {
                "total_size": update_plan.total_download_size,
                "estimated_time": update_plan.estimated_time,
                "compression_ratio": update_plan.compression_ratio
            },
            "requirements": {
                "min_version": "1.7.3",  # 可以从配置获取
                "platform": "windows",
                "arch": "x64"
            }
        }
    
    def _generate_checksums(self, package_dir: Path):
        """生成校验文件"""
        checksums = {}
        
        for file_path in package_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "checksums.json":
                relative_path = file_path.relative_to(package_dir)
                checksums[str(relative_path)] = calculate_file_hash(file_path)
        
        checksum_file = package_dir / "checksums.json"
        with open(checksum_file, 'w', encoding='utf-8') as f:
            json.dump(checksums, f, indent=2, ensure_ascii=False)
    
    def _should_create_archive(self) -> bool:
        """是否应该创建压缩包"""
        return True  # 默认创建压缩包
    
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
    generator = UpdatePackageGenerator()
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
