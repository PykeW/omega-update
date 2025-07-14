#!/usr/bin/env python3
"""
配置文件验证脚本
验证项目中所有配置文件的正确性和完整性
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# 处理 Python 版本兼容性
tomllib: Optional[Any] = None
try:
    # For Python 3.11+
    import tomllib  # type: ignore
except ImportError:
    try:
        # For Python < 3.11
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None

try:
    import yaml
except ImportError:
    yaml = None


class ConfigValidator:
    """配置文件验证器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """验证所有配置文件"""
        print("🔍 开始验证配置文件...")

        # 验证各种配置文件
        self.validate_json_files()
        self.validate_yaml_files()
        self.validate_toml_files()
        self.validate_python_files()
        self.validate_env_files()
        self.validate_gitignore()
        self.validate_vscode_config()

        # 输出结果
        self.print_results()

        return len(self.errors) == 0

    def validate_json_files(self):
        """验证 JSON 配置文件"""
        # 标准 JSON 文件
        json_files = [
            "config/config.json",
            "config/upload_config.json",
            "config/upload_config_sample.json",
            "config/batch_config_sample.json",
        ]

        # JSONC 文件（VSCode 配置，支持注释）
        jsonc_files = [
            ".vscode/settings.json",
            ".vscode/launch.json",
            ".vscode/tasks.json",
            ".vscode/extensions.json",
        ]

        # 验证标准 JSON 文件
        for file_path in json_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                    print(f"✅ {file_path}: JSON 格式正确")
                except json.JSONDecodeError as e:
                    self.errors.append(f"❌ {file_path}: JSON 格式错误 - {e}")
                except Exception as e:
                    self.errors.append(f"❌ {file_path}: 读取失败 - {e}")
            else:
                self.warnings.append(f"⚠️  {file_path}: 文件不存在")

        # 验证 JSONC 文件（简单检查文件存在性和基本语法）
        for file_path in jsonc_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 简单检查：确保有开始和结束的大括号
                    content_stripped = content.strip()
                    if content_stripped.startswith('{') and content_stripped.endswith('}'):
                        print(f"✅ {file_path}: JSONC 格式基本正确")
                    else:
                        self.errors.append(f"❌ {file_path}: JSONC 格式错误 - 缺少大括号")
                except Exception as e:
                    self.errors.append(f"❌ {file_path}: 读取失败 - {e}")
            else:
                self.warnings.append(f"⚠️  {file_path}: 文件不存在")

    def validate_yaml_files(self):
        """验证 YAML 配置文件"""
        if yaml is None:
            self.warnings.append("⚠️  PyYAML 未安装，跳过 YAML 文件验证")
            return

        yaml_files = [
            ".pre-commit-config.yaml",
        ]

        for file_path in yaml_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    print(f"✅ {file_path}: YAML 格式正确")
                except yaml.YAMLError as e:
                    self.errors.append(f"❌ {file_path}: YAML 格式错误 - {e}")
                except Exception as e:
                    self.errors.append(f"❌ {file_path}: 读取失败 - {e}")
            else:
                self.warnings.append(f"⚠️  {file_path}: 文件不存在")

    def validate_toml_files(self):
        """验证 TOML 配置文件"""
        if tomllib is None:
            self.warnings.append("⚠️  tomllib/tomli 未安装，跳过 TOML 文件验证")
            return

        toml_files = [
            "pyproject.toml",
        ]

        for file_path in toml_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'rb') as f:
                        tomllib.load(f)
                    print(f"✅ {file_path}: TOML 格式正确")
                except Exception as e:  # 使用通用异常处理，因为不同库的异常类型不同
                    self.errors.append(f"❌ {file_path}: TOML 格式错误 - {e}")
            else:
                self.warnings.append(f"⚠️  {file_path}: 文件不存在")

    def validate_python_files(self):
        """验证 Python 配置文件"""
        python_files = [
            "setup.py",
        ]

        for file_path in python_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        compile(f.read(), file_path, 'exec')
                    print(f"✅ {file_path}: Python 语法正确")
                except SyntaxError as e:
                    self.errors.append(f"❌ {file_path}: Python 语法错误 - {e}")
                except Exception as e:
                    self.errors.append(f"❌ {file_path}: 读取失败 - {e}")
            else:
                self.warnings.append(f"⚠️  {file_path}: 文件不存在")

    def validate_env_files(self):
        """验证环境变量文件"""
        env_files = [
            ".env.example",
        ]

        for file_path in env_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    required_vars = ['API_KEY', 'DATABASE_URL', 'SERVER_HOST', 'SERVER_PORT']
                    found_vars = []

                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                var_name = line.split('=')[0].strip()
                                found_vars.append(var_name)

                    missing_vars = set(required_vars) - set(found_vars)
                    if missing_vars:
                        self.warnings.append(f"⚠️  {file_path}: 缺少环境变量 - {', '.join(missing_vars)}")
                    else:
                        print(f"✅ {file_path}: 环境变量配置完整")

                except Exception as e:
                    self.errors.append(f"❌ {file_path}: 读取失败 - {e}")
            else:
                self.errors.append(f"❌ {file_path}: 必需的环境变量模板文件不存在")

    def validate_gitignore(self):
        """验证 .gitignore 文件"""
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                required_patterns = [
                    '__pycache__/',
                    '.env',
                    'venv/',
                    '*.log',
                    'dist/',
                    'build/',
                ]

                # 检查 Python 编译文件模式（*.pyc 或 *.py[cod]）
                python_patterns = ['*.pyc', '*.py[cod]']
                has_python_pattern = any(pattern in content for pattern in python_patterns)

                missing_patterns = []
                for pattern in required_patterns:
                    if pattern not in content:
                        missing_patterns.append(pattern)

                if not has_python_pattern:
                    missing_patterns.append("*.pyc 或 *.py[cod]")

                if missing_patterns:
                    self.warnings.append(f"⚠️  .gitignore: 建议添加模式 - {', '.join(missing_patterns)}")
                else:
                    print("✅ .gitignore: 包含必要的忽略模式")

            except Exception as e:
                self.errors.append(f"❌ .gitignore: 读取失败 - {e}")
        else:
            self.errors.append("❌ .gitignore: 文件不存在")

    def validate_vscode_config(self):
        """验证 VSCode 配置"""
        vscode_dir = self.project_root / ".vscode"
        if not vscode_dir.exists():
            self.warnings.append("⚠️  .vscode/: 目录不存在，建议创建 VSCode 配置")
            return

        required_files = [
            "settings.json",
            "launch.json",
            "tasks.json",
            "extensions.json",
        ]

        for file_name in required_files:
            file_path = vscode_dir / file_name
            if not file_path.exists():
                self.warnings.append(f"⚠️  .vscode/{file_name}: 建议创建此配置文件")

    def print_results(self):
        """打印验证结果"""
        print("\n" + "="*60)
        print("📋 配置文件验证结果")
        print("="*60)

        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n🎉 所有配置文件验证通过！")
        elif not self.errors:
            print(f"\n✅ 验证通过，但有 {len(self.warnings)} 个建议改进的地方")
        else:
            print(f"\n💥 验证失败，请修复 {len(self.errors)} 个错误")


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # 创建验证器并运行验证
    validator = ConfigValidator(project_root)
    success = validator.validate_all()

    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
