#!/usr/bin/env python3
"""
启动集成了简化API的Omega更新服务器 - 推荐版本
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    from server.enhanced_main import app

    print("启动 Omega 更新服务器（集成简化API）...")  # 注意：此文件是推荐的启动方式
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True
    )
