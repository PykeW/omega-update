#!/usr/bin/env python3
"""
Omega软件版本分析工具
分析两个版本之间的文件差异，生成详细报告
"""

import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import argparse

class FileInfo:
    """文件信息类"""
    def __init__(self, path: str, size: int, mtime: float, sha256: Optional[str] = None):
        self.path = path
        self.size = size
        self.mtime = mtime
        self.sha256 = sha256
    
    def to_dict(self):
        return {
            'path': self.path,
            'size': self.size,
            'mtime': self.mtime,
            'sha256': self.sha256
        }

class VersionAnalyzer:
    """版本分析器"""
    
    def __init__(self):
        self.chunk_size = 8192
    
    def calculate_sha256(self, file_path: Path) -> str:
        """计算文件SHA256哈希值"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(self.chunk_size), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"计算哈希失败 {file_path}: {e}")
            return ""
    
    def scan_directory(self, directory: Path, base_path: Optional[Path] = None) -> Dict[str, FileInfo]:
        """扫描目录，生成文件信息字典"""
        if base_path is None:
            base_path = directory
        
        files_info = {}
        
        print(f"扫描目录: {directory}")
        
        for root, _, files in os.walk(directory):
            root_path = Path(root)
            
            for file_name in files:
                file_path = root_path / file_name
                relative_path = file_path.relative_to(base_path)
                
                try:
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime
                    
                    # 计算哈希值（仅对小于100MB的文件）
                    sha256 = ""
                    if size < 100 * 1024 * 1024:  # 100MB
                        sha256 = self.calculate_sha256(file_path)
                    
                    files_info[str(relative_path)] = FileInfo(
                        str(relative_path), size, mtime, sha256
                    )
                    
                    if len(files_info) % 50 == 0:
                        print(f"已扫描 {len(files_info)} 个文件...")
                        
                except Exception as e:
                    print(f"处理文件失败 {file_path}: {e}")
        
        print(f"扫描完成，共 {len(files_info)} 个文件")
        return files_info
    
    def compare_versions(self, old_files: Dict[str, FileInfo], 
                        new_files: Dict[str, FileInfo]) -> Dict:
        """比较两个版本的文件差异"""
        
        old_paths = set(old_files.keys())
        new_paths = set(new_files.keys())
        
        # 分类文件
        added_files = new_paths - old_paths
        deleted_files = old_paths - new_paths
        common_files = old_paths & new_paths
        
        modified_files = []
        unchanged_files = []
        
        for file_path in common_files:
            old_file = old_files[file_path]
            new_file = new_files[file_path]
            
            # 比较大小和哈希值
            if (old_file.size != new_file.size or 
                (old_file.sha256 and new_file.sha256 and old_file.sha256 != new_file.sha256)):
                modified_files.append(file_path)
            else:
                unchanged_files.append(file_path)
        
        # 计算统计信息
        total_old_size = sum(f.size for f in old_files.values())
        total_new_size = sum(f.size for f in new_files.values())
        
        added_size = sum(new_files[f].size for f in added_files)
        deleted_size = sum(old_files[f].size for f in deleted_files)
        
        modified_old_size = sum(old_files[f].size for f in modified_files)
        modified_new_size = sum(new_files[f].size for f in modified_files)
        
        return {
            'summary': {
                'total_files_old': len(old_files),
                'total_files_new': len(new_files),
                'total_size_old': total_old_size,
                'total_size_new': total_new_size,
                'size_difference': total_new_size - total_old_size,
                'added_files_count': len(added_files),
                'deleted_files_count': len(deleted_files),
                'modified_files_count': len(modified_files),
                'unchanged_files_count': len(unchanged_files),
                'added_size': added_size,
                'deleted_size': deleted_size,
                'modified_old_size': modified_old_size,
                'modified_new_size': modified_new_size
            },
            'added_files': sorted(list(added_files)),
            'deleted_files': sorted(list(deleted_files)),
            'modified_files': sorted(modified_files),
            'unchanged_files': sorted(unchanged_files),
            'file_details': {
                'added': {f: new_files[f].to_dict() for f in added_files},
                'deleted': {f: old_files[f].to_dict() for f in deleted_files},
                'modified': {
                    f: {
                        'old': old_files[f].to_dict(),
                        'new': new_files[f].to_dict()
                    } for f in modified_files
                }
            }
        }
    
    def format_size(self, size_bytes: float) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def generate_report(self, comparison: Dict, output_file: Optional[str] = None):
        """生成分析报告"""
        summary = comparison['summary']
        
        report = []
        report.append("=" * 80)
        report.append("OMEGA软件版本差异分析报告")
        report.append("=" * 80)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 总体统计
        report.append("总体统计:")
        report.append(f"  旧版本文件数: {summary['total_files_old']:,}")
        report.append(f"  新版本文件数: {summary['total_files_new']:,}")
        report.append(f"  旧版本总大小: {self.format_size(summary['total_size_old'])}")
        report.append(f"  新版本总大小: {self.format_size(summary['total_size_new'])}")
        report.append(f"  大小变化: {self.format_size(summary['size_difference'])}")
        report.append("")
        
        # 变更统计
        report.append("变更统计:")
        report.append(f"  新增文件: {summary['added_files_count']:,} 个 ({self.format_size(summary['added_size'])})")
        report.append(f"  删除文件: {summary['deleted_files_count']:,} 个 ({self.format_size(summary['deleted_size'])})")
        report.append(f"  修改文件: {summary['modified_files_count']:,} 个")
        report.append(f"  未变更文件: {summary['unchanged_files_count']:,} 个")
        report.append("")
        
        # 详细列表
        if comparison['added_files']:
            report.append("新增文件列表:")
            for file_path in comparison['added_files'][:20]:  # 只显示前20个
                file_info = comparison['file_details']['added'][file_path]
                report.append(f"  + {file_path} ({self.format_size(file_info['size'])})")
            if len(comparison['added_files']) > 20:
                report.append(f"  ... 还有 {len(comparison['added_files']) - 20} 个文件")
            report.append("")
        
        if comparison['deleted_files']:
            report.append("删除文件列表:")
            for file_path in comparison['deleted_files'][:20]:
                file_info = comparison['file_details']['deleted'][file_path]
                report.append(f"  - {file_path} ({self.format_size(file_info['size'])})")
            if len(comparison['deleted_files']) > 20:
                report.append(f"  ... 还有 {len(comparison['deleted_files']) - 20} 个文件")
            report.append("")
        
        if comparison['modified_files']:
            report.append("修改文件列表:")
            for file_path in comparison['modified_files'][:20]:
                old_info = comparison['file_details']['modified'][file_path]['old']
                new_info = comparison['file_details']['modified'][file_path]['new']
                size_change = new_info['size'] - old_info['size']
                change_str = f"({self.format_size(old_info['size'])} → {self.format_size(new_info['size'])})"
                if size_change > 0:
                    change_str += f" +{self.format_size(size_change)}"
                elif size_change < 0:
                    change_str += f" {self.format_size(size_change)}"
                report.append(f"  * {file_path} {change_str}")
            if len(comparison['modified_files']) > 20:
                report.append(f"  ... 还有 {len(comparison['modified_files']) - 20} 个文件")
            report.append("")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"报告已保存到: {output_file}")
        
        return report_text

def main():
    parser = argparse.ArgumentParser(description='Omega软件版本分析工具')
    parser.add_argument('--old-version', required=True, help='旧版本目录路径')
    parser.add_argument('--new-version', required=True, help='新版本目录路径')
    parser.add_argument('--output-json', help='JSON输出文件路径')
    parser.add_argument('--output-report', help='报告输出文件路径')
    
    args = parser.parse_args()
    
    analyzer = VersionAnalyzer()
    
    # 扫描两个版本
    old_path = Path(args.old_version)
    new_path = Path(args.new_version)
    
    if not old_path.exists():
        print(f"错误: 旧版本目录不存在: {old_path}")
        return 1
    
    if not new_path.exists():
        print(f"错误: 新版本目录不存在: {new_path}")
        return 1
    
    print("开始分析版本差异...")
    
    old_files = analyzer.scan_directory(old_path)
    new_files = analyzer.scan_directory(new_path)
    
    comparison = analyzer.compare_versions(old_files, new_files)
    
    # 保存JSON结果
    if args.output_json:
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        print(f"详细数据已保存到: {args.output_json}")
    
    # 生成报告
    report = analyzer.generate_report(comparison, args.output_report)
    print("\n" + report)
    
    return 0

if __name__ == "__main__":
    exit(main())
