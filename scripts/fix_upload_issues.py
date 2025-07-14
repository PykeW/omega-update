#!/usr/bin/env python3
"""
修复上传问题的脚本
解决API密钥不匹配和上传配置问题
"""

import json
import sys
import requests
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))


def fix_api_key_config():
    """修复API密钥配置"""
    print("🔧 修复API密钥配置...")
    
    # 正确的API密钥（从服务器端代码中获取）
    correct_api_key = "dac450db3ec47d79196edb7a34defaed"
    
    # 需要更新的配置文件
    config_files = [
        "config/config.json",
        "config/upload_config.json",
        "local_server_config.json",
        "deployment/server_config.json"
    ]
    
    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新API密钥
                if 'server' in config:
                    config['server']['api_key'] = correct_api_key
                if 'api' in config:
                    config['api']['key'] = correct_api_key
                
                # 保存更新后的配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                print(f"✅ 已更新 {config_file}")
                
            except Exception as e:
                print(f"❌ 更新 {config_file} 失败: {e}")
        else:
            print(f"⚠️  {config_file} 不存在")


def fix_upload_timeout_config():
    """修复上传超时配置"""
    print("\n🔧 修复上传超时配置...")
    
    config_path = Path("config/upload_config.json")
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 增加超时时间和块大小
            if 'upload' in config:
                config['upload']['timeout'] = 600  # 增加到10分钟
                config['upload']['chunk_size'] = 65536  # 增加到64KB
                config['upload']['retry_count'] = 5  # 增加重试次数
                config['upload']['retry_delay'] = 10  # 增加重试延迟
            
            # 保存更新后的配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print("✅ 已更新上传超时配置")
            
        except Exception as e:
            print(f"❌ 更新上传配置失败: {e}")


def test_fixed_upload():
    """测试修复后的上传功能"""
    print("\n🧪 测试修复后的上传功能...")
    
    try:
        # 测试API认证
        api_key = "dac450db3ec47d79196edb7a34defaed"
        server_url = "http://106.14.28.97:8000"
        
        headers = {"X-API-Key": api_key}
        response = requests.get(
            f"{server_url}/api/v1/packages",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ API认证测试通过")
            return True
        else:
            print(f"❌ API认证测试失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def create_file_filter_config():
    """创建文件过滤配置"""
    print("\n🔧 创建文件过滤配置...")
    
    # 创建文件过滤配置，排除系统DLL文件
    filter_config = {
        "exclude_patterns": [
            "*.tmp", "*.temp", "*.log", "*.bak",
            ".git", ".svn", "__pycache__", "*.pyc",
            "Thumbs.db", ".DS_Store",
            # 排除Windows系统DLL
            "api-ms-win-*.dll",
            "vcruntime*.dll",
            "msvcp*.dll",
            "msvcr*.dll",
            # 排除大文件
            "*.pdb"
        ],
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "skip_large_files": True
    }
    
    config_path = Path("config/file_filter.json")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(filter_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已创建文件过滤配置: {config_path}")
        
    except Exception as e:
        print(f"❌ 创建文件过滤配置失败: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("🛠️  Omega上传问题修复工具")
    print("=" * 60)
    
    # 修复API密钥配置
    fix_api_key_config()
    
    # 修复上传超时配置
    fix_upload_timeout_config()
    
    # 创建文件过滤配置
    create_file_filter_config()
    
    # 测试修复结果
    test_result = test_fixed_upload()
    
    print("\n" + "=" * 60)
    print("🎯 修复完成")
    print("=" * 60)
    
    if test_result:
        print("✅ 所有修复都已完成，上传功能应该正常工作")
        print("\n📋 建议的下一步操作:")
        print("   1. 重新启动上传工具")
        print("   2. 选择较小的测试文件夹进行上传测试")
        print("   3. 如果仍有问题，检查网络连接和防火墙设置")
    else:
        print("❌ 修复后仍有问题，请检查:")
        print("   1. 服务器是否正常运行")
        print("   2. 网络连接是否正常")
        print("   3. API密钥是否正确")


if __name__ == "__main__":
    main()
