#!/usr/bin/env python3
"""
更新包管理工具
用于管理服务器上的更新包
"""

import os
import sys
import argparse
import requests
import json
from pathlib import Path
from datetime import datetime
import hashlib

class UpdateManager:
    """更新包管理器"""
    
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
    
    def upload_version(self, version: str, file_path: Path, description: str = "",
                      is_stable: bool = True, is_critical: bool = False,
                      platform: str = "windows", arch: str = "x64"):
        """上传新版本"""
        
        if not file_path.exists():
            print(f"错误: 文件不存在 {file_path}")
            return False
        
        print(f"上传版本 {version}...")
        print(f"文件: {file_path}")
        print(f"大小: {file_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        url = f"{self.server_url}/api/v1/upload/version"
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            data = {
                'version': version,
                'description': description,
                'is_stable': is_stable,
                'is_critical': is_critical,
                'platform': platform,
                'arch': arch,
                'api_key': self.api_key
            }
            
            try:
                response = self.session.post(url, files=files, data=data, timeout=300)
                response.raise_for_status()
                
                result = response.json()
                print(f"✅ 版本上传成功!")
                print(f"   版本: {result['version']}")
                print(f"   大小: {result['file_size']} bytes")
                print(f"   SHA256: {result['sha256']}")
                return True
                
            except requests.exceptions.RequestException as e:
                print(f"❌ 上传失败: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.json()
                        print(f"   详细错误: {error_detail}")
                    except:
                        print(f"   HTTP状态码: {e.response.status_code}")
                return False
    
    def list_versions(self, platform: str = "windows", arch: str = "x64", limit: int = 10):
        """列出版本"""
        
        url = f"{self.server_url}/api/v1/versions"
        params = {
            'platform': platform,
            'arch': arch,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            versions = response.json()
            
            if not versions:
                print("没有找到版本")
                return
            
            print(f"\n版本列表 ({platform}/{arch}):")
            print("-" * 80)
            print(f"{'版本':<15} {'发布时间':<20} {'大小':<10} {'状态':<10} {'描述'}")
            print("-" * 80)
            
            for v in versions:
                size_mb = v['file_size'] / 1024 / 1024 if v['file_size'] else 0
                status = []
                if v['is_stable']:
                    status.append("稳定")
                if v['is_critical']:
                    status.append("重要")
                status_str = ",".join(status) if status else "开发"
                
                release_date = v['release_date'][:19] if v['release_date'] else "未知"
                description = v['description'][:30] + "..." if len(v['description']) > 30 else v['description']
                
                print(f"{v['version']:<15} {release_date:<20} {size_mb:<9.1f}M {status_str:<10} {description}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取版本列表失败: {e}")
    
    def check_version(self, current_version: str, platform: str = "windows", arch: str = "x64"):
        """检查版本更新"""
        
        url = f"{self.server_url}/api/v1/version/check"
        params = {
            'current_version': current_version,
            'platform': platform,
            'arch': arch
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"\n版本检查结果:")
            print(f"  当前版本: {result['current_version']}")
            print(f"  最新版本: {result['latest_version']}")
            print(f"  有更新: {'是' if result['has_update'] else '否'}")
            
            if result['has_update'] and 'update_info' in result:
                info = result['update_info']
                print(f"\n更新信息:")
                print(f"  版本: {info['version']}")
                print(f"  描述: {info['description']}")
                print(f"  发布时间: {info['release_date']}")
                print(f"  文件大小: {info['file_size'] / 1024 / 1024:.1f} MB")
                print(f"  重要更新: {'是' if info['is_critical'] else '否'}")
                print(f"  下载地址: {self.server_url}{info['download_url']}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 版本检查失败: {e}")
    
    def get_stats(self):
        """获取服务器统计信息"""
        
        url = f"{self.server_url}/api/v1/stats"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            stats = response.json()
            
            print(f"\n服务器统计信息:")
            print(f"  总版本数: {stats['total_versions']}")
            print(f"  稳定版本数: {stats['stable_versions']}")
            print(f"  服务器状态: {stats['server_status']}")
            print(f"  统计时间: {stats['timestamp']}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取统计信息失败: {e}")
    
    def health_check(self):
        """健康检查"""
        
        url = f"{self.server_url}/api/v1/health"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            health = response.json()
            
            print(f"✅ 服务器健康检查通过")
            print(f"   状态: {health['status']}")
            print(f"   版本: {health['version']}")
            print(f"   时间: {health['timestamp']}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 服务器健康检查失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="Omega更新包管理工具")
    parser.add_argument("--server", default="http://106.14.28.97", help="服务器地址")
    parser.add_argument("--api-key", help="API密钥")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 上传版本
    upload_parser = subparsers.add_parser("upload", help="上传新版本")
    upload_parser.add_argument("version", help="版本号")
    upload_parser.add_argument("file", help="文件路径")
    upload_parser.add_argument("--description", default="", help="版本描述")
    upload_parser.add_argument("--stable", action="store_true", help="标记为稳定版本")
    upload_parser.add_argument("--critical", action="store_true", help="标记为重要更新")
    upload_parser.add_argument("--platform", default="windows", help="平台")
    upload_parser.add_argument("--arch", default="x64", help="架构")
    
    # 列出版本
    list_parser = subparsers.add_parser("list", help="列出版本")
    list_parser.add_argument("--platform", default="windows", help="平台")
    list_parser.add_argument("--arch", default="x64", help="架构")
    list_parser.add_argument("--limit", type=int, default=10, help="显示数量")
    
    # 检查版本
    check_parser = subparsers.add_parser("check", help="检查版本更新")
    check_parser.add_argument("version", help="当前版本号")
    check_parser.add_argument("--platform", default="windows", help="平台")
    check_parser.add_argument("--arch", default="x64", help="架构")
    
    # 统计信息
    subparsers.add_parser("stats", help="获取统计信息")
    
    # 健康检查
    subparsers.add_parser("health", help="健康检查")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 获取API密钥
    api_key = args.api_key or os.getenv("OMEGA_API_KEY")
    if not api_key and args.command == "upload":
        print("错误: 需要API密钥才能上传文件")
        print("使用 --api-key 参数或设置 OMEGA_API_KEY 环境变量")
        return
    
    manager = UpdateManager(args.server, api_key)
    
    # 执行命令
    if args.command == "upload":
        file_path = Path(args.file)
        manager.upload_version(
            args.version, file_path, args.description,
            args.stable, args.critical, args.platform, args.arch
        )
    elif args.command == "list":
        manager.list_versions(args.platform, args.arch, args.limit)
    elif args.command == "check":
        manager.check_version(args.version, args.platform, args.arch)
    elif args.command == "stats":
        manager.get_stats()
    elif args.command == "health":
        manager.health_check()

if __name__ == "__main__":
    main()
