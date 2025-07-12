# 自动上传脚本 - 使用预设密码
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root",
    [string]$Password = "LU@pyke7"
)

# 检查并安装posh-ssh模块
if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
    Write-Host "[INFO] 安装Posh-SSH模块..." -ForegroundColor Yellow
    try {
        Install-Module -Name Posh-SSH -Force -Scope CurrentUser -AllowClobber
        Write-Host "[INFO] Posh-SSH模块安装成功" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] 无法安装Posh-SSH模块: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "[INFO] 请手动安装: Install-Module -Name Posh-SSH -Force" -ForegroundColor Yellow
        exit 1
    }
}

try {
    Import-Module Posh-SSH -ErrorAction Stop
    Write-Host "[INFO] Posh-SSH模块加载成功" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 无法加载Posh-SSH模块: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 自动上传工具"
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
    
    # 创建远程目录
    Write-Host "[STEP] 创建远程目录..." -ForegroundColor Blue
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment"
    
    if ($result.ExitStatus -ne 0) {
        throw "无法创建远程目录: $($result.Error)"
    }
    
    # 建立SFTP连接
    Write-Host "[STEP] 建立SFTP连接..." -ForegroundColor Blue
    $sftp = New-SFTPSession -ComputerName $ServerIP -Credential $credential -AcceptKey
    
    if (-not $sftp) {
        throw "无法建立SFTP连接"
    }
    
    # 上传文件函数
    function Upload-File {
        param($LocalPath, $RemotePath, $Description)

        if (Test-Path $LocalPath) {
            Write-Host "  上传: $Description" -ForegroundColor Gray
            try {
                # 使用正确的Posh-SSH命令
                $null = Set-SFTPLocation -SessionId $sftp.SessionId -Path (Split-Path $RemotePath -Parent)
                $null = Put-SFTPItem -SessionId $sftp.SessionId -Path $LocalPath -Destination $RemotePath -Force
                Write-Host "    成功: $Description" -ForegroundColor Green
            } catch {
                Write-Host "    失败: $Description - $($_.Exception.Message)" -ForegroundColor Red
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
    
    # 上传项目文件
    Write-Host "[STEP] 上传项目文件..." -ForegroundColor Blue
    Upload-File "generate_update_package.py" "/tmp/omega-deployment/generate_update_package.py" "更新包生成器"
    Upload-File "simple_update_generator.py" "/tmp/omega-deployment/simple_update_generator.py" "简单更新生成器"
    Upload-File "version_analyzer.py" "/tmp/omega-deployment/version_analyzer.py" "版本分析器"
    
    # 上传update_server目录
    if (Test-Path "update_server") {
        Write-Host "[STEP] 上传update_server模块..." -ForegroundColor Blue
        
        # 递归上传目录
        function Upload-Directory {
            param($LocalDir, $RemoteDir)
            
            # 创建远程目录
            Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p $RemoteDir" | Out-Null
            
            Get-ChildItem $LocalDir -Recurse -File | ForEach-Object {
                $relativePath = $_.FullName.Substring($LocalDir.Length + 1).Replace('\', '/')
                $remoteFilePath = "$RemoteDir/$relativePath"
                $remoteFileDir = Split-Path $remoteFilePath -Parent
                
                # 创建远程子目录
                if ($remoteFileDir -ne $RemoteDir) {
                    Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p `"$remoteFileDir`"" | Out-Null
                }
                
                Write-Host "    上传: $relativePath" -ForegroundColor Gray
                try {
                    $null = Put-SFTPItem -SessionId $sftp.SessionId -Path $_.FullName -Destination $remoteFilePath -Force
                } catch {
                    Write-Host "      失败: $relativePath" -ForegroundColor Red
                }
            }
        }
        
        Upload-Directory "update_server" "/tmp/omega-deployment/update_server"
    }
    
    # 设置文件权限
    Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "chmod +x /tmp/omega-deployment/*.sh"
    
    if ($result.ExitStatus -eq 0) {
        Write-Host "[INFO] 文件权限设置成功" -ForegroundColor Green
    }
    
    # 关闭连接
    Remove-SSHSession -SessionId $session.SessionId | Out-Null
    Remove-SFTPSession -SessionId $sftp.SessionId | Out-Null
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    文件上传完成！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "下一步操作："
    Write-Host "1. 自动连接服务器并修复设置:" -ForegroundColor Yellow
    Write-Host "   .\deployment\auto_server_setup.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 或手动连接服务器:" -ForegroundColor Yellow
    Write-Host "   ssh root@$ServerIP" -ForegroundColor White
    Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
    Write-Host "   ./fix_server_limits.sh" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    
    # 清理连接
    if ($session) { Remove-SSHSession -SessionId $session.SessionId | Out-Null }
    if ($sftp) { Remove-SFTPSession -SessionId $sftp.SessionId | Out-Null }
    
    exit 1
}

Write-Host "上传完成！" -ForegroundColor Green
