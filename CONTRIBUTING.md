# 贡献指南

感谢您对 Omega 更新系统的关注！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- ✨ 添加新功能

## 📋 开发环境设置

### 1. 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10/11, Linux, macOS
- **工具**: Git, pipenv (推荐)

### 2. 克隆项目

```bash
git clone https://github.com/omega-team/omega-update.git
cd omega-update
```

### 3. 安装依赖

```bash
# 使用 pipenv (推荐)
pipenv install --dev
pipenv shell

# 或使用 pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
# 至少需要设置 API_KEY
```

### 5. 验证安装

```bash
# 运行测试
pytest

# 启动服务器
python start_server.py

# 在另一个终端启动客户端工具
python start_upload_tool.py
```

## 🔧 开发工作流

### 1. 创建分支

```bash
# 从 main 分支创建新的功能分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 或者修复 bug
git checkout -b fix/bug-description
```

### 2. 代码开发

#### 代码规范

我们使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: 导入排序
- **Flake8**: 代码质量检查
- **MyPy**: 类型检查
- **Pytest**: 单元测试

#### 运行代码检查

```bash
# 格式化代码
black .
isort .

# 代码质量检查
flake8 .

# 类型检查
mypy .

# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest --cov=server --cov=tools --cov-report=html tests/
```

#### 使用 Pre-commit Hooks

```bash
# 安装 pre-commit hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

### 3. 提交代码

#### 提交信息规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 代码重构
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

**示例:**
```bash
git commit -m "feat(server): add file upload progress tracking"
git commit -m "fix(download): resolve connection timeout issue"
git commit -m "docs: update installation guide"
```

### 4. 推送和创建 PR

```bash
# 推送分支
git push origin feature/your-feature-name

# 在 GitHub 上创建 Pull Request
```

## 📝 代码规范

### Python 代码风格

- 遵循 [PEP 8](https://pep8.org/) 规范
- 使用 Black 进行代码格式化（行长度 88 字符）
- 使用 Google 风格的文档字符串
- 类型注解：所有公共函数和方法都应该有类型注解

### 文档字符串示例

```python
def upload_file(file_path: str, server_url: str) -> bool:
    """上传文件到服务器。

    Args:
        file_path: 要上传的文件路径
        server_url: 服务器 URL

    Returns:
        上传成功返回 True，否则返回 False

    Raises:
        FileNotFoundError: 当文件不存在时
        ConnectionError: 当网络连接失败时
    """
    pass
```

### 项目结构规范

```
omega-update/
├── server/          # 服务器端代码
├── tools/           # 客户端工具
│   ├── upload/      # 上传功能
│   ├── download/    # 下载功能
│   └── common/      # 共享组件
├── tests/           # 测试代码
├── docs/            # 文档
├── config/          # 配置文件
└── scripts/         # 构建和部署脚本
```

## 🧪 测试指南

### 测试类型

1. **单元测试**: 测试单个函数或类
2. **集成测试**: 测试模块间的交互
3. **端到端测试**: 测试完整的用户流程

### 编写测试

```python
import pytest
from server.enhanced_main import app
from fastapi.testclient import TestClient

def test_health_check():
    """测试健康检查接口。"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_server.py

# 运行特定测试函数
pytest tests/test_server.py::test_health_check

# 生成覆盖率报告
pytest --cov=server --cov=tools --cov-report=html
```

## 📚 文档贡献

### 文档类型

- **README.md**: 项目概述和快速开始
- **docs/**: 详细文档
- **API 文档**: 自动生成的 API 文档
- **代码注释**: 内联文档

### 文档规范

- 使用 Markdown 格式
- 包含代码示例
- 提供清晰的步骤说明
- 保持版本信息更新

## 🐛 报告 Bug

### Bug 报告模板

请使用以下模板报告 Bug：

```markdown
## Bug 描述
简要描述遇到的问题

## 复现步骤
1. 执行步骤 1
2. 执行步骤 2
3. 看到错误

## 期望行为
描述您期望发生的情况

## 实际行为
描述实际发生的情况

## 环境信息
- 操作系统: [例如 Windows 11]
- Python 版本: [例如 3.10.11]
- 项目版本: [例如 2.0.0]

## 附加信息
添加任何其他有助于解决问题的信息
```

## 💡 功能建议

### 功能请求模板

```markdown
## 功能描述
简要描述建议的功能

## 问题背景
描述这个功能要解决的问题

## 解决方案
描述您希望的解决方案

## 替代方案
描述您考虑过的其他解决方案

## 附加信息
添加任何其他相关信息
```

## 📞 获取帮助

如果您在贡献过程中遇到问题，可以通过以下方式获取帮助：

- 📧 邮件: dev@omega-update.com
- 💬 GitHub Issues: 创建 issue 讨论
- 📖 文档: 查看 `docs/` 目录下的详细文档

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下发布。

---

再次感谢您的贡献！🎉
