#!/bin/bash
# 修复服务器文件上传大小限制

echo "=================================================="
echo "    修复Omega更新服务器文件大小限制"
echo "=================================================="

# 检查当前用户
if [[ $EUID -ne 0 ]]; then
   echo "此脚本需要root权限运行"
   exit 1
fi

echo "[INFO] 修复Nginx文件大小限制..."

# 备份原始配置
cp /etc/nginx/sites-available/omega-update-server /etc/nginx/sites-available/omega-update-server.backup.$(date +%Y%m%d_%H%M%S)

# 修改Nginx配置，增加文件大小限制
if ! grep -q "client_max_body_size" /etc/nginx/sites-available/omega-update-server; then
    # 在server块中添加client_max_body_size
    sed -i '/server {/a\    client_max_body_size 10G;' /etc/nginx/sites-available/omega-update-server
    echo "[INFO] 已添加Nginx文件大小限制: 10GB"
else
    # 更新现有的client_max_body_size
    sed -i 's/client_max_body_size.*;/client_max_body_size 10G;/' /etc/nginx/sites-available/omega-update-server
    echo "[INFO] 已更新Nginx文件大小限制: 10GB"
fi

# 修改FastAPI应用的文件大小限制
echo "[INFO] 修复FastAPI文件大小限制..."

# 更新环境变量文件
if grep -q "MAX_FILE_SIZE" /opt/omega-update-server/.env; then
    sed -i 's/MAX_FILE_SIZE=.*/MAX_FILE_SIZE=10737418240/' /opt/omega-update-server/.env
    echo "[INFO] 已更新应用文件大小限制: 10GB"
else
    echo "MAX_FILE_SIZE=10737418240" >> /opt/omega-update-server/.env
    echo "[INFO] 已添加应用文件大小限制: 10GB"
fi

# 修改系统临时目录大小（如果需要）
echo "[INFO] 检查临时目录空间..."
temp_space=$(df /tmp | tail -1 | awk '{print $4}')
temp_space_gb=$((temp_space / 1024 / 1024))

if [ $temp_space_gb -lt 20 ]; then
    echo "[WARN] /tmp 目录可用空间不足 20GB，当前: ${temp_space_gb}GB"
    echo "[WARN] 建议清理临时文件或扩展磁盘空间"
fi

# 测试Nginx配置
echo "[INFO] 测试Nginx配置..."
if nginx -t; then
    echo "[INFO] Nginx配置测试通过"
else
    echo "[ERROR] Nginx配置测试失败，恢复备份"
    cp /etc/nginx/sites-available/omega-update-server.backup.* /etc/nginx/sites-available/omega-update-server
    exit 1
fi

# 重启服务
echo "[INFO] 重启服务..."
systemctl restart nginx
systemctl restart omega-update-server

# 等待服务启动
sleep 5

# 检查服务状态
echo "[INFO] 检查服务状态..."
if systemctl is-active --quiet nginx && systemctl is-active --quiet omega-update-server; then
    echo "[SUCCESS] 服务重启成功"
else
    echo "[ERROR] 服务重启失败"
    systemctl status nginx --no-pager
    systemctl status omega-update-server --no-pager
    exit 1
fi

echo "=================================================="
echo "    文件大小限制修复完成"
echo "=================================================="
echo "新的限制:"
echo "  - Nginx: 10GB"
echo "  - FastAPI: 10GB"
echo "  - 建议单个文件不超过 8GB"
echo "=================================================="

# 显示当前配置
echo "[INFO] 当前Nginx配置:"
grep -n "client_max_body_size" /etc/nginx/sites-available/omega-update-server

echo "[INFO] 当前应用配置:"
grep "MAX_FILE_SIZE" /opt/omega-update-server/.env

echo "[INFO] 修复完成！现在可以上传更大的文件了。"
