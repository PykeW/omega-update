#!/usr/bin/env python3
"""
Omega更新服务器 - 批处理上传工具
专门用于批量处理多个文件夹的自动化上传
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.upload.auto_upload import AutoUploader


class BatchUploader:
    """批处理上传器"""

    def __init__(self, config_file: str = "upload_config.json"):
        """初始化批处理上传器"""
        self.uploader = AutoUploader(config_file)
        self.batch_results = []

    def scan_directory_for_versions(self, base_path: str, version_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        扫描目录寻找版本文件夹

        Args:
            base_path: 基础路径
            version_pattern: 版本模式（可选）

        Returns:
            版本文件夹列表
        """
        base_path_obj = Path(base_path)
        if not base_path_obj.exists():
            print(f"✗ 基础路径不存在: {base_path_obj}")
            return []

        version_folders = []

        # 扫描子目录
        for item in base_path_obj.iterdir():
            if item.is_dir():
                # 简单的版本检测：包含数字和点的文件夹名
                folder_name = item.name
                if any(char.isdigit() for char in folder_name) and '.' in folder_name:
                    version_folders.append({
                        'path': str(item),
                        'version': folder_name,
                        'description': f'自动检测版本 - {folder_name}'
                    })

        print(f"✓ 在 {base_path} 中发现 {len(version_folders)} 个版本文件夹")
        return version_folders

    def create_batch_config_from_directory(self, base_path: str, output_file: str = "batch_config.json"):
        """
        从目录结构创建批处理配置文件

        Args:
            base_path: 基础路径
            output_file: 输出配置文件
        """
        version_folders = self.scan_directory_for_versions(base_path)

        if not version_folders:
            print("✗ 没有发现版本文件夹")
            return

        batch_config = {
            "description": f"从 {base_path} 自动生成的批处理配置",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "folders": version_folders
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_config, f, indent=2, ensure_ascii=False)

        print(f"✓ 批处理配置文件已创建: {output_file}")
        print(f"✓ 包含 {len(version_folders)} 个版本文件夹")

    def upload_from_directory(self, base_path: str, platform: str = "windows",
                            architecture: str = "x64", package_type: str = "full") -> bool:
        """
        直接从目录上传所有版本

        Args:
            base_path: 基础路径
            platform: 平台
            architecture: 架构
            package_type: 包类型

        Returns:
            是否全部成功
        """
        version_folders = self.scan_directory_for_versions(base_path)

        if not version_folders:
            print("✗ 没有发现版本文件夹")
            return False

        print(f"开始批量上传 {len(version_folders)} 个版本...")

        all_success = True

        for i, folder_info in enumerate(version_folders, 1):
            print(f"\n处理第 {i}/{len(version_folders)} 个版本: {folder_info['version']}")

            success = self.uploader.upload_folder(
                folder_path=folder_info['path'],
                version=folder_info['version'],
                description=folder_info['description'],
                platform=platform,
                architecture=architecture,
                package_type=package_type
            )

            self.batch_results.append({
                'version': folder_info['version'],
                'path': folder_info['path'],
                'success': success
            })

            if not success:
                all_success = False

            # 添加延迟
            if i < len(version_folders):
                time.sleep(3)

        self.print_batch_results()
        return all_success

    def print_batch_results(self):
        """打印批处理结果"""
        if not self.batch_results:
            return

        print("\n" + "="*60)
        print("批处理上传结果")
        print("="*60)

        successful = 0
        failed = 0

        for result in self.batch_results:
            status = "✓ 成功" if result['success'] else "✗ 失败"
            print(f"{status} {result['version']:20} - {result['path']}")

            if result['success']:
                successful += 1
            else:
                failed += 1

        print("-"*60)
        print(f"总计: {len(self.batch_results)} 个版本")
        print(f"成功: {successful} 个")
        print(f"失败: {failed} 个")
        print(f"成功率: {(successful/len(self.batch_results))*100:.1f}%")
        print("="*60)


def create_sample_batch_config():
    """创建示例批处理配置文件"""
    sample_batch = {
        "description": "示例批处理配置",
        "folders": [
            {
                "path": "./version_1.0.0",
                "version": "v1.0.0",
                "description": "第一个版本",
                "platform": "windows",
                "architecture": "x64",
                "package_type": "full",
                "is_stable": True,
                "is_critical": False
            },
            {
                "path": "./version_1.0.1",
                "version": "v1.0.1",
                "description": "修复版本",
                "platform": "windows",
                "architecture": "x64",
                "package_type": "patch",
                "from_version": "v1.0.0",
                "is_stable": True,
                "is_critical": False
            },
            {
                "path": "./version_1.0.2",
                "version": "v1.0.2",
                "description": "紧急修复",
                "platform": "windows",
                "architecture": "x64",
                "package_type": "hotfix",
                "from_version": "v1.0.1",
                "is_stable": False,
                "is_critical": True
            }
        ]
    }

    with open("batch_config_sample.json", 'w', encoding='utf-8') as f:
        json.dump(sample_batch, f, indent=2, ensure_ascii=False)

    print("✓ 示例批处理配置文件已创建: batch_config_sample.json")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Omega更新服务器批处理上传工具")

    parser.add_argument('--config', '-c', help='配置文件路径', default='upload_config.json')
    parser.add_argument('--create-sample', action='store_true', help='创建示例批处理配置')

    # 从目录扫描模式
    parser.add_argument('--scan-dir', help='扫描目录并创建批处理配置')
    parser.add_argument('--output', '-o', help='输出配置文件名', default='batch_config.json')

    # 直接上传模式
    parser.add_argument('--upload-dir', help='直接从目录上传所有版本')
    parser.add_argument('--platform', '-p', help='平台', default='windows')
    parser.add_argument('--architecture', '-a', help='架构', default='x64')
    parser.add_argument('--package-type', '-t', help='包类型', default='full')

    # 批处理文件模式
    parser.add_argument('--batch-file', '-b', help='批处理配置文件')

    args = parser.parse_args()

    # 创建示例配置
    if args.create_sample:
        create_sample_batch_config()
        return

    # 初始化批处理上传器
    try:
        batch_uploader = BatchUploader(args.config)
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        sys.exit(1)

    # 扫描目录模式
    if args.scan_dir:
        batch_uploader.create_batch_config_from_directory(args.scan_dir, args.output)
        return

    # 直接上传模式
    if args.upload_dir:
        success = batch_uploader.upload_from_directory(
            args.upload_dir,
            args.platform,
            args.architecture,
            args.package_type
        )
        sys.exit(0 if success else 1)

    # 批处理文件模式
    if args.batch_file:
        try:
            with open(args.batch_file, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)

            success = batch_uploader.uploader.upload_batch(batch_config)
            sys.exit(0 if success else 1)

        except Exception as e:
            print(f"✗ 批处理上传失败: {e}")
            sys.exit(1)

    else:
        parser.print_help()
        print("\n示例用法:")
        print("  python auto_upload_batch.py --scan-dir ./versions")
        print("  python auto_upload_batch.py --upload-dir ./versions --platform windows")
        print("  python auto_upload_batch.py --batch-file batch_config.json")
        print("  python auto_upload_batch.py --create-sample")


if __name__ == "__main__":
    main()
