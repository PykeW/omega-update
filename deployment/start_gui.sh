#!/bin/bash
# Omega更新包管理GUI工具启动脚本

echo "================================================"
echo "     Omega更新包管理GUI工具"
echo "================================================"
echo

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "错误: 未找到Python，请先安装Python 3.6+"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

echo "使用Python: $PYTHON_CMD"
$PYTHON_CMD --version

echo "检查Python依赖..."

# 安装必要的依赖
$PYTHON_CMD -m pip install requests &> /dev/null
if [ $? -ne 0 ]; then
    echo "警告: 无法安装requests库，可能会影响网络功能"
fi

echo "启动GUI程序..."
echo

# 启动GUI程序
$PYTHON_CMD omega_update_gui.py

if [ $? -ne 0 ]; then
    echo
    echo "程序运行出错，请检查错误信息"
    read -p "按Enter键退出..."
fi
