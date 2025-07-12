# 无密码上传脚本 - 使用SSH密钥认证
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root"
)

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 无密码上传工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP"
Write-Host "用户: $ServerUser"
Write-Host "认证方式: SSH密钥"
Write-Host "=================================================="
Write-Host ""

$keyPath = "$env:USERPROFILE\.ssh\id_rsa_omega"

# 检查SSH密钥是否存在
if (-not (Test-Path $keyPath)) {
    Write-Host "[ERROR] SSH密钥不存在: $keyPath" -ForegroundColor Red
    Write-Host "请先运行SSH密钥配置脚本:" -ForegroundColor Yellow
    Write-Host ".\deployment\setup_ssh_key.ps1" -ForegroundColor White
    exit 1
}

try {
    # SSH选项
    $sshOpts = @(
        "-i", $keyPath,
        "-o", "StrictHostKeyChecking=no",
        "-o", "PasswordAuthentication=no",
        "-o", "IdentitiesOnly=yes"
    )
    
    # 测试SSH连接
    Write-Host "[STEP] 测试SSH密钥认证..." -ForegroundColor Blue
    $testResult = & ssh @sshOpts "$ServerUser@$ServerIP" "echo 'SSH连接成功'" 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        throw "SSH密钥认证失败，请检查密钥配置"
    }
    
    Write-Host "[INFO] SSH密钥认证成功" -ForegroundColor Green
    
    # 创建远程目录
    Write-Host "[STEP] 创建远程目录..." -ForegroundColor Blue
    & ssh @sshOpts "$ServerUser@$ServerIP" "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment"
    
    if ($LASTEXITCODE -ne 0) {
        throw "无法创建远程目录"
    }
    
    # 上传文件函数
    function Upload-File {
        param($LocalPath, $RemotePath, $Description)
        
        if (Test-Path $LocalPath) {
            Write-Host "  上传: $Description" -ForegroundColor Gray
            & scp @sshOpts $LocalPath "$ServerUser@${ServerIP}:$RemotePath" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    成功: $Description" -ForegroundColor Green
            } else {
                Write-Host "    失败: $Description" -ForegroundColor Red
            }
        } else {
            Write-Host "  跳过: $Description (文件不存在)" -ForegroundColor Yellow
        }
    }
    
    # 上传部署脚本
    Write-Host "[STEP] 上传部署脚本..." -ForegroundColor Blue
    Upload-File "deployment\deploy.sh" "/tmp/omega-deployment/deploy.sh" "部署脚本"
    Upload-File "deployment\diagnose.sh" "/tmp/omega-deployment/diagnose.sh" "诊断脚本"
    Upload-File "deployment\fix_common_issues.sh" "/tmp/omega-deployment/fix_common_issues.sh" "修复脚本"
    Upload-File "deployment\fix_server_limits.sh" "/tmp/omega-deployment/fix_server_limits.sh" "限制修复脚本"
    
    # 上传配置文件
    Write-Host "[STEP] 上传配置文件..." -ForegroundColor Blue
    Upload-File "deployment\main.py" "/tmp/omega-deployment/main.py" "主程序"
    Upload-File "deployment\server_config.py" "/tmp/omega-deployment/server_config.py" "服务器配置"
    Upload-File "deployment\nginx.conf" "/tmp/omega-deployment/nginx.conf" "Nginx配置"
    Upload-File "deployment\omega-update-server.service" "/tmp/omega-deployment/omega-update-server.service" "系统服务"
    
    # 上传工具脚本
    Write-Host "[STEP] 上传工具脚本..." -ForegroundColor Blue
    Upload-File "deployment\simple_package_maker.py" "/tmp/omega-deployment/simple_package_maker.py" "更新包制作工具"
    Upload-File "generate_update_package.py" "/tmp/omega-deployment/generate_update_package.py" "更新包生成器"
    Upload-File "simple_update_generator.py" "/tmp/omega-deployment/simple_update_generator.py" "简单更新生成器"
    Upload-File "version_analyzer.py" "/tmp/omega-deployment/version_analyzer.py" "版本分析器"
    
    # 上传update_server目录
    if (Test-Path "update_server") {
        Write-Host "[STEP] 上传update_server模块..." -ForegroundColor Blue
        & scp @sshOpts -r "update_server" "$ServerUser@${ServerIP}:/tmp/omega-deployment/" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    成功: update_server模块" -ForegroundColor Green
        } else {
            Write-Host "    失败: update_server模块" -ForegroundColor Red
        }
    }
    
    # 设置文件权限
    Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
    & ssh @sshOpts "$ServerUser@$ServerIP" "chmod +x /tmp/omega-deployment/*.sh"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[INFO] 文件权限设置成功" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    文件上传完成！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "下一步操作："
    Write-Host "1. 自动配置服务器:" -ForegroundColor Yellow
    Write-Host "   .\deployment\passwordless_server_setup.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 或手动连接服务器:" -ForegroundColor Yellow
    Write-Host "   ssh omega-server" -ForegroundColor White
    Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
    Write-Host "   ./fix_server_limits.sh" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "如果SSH密钥有问题，请重新配置:" -ForegroundColor Yellow
    Write-Host ".\deployment\setup_ssh_key.ps1" -ForegroundColor White
    exit 1
}

Write-Host "上传完成！无需密码认证。" -ForegroundColor Green
