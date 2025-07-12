#!/bin/bash
# Omega更新服务器常见问题修复脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[修复]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1"
}

show_banner() {
    echo "=================================================="
    echo "    Omega更新服务器 - 常见问题修复工具"
    echo "=================================================="
    echo
}

fix_permissions() {
    log_info "修复文件权限..."
    
    # 确保omega用户存在
    if ! id omega &>/dev/null; then
        log_info "创建omega用户..."
        useradd --system --shell /bin/bash --home-dir /opt/omega-update-server --create-home omega
    fi
    
    # 修复目录权限
    local dirs=(
        "/opt/omega-update-server"
        "/var/www/omega-updates"
        "/var/log/omega-updates"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_info "修复 $dir 权限..."
            chown -R omega:omega "$dir"
            chmod -R 755 "$dir"
        fi
    done
    
    # 修复环境变量文件权限
    if [ -f "/opt/omega-update-server/.env" ]; then
        chmod 600 /opt/omega-update-server/.env
        chown omega:omega /opt/omega-update-server/.env
    fi
    
    log_info "文件权限修复完成"
}

fix_nginx_config() {
    log_info "修复Nginx配置..."
    
    # 检查配置文件是否存在
    if [ ! -f "/etc/nginx/sites-available/omega-update-server" ]; then
        log_error "Nginx配置文件不存在，请重新部署"
        return 1
    fi
    
    # 测试配置
    if ! nginx -t; then
        log_error "Nginx配置有误，请检查配置文件"
        return 1
    fi
    
    # 确保站点已启用
    if [ ! -L "/etc/nginx/sites-enabled/omega-update-server" ]; then
        log_info "启用Omega更新服务器站点..."
        ln -sf /etc/nginx/sites-available/omega-update-server /etc/nginx/sites-enabled/
    fi
    
    # 删除默认站点
    if [ -L "/etc/nginx/sites-enabled/default" ]; then
        log_info "删除默认站点..."
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    # 重启Nginx
    systemctl restart nginx
    log_info "Nginx配置修复完成"
}

fix_python_environment() {
    log_info "修复Python环境..."

    local venv_dir="/opt/omega-update-server/venv"

    # 确保目录存在
    mkdir -p /opt/omega-update-server
    chown omega:omega /opt/omega-update-server

    # 检查虚拟环境
    if [ ! -d "$venv_dir" ]; then
        log_info "重新创建Python虚拟环境..."
        cd /opt/omega-update-server
        sudo -u omega python3 -m venv venv
    fi

    # 重新安装依赖（使用国内镜像）
    log_info "重新安装Python依赖..."
    sudo -u omega bash -c "
        cd /opt/omega-update-server
        source venv/bin/activate
        pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip install fastapi -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip install uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip install sqlalchemy -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip install python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip install aiofiles -i https://pypi.tuna.tsinghua.edu.cn/simple
        pip list | grep -E '(fastapi|uvicorn|sqlalchemy|multipart|aiofiles)'
    "

    log_info "Python环境修复完成"
}

fix_database() {
    log_info "修复数据库..."
    
    local db_file="/opt/omega-update-server/omega_updates.db"
    
    # 如果数据库文件不存在，重新初始化
    if [ ! -f "$db_file" ]; then
        log_info "重新初始化数据库..."
        cd /opt/omega-update-server
        sudo -u omega bash -c "
            source venv/bin/activate
            python -c 'from update_server.models.database import init_database; init_database()'
        "
    fi
    
    # 修复数据库权限
    if [ -f "$db_file" ]; then
        chown omega:omega "$db_file"
        chmod 644 "$db_file"
    fi
    
    log_info "数据库修复完成"
}

fix_systemd_service() {
    log_info "修复systemd服务..."
    
    # 检查服务文件
    if [ ! -f "/etc/systemd/system/omega-update-server.service" ]; then
        log_error "服务文件不存在，请重新部署"
        return 1
    fi
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable omega-update-server
    
    # 重启服务
    systemctl restart omega-update-server
    
    log_info "systemd服务修复完成"
}

fix_firewall() {
    log_info "修复防火墙配置..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian 使用 ufw
        ufw allow 22/tcp   # SSH
        ufw allow 80/tcp   # HTTP
        ufw allow 443/tcp  # HTTPS
        ufw --force enable
        log_info "ufw防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL 使用 firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        log_info "firewalld防火墙配置完成"
    else
        log_warn "未找到防火墙工具，请手动配置"
    fi
}

fix_environment_variables() {
    log_info "修复环境变量..."
    
    local env_file="/opt/omega-update-server/.env"
    
    if [ ! -f "$env_file" ]; then
        log_info "创建环境变量文件..."
        cat > "$env_file" << EOF
# Omega更新服务器环境变量配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

DATABASE_URL=sqlite:///./omega_updates.db

UPLOAD_DIR=/var/www/omega-updates/uploads
STATIC_DIR=/var/www/omega-updates/static
LOG_DIR=/var/log/omega-updates

SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 16)

MAX_FILE_SIZE=104857600
LOG_LEVEL=INFO
EOF
        chown omega:omega "$env_file"
        chmod 600 "$env_file"
        log_info "环境变量文件创建完成"
    else
        log_info "环境变量文件已存在"
    fi
}

check_and_fix_all() {
    log_info "开始全面修复..."
    
    # 按顺序执行修复
    fix_permissions
    fix_environment_variables
    fix_python_environment
    fix_database
    fix_nginx_config
    fix_systemd_service
    fix_firewall
    
    log_info "全面修复完成"
}

verify_fixes() {
    log_info "验证修复结果..."
    
    # 检查服务状态
    local services=("nginx" "omega-update-server")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_info "$service 服务运行正常"
        else
            log_error "$service 服务仍有问题"
        fi
    done
    
    # 检查端口监听
    if netstat -tlnp | grep -q ":80 "; then
        log_info "端口80监听正常"
    else
        log_error "端口80未监听"
    fi
    
    if netstat -tlnp | grep -q ":8000 "; then
        log_info "端口8000监听正常"
    else
        log_error "端口8000未监听"
    fi
    
    # 测试HTTP接口
    sleep 3
    if curl -s --connect-timeout 5 "http://localhost/health" > /dev/null; then
        log_info "HTTP接口响应正常"
    else
        log_error "HTTP接口仍有问题"
    fi
}

show_usage() {
    echo "Omega更新服务器常见问题修复工具"
    echo
    echo "使用方法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --permissions    修复文件权限"
    echo "  --nginx         修复Nginx配置"
    echo "  --python        修复Python环境"
    echo "  --database      修复数据库"
    echo "  --service       修复systemd服务"
    echo "  --firewall      修复防火墙"
    echo "  --env           修复环境变量"
    echo "  --all           执行全面修复（默认）"
    echo "  --help, -h      显示此帮助信息"
    echo
}

# 主程序
main() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
    
    show_banner
    
    case "${1:-all}" in
        --permissions)
            fix_permissions
            ;;
        --nginx)
            fix_nginx_config
            ;;
        --python)
            fix_python_environment
            ;;
        --database)
            fix_database
            ;;
        --service)
            fix_systemd_service
            ;;
        --firewall)
            fix_firewall
            ;;
        --env)
            fix_environment_variables
            ;;
        --all)
            check_and_fix_all
            verify_fixes
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
    
    echo
    log_info "修复完成！建议运行诊断脚本验证："
    echo "  ./diagnose.sh"
}

# 运行主程序
main "$@"
