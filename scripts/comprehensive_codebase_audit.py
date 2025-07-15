#!/usr/bin/env python3
"""
Omega更新系统代码库全面审计
识别和分类可能需要清理或整合的文件
"""

import sys
import json
import ast
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))


class CodebaseAuditor:
    """代码库审计器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.audit_results = {
            "obsolete_scripts": [],
            "redundant_docs": [],
            "legacy_configs": [],
            "test_files": [],
            "temporary_files": [],
            "reports_analysis": {},
            "config_analysis": {},
            "recommendations": {}
        }
    
    def scan_scripts_directory(self):
        """扫描scripts目录，识别过时的脚本"""
        print("🔍 扫描 /scripts 目录...")
        
        scripts_dir = self.project_root / "scripts"
        if not scripts_dir.exists():
            return
        
        # 定义脚本类别
        migration_scripts = []
        test_scripts = []
        utility_scripts = []
        obsolete_scripts = []
        
        for script_file in scripts_dir.glob("*.py"):
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 分析脚本用途
                script_info = {
                    "file": str(script_file.relative_to(self.project_root)),
                    "size": script_file.stat().st_size,
                    "purpose": self._analyze_script_purpose(content),
                    "imports": self._extract_imports(content),
                    "last_modified": datetime.fromtimestamp(script_file.stat().st_mtime).isoformat()
                }
                
                # 分类脚本
                if any(keyword in script_file.name.lower() for keyword in 
                       ['migrate', 'cleanup', 'integrate', 'legacy']):
                    migration_scripts.append(script_info)
                elif any(keyword in script_file.name.lower() for keyword in 
                         ['test', 'verify', 'check']):
                    test_scripts.append(script_info)
                elif any(keyword in script_file.name.lower() for keyword in 
                         ['demo', 'temp', 'fix']):
                    obsolete_scripts.append(script_info)
                else:
                    utility_scripts.append(script_info)
                
            except Exception as e:
                print(f"   ❌ 分析脚本失败: {script_file.name}: {e}")
        
        self.audit_results["migration_scripts"] = migration_scripts
        self.audit_results["test_scripts"] = test_scripts
        self.audit_results["utility_scripts"] = utility_scripts
        self.audit_results["obsolete_scripts"] = obsolete_scripts
        
        print(f"   📊 发现脚本: 迁移({len(migration_scripts)}) 测试({len(test_scripts)}) 工具({len(utility_scripts)}) 过时({len(obsolete_scripts)})")
    
    def _analyze_script_purpose(self, content: str) -> str:
        """分析脚本用途"""
        content_lower = content.lower()
        
        if "legacy" in content_lower and "cleanup" in content_lower:
            return "legacy_cleanup"
        elif "migrate" in content_lower:
            return "migration"
        elif "test" in content_lower and "verify" in content_lower:
            return "testing"
        elif "demo" in content_lower:
            return "demonstration"
        elif "fix" in content_lower:
            return "bug_fix"
        elif "deploy" in content_lower:
            return "deployment"
        elif "diagnose" in content_lower:
            return "diagnostics"
        else:
            return "utility"
    
    def _extract_imports(self, content: str) -> List[str]:
        """提取脚本的导入语句"""
        try:
            tree = ast.parse(content)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            return imports
        except:
            return []
    
    def scan_documentation_files(self):
        """扫描文档文件，识别冗余或过时的文档"""
        print("\n🔍 扫描文档文件...")
        
        # 扫描根目录的markdown文件
        root_docs = []
        for md_file in self.project_root.glob("*.md"):
            doc_info = self._analyze_documentation(md_file)
            root_docs.append(doc_info)
        
        # 扫描docs目录
        docs_dir_files = []
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.glob("*.md"):
                doc_info = self._analyze_documentation(md_file)
                docs_dir_files.append(doc_info)
        
        # 扫描deployment目录
        deployment_docs = []
        deployment_dir = self.project_root / "deployment"
        if deployment_dir.exists():
            for md_file in deployment_dir.glob("*.md"):
                doc_info = self._analyze_documentation(md_file)
                deployment_docs.append(doc_info)
        
        self.audit_results["root_docs"] = root_docs
        self.audit_results["docs_dir_files"] = docs_dir_files
        self.audit_results["deployment_docs"] = deployment_docs
        
        # 识别冗余文档
        self._identify_redundant_docs(root_docs + docs_dir_files + deployment_docs)
        
        print(f"   📊 发现文档: 根目录({len(root_docs)}) docs目录({len(docs_dir_files)}) deployment目录({len(deployment_docs)})")
    
    def _analyze_documentation(self, md_file: Path) -> Dict:
        """分析文档文件"""
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "file": str(md_file.relative_to(self.project_root)),
                "size": md_file.stat().st_size,
                "lines": len(content.split('\n')),
                "topics": self._extract_doc_topics(content),
                "mentions_legacy": "legacy" in content.lower() or "simplified" in content.lower(),
                "mentions_version_numbers": any(pattern in content.lower() for pattern in 
                                               ["version number", "1.0.0", "2.1.3", "版本号"]),
                "last_modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
            }
        except Exception as e:
            return {
                "file": str(md_file.relative_to(self.project_root)),
                "error": str(e)
            }
    
    def _extract_doc_topics(self, content: str) -> List[str]:
        """提取文档主题"""
        topics = []
        content_lower = content.lower()
        
        topic_keywords = {
            "deployment": ["deploy", "部署", "安装"],
            "usage": ["usage", "使用", "操作"],
            "api": ["api", "接口"],
            "troubleshooting": ["troubleshoot", "故障", "问题"],
            "setup": ["setup", "配置", "设置"],
            "migration": ["migrate", "迁移", "转换"],
            "cleanup": ["cleanup", "清理"],
            "legacy": ["legacy", "旧版", "遗留"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _identify_redundant_docs(self, all_docs: List[Dict]):
        """识别冗余文档"""
        redundant_groups = []
        
        # 按主题分组
        topic_groups = {}
        for doc in all_docs:
            if "topics" in doc:
                for topic in doc["topics"]:
                    if topic not in topic_groups:
                        topic_groups[topic] = []
                    topic_groups[topic].append(doc)
        
        # 识别可能冗余的组
        for topic, docs in topic_groups.items():
            if len(docs) > 1:
                redundant_groups.append({
                    "topic": topic,
                    "files": [doc["file"] for doc in docs],
                    "total_size": sum(doc.get("size", 0) for doc in docs)
                })
        
        self.audit_results["redundant_doc_groups"] = redundant_groups
    
    def analyze_reports_directory(self):
        """分析reports目录"""
        print("\n🔍 分析 /reports 目录...")
        
        reports_dir = self.project_root / "reports"
        if not reports_dir.exists():
            self.audit_results["reports_analysis"] = {"exists": False}
            return
        
        reports = []
        total_size = 0
        
        for report_file in reports_dir.glob("*.json"):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                file_size = report_file.stat().st_size
                total_size += file_size
                
                report_info = {
                    "file": report_file.name,
                    "size": file_size,
                    "type": self._classify_report(report_file.name, report_data),
                    "date": report_data.get("date", report_data.get("cleanup_date", 
                                          report_data.get("verification_date", "unknown"))),
                    "purpose": self._determine_report_purpose(report_file.name)
                }
                reports.append(report_info)
                
            except Exception as e:
                print(f"   ❌ 分析报告失败: {report_file.name}: {e}")
        
        self.audit_results["reports_analysis"] = {
            "exists": True,
            "total_files": len(reports),
            "total_size": total_size,
            "reports": reports,
            "archival_candidates": [r for r in reports if r["type"] in ["migration", "cleanup", "verification"]]
        }
        
        print(f"   📊 发现报告: {len(reports)} 个文件，总大小 {total_size} 字节")
    
    def _classify_report(self, filename: str, data: Dict) -> str:
        """分类报告类型"""
        filename_lower = filename.lower()
        
        if "cleanup" in filename_lower:
            return "cleanup"
        elif "migration" in filename_lower:
            return "migration"
        elif "verification" in filename_lower:
            return "verification"
        elif "test" in filename_lower:
            return "testing"
        elif "legacy" in filename_lower:
            return "legacy"
        else:
            return "operational"
    
    def _determine_report_purpose(self, filename: str) -> str:
        """确定报告用途"""
        purposes = {
            "cleanup": "记录系统清理过程",
            "migration": "记录数据迁移过程", 
            "verification": "记录系统验证结果",
            "testing": "记录测试结果",
            "legacy": "记录遗留系统处理"
        }
        
        for key, purpose in purposes.items():
            if key in filename.lower():
                return purpose
        
        return "未知用途"
    
    def analyze_config_directory(self):
        """分析config目录"""
        print("\n🔍 分析 /config 目录...")
        
        config_dir = self.project_root / "config"
        if not config_dir.exists():
            self.audit_results["config_analysis"] = {"exists": False}
            return
        
        configs = []
        
        for config_file in config_dir.glob("*"):
            if config_file.is_file():
                config_info = {
                    "file": config_file.name,
                    "size": config_file.stat().st_size,
                    "type": config_file.suffix,
                    "purpose": self._determine_config_purpose(config_file.name),
                    "essential": self._is_essential_config(config_file.name),
                    "last_modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                }
                configs.append(config_info)
        
        self.audit_results["config_analysis"] = {
            "exists": True,
            "total_files": len(configs),
            "configs": configs,
            "essential_configs": [c for c in configs if c["essential"]],
            "optional_configs": [c for c in configs if not c["essential"]]
        }
        
        print(f"   📊 发现配置: {len(configs)} 个文件")
    
    def _determine_config_purpose(self, filename: str) -> str:
        """确定配置文件用途"""
        purposes = {
            "config.json": "主配置文件",
            "upload_config.json": "上传配置",
            "file_filter.json": "文件过滤配置",
            "local_server_config.json": "本地服务器配置",
            "batch_config": "批处理配置示例",
            "upload_config_sample": "上传配置示例"
        }
        
        for key, purpose in purposes.items():
            if key in filename:
                return purpose
        
        return "未知配置"
    
    def _is_essential_config(self, filename: str) -> bool:
        """判断配置文件是否必需"""
        essential_configs = {
            "config.json",
            "upload_config.json", 
            "file_filter.json"
        }
        
        return any(essential in filename for essential in essential_configs)
    
    def generate_recommendations(self):
        """生成清理建议"""
        print("\n💡 生成清理建议...")
        
        recommendations = {
            "safe_to_delete": [],
            "archive_candidates": [],
            "consolidation_opportunities": [],
            "directory_restructuring": [],
            "maintenance_strategy": []
        }
        
        # 脚本清理建议
        for script in self.audit_results.get("obsolete_scripts", []):
            if any(keyword in script["file"] for keyword in ["demo", "temp", "fix"]):
                recommendations["safe_to_delete"].append({
                    "file": script["file"],
                    "reason": "演示或临时脚本，已完成使命",
                    "type": "script"
                })
        
        for script in self.audit_results.get("migration_scripts", []):
            recommendations["archive_candidates"].append({
                "file": script["file"],
                "reason": "迁移脚本，保留作为历史记录",
                "type": "script"
            })
        
        # 文档整合建议
        for group in self.audit_results.get("redundant_doc_groups", []):
            if len(group["files"]) > 2:
                recommendations["consolidation_opportunities"].append({
                    "files": group["files"],
                    "reason": f"多个文档涉及相同主题: {group['topic']}",
                    "type": "documentation"
                })
        
        # 报告归档建议
        reports_analysis = self.audit_results.get("reports_analysis", {})
        if reports_analysis.get("exists"):
            for report in reports_analysis.get("archival_candidates", []):
                recommendations["archive_candidates"].append({
                    "file": f"reports/{report['file']}",
                    "reason": f"{report['purpose']} - 可归档",
                    "type": "report"
                })
        
        # 目录重构建议
        recommendations["directory_restructuring"] = [
            {
                "action": "创建 /archive 目录",
                "reason": "存放历史文件和报告",
                "files": "迁移脚本、清理报告等"
            },
            {
                "action": "整理 /docs 目录",
                "reason": "按主题组织文档",
                "files": "合并重复的部署和使用指南"
            }
        ]
        
        # 维护策略
        recommendations["maintenance_strategy"] = [
            "定期清理 /reports 目录中的旧报告",
            "合并重复的文档文件",
            "移除完成使命的临时脚本",
            "保持配置文件的最小化",
            "建立文件命名规范"
        ]
        
        self.audit_results["recommendations"] = recommendations
    
    def generate_audit_report(self):
        """生成审计报告"""
        print("\n📄 生成审计报告...")
        
        report = {
            "audit_date": datetime.now().isoformat(),
            "project_status": "simplified_system_active",
            "audit_results": self.audit_results,
            "summary": {
                "total_scripts": len(self.audit_results.get("migration_scripts", [])) + 
                               len(self.audit_results.get("test_scripts", [])) + 
                               len(self.audit_results.get("utility_scripts", [])) + 
                               len(self.audit_results.get("obsolete_scripts", [])),
                "total_docs": len(self.audit_results.get("root_docs", [])) + 
                             len(self.audit_results.get("docs_dir_files", [])) + 
                             len(self.audit_results.get("deployment_docs", [])),
                "reports_count": self.audit_results.get("reports_analysis", {}).get("total_files", 0),
                "config_count": self.audit_results.get("config_analysis", {}).get("total_files", 0)
            }
        }
        
        try:
            report_path = self.project_root / "reports" / "comprehensive_codebase_audit.json"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 审计报告已保存: {report_path}")
            return report
            
        except Exception as e:
            print(f"❌ 保存审计报告失败: {e}")
            return report
    
    def run_comprehensive_audit(self):
        """运行全面审计"""
        print("=" * 60)
        print("🔍 Omega更新系统代码库全面审计")
        print("=" * 60)
        
        # 执行各项审计
        self.scan_scripts_directory()
        self.scan_documentation_files()
        self.analyze_reports_directory()
        self.analyze_config_directory()
        self.generate_recommendations()
        
        # 生成报告
        report = self.generate_audit_report()
        
        # 显示总结
        self._display_audit_summary()
        
        return report
    
    def _display_audit_summary(self):
        """显示审计总结"""
        print("\n" + "=" * 60)
        print("📊 审计结果总结")
        print("=" * 60)
        
        # 脚本统计
        migration_count = len(self.audit_results.get("migration_scripts", []))
        test_count = len(self.audit_results.get("test_scripts", []))
        utility_count = len(self.audit_results.get("utility_scripts", []))
        obsolete_count = len(self.audit_results.get("obsolete_scripts", []))
        
        print(f"\n📜 脚本文件:")
        print(f"   迁移脚本: {migration_count}")
        print(f"   测试脚本: {test_count}")
        print(f"   工具脚本: {utility_count}")
        print(f"   过时脚本: {obsolete_count}")
        
        # 文档统计
        root_docs = len(self.audit_results.get("root_docs", []))
        docs_dir = len(self.audit_results.get("docs_dir_files", []))
        deployment_docs = len(self.audit_results.get("deployment_docs", []))
        redundant_groups = len(self.audit_results.get("redundant_doc_groups", []))
        
        print(f"\n📚 文档文件:")
        print(f"   根目录文档: {root_docs}")
        print(f"   docs目录文档: {docs_dir}")
        print(f"   deployment文档: {deployment_docs}")
        print(f"   冗余文档组: {redundant_groups}")
        
        # 报告和配置统计
        reports_analysis = self.audit_results.get("reports_analysis", {})
        config_analysis = self.audit_results.get("config_analysis", {})
        
        if reports_analysis.get("exists"):
            print(f"\n📊 报告文件: {reports_analysis.get('total_files', 0)}")
        
        if config_analysis.get("exists"):
            essential_configs = len(config_analysis.get("essential_configs", []))
            optional_configs = len(config_analysis.get("optional_configs", []))
            print(f"\n⚙️  配置文件: 必需({essential_configs}) 可选({optional_configs})")
        
        # 清理建议
        recommendations = self.audit_results.get("recommendations", {})
        safe_delete = len(recommendations.get("safe_to_delete", []))
        archive_candidates = len(recommendations.get("archive_candidates", []))
        consolidation = len(recommendations.get("consolidation_opportunities", []))
        
        print(f"\n💡 清理建议:")
        print(f"   可安全删除: {safe_delete} 个文件")
        print(f"   建议归档: {archive_candidates} 个文件")
        print(f"   整合机会: {consolidation} 个组")


def main():
    """主函数"""
    auditor = CodebaseAuditor()
    auditor.run_comprehensive_audit()


if __name__ == "__main__":
    main()
