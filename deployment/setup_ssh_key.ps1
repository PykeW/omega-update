# SSH密钥配置脚本 - 一次性设置，以后无需密码
param(
    [string]$ServerIP = "106.14.28.97",
    [string]$ServerUser = "root",
    [string]$Password = "LU@pyke7"
)

Write-Host "=================================================="
Write-Host "    SSH密钥配置工具 - 一次性设置"
Write-Host "=================================================="
Write-Host "服务器: $ServerIP"
Write-Host "用户: $ServerUser"
Write-Host "配置完成后，以后所有操作都无需输入密码！"
Write-Host "=================================================="
Write-Host ""

$keyPath = "$env:USERPROFILE\.ssh\id_rsa_omega"
$pubKeyPath = "$keyPath.pub"

try {
    # 检查SSH目录
    $sshDir = "$env:USERPROFILE\.ssh"
    if (-not (Test-Path $sshDir)) {
        Write-Host "[STEP] 创建SSH目录..." -ForegroundColor Blue
        New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    }

    # 生成SSH密钥对（如果不存在）
    if (-not (Test-Path $keyPath)) {
        Write-Host "[STEP] 生成SSH密钥对..." -ForegroundColor Blue
        Write-Host "  密钥路径: $keyPath" -ForegroundColor Gray
        
        # 生成密钥（无密码保护）
        & ssh-keygen -t rsa -b 4096 -f $keyPath -N '""' -C "omega-server-key" 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] SSH密钥生成成功" -ForegroundColor Green
        } else {
            throw "SSH密钥生成失败"
        }
    } else {
        Write-Host "[INFO] SSH密钥已存在，跳过生成" -ForegroundColor Yellow
    }

    # 读取公钥内容
    if (Test-Path $pubKeyPath) {
        $publicKey = Get-Content $pubKeyPath -Raw
        Write-Host "[INFO] 公钥内容:" -ForegroundColor Blue
        Write-Host $publicKey.Trim() -ForegroundColor Gray
    } else {
        throw "找不到公钥文件: $pubKeyPath"
    }

    # 将公钥复制到服务器
    Write-Host "[STEP] 将公钥复制到服务器..." -ForegroundColor Blue
    Write-Host "  需要输入一次密码来配置密钥认证" -ForegroundColor Yellow
    
    # 创建临时脚本来复制公钥
    $tempScript = @"
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo '$($publicKey.Trim())' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
# 去重
sort ~/.ssh/authorized_keys | uniq > ~/.ssh/authorized_keys.tmp
mv ~/.ssh/authorized_keys.tmp ~/.ssh/authorized_keys
echo "SSH密钥配置完成"
"@

    # 执行远程命令
    $sshOpts = @(
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "-o", "StrictHostKeyChecking=no"
    )
    
    $env:SSHPASS = $Password
    echo $tempScript | & ssh @sshOpts "$ServerUser@$ServerIP" "bash"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[INFO] 公钥复制成功" -ForegroundColor Green
    } else {
        throw "公钥复制失败"
    }

    # 测试密钥认证
    Write-Host "[STEP] 测试SSH密钥认证..." -ForegroundColor Blue
    
    $testResult = & ssh -i $keyPath -o "StrictHostKeyChecking=no" -o "PasswordAuthentication=no" "$ServerUser@$ServerIP" "echo 'SSH密钥认证测试成功'" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] SSH密钥认证配置成功！" -ForegroundColor Green
        Write-Host "测试结果: $testResult" -ForegroundColor Gray
        
        # 更新SSH配置文件
        Write-Host "[STEP] 更新SSH配置..." -ForegroundColor Blue
        $sshConfigPath = "$sshDir\config"
        $configEntry = @"

# Omega服务器配置
Host omega-server
    HostName $ServerIP
    User $ServerUser
    IdentityFile $keyPath
    IdentitiesOnly yes

Host $ServerIP
    User $ServerUser
    IdentityFile $keyPath
    IdentitiesOnly yes
"@

        # 检查配置是否已存在
        if (Test-Path $sshConfigPath) {
            $existingConfig = Get-Content $sshConfigPath -Raw
            if ($existingConfig -notlike "*omega-server*") {
                Add-Content -Path $sshConfigPath -Value $configEntry
                Write-Host "[INFO] SSH配置已更新" -ForegroundColor Green
            } else {
                Write-Host "[INFO] SSH配置已存在" -ForegroundColor Yellow
            }
        } else {
            Set-Content -Path $sshConfigPath -Value $configEntry.TrimStart()
            Write-Host "[INFO] SSH配置文件已创建" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "=================================================="
        Write-Host "    SSH密钥配置完成！"
        Write-Host "=================================================="
        Write-Host ""
        Write-Host "现在您可以使用以下方式无密码连接："
        Write-Host "1. 直接连接:" -ForegroundColor Yellow
        Write-Host "   ssh omega-server" -ForegroundColor White
        Write-Host "   或 ssh $ServerUser@$ServerIP" -ForegroundColor White
        Write-Host ""
        Write-Host "2. 运行无密码上传脚本:" -ForegroundColor Yellow
        Write-Host "   .\deployment\passwordless_upload.ps1" -ForegroundColor White
        Write-Host ""
        Write-Host "3. 运行无密码服务器配置:" -ForegroundColor Yellow
        Write-Host "   .\deployment\passwordless_server_setup.ps1" -ForegroundColor White
        Write-Host ""
        
    } else {
        Write-Host "[ERROR] SSH密钥认证测试失败" -ForegroundColor Red
        Write-Host "可能的原因：" -ForegroundColor Yellow
        Write-Host "1. 服务器SSH配置不允许密钥认证"
        Write-Host "2. 公钥复制过程有问题"
        Write-Host "3. 文件权限设置不正确"
        Write-Host ""
        Write-Host "请手动检查服务器上的 ~/.ssh/authorized_keys 文件"
    }

} catch {
    Write-Host "[ERROR] SSH密钥配置失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "您仍然可以使用密码认证的脚本："
    Write-Host ".\deployment\simple_auto_upload.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "SSH密钥配置完成！" -ForegroundColor Green
