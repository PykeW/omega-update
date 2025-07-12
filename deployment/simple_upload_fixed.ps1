# 修复版本的自动上传脚本
# 使用更简单可靠的方法

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
Write-Host "    Omega更新服务器 - 修复版上传工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP ($Domain)"
Write-Host "用户: $ServerUser"
Write-Host "=================================================="
Write-Host ""

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

# 创建凭据对象
$securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($ServerUser, $securePassword)

try {
    # 建立SSH连接
    Write-Host "[STEP] 建立SSH连接..." -ForegroundColor Blue
    $sshSession = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey
    
    if (-not $sshSession) {
        throw "无法建立SSH连接"
    }
    
    Write-Host "[INFO] SSH连接成功" -ForegroundColor Green
    
    # 执行远程命令函数
    function Invoke-RemoteCommand {
        param($Command, $Description)
        
        $result = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $Command
        
        if ($result.ExitStatus -eq 0) {
            if ($Description) {
                Write-Host "    成功: $Description" -ForegroundColor Green
            }
            return $true
        } else {
            if ($Description) {
                Write-Host "    失败: $Description" -ForegroundColor Red
                if ($result.Error) {
                    Write-Host "    错误: $($result.Error)" -ForegroundColor Red
                }
            }
            return $false
        }
    }
    
    # 创建远程目录
    Write-Host "[STEP] 创建远程目录..." -ForegroundColor Blue
    if (-not (Invoke-RemoteCommand "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment" "创建部署目录")) {
        throw "无法创建远程目录"
    }
    
    # 使用SSH传输文件内容的函数
    function Upload-FileContent {
        param($LocalPath, $RemotePath, $Description)
        
        if (Test-Path $LocalPath) {
            Write-Host "  上传: $Description" -ForegroundColor Gray
            try {
                # 读取本地文件内容
                $content = Get-Content $LocalPath -Raw -Encoding UTF8
                
                # 转义特殊字符
                $escapedContent = $content -replace "'", "'\\''" -replace "`n", "\n" -replace "`r", ""
                
                # 使用SSH命令创建文件
                $createFileCmd = "cat > '$RemotePath' << 'OMEGA_EOF'`n$content`nOMEGA_EOF"
                $result = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $createFileCmd
                
                if ($result.ExitStatus -eq 0) {
                    Write-Host "    成功: $Description" -ForegroundColor Green
                } else {
                    Write-Host "    失败: $Description" -ForegroundColor Red
                }
            } catch {
                Write-Host "    失败: $Description - $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "  跳过: $Description (文件不存在)" -ForegroundColor Yellow
        }
    }
    
    # 上传部署脚本
    Write-Host "[STEP] 上传部署脚本..." -ForegroundColor Blue
    Upload-FileContent "deployment\deploy.sh" "/tmp/omega-deployment/deploy.sh" "部署脚本"
    Upload-FileContent "deployment\diagnose.sh" "/tmp/omega-deployment/diagnose.sh" "诊断脚本"
    Upload-FileContent "deployment\fix_common_issues.sh" "/tmp/omega-deployment/fix_common_issues.sh" "修复脚本"
    Upload-FileContent "deployment\fix_server_limits.sh" "/tmp/omega-deployment/fix_server_limits.sh" "限制修复脚本"
    
    # 上传配置文件
    Write-Host "[STEP] 上传配置文件..." -ForegroundColor Blue
    Upload-FileContent "deployment\main.py" "/tmp/omega-deployment/main.py" "主程序"
    Upload-FileContent "deployment\server_config.py" "/tmp/omega-deployment/server_config.py" "服务器配置"
    Upload-FileContent "deployment\nginx.conf" "/tmp/omega-deployment/nginx.conf" "Nginx配置"
    Upload-FileContent "deployment\omega-update-server.service" "/tmp/omega-deployment/omega-update-server.service" "系统服务"
    
    # 上传工具脚本
    Write-Host "[STEP] 上传工具脚本..." -ForegroundColor Blue
    Upload-FileContent "deployment\simple_package_maker.py" "/tmp/omega-deployment/simple_package_maker.py" "更新包制作工具"
    Upload-FileContent "generate_update_package.py" "/tmp/omega-deployment/generate_update_package.py" "更新包生成器"
    Upload-FileContent "simple_update_generator.py" "/tmp/omega-deployment/simple_update_generator.py" "简单更新生成器"
    Upload-FileContent "version_analyzer.py" "/tmp/omega-deployment/version_analyzer.py" "版本分析器"
    
    # 上传update_server目录
    if (Test-Path "update_server") {
        Write-Host "[STEP] 上传update_server模块..." -ForegroundColor Blue
        
        # 创建远程目录结构
        Invoke-RemoteCommand "mkdir -p /tmp/omega-deployment/update_server/{api,models,config,utils}" "创建update_server目录结构"
        
        # 上传Python文件
        Get-ChildItem "update_server" -Recurse -Filter "*.py" | ForEach-Object {
            $relativePath = $_.FullName.Substring((Get-Item "update_server").FullName.Length + 1).Replace('\', '/')
            $remotePath = "/tmp/omega-deployment/update_server/$relativePath"
            
            Write-Host "    上传: $relativePath" -ForegroundColor Gray
            
            # 读取文件内容并上传
            $content = Get-Content $_.FullName -Raw -Encoding UTF8
            $createFileCmd = "cat > '$remotePath' << 'OMEGA_EOF'`n$content`nOMEGA_EOF"
            $result = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command $createFileCmd
            
            if ($result.ExitStatus -eq 0) {
                Write-Host "      成功: $relativePath" -ForegroundColor Green
            } else {
                Write-Host "      失败: $relativePath" -ForegroundColor Red
            }
        }
    }
    
    # 设置文件权限
    Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
    if (Invoke-RemoteCommand "chmod +x /tmp/omega-deployment/*.sh" "设置执行权限") {
        Write-Host "[INFO] 文件权限设置成功" -ForegroundColor Green
    }
    
    # 验证上传结果
    Write-Host "[STEP] 验证上传结果..." -ForegroundColor Blue
    $result = Invoke-SSHCommand -SessionId $sshSession.SessionId -Command "ls -la /tmp/omega-deployment/"
    if ($result.Output) {
        Write-Host "上传的文件列表:" -ForegroundColor Gray
        Write-Host $result.Output -ForegroundColor Gray
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
    
} catch {
    Write-Host "[ERROR] 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # 清理连接
    if ($sshSession) { Remove-SSHSession -SessionId $sshSession.SessionId | Out-Null }
}

Write-Host "上传完成！真正无需手动输入密码。" -ForegroundColor Green
