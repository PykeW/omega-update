# Omega更新服务器部署检查清单

## 部署前检查

### 1. 本地环境准备
- [ ] 确认项目文件完整
  - [ ] `deployment/` 目录存在
  - [ ] `update_server/` 目录存在
  - [ ] 主要Python文件存在（generate_update_package.py等）
- [ ] SSH工具可用
  - [ ] `ssh` 命令可用
  - [ ] `scp` 命令可用
- [ ] 网络连接正常
  - [ ] 可以ping通服务器IP (106.14.28.97)

### 2. 服务器访问准备
- [ ] SSH密钥已配置
  - [ ] 公钥已添加到服务器 `~/.ssh/authorized_keys`
  - [ ] 可以无密码登录: `ssh root@106.14.28.97`
- [ ] 或者确认root密码可用
- [ ] 服务器防火墙允许SSH连接（端口22）

### 3. 服务器环境检查
- [ ] 操作系统兼容（Ubuntu 18.04+, CentOS 7+）
- [ ] 磁盘空间充足（至少5GB可用空间）
- [ ] 内存充足（至少1GB可用内存）
- [ ] 网络连接正常（可以访问外网下载包）

## 部署过程检查

### 1. 文件上传
- [ ] 部署文件上传成功
  - [ ] `deploy.sh` 脚本
  - [ ] `main.py` 主程序
  - [ ] `server_config.py` 配置文件
  - [ ] `nginx.conf` Nginx配置
  - [ ] `omega-update-server.service` 服务配置
- [ ] 项目文件上传成功
  - [ ] `update_server/` 模块
  - [ ] Python工具脚本
- [ ] 文件权限设置正确
  - [ ] 脚本文件可执行

### 2. 系统依赖安装
- [ ] Python 3.8+ 安装成功
- [ ] pip 安装成功
- [ ] Nginx 安装成功
- [ ] SQLite 安装成功
- [ ] 其他系统工具安装成功

### 3. 用户和目录创建
- [ ] 服务用户 `omega` 创建成功
- [ ] 应用目录创建成功: `/opt/omega-update-server/`
- [ ] Web目录创建成功: `/var/www/omega-updates/`
- [ ] 日志目录创建成功: `/var/log/omega-updates/`
- [ ] 目录权限设置正确

### 4. Python环境配置
- [ ] 虚拟环境创建成功
- [ ] Python依赖安装成功
  - [ ] FastAPI
  - [ ] Uvicorn
  - [ ] SQLAlchemy
  - [ ] 其他依赖包
- [ ] 环境变量文件创建成功

### 5. 服务配置
- [ ] Nginx配置文件部署成功
- [ ] Nginx配置测试通过: `nginx -t`
- [ ] systemd服务文件部署成功
- [ ] 服务配置重新加载: `systemctl daemon-reload`

### 6. 防火墙配置
- [ ] 端口22（SSH）开放
- [ ] 端口80（HTTP）开放
- [ ] 端口443（HTTPS）开放（如需要）
- [ ] 防火墙规则生效

## 部署后验证

### 1. 服务状态检查
- [ ] Omega更新服务运行正常
  ```bash
  systemctl status omega-update-server
  ```
- [ ] Nginx服务运行正常
  ```bash
  systemctl status nginx
  ```
- [ ] 服务自启动已启用
  ```bash
  systemctl is-enabled omega-update-server
  systemctl is-enabled nginx
  ```

### 2. 端口监听检查
- [ ] 端口8000监听正常（FastAPI）
  ```bash
  netstat -tlnp | grep :8000
  ```
- [ ] 端口80监听正常（Nginx）
  ```bash
  netstat -tlnp | grep :80
  ```

### 3. HTTP接口测试
- [ ] 主页访问正常
  ```bash
  curl http://106.14.28.97/
  ```
- [ ] 健康检查接口正常
  ```bash
  curl http://106.14.28.97/health
  ```
- [ ] API接口正常
  ```bash
  curl http://106.14.28.97/api/v1/stats
  ```
- [ ] API文档可访问
  - 浏览器访问: http://106.14.28.97/docs

### 4. 数据库检查
- [ ] 数据库文件创建成功
  ```bash
  ls -la /opt/omega-update-server/omega_updates.db
  ```
- [ ] 数据库表创建成功
  ```bash
  sqlite3 /opt/omega-update-server/omega_updates.db ".tables"
  ```
- [ ] 默认配置数据存在
  ```bash
  sqlite3 /opt/omega-update-server/omega_updates.db "SELECT * FROM server_config;"
  ```

### 5. 文件权限检查
- [ ] 应用文件权限正确
  ```bash
  ls -la /opt/omega-update-server/
  ```
- [ ] Web目录权限正确
  ```bash
  ls -la /var/www/omega-updates/
  ```
- [ ] 日志目录权限正确
  ```bash
  ls -la /var/log/omega-updates/
  ```

### 6. 日志检查
- [ ] 应用日志正常
  ```bash
  tail -n 20 /var/log/omega-updates/server.log
  ```
- [ ] Nginx访问日志正常
  ```bash
  tail -n 20 /var/log/nginx/omega-update-access.log
  ```
- [ ] 系统日志无错误
  ```bash
  journalctl -u omega-update-server --no-pager -l
  ```

## 功能测试

### 1. 版本检查功能
- [ ] 版本检查API正常
  ```bash
  curl "http://106.14.28.97/api/v1/version/check?current_version=1.0.0"
  ```

### 2. 版本列表功能
- [ ] 版本列表API正常
  ```bash
  curl "http://106.14.28.97/api/v1/versions"
  ```

### 3. 统计信息功能
- [ ] 统计信息API正常
  ```bash
  curl "http://106.14.28.97/api/v1/stats"
  ```

### 4. 文件上传功能（需要API密钥）
- [ ] 获取API密钥
  ```bash
  grep API_KEY /opt/omega-update-server/.env
  ```
- [ ] 测试文件上传（可选）

## 安全检查

### 1. 访问控制
- [ ] SSH密钥认证工作正常
- [ ] root密码登录已禁用（推荐）
- [ ] 防火墙规则正确配置
- [ ] 不必要的服务已关闭

### 2. 文件安全
- [ ] 敏感文件权限正确（如.env文件）
- [ ] 数据库文件权限正确
- [ ] 日志文件权限正确

### 3. 网络安全
- [ ] 只开放必要端口
- [ ] API密钥已修改为随机值
- [ ] 密钥文件权限正确

## 性能检查

### 1. 响应时间
- [ ] 主页响应时间 < 2秒
- [ ] API响应时间 < 1秒
- [ ] 健康检查响应时间 < 500ms

### 2. 资源使用
- [ ] CPU使用率正常（< 50%）
- [ ] 内存使用率正常（< 80%）
- [ ] 磁盘使用率正常（< 80%）

### 3. 并发处理
- [ ] 多个并发请求处理正常
- [ ] 服务稳定性良好

## 备份和恢复

### 1. 配置备份
- [ ] 环境变量文件已备份
- [ ] Nginx配置文件已备份
- [ ] 服务配置文件已备份

### 2. 数据备份
- [ ] 数据库文件备份计划制定
- [ ] 上传文件备份计划制定

## 监控和维护

### 1. 日志轮转
- [ ] 日志轮转配置正确
- [ ] 旧日志清理策略制定

### 2. 更新策略
- [ ] 应用更新流程制定
- [ ] 系统更新策略制定

### 3. 监控设置
- [ ] 服务状态监控
- [ ] 资源使用监控
- [ ] 错误日志监控

## 文档和培训

### 1. 操作文档
- [ ] 部署文档完整
- [ ] 维护手册准备
- [ ] 故障排除指南准备

### 2. 管理培训
- [ ] 管理员培训完成
- [ ] 操作流程熟悉
- [ ] 应急响应流程制定

---

## 检查完成确认

- [ ] 所有检查项目已完成
- [ ] 部署验证通过
- [ ] 功能测试通过
- [ ] 安全检查通过
- [ ] 性能检查通过
- [ ] 文档准备完整

**部署负责人签名**: _________________ **日期**: _________________

**验收负责人签名**: _________________ **日期**: _________________
