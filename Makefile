# Omega 更新系统 - Makefile
# 简化常用的开发和部署任务

.PHONY: help install install-dev clean test lint format check build deploy validate

# 默认目标
help:
	@echo "Omega 更新系统 - 可用命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  install      - 安装生产依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  clean        - 清理缓存和临时文件"
	@echo ""
	@echo "代码质量:"
	@echo "  format       - 格式化代码 (black + isort)"
	@echo "  lint         - 代码质量检查 (flake8)"
	@echo "  typecheck    - 类型检查 (mypy)"
	@echo "  check        - 运行所有检查 (format + lint + typecheck)"
	@echo ""
	@echo "测试:"
	@echo "  test         - 运行测试"
	@echo "  test-cov     - 运行测试并生成覆盖率报告"
	@echo ""
	@echo "构建和部署:"
	@echo "  build        - 构建发布包"
	@echo "  validate     - 验证配置文件"
	@echo ""
	@echo "应用程序:"
	@echo "  server       - 启动服务器"
	@echo "  upload       - 启动上传工具"
	@echo "  download     - 启动下载工具"

# 安装依赖
install:
	@echo "📦 安装生产依赖..."
	pipenv install

install-dev:
	@echo "📦 安装开发依赖..."
	pipenv install --dev
	@echo "🔧 安装 pre-commit hooks..."
	pipenv run pre-commit install

# 清理
clean:
	@echo "🧹 清理缓存和临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ htmlcov/ .tox/ 2>/dev/null || true
	@echo "✅ 清理完成"

# 代码格式化
format:
	@echo "🎨 格式化代码..."
	pipenv run black .
	pipenv run isort .
	@echo "✅ 代码格式化完成"

# 代码质量检查
lint:
	@echo "🔍 运行代码质量检查..."
	pipenv run flake8 .
	@echo "✅ 代码质量检查完成"

# 类型检查
typecheck:
	@echo "🔍 运行类型检查..."
	pipenv run mypy .
	@echo "✅ 类型检查完成"

# 运行所有检查
check: format lint typecheck
	@echo "✅ 所有检查完成"

# 测试
test:
	@echo "🧪 运行测试..."
	pipenv run pytest tests/ -v

test-cov:
	@echo "🧪 运行测试并生成覆盖率报告..."
	pipenv run pytest --cov=server --cov=tools --cov-report=html --cov-report=term tests/
	@echo "📊 覆盖率报告已生成到 htmlcov/ 目录"

# 构建
build: clean check test
	@echo "📦 构建发布包..."
	pipenv run python setup.py sdist bdist_wheel
	@echo "✅ 构建完成，文件在 dist/ 目录"

# 验证配置
validate:
	@echo "🔍 验证配置文件..."
	python scripts/validate_config.py

# 启动应用程序
server:
	@echo "🚀 启动服务器..."
	python start_server.py

upload:
	@echo "📤 启动上传工具..."
	python start_upload_tool.py

download:
	@echo "📥 启动下载工具..."
	python start_download_tool.py

# 开发环境设置
setup-dev: install-dev
	@echo "⚙️  设置开发环境..."
	@if [ ! -f .env ]; then \
		echo "📝 创建 .env 文件..."; \
		cp .env.example .env; \
		echo "请编辑 .env 文件设置必要的配置"; \
	fi
	@echo "✅ 开发环境设置完成"

# 运行所有检查和测试
ci: check test validate
	@echo "✅ CI 检查完成"

# 部署前检查
pre-deploy: ci build
	@echo "✅ 部署前检查完成"

# 显示项目信息
info:
	@echo "📋 项目信息:"
	@echo "  名称: Omega 更新系统"
	@echo "  版本: $(shell cat VERSION 2>/dev/null || echo '未知')"
	@echo "  Python: $(shell python --version 2>/dev/null || echo '未安装')"
	@echo "  Pipenv: $(shell pipenv --version 2>/dev/null || echo '未安装')"
	@echo "  Git: $(shell git --version 2>/dev/null || echo '未安装')"

# 更新依赖
update:
	@echo "📦 更新依赖..."
	pipenv update
	@echo "✅ 依赖更新完成"

# 安全检查
security:
	@echo "🔒 运行安全检查..."
	pipenv run bandit -r . -f json -o bandit-report.json || true
	@echo "📊 安全报告已生成到 bandit-report.json"

# 生成需求文件
requirements:
	@echo "📝 生成 requirements.txt..."
	pipenv requirements > requirements.txt
	pipenv requirements --dev > requirements-dev.txt
	@echo "✅ 需求文件已生成"
