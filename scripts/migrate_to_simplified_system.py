#!/usr/bin/env python3
"""
数据库迁移脚本
将现有的复杂版本系统迁移到简化的三版本类型系统
"""

import sqlite3
import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))


class VersionMigrator:
    """版本迁移器"""
    
    def __init__(self, old_db_path: str, new_db_path: str):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        self.migration_log = []
    
    def analyze_existing_data(self) -> Dict:
        """分析现有数据"""
        print("🔍 分析现有数据...")
        
        conn = sqlite3.connect(self.old_db_path)
        cursor = conn.cursor()
        
        analysis = {
            "total_versions": 0,
            "platforms": {},
            "version_patterns": {},
            "stable_versions": [],
            "beta_versions": [],
            "alpha_versions": []
        }
        
        try:
            # 查询现有版本
            cursor.execute("""
                SELECT version, platform, architecture, is_stable, is_critical, 
                       description, release_date, total_size, file_count
                FROM versions 
                ORDER BY release_date DESC
            """)
            
            versions = cursor.fetchall()
            analysis["total_versions"] = len(versions)
            
            for version_data in versions:
                version, platform, arch, is_stable, is_critical, desc, date, size, count = version_data
                
                # 统计平台分布
                platform_key = f"{platform}_{arch}"
                if platform_key not in analysis["platforms"]:
                    analysis["platforms"][platform_key] = 0
                analysis["platforms"][platform_key] += 1
                
                # 分析版本模式
                version_type = self._classify_version(version, is_stable, is_critical, desc)
                if version_type not in analysis["version_patterns"]:
                    analysis["version_patterns"][version_type] = 0
                analysis["version_patterns"][version_type] += 1
                
                # 分类版本
                version_info = {
                    "version": version,
                    "platform": platform,
                    "architecture": arch,
                    "description": desc,
                    "date": date,
                    "size": size,
                    "file_count": count
                }
                
                if version_type == "stable":
                    analysis["stable_versions"].append(version_info)
                elif version_type == "beta":
                    analysis["beta_versions"].append(version_info)
                else:
                    analysis["alpha_versions"].append(version_info)
            
        except Exception as e:
            print(f"❌ 分析数据失败: {e}")
        finally:
            conn.close()
        
        return analysis
    
    def _classify_version(self, version: str, is_stable: bool, is_critical: bool, 
                         description: Optional[str]) -> str:
        """
        根据版本号、稳定性标记和描述分类版本
        
        分类规则:
        - stable: is_stable=True 或版本号包含 "stable", "release", "final"
        - beta: 版本号包含 "beta", "rc", "preview" 或 is_stable=False 但不是 alpha
        - alpha: 版本号包含 "alpha", "dev", "test" 或 is_critical=True
        """
        version_lower = version.lower()
        desc_lower = (description or "").lower()
        
        # Alpha 版本识别
        alpha_keywords = ["alpha", "dev", "test", "experimental", "nightly"]
        if any(keyword in version_lower for keyword in alpha_keywords):
            return "alpha"
        if any(keyword in desc_lower for keyword in alpha_keywords):
            return "alpha"
        if is_critical:  # 关键更新通常是测试性质的
            return "alpha"
        
        # Stable 版本识别
        stable_keywords = ["stable", "release", "final", "production"]
        if is_stable:
            return "stable"
        if any(keyword in version_lower for keyword in stable_keywords):
            return "stable"
        if any(keyword in desc_lower for keyword in stable_keywords):
            return "stable"
        
        # Beta 版本识别（默认）
        beta_keywords = ["beta", "rc", "preview", "candidate"]
        if any(keyword in version_lower for keyword in beta_keywords):
            return "beta"
        if any(keyword in desc_lower for keyword in beta_keywords):
            return "beta"
        
        # 根据版本号模式判断
        if re.search(r'\d+\.\d+\.\d+$', version):  # 标准版本号格式
            return "stable"
        
        # 默认为 beta
        return "beta"
    
    def create_simplified_tables(self):
        """创建简化版本管理系统的数据库表"""
        print("🔧 创建简化数据库表...")
        
        conn = sqlite3.connect(self.new_db_path)
        cursor = conn.cursor()
        
        try:
            # 创建简化版本表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simplified_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_type VARCHAR(20) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    architecture VARCHAR(20) NOT NULL,
                    description TEXT,
                    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path VARCHAR(500) NOT NULL,
                    file_size BIGINT NOT NULL,
                    file_hash VARCHAR(64) NOT NULL,
                    uploader_info TEXT,
                    UNIQUE(version_type, platform, architecture)
                )
            """)
            
            # 创建版本历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_type VARCHAR(20) NOT NULL,
                    platform VARCHAR(50) NOT NULL,
                    architecture VARCHAR(20) NOT NULL,
                    description TEXT,
                    upload_date DATETIME,
                    file_path VARCHAR(500),
                    file_size BIGINT,
                    file_hash VARCHAR(64),
                    action VARCHAR(20),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ 数据库表创建成功")
            
        except Exception as e:
            print(f"❌ 创建数据库表失败: {e}")
        finally:
            conn.close()
    
    def migrate_data(self, analysis: Dict) -> bool:
        """执行数据迁移"""
        print("🚀 开始数据迁移...")
        
        old_conn = sqlite3.connect(self.old_db_path)
        new_conn = sqlite3.connect(self.new_db_path)
        
        try:
            old_cursor = old_conn.cursor()
            new_cursor = new_conn.cursor()
            
            # 为每个平台/架构组合选择最新的版本
            platforms = ["windows", "linux", "macos"]
            architectures = ["x64", "x86", "arm64"]
            version_types = ["stable", "beta", "alpha"]
            
            migrated_count = 0
            
            for platform in platforms:
                for arch in architectures:
                    for version_type in version_types:
                        # 查找该类型的最新版本
                        latest_version = self._find_latest_version(
                            old_cursor, platform, arch, version_type
                        )
                        
                        if latest_version:
                            # 迁移到新系统
                            success = self._migrate_version(new_cursor, latest_version, version_type)
                            if success:
                                migrated_count += 1
                                self.migration_log.append(
                                    f"迁移成功: {version_type}/{platform}/{arch} - {latest_version['version']}"
                                )
            
            new_conn.commit()
            print(f"✅ 数据迁移完成，共迁移 {migrated_count} 个版本")
            return True
            
        except Exception as e:
            print(f"❌ 数据迁移失败: {e}")
            return False
        finally:
            old_conn.close()
            new_conn.close()
    
    def _find_latest_version(self, cursor, platform: str, arch: str, 
                           version_type: str) -> Optional[Dict]:
        """查找指定类型的最新版本"""
        try:
            # 查询所有版本
            cursor.execute("""
                SELECT version, platform, architecture, is_stable, is_critical,
                       description, release_date, total_size, file_count
                FROM versions 
                WHERE platform = ? AND architecture = ?
                ORDER BY release_date DESC
            """, (platform, arch))
            
            versions = cursor.fetchall()
            
            # 找到匹配类型的最新版本
            for version_data in versions:
                version, plat, arc, is_stable, is_critical, desc, date, size, count = version_data
                classified_type = self._classify_version(version, is_stable, is_critical, desc)
                
                if classified_type == version_type:
                    return {
                        "version": version,
                        "platform": plat,
                        "architecture": arc,
                        "description": desc,
                        "upload_date": date,
                        "file_size": size or 0,
                        "file_count": count or 0
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ 查找版本失败: {e}")
            return None
    
    def _migrate_version(self, cursor, version_data: Dict, version_type: str) -> bool:
        """迁移单个版本到新系统"""
        try:
            # 构建文件路径（模拟）
            file_path = f"uploads/simplified/{version_data['platform']}/{version_data['architecture']}/{version_type}/{version_data['version']}.zip"
            
            # 生成模拟哈希值
            file_hash = f"migrated_{version_data['version']}_{version_type}"[:64]
            
            # 准备上传者信息
            uploader_info = json.dumps({
                "migrated_from": version_data['version'],
                "migration_date": datetime.now().isoformat(),
                "original_file_count": version_data['file_count']
            })
            
            # 插入到简化版本表
            cursor.execute("""
                INSERT OR REPLACE INTO simplified_versions 
                (version_type, platform, architecture, description, upload_date,
                 file_path, file_size, file_hash, uploader_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_type,
                version_data['platform'],
                version_data['architecture'],
                version_data['description'],
                version_data['upload_date'],
                file_path,
                version_data['file_size'],
                file_hash,
                uploader_info
            ))
            
            # 记录迁移历史
            cursor.execute("""
                INSERT INTO version_history 
                (version_type, platform, architecture, description, upload_date,
                 file_path, file_size, file_hash, action)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version_type,
                version_data['platform'],
                version_data['architecture'],
                version_data['description'],
                version_data['upload_date'],
                file_path,
                version_data['file_size'],
                file_hash,
                'migrated'
            ))
            
            return True
            
        except Exception as e:
            print(f"❌ 迁移版本失败: {e}")
            return False
    
    def generate_migration_report(self, analysis: Dict):
        """生成迁移报告"""
        print("\n📊 生成迁移报告...")
        
        report = {
            "migration_date": datetime.now().isoformat(),
            "original_data": analysis,
            "migration_log": self.migration_log,
            "summary": {
                "total_original_versions": analysis["total_versions"],
                "migrated_versions": len(self.migration_log),
                "migration_success_rate": len(self.migration_log) / max(1, analysis["total_versions"]) * 100
            }
        }
        
        # 保存报告
        report_path = Path("migration_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 迁移报告已保存到: {report_path}")
        
        # 打印摘要
        print("\n📋 迁移摘要:")
        print(f"   原始版本数量: {report['summary']['total_original_versions']}")
        print(f"   迁移版本数量: {report['summary']['migrated_versions']}")
        print(f"   迁移成功率: {report['summary']['migration_success_rate']:.1f}%")


def main():
    """主函数"""
    print("=" * 60)
    print("🔄 Omega版本系统迁移工具")
    print("=" * 60)
    
    # 数据库路径
    old_db = "omega_updates.db"
    new_db = "omega_updates_simplified.db"
    
    if not Path(old_db).exists():
        print(f"❌ 原数据库文件不存在: {old_db}")
        return
    
    # 创建迁移器
    migrator = VersionMigrator(old_db, new_db)
    
    # 分析现有数据
    analysis = migrator.analyze_existing_data()
    
    # 创建新数据库表
    migrator.create_simplified_tables()
    
    # 执行迁移
    success = migrator.migrate_data(analysis)
    
    # 生成报告
    migrator.generate_migration_report(analysis)
    
    if success:
        print("\n🎉 迁移完成！")
        print(f"   新数据库: {new_db}")
        print("   请备份原数据库后，将新数据库重命名为原数据库名称")
    else:
        print("\n❌ 迁移失败，请检查错误信息")


if __name__ == "__main__":
    main()
