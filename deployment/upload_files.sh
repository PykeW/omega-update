#!/bin/bash
# 文件上传脚本
# 将本地文件上传到阿里云服务器

set -e

# 服务器配置
SERVER_IP="106.14.28.97"
SERVER_USER="root"
SERVER_PORT="22"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_ssh_connection() {
    log_info "检查SSH连接..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" exit 2>/dev/null; then
        log_info "SSH连接正常"
    else
        log_error "无法连接到服务器，请检查："
        echo "  1. 服务器IP地址是否正确"
        echo "  2. SSH密钥是否已配置"
        echo "  3. 服务器是否允许SSH连接"
        exit 1
    fi
}

upload_deployment_files() {
    log_info "上传部署文件..."
    
    # 创建远程目录
    ssh "$SERVER_USER@$SERVER_IP" "mkdir -p /tmp/omega-deployment"
    
    # 上传部署文件
    scp -r deployment/* "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/"
    
    # 上传更新服务器模块
    if [ -d "update_server" ]; then
        scp -r update_server "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/"
    fi
    
    log_info "部署文件上传完成"
}

upload_project_files() {
    log_info "上传项目文件..."
    
    # 创建项目文件列表
    files_to_upload=(
        "updater/"
        "generate_update_package.py"
        "simple_update_generator.py"
        "version_analyzer.py"
        "PROJECT_STRUCTURE.md"
        "Pipfile"
        "Pipfile.lock"
    )
    
    # 上传项目文件
    for file in "${files_to_upload[@]}"; do
        if [ -e "$file" ]; then
            log_info "上传: $file"
            scp -r "$file" "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/"
        else
            log_warn "文件不存在，跳过: $file"
        fi
    done
    
    log_info "项目文件上传完成"
}

set_permissions() {
    log_info "设置文件权限..."
    
    ssh "$SERVER_USER@$SERVER_IP" "
        chmod +x /tmp/omega-deployment/deploy.sh
        chmod +x /tmp/omega-deployment/upload_files.sh
        chmod 644 /tmp/omega-deployment/*.py
        chmod 644 /tmp/omega-deployment/*.conf
        chmod 644 /tmp/omega-deployment/*.service
    "
    
    log_info "文件权限设置完成"
}

show_next_steps() {
    echo
    echo "=== 文件上传完成 ==="
    echo
    echo "下一步操作："
    echo "1. 连接到服务器:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo
    echo "2. 进入部署目录:"
    echo "   cd /tmp/omega-deployment"
    echo
    echo "3. 运行部署脚本:"
    echo "   ./deploy.sh install"
    echo
    echo "4. 检查服务状态:"
    echo "   ./deploy.sh status"
    echo
    echo "5. 访问服务器:"
    echo "   http://$SERVER_IP"
    echo "   http://$SERVER_IP/docs (API文档)"
    echo
}

# 主程序
main() {
    log_info "开始上传文件到Omega更新服务器..."
    
    check_ssh_connection
    upload_deployment_files
    upload_project_files
    set_permissions
    
    show_next_steps
}

# 检查参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Omega更新服务器文件上传脚本"
    echo
    echo "使用方法: $0"
    echo
    echo "此脚本将上传以下文件到服务器:"
    echo "  - 部署脚本和配置文件"
    echo "  - 更新服务器代码"
    echo "  - 项目相关文件"
    echo
    echo "服务器信息:"
    echo "  IP: $SERVER_IP"
    echo "  用户: $SERVER_USER"
    echo "  端口: $SERVER_PORT"
    echo
    exit 0
fi

# 运行主程序
main
