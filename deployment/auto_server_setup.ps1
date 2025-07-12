# 自动服务器配置脚本
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root",
    [string]$Password = "LU@pyke7"
)

# 导入Posh-SSH模块
Import-Module Posh-SSH

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 自动配置工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP"
Write-Host "用户: $ServerUser"
Write-Host "=================================================="
Write-Host ""

try {
    # 创建凭据对象
    $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential ($ServerUser, $securePassword)
    
    # 建立SSH连接
    Write-Host "[STEP] 建立SSH连接..." -ForegroundColor Blue
    $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey
    
    if (-not $session) {
        throw "无法建立SSH连接"
    }
    
    Write-Host "[INFO] SSH连接成功" -ForegroundColor Green
    
    # 执行命令函数
    function Invoke-RemoteCommand {
        param($Command, $Description)
        
        Write-Host "[EXEC] $Description" -ForegroundColor Blue
        $result = Invoke-SSHCommand -SessionId $session.SessionId -Command $Command
        
        if ($result.Output) {
            Write-Host $result.Output -ForegroundColor Gray
        }
        
        if ($result.ExitStatus -ne 0 -and $result.Error) {
            Write-Host "[WARN] $($result.Error)" -ForegroundColor Yellow
        }
        
        return $result
    }
    
    # 检查部署文件
    Write-Host "[STEP] 检查部署文件..." -ForegroundColor Blue
    $result = Invoke-RemoteCommand "cd /tmp/omega-deployment && ls -la" "列出部署文件"
    
    # 修复服务器文件大小限制
    Write-Host "[STEP] 修复服务器文件大小限制..." -ForegroundColor Blue
    $result = Invoke-RemoteCommand "cd /tmp/omega-deployment && ./fix_server_limits.sh" "执行限制修复脚本"
    
    if ($result.ExitStatus -eq 0) {
        Write-Host "[INFO] 服务器限制修复成功" -ForegroundColor Green
    } else {
        Write-Host "[WARN] 服务器限制修复可能有问题" -ForegroundColor Yellow
    }
    
    # 等待服务重启
    Write-Host "[STEP] 等待服务重启..." -ForegroundColor Blue
    Start-Sleep -Seconds 10
    
    # 运行诊断
    Write-Host "[STEP] 运行系统诊断..." -ForegroundColor Blue
    $result = Invoke-RemoteCommand "cd /tmp/omega-deployment && ./diagnose.sh" "执行系统诊断"
    
    # 检查服务状态
    Write-Host "[STEP] 检查服务状态..." -ForegroundColor Blue
    $result = Invoke-RemoteCommand "systemctl status omega-update-server --no-pager" "检查更新服务状态"
    $result = Invoke-RemoteCommand "systemctl status nginx --no-pager" "检查Nginx状态"
    
    # 测试HTTP接口
    Write-Host "[STEP] 测试HTTP接口..." -ForegroundColor Blue
    $result = Invoke-RemoteCommand "curl -s http://localhost/health" "测试健康检查接口"
    
    if ($result.Output -like "*healthy*") {
        Write-Host "[INFO] HTTP接口测试成功" -ForegroundColor Green
    } else {
        Write-Host "[WARN] HTTP接口可能有问题" -ForegroundColor Yellow
        
        # 如果有问题，尝试修复
        Write-Host "[STEP] 尝试修复常见问题..." -ForegroundColor Blue
        $result = Invoke-RemoteCommand "cd /tmp/omega-deployment && ./fix_common_issues.sh --all" "执行全面修复"
        
        # 再次测试
        Start-Sleep -Seconds 5
        $result = Invoke-RemoteCommand "curl -s http://localhost/health" "重新测试健康检查接口"
    }
    
    # 检查API密钥
    Write-Host "[STEP] 获取API密钥..." -ForegroundColor Blue
    $result = Invoke-RemoteCommand "grep API_KEY /opt/omega-update-server/.env" "获取API密钥"
    
    if ($result.Output) {
        Write-Host "[INFO] API密钥: $($result.Output)" -ForegroundColor Green
    }
    
    # 关闭连接
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    服务器配置完成！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "服务器状态:"
    Write-Host "  - 地址: http://update.chpyke.cn" -ForegroundColor Green
    Write-Host "  - API文档: http://update.chpyke.cn/docs" -ForegroundColor Green
    Write-Host "  - 健康检查: http://update.chpyke.cn/health" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作:"
    Write-Host "1. 启动GUI工具制作更新包:" -ForegroundColor Yellow
    Write-Host "   cd deployment" -ForegroundColor White
    Write-Host "   python omega_update_gui.py" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 或在浏览器中访问:" -ForegroundColor Yellow
    Write-Host "   http://update.chpyke.cn" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] 配置失败: $($_.Exception.Message)" -ForegroundColor Red
    
    # 清理连接
    if ($session) { Remove-SSHSession -SessionId $session.SessionId | Out-Null }
    
    exit 1
}

Write-Host "配置完成！现在可以使用GUI工具了。" -ForegroundColor Green
