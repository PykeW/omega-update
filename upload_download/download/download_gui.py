#!/usr/bin/env python3
"""
Omega更新系统 - 下载GUI模块
重构版本 - 统一的下载界面
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """启动下载GUI的主函数"""
    try:
        # 导入现有的下载工具
        from start_download_tool import main as start_download_main
        
        print("🚀 启动Omega更新系统 - 下载工具 (重构版)")
        print("=" * 60)
        print("📁 项目根目录:", project_root)
        print("🔧 使用重构后的模块结构")
        print("=" * 60)
        
        # 调用原有的下载工具主函数
        start_download_main()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("正在尝试备用启动方式...")
        
        try:
            # 备用方式：直接导入下载工具
            from download_tool import DownloadTool
            
            print("✅ 使用备用启动方式")
            app = DownloadTool()
            app.run()
            
        except Exception as backup_error:
            print(f"❌ 备用启动也失败: {backup_error}")
            print("请检查项目结构和依赖")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


class DownloadGUI:
    """下载GUI类 - 重构版本的包装器"""
    
    def __init__(self):
        """初始化下载GUI"""
        self.project_root = Path(__file__).parent.parent.parent
        
    def run(self):
        """运行下载GUI"""
        main()


if __name__ == "__main__":
    main()
