#!/usr/bin/env python3
"""
Omega更新服务器启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置工作目录为项目根目录
os.chdir(project_root)

if __name__ == "__main__":
    # 导入并启动服务器
    import uvicorn
    from server.server_config import ServerConfig

    config = ServerConfig()

    print("=" * 50)
    print("Omega 更新服务器启动中...")
    print(f"服务器地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"API 文档: http://{config.SERVER_HOST}:{config.SERVER_PORT}/docs")
    print("=" * 50)

    uvicorn.run(
        "server.enhanced_main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )
