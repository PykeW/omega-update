#!/usr/bin/env python3
"""
简化的更新包制作工具
专门为GUI工具设计的可靠版本
"""

import os
import sys
import zipfile
import shutil
import hashlib
import json
from pathlib import Path
from datetime import datetime

def calculate_file_hash(file_path):
    """计算文件SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_file_info(file_path, base_path):
    """获取文件信息"""
    rel_path = os.path.relpath(file_path, base_path)
    return {
        "path": rel_path.replace("\\", "/"),
        "size": os.path.getsize(file_path),
        "hash": calculate_file_hash(file_path),
        "modified": os.path.getmtime(file_path)
    }

def should_exclude_file(file_path):
    """检查是否应该排除文件"""
    exclude_patterns = [
        # 排除大型调试文件
        '.pdb', '.ilk', '.exp', '.lib',
        # 排除临时文件
        '.tmp', '.temp', '.bak', '.old',
        # 排除日志文件
        '.log', '.logs',
        # 排除缓存文件
        '__pycache__', '.pyc', '.pyo',
        # 排除开发工具文件
        '.git', '.svn', '.vscode', '.idea',
        # 排除特定大文件（根据需要调整）
        'vcruntime140_1.dll', 'msvcp140.dll'
    ]

    file_lower = file_path.lower()
    for pattern in exclude_patterns:
        if pattern in file_lower:
            return True

    # 排除超大文件（超过100MB）
    try:
        if os.path.getsize(file_path) > 100 * 1024 * 1024:
            print(f"排除大文件: {file_path} ({os.path.getsize(file_path) / 1024 / 1024:.1f} MB)")
            return True
    except:
        pass

    return False

def scan_directory(directory):
    """扫描目录获取所有文件信息"""
    files = {}
    total_size = 0
    excluded_count = 0

    for root, dirs, filenames in os.walk(directory):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.svn', 'logs', 'temp']]

        for filename in filenames:
            file_path = os.path.join(root, filename)

            if should_exclude_file(file_path):
                excluded_count += 1
                continue

            rel_path = os.path.relpath(file_path, directory)
            file_info = get_file_info(file_path, directory)
            files[rel_path.replace("\\", "/")] = file_info
            total_size += file_info['size']

    print(f"扫描完成: {len(files)} 个文件, 总大小: {total_size / 1024 / 1024:.1f} MB, 排除: {excluded_count} 个文件")
    return files

def create_incremental_package(old_dir, new_dir, output_file):
    """创建增量更新包"""
    print(f"扫描旧版本目录: {old_dir}")
    old_files = scan_directory(old_dir)
    
    print(f"扫描新版本目录: {new_dir}")
    new_files = scan_directory(new_dir)
    
    # 分析差异
    added_files = []
    modified_files = []
    deleted_files = []
    
    # 找出新增和修改的文件
    for rel_path, file_info in new_files.items():
        if rel_path not in old_files:
            added_files.append(rel_path)
        elif old_files[rel_path]["hash"] != file_info["hash"]:
            modified_files.append(rel_path)
    
    # 找出删除的文件
    for rel_path in old_files:
        if rel_path not in new_files:
            deleted_files.append(rel_path)
    
    print(f"新增文件: {len(added_files)}")
    print(f"修改文件: {len(modified_files)}")
    print(f"删除文件: {len(deleted_files)}")
    
    # 创建更新包
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # 添加新增和修改的文件
        for rel_path in added_files + modified_files:
            source_file = os.path.join(new_dir, rel_path)
            zf.write(source_file, f"files/{rel_path}")
            print(f"添加文件: {rel_path}")
        
        # 创建更新信息
        update_info = {
            "type": "incremental",
            "timestamp": datetime.now().isoformat(),
            "old_version": os.path.basename(old_dir),
            "new_version": os.path.basename(new_dir),
            "changes": {
                "added": added_files,
                "modified": modified_files,
                "deleted": deleted_files
            },
            "total_files": len(added_files) + len(modified_files)
        }
        
        # 添加更新信息文件
        zf.writestr("update_info.json", json.dumps(update_info, indent=2, ensure_ascii=False))
        
        # 添加安装脚本
        install_script = """@echo off
echo 正在应用增量更新...

REM 复制新文件
if exist files (
    echo 复制更新文件...
    xcopy /E /Y files\\* .\\
    rmdir /S /Q files
)

REM 删除旧文件
if exist update_info.json (
    echo 清理临时文件...
    del update_info.json
)

echo 更新完成！
pause
"""
        zf.writestr("install.bat", install_script)
    
    print(f"增量更新包创建完成: {output_file}")
    return True

def create_full_package(source_dir, output_file):
    """创建完整更新包"""
    print(f"扫描源目录: {source_dir}")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arc_path)
                print(f"添加文件: {arc_path}")
        
        # 创建版本信息
        version_info = {
            "type": "full",
            "timestamp": datetime.now().isoformat(),
            "version": os.path.basename(source_dir),
            "total_files": len(list(Path(source_dir).rglob("*"))) - len(list(Path(source_dir).rglob("*/")))
        }
        
        zf.writestr("version_info.json", json.dumps(version_info, indent=2, ensure_ascii=False))
    
    print(f"完整更新包创建完成: {output_file}")
    return True

def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  制作增量包: python simple_package_maker.py incremental <old_dir> <new_dir> <output_file>")
        print("  制作完整包: python simple_package_maker.py full <source_dir> <output_file>")
        return 1
    
    package_type = sys.argv[1]
    
    try:
        if package_type == "incremental":
            if len(sys.argv) != 5:
                print("增量包需要4个参数: incremental <old_dir> <new_dir> <output_file>")
                return 1
            
            old_dir = sys.argv[2]
            new_dir = sys.argv[3]
            output_file = sys.argv[4]
            
            if not os.path.exists(old_dir):
                print(f"错误: 旧版本目录不存在: {old_dir}")
                return 1
            
            if not os.path.exists(new_dir):
                print(f"错误: 新版本目录不存在: {new_dir}")
                return 1
            
            return 0 if create_incremental_package(old_dir, new_dir, output_file) else 1
            
        elif package_type == "full":
            if len(sys.argv) != 4:
                print("完整包需要3个参数: full <source_dir> <output_file>")
                return 1
            
            source_dir = sys.argv[2]
            output_file = sys.argv[3]
            
            if not os.path.exists(source_dir):
                print(f"错误: 源目录不存在: {source_dir}")
                return 1
            
            return 0 if create_full_package(source_dir, output_file) else 1
            
        else:
            print(f"错误: 未知的包类型: {package_type}")
            return 1
            
    except Exception as e:
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
