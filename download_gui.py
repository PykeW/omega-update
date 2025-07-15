#!/usr/bin/env python3
"""
Omega更新系统 - 下载GUI入口程序
重构版本 - 统一的下载界面入口
"""

import sys
import os
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "upload_download"))
sys.path.insert(0, str(project_root / "tools"))

def main():
    """主函数 - 启动下载GUI"""
    try:
        # 导入下载GUI模块
        from upload_download.download.download_gui import DownloadGUI
        
        print("🚀 启动Omega更新系统 - 下载工具")
        print("=" * 50)
        
        # 创建并启动下载GUI
        app = DownloadGUI()
        app.run()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保项目结构完整，所有依赖模块都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
