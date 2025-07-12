# Simple large file upload test
param(
    [string]$FilePath = "test_1gb_file.zip",
    [string]$ServerIP = "106.14.28.97",
    [string]$ApiKey = "dac450db3ec47d79196edb7a34defaed"
)

Write-Host "Large File Upload Test" -ForegroundColor Green
Write-Host "File: $FilePath"
Write-Host "Server: $ServerIP"
Write-Host ""

# Check if file exists
if (-not (Test-Path $FilePath)) {
    Write-Host "ERROR: Test file not found: $FilePath" -ForegroundColor Red
    exit 1
}

# Get file info
$fileInfo = Get-Item $FilePath
$fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
Write-Host "File size: $fileSizeMB MB" -ForegroundColor Yellow

# Test using curl (simpler approach)
Write-Host "Starting upload with curl..." -ForegroundColor Blue

$curlCmd = @"
curl -X POST "http://$ServerIP/api/v1/upload/version" \
  -F "version=test-1.0.0" \
  -F "description=1GB file upload test" \
  -F "is_stable=true" \
  -F "is_critical=false" \
  -F "platform=windows" \
  -F "arch=x64" \
  -F "api_key=$ApiKey" \
  -F "file=@$FilePath" \
  --connect-timeout 300 \
  --max-time 3600 \
  -v
"@

Write-Host "Executing curl command..." -ForegroundColor Gray
try {
    $result = Invoke-Expression $curlCmd
    Write-Host "Upload completed!" -ForegroundColor Green
    Write-Host $result
} catch {
    Write-Host "Upload failed: $($_.Exception.Message)" -ForegroundColor Red
}
