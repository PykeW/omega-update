#!/usr/bin/env python3
"""
测试上传修复效果
创建一个小的测试文件夹并尝试上传
"""

import tempfile
import sys
import requests
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from tools.common.common_utils import get_config, get_server_url, get_api_key


def create_test_folder():
    """创建测试文件夹"""
    print("🔧 创建测试文件夹...")
    
    # 创建临时目录
    test_dir = Path(tempfile.mkdtemp(prefix="omega_test_"))
    
    # 创建一些测试文件
    (test_dir / "test.txt").write_text("这是一个测试文件")
    (test_dir / "readme.md").write_text("# 测试项目\n这是一个测试项目")
    
    # 创建子目录
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "config.json").write_text('{"test": true}')
    
    print(f"✅ 测试文件夹创建完成: {test_dir}")
    return test_dir


def test_original_upload(test_dir):
    """测试原始上传API"""
    print("\n🧪 测试原始上传API...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        
        # 测试单个文件上传
        test_file = test_dir / "test.txt"
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            data = {
                'version': 'test-1.0.0',
                'platform': 'windows',
                'arch': 'x64',
                'relative_path': 'test.txt',
                'package_type': 'full',
                'description': 'Test upload fix',
                'is_stable': 'false',
                'is_critical': 'false',
                'api_key': api_key,
                'file_hash': 'test_hash'
            }
            
            response = requests.post(
                f"{server_url}/api/v1/upload/file",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            print("✅ 原始上传API测试成功")
            return True
        else:
            print(f"❌ 原始上传API测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 原始上传API测试异常: {e}")
        return False


def test_simplified_upload(test_dir):
    """测试简化上传API"""
    print("\n🧪 测试简化上传API...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        
        # 创建ZIP文件
        import zipfile
        zip_path = test_dir.parent / "test_upload.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in test_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(test_dir)
                    zipf.write(file_path, arcname)
        
        # 上传ZIP文件
        with open(zip_path, 'rb') as f:
            files = {'file': ('test_stable.zip', f, 'application/zip')}
            data = {
                'version_type': 'alpha',  # 使用alpha避免覆盖重要版本
                'platform': 'windows',
                'architecture': 'x64',
                'description': 'Test simplified upload fix',
                'api_key': api_key
            }
            
            response = requests.post(
                f"{server_url}/api/v2/upload/simple",
                files=files,
                data=data,
                timeout=60
            )
        
        # 清理ZIP文件
        zip_path.unlink(missing_ok=True)
        
        if response.status_code == 200:
            print("✅ 简化上传API测试成功")
            result = response.json()
            print(f"   下载URL: {result.get('download_url', 'N/A')}")
            return True
        else:
            print(f"❌ 简化上传API测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 简化上传API测试异常: {e}")
        return False


def test_download_api():
    """测试下载API"""
    print("\n🧪 测试下载API...")
    
    try:
        server_url = get_server_url()
        
        # 测试获取版本列表
        response = requests.get(
            f"{server_url}/api/v2/versions/simple",
            params={"platform": "windows", "architecture": "x64"},
            timeout=10
        )
        
        if response.status_code == 200:
            versions = response.json()
            print("✅ 版本列表获取成功")
            
            for version_type, info in versions.items():
                if info:
                    print(f"   {version_type}: {info.get('description', 'No description')}")
                else:
                    print(f"   {version_type}: 无可用版本")
            
            return True
        else:
            print(f"❌ 版本列表获取失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 下载API测试异常: {e}")
        return False


def cleanup_test_data():
    """清理测试数据"""
    print("\n🧹 清理测试数据...")
    
    try:
        server_url = get_server_url()
        api_key = get_api_key()
        
        # 删除测试版本
        response = requests.delete(
            f"{server_url}/api/v2/version/simple/alpha",
            data={'api_key': api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 测试数据清理成功")
        else:
            print(f"⚠️  测试数据清理失败: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️  测试数据清理异常: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Omega上传修复效果测试")
    print("=" * 60)
    
    # 创建测试文件夹
    test_dir = create_test_folder()
    
    try:
        # 测试原始上传API
        original_success = test_original_upload(test_dir)
        
        # 测试简化上传API
        simplified_success = test_simplified_upload(test_dir)
        
        # 测试下载API
        download_success = test_download_api()
        
        # 清理测试数据
        cleanup_test_data()
        
        # 总结结果
        print("\n" + "=" * 60)
        print("🎯 测试结果总结")
        print("=" * 60)
        print(f"原始上传API: {'✅ 通过' if original_success else '❌ 失败'}")
        print(f"简化上传API: {'✅ 通过' if simplified_success else '❌ 失败'}")
        print(f"下载API: {'✅ 通过' if download_success else '❌ 失败'}")
        
        if all([original_success, simplified_success, download_success]):
            print("\n🎉 所有测试通过！上传问题已修复")
        else:
            print("\n⚠️  部分测试失败，请检查相关配置")
        
    finally:
        # 清理测试文件夹
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n🧹 测试文件夹已清理: {test_dir}")


if __name__ == "__main__":
    main()
