#!/bin/bash
# Omega更新服务器 - 下载工具启动脚本 (Linux/macOS)
# 用于启动独立的文件下载和更新检查工具

echo "========================================"
echo "Omega更新服务器 - 下载工具 v3.1 (重构版)"
echo "========================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "错误: 未找到Python，请先安装Python 3.7+"
        echo "Ubuntu/Debian: sudo apt install python3"
        echo "CentOS/RHEL: sudo yum install python3"
        echo "macOS: brew install python3"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 显示Python版本
echo "使用Python版本:"
$PYTHON_CMD --version
echo

# 检查必需文件是否存在
required_files=("download_tool.py" "common_utils.py" "local_file_scanner.py" "difference_detector.py" "download_manager.py")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "错误: 未找到 $file 文件"
        exit 1
    fi
done

# 检查配置文件
if [ ! -f "local_server_config.json" ] && [ ! -f "deployment/server_config.json" ]; then
    echo "警告: 未找到配置文件，将使用默认配置"
    echo "建议创建 local_server_config.json 配置文件"
    echo
fi

echo "正在启动下载工具..."
echo

# 启动下载工具
$PYTHON_CMD download_tool.py

# 检查退出代码
if [ $? -ne 0 ]; then
    echo
    echo "下载工具异常退出，错误代码: $?"
    echo "请检查错误信息并重试"
else
    echo
    echo "下载工具正常退出"
fi

echo "按任意键继续..."
read -n 1
