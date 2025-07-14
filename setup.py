#!/usr/bin/env python3
"""
Omega 更新系统 - 安装配置文件
一个完整的软件更新管理系统，支持完整包、增量包和智能存储管理。
"""

from setuptools import setup, find_packages
import os
import sys

# 确保 Python 版本兼容性
if sys.version_info < (3, 8):
    raise RuntimeError("Omega 更新系统需要 Python 3.8 或更高版本")

# 读取 README 文件作为长描述
def read_readme():
    """读取 README.md 文件内容"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取版本信息
def get_version():
    """从版本文件或环境变量获取版本号"""
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "2.0.0"  # 默认版本

# 读取依赖列表
def get_requirements():
    """从 requirements.txt 读取依赖列表"""
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # 如果没有 requirements.txt，从 Pipfile 推断基本依赖
    return [
        'fastapi>=0.104.0',
        'uvicorn[standard]>=0.24.0',
        'sqlalchemy>=2.0.0',
        'python-multipart>=0.0.6',
        'python-dotenv>=1.0.0',
        'requests>=2.31.0',
        'psutil>=5.9.0',
        'bsdiff4>=1.2.0',
    ]

# 开发依赖
dev_requirements = [
    'pytest>=7.4.0',
    'pytest-cov>=4.1.0',
    'black>=23.0.0',
    'flake8>=6.0.0',
    'isort>=5.12.0',
    'mypy>=1.5.0',
    'pre-commit>=3.4.0',
]

setup(
    # 基本信息
    name="omega-update",
    version=get_version(),
    description="一个完整的软件更新管理系统，支持完整包、增量包和智能存储管理",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    # 作者信息
    author="Omega Development Team",
    author_email="dev@omega-update.com",
    maintainer="Omega Development Team",
    maintainer_email="dev@omega-update.com",
    
    # 项目链接
    url="https://github.com/omega-team/omega-update",
    project_urls={
        "Bug Reports": "https://github.com/omega-team/omega-update/issues",
        "Source": "https://github.com/omega-team/omega-update",
        "Documentation": "https://omega-update.readthedocs.io/",
    },
    
    # 包信息
    packages=find_packages(exclude=['tests', 'tests.*', 'docs', 'docs.*']),
    package_data={
        'omega_update': [
            'config/*.json',
            'deployment/*.conf',
            'deployment/*.service',
            'scripts/*.sh',
            'scripts/*.ps1',
        ],
    },
    include_package_data=True,
    
    # 依赖管理
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        'dev': dev_requirements,
        'test': ['pytest>=7.4.0', 'pytest-cov>=4.1.0'],
        'docs': ['sphinx>=7.0.0', 'sphinx-rtd-theme>=1.3.0'],
    },
    
    # 入口点
    entry_points={
        'console_scripts': [
            'omega-server=server.enhanced_main:main',
            'omega-upload=tools.upload.upload_tool:main',
            'omega-download=tools.download.download_tool:main',
        ],
    },
    
    # 分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Software Distribution",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    
    # 关键词
    keywords="update system, software distribution, patch management, fastapi, gui",
    
    # 许可证
    license="MIT",
    
    # 其他配置
    zip_safe=False,
    platforms=["any"],
)
