#!/usr/bin/env python3
"""
Omega更新系统 - 系统验证工具
重构版本 - 验证重构后的系统功能完整性
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class SystemVerifier:
    """系统验证器"""
    
    def __init__(self):
        self.project_root = project_root
        self.results = {}
    
    def verify_project_structure(self):
        """验证项目结构"""
        print("🔍 验证项目结构...")
        
        required_files = [
            "upload_gui.py",
            "download_gui.py", 
            "package_config.json"
        ]
        
        required_dirs = [
            "upload_download",
            "upload_download/upload",
            "upload_download/download",
            "upload_download/common",
            "server_setup",
            "server_setup/deploy_scripts",
            "server_setup/config_templates",
            "server_setup/maintenance_tools",
            "tools/verification",
            "tools/utilities"
        ]
        
        # 检查文件
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        # 检查目录
        missing_dirs = []
        for dir_path in required_dirs:
            if not (self.project_root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        if not missing_files and not missing_dirs:
            print("✅ 项目结构完整")
            self.results["structure"] = True
        else:
            print(f"❌ 项目结构不完整")
            if missing_files:
                print(f"   缺少文件: {missing_files}")
            if missing_dirs:
                print(f"   缺少目录: {missing_dirs}")
            self.results["structure"] = False
    
    def verify_module_imports(self):
        """验证模块导入"""
        print("🔍 验证模块导入...")
        
        modules_to_test = [
            "upload_download.common.api_client",
            "upload_download.common.common_utils",
            "upload_download.upload.upload_handler",
            "upload_download.download.download_handler"
        ]
        
        import_errors = []
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module}")
            except ImportError as e:
                print(f"❌ {module}: {e}")
                import_errors.append(module)
        
        self.results["imports"] = len(import_errors) == 0
    
    def verify_api_connection(self):
        """验证API连接"""
        print("🔍 验证API连接...")
        
        try:
            from upload_download.common.api_client import api_client
            
            # 测试连接
            result = api_client.test_connection()
            if result["success"]:
                print("✅ API连接正常")
                
                # 测试API v2状态
                status_result = api_client.get_api_v2_status()
                if status_result["success"]:
                    print("✅ API v2状态正常")
                    self.results["api"] = True
                else:
                    print(f"❌ API v2状态异常: {status_result.get('error', 'Unknown error')}")
                    self.results["api"] = False
            else:
                print(f"❌ API连接失败: {result.get('error', 'Unknown error')}")
                self.results["api"] = False
                
        except Exception as e:
            print(f"❌ API验证异常: {e}")
            self.results["api"] = False
    
    def verify_gui_startup(self):
        """验证GUI启动"""
        print("🔍 验证GUI启动能力...")
        
        try:
            # 测试上传GUI导入
            from upload_download.upload.upload_gui import UploadGUI
            print("✅ 上传GUI模块导入成功")
            
            # 测试下载GUI导入
            from upload_download.download.download_gui import DownloadGUI
            print("✅ 下载GUI模块导入成功")
            
            self.results["gui"] = True
            
        except Exception as e:
            print(f"❌ GUI验证失败: {e}")
            self.results["gui"] = False
    
    def verify_database_connection(self):
        """验证数据库连接修复"""
        print("🔍 验证数据库连接修复...")
        
        try:
            from upload_download.common.api_client import api_client
            
            # 测试获取文件列表
            result = api_client.get_files_list("stable")
            if result["success"]:
                data = result["data"]
                if "message" in data and "数据库连接不可用" in data["message"]:
                    print("⚠️ 数据库连接问题仍然存在")
                    self.results["database"] = False
                else:
                    print("✅ 数据库连接正常")
                    self.results["database"] = True
            else:
                print(f"❌ 文件列表获取失败: {result.get('error', 'Unknown error')}")
                self.results["database"] = False
                
        except Exception as e:
            print(f"❌ 数据库验证异常: {e}")
            self.results["database"] = False
    
    def generate_report(self):
        """生成验证报告"""
        print("\n" + "=" * 60)
        print("📊 系统验证报告")
        print("=" * 60)
        
        total_checks = len(self.results)
        passed_checks = sum(1 for result in self.results.values() if result)
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"📈 验证结果: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
        print()
        
        for check_name, result in self.results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {check_name.title()}: {status}")
        
        print()
        if success_rate >= 80:
            print("🎉 系统重构成功！大部分功能正常")
        elif success_rate >= 60:
            print("⚠️ 系统基本可用，但有部分问题需要修复")
        else:
            print("❌ 系统存在严重问题，需要进一步修复")
        
        print("\n💡 建议的下一步操作:")
        if not self.results.get("database", True):
            print("   1. 运行数据库修复工具: python server_setup/maintenance_tools/database_fixer.py")
        if not self.results.get("api", True):
            print("   2. 检查服务器连接和API v2部署")
        if not self.results.get("structure", True):
            print("   3. 完善项目结构，创建缺失的文件和目录")
        
        return success_rate >= 60
    
    def run_full_verification(self):
        """运行完整验证"""
        print("🚀 开始系统验证")
        print("=" * 60)
        
        self.verify_project_structure()
        self.verify_module_imports()
        self.verify_api_connection()
        self.verify_gui_startup()
        self.verify_database_connection()
        
        return self.generate_report()


def main():
    """主函数"""
    verifier = SystemVerifier()
    success = verifier.run_full_verification()
    
    if success:
        print("\n🎯 验证完成：系统可以正常使用")
        return 0
    else:
        print("\n⚠️ 验证完成：系统需要进一步修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
