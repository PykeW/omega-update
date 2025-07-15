#!/usr/bin/env python3
"""
Omega服务器 - API v2部署脚本
重构版本 - 自动化部署API v2端点
"""

import subprocess
import sys
from pathlib import Path

def deploy_api_v2():
    """部署API v2端点到远程服务器"""
    
    print("🚀 开始部署API v2端点到远程服务器")
    print("=" * 50)
    
    server_ip = "106.14.28.97"
    username = "root"
    project_path = "/opt/omega-update-server"
    
    try:
        # 导入现有的部署脚本
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from deploy_api_v2_auto import main as deploy_main
        
        print("✅ 使用现有的自动化部署脚本")
        deploy_main()
        
    except ImportError:
        print("⚠️ 现有部署脚本不可用，使用手动部署方式")
        
        # 手动部署命令
        commands = [
            f"ssh {username}@{server_ip} 'systemctl status omega-update-server'",
            f"ssh {username}@{server_ip} 'cd {project_path} && ls -la api_v2_integration.py'",
            f"ssh {username}@{server_ip} 'systemctl restart omega-update-server'",
            f"ssh {username}@{server_ip} 'curl -s http://localhost:8000/api/v2/status/simple'"
        ]
        
        for cmd in commands:
            print(f"🔧 执行: {cmd}")
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ 成功: {result.stdout.strip()}")
                else:
                    print(f"❌ 失败: {result.stderr.strip()}")
            except Exception as e:
                print(f"❌ 执行错误: {e}")

if __name__ == "__main__":
    deploy_api_v2()
