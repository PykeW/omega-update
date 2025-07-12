# 自动上传脚本 - 真正无密码提示版本
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
} catch {
    Write-Host "[ERROR] 配置文件格式错误: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 自动上传工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP ($Domain)"
Write-Host "用户: $ServerUser"
Write-Host "认证: Posh-SSH自动认证"
Write-Host "=================================================="
Write-Host ""

# 创建凭据对象
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($ServerUser, $securePassword)

# 建立SSH和SFTP连接
try {
    Write-Host "[STEP] 建立SSH连接..." -ForegroundColor Blue
    $sshSession = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey

    if (-not $sshSession) {
        throw "无法建立SSH连接"
    }

    Write-Host "[INFO] SSH连接成功" -ForegroundColor Green

    Write-Host "[STEP] 建立SFTP连接..." -ForegroundColor Blue
    $sftpSession = New-SFTPSession -ComputerName $ServerIP -Credential $credential -AcceptKey

    if (-not $sftpSession) {
        throw "无法建立SFTP连接"
    }

    Write-Host "[INFO] SFTP连接成功" -ForegroundColor Green

} catch {
    Write-Host "[ERROR] 连接失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 执行SSH命令函数
function Invoke-RemoteCommand {
    param($Command, $Description)

    Write-Host "  执行: $Description" -ForegroundColor Gray
    $result = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $Command

    if ($result.ExitStatus -eq 0) {
        Write-Host "    成功: $Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "    失败: $Description" -ForegroundColor Red
        if ($result.Error) {
            Write-Host "    错误: $($result.Error)" -ForegroundColor Red
        }
        return $false
    }
}

# 上传文件函数
function Upload-File {
    param($LocalPath, $RemotePath, $Description)

    if (Test-Path $LocalPath) {
        Write-Host "  上传: $Description" -ForegroundColor Gray
        try {
            # 确保远程目录存在
            $remoteDir = Split-Path $RemotePath -Parent
            Invoke-RemoteCommand "mkdir -p `"$remoteDir`"" "创建目录" | Out-Null

            # 使用正确的SFTP上传命令
            Set-SFTPFile -SessionId $sftpSession.SessionId -LocalFile $LocalPath -RemotePath $RemotePath -Overwrite
            Write-Host "    成功: $Description" -ForegroundColor Green
        } catch {
            Write-Host "    失败: $Description - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "  跳过: $Description (文件不存在)" -ForegroundColor Yellow
    }
}

try {
    # 创建远程目录
    Write-Host "[STEP] 创建远程目录..." -ForegroundColor Blue
    if (-not (Invoke-RemoteCommand "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment" "创建部署目录")) {
        throw "无法创建远程目录"
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
        try {
            # 递归上传目录
            Get-ChildItem "update_server" -Recurse -File | ForEach-Object {
                $relativePath = $_.FullName.Substring((Get-Item "update_server").FullName.Length + 1).Replace('\', '/')
                $remotePath = "/tmp/omega-deployment/update_server/$relativePath"
                $remoteDir = Split-Path $remotePath -Parent

                # 创建远程目录
                Invoke-RemoteCommand "mkdir -p `"$remoteDir`"" "创建目录 $remoteDir" | Out-Null

                # 上传文件
                Write-Host "    上传: $relativePath" -ForegroundColor Gray
                Set-SFTPFile -SessionId $sftpSession.SessionId -LocalFile $_.FullName -RemotePath $remotePath -Overwrite
            }
            Write-Host "    成功: update_server模块" -ForegroundColor Green
        } catch {
            Write-Host "    失败: update_server模块 - $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    # 设置文件权限
    Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
    if (Invoke-RemoteCommand "chmod +x /tmp/omega-deployment/*.sh" "设置执行权限") {
        Write-Host "[INFO] 文件权限设置成功" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    文件上传完成！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "下一步操作："
    Write-Host "1. 自动配置服务器:" -ForegroundColor Yellow
    Write-Host "   .\deployment\auto_server_config.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 或手动连接服务器:" -ForegroundColor Yellow
    Write-Host "   ssh $ServerUser@$ServerIP" -ForegroundColor White
    Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
    Write-Host "   ./fix_server_limits.sh" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 启动GUI工具:" -ForegroundColor Yellow
    Write-Host "   cd deployment" -ForegroundColor White
    Write-Host "   python omega_update_gui.py" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # 清理连接
    if ($sshSession) { Remove-SSHSession -SessionId $sshSession.SessionId | Out-Null }
    if ($sftpSession) { Remove-SFTPSession -SessionId $sftpSession.SessionId | Out-Null }
}

Write-Host "上传完成！无需手动输入密码。" -ForegroundColor Green
