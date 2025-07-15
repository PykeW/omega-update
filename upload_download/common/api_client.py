#!/usr/bin/env python3
"""
Omega更新系统 - API客户端
重构版本 - 统一的API访问接口，解决数据库连接问题
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

class OmegaAPIClient:
    """Omega服务器API客户端"""
    
    def __init__(self, server_url: str = "http://106.14.28.97:8000", api_key: str = None):
        """
        初始化API客户端
        
        Args:
            server_url: 服务器URL
            api_key: API密钥
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key or "dac450db3ec47d79196edb7a34defaed"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Omega-Update-Client/2.0.0',
            'X-API-Key': self.api_key
        })
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> Dict[str, Any]:
        """测试服务器连接"""
        try:
            response = self.session.get(f"{self.server_url}/", timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def get_api_v2_status(self) -> Dict[str, Any]:
        """获取API v2状态"""
        try:
            response = self.session.get(f"{self.server_url}/api/v2/status/simple", timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json(),
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def get_files_list(self, version_type: str, platform: str = "windows", architecture: str = "x64") -> Dict[str, Any]:
        """
        获取文件列表
        
        Args:
            version_type: 版本类型 (stable/beta/alpha)
            platform: 平台 (windows/linux/macos)
            architecture: 架构 (x64/x86/arm64)
        """
        try:
            url = f"{self.server_url}/api/v2/files/simple/{version_type}"
            params = {
                "platform": platform,
                "architecture": architecture
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return {
                "success": True,
                "data": data,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def get_all_versions_files(self, platform: str = "windows", architecture: str = "x64") -> Dict[str, Any]:
        """获取所有版本的文件列表"""
        results = {}
        version_types = ["stable", "beta", "alpha"]
        
        for version_type in version_types:
            result = self.get_files_list(version_type, platform, architecture)
            results[version_type] = result
        
        # 统计总体信息
        total_files = 0
        total_size = 0
        all_files = []
        
        for version_type, result in results.items():
            if result["success"] and "data" in result:
                data = result["data"]
                if "files" in data:
                    all_files.extend(data["files"])
                    total_files += data.get("total_files", 0)
                    total_size += data.get("total_size", 0)
        
        return {
            "success": True,
            "data": {
                "versions": results,
                "summary": {
                    "total_files": total_files,
                    "total_size": total_size,
                    "all_files": all_files,
                    "platform": platform,
                    "architecture": architecture
                }
            }
        }
    
    def upload_file(self, file_path: Path, version_type: str, platform: str = "windows", architecture: str = "x64") -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file_path: 文件路径
            version_type: 版本类型
            platform: 平台
            architecture: 架构
        """
        try:
            url = f"{self.server_url}/api/v2/upload/simple/file"
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                data = {
                    'version_type': version_type,
                    'platform': platform,
                    'architecture': architecture,
                    'relative_path': str(file_path.name)
                }
                
                response = self.session.post(url, files=files, data=data, timeout=300)
                response.raise_for_status()
                
                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def check_server_health(self) -> Dict[str, Any]:
        """检查服务器健康状态"""
        health_checks = {
            "connection": self.test_connection(),
            "api_v2_status": self.get_api_v2_status(),
            "files_stable": self.get_files_list("stable"),
            "files_beta": self.get_files_list("beta"),
            "files_alpha": self.get_files_list("alpha")
        }
        
        # 计算健康分数
        success_count = sum(1 for check in health_checks.values() if check["success"])
        total_checks = len(health_checks)
        health_score = (success_count / total_checks) * 100
        
        return {
            "success": health_score > 60,  # 60%以上认为健康
            "health_score": health_score,
            "checks": health_checks,
            "summary": {
                "passed": success_count,
                "total": total_checks,
                "status": "healthy" if health_score > 80 else "degraded" if health_score > 60 else "unhealthy"
            }
        }


# 全局API客户端实例
api_client = OmegaAPIClient()


def get_api_client() -> OmegaAPIClient:
    """获取全局API客户端实例"""
    return api_client


def test_api_connection() -> bool:
    """快速测试API连接"""
    result = api_client.test_connection()
    return result["success"]


def get_remote_files(version_type: str = "stable", platform: str = "windows", architecture: str = "x64") -> List[Dict]:
    """获取远程文件列表的简化接口"""
    result = api_client.get_files_list(version_type, platform, architecture)
    if result["success"] and "data" in result:
        return result["data"].get("files", [])
    return []
