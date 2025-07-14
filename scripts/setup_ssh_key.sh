#!/bin/bash
# Omega 更新系统 - SSH密钥设置脚本

echo "=== Omega 更新系统 SSH 密钥设置 ==="
echo ""

# 显示公钥
echo "您的SSH公钥内容如下："
echo "=================================="
cat ~/.ssh/omega_update_key.pub
echo "=================================="
echo ""

echo "请按照以下步骤将公钥添加到远程服务器："
echo ""
echo "方法1: 使用 ssh-copy-id (推荐)"
echo "ssh-copy-id -i ~/.ssh/omega_update_key.pub root@106.14.28.97"
echo ""
echo "方法2: 手动添加"
echo "1. 登录到远程服务器: ssh root@106.14.28.97"
echo "2. 创建 .ssh 目录: mkdir -p ~/.ssh"
echo "3. 将上面的公钥内容添加到: ~/.ssh/authorized_keys"
echo "4. 设置权限: chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
echo ""
echo "方法3: 一键复制公钥到剪贴板"
echo "cat ~/.ssh/omega_update_key.pub | clip"
echo ""

# 测试连接函数
test_connection() {
    echo "测试SSH连接..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes omega-server "echo 'SSH连接成功!'" 2>/dev/null; then
        echo "✅ SSH连接测试成功!"
        return 0
    else
        echo "❌ SSH连接测试失败，请检查公钥是否已正确添加到远程服务器"
        return 1
    fi
}

# 询问是否测试连接
echo "是否现在测试SSH连接? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    test_connection
fi

echo ""
echo "SSH密钥设置完成!"
echo "您现在可以使用以下命令连接到远程服务器:"
echo "ssh omega-server"
