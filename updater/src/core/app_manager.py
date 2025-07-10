#!/usr/bin/env python3
"""
Omega应用程序管理模块
负责管理主应用程序的启动、关闭、版本检测等功能
"""

import os
import time
import subprocess
import psutil
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from .config import config

class ApplicationManager:
    """应用程序管理器"""
    
    def __init__(self):
        self.config = config
        self.app_path = self.config.app_path
        self.app_name = self.config.get("app_executable")
        self.process = None
        self.logger = logging.getLogger(__name__)
    
    def is_app_running(self) -> Tuple[bool, Optional[int]]:
        """
        检查主应用是否正在运行
        
        Returns:
            Tuple[bool, Optional[int]]: (是否运行, 进程ID)
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] == self.app_name:
                        return True, proc_info['pid']
                    
                    # 也检查完整路径匹配
                    if proc_info['exe'] and Path(proc_info['exe']) == self.app_path:
                        return True, proc_info['pid']
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"检查应用运行状态失败: {e}")
            return False, None
    
    def get_running_processes(self) -> List[dict]:
        """获取所有相关的运行进程"""
        processes = []
        app_dir = self.config.get("app_directory")
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['exe'] and app_dir in proc_info['exe']:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'exe': proc_info['exe'],
                            'create_time': proc_info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"获取进程列表失败: {e}")
        
        return processes
    
    def close_app_gracefully(self, timeout: int = 30) -> bool:
        """
        优雅地关闭主应用
        
        Args:
            timeout: 等待超时时间（秒）
            
        Returns:
            bool: 是否成功关闭
        """
        running, pid = self.is_app_running()
        if not running:
            self.logger.info("应用程序未运行")
            return True
        
        try:
            proc = psutil.Process(pid)
            self.logger.info(f"尝试关闭应用程序 (PID: {pid})")
            
            # 首先尝试优雅关闭
            proc.terminate()
            
            # 等待进程结束
            try:
                proc.wait(timeout=timeout)
                self.logger.info("应用程序已优雅关闭")
                return True
            except psutil.TimeoutExpired:
                self.logger.warning(f"优雅关闭超时，强制终止进程")
                proc.kill()
                proc.wait(timeout=5)
                self.logger.info("应用程序已强制关闭")
                return True
                
        except psutil.NoSuchProcess:
            self.logger.info("进程已不存在")
            return True
        except Exception as e:
            self.logger.error(f"关闭应用程序失败: {e}")
            return False
    
    def close_all_related_processes(self) -> bool:
        """关闭所有相关进程"""
        processes = self.get_running_processes()
        
        if not processes:
            self.logger.info("没有发现相关进程")
            return True
        
        success = True
        for proc_info in processes:
            try:
                proc = psutil.Process(proc_info['pid'])
                self.logger.info(f"关闭进程: {proc_info['name']} (PID: {proc_info['pid']})")
                
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.warning(f"无法关闭进程 {proc_info['pid']}: {e}")
                success = False
            except Exception as e:
                self.logger.error(f"关闭进程失败 {proc_info['pid']}: {e}")
                success = False
        
        return success
    
    def start_app(self, wait_for_start: bool = False) -> bool:
        """
        启动主应用
        
        Args:
            wait_for_start: 是否等待应用启动完成
            
        Returns:
            bool: 是否成功启动
        """
        if not self.app_path.exists():
            self.logger.error(f"应用程序不存在: {self.app_path}")
            return False
        
        # 检查是否已经在运行
        running, pid = self.is_app_running()
        if running:
            self.logger.info(f"应用程序已在运行 (PID: {pid})")
            return True
        
        try:
            self.logger.info(f"启动应用程序: {self.app_path}")
            
            # 启动进程
            self.process = subprocess.Popen(
                [str(self.app_path)],
                cwd=str(self.app_path.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            if wait_for_start:
                # 等待应用启动
                for _ in range(30):  # 最多等待30秒
                    time.sleep(1)
                    running, pid = self.is_app_running()
                    if running:
                        self.logger.info(f"应用程序启动成功 (PID: {pid})")
                        return True
                
                self.logger.error("应用程序启动超时")
                return False
            else:
                self.logger.info("应用程序启动命令已执行")
                return True
                
        except Exception as e:
            self.logger.error(f"启动应用程序失败: {e}")
            return False
    
    def restart_app(self) -> bool:
        """重启应用程序"""
        self.logger.info("重启应用程序")
        
        # 关闭应用
        if not self.close_app_gracefully():
            self.logger.error("无法关闭应用程序")
            return False
        
        # 等待一下确保进程完全关闭
        time.sleep(2)
        
        # 启动应用
        return self.start_app(wait_for_start=True)
    
    def get_app_version(self) -> str:
        """获取应用程序版本"""
        version_info = self.config.get_version_info()
        return version_info.get("version", "unknown")
    
    def verify_app_integrity(self) -> bool:
        """验证应用程序完整性"""
        if not self.app_path.exists():
            self.logger.error("主执行文件不存在")
            return False
        
        # 检查文件大小（基本检查）
        try:
            size = self.app_path.stat().st_size
            if size < 1024:  # 小于1KB可能有问题
                self.logger.error(f"主执行文件大小异常: {size} bytes")
                return False
        except Exception as e:
            self.logger.error(f"无法获取文件信息: {e}")
            return False
        
        # 检查关键目录
        app_dir = Path(self.config.get("app_directory"))
        internal_dir = app_dir / "_internal"
        
        if not internal_dir.exists():
            self.logger.error("_internal目录不存在")
            return False
        
        # 检查关键文件
        critical_files = [
            internal_dir / "base_library.zip",
            internal_dir / "python310.dll"
        ]
        
        for file_path in critical_files:
            if not file_path.exists():
                self.logger.warning(f"关键文件缺失: {file_path}")
        
        self.logger.info("应用程序完整性检查通过")
        return True
    
    def create_backup(self, backup_name: str = None) -> Optional[Path]:
        """
        创建应用程序备份
        
        Args:
            backup_name: 备份名称，如果为None则使用时间戳
            
        Returns:
            Optional[Path]: 备份路径，失败时返回None
        """
        if backup_name is None:
            from datetime import datetime
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.config.backup_path / backup_name
        app_dir = Path(self.config.get("app_directory"))
        
        try:
            self.logger.info(f"创建备份: {backup_dir}")
            
            # 确保备份目录存在
            backup_dir.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制应用目录
            import shutil
            shutil.copytree(app_dir, backup_dir, dirs_exist_ok=True)
            
            self.logger.info(f"备份创建成功: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return None
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """
        从备份恢复应用程序
        
        Args:
            backup_path: 备份路径
            
        Returns:
            bool: 是否成功恢复
        """
        if not backup_path.exists():
            self.logger.error(f"备份不存在: {backup_path}")
            return False
        
        app_dir = Path(self.config.get("app_directory"))
        
        try:
            self.logger.info(f"从备份恢复: {backup_path}")
            
            # 关闭应用
            self.close_app_gracefully()
            
            # 删除当前应用目录
            if app_dir.exists():
                import shutil
                shutil.rmtree(app_dir)
            
            # 从备份恢复
            import shutil
            shutil.copytree(backup_path, app_dir)
            
            self.logger.info("从备份恢复成功")
            return True
            
        except Exception as e:
            self.logger.error(f"从备份恢复失败: {e}")
            return False
