# PowerShell脚本：上传文件到Omega更新服务器
# 适用于Windows环境

param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root",
    [string]$ServerDomain = "update.chpyke.cn"
)

# 颜色输出函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "[STEP] $Message" -ForegroundColor Blue
}

function Show-Banner {
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "    Omega软件自动更新系统 - Windows部署工具" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host "服务器IP: $ServerIP"
    Write-Host "域名: $ServerDomain"
    Write-Host "用户: $ServerUser"
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-SSHConnection {
    Write-Step "检查SSH连接..."
    
    try {
        $result = ssh -o ConnectTimeout=10 -o BatchMode=yes "$ServerUser@$ServerIP" "exit" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Info "SSH连接正常"
            return $true
        } else {
            Write-Error "无法连接到服务器 $ServerIP"
            Write-Error "请确保："
            Write-Host "  1. 服务器IP地址正确"
            Write-Host "  2. SSH密钥已配置或密码认证可用"
            Write-Host "  3. 服务器允许SSH连接"
            return $false
        }
    } catch {
        Write-Error "SSH连接测试失败: $($_.Exception.Message)"
        return $false
    }
}

function Test-RequiredFiles {
    Write-Step "检查本地文件..."
    
    $requiredFiles = @(
        "deployment\deploy.sh",
        "deployment\main.py",
        "deployment\server_config.py",
        "deployment\nginx.conf",
        "deployment\omega-update-server.service"
    )
    
    $allFilesExist = $true
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            Write-Info "✓ $file"
        } else {
            Write-Error "✗ $file (文件不存在)"
            $allFilesExist = $false
        }
    }
    
    return $allFilesExist
}

function Upload-DeploymentFiles {
    Write-Step "上传部署文件到服务器..."
    
    try {
        # 创建远程目录
        Write-Info "创建远程目录..."
        ssh "$ServerUser@$ServerIP" "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment"
        
        # 上传deployment目录下的所有文件
        Write-Info "上传部署配置文件..."
        scp deployment\*.py "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
        scp deployment\*.sh "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
        scp deployment\*.conf "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
        scp deployment\*.service "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
        scp deployment\*.md "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
        
        # 上传update_server目录
        if (Test-Path "update_server") {
            Write-Info "上传update_server模块..."
            scp -r update_server "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
        }
        
        # 上传其他项目文件
        $projectFiles = @(
            "generate_update_package.py",
            "simple_update_generator.py", 
            "version_analyzer.py",
            "PROJECT_STRUCTURE.md"
        )
        
        foreach ($file in $projectFiles) {
            if (Test-Path $file) {
                Write-Info "上传: $file"
                scp $file "$ServerUser@${ServerIP}:/tmp/omega-deployment/"
            } else {
                Write-Warn "文件不存在，跳过: $file"
            }
        }
        
        # 设置文件权限
        Write-Info "设置文件权限..."
        ssh "$ServerUser@$ServerIP" "chmod +x /tmp/omega-deployment/*.sh"
        
        Write-Info "文件上传完成"
        return $true
        
    } catch {
        Write-Error "文件上传失败: $($_.Exception.Message)"
        return $false
    }
}

function Show-NextSteps {
    Write-Host ""
    Write-Host "=== 文件上传完成 ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步操作："
    Write-Host "1. 连接到服务器:" -ForegroundColor Yellow
    Write-Host "   ssh $ServerUser@$ServerIP" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 进入部署目录:" -ForegroundColor Yellow
    Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 运行部署脚本:" -ForegroundColor Yellow
    Write-Host "   ./deploy.sh install" -ForegroundColor White
    Write-Host ""
    Write-Host "4. 检查服务状态:" -ForegroundColor Yellow
    Write-Host "   ./deploy.sh status" -ForegroundColor White
    Write-Host ""
    Write-Host "5. 访问服务器:" -ForegroundColor Yellow
    Write-Host "   http://$ServerDomain" -ForegroundColor White
    Write-Host "   http://$ServerDomain/docs (API文档)" -ForegroundColor White
    Write-Host ""
    Write-Host "如果遇到问题，可以运行诊断脚本:" -ForegroundColor Yellow
    Write-Host "   ./diagnose.sh" -ForegroundColor White
    Write-Host ""
    Write-Host "或运行修复脚本:" -ForegroundColor Yellow
    Write-Host "   ./fix_common_issues.sh" -ForegroundColor White
    Write-Host ""
}

function Test-Prerequisites {
    Write-Step "检查部署前提条件..."
    
    # 检查SSH命令
    try {
        ssh -V 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "SSH命令不可用，请安装OpenSSH客户端"
            return $false
        }
    } catch {
        Write-Error "SSH命令不可用，请安装OpenSSH客户端"
        return $false
    }
    
    # 检查SCP命令
    try {
        scp 2>$null | Out-Null
    } catch {
        Write-Error "SCP命令不可用，请安装OpenSSH客户端"
        return $false
    }
    
    Write-Info "SSH/SCP工具检查通过"
    return $true
}

# 主程序
function Main {
    Show-Banner
    
    # 检查前提条件
    if (-not (Test-Prerequisites)) {
        Write-Error "前提条件检查失败，请安装必要工具后重试"
        exit 1
    }
    
    # 检查本地文件
    if (-not (Test-RequiredFiles)) {
        Write-Error "本地文件检查失败，请确保所有必要文件存在"
        exit 1
    }
    
    # 检查SSH连接
    if (-not (Test-SSHConnection)) {
        Write-Error "SSH连接检查失败，请检查网络和认证配置"
        exit 1
    }
    
    # 上传文件
    if (-not (Upload-DeploymentFiles)) {
        Write-Error "文件上传失败"
        exit 1
    }
    
    # 显示下一步操作
    Show-NextSteps
}

# 运行主程序
Main
