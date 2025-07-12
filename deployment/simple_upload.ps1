# 简化的文件上传脚本
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root"
)

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 简化上传工具"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP"
Write-Host "用户: $ServerUser"
Write-Host "=================================================="
Write-Host ""

Write-Host "[INFO] 开始上传文件..." -ForegroundColor Green

try {
    # 创建远程目录
    Write-Host "[STEP] 创建远程目录..." -ForegroundColor Blue
    ssh "$ServerUser@$ServerIP" "mkdir -p /tmp/omega-deployment"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] 无法创建远程目录，请检查SSH连接" -ForegroundColor Red
        Write-Host "请手动测试连接: ssh $ServerUser@$ServerIP" -ForegroundColor Yellow
        exit 1
    }
    
    # 上传部署文件
    Write-Host "[STEP] 上传部署文件..." -ForegroundColor Blue
    
    $filesToUpload = @(
        "deployment\*.py",
        "deployment\*.sh", 
        "deployment\*.conf",
        "deployment\*.service",
        "deployment\*.md"
    )
    
    foreach ($pattern in $filesToUpload) {
        $files = Get-ChildItem $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Write-Host "  上传: $($file.Name)" -ForegroundColor Gray
            scp $file.FullName "${ServerUser}@${ServerIP}:/tmp/omega-deployment/"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[WARN] 上传失败: $($file.Name)" -ForegroundColor Yellow
            }
        }
    }
    
    # 上传项目文件
    Write-Host "[STEP] 上传项目文件..." -ForegroundColor Blue
    
    $projectFiles = @(
        "update_server",
        "generate_update_package.py",
        "simple_update_generator.py",
        "version_analyzer.py"
    )
    
    foreach ($item in $projectFiles) {
        if (Test-Path $item) {
            Write-Host "  上传: $item" -ForegroundColor Gray
            if (Test-Path $item -PathType Container) {
                # 目录
                scp -r $item "${ServerUser}@${ServerIP}:/tmp/omega-deployment/"
            } else {
                # 文件
                scp $item "${ServerUser}@${ServerIP}:/tmp/omega-deployment/"
            }
            
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[WARN] 上传失败: $item" -ForegroundColor Yellow
            }
        } else {
            Write-Host "[WARN] 文件不存在，跳过: $item" -ForegroundColor Yellow
        }
    }
    
    # 设置文件权限
    Write-Host "[STEP] 设置文件权限..." -ForegroundColor Blue
    ssh "$ServerUser@$ServerIP" "chmod +x /tmp/omega-deployment/*.sh"
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    文件上传完成！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "下一步操作："
    Write-Host "1. 连接到服务器:" -ForegroundColor Yellow
    Write-Host "   ssh $ServerUser@$ServerIP" -ForegroundColor White
    Write-Host ""
    Write-Host "2. 修复服务器限制:" -ForegroundColor Yellow
    Write-Host "   cd /tmp/omega-deployment" -ForegroundColor White
    Write-Host "   ./fix_server_limits.sh" -ForegroundColor White
    Write-Host ""
    Write-Host "3. 检查服务状态:" -ForegroundColor Yellow
    Write-Host "   ./diagnose.sh" -ForegroundColor White
    Write-Host ""
    Write-Host "4. 如有问题，运行修复:" -ForegroundColor Yellow
    Write-Host "   ./fix_common_issues.sh" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] 上传过程中出现错误: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查："
    Write-Host "1. SSH连接是否正常"
    Write-Host "2. 网络连接是否稳定"
    Write-Host "3. 服务器是否可访问"
    Write-Host ""
    Write-Host "手动测试连接:"
    Write-Host "ssh $ServerUser@$ServerIP" -ForegroundColor Yellow
    exit 1
}

Write-Host "上传完成！请按照上述步骤继续操作。" -ForegroundColor Green
