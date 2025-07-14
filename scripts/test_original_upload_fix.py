#!/usr/bin/env python3
"""
测试原始上传问题修复
验证API密钥和上传配置是否正确
"""

import tempfile
import sys
import requests
import hashlib
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from tools.common.common_utils import get_config, get_server_url, get_api_key


def test_server_connection():
    """测试服务器连接"""
    print("🔍 测试服务器连接...")
    
    try:
        server_url = get_server_url()
        response = requests.get(f"{server_url}", timeout=10)
        
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


def test_api_authentication():
    """测试API认证"""
    print("\n🔍 测试API认证...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        
        print(f"   使用API密钥: {api_key}")
        
        # 测试通过Header认证
        headers = {"X-API-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/packages",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ API认证成功（Header方式）")
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


def test_small_file_upload():
    """测试小文件上传"""
    print("\n🔍 测试小文件上传...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        
        # 创建一个小测试文件
        test_content = "这是一个测试文件，用于验证上传功能是否正常工作。"
        test_file = Path(tempfile.mktemp(suffix='.txt'))
        test_file.write_text(test_content, encoding='utf-8')
        
        # 计算文件哈希
        file_hash = hashlib.sha256(test_content.encode('utf-8')).hexdigest()
        
        try:
            # 准备上传数据
            with open(test_file, 'rb') as f:
                files = {'file': ('test_upload.txt', f, 'text/plain')}
                data = {
                    'version': 'test-upload-fix-1.0.0',
                    'platform': 'windows',
                    'arch': 'x64',
                    'relative_path': 'test_upload.txt',
                    'package_type': 'full',
                    'description': 'Test upload fix - small file',
                    'is_stable': 'false',
                    'is_critical': 'false',
                    'api_key': api_key,
                    'file_hash': file_hash
                }
                
                print(f"   文件大小: {len(test_content)} 字节")
                print(f"   文件哈希: {file_hash}")
                
                # 发送上传请求
                response = requests.post(
                    f"{server_url}/api/v1/upload/file",
                    files=files,
                    data=data,
                    timeout=60
                )
            
            if response.status_code == 200:
                print("✅ 小文件上传成功")
                result = response.json()
                print(f"   响应: {result.get('message', 'Success')}")
                return True
            else:
                print(f"❌ 小文件上传失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return False
                
        finally:
            # 清理测试文件
            test_file.unlink(missing_ok=True)
            
    except Exception as e:
        print(f"❌ 小文件上传测试异常: {e}")
        return False


def test_upload_configuration():
    """测试上传配置"""
    print("\n🔍 检查上传配置...")
    
    try:
        config = get_config()
        
        # 检查上传相关配置
        upload_config = config.get('upload', {})
        timeout = upload_config.get('timeout', 300)
        chunk_size = upload_config.get('chunk_size', 8192)
        
        print(f"   上传超时: {timeout}秒")
        print(f"   块大小: {chunk_size}字节")
        
        # 建议优化
        suggestions = []
        if timeout < 600:
            suggestions.append("建议增加上传超时时间到600秒以上")
        
        if chunk_size < 65536:
            suggestions.append("建议增加块大小到64KB以上提高传输效率")
        
        if suggestions:
            print("   💡 优化建议:")
            for suggestion in suggestions:
                print(f"      • {suggestion}")
        else:
            print("✅ 上传配置已优化")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查上传配置失败: {e}")
        return False


def test_file_filter_config():
    """测试文件过滤配置"""
    print("\n🔍 检查文件过滤配置...")
    
    filter_config_path = Path("config/file_filter.json")
    
    if filter_config_path.exists():
        try:
            import json
            with open(filter_config_path, 'r', encoding='utf-8') as f:
                filter_config = json.load(f)
            
            exclude_patterns = filter_config.get('exclude_patterns', [])
            max_file_size = filter_config.get('max_file_size', 0)
            
            print(f"✅ 文件过滤配置已存在")
            print(f"   排除模式数量: {len(exclude_patterns)}")
            print(f"   最大文件大小: {max_file_size / (1024*1024):.1f} MB")
            
            # 检查是否包含关键排除模式
            important_patterns = ["api-ms-win-*.dll", "*.pdb", "*.tmp"]
            missing_patterns = [p for p in important_patterns if p not in exclude_patterns]
            
            if missing_patterns:
                print(f"   ⚠️  建议添加排除模式: {missing_patterns}")
            
            return True
            
        except Exception as e:
            print(f"❌ 读取文件过滤配置失败: {e}")
            return False
    else:
        print("⚠️  文件过滤配置不存在，建议运行 fix_upload_issues.py 创建")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Omega原始上传问题修复验证")
    print("=" * 60)
    
    # 测试项目
    tests = [
        ("服务器连接", test_server_connection),
        ("API认证", test_api_authentication),
        ("小文件上传", test_small_file_upload),
        ("上传配置", test_upload_configuration),
        ("文件过滤配置", test_file_filter_config)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results[test_name] = False
    
    # 总结结果
    print("\n" + "=" * 60)
    print("🎯 测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！原始上传问题已修复")
        print("\n📋 下一步建议:")
        print("   1. 尝试上传一个小的测试文件夹")
        print("   2. 如果成功，可以尝试上传完整项目")
        print("   3. 考虑部署简化版本管理系统")
    elif passed >= total * 0.8:
        print("\n✅ 大部分测试通过，上传功能基本正常")
        print("\n📋 建议:")
        print("   1. 解决失败的测试项目")
        print("   2. 进行小规模测试上传")
    else:
        print("\n⚠️  多项测试失败，需要进一步排查问题")
        print("\n📋 建议:")
        print("   1. 检查网络连接和防火墙设置")
        print("   2. 验证服务器配置")
        print("   3. 运行 fix_upload_issues.py 重新修复")


if __name__ == "__main__":
    main()
