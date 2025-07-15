#!/usr/bin/env python3
"""
将云端现有版本设置为基础版本
为简化版本管理系统做准备
"""

import sys
import requests
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from tools.common.common_utils import get_config, get_server_url, get_api_key


class CloudVersionManager:
    """云端版本管理器"""
    
    def __init__(self):
        self.server_url = get_server_url()
        self.api_key = get_api_key()
        self.db_path = "omega_updates.db"
    
    def get_current_versions(self):
        """获取当前云端版本"""
        print("🔍 获取当前云端版本...")
        
        try:
            headers = {"X-API-Key": self.api_key}
            response = requests.get(
                f"{self.server_url}/api/v1/packages",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                packages = response.json()
                print(f"✅ 获取到 {len(packages)} 个版本包")
                
                # 按平台和架构分组
                grouped = {}
                for pkg in packages:
                    key = f"{pkg.get('platform', 'unknown')}_{pkg.get('arch', 'unknown')}"
                    if key not in grouped:
                        grouped[key] = []
                    grouped[key].append(pkg)
                
                return grouped
            else:
                print(f"❌ 获取版本失败: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ 获取版本异常: {e}")
            return {}
    
    def analyze_versions(self, grouped_versions):
        """分析版本分布"""
        print("\n📊 分析版本分布...")
        
        analysis = {
            "total_packages": 0,
            "platforms": {},
            "version_patterns": {},
            "recommendations": []
        }
        
        for platform_arch, packages in grouped_versions.items():
            analysis["total_packages"] += len(packages)
            platform, arch = platform_arch.split('_', 1)
            
            if platform not in analysis["platforms"]:
                analysis["platforms"][platform] = {}
            analysis["platforms"][platform][arch] = len(packages)
            
            # 分析版本号模式
            for pkg in packages:
                version = pkg.get('version', 'unknown')
                if 'stable' in version.lower() or 'release' in version.lower():
                    analysis["version_patterns"]["stable"] = analysis["version_patterns"].get("stable", 0) + 1
                elif 'beta' in version.lower() or 'test' in version.lower():
                    analysis["version_patterns"]["beta"] = analysis["version_patterns"].get("beta", 0) + 1
                elif 'alpha' in version.lower() or 'dev' in version.lower():
                    analysis["version_patterns"]["alpha"] = analysis["version_patterns"].get("alpha", 0) + 1
                else:
                    analysis["version_patterns"]["other"] = analysis["version_patterns"].get("other", 0) + 1
        
        # 显示分析结果
        print(f"   总包数: {analysis['total_packages']}")
        print(f"   平台分布: {analysis['platforms']}")
        print(f"   版本模式: {analysis['version_patterns']}")
        
        # 生成建议
        if analysis["total_packages"] == 0:
            analysis["recommendations"].append("无现有版本，可以直接开始使用简化系统")
        elif analysis["total_packages"] <= 5:
            analysis["recommendations"].append("版本数量较少，建议设置最新版本为基础稳定版")
        else:
            analysis["recommendations"].append("版本数量较多，建议选择最稳定的版本作为基础版本")
        
        return analysis
    
    def set_base_version(self, grouped_versions):
        """设置基础版本"""
        print("\n🔧 设置基础版本...")
        
        if not grouped_versions:
            print("⚠️  没有现有版本，跳过基础版本设置")
            return True
        
        # 为每个平台架构组合选择基础版本
        base_versions = {}
        
        for platform_arch, packages in grouped_versions.items():
            platform, arch = platform_arch.split('_', 1)
            
            if not packages:
                continue
            
            # 选择最新的包作为基础版本
            latest_pkg = max(packages, key=lambda x: x.get('upload_date', ''))
            
            base_versions[platform_arch] = {
                "platform": platform,
                "architecture": arch,
                "original_version": latest_pkg.get('version', 'unknown'),
                "file_path": latest_pkg.get('file_path', ''),
                "description": f"基础版本 (从 {latest_pkg.get('version', 'unknown')} 转换)",
                "upload_date": latest_pkg.get('upload_date', datetime.now().isoformat())
            }
            
            print(f"   {platform}_{arch}: {latest_pkg.get('version', 'unknown')} → 基础稳定版")
        
        return self.create_base_versions_in_db(base_versions)
    
    def create_base_versions_in_db(self, base_versions):
        """在数据库中创建基础版本"""
        print("\n💾 在数据库中创建基础版本...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查简化版本表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='simplified_versions'
            """)
            
            if not cursor.fetchone():
                print("❌ 简化版本表不存在，请先运行集成脚本")
                conn.close()
                return False
            
            # 清空现有的简化版本（如果有）
            cursor.execute("DELETE FROM simplified_versions")
            
            # 插入基础版本
            for platform_arch, version_info in base_versions.items():
                cursor.execute("""
                    INSERT INTO simplified_versions 
                    (version_type, platform, architecture, file_path, description, 
                     upload_date, file_size, file_hash, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'stable',  # 设置为稳定版
                    version_info['platform'],
                    version_info['architecture'],
                    version_info['file_path'],
                    version_info['description'],
                    version_info['upload_date'],
                    0,  # 文件大小，需要实际计算
                    'base_version_hash',  # 占位符哈希
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                print(f"   ✅ 创建基础版本: {platform_arch}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ 成功创建 {len(base_versions)} 个基础版本")
            return True
            
        except Exception as e:
            print(f"❌ 创建基础版本失败: {e}")
            return False
    
    def verify_base_versions(self):
        """验证基础版本设置"""
        print("\n🔍 验证基础版本设置...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT version_type, platform, architecture, description, upload_date
                FROM simplified_versions
                ORDER BY platform, architecture
            """)
            
            versions = cursor.fetchall()
            conn.close()
            
            if versions:
                print("✅ 基础版本设置成功:")
                for version in versions:
                    version_type, platform, arch, desc, upload_date = version
                    print(f"   {platform}_{arch}: {version_type} - {desc}")
                return True
            else:
                print("⚠️  未找到基础版本")
                return False
                
        except Exception as e:
            print(f"❌ 验证基础版本失败: {e}")
            return False
    
    def generate_migration_summary(self, analysis, success):
        """生成迁移总结"""
        print("\n📄 生成迁移总结...")
        
        summary = {
            "migration_date": datetime.now().isoformat(),
            "operation": "set_cloud_base_version",
            "analysis": analysis,
            "success": success,
            "next_steps": [
                "重启服务器启用新API",
                "使用简化上传工具上传新版本",
                "测试三版本类型系统"
            ]
        }
        
        try:
            with open("cloud_base_version_summary.json", 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print("✅ 迁移总结已保存: cloud_base_version_summary.json")
            
        except Exception as e:
            print(f"❌ 保存迁移总结失败: {e}")
        
        return summary
    
    def run_base_version_setup(self):
        """运行基础版本设置"""
        print("=" * 60)
        print("🔄 云端版本基础化设置")
        print("=" * 60)
        
        # 获取当前版本
        grouped_versions = self.get_current_versions()
        
        # 分析版本
        analysis = self.analyze_versions(grouped_versions)
        
        # 显示建议
        print("\n💡 建议:")
        for recommendation in analysis["recommendations"]:
            print(f"   • {recommendation}")
        
        # 确认操作
        if analysis["total_packages"] > 0:
            confirm = input(f"\n❓ 是否将现有版本设置为基础稳定版？(y/N): ")
            if confirm.lower() != 'y':
                print("❌ 操作已取消")
                return False
        
        # 设置基础版本
        success = self.set_base_version(grouped_versions)
        
        # 验证设置
        if success:
            success = self.verify_base_versions()
        
        # 生成总结
        summary = self.generate_migration_summary(analysis, success)
        
        # 显示结果
        print("\n" + "=" * 60)
        print("🎯 基础版本设置结果")
        print("=" * 60)
        
        if success:
            print("🎉 基础版本设置成功！")
            print("\n📋 下一步操作:")
            print("   1. 重启服务器: python start_integrated_server.py")
            print("   2. 测试简化上传: python start_simplified_upload_tool.py")
            print("   3. 测试简化下载: python start_simplified_download_tool.py")
        else:
            print("❌ 基础版本设置失败")
            print("\n📋 建议:")
            print("   1. 检查数据库连接")
            print("   2. 确认简化API已集成")
            print("   3. 重新运行集成脚本")
        
        return success


def main():
    """主函数"""
    manager = CloudVersionManager()
    manager.run_base_version_setup()


if __name__ == "__main__":
    main()
