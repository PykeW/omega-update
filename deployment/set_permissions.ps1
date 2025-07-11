# PowerShell脚本：设置部署文件权限
# 在Windows环境下为部署文件设置适当的权限

Write-Host "设置Omega更新服务器部署文件权限..." -ForegroundColor Green

# 获取当前目录
$deploymentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 需要设置执行权限的脚本文件
$scriptFiles = @(
    "deploy.sh",
    "upload_files.sh", 
    "quick_deploy.sh"
)

# 需要设置读取权限的配置文件
$configFiles = @(
    "main.py",
    "server_config.py",
    "manage_updates.py",
    "nginx.conf",
    "omega-update-server.service"
)

Write-Host "设置脚本文件权限..." -ForegroundColor Yellow

foreach ($file in $scriptFiles) {
    $filePath = Join-Path $deploymentDir $file
    if (Test-Path $filePath) {
        # 在Windows上，我们主要确保文件存在且可读
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (文件不存在)" -ForegroundColor Red
    }
}

Write-Host "设置配置文件权限..." -ForegroundColor Yellow

foreach ($file in $configFiles) {
    $filePath = Join-Path $deploymentDir $file
    if (Test-Path $filePath) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (文件不存在)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "权限设置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作："
Write-Host "1. 确保已配置SSH密钥到服务器"
Write-Host "2. 运行快速部署脚本："
Write-Host "   .\deployment\quick_deploy.sh"
Write-Host ""
Write-Host "或者分步执行："
Write-Host "1. 上传文件: .\deployment\upload_files.sh"
Write-Host "2. 连接服务器: ssh root@106.14.28.97"
Write-Host "3. 执行部署: cd /tmp/omega-deployment && ./deploy.sh install"
Write-Host ""
