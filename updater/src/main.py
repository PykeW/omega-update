#!/usr/bin/env python3
"""
Omega更新器主入口文件
支持GUI模式、静默模式和检查模式
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import config
from core.app_manager import ApplicationManager
from core.update_manager import UpdateManager

class UpdaterApp:
    """更新器应用主类"""
    
    def __init__(self):
        self.config = config
        self.app_manager = ApplicationManager()
        self.update_manager = UpdateManager()
        self.logger = logging.getLogger(__name__)
        
        # 确保必要的目录存在
        self.config.ensure_directories()
        
        # 验证配置
        if not self.config.validate_config():
            self.logger.error("配置验证失败")
            sys.exit(1)
    
    def run_gui_mode(self):
        """运行图形界面模式"""
        try:
            from gui.updater_window import UpdaterWindow
            
            self.logger.info("启动GUI模式")
            app = UpdaterWindow(self.config, self.update_manager, self.app_manager)
            return app.run()
            
        except ImportError as e:
            self.logger.error(f"GUI模块导入失败: {e}")
            print("错误: GUI模块不可用，请检查依赖包是否安装")
            return False
        except Exception as e:
            self.logger.error(f"GUI模式运行失败: {e}")
            return False
    
    def run_silent_mode(self):
        """运行静默更新模式"""
        try:
            self.logger.info("启动静默更新模式")
            print("检查更新...")
            
            # 检查是否有更新
            has_update, update_info = self.update_manager.check_for_updates()
            
            if not has_update:
                print("已是最新版本")
                return True
            
            print(f"发现新版本: {update_info.version}")
            print(f"当前版本: {self.app_manager.get_app_version()}")
            
            # 询问是否更新（除非配置为完全静默）
            if not self.config.get("enable_silent_update", False):
                response = input("是否立即更新? (y/N): ").lower()
                if response not in ['y', 'yes']:
                    print("更新已取消")
                    return True
            
            # 关闭主应用
            print("关闭应用程序...")
            if not self.app_manager.close_app_gracefully():
                print("错误: 无法关闭主应用，更新中止")
                return False
            
            # 设置进度回调
            def progress_callback(progress):
                if progress.total_size > 0:
                    percent = (progress.downloaded_size / progress.total_size) * 100
                    print(f"\r下载进度: {percent:.1f}% ({progress.current_file})", end="")
            
            def status_callback(status):
                print(f"\n{status}")
            
            self.update_manager.set_progress_callback(progress_callback)
            self.update_manager.set_status_callback(status_callback)
            
            # 执行更新
            print("开始更新...")
            success = self.update_manager.perform_update(update_info)
            
            if success:
                print("\n更新完成!")
                
                # 询问是否启动应用
                if not self.config.get("enable_silent_update", False):
                    response = input("是否启动应用程序? (Y/n): ").lower()
                    if response not in ['n', 'no']:
                        print("启动应用程序...")
                        self.app_manager.start_app()
                else:
                    # 静默模式自动启动
                    self.app_manager.start_app()
                
                return True
            else:
                print("\n更新失败!")
                return False
                
        except KeyboardInterrupt:
            print("\n更新已被用户中断")
            return False
        except Exception as e:
            self.logger.error(f"静默模式运行失败: {e}")
            print(f"错误: {e}")
            return False
    
    def run_check_only(self):
        """仅检查更新，不执行"""
        try:
            self.logger.info("检查更新模式")
            
            has_update, update_info = self.update_manager.check_for_updates()
            
            current_version = self.app_manager.get_app_version()
            print(f"当前版本: {current_version}")
            
            if has_update:
                print(f"有可用更新: {update_info.version}")
                print(f"更新描述: {update_info.description}")
                print(f"发布日期: {update_info.release_date}")
                print(f"文件大小: {update_info.file_size / 1024 / 1024:.1f} MB")
                
                if update_info.is_critical:
                    print("⚠️  这是一个重要更新，建议立即安装")
                
                return True
            else:
                print("已是最新版本")
                return False
                
        except Exception as e:
            self.logger.error(f"检查更新失败: {e}")
            print(f"错误: {e}")
            return False
    
    def run_config_mode(self):
        """配置模式"""
        try:
            print("=== Omega更新器配置 ===")
            print(f"配置文件: {self.config.config_file}")
            print(f"服务器URL: {self.config.get('server_url')}")
            print(f"应用目录: {self.config.get('app_directory')}")
            print(f"当前版本: {self.app_manager.get_app_version()}")
            print(f"自动检查: {'启用' if self.config.get('auto_check_interval') > 0 else '禁用'}")
            print(f"自动更新: {'启用' if self.config.get('enable_auto_update') else '禁用'}")
            
            print("\n可用操作:")
            print("1. 修改服务器URL")
            print("2. 修改应用目录")
            print("3. 启用/禁用自动检查")
            print("4. 启用/禁用自动更新")
            print("5. 重置配置")
            print("0. 退出")
            
            while True:
                choice = input("\n请选择操作 (0-5): ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    new_url = input(f"输入新的服务器URL (当前: {self.config.get('server_url')}): ").strip()
                    if new_url:
                        self.config.set('server_url', new_url)
                        self.config.save_config()
                        print("服务器URL已更新")
                elif choice == '2':
                    new_dir = input(f"输入新的应用目录 (当前: {self.config.get('app_directory')}): ").strip()
                    if new_dir:
                        self.config.set('app_directory', new_dir)
                        self.config.save_config()
                        print("应用目录已更新")
                elif choice == '3':
                    current = self.config.get('auto_check_interval', 0) > 0
                    new_state = not current
                    interval = 3600 if new_state else 0
                    self.config.set('auto_check_interval', interval)
                    self.config.save_config()
                    print(f"自动检查已{'启用' if new_state else '禁用'}")
                elif choice == '4':
                    current = self.config.get('enable_auto_update', False)
                    new_state = not current
                    self.config.set('enable_auto_update', new_state)
                    self.config.save_config()
                    print(f"自动更新已{'启用' if new_state else '禁用'}")
                elif choice == '5':
                    confirm = input("确认重置所有配置? (y/N): ").lower()
                    if confirm in ['y', 'yes']:
                        self.config.reset_to_defaults()
                        print("配置已重置")
                else:
                    print("无效选择")
            
            return True
            
        except Exception as e:
            self.logger.error(f"配置模式失败: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Omega应用程序更新器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                    # 启动GUI界面
  %(prog)s --mode gui         # 启动GUI界面
  %(prog)s --mode silent      # 静默更新模式
  %(prog)s --mode check       # 仅检查更新
  %(prog)s --mode config      # 配置模式
  %(prog)s --config custom.json  # 使用自定义配置文件
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["gui", "silent", "check", "config"], 
        default="gui", 
        help="运行模式 (默认: gui)"
    )
    
    parser.add_argument(
        "--config", 
        help="配置文件路径"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Omega Updater 1.0.0"
    )
    
    args = parser.parse_args()
    
    try:
        # 设置配置文件
        if args.config:
            config.config_file = Path(args.config)
            config.load_config()
        
        # 设置日志级别
        if args.log_level:
            config.set("log_level", args.log_level)
            config.setup_logging()
        
        # 创建更新器应用
        updater = UpdaterApp()
        
        # 根据模式运行
        if args.mode == "gui":
            success = updater.run_gui_mode()
        elif args.mode == "silent":
            success = updater.run_silent_mode()
        elif args.mode == "check":
            success = updater.run_check_only()
        elif args.mode == "config":
            success = updater.run_config_mode()
        else:
            print(f"未知模式: {args.mode}")
            success = False
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        logging.error(f"程序运行失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
