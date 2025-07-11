#!/bin/bash
# Omega更新服务器部署脚本
# 使用方法: ./deploy.sh [install|update|restart|status]

set -e

# 配置变量
SERVER_USER="omega"
SERVER_GROUP="omega"
INSTALL_DIR="/opt/omega-update-server"
WEB_DIR="/var/www/omega-updates"
LOG_DIR="/var/log/omega-updates"
SERVICE_NAME="omega-update-server"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        exit 1
    fi
}

install_dependencies() {
    log_info "安装系统依赖..."

    # 检测操作系统
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        log_info "检测到Debian/Ubuntu系统"
        apt update || { log_error "更新包列表失败"; exit 1; }
        apt install -y python3 python3-pip python3-venv nginx sqlite3 curl wget git ufw || { log_error "安装基础包失败"; exit 1; }
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        log_info "检测到CentOS/RHEL系统"
        yum update -y || { log_error "更新包列表失败"; exit 1; }
        yum install -y python3 python3-pip nginx sqlite curl wget git firewalld || { log_error "安装基础包失败"; exit 1; }
        systemctl enable firewalld
        systemctl start firewalld
    else
        log_error "不支持的操作系统"
        exit 1
    fi

    # 安装Python依赖管理工具
    pip3 install --upgrade pip setuptools wheel || { log_error "升级pip失败"; exit 1; }

    log_info "系统依赖安装完成"
}

create_user() {
    log_info "创建服务用户..."
    
    if ! id "$SERVER_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir "$INSTALL_DIR" --create-home "$SERVER_USER"
        log_info "用户 $SERVER_USER 创建成功"
    else
        log_warn "用户 $SERVER_USER 已存在"
    fi
}

create_directories() {
    log_info "创建目录结构..."
    
    # 创建必要目录
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$WEB_DIR"/{uploads,static}/{versions,packages,patches}
    mkdir -p "$LOG_DIR"
    
    # 设置权限
    chown -R "$SERVER_USER:$SERVER_GROUP" "$INSTALL_DIR"
    chown -R "$SERVER_USER:$SERVER_GROUP" "$WEB_DIR"
    chown -R "$SERVER_USER:$SERVER_GROUP" "$LOG_DIR"
    
    chmod 755 "$WEB_DIR"
    chmod 755 "$LOG_DIR"
    
    log_info "目录结构创建完成"
}

setup_python_env() {
    log_info "设置Python虚拟环境..."
    
    # 切换到安装目录
    cd "$INSTALL_DIR"
    
    # 创建虚拟环境
    if [ ! -d "venv" ]; then
        sudo -u "$SERVER_USER" python3 -m venv venv
        log_info "Python虚拟环境创建完成"
    fi
    
    # 激活虚拟环境并安装依赖
    sudo -u "$SERVER_USER" bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install fastapi uvicorn sqlalchemy python-multipart aiofiles
    "
    
    log_info "Python依赖安装完成"
}

deploy_application() {
    log_info "部署应用程序..."
    
    # 复制应用文件
    cp main.py "$INSTALL_DIR/"
    cp server_config.py "$INSTALL_DIR/"
    
    # 复制更新服务器模块
    if [ -d "../update_server" ]; then
        cp -r ../update_server "$INSTALL_DIR/"
    fi
    
    # 创建环境变量文件
    if [ ! -f "$INSTALL_DIR/.env" ]; then
        cat > "$INSTALL_DIR/.env" << EOF
# Omega更新服务器环境变量配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False

DATABASE_URL=sqlite:///$INSTALL_DIR/omega_updates.db

UPLOAD_DIR=$WEB_DIR/uploads
STATIC_DIR=$WEB_DIR/static
LOG_DIR=$LOG_DIR

SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 16)

MAX_FILE_SIZE=104857600
LOG_LEVEL=INFO
EOF
        log_info "环境变量文件创建完成"
    fi
    
    # 设置文件权限
    chown -R "$SERVER_USER:$SERVER_GROUP" "$INSTALL_DIR"
    chmod 600 "$INSTALL_DIR/.env"
    
    log_info "应用程序部署完成"
}

configure_nginx() {
    log_info "配置Nginx..."
    
    # 复制Nginx配置
    cp nginx.conf /etc/nginx/sites-available/omega-update-server
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/omega-update-server /etc/nginx/sites-enabled/
    
    # 删除默认站点
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试Nginx配置
    nginx -t
    
    # 重启Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log_info "Nginx配置完成"
}

configure_service() {
    log_info "配置systemd服务..."
    
    # 复制服务文件
    cp omega-update-server.service /etc/systemd/system/
    
    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable "$SERVICE_NAME"
    
    log_info "systemd服务配置完成"
}

configure_firewall() {
    log_info "配置防火墙..."

    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian 使用 ufw
        log_info "使用ufw配置防火墙..."
        ufw allow 22/tcp   # SSH
        ufw allow 80/tcp   # HTTP
        ufw allow 443/tcp  # HTTPS
        ufw --force enable
        ufw status
        log_info "ufw防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL 使用 firewalld
        log_info "使用firewalld配置防火墙..."
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        firewall-cmd --list-all
        log_info "firewalld防火墙配置完成"
    else
        log_warn "未找到防火墙工具，请手动配置防火墙规则"
        log_warn "需要开放端口: 22(SSH), 80(HTTP), 443(HTTPS)"
    fi
}

start_services() {
    log_info "启动服务..."
    
    # 启动应用服务
    systemctl start "$SERVICE_NAME"
    
    # 检查服务状态
    sleep 3
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_info "Omega更新服务器启动成功"
    else
        log_error "Omega更新服务器启动失败"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
    
    # 检查Nginx状态
    if systemctl is-active --quiet nginx; then
        log_info "Nginx运行正常"
    else
        log_error "Nginx启动失败"
        systemctl status nginx
        exit 1
    fi
}

show_status() {
    echo "=== Omega更新服务器状态 ==="
    echo
    echo "服务状态:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo
    echo "Nginx状态:"
    systemctl status nginx --no-pager -l
    echo
    echo "端口监听:"
    netstat -tlnp | grep -E ':80|:8000'
    echo
    echo "日志文件:"
    echo "  应用日志: $LOG_DIR/server.log"
    echo "  Nginx访问日志: /var/log/nginx/omega-update-access.log"
    echo "  Nginx错误日志: /var/log/nginx/omega-update-error.log"
    echo "  系统日志: journalctl -u $SERVICE_NAME"
}

install_all() {
    log_info "开始安装Omega更新服务器..."
    
    check_root
    install_dependencies
    create_user
    create_directories
    setup_python_env
    deploy_application
    configure_nginx
    configure_service
    configure_firewall
    start_services
    
    log_info "安装完成！"
    echo
    echo "服务器信息:"
    echo "  HTTP访问: http://106.14.28.97"
    echo "  API文档: http://106.14.28.97/docs"
    echo "  健康检查: http://106.14.28.97/health"
    echo
    show_status
}

update_application() {
    log_info "更新应用程序..."
    
    check_root
    
    # 停止服务
    systemctl stop "$SERVICE_NAME"
    
    # 备份当前版本
    backup_dir="/tmp/omega-backup-$(date +%Y%m%d-%H%M%S)"
    cp -r "$INSTALL_DIR" "$backup_dir"
    log_info "当前版本已备份到: $backup_dir"
    
    # 部署新版本
    deploy_application
    
    # 重启服务
    systemctl start "$SERVICE_NAME"
    
    log_info "应用程序更新完成"
}

restart_services() {
    log_info "重启服务..."
    
    check_root
    systemctl restart "$SERVICE_NAME"
    systemctl restart nginx
    
    log_info "服务重启完成"
}

# 主程序
case "${1:-install}" in
    install)
        install_all
        ;;
    update)
        update_application
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "使用方法: $0 [install|update|restart|status]"
        echo "  install  - 完整安装"
        echo "  update   - 更新应用"
        echo "  restart  - 重启服务"
        echo "  status   - 查看状态"
        exit 1
        ;;
esac
