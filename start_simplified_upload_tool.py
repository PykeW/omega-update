#!/usr/bin/env python3
"""
启动简化上传工具
"""

import sys
import tkinter as tk
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from tools.upload.simplified_upload_tool import SimplifiedUploadTool


def main():
    """主函数"""
    print("启动 Omega 简化上传工具...")
    
    root = tk.Tk()
    
    # 设置主题
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass  # 如果主题文件不存在，使用默认主题
    
    app = SimplifiedUploadTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
