#!/usr/bin/env python3
"""
Omega更新服务器下载工具自动化打包脚本
使用PyInstaller将下载工具打包为独立的可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time


class DownloadToolBuilder:
    """下载工具构建器"""
    
    def __init__(self):
        """初始化构建器"""
        self.project_root = Path.cwd()
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.spec_file = self.project_root / "download_tool.spec"
        
        # 构建配置
        self.build_config = {
            'name': 'OmegaDownloadTool',
            'version': '3.1.0',
            'description': 'Omega更新服务器下载工具',
            'author': 'Omega Team',
            'clean_build': True,
            'upx_compress': True,
            'console_mode': False,
            'one_file': True
        }
    
    def check_dependencies(self) -> bool:
        """检查构建依赖"""
        print("🔍 检查构建依赖...")
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print(f"✓ PyInstaller: {PyInstaller.__version__}")
        except ImportError:
            print("✗ PyInstaller 未安装")
            print("请运行: pip install pyinstaller")
            return False
        
        # 检查主要模块
        required_modules = [
            'tkinter',
            'requests',
            'pathlib',
            'threading',
            'json'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                print(f"✓ {module}")
            except ImportError:
                missing_modules.append(module)
                print(f"✗ {module}")
        
        if missing_modules:
            print(f"缺少模块: {', '.join(missing_modules)}")
            return False
        
        # 检查项目文件
        required_files = [
            'download_tool.py',
            'ui_factory.py',
            'download_handler.py',
            'common_utils.py',
            'local_file_scanner.py',
            'difference_detector.py',
            'download_manager.py',
            'config.json'
        ]
        
        missing_files = []
        for file_name in required_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                print(f"✓ {file_name}")
            else:
                missing_files.append(file_name)
                print(f"✗ {file_name}")
        
        if missing_files:
            print(f"缺少文件: {', '.join(missing_files)}")
            return False
        
        print("✓ 所有依赖检查通过")
        return True
    
    def clean_build_directories(self):
        """清理构建目录"""
        if self.build_config['clean_build']:
            print("🧹 清理构建目录...")
            
            for directory in [self.build_dir, self.dist_dir]:
                if directory.exists():
                    shutil.rmtree(directory)
                    print(f"✓ 已清理: {directory}")
            
            # 清理spec文件生成的临时文件
            for pattern in ['*.pyc', '__pycache__']:
                for file_path in self.project_root.rglob(pattern):
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
    
    def create_version_file(self) -> Path:
        """创建版本信息文件"""
        version_info = f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(3, 1, 0, 0),
    prodvers=(3, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Omega Team'),
        StringStruct(u'FileDescription', u'{self.build_config["description"]}'),
        StringStruct(u'FileVersion', u'{self.build_config["version"]}'),
        StringStruct(u'InternalName', u'{self.build_config["name"]}'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 Omega Team'),
        StringStruct(u'OriginalFilename', u'{self.build_config["name"]}.exe'),
        StringStruct(u'ProductName', u'Omega更新服务器'),
        StringStruct(u'ProductVersion', u'{self.build_config["version"]}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        
        version_file = self.project_root / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_info)
        
        return version_file
    
    def build_executable(self) -> bool:
        """构建可执行文件"""
        print("🔨 开始构建可执行文件...")
        
        # 构建PyInstaller命令
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
        ]
        
        # 使用spec文件或直接参数
        if self.spec_file.exists():
            print(f"使用spec文件: {self.spec_file}")
            cmd.append(str(self.spec_file))
        else:
            print("使用直接参数构建")
            cmd.extend([
                '--onefile' if self.build_config['one_file'] else '--onedir',
                '--name', self.build_config['name'],
                '--distpath', str(self.dist_dir),
                '--workpath', str(self.build_dir),
            ])
            
            if not self.build_config['console_mode']:
                cmd.append('--windowed')
            
            if self.build_config['upx_compress']:
                cmd.append('--upx-dir')
            
            # 添加隐藏导入
            hidden_imports = [
                'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
                'common_utils', 'ui_factory', 'download_handler',
                'local_file_scanner', 'difference_detector', 'download_manager',
                'requests', 'urllib3', 'threading', 'pathlib', 'json'
            ]
            
            for module in hidden_imports:
                cmd.extend(['--hidden-import', module])
            
            # 添加数据文件
            cmd.extend(['--add-data', 'config.json;.'])
            
            # 主程序文件
            cmd.append('download_tool.py')
        
        # 执行构建
        print(f"执行命令: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            end_time = time.time()
            
            if result.returncode == 0:
                print(f"✓ 构建成功，耗时: {end_time - start_time:.1f}秒")
                return True
            else:
                print(f"✗ 构建失败")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
                
        except Exception as e:
            print(f"✗ 构建异常: {e}")
            return False
    
    def verify_build(self) -> bool:
        """验证构建结果"""
        print("🔍 验证构建结果...")
        
        # 查找生成的可执行文件
        exe_name = f"{self.build_config['name']}.exe"
        exe_path = self.dist_dir / exe_name
        
        if not exe_path.exists():
            print(f"✗ 可执行文件不存在: {exe_path}")
            return False
        
        # 检查文件大小
        file_size = exe_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        print(f"✓ 可执行文件: {exe_path}")
        print(f"✓ 文件大小: {size_mb:.1f} MB")
        
        # 检查是否过大
        if size_mb > 100:
            print("⚠ 警告: 文件大小较大，考虑优化")
        
        return True
    
    def create_distribution_package(self):
        """创建分发包"""
        print("📦 创建分发包...")
        
        # 创建分发目录
        package_dir = self.project_root / f"OmegaDownloadTool_v{self.build_config['version']}"
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()
        
        # 复制可执行文件
        exe_name = f"{self.build_config['name']}.exe"
        exe_path = self.dist_dir / exe_name
        if exe_path.exists():
            shutil.copy2(exe_path, package_dir / exe_name)
            print(f"✓ 复制可执行文件: {exe_name}")
        
        # 复制配置文件
        config_files = ['config.json', 'README.md']
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                shutil.copy2(config_path, package_dir / config_file)
                print(f"✓ 复制配置文件: {config_file}")
        
        # 创建使用说明
        readme_content = f"""# Omega更新服务器下载工具 v{self.build_config['version']}

## 使用说明

1. 双击 {exe_name} 启动程序
2. 选择本地文件夹
3. 输入目标版本号
4. 点击"扫描本地文件"
5. 点击"检查更新"
6. 选择要下载的文件
7. 点击"开始下载"

## 配置文件

- config.json: 服务器配置文件
- 可以修改服务器地址和API密钥

## 系统要求

- Windows 7 或更高版本
- 网络连接

## 技术支持

如有问题，请联系技术支持团队。

---
构建时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
版本: {self.build_config['version']}
"""
        
        with open(package_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✓ 分发包创建完成: {package_dir}")
        return package_dir
    
    def build(self) -> bool:
        """执行完整构建流程"""
        print("🚀 开始构建Omega下载工具...")
        print("="*50)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 清理构建目录
        self.clean_build_directories()
        
        # 构建可执行文件
        if not self.build_executable():
            return False
        
        # 验证构建结果
        if not self.verify_build():
            return False
        
        # 创建分发包
        package_dir = self.create_distribution_package()
        
        print("="*50)
        print("🎉 构建完成！")
        print(f"📁 分发包位置: {package_dir}")
        print(f"📄 可执行文件: {self.build_config['name']}.exe")
        print("="*50)
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Omega下载工具构建脚本")
    parser.add_argument('--no-clean', action='store_true', help='不清理构建目录')
    parser.add_argument('--console', action='store_true', help='启用控制台模式')
    parser.add_argument('--no-upx', action='store_true', help='禁用UPX压缩')
    parser.add_argument('--onedir', action='store_true', help='创建目录分发版本')
    
    args = parser.parse_args()
    
    # 创建构建器
    builder = DownloadToolBuilder()
    
    # 应用命令行参数
    if args.no_clean:
        builder.build_config['clean_build'] = False
    if args.console:
        builder.build_config['console_mode'] = True
    if args.no_upx:
        builder.build_config['upx_compress'] = False
    if args.onedir:
        builder.build_config['one_file'] = False
    
    # 执行构建
    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
