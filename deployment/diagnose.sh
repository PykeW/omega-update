#!/bin/bash
# Omega更新服务器诊断脚本
# 用于快速诊断部署问题

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_check() {
    echo -e "${BLUE}[检查]${NC} $1"
}

show_banner() {
    echo "=================================================="
    echo "    Omega更新服务器 - 系统诊断工具"
    echo "=================================================="
    echo
}

check_system_info() {
    log_check "系统信息"
    echo "操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "内核版本: $(uname -r)"
    echo "系统时间: $(date)"
    echo "运行时间: $(uptime)"
    echo
}

check_disk_space() {
    log_check "磁盘空间"
    df -h | grep -E "(Filesystem|/dev/)"
    echo
    
    # 检查关键目录空间
    local critical_dirs=("/opt" "/var" "/tmp")
    for dir in "${critical_dirs[@]}"; do
        if [ -d "$dir" ]; then
            local usage=$(df "$dir" | tail -1 | awk '{print $5}' | sed 's/%//')
            if [ "$usage" -gt 90 ]; then
                log_error "$dir 磁盘使用率过高: ${usage}%"
            elif [ "$usage" -gt 80 ]; then
                log_warn "$dir 磁盘使用率较高: ${usage}%"
            else
                log_info "$dir 磁盘使用率正常: ${usage}%"
            fi
        fi
    done
    echo
}

check_memory() {
    log_check "内存使用"
    free -h
    echo
    
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$mem_usage" -gt 90 ]; then
        log_error "内存使用率过高: ${mem_usage}%"
    elif [ "$mem_usage" -gt 80 ]; then
        log_warn "内存使用率较高: ${mem_usage}%"
    else
        log_info "内存使用率正常: ${mem_usage}%"
    fi
    echo
}

check_services() {
    log_check "服务状态"
    
    local services=("nginx" "omega-update-server")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_info "$service 服务运行正常"
        else
            log_error "$service 服务未运行"
            echo "  状态详情:"
            systemctl status "$service" --no-pager -l | head -10
        fi
    done
    echo
}

check_ports() {
    log_check "端口监听"
    
    local ports=("80" "8000" "22")
    for port in "${ports[@]}"; do
        if netstat -tlnp | grep -q ":$port "; then
            local process=$(netstat -tlnp | grep ":$port " | awk '{print $7}' | head -1)
            log_info "端口 $port 正在监听 ($process)"
        else
            log_error "端口 $port 未监听"
        fi
    done
    echo
}

check_network() {
    log_check "网络连接"
    
    # 检查外网连接
    if ping -c 1 8.8.8.8 &> /dev/null; then
        log_info "外网连接正常"
    else
        log_error "外网连接失败"
    fi
    
    # 检查域名解析
    if nslookup update.chpyke.cn &> /dev/null; then
        local ip=$(nslookup update.chpyke.cn | grep "Address:" | tail -1 | awk '{print $2}')
        log_info "域名解析正常: update.chpyke.cn -> $ip"
    else
        log_error "域名解析失败: update.chpyke.cn"
    fi
    echo
}

check_files() {
    log_check "关键文件"
    
    local files=(
        "/opt/omega-update-server/main.py"
        "/opt/omega-update-server/.env"
        "/opt/omega-update-server/omega_updates.db"
        "/etc/nginx/sites-available/omega-update-server"
        "/etc/systemd/system/omega-update-server.service"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log_info "$file 存在"
        else
            log_error "$file 不存在"
        fi
    done
    echo
}

check_logs() {
    log_check "日志文件"
    
    local log_files=(
        "/var/log/omega-updates/server.log"
        "/var/log/nginx/omega-update-access.log"
        "/var/log/nginx/omega-update-error.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            local size=$(du -h "$log_file" | cut -f1)
            log_info "$log_file 存在 (大小: $size)"
            
            # 检查最近的错误
            if [ "$log_file" = "/var/log/omega-updates/server.log" ]; then
                local errors=$(tail -100 "$log_file" | grep -i error | wc -l)
                if [ "$errors" -gt 0 ]; then
                    log_warn "发现 $errors 个错误日志"
                fi
            fi
        else
            log_error "$log_file 不存在"
        fi
    done
    echo
}

check_http_endpoints() {
    log_check "HTTP接口测试"
    
    local endpoints=(
        "http://localhost/"
        "http://localhost/health"
        "http://localhost/api/v1/stats"
        "http://update.chpyke.cn/"
        "http://update.chpyke.cn/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s --connect-timeout 5 "$endpoint" > /dev/null; then
            log_info "$endpoint 响应正常"
        else
            log_error "$endpoint 响应失败"
        fi
    done
    echo
}

check_database() {
    log_check "数据库检查"
    
    local db_file="/opt/omega-update-server/omega_updates.db"
    if [ -f "$db_file" ]; then
        log_info "数据库文件存在"
        
        # 检查表结构
        local tables=$(sqlite3 "$db_file" ".tables" 2>/dev/null || echo "")
        if [ -n "$tables" ]; then
            log_info "数据库表: $tables"
        else
            log_error "数据库表为空或无法访问"
        fi
        
        # 检查版本数据
        local version_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM versions;" 2>/dev/null || echo "0")
        log_info "版本记录数: $version_count"
    else
        log_error "数据库文件不存在"
    fi
    echo
}

check_permissions() {
    log_check "文件权限"
    
    local omega_user="omega"
    if id "$omega_user" &>/dev/null; then
        log_info "用户 $omega_user 存在"
        
        # 检查关键目录权限
        local dirs=(
            "/opt/omega-update-server"
            "/var/www/omega-updates"
            "/var/log/omega-updates"
        )
        
        for dir in "${dirs[@]}"; do
            if [ -d "$dir" ]; then
                local owner=$(stat -c '%U:%G' "$dir")
                if [[ "$owner" == *"$omega_user"* ]]; then
                    log_info "$dir 权限正确 ($owner)"
                else
                    log_warn "$dir 权限可能有问题 ($owner)"
                fi
            fi
        done
    else
        log_error "用户 $omega_user 不存在"
    fi
    echo
}

show_quick_fixes() {
    echo "=================================================="
    echo "    常见问题快速修复"
    echo "=================================================="
    echo
    echo "1. 重启所有服务:"
    echo "   systemctl restart omega-update-server nginx"
    echo
    echo "2. 查看详细错误日志:"
    echo "   journalctl -u omega-update-server -f"
    echo "   tail -f /var/log/omega-updates/server.log"
    echo
    echo "3. 重新配置Nginx:"
    echo "   nginx -t"
    echo "   systemctl reload nginx"
    echo
    echo "4. 修复文件权限:"
    echo "   chown -R omega:omega /opt/omega-update-server"
    echo "   chown -R omega:omega /var/www/omega-updates"
    echo
    echo "5. 重新部署:"
    echo "   cd /tmp/omega-deployment"
    echo "   ./deploy.sh restart"
    echo
}

# 主程序
main() {
    show_banner
    check_system_info
    check_disk_space
    check_memory
    check_services
    check_ports
    check_network
    check_files
    check_logs
    check_http_endpoints
    check_database
    check_permissions
    show_quick_fixes
}

# 运行诊断
main "$@"
