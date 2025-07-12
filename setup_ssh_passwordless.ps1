#!/usr/bin/env pwsh
# SSH密钥自动配置脚本

$ServerIP = "106.14.28.97"
$Username = "root"
$Password = "LU@pyke7"

Write-Host "=== SSH免密连接自动配置 ===" -ForegroundColor Green

# 1. 读取公钥内容
$PublicKeyPath = "$env:USERPROFILE\.ssh\id_rsa.pub"
if (-not (Test-Path $PublicKeyPath)) {
    Write-Host "错误: 公钥文件不存在: $PublicKeyPath" -ForegroundColor Red
    exit 1
}

$PublicKey = Get-Content $PublicKeyPath -Raw
Write-Host "✓ 读取公钥成功" -ForegroundColor Green

# 2. 显示手动配置指令
Write-Host "`n请手动执行以下操作:" -ForegroundColor Cyan
Write-Host "1. 连接到服务器:" -ForegroundColor White
Write-Host "   ssh root@$ServerIP" -ForegroundColor Gray
Write-Host "   密码: $Password" -ForegroundColor Gray

Write-Host "`n2. 在服务器上执行以下命令:" -ForegroundColor White
$SSHCommands = @"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo '$($PublicKey.Trim())' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
# 去重复行
sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp
mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
# 确保SSH配置正确
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd
echo "SSH密钥配置完成!"
"@

Write-Host $SSHCommands -ForegroundColor Gray

Write-Host "`n3. 退出服务器后测试免密连接:" -ForegroundColor White
Write-Host "   ssh root@$ServerIP" -ForegroundColor Gray

Write-Host "`n=== 配置说明 ===" -ForegroundColor Green
Write-Host "如果配置成功，应该可以无密码连接到服务器" -ForegroundColor Yellow
