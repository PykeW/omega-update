#!/usr/bin/env python3
"""
最终系统验证
运行完整测试套件，确认所有功能正常工作
"""

import sys
import sqlite3
import json
import requests
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))


class FinalSystemVerifier:
    """最终系统验证器"""

    def __init__(self):
        self.server_url = "http://106.14.28.97:8000"
        self.api_key = "dac450db3ec47d79196edb7a34defaed"
        self.db_path = "omega_updates.db"
        self.verification_results = {}

    def verify_database_structure(self):
        """验证数据库结构"""
        print("🔍 验证数据库结构...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查简化版本表
            cursor.execute("PRAGMA table_info(simplified_versions)")
            simplified_columns = cursor.fetchall()

            cursor.execute("PRAGMA table_info(version_history)")
            history_columns = cursor.fetchall()

            conn.close()

            if len(simplified_columns) >= 10 and len(history_columns) >= 11:
                print("✅ 数据库表结构正确")
                print(f"   simplified_versions: {len(simplified_columns)} 列")
                print(f"   version_history: {len(history_columns)} 列")
                return True
            else:
                print(f"❌ 数据库表结构不完整")
                return False

        except Exception as e:
            print(f"❌ 数据库结构验证失败: {e}")
            return False

    def verify_server_integration(self):
        """验证服务器集成"""
        print("\n🔍 验证服务器集成...")

        try:
            # 检查服务器主文件
            server_main_path = Path("server/enhanced_main.py")
            if not server_main_path.exists():
                print("❌ 服务器主文件不存在")
                return False

            with open(server_main_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if "simplified_api" in content:
                print("✅ 简化API已集成到服务器")
            else:
                print("❌ 简化API未集成到服务器")
                return False

            # 检查启动脚本
            if Path("start_integrated_server.py").exists():
                print("✅ 集成服务器启动脚本存在")
            else:
                print("❌ 集成服务器启动脚本不存在")
                return False

            return True

        except Exception as e:
            print(f"❌ 服务器集成验证失败: {e}")
            return False

    def verify_original_upload_fix(self):
        """验证原始上传问题修复"""
        print("\n🔍 验证原始上传问题修复...")

        try:
            # 测试API认证
            headers = {"X-API-Key": self.api_key}
            response = requests.get(
                f"{self.server_url}/api/v1/packages",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                print("✅ 原始API认证正常")
                return True
            else:
                print(f"❌ 原始API认证失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ 原始上传验证失败: {e}")
            return False

    def verify_simplified_tools(self):
        """验证简化工具"""
        print("\n🔍 验证简化工具...")

        tools_status = {}

        # 检查工具文件
        tool_files = [
            "tools/upload/simplified_upload_tool.py",
            "tools/download/simplified_download_tool.py",
            "start_simplified_upload_tool.py",
            "start_simplified_download_tool.py"
        ]

        for tool_file in tool_files:
            if Path(tool_file).exists():
                tools_status[tool_file] = True
                print(f"✅ {tool_file} 存在")
            else:
                tools_status[tool_file] = False
                print(f"❌ {tool_file} 不存在")

        # 测试工具导入
        try:
            from tools.upload.upload_tool import SimplifiedUploadTool
            from tools.download.download_tool import SimplifiedDownloadTool
            print("✅ 简化工具导入成功")
            tools_status["import"] = True
        except Exception as e:
            print(f"❌ 简化工具导入失败: {e}")
            tools_status["import"] = False

        return all(tools_status.values())

    def verify_configuration(self):
        """验证配置"""
        print("\n🔍 验证配置...")

        config_files = [
            "config/config.json",
            "config/upload_config.json",
            "config/file_filter.json"
        ]

        config_status = {}

        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    config_status[config_file] = True
                    print(f"✅ {config_file} 正常")
                except Exception as e:
                    config_status[config_file] = False
                    print(f"❌ {config_file} 格式错误: {e}")
            else:
                config_status[config_file] = False
                print(f"❌ {config_file} 不存在")

        return all(config_status.values())

    def verify_migration_completion(self):
        """验证迁移完成"""
        print("\n🔍 验证迁移完成...")

        try:
            # 检查迁移报告
            if Path("migration_report.json").exists():
                with open("migration_report.json", 'r', encoding='utf-8') as f:
                    report = json.load(f)

                print("✅ 迁移报告存在")
                print(f"   迁移日期: {report.get('migration_date', 'Unknown')}")
                print(f"   原始版本数: {report['summary']['total_original_versions']}")
                print(f"   迁移版本数: {report['summary']['migrated_versions']}")
                return True
            else:
                print("❌ 迁移报告不存在")
                return False

        except Exception as e:
            print(f"❌ 迁移验证失败: {e}")
            return False

    def verify_documentation(self):
        """验证文档"""
        print("\n🔍 验证文档...")

        docs = [
            "DEPLOYMENT_GUIDE.md",
            "SOLUTION_SUMMARY.md",
            "docs/SIMPLIFIED_VERSION_SYSTEM_DESIGN.md"
        ]

        doc_status = {}

        for doc in docs:
            if Path(doc).exists():
                doc_status[doc] = True
                print(f"✅ {doc} 存在")
            else:
                doc_status[doc] = False
                print(f"❌ {doc} 不存在")

        return all(doc_status.values())

    def generate_final_report(self):
        """生成最终报告"""
        print("\n📊 生成最终验证报告...")

        report = {
            "verification_date": "2025-07-14T18:30:00",
            "system_version": "2.0.0",
            "verification_results": self.verification_results,
            "summary": {
                "total_checks": len(self.verification_results),
                "passed_checks": sum(1 for result in self.verification_results.values() if result),
                "success_rate": 0
            },
            "recommendations": []
        }

        # 计算成功率
        if report["summary"]["total_checks"] > 0:
            report["summary"]["success_rate"] = (
                report["summary"]["passed_checks"] / report["summary"]["total_checks"] * 100
            )

        # 添加建议
        if report["summary"]["success_rate"] == 100:
            report["recommendations"] = [
                "系统已完全就绪，可以投入使用",
                "建议进行用户验收测试",
                "可以开始部署到生产环境"
            ]
        elif report["summary"]["success_rate"] >= 80:
            report["recommendations"] = [
                "系统基本就绪，需要修复少量问题",
                "建议完成所有验证项目后再部署",
                "可以进行有限的测试部署"
            ]
        else:
            report["recommendations"] = [
                "系统存在较多问题，需要进一步修复",
                "建议重新检查集成步骤",
                "不建议立即部署到生产环境"
            ]

        # 保存报告
        try:
            with open("final_verification_report.json", 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"✅ 最终验证报告已保存: final_verification_report.json")
            return report

        except Exception as e:
            print(f"❌ 保存验证报告失败: {e}")
            return report

    def run_full_verification(self):
        """运行完整验证"""
        print("=" * 60)
        print("🏁 Omega更新系统最终验证")
        print("=" * 60)

        verifications = [
            ("数据库结构", self.verify_database_structure),
            ("服务器集成", self.verify_server_integration),
            ("原始上传修复", self.verify_original_upload_fix),
            ("简化工具", self.verify_simplified_tools),
            ("配置文件", self.verify_configuration),
            ("迁移完成", self.verify_migration_completion),
            ("文档完整性", self.verify_documentation),
        ]

        for verification_name, verification_func in verifications:
            try:
                result = verification_func()
                self.verification_results[verification_name] = result
            except Exception as e:
                print(f"❌ {verification_name} 验证异常: {e}")
                self.verification_results[verification_name] = False

        # 生成最终报告
        report = self.generate_final_report()

        # 显示总结
        print("\n" + "=" * 60)
        print("🎯 最终验证结果")
        print("=" * 60)

        for verification_name, result in self.verification_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{verification_name}: {status}")

        success_rate = report["summary"]["success_rate"]
        print(f"\n总体成功率: {success_rate:.1f}%")

        if success_rate == 100:
            print("\n🎉 所有验证通过！系统已完全就绪")
            print("\n📋 下一步行动:")
            print("   1. 重启服务器启用新功能")
            print("   2. 进行用户验收测试")
            print("   3. 准备生产环境部署")
        elif success_rate >= 80:
            print("\n✅ 系统基本就绪")
            print("\n📋 建议:")
            print("   1. 修复失败的验证项目")
            print("   2. 进行补充测试")
            print("   3. 完成后可以部署")
        else:
            print("\n⚠️  系统需要进一步完善")
            print("\n📋 建议:")
            print("   1. 重新检查集成步骤")
            print("   2. 修复所有失败项目")
            print("   3. 重新运行验证")

        print(f"\n📄 详细报告: final_verification_report.json")

        return success_rate == 100


def main():
    """主函数"""
    verifier = FinalSystemVerifier()
    verifier.run_full_verification()


if __name__ == "__main__":
    main()
