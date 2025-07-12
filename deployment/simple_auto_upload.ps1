# 简化的自动上传脚本 - 使用SCP
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root",
    [string]$Password = "LU@pyke7"
)

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 简化自动上传工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP"
Write-Host "用户: $ServerUser"
Write-Host "=================================================="
Write-Host ""

# 创建临时密码文件（用于sshpass）
$tempDir = $env:TEMP
$passwordFile = Join-Path $tempDir "omega_ssh_pass.txt"
$Password | Out-File -FilePath $passwordFile -Encoding ASCII -NoNewline

try {
    # SSH选项
    $sshOpts = @(
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL"
    )
    
    # 创建远程目录
    Write-Host "[STEP] 创建远程目录..." -ForegroundColor Blue
    $env:SSHPASS = $Password
    $result = & ssh @sshOpts "$ServerUser@$ServerIP" "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment" 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        # 如果sshpass不可用，尝试使用expect或其他方法
        Write-Host "[INFO] 尝试使用PowerShell SSH..." -ForegroundColor Yellow
        
        # 使用.NET的SSH库
        if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
            Write-Host "[INFO] 安装Posh-SSH模块..." -ForegroundColor Yellow
            Install-Module -Name Posh-SSH -Force -Scope CurrentUser -AllowClobber
        }
        
        Import-Module Posh-SSH
        
        # 创建凭据
        $securePassword = ConvertTo-SecureString $Password -AsPlainText -Force
        $credential = New-Object System.Management.Automation.PSCredential ($ServerUser, $securePassword)
        
        # 建立SSH连接
        $session = New-SSHSession -ComputerName $ServerIP -Credential $credential -AcceptKey
        
        if (-not $session) {
            throw "无法建立SSH连接"
        }
        
        Write-Host "[INFO] SSH连接成功" -ForegroundColor Green
        
        # 创建远程目录
        $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment"
        
        if ($result.ExitStatus -ne 0) {
            throw "无法创建远程目录"
        }
        
        # 使用PowerShell方式上传文件
        Write-Host "[STEP] 使用PowerShell SSH上传文件..." -ForegroundColor Blue
        
        # 上传文件函数
        function Upload-FileContent {
            param($LocalPath, $RemotePath, $Description)
            
            if (Test-Path $LocalPath) {
                Write-Host "  上传: $Description" -ForegroundColor Gray
                $content = Get-Content $LocalPath -Raw -Encoding UTF8
                $encodedContent = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
                
                # 使用base64编码传输文件内容
                $uploadCmd = "echo '$encodedContent' | base64 -d > '$RemotePath'"
                $result = Invoke-SSHCommand -SessionId $session.SessionId -Command $uploadCmd
                
                if ($result.ExitStatus -ne 0) {
                    Write-Host "    失败: $Description" -ForegroundColor Red
                } else {
                    Write-Host "    成功: $Description" -ForegroundColor Green
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
        
        # 上传项目文件
        Write-Host "[STEP] 上传项目文件..." -ForegroundColor Blue
        if (Test-Path "generate_update_package.py") {
            Upload-FileContent "generate_update_package.py" "/tmp/omega-deployment/generate_update_package.py" "更新包生成器"
        }
        if (Test-Path "simple_update_generator.py") {
            Upload-FileContent "simple_update_generator.py" "/tmp/omega-deployment/simple_update_generator.py" "简单更新生成器"
        }
        if (Test-Path "version_analyzer.py") {
            Upload-FileContent "version_analyzer.py" "/tmp/omega-deployment/version_analyzer.py" "版本分析器"
        }
        
        # 上传update_server目录（简化版本，只上传主要文件）
        if (Test-Path "update_server") {
            Write-Host "[STEP] 上传update_server模块..." -ForegroundColor Blue
            
            # 创建远程目录结构
            Invoke-SSHCommand -SessionId $session.SessionId -Command "mkdir -p /tmp/omega-deployment/update_server/{api,models,config,utils,static}" | Out-Null
            
            # 上传主要Python文件
            Get-ChildItem "update_server" -Recurse -Filter "*.py" | ForEach-Object {
                $relativePath = $_.FullName.Substring((Get-Item "update_server").FullName.Length + 1).Replace('\', '/')
                $remotePath = "/tmp/omega-deployment/update_server/$relativePath"
                
                Write-Host "    上传: $relativePath" -ForegroundColor Gray
                $content = Get-Content $_.FullName -Raw -Encoding UTF8
                $encodedContent = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
                $uploadCmd = "echo '$encodedContent' | base64 -d > '$remotePath'"
                Invoke-SSHCommand -SessionId $session.SessionId -Command $uploadCmd | Out-Null
            }
        }
        
        # 设置文件权限
        Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
        $result = Invoke-SSHCommand -SessionId $session.SessionId -Command "chmod +x /tmp/omega-deployment/*.sh"
        
        if ($result.ExitStatus -eq 0) {
            Write-Host "[INFO] 文件权限设置成功" -ForegroundColor Green
        }
        
        # 关闭连接
        Remove-SSHSession -SessionId $session.SessionId | Out-Null
        
        Write-Host ""
        Write-Host "=================================================="
        Write-Host "    文件上传完成！"
        Write-Host "=================================================="
        Write-Host ""
        Write-Host "下一步操作："
        Write-Host "1. 自动配置服务器:" -ForegroundColor Yellow
        Write-Host "   .\deployment\auto_server_setup.ps1" -ForegroundColor White
        Write-Host ""
        Write-Host "2. 或手动连接服务器:" -ForegroundColor Yellow
        Write-Host "   ssh root@$ServerIP" -ForegroundColor White
        Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
        Write-Host "   ./fix_server_limits.sh" -ForegroundColor White
        Write-Host ""
        
    } else {
        Write-Host "[INFO] 使用系统SSH成功创建目录" -ForegroundColor Green

        # 使用SCP上传文件
        Write-Host "[STEP] 使用SCP上传文件..." -ForegroundColor Blue

        # 上传部署脚本
        Write-Host "[STEP] 上传部署脚本..." -ForegroundColor Blue
        $deploymentFiles = @(
            @{Local="deployment\deploy.sh"; Remote="/tmp/omega-deployment/deploy.sh"; Desc="部署脚本"},
            @{Local="deployment\diagnose.sh"; Remote="/tmp/omega-deployment/diagnose.sh"; Desc="诊断脚本"},
            @{Local="deployment\fix_common_issues.sh"; Remote="/tmp/omega-deployment/fix_common_issues.sh"; Desc="修复脚本"},
            @{Local="deployment\fix_server_limits.sh"; Remote="/tmp/omega-deployment/fix_server_limits.sh"; Desc="限制修复脚本"}
        )

        foreach ($file in $deploymentFiles) {
            if (Test-Path $file.Local) {
                Write-Host "  上传: $($file.Desc)" -ForegroundColor Gray
                $env:SSHPASS = $Password
                & scp @sshOpts $file.Local "$ServerUser@${ServerIP}:$($file.Remote)" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    成功: $($file.Desc)" -ForegroundColor Green
                } else {
                    Write-Host "    失败: $($file.Desc)" -ForegroundColor Red
                }
            }
        }

        # 上传配置文件
        Write-Host "[STEP] 上传配置文件..." -ForegroundColor Blue
        $configFiles = @(
            @{Local="deployment\main.py"; Remote="/tmp/omega-deployment/main.py"; Desc="主程序"},
            @{Local="deployment\server_config.py"; Remote="/tmp/omega-deployment/server_config.py"; Desc="服务器配置"},
            @{Local="deployment\nginx.conf"; Remote="/tmp/omega-deployment/nginx.conf"; Desc="Nginx配置"},
            @{Local="deployment\omega-update-server.service"; Remote="/tmp/omega-deployment/omega-update-server.service"; Desc="系统服务"}
        )

        foreach ($file in $configFiles) {
            if (Test-Path $file.Local) {
                Write-Host "  上传: $($file.Desc)" -ForegroundColor Gray
                $env:SSHPASS = $Password
                & scp @sshOpts $file.Local "$ServerUser@${ServerIP}:$($file.Remote)" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    成功: $($file.Desc)" -ForegroundColor Green
                } else {
                    Write-Host "    失败: $($file.Desc)" -ForegroundColor Red
                }
            }
        }

        # 上传工具脚本
        Write-Host "[STEP] 上传工具脚本..." -ForegroundColor Blue
        $toolFiles = @(
            @{Local="deployment\simple_package_maker.py"; Remote="/tmp/omega-deployment/simple_package_maker.py"; Desc="更新包制作工具"},
            @{Local="generate_update_package.py"; Remote="/tmp/omega-deployment/generate_update_package.py"; Desc="更新包生成器"},
            @{Local="simple_update_generator.py"; Remote="/tmp/omega-deployment/simple_update_generator.py"; Desc="简单更新生成器"},
            @{Local="version_analyzer.py"; Remote="/tmp/omega-deployment/version_analyzer.py"; Desc="版本分析器"}
        )

        foreach ($file in $toolFiles) {
            if (Test-Path $file.Local) {
                Write-Host "  上传: $($file.Desc)" -ForegroundColor Gray
                $env:SSHPASS = $Password
                & scp @sshOpts $file.Local "$ServerUser@${ServerIP}:$($file.Remote)" 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    成功: $($file.Desc)" -ForegroundColor Green
                } else {
                    Write-Host "    失败: $($file.Desc)" -ForegroundColor Red
                }
            }
        }

        # 上传update_server目录
        if (Test-Path "update_server") {
            Write-Host "[STEP] 上传update_server模块..." -ForegroundColor Blue
            $env:SSHPASS = $Password
            & scp @sshOpts -r "update_server" "$ServerUser@${ServerIP}:/tmp/omega-deployment/" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "    成功: update_server模块" -ForegroundColor Green
            } else {
                Write-Host "    失败: update_server模块" -ForegroundColor Red
            }
        }

        # 设置文件权限
        Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
        $env:SSHPASS = $Password
        & ssh @sshOpts "$ServerUser@$ServerIP" "chmod +x /tmp/omega-deployment/*.sh" 2>$null
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
        Write-Host "   .\deployment\auto_server_setup.ps1" -ForegroundColor White
        Write-Host ""
        Write-Host "2. 或手动连接服务器:" -ForegroundColor Yellow
        Write-Host "   ssh root@$ServerIP" -ForegroundColor White
        Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
        Write-Host "   ./fix_server_limits.sh" -ForegroundColor White
        Write-Host ""
    }
    
} catch {
    Write-Host "[ERROR] 上传失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # 清理临时文件
    if (Test-Path $passwordFile) {
        Remove-Item $passwordFile -Force
    }
}

Write-Host "上传完成！请运行下一步配置脚本。" -ForegroundColor Green
