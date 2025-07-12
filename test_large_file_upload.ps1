# 大文件上传测试脚本
# 测试1GB文件上传功能

param(
    [string]$FilePath = "test_1gb_file.zip",
    [string]$Version = "test-1.0.0",
    [string]$Description = "1GB文件上传测试",
    [string]$ServerIP = "106.14.28.97",
    [string]$ApiKey = "dac450db3ec47d79196edb7a34defaed"
)

Write-Host "=================================================="
Write-Host "    Omega更新服务器 - 大文件上传测试"
Write-Host "=================================================="
Write-Host "文件: $FilePath"
Write-Host "版本: $Version"
Write-Host "服务器: $ServerIP"
Write-Host "=================================================="
Write-Host ""

# 检查文件是否存在
if (-not (Test-Path $FilePath)) {
    Write-Host "[ERROR] 测试文件不存在: $FilePath" -ForegroundColor Red
    Write-Host "请先运行以下命令创建测试文件:" -ForegroundColor Yellow
    Write-Host "fsutil file createnew $FilePath 1073741824" -ForegroundColor White
    exit 1
}

# 获取文件信息
$fileInfo = Get-Item $FilePath
$fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
$fileSizeGB = [math]::Round($fileInfo.Length / 1GB, 2)

Write-Host "[INFO] File size: $fileSizeMB MB ($fileSizeGB GB)" -ForegroundColor Green
Write-Host ""

# 准备上传数据
$uploadUrl = "http://$ServerIP/api/v1/upload/version"

Write-Host "[STEP] 开始上传文件..." -ForegroundColor Blue
Write-Host "上传URL: $uploadUrl" -ForegroundColor Gray

try {
    # 使用Invoke-RestMethod上传文件
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    # 读取文件内容
    Write-Host "[INFO] 读取文件内容..." -ForegroundColor Yellow
    $fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
    
    # 构建multipart/form-data内容
    Write-Host "[INFO] 构建上传数据..." -ForegroundColor Yellow
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"version`"$LF",
        $Version,
        "--$boundary",
        "Content-Disposition: form-data; name=`"description`"$LF", 
        $Description,
        "--$boundary",
        "Content-Disposition: form-data; name=`"is_stable`"$LF",
        "true",
        "--$boundary",
        "Content-Disposition: form-data; name=`"is_critical`"$LF",
        "false", 
        "--$boundary",
        "Content-Disposition: form-data; name=`"platform`"$LF",
        "windows",
        "--$boundary",
        "Content-Disposition: form-data; name=`"arch`"$LF",
        "x64",
        "--$boundary",
        "Content-Disposition: form-data; name=`"api_key`"$LF",
        $ApiKey,
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$($fileInfo.Name)`"",
        "Content-Type: application/zip$LF"
    )
    
    $bodyString = ($bodyLines -join $LF) + $LF
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyString)
    
    # 组合所有数据
    $endBoundaryBytes = [System.Text.Encoding]::UTF8.GetBytes("$LF--$boundary--$LF")
    $totalBytes = $bodyBytes + $fileBytes + $endBoundaryBytes
    
    Write-Host "[INFO] 开始HTTP上传 (总大小: $([math]::Round($totalBytes.Length / 1MB, 2)) MB)..." -ForegroundColor Yellow
    
    # 设置较长的超时时间
    $timeoutSeconds = 3600  # 1小时
    
    # 执行上传
    $response = Invoke-RestMethod -Uri $uploadUrl -Method Post -Body $totalBytes -ContentType "multipart/form-data; boundary=$boundary" -TimeoutSec $timeoutSeconds
    
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    上传成功！"
    Write-Host "=================================================="
    Write-Host "响应信息:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "=================================================="
    Write-Host "    上传失败！"
    Write-Host "=================================================="
    Write-Host "错误信息:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.Exception.Response) {
        Write-Host "HTTP状态码: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "错误详情: $errorBody" -ForegroundColor Red
        } catch {
            Write-Host "无法读取错误详情" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    exit 1
}

# 验证上传结果
Write-Host "[STEP] 验证上传结果..." -ForegroundColor Blue

try {
    $statsUrl = "http://$ServerIP/api/v1/stats"
    $stats = Invoke-RestMethod -Uri $statsUrl -Method Get
    
    Write-Host "服务器统计信息:" -ForegroundColor Green
    $stats | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
    
} catch {
    Write-Host "[WARN] 无法获取服务器统计信息: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================="
Write-Host "    测试完成！"
Write-Host "=================================================="
Write-Host "文件上传测试成功完成。" -ForegroundColor Green
Write-Host "可以通过以下URL访问服务器:" -ForegroundColor Yellow
Write-Host "  主页: http://$ServerIP" -ForegroundColor White
Write-Host "  API文档: http://$ServerIP/docs" -ForegroundColor White
Write-Host "  统计信息: http://$ServerIP/api/v1/stats" -ForegroundColor White
Write-Host ""
