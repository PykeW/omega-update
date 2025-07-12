# 部署增强版Omega更新服务器
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root"
)

Write-Host "=================================================="
Write-Host "    部署增强版Omega更新服务器"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP"
Write-Host "用户: $ServerUser"
Write-Host "=================================================="
Write-Host ""

# 检查文件是否存在
$requiredFiles = @(
    "enhanced_database.py",
    "storage_manager.py", 
    "enhanced_main.py",
    "advanced_upload_gui.py",
    "storage_management_strategy.md"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "[ERROR] 缺少必要文件: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "[INFO] 所有必要文件检查完成" -ForegroundColor Green

try {
    # 1. 备份当前版本
    Write-Host "[STEP] 备份当前版本..." -ForegroundColor Blue
    ssh $ServerUser@$ServerIP "cd /opt/omega-update-server && cp -r . ../omega-update-server-backup-$(date +%Y%m%d_%H%M%S)"
    Write-Host "[INFO] 备份完成" -ForegroundColor Green

    # 2. 停止服务
    Write-Host "[STEP] 停止服务..." -ForegroundColor Blue
    ssh $ServerUser@$ServerIP "systemctl stop omega-update-server"
    Write-Host "[INFO] 服务已停止" -ForegroundColor Green

    # 3. 上传新文件
    Write-Host "[STEP] 上传增强版文件..." -ForegroundColor Blue
    
    # 上传数据库模型
    scp enhanced_database.py $ServerUser@${ServerIP}:/opt/omega-update-server/
    Write-Host "  ✓ 上传 enhanced_database.py" -ForegroundColor Gray
    
    # 上传存储管理器
    scp storage_manager.py $ServerUser@${ServerIP}:/opt/omega-update-server/
    Write-Host "  ✓ 上传 storage_manager.py" -ForegroundColor Gray
    
    # 上传增强版主程序
    scp enhanced_main.py $ServerUser@${ServerIP}:/opt/omega-update-server/
    Write-Host "  ✓ 上传 enhanced_main.py" -ForegroundColor Gray
    
    # 上传文档
    scp storage_management_strategy.md $ServerUser@${ServerIP}:/opt/omega-update-server/
    Write-Host "  ✓ 上传 storage_management_strategy.md" -ForegroundColor Gray

    Write-Host "[INFO] 文件上传完成" -ForegroundColor Green

    # 4. 创建存储目录结构
    Write-Host "[STEP] 创建存储目录结构..." -ForegroundColor Blue
    ssh $ServerUser@$ServerIP @"
        mkdir -p /var/www/updates/{full,patches,hotfixes,temp}
        chown -R omega:omega /var/www/updates
        chmod -R 755 /var/www/updates
"@
    Write-Host "[INFO] 存储目录创建完成" -ForegroundColor Green

    # 5. 数据库迁移
    Write-Host "[STEP] 执行数据库迁移..." -ForegroundColor Blue
    ssh $ServerUser@$ServerIP @"
        cd /opt/omega-update-server
        source venv/bin/activate
        python enhanced_database.py
"@
    Write-Host "[INFO] 数据库迁移完成" -ForegroundColor Green

    # 6. 更新systemd服务文件
    Write-Host "[STEP] 更新服务配置..." -ForegroundColor Blue
    ssh $ServerUser@$ServerIP @"
        cd /opt/omega-update-server
        sed -i 's/main.py/enhanced_main.py/' /etc/systemd/system/omega-update-server.service
        systemctl daemon-reload
"@
    Write-Host "[INFO] 服务配置更新完成" -ForegroundColor Green

    # 7. 启动服务
    Write-Host "[STEP] 启动增强版服务..." -ForegroundColor Blue
    ssh $ServerUser@$ServerIP "systemctl start omega-update-server"
    Start-Sleep -Seconds 5
    
    # 检查服务状态
    $serviceStatus = ssh $ServerUser@$ServerIP "systemctl is-active omega-update-server"
    if ($serviceStatus -eq "active") {
        Write-Host "[INFO] 增强版服务启动成功" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] 服务启动失败" -ForegroundColor Red
        ssh $ServerUser@$ServerIP "journalctl -u omega-update-server --no-pager -n 10"
        throw "服务启动失败"
    }

    # 8. 验证功能
    Write-Host "[STEP] 验证增强版功能..." -ForegroundColor Blue
    
    # 测试健康检查
    $healthResponse = curl -s "http://$ServerIP/health"
    if ($healthResponse -like "*healthy*") {
        Write-Host "  ✓ 健康检查正常" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ 健康检查失败" -ForegroundColor Red
    }
    
    # 测试存储统计
    $storageResponse = curl -s "http://$ServerIP/api/v1/storage/stats"
    if ($storageResponse -like "*usage_percentage*") {
        Write-Host "  ✓ 存储统计API正常" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ 存储统计API失败" -ForegroundColor Red
    }
    
    # 测试包列表
    $packagesResponse = curl -s "http://$ServerIP/api/v1/packages"
    if ($packagesResponse -like "*[*") {
        Write-Host "  ✓ 包列表API正常" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ 包列表API失败" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    增强版部署成功！"
    Write-Host "=================================================="
    Write-Host ""
    Write-Host "新功能:" -ForegroundColor Green
    Write-Host "  • 支持完整包、增量包、热修复包" -ForegroundColor White
    Write-Host "  • 智能存储管理和自动清理" -ForegroundColor White
    Write-Host "  • 存储空间监控和告警" -ForegroundColor White
    Write-Host "  • 增强的版本管理" -ForegroundColor White
    Write-Host ""
    Write-Host "API端点:" -ForegroundColor Green
    Write-Host "  • POST /api/v1/upload/package - 上传包（支持类型选择）" -ForegroundColor White
    Write-Host "  • GET  /api/v1/storage/stats - 存储统计" -ForegroundColor White
    Write-Host "  • POST /api/v1/storage/cleanup - 手动清理" -ForegroundColor White
    Write-Host "  • GET  /api/v1/packages - 包列表" -ForegroundColor White
    Write-Host ""
    Write-Host "GUI工具:" -ForegroundColor Green
    Write-Host "  运行: python advanced_upload_gui.py" -ForegroundColor White
    Write-Host ""
    Write-Host "存储配置:" -ForegroundColor Green
    Write-Host "  • 最大完整包: 3个" -ForegroundColor White
    Write-Host "  • 最大增量包: 10个" -ForegroundColor White
    Write-Host "  • 最大热修复包: 20个" -ForegroundColor White
    Write-Host "  • 自动清理阈值: 85%" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    部署失败！"
    Write-Host "=================================================="
    Write-Host "错误信息:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "回滚建议:" -ForegroundColor Yellow
    Write-Host "1. 恢复备份:" -ForegroundColor White
    Write-Host "   ssh $ServerUser@$ServerIP" -ForegroundColor Gray
    Write-Host "   systemctl stop omega-update-server" -ForegroundColor Gray
    Write-Host "   cd /opt && rm -rf omega-update-server" -ForegroundColor Gray
    Write-Host "   mv omega-update-server-backup-* omega-update-server" -ForegroundColor Gray
    Write-Host "   systemctl start omega-update-server" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "部署完成！现在可以使用增强版功能了。" -ForegroundColor Green
