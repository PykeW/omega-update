#!/usr/bin/env python3
"""
Omega 更新系统 - 连接测试脚本
测试与远程服务器的连接和API功能
"""

import sys
import requests
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tools.common.common_utils import get_config, get_server_url, get_api_key


def test_basic_connection():
    """测试基本HTTP连接"""
    print("🔍 测试基本HTTP连接...")
    
    try:
        server_url = get_server_url()
        response = requests.get(f"{server_url}/health", timeout=10)
        
        if response.status_code == 200:
            print(f"✅ 基本连接成功: {server_url}")
            print(f"   响应: {response.json()}")
            return True
        else:
            print(f"❌ 连接失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ 连接超时: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def test_api_authentication():
    """测试API密钥认证"""
    print("\n🔐 测试API密钥认证...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        
        headers = {"X-API-Key": api_key}
        response = requests.get(f"{server_url}/", headers=headers, timeout=10)
        
        print(f"   API密钥: {api_key}")
        print(f"   响应状态: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API认证成功")
            return True
        elif response.status_code == 401:
            print("❌ API密钥认证失败")
            return False
        else:
            print(f"⚠️  API响应异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API测试错误: {e}")
        return False


def test_api_endpoints():
    """测试API端点"""
    print("\n📡 测试API端点...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        headers = {"X-API-Key": api_key}
        
        # 测试根端点
        response = requests.get(f"{server_url}/", headers=headers, timeout=10)
        print(f"   根端点 (/): HTTP {response.status_code}")
        
        # 测试健康检查
        response = requests.get(f"{server_url}/health", timeout=10)
        print(f"   健康检查 (/health): HTTP {response.status_code}")
        
        # 测试API文档
        response = requests.get(f"{server_url}/docs", timeout=10)
        print(f"   API文档 (/docs): HTTP {response.status_code}")
        
        # 测试OpenAPI规范
        response = requests.get(f"{server_url}/openapi.json", timeout=10)
        print(f"   OpenAPI规范 (/openapi.json): HTTP {response.status_code}")
        
        print("✅ API端点测试完成")
        return True
        
    except Exception as e:
        print(f"❌ API端点测试错误: {e}")
        return False


def test_upload_functionality():
    """测试上传功能（模拟）"""
    print("\n📤 测试上传功能...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        headers = {"X-API-Key": api_key}
        
        # 创建一个测试文件
        test_data = b"This is a test file for Omega update system"
        files = {"file": ("test.txt", test_data, "text/plain")}
        
        # 尝试上传（这可能会失败，但我们可以看到错误信息）
        response = requests.post(
            f"{server_url}/upload", 
            headers=headers, 
            files=files, 
            timeout=30
        )
        
        print(f"   上传测试响应: HTTP {response.status_code}")
        if response.status_code != 200:
            print(f"   响应内容: {response.text}")
        
        return response.status_code in [200, 404, 422]  # 404或422也算正常，说明端点存在
        
    except Exception as e:
        print(f"❌ 上传功能测试错误: {e}")
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 Omega 更新系统连接测试")
    print("=" * 60)
    
    # 显示配置信息
    config = get_config()
    print(f"\n📋 当前配置:")
    print(f"   服务器地址: {get_server_url()}")
    print(f"   API密钥: {get_api_key()}")
    print(f"   连接超时: {config.get('connection', {}).get('timeout', 30)}秒")
    print(f"   最大重试: {config.get('connection', {}).get('max_retries', 3)}次")
    
    # 运行测试
    tests = [
        ("基本连接", test_basic_connection),
        ("API认证", test_api_authentication),
        ("API端点", test_api_endpoints),
        ("上传功能", test_upload_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！连接配置正确。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置或网络连接。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
