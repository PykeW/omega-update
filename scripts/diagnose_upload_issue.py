#!/usr/bin/env python3
"""
上传问题诊断脚本
用于分析和诊断上传失败的具体原因
"""

import requests
import json
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from tools.common.common_utils import get_config, get_server_url, get_api_key


class UploadDiagnostic:
    """上传诊断器"""
    
    def __init__(self):
        self.config = get_config()
        self.server_url = get_server_url()
        self.api_key = get_api_key()
        
    def test_server_connection(self) -> bool:
        """测试服务器连接"""
        print("🔍 测试服务器连接...")
        try:
            response = requests.get(f"{self.server_url}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务器连接正常")
                print(f"   版本: {data.get('version', 'Unknown')}")
                print(f"   状态: {data.get('status', 'Unknown')}")
                return True
            else:
                print(f"❌ 服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 服务器连接失败: {e}")
            return False
    
    def test_api_authentication(self) -> bool:
        """测试API认证"""
        print("\n🔍 测试API认证...")
        try:
            headers = {"X-API-Key": self.api_key}
            response = requests.get(
                f"{self.server_url}/api/v1/packages",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ API认证成功")
                packages = response.json()
                print(f"   当前包数量: {len(packages)}")
                return True
            elif response.status_code == 401:
                print("❌ API认证失败: 无效的API密钥")
                return False
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
        except Exception as e:
            print(f"❌ API认证测试失败: {e}")
            return False
    
    def test_upload_endpoint(self) -> bool:
        """测试上传端点"""
        print("\n🔍 测试上传端点...")
        try:
            # 创建一个小的测试文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("Test upload file content")
                test_file_path = f.name
            
            # 准备上传数据
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {
                    'version': 'test-1.0.0',
                    'platform': 'windows',
                    'arch': 'x64',
                    'relative_path': 'test.txt',
                    'package_type': 'full',
                    'description': 'Test upload',
                    'is_stable': 'false',
                    'is_critical': 'false',
                    'api_key': self.api_key,
                    'file_hash': 'test_hash'
                }
                
                # 发送上传请求
                response = requests.post(
                    f"{self.server_url}/api/v1/upload/file",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            # 清理测试文件
            os.unlink(test_file_path)
            
            if response.status_code == 200:
                print("✅ 上传端点正常")
                return True
            else:
                print(f"❌ 上传端点测试失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 上传端点测试异常: {e}")
            return False
    
    def analyze_upload_error(self, error_log: str) -> Dict[str, Any]:
        """分析上传错误日志"""
        print("\n🔍 分析上传错误...")
        
        analysis = {
            "common_errors": [],
            "suggestions": [],
            "file_types": []
        }
        
        # 分析错误模式
        if "omega.exe" in error_log:
            analysis["common_errors"].append("主执行文件上传失败")
            analysis["suggestions"].append("检查文件是否被占用或权限不足")
        
        if "api-ms-win-core" in error_log:
            analysis["common_errors"].append("Windows系统DLL文件上传失败")
            analysis["file_types"].append("Windows Runtime DLLs")
            analysis["suggestions"].append("这些是Windows运行时库文件，可能文件过大或网络超时")
        
        if "_internal" in error_log:
            analysis["common_errors"].append("PyInstaller打包的内部文件上传失败")
            analysis["suggestions"].append("考虑排除某些系统文件或增加上传超时时间")
        
        return analysis
    
    def check_file_size_limits(self) -> None:
        """检查文件大小限制"""
        print("\n🔍 检查文件大小限制...")
        
        # 检查配置中的限制
        upload_config = self.config.get('upload', {})
        timeout = upload_config.get('timeout', 300)
        chunk_size = upload_config.get('chunk_size', 8192)
        
        print(f"   上传超时: {timeout}秒")
        print(f"   块大小: {chunk_size}字节")
        
        # 建议优化
        if timeout < 600:
            print("⚠️  建议增加上传超时时间到600秒以上")
        
        if chunk_size < 65536:
            print("⚠️  建议增加块大小到64KB以上提高传输效率")
    
    def run_full_diagnosis(self) -> None:
        """运行完整诊断"""
        print("=" * 60)
        print("🏥 Omega上传问题诊断报告")
        print("=" * 60)
        
        # 基础连接测试
        server_ok = self.test_server_connection()
        auth_ok = self.test_api_authentication()
        upload_ok = self.test_upload_endpoint()
        
        # 配置检查
        self.check_file_size_limits()
        
        # 错误日志分析（基于用户提供的日志）
        error_log = """
        [ERROR] 上传失败: omega.exe
        [ERROR] 上传失败: _internal\\api-ms-win-core-console-l1-1-0.dll
        [ERROR] 上传失败: _internal\\api-ms-win-core-datetime-l1-1-0.dll
        """
        
        analysis = self.analyze_upload_error(error_log)
        
        print("\n📊 诊断结果:")
        print(f"   服务器连接: {'✅' if server_ok else '❌'}")
        print(f"   API认证: {'✅' if auth_ok else '❌'}")
        print(f"   上传端点: {'✅' if upload_ok else '❌'}")
        
        print("\n🔍 错误分析:")
        for error in analysis["common_errors"]:
            print(f"   • {error}")
        
        print("\n💡 建议解决方案:")
        for suggestion in analysis["suggestions"]:
            print(f"   • {suggestion}")
        
        # 总体建议
        print("\n🎯 主要建议:")
        print("   1. 增加上传超时时间到600秒")
        print("   2. 增加文件块大小到64KB")
        print("   3. 添加文件类型过滤，排除系统DLL文件")
        print("   4. 实现断点续传功能")
        print("   5. 添加更详细的错误日志记录")


if __name__ == "__main__":
    diagnostic = UploadDiagnostic()
    diagnostic.run_full_diagnosis()
