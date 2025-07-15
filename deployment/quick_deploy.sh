#!/bin/bash
# Omega更新服务器快速部署脚本
# 一键完成从本地到服务器的完整部署流程

set -e

# 配置变量
SERVER_IP="106.14.28.97"
SERVER_DOMAIN="update.chpyke.cn"
SERVER_USER="root"
LOCAL_PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

show_banner() {
    echo "=================================================="
    echo "    Omega软件自动更新系统 - 快速部署工具"
    echo "=================================================="
    echo "服务器IP: $SERVER_IP"
    echo "域名: $SERVER_DOMAIN"
    echo "用户: $SERVER_USER"
    echo "项目目录: $LOCAL_PROJECT_DIR"
    echo "=================================================="
    echo
}

check_prerequisites() {
    log_step "检查部署前提条件..."

    # 检查必要命令
    local commands=("ssh" "scp" "curl")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "缺少必要命令: $cmd"
            exit 1
        fi
    done

    # 检查SSH连接
    log_info "测试SSH连接..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_USER@$SERVER_IP" exit 2>/dev/null; then
        log_error "无法连接到服务器 $SERVER_IP"
        log_error "请确保："
        echo "  1. 服务器IP地址正确"
        echo "  2. SSH密钥已配置或密码认证可用"
        echo "  3. 服务器防火墙允许SSH连接"
        exit 1
    fi

    log_info "SSH连接测试成功"

    # 检查本地文件
    local required_files=(
        "deployment/deploy.sh"
        "deployment/main.py"
        "deployment/server_config.py"
        "deployment/nginx.conf"
        "deployment/omega-update-server.service"
        "update_server/models/database.py"
        "update_server/models/database.py"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$LOCAL_PROJECT_DIR/$file" ]; then
            log_error "缺少必要文件: $file"
            exit 1
        fi
    done

    log_info "本地文件检查完成"
}

upload_files() {
    log_step "上传文件到服务器..."

    # 创建远程临时目录
    ssh "$SERVER_USER@$SERVER_IP" "rm -rf /tmp/omega-deployment && mkdir -p /tmp/omega-deployment"

    # 上传部署文件
    log_info "上传部署配置文件..."
    scp -q "$DEPLOYMENT_DIR"/*.{py,sh,conf,service} "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/" 2>/dev/null || true
    scp -q "$DEPLOYMENT_DIR"/README.md "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/" 2>/dev/null || true

    # 上传项目文件
    log_info "上传项目源码..."
    if [ -d "$LOCAL_PROJECT_DIR/update_server" ]; then
        scp -q -r "$LOCAL_PROJECT_DIR/update_server" "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/"
    fi

    # 上传其他必要文件
    local project_files=(
        "generate_update_package.py"
        "simple_update_generator.py"
        "version_analyzer.py"
        "PROJECT_STRUCTURE.md"
    )

    for file in "${project_files[@]}"; do
        if [ -f "$LOCAL_PROJECT_DIR/$file" ]; then
            scp -q "$LOCAL_PROJECT_DIR/$file" "$SERVER_USER@$SERVER_IP:/tmp/omega-deployment/"
        fi
    done

    # 设置文件权限
    ssh "$SERVER_USER@$SERVER_IP" "chmod +x /tmp/omega-deployment/*.sh"

    log_info "文件上传完成"
}

deploy_server() {
    log_step "在服务器上执行部署..."

    # 执行部署脚本
    ssh "$SERVER_USER@$SERVER_IP" "cd /tmp/omega-deployment && ./deploy.sh install"

    log_info "服务器部署完成"
}

verify_deployment() {
    log_step "验证部署结果..."

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    log_info "检查服务状态..."
    if ssh "$SERVER_USER@$SERVER_IP" "systemctl is-active --quiet omega-update-server"; then
        log_info "✅ Omega更新服务运行正常"
    else
        log_error "❌ Omega更新服务启动失败"
        return 1
    fi

    if ssh "$SERVER_USER@$SERVER_IP" "systemctl is-active --quiet nginx"; then
        log_info "✅ Nginx服务运行正常"
    else
        log_error "❌ Nginx服务启动失败"
        return 1
    fi

    # 测试HTTP接口
    log_info "测试HTTP接口..."
    local max_retries=5
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if curl -s --connect-timeout 10 "http://$SERVER_IP/health" > /dev/null; then
            log_info "✅ HTTP接口响应正常"
            break
        else
            retry=$((retry + 1))
            if [ $retry -lt $max_retries ]; then
                log_warn "HTTP接口测试失败，重试 $retry/$max_retries..."
                sleep 5
            else
                log_error "❌ HTTP接口测试失败"
                return 1
            fi
        fi
    done

    # 测试API接口
    log_info "测试API接口..."
    if curl -s "http://$SERVER_IP/api/v1/stats" | grep -q "total_versions"; then
        log_info "✅ API接口响应正常"
    else
        log_warn "⚠️  API接口可能存在问题"
    fi

    log_info "部署验证完成"
}

show_deployment_info() {
    log_step "部署完成信息"

    echo
    echo "🎉 Omega更新服务器部署成功！"
    echo
    echo "服务器信息:"
    echo "  IP地址: $SERVER_IP"
    echo "  主页: http://$SERVER_IP"
    echo "  API文档: http://$SERVER_IP/docs"
    echo "  健康检查: http://$SERVER_IP/health"
    echo "  统计信息: http://$SERVER_IP/api/v1/stats"
    echo
    echo "管理命令:"
    echo "  连接服务器: ssh $SERVER_USER@$SERVER_IP"
    echo "  查看状态: ssh $SERVER_USER@$SERVER_IP 'cd /tmp/omega-deployment && ./deploy.sh status'"
    echo "  重启服务: ssh $SERVER_USER@$SERVER_IP 'cd /tmp/omega-deployment && ./deploy.sh restart'"
    echo "  查看日志: ssh $SERVER_USER@$SERVER_IP 'tail -f /var/log/omega-updates/server.log'"
    echo
    echo "下一步操作:"
    echo "  1. 修改API密钥: 编辑 /opt/omega-update-server/.env"
    echo "  2. 上传更新包: 使用 deployment/manage_updates.py"
    echo "  3. 配置域名: 修改 /etc/nginx/sites-available/omega-update-server"
    echo "  4. 配置SSL: 使用 certbot 获取HTTPS证书"
    echo
}

show_usage() {
    echo "Omega更新服务器快速部署工具"
    echo
    echo "使用方法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --check-only    仅检查部署条件，不执行部署"
    echo "  --upload-only   仅上传文件，不执行部署"
    echo "  --deploy-only   仅执行部署（假设文件已上传）"
    echo "  --verify-only   仅验证现有部署"
    echo "  --help, -h      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0                # 完整部署流程"
    echo "  $0 --check-only   # 仅检查部署条件"
    echo "  $0 --upload-only  # 仅上传文件"
    echo
}

# 主程序
main() {
    local check_only=false
    local upload_only=false
    local deploy_only=false
    local verify_only=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check-only)
                check_only=true
                shift
                ;;
            --upload-only)
                upload_only=true
                shift
                ;;
            --deploy-only)
                deploy_only=true
                shift
                ;;
            --verify-only)
                verify_only=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    show_banner

    # 执行相应操作
    if [ "$check_only" = true ]; then
        check_prerequisites
        log_info "部署条件检查完成，可以开始部署"
    elif [ "$upload_only" = true ]; then
        check_prerequisites
        upload_files
        log_info "文件上传完成，可以执行部署"
    elif [ "$deploy_only" = true ]; then
        deploy_server
        verify_deployment
        show_deployment_info
    elif [ "$verify_only" = true ]; then
        verify_deployment
        log_info "部署验证完成"
    else
        # 完整部署流程
        check_prerequisites
        upload_files
        deploy_server
        verify_deployment
        show_deployment_info
    fi
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 运行主程序
main "$@"
