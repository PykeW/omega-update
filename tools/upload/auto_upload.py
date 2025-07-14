#!/usr/bin/env python3
"""
Omega更新服务器 - 自动化上传工具
用于项目现场的软件更新分发，支持命令行操作和批处理模式
"""

import argparse
import json
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# 导入现有模块
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.upload.upload_handler import UploadHandler
from tools.common.common_utils import get_config, LogManager, ValidationUtils


class AutoUploader:
    """自动化上传器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化自动化上传器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file or "upload_config.json"
        self.config = self.load_config()
        self.setup_logging()

        # 初始化上传处理器
        self.log_manager = LogManager()
        self.upload_handler = UploadHandler(self.log_manager)

        # 统计信息
        self.stats = {
            'total_folders': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'start_time': None,
            'end_time': None
        }

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✓ 配置文件加载成功: {self.config_file}")
                return config
            else:
                print(f"⚠ 配置文件不存在: {self.config_file}")
                print("使用默认配置...")
                return self.get_default_config()
        except Exception as e:
            print(f"✗ 配置文件加载失败: {e}")
            print("使用默认配置...")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "url": "http://106.14.28.97:8000",
                "api_key": "dac450db3ec47d79b8e8b5c6e9f4a2b1"
            },
            "upload": {
                "default_platform": "windows",
                "default_architecture": "x64",
                "default_package_type": "full",
                "default_is_stable": True,
                "default_is_critical": False,
                "chunk_size": 8192,
                "timeout": 300,
                "retry_count": 3,
                "retry_delay": 5
            },
            "logging": {
                "level": "INFO",
                "file": "auto_upload.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }

    def setup_logging(self):
        """设置日志记录"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'auto_upload.log')

        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)

        # 配置根日志器
        logging.basicConfig(
            level=log_level,
            handlers=[file_handler, console_handler]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("自动化上传工具启动")

    def validate_upload_params(self, params: Dict[str, Any]) -> tuple:
        """验证上传参数"""
        # 验证必需参数
        required_params = ['folder_path', 'version']
        for param in required_params:
            if not params.get(param):
                return False, f"缺少必需参数: {param}"

        # 验证文件夹路径
        valid, msg = ValidationUtils.validate_folder_path(params['folder_path'])
        if not valid:
            return False, f"文件夹路径无效: {msg}"

        # 验证版本格式
        valid, msg = ValidationUtils.validate_version_format(params['version'])
        if not valid:
            return False, f"版本格式无效: {msg}"

        # 验证描述
        if params.get('description'):
            valid, msg = ValidationUtils.validate_description(params['description'])
            if not valid:
                return False, f"描述无效: {msg}"

        return True, "参数验证通过"

    def upload_folder(self, folder_path: str, version: str, description: str = "",
                     platform: Optional[str] = None, architecture: Optional[str] = None,
                     package_type: Optional[str] = None, is_stable: Optional[bool] = None,
                     is_critical: Optional[bool] = None, from_version: str = "") -> bool:
        """
        上传单个文件夹

        Args:
            folder_path: 文件夹路径
            version: 版本号
            description: 描述
            platform: 平台
            architecture: 架构
            package_type: 包类型
            is_stable: 是否稳定版本
            is_critical: 是否关键更新
            from_version: 来源版本（增量包用）

        Returns:
            是否成功
        """
        # 使用配置文件的默认值
        upload_config = self.config.get('upload', {})

        params = {
            'folder_path': folder_path,
            'version': version,
            'description': description or f"自动上传 - {version}",
            'platform': platform or upload_config.get('default_platform', 'windows'),
            'architecture': architecture or upload_config.get('default_architecture', 'x64'),
            'package_type': package_type or upload_config.get('default_package_type', 'full'),
            'is_stable': is_stable if is_stable is not None else upload_config.get('default_is_stable', True),
            'is_critical': is_critical if is_critical is not None else upload_config.get('default_is_critical', False),
            'from_version': from_version
        }

        # 验证参数
        valid, msg = self.validate_upload_params(params)
        if not valid:
            self.logger.error(f"参数验证失败: {msg}")
            return False

        # 分析文件夹
        self.logger.info(f"开始分析文件夹: {folder_path}")
        analysis_result = self.upload_handler.analyze_folder(folder_path)
        if not analysis_result:
            self.logger.error("文件夹分析失败")
            return False

        self.logger.info(f"文件夹分析完成: {analysis_result}")

        # 开始上传
        self.logger.info(f"开始上传版本: {version}")

        def progress_callback(progress: float, status: str):
            """进度回调"""
            print(f"\r上传进度: {progress:.1f}% - {status}", end='', flush=True)

        try:
            success = self.upload_handler.start_upload(params, progress_callback)
            print()  # 换行

            if success:
                self.logger.info(f"上传成功: {version}")
                self.stats['successful_uploads'] += 1
                return True
            else:
                self.logger.error(f"上传失败: {version}")
                self.stats['failed_uploads'] += 1
                return False

        except Exception as e:
            print()  # 换行
            self.logger.error(f"上传异常: {e}")
            self.stats['failed_uploads'] += 1
            return False

    def upload_batch(self, batch_config: Dict[str, Any]) -> bool:
        """
        批量上传

        Args:
            batch_config: 批量配置

        Returns:
            是否全部成功
        """
        folders = batch_config.get('folders', [])
        if not folders:
            self.logger.error("批量配置中没有指定文件夹")
            return False

        self.stats['total_folders'] = len(folders)
        self.stats['start_time'] = time.time()

        self.logger.info(f"开始批量上传，共 {len(folders)} 个文件夹")

        all_success = True

        for i, folder_config in enumerate(folders, 1):
            self.logger.info(f"处理第 {i}/{len(folders)} 个文件夹")

            # 提取文件夹配置
            folder_path = folder_config.get('path')
            if not folder_path:
                self.logger.error(f"第 {i} 个文件夹配置缺少路径")
                all_success = False
                continue

            # 上传文件夹
            success = self.upload_folder(
                folder_path=folder_path,
                version=folder_config.get('version', ''),
                description=folder_config.get('description', ''),
                platform=folder_config.get('platform'),
                architecture=folder_config.get('architecture'),
                package_type=folder_config.get('package_type'),
                is_stable=folder_config.get('is_stable'),
                is_critical=folder_config.get('is_critical'),
                from_version=folder_config.get('from_version', '')
            )

            if not success:
                all_success = False

            # 添加延迟避免服务器压力
            if i < len(folders):
                time.sleep(2)

        self.stats['end_time'] = time.time()
        self.print_statistics()

        return all_success

    def print_statistics(self):
        """打印统计信息"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            duration_str = f"{duration:.1f}秒"
        else:
            duration_str = "未知"

        print("\n" + "="*50)
        print("上传统计信息")
        print("="*50)
        print(f"总文件夹数: {self.stats['total_folders']}")
        print(f"成功上传: {self.stats['successful_uploads']}")
        print(f"失败上传: {self.stats['failed_uploads']}")
        print(f"成功率: {(self.stats['successful_uploads']/max(1, self.stats['total_folders']))*100:.1f}%")
        print(f"总耗时: {duration_str}")
        print("="*50)

        self.logger.info(f"上传完成 - 成功: {self.stats['successful_uploads']}, 失败: {self.stats['failed_uploads']}")


def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        "server": {
            "url": "http://106.14.28.97:8000",
            "api_key": "your_api_key_here"
        },
        "upload": {
            "default_platform": "windows",
            "default_architecture": "x64",
            "default_package_type": "full",
            "default_is_stable": True,
            "default_is_critical": False
        },
        "logging": {
            "level": "INFO",
            "file": "auto_upload.log"
        }
    }

    with open("upload_config_sample.json", 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)

    print("✓ 示例配置文件已创建: upload_config_sample.json")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Omega更新服务器自动化上传工具")

    # 基本参数
    parser.add_argument('--config', '-c', help='配置文件路径', default='upload_config.json')
    parser.add_argument('--create-config', action='store_true', help='创建示例配置文件')

    # 单文件夹上传参数
    parser.add_argument('--folder', '-f', help='要上传的文件夹路径')
    parser.add_argument('--version', '-v', help='版本号')
    parser.add_argument('--description', '-d', help='版本描述')
    parser.add_argument('--platform', '-p', help='平台 (windows/linux/macos)')
    parser.add_argument('--architecture', '-a', help='架构 (x64/x86/arm64)')
    parser.add_argument('--package-type', '-t', help='包类型 (full/patch/hotfix)')
    parser.add_argument('--stable', action='store_true', help='标记为稳定版本')
    parser.add_argument('--critical', action='store_true', help='标记为关键更新')
    parser.add_argument('--from-version', help='来源版本（增量包用）')

    # 批量上传参数
    parser.add_argument('--batch', '-b', help='批量配置文件路径')

    args = parser.parse_args()

    # 创建示例配置
    if args.create_config:
        create_sample_config()
        return

    # 初始化上传器
    try:
        uploader = AutoUploader(args.config)
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        sys.exit(1)

    # 批量上传模式
    if args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                batch_config = json.load(f)

            success = uploader.upload_batch(batch_config)
            sys.exit(0 if success else 1)

        except Exception as e:
            print(f"✗ 批量上传失败: {e}")
            sys.exit(1)

    # 单文件夹上传模式
    elif args.folder and args.version:
        success = uploader.upload_folder(
            folder_path=args.folder,
            version=args.version,
            description=args.description,
            platform=args.platform,
            architecture=args.architecture,
            package_type=args.package_type,
            is_stable=args.stable,
            is_critical=args.critical,
            from_version=args.from_version
        )

        sys.exit(0 if success else 1)

    else:
        parser.print_help()
        print("\n示例用法:")
        print("  python auto_upload.py --folder ./my_app --version v1.0.0 --description '新版本发布'")
        print("  python auto_upload.py --batch batch_config.json")
        print("  python auto_upload.py --create-config")


if __name__ == "__main__":
    main()
