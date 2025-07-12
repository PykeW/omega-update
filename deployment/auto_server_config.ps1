# 自动服务器配置脚本 - 真正无密码提示版本
# 使用Posh-SSH模块和配置文件中的密码

# 检查并安装Posh-SSH模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "[INFO] 安装Posh-SSH模块..." -ForegroundColor Yellow
    try {
        Install-Module -Name Posh-SSH -Force -Scope CurrentUser -AllowClobber
        Write-Host "[INFO] Posh-SSH模块安装成功" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] 无法安装Posh-SSH模块: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Import-Module Posh-SSH

# 读取配置文件
$configPath = Join-Path $PSScriptRoot "server_config.json"
if (-not (Test-Path $configPath)) {
    Write-Host "[ERROR] 配置文件不存在: $configPath" -ForegroundColor Red
    exit 1
}

try {
    $config = Get-Content $configPath | ConvertFrom-Json
    $ServerIP = $config.server.ip
    $ServerUser = $config.server.user
    $Password = $config.server.password
    $Domain = $config.server.domain
    $ApiKey = $config.api.key
} catch {
    Write-Host "[ERROR] 配置文件格式错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 自动配置工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP ($Domain)"
Write-Host "用户: $ServerUser"
Write-Host "API密钥: $ApiKey"
Write-Host "=================================================="
Write-Host ""

# 创建凭据对象并建立SSH连接
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($ServerUser, $securePassword)

try {
    Write-Host "[STEP] 建立SSH连接..." -ForegroundColor Blue
    $sshSession = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey

    if (-not $sshSession) {
        throw "无法建立SSH连接"
    }

    Write-Host "[INFO] SSH连接成功" -ForegroundColor Green

} catch {
    Write-Host "[ERROR] 连接失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 执行远程命令函数
function Invoke-RemoteCommand {
    param($Command, $Description)

    Write-Host "[EXEC] $Description" -ForegroundColor Blue
    $result = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $Command

    if ($result.ExitStatus -eq 0) {
        Write-Host "[SUCCESS] $Description" -ForegroundColor Green
        if ($result.Output) {
            Write-Host $result.Output -ForegroundColor Gray
        }
        return $true
    } else {
        Write-Host "[WARN] $Description 可能有问题" -ForegroundColor Yellow
        if ($result.Error) {
            Write-Host $result.Error -ForegroundColor Gray
        }
        return $false
    }
}

try {
    # 检查部署文件
    Write-Host "[STEP] 检查部署文件..." -ForegroundColor Blue
    Invoke-RemoteCommand "cd /tmp/omega-deployment && ls -la" "列出部署文件"
    
    # 修复服务器文件大小限制
    Write-Host "[STEP] 修复服务器文件大小限制..." -ForegroundColor Blue
    if (Invoke-RemoteCommand "cd /tmp/omega-deployment && ./fix_server_limits.sh" "执行限制修复脚本") {
        Write-Host "[INFO] 服务器限制修复成功" -ForegroundColor Green
    }
    
    # 等待服务重启
    Write-Host "[STEP] 等待服务重启..." -ForegroundColor Blue
    Start-Sleep -Seconds 10
    
    # 运行诊断
    Write-Host "[STEP] 运行系统诊断..." -ForegroundColor Blue
    Invoke-RemoteCommand "cd /tmp/omega-deployment && ./diagnose.sh" "执行系统诊断"
    
    # 检查服务状态
    Write-Host "[STEP] 检查服务状态..." -ForegroundColor Blue
    Invoke-RemoteCommand "systemctl status omega-update-server --no-pager" "检查更新服务状态"
    Invoke-RemoteCommand "systemctl status nginx --no-pager" "检查Nginx状态"
    
    # 测试HTTP接口
    Write-Host "[STEP] 测试HTTP接口..." -ForegroundColor Blue
    $healthCheck = Invoke-RemoteCommand "curl -s http://localhost/health" "测试健康检查接口"
    
    if ($healthCheck) {
        Write-Host "[INFO] HTTP接口测试成功" -ForegroundColor Green
    } else {
        Write-Host "[WARN] HTTP接口可能有问题，尝试修复..." -ForegroundColor Yellow
        
        # 如果有问题，尝试修复
        Write-Host "[STEP] 尝试修复常见问题..." -ForegroundColor Blue
        Invoke-RemoteCommand "cd /tmp/omega-deployment && ./fix_common_issues.sh --all" "执行全面修复"
        
        # 再次测试
        Start-Sleep -Seconds 5
        Invoke-RemoteCommand "curl -s http://localhost/health" "重新测试健康检查接口"
    }
    
    # 检查API密钥
    Write-Host "[STEP] 验证API密钥..." -ForegroundColor Blue
    $apiKeyResult = Invoke-RemoteCommand "grep API_KEY /opt/omega-update-server/.env" "获取API密钥"
    
    # 检查防火墙设置
    Write-Host "[STEP] 检查防火墙设置..." -ForegroundColor Blue
    Invoke-RemoteCommand "ufw status" "检查防火墙状态"
    
    # 检查端口监听
    Write-Host "[STEP] 检查端口监听..." -ForegroundColor Blue
    Invoke-RemoteCommand "netstat -tlnp | grep -E ':80|:8000'" "检查端口监听状态"
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    服务器配置完成！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "服务器状态:"
    Write-Host "  - 主页: http://$Domain" -ForegroundColor Green
    Write-Host "  - API文档: http://$Domain/docs" -ForegroundColor Green
    Write-Host "  - 健康检查: http://$Domain/health" -ForegroundColor Green
    Write-Host "  - API密钥: $ApiKey" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:"
    Write-Host "1. 启动GUI工具制作更新包:" -ForegroundColor Yellow
    Write-Host "   cd deployment" -ForegroundColor White
    Write-Host "   python omega_update_gui.py" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 在浏览器中访问:" -ForegroundColor Yellow
    Write-Host "   http://$Domain" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 测试更新包上传:" -ForegroundColor Yellow
    Write-Host "   使用GUI工具制作并上传更新包" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] 配置失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # 清理连接
    if ($sshSession) { Remove-SSHSession -SessionId $sshSession.SessionId | Out-Null }
}

Write-Host "配置完成！现在可以使用GUI工具了。" -ForegroundColor Green
