#!/usr/bin/env python3
"""
Omega上传工具启动脚本
"""

import sys
import os
import tkinter as tk
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置工作目录为项目根目录
os.chdir(project_root)

if __name__ == "__main__":
    # 导入并启动上传工具
    from tools.upload.upload_tool import UploadToolRefactored
    
    print("启动 Omega 上传工具...")
    
    root = tk.Tk()
    app = UploadToolRefactored(root)
    root.mainloop()
