# Omega更新服务器 - 自动化工具部署指南

## 📋 概述

本指南介绍如何部署和使用Omega更新服务器的自动化工具，包括：
- 自动化上传程序（命令行版本）
- 下载工具的PyInstaller打包分发

## 🛠️ 工具清单

### 自动化上传工具
- `auto_upload.py` - 主要的自动化上传程序
- `auto_upload_batch.py` - 批处理版本
- `upload_config.json` - 配置文件

### 下载工具打包
- `download_tool.spec` - PyInstaller配置文件
- `build_download_tool.py` - 自动化打包脚本
- `OmegaDownloadTool.exe` - 打包后的可执行文件

## 🚀 部署步骤

### 第一步：环境准备

#### Python环境要求
```bash
# Python 3.8 或更高版本
python --version

# 安装必要的依赖
pip install requests pathlib
pip install pyinstaller  # 仅打包时需要
```

#### 项目文件检查
确保以下文件存在：
```
omega-update/
├── auto_upload.py              # 自动化上传程序
├── auto_upload_batch.py        # 批处理上传程序
├── upload_config.json          # 上传配置文件
├── download_tool.py            # 下载工具源码
├── download_tool.spec          # PyInstaller配置
├── build_download_tool.py      # 打包脚本
├── ui_factory.py              # UI工厂模块
├── upload_handler.py           # 上传处理器
├── download_handler.py         # 下载处理器
├── common_utils.py             # 共享工具
├── local_file_scanner.py       # 文件扫描器
├── difference_detector.py      # 差异检测器
├── download_manager.py         # 下载管理器
└── config.json                 # 基础配置文件
```

### 第二步：配置自动化上传工具

#### 1. 配置服务器信息
编辑 `upload_config.json`：
```json
{
  "server": {
    "url": "http://your-server-ip:8000",
    "api_key": "your_api_key_here"
  },
  "upload": {
    "default_platform": "windows",
    "default_architecture": "x64",
    "default_package_type": "full",
    "default_is_stable": true,
    "default_is_critical": false
  }
}
```

#### 2. 测试自动化上传
```bash
# 创建示例配置
python auto_upload.py --create-config

# 测试单文件夹上传
python auto_upload.py --folder ./test_folder --version v1.0.0 --description "测试版本"

# 测试批处理上传
python auto_upload_batch.py --create-sample
python auto_upload_batch.py --batch-file batch_config_sample.json
```

### 第三步：打包下载工具

#### 1. 检查打包环境
```bash
# 安装PyInstaller
pip install pyinstaller

# 检查依赖
python build_download_tool.py --help
```

#### 2. 执行打包
```bash
# 标准打包（推荐）
python build_download_tool.py

# 自定义打包选项
python build_download_tool.py --console --no-upx --onedir
```

#### 3. 验证打包结果
```bash
# 检查生成的文件
ls -la dist/
ls -la OmegaDownloadTool_v3.1.0/

# 测试可执行文件
./dist/OmegaDownloadTool.exe
```

## 📖 使用指南

### 自动化上传工具使用

#### 命令行参数
```bash
# 基本用法
python auto_upload.py --folder <文件夹路径> --version <版本号>

# 完整参数
python auto_upload.py \
  --folder ./my_app \
  --version v1.2.3 \
  --description "新功能发布" \
  --platform windows \
  --architecture x64 \
  --package-type full \
  --stable \
  --config custom_config.json
```

#### 批处理模式
```bash
# 从目录自动生成批处理配置
python auto_upload_batch.py --scan-dir ./versions --output batch.json

# 直接从目录上传所有版本
python auto_upload_batch.py --upload-dir ./versions --platform windows

# 使用批处理配置文件
python auto_upload_batch.py --batch-file batch.json
```

#### 配置文件示例
```json
{
  "description": "批量上传配置",
  "folders": [
    {
      "path": "./version_1.0.0",
      "version": "v1.0.0",
      "description": "第一个版本",
      "package_type": "full"
    },
    {
      "path": "./version_1.0.1", 
      "version": "v1.0.1",
      "description": "修复版本",
      "package_type": "patch",
      "from_version": "v1.0.0"
    }
  ]
}
```

### 下载工具分发

#### 分发包内容
```
OmegaDownloadTool_v3.1.0/
├── OmegaDownloadTool.exe      # 主程序
├── config.json                # 配置文件
├── README.md                  # 说明文档
└── 使用说明.txt               # 中文说明
```

#### 现场部署
1. 将分发包复制到目标机器
2. 修改 `config.json` 中的服务器地址
3. 双击 `OmegaDownloadTool.exe` 启动程序
4. 按照界面提示操作

## 🔧 高级配置

### 自动化脚本集成

#### Windows批处理脚本
```batch
@echo off
echo 开始自动化上传...
python auto_upload.py --folder "%1" --version "%2" --description "%3"
if %errorlevel% equ 0 (
    echo 上传成功！
) else (
    echo 上传失败！
    pause
)
```

#### Linux/macOS Shell脚本
```bash
#!/bin/bash
echo "开始自动化上传..."
python3 auto_upload.py --folder "$1" --version "$2" --description "$3"
if [ $? -eq 0 ]; then
    echo "上传成功！"
else
    echo "上传失败！"
    exit 1
fi
```

### 定时任务配置

#### Windows任务计划程序
```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T02:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>python</Command>
      <Arguments>auto_upload_batch.py --upload-dir ./daily_builds</Arguments>
      <WorkingDirectory>C:\omega-update</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

#### Linux Cron任务
```bash
# 每天凌晨2点执行自动上传
0 2 * * * cd /path/to/omega-update && python3 auto_upload_batch.py --upload-dir ./daily_builds
```

## 🐛 故障排除

### 常见问题

#### 1. 上传失败
```bash
# 检查网络连接
ping your-server-ip

# 检查API密钥
curl -H "Authorization: Bearer your_api_key" http://your-server-ip:8000/api/status

# 查看详细日志
python auto_upload.py --folder ./test --version v1.0.0 --config upload_config.json
tail -f auto_upload.log
```

#### 2. 打包失败
```bash
# 检查PyInstaller版本
pip show pyinstaller

# 清理缓存重新打包
python build_download_tool.py --no-clean

# 使用控制台模式调试
python build_download_tool.py --console
```

#### 3. 可执行文件无法运行
```bash
# 检查依赖库
ldd OmegaDownloadTool.exe  # Linux
otool -L OmegaDownloadTool  # macOS

# 在目标机器上测试
./OmegaDownloadTool.exe --help
```

### 日志分析

#### 上传日志位置
- `auto_upload.log` - 主要日志文件
- 控制台输出 - 实时进度信息

#### 日志级别配置
```json
{
  "logging": {
    "level": "DEBUG",  // DEBUG, INFO, WARNING, ERROR
    "file": "auto_upload.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}
```

## 📊 性能优化

### 上传性能
- 调整 `chunk_size` 参数
- 配置 `retry_count` 和 `retry_delay`
- 使用批处理模式减少连接开销

### 打包优化
- 使用 `--upx` 压缩可执行文件
- 排除不必要的模块
- 使用 `--onefile` 创建单文件分发

## 🔒 安全考虑

### API密钥管理
- 不要在代码中硬编码API密钥
- 使用环境变量或配置文件
- 定期更换API密钥

### 网络安全
- 使用HTTPS连接（如果服务器支持）
- 验证服务器证书
- 配置防火墙规则

---

## 📞 技术支持

如果在部署过程中遇到问题：

1. **查看日志文件** - 检查详细的错误信息
2. **检查网络连接** - 确保能够访问服务器
3. **验证配置文件** - 确保所有参数正确
4. **测试基本功能** - 从简单的测试开始

**部署指南版本**: 1.0
**适用工具版本**: Omega更新服务器 v3.1+
**更新日期**: 2025-07-13

---

## 📚 用户手册

### 快速开始指南

#### 自动化上传工具
```bash
# 1. 配置服务器信息
cp upload_config.json my_config.json
# 编辑 my_config.json 中的服务器地址和API密钥

# 2. 上传单个文件夹
python auto_upload.py --folder ./my_app_v1.0 --version v1.0.0

# 3. 批量上传多个版本
python auto_upload_batch.py --upload-dir ./all_versions
```

#### 下载工具分发
```bash
# 1. 打包下载工具
python build_download_tool.py

# 2. 分发到目标机器
# 复制 OmegaDownloadTool_v3.1.0/ 文件夹到目标机器

# 3. 在目标机器上运行
# 双击 OmegaDownloadTool.exe
```

### 常用命令参考

#### 自动化上传
```bash
# 基本上传
python auto_upload.py -f ./app -v v1.0.0 -d "新版本"

# 增量包上传
python auto_upload.py -f ./patch -v v1.0.1 -t patch --from-version v1.0.0

# 热修复包上传
python auto_upload.py -f ./hotfix -v v1.0.1-hotfix -t hotfix --critical

# 批量处理
python auto_upload_batch.py --scan-dir ./versions
python auto_upload_batch.py --batch-file generated_batch.json
```

#### 打包配置
```bash
# 标准打包
python build_download_tool.py

# 调试版本（显示控制台）
python build_download_tool.py --console

# 目录分发版本
python build_download_tool.py --onedir

# 不压缩版本
python build_download_tool.py --no-upx
```
