#!/usr/bin/env python3
"""
Omega服务器 - 数据库修复工具
重构版本 - 修复数据库连接和表结构问题
"""

import subprocess
import json
from pathlib import Path

class DatabaseFixer:
    """数据库修复器"""
    
    def __init__(self):
        self.server_ip = "106.14.28.97"
        self.username = "root"
        self.project_path = "/opt/omega-update-server"
    
    def ssh_execute(self, command: str) -> tuple:
        """执行SSH命令"""
        try:
            full_command = f"ssh {self.username}@{self.server_ip} '{command}'"
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e)
    
    def check_database_structure(self):
        """检查数据库结构"""
        print("🔍 检查数据库结构...")
        
        # 检查表
        success, output, error = self.ssh_execute(
            f"cd {self.project_path} && sqlite3 omega_updates.db '.tables'"
        )
        
        if success:
            print(f"✅ 数据库表: {output}")
            return output.split()
        else:
            print(f"❌ 检查表失败: {error}")
            return []
    
    def check_table_schema(self, table_name: str):
        """检查表结构"""
        print(f"🔍 检查表 {table_name} 的结构...")
        
        success, output, error = self.ssh_execute(
            f"cd {self.project_path} && sqlite3 omega_updates.db '.schema {table_name}'"
        )
        
        if success:
            print(f"✅ 表结构: {output}")
            return output
        else:
            print(f"❌ 检查表结构失败: {error}")
            return None
    
    def fix_api_v2_database_connection(self):
        """修复API v2数据库连接问题"""
        print("🔧 修复API v2数据库连接问题...")
        
        # 检查当前数据库结构
        tables = self.check_database_structure()
        
        # 检查是否有简化版本管理表
        required_tables = ["simplified_versions", "simplified_files"]
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠️ 缺少表: {missing_tables}")
            self.create_missing_tables(missing_tables)
        else:
            print("✅ 所有必需的表都存在")
        
        # 检查数据
        self.check_table_data()
    
    def create_missing_tables(self, missing_tables: list):
        """创建缺失的表"""
        print("🔧 创建缺失的数据库表...")
        
        # 简化版本表结构
        simplified_versions_sql = """
        CREATE TABLE IF NOT EXISTS simplified_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_type TEXT NOT NULL,
            platform TEXT NOT NULL,
            architecture TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 简化文件表结构
        simplified_files_sql = """
        CREATE TABLE IF NOT EXISTS simplified_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER,
            file_hash TEXT,
            relative_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (version_id) REFERENCES simplified_versions (id)
        );
        """
        
        if "simplified_versions" in missing_tables:
            success, output, error = self.ssh_execute(
                f"cd {self.project_path} && sqlite3 omega_updates.db \"{simplified_versions_sql}\""
            )
            if success:
                print("✅ 创建 simplified_versions 表成功")
            else:
                print(f"❌ 创建 simplified_versions 表失败: {error}")
        
        if "simplified_files" in missing_tables:
            success, output, error = self.ssh_execute(
                f"cd {self.project_path} && sqlite3 omega_updates.db \"{simplified_files_sql}\""
            )
            if success:
                print("✅ 创建 simplified_files 表成功")
            else:
                print(f"❌ 创建 simplified_files 表失败: {error}")
    
    def check_table_data(self):
        """检查表数据"""
        print("🔍 检查表数据...")
        
        tables_to_check = ["simplified_versions", "simplified_files"]
        
        for table in tables_to_check:
            success, output, error = self.ssh_execute(
                f"cd {self.project_path} && sqlite3 omega_updates.db 'SELECT COUNT(*) FROM {table};'"
            )
            
            if success:
                print(f"✅ 表 {table} 记录数: {output}")
            else:
                print(f"❌ 检查表 {table} 失败: {error}")
    
    def migrate_existing_data(self):
        """迁移现有数据"""
        print("🔄 检查是否需要迁移现有数据...")
        
        # 检查uploads目录中的文件
        success, output, error = self.ssh_execute(
            "find /var/www/omega-updates/uploads -type f | wc -l"
        )
        
        if success and output.strip() != "0":
            print(f"📊 发现 {output.strip()} 个上传文件")
            print("💡 建议：运行数据迁移脚本来将现有文件信息导入数据库")
        else:
            print("ℹ️ 没有发现现有上传文件")
    
    def run_full_fix(self):
        """运行完整的修复流程"""
        print("🚀 开始数据库修复流程")
        print("=" * 50)
        
        self.fix_api_v2_database_connection()
        self.migrate_existing_data()
        
        print("=" * 50)
        print("🎉 数据库修复完成！")
        print("💡 建议重启服务器服务以应用更改")


def main():
    """主函数"""
    fixer = DatabaseFixer()
    fixer.run_full_fix()


if __name__ == "__main__":
    main()
