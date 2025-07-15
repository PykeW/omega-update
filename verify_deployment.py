#!/usr/bin/env python3
"""
Omega服务器部署验证脚本
验证API v2端点和增量上传功能
"""

import sys
import requests
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from tools.common.common_utils import get_server_url, get_api_key


class DeploymentVerifier:
    """部署验证器"""
    
    def __init__(self):
        self.server_url = get_server_url()
        self.api_key = get_api_key()
        
    def print_section(self, title: str):
        """打印章节标题"""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print(f"{'='*60}")
    
    def print_result(self, status: str, message: str, details: str = ""):
        """打印结果"""
        icons = {"✅": "✅", "❌": "❌", "⚠️": "⚠️", "ℹ️": "ℹ️"}
        icon = icons.get(status, "•")
        print(f"{icon} {message}")
        if details:
            print(f"   {details}")
    
    def verify_basic_connectivity(self) -> bool:
        """验证基础连接"""
        self.print_section("基础连接验证")
        
        try:
            response = requests.get(self.server_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.print_result("✅", f"服务器连接正常: {self.server_url}")
                self.print_result("ℹ️", f"服务器版本: {data.get('version', 'unknown')}")
                self.print_result("ℹ️", f"服务器状态: {data.get('status', 'unknown')}")
                return True
            else:
                self.print_result("❌", f"服务器响应异常: {response.status_code}")
                return False
        except Exception as e:
            self.print_result("❌", f"服务器连接失败: {e}")
            return False
    
    def verify_api_v2_endpoints(self) -> bool:
        """验证API v2端点"""
        self.print_section("API v2端点验证")
        
        endpoints = [
            ("/api/v2/status/simple", "状态查询端点"),
            ("/api/v2/files/simple/stable", "文件列表端点"),
        ]
        
        all_working = True
        
        for endpoint, description in endpoints:
            try:
                url = f"{self.server_url}{endpoint}"
                
                # 为文件列表端点添加参数
                if "files" in endpoint:
                    params = {"platform": "windows", "architecture": "x64"}
                    response = requests.get(url, params=params, timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.print_result("✅", f"{description}: {endpoint}")
                    
                    # 显示响应内容
                    try:
                        data = response.json()
                        if 'system' in data:
                            self.print_result("ℹ️", f"系统: {data['system']}")
                        if 'api_version' in data:
                            self.print_result("ℹ️", f"API版本: {data['api_version']}")
                        if 'total_files' in data:
                            self.print_result("ℹ️", f"文件数: {data['total_files']}")
                        if 'message' in data:
                            self.print_result("ℹ️", f"消息: {data['message']}")
                    except:
                        pass
                        
                else:
                    self.print_result("❌", f"{description}: {endpoint} (状态码: {response.status_code})")
                    all_working = False
                    
            except Exception as e:
                self.print_result("❌", f"{description}: {endpoint} (错误: {e})")
                all_working = False
        
        return all_working
    
    def verify_upload_endpoint(self) -> bool:
        """验证上传端点"""
        self.print_section("上传端点验证")
        
        try:
            url = f"{self.server_url}/api/v2/upload/simple/file"
            
            # 使用OPTIONS方法测试端点是否存在
            response = requests.options(url, timeout=10)
            
            if response.status_code in [200, 405]:  # 405表示方法不允许但端点存在
                self.print_result("✅", f"上传端点存在: /api/v2/upload/simple/file")
                if 'Allow' in response.headers:
                    self.print_result("ℹ️", f"支持方法: {response.headers['Allow']}")
                return True
            elif response.status_code == 404:
                self.print_result("❌", "上传端点不存在")
                return False
            else:
                self.print_result("⚠️", f"上传端点响应异常: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_result("❌", f"上传端点测试失败: {e}")
            return False
    
    def verify_incremental_upload_logic(self) -> bool:
        """验证增量上传逻辑"""
        self.print_section("增量上传功能验证")
        
        try:
            from tools.upload.incremental_uploader import RemoteFileRetriever
            
            retriever = RemoteFileRetriever()
            
            # 测试不同版本类型
            test_cases = [
                ("stable", "windows", "x64"),
                ("beta", "windows", "x64"),
                ("alpha", "windows", "x64")
            ]
            
            all_working = True
            total_files = 0
            
            for version_type, platform, architecture in test_cases:
                try:
                    remote_files = retriever.get_remote_files(version_type, platform, architecture)
                    file_count = len(remote_files)
                    total_files += file_count
                    
                    self.print_result("✅", f"远程文件获取成功: {version_type}/{platform}/{architecture}")
                    self.print_result("ℹ️", f"文件数: {file_count}")
                    
                    if file_count > 0:
                        # 显示前几个文件
                        for i, (path, file_info) in enumerate(remote_files.items()):
                            if i >= 2:  # 只显示前2个
                                break
                            self.print_result("ℹ️", f"  📄 {path} ({file_info.file_size} bytes)")
                    
                except Exception as e:
                    self.print_result("❌", f"远程文件获取失败: {version_type}/{platform}/{architecture} - {e}")
                    all_working = False
            
            self.print_result("ℹ️", f"总远程文件数: {total_files}")
            
            if total_files == 0:
                self.print_result("🎯", "远程服务器没有文件，这解释了为什么增量上传显示'全部新增'")
                self.print_result("💡", "这是正常行为，完成上传后再次测试增量功能")
            
            return all_working
            
        except Exception as e:
            self.print_result("❌", f"增量上传逻辑测试失败: {e}")
            return False
    
    def test_upload_tool_integration(self) -> bool:
        """测试上传工具集成"""
        self.print_section("上传工具集成测试")
        
        try:
            from tools.upload.upload_handler import UploadHandler
            
            # 检查上传处理器配置
            upload_handler = UploadHandler()
            self.print_result("✅", "UploadHandler初始化成功")
            
            # 检查端点配置
            expected_endpoint = f"{self.server_url}/api/v2/upload/simple/file"
            self.print_result("ℹ️", f"预期上传端点: {expected_endpoint}")
            
            return True
            
        except Exception as e:
            self.print_result("❌", f"上传工具集成测试失败: {e}")
            return False
    
    def generate_deployment_report(self, basic_ok: bool, api_v2_ok: bool, 
                                 upload_ok: bool, incremental_ok: bool, 
                                 integration_ok: bool) -> None:
        """生成部署报告"""
        self.print_section("部署验证综合报告")
        
        # 计算成功率
        total_checks = 5
        passed_checks = sum([basic_ok, api_v2_ok, upload_ok, incremental_ok, integration_ok])
        success_rate = (passed_checks / total_checks) * 100
        
        print(f"📊 部署验证结果:")
        print(f"   通过检查: {passed_checks}/{total_checks}")
        print(f"   成功率: {success_rate:.1f}%")
        
        print(f"\n🎯 详细结果:")
        self.print_result("✅" if basic_ok else "❌", f"基础连接: {'正常' if basic_ok else '异常'}")
        self.print_result("✅" if api_v2_ok else "❌", f"API v2端点: {'正常' if api_v2_ok else '异常'}")
        self.print_result("✅" if upload_ok else "❌", f"上传端点: {'正常' if upload_ok else '异常'}")
        self.print_result("✅" if incremental_ok else "❌", f"增量上传: {'正常' if incremental_ok else '异常'}")
        self.print_result("✅" if integration_ok else "❌", f"工具集成: {'正常' if integration_ok else '异常'}")
        
        print(f"\n💡 部署状态评估:")
        if success_rate >= 80:
            self.print_result("🎉", "部署成功！系统可以正常使用")
            print(f"\n🎯 下一步操作:")
            print(f"   1. 测试增量上传功能:")
            print(f"      python start_upload_tool.py")
            print(f"   2. 选择文件夹并启用增量上传模式")
            print(f"   3. 点击'分析差异'验证功能")
            print(f"   4. 完成上传测试")
        elif success_rate >= 60:
            self.print_result("⚠️", "部分功能正常，但存在问题")
            print(f"\n🔧 建议操作:")
            print(f"   1. 检查失败的组件")
            print(f"   2. 重新运行部署脚本")
            print(f"   3. 查看服务器日志")
        else:
            self.print_result("❌", "部署失败，需要重新部署")
            print(f"\n🔧 修复建议:")
            print(f"   1. 重新运行部署脚本: bash deploy_omega_server.sh")
            print(f"   2. 检查服务器状态和日志")
            print(f"   3. 手动验证API端点")
        
        print(f"\n📋 服务器信息:")
        print(f"   服务器地址: {self.server_url}")
        print(f"   API密钥: {self.api_key[:16]}...")
        print(f"   验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run_full_verification(self) -> bool:
        """运行完整验证"""
        print("🚀 开始Omega服务器部署验证")
        print("检查API v2端点和增量上传功能")
        
        # 执行所有验证
        basic_ok = self.verify_basic_connectivity()
        api_v2_ok = self.verify_api_v2_endpoints()
        upload_ok = self.verify_upload_endpoint()
        incremental_ok = self.verify_incremental_upload_logic()
        integration_ok = self.test_upload_tool_integration()
        
        # 生成报告
        self.generate_deployment_report(
            basic_ok, api_v2_ok, upload_ok, incremental_ok, integration_ok
        )
        
        # 返回总体成功状态
        return all([basic_ok, api_v2_ok, upload_ok, incremental_ok, integration_ok])


def main():
    """主函数"""
    verifier = DeploymentVerifier()
    success = verifier.run_full_verification()
    
    # 设置退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
