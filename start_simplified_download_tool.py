#!/usr/bin/env python3
"""
启动简化下载工具
"""

import sys
import tkinter as tk
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from tools.download.simplified_download_tool import SimplifiedDownloadTool


def main():
    """主函数"""
    print("启动 Omega 简化下载工具...")
    
    root = tk.Tk()
    
    # 设置主题
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass  # 如果主题文件不存在，使用默认主题
    
    app = SimplifiedDownloadTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
