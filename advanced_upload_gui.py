#!/usr/bin/env python3
"""
Omega更新服务器 - 高级上传GUI工具
支持完整包、增量包、热修复包上传和存储管理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import json
import threading
import os
from pathlib import Path
from datetime import datetime
# import hashlib  # 暂未使用

# 禁用所有代理
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

class AdvancedUploadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Omega更新服务器 - 高级上传工具 v2.0")
        self.root.geometry("800x700")
        
        # 配置
        self.config = self.load_config()
        
        # 变量
        self.selected_file = tk.StringVar()
        self.package_type = tk.StringVar(value="full")
        self.version = tk.StringVar()
        self.from_version = tk.StringVar()
        self.description = tk.StringVar()
        self.is_stable = tk.BooleanVar(value=True)
        self.is_critical = tk.BooleanVar(value=False)
        self.platform = tk.StringVar(value="windows")
        self.architecture = tk.StringVar(value="x64")
        
        self.setup_ui()
        self.refresh_storage_stats()
        
    def load_config(self):
        """加载配置"""
        # 优先使用本地配置
        local_config_file = Path("local_server_config.json")
        if local_config_file.exists():
            with open(local_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 其次使用部署配置
        config_file = Path("deployment/server_config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "server": {
                    "ip": "localhost",
                    "domain": "localhost",
                    "port": 8000
                },
                "api": {
                    "key": "dac450db3ec47d79196edb7a34defaed"
                }
            }
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="wens")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Omega更新服务器 - 高级上传工具", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 存储状态框架
        self.setup_storage_frame(main_frame, 1)
        
        # 包类型选择框架
        self.setup_package_type_frame(main_frame, 2)
        
        # 版本信息框架
        self.setup_version_frame(main_frame, 3)
        
        # 文件选择框架
        self.setup_file_frame(main_frame, 4)
        
        # 选项框架
        self.setup_options_frame(main_frame, 5)
        
        # 操作按钮框架
        self.setup_buttons_frame(main_frame, 6)
        
        # 进度和日志框架
        self.setup_progress_frame(main_frame, 7)

    def get_server_url(self):
        """获取完整的服务器URL"""
        server_config = self.config["server"]
        ip = server_config["ip"]
        port = server_config.get("port", 80)  # 默认80端口

        if port == 80:
            return f"http://{ip}"
        else:
            return f"http://{ip}:{port}"

    def setup_storage_frame(self, parent, row):
        """设置存储状态框架"""
        storage_frame = ttk.LabelFrame(parent, text="存储状态", padding="10")
        storage_frame.grid(row=row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        storage_frame.columnconfigure(1, weight=1)
        
        # 存储使用率
        ttk.Label(storage_frame, text="存储使用率:").grid(row=0, column=0, sticky=tk.W)
        self.storage_usage = ttk.Label(storage_frame, text="加载中...", foreground="blue")
        self.storage_usage.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 刷新按钮
        ttk.Button(storage_frame, text="刷新", command=self.refresh_storage_stats).grid(row=0, column=2)
        
        # 进度条
        self.storage_progress = ttk.Progressbar(storage_frame, mode='determinate')
        self.storage_progress.grid(row=1, column=0, columnspan=3, sticky="we", pady=(5, 0))
        
    def setup_package_type_frame(self, parent, row):
        """设置包类型选择框架"""
        type_frame = ttk.LabelFrame(parent, text="包类型", padding="10")
        type_frame.grid(row=row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        
        # 包类型单选按钮
        ttk.Radiobutton(type_frame, text="完整包 (FULL)", variable=self.package_type, 
                       value="full", command=self.on_package_type_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(type_frame, text="增量包 (PATCH)", variable=self.package_type, 
                       value="patch", command=self.on_package_type_change).grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(type_frame, text="热修复包 (HOTFIX)", variable=self.package_type, 
                       value="hotfix", command=self.on_package_type_change).grid(row=0, column=2, sticky=tk.W)
        
        # 包类型说明
        self.type_description = ttk.Label(type_frame, text="完整安装包，适用于全新安装或大版本升级", 
                                         foreground="gray")
        self.type_description.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
    def setup_version_frame(self, parent, row):
        """设置版本信息框架"""
        version_frame = ttk.LabelFrame(parent, text="版本信息", padding="10")
        version_frame.grid(row=row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        version_frame.columnconfigure(1, weight=1)
        version_frame.columnconfigure(3, weight=1)
        
        # 目标版本
        ttk.Label(version_frame, text="目标版本:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(version_frame, textvariable=self.version, width=20).grid(row=0, column=1, sticky="we", padx=(5, 10))
        
        # 源版本（仅增量包）
        self.from_version_label = ttk.Label(version_frame, text="源版本:")
        self.from_version_entry = ttk.Entry(version_frame, textvariable=self.from_version, width=20)
        
        # 平台和架构
        ttk.Label(version_frame, text="平台:").grid(row=1, column=0, sticky=tk.W)
        platform_combo = ttk.Combobox(version_frame, textvariable=self.platform, 
                                     values=["windows", "linux", "macos"], width=15)
        platform_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 10))
        
        ttk.Label(version_frame, text="架构:").grid(row=1, column=2, sticky=tk.W)
        arch_combo = ttk.Combobox(version_frame, textvariable=self.architecture,
                                 values=["x64", "x86", "arm64"], width=15)
        arch_combo.grid(row=1, column=3, sticky=tk.W, padx=(5, 0))
        
        # 描述
        ttk.Label(version_frame, text="描述:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(version_frame, textvariable=self.description, width=50).grid(row=2, column=1, columnspan=3,
                                                                              sticky="we", padx=(5, 0), pady=(5, 0))
        
    def setup_file_frame(self, parent, row):
        """设置文件选择框架"""
        file_frame = ttk.LabelFrame(parent, text="文件选择", padding="10")
        file_frame.grid(row=row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        # 文件路径
        file_path_frame = ttk.Frame(file_frame)
        file_path_frame.grid(row=0, column=0, sticky="we")
        file_path_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_path_frame, textvariable=self.selected_file, state="readonly")
        self.file_entry.grid(row=0, column=0, sticky="we", padx=(0, 10))
        
        ttk.Button(file_path_frame, text="选择文件", command=self.select_file).grid(row=0, column=1)
        
        # 文件信息
        self.file_info = ttk.Label(file_frame, text="", foreground="gray")
        self.file_info.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
    def setup_options_frame(self, parent, row):
        """设置选项框架"""
        options_frame = ttk.LabelFrame(parent, text="选项", padding="10")
        options_frame.grid(row=row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="稳定版本", variable=self.is_stable).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="关键更新", variable=self.is_critical).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
    def setup_buttons_frame(self, parent, row):
        """设置操作按钮框架"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=row, column=0, columnspan=3, pady=(0, 10))
        
        ttk.Button(buttons_frame, text="上传", command=self.upload_package).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(buttons_frame, text="清理存储", command=self.cleanup_storage).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(buttons_frame, text="查看包列表", command=self.view_packages).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(buttons_frame, text="退出", command=self.root.quit).grid(row=0, column=3)
        
    def setup_progress_frame(self, parent, row):
        """设置进度和日志框架"""
        progress_frame = ttk.LabelFrame(parent, text="进度和日志", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=3, sticky="wens", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky="we", pady=(0, 10))
        
        # 日志文本框
        log_frame = ttk.Frame(progress_frame)
        log_frame.grid(row=1, column=0, sticky="wens")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="wens")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
    def on_package_type_change(self):
        """包类型改变事件"""
        pkg_type = self.package_type.get()
        
        descriptions = {
            "full": "完整安装包，适用于全新安装或大版本升级（约8GB）",
            "patch": "增量更新包，仅包含变更文件（通常<500MB）",
            "hotfix": "热修复包，用于紧急bug修复（通常<100MB）"
        }
        
        self.type_description.config(text=descriptions.get(pkg_type, ""))
        
        # 显示/隐藏源版本字段
        if pkg_type == "patch":
            self.from_version_label.grid(row=0, column=2, sticky=tk.W)
            self.from_version_entry.grid(row=0, column=3, sticky="we", padx=(5, 0))
        else:
            self.from_version_label.grid_remove()
            self.from_version_entry.grid_remove()
    
    def select_file(self):
        """选择文件"""
        file_path = filedialog.askopenfilename(
            title="选择更新包文件",
            filetypes=[
                ("压缩文件", "*.zip *.tar.gz"),
                ("可执行文件", "*.exe *.msi"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file.set(file_path)
            self.update_file_info(file_path)
    
    def update_file_info(self, file_path):
        """更新文件信息"""
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            size_gb = file_size / (1024 * 1024 * 1024)
            
            if size_gb >= 1:
                size_text = f"{size_gb:.2f} GB"
            else:
                size_text = f"{size_mb:.2f} MB"
            
            self.file_info.config(text=f"文件大小: {size_text}")
        except Exception as e:
            self.file_info.config(text=f"无法获取文件信息: {e}")
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def refresh_storage_stats(self):
        """刷新存储统计"""
        def fetch_stats():
            try:
                server_url = self.get_server_url()
                self.root.after(0, lambda: self.log_message(f"正在连接: {server_url}/api/v1/storage/stats"))

                # 创建新的session以确保没有代理
                session = requests.Session()
                session.trust_env = False  # 忽略环境变量中的代理设置

                response = session.get(
                    f"{server_url}/api/v1/storage/stats",
                    timeout=10,
                    proxies={}
                )

                if response.status_code == 200:
                    stats = response.json()
                    usage = stats.get("usage_percentage", 0)
                    status = stats.get("status", "unknown")

                    # 更新UI
                    self.root.after(0, lambda: self.update_storage_ui(usage, status))
                    self.root.after(0, lambda: self.log_message(f"存储统计获取成功: {usage:.1f}%"))
                else:
                    self.root.after(0, lambda: self.log_message(f"获取存储统计失败: {response.status_code} - {response.text}"))
            except Exception as e:
                error_msg = f"连接服务器失败: {type(e).__name__}: {e}"
                self.root.after(0, lambda: self.log_message(error_msg))
        
        threading.Thread(target=fetch_stats, daemon=True).start()
    
    def update_storage_ui(self, usage, status):
        """更新存储UI"""
        color_map = {
            "healthy": "green",
            "caution": "orange", 
            "warning": "orange",
            "critical": "red"
        }
        
        color = color_map.get(status, "blue")
        self.storage_usage.config(text=f"{usage:.1f}% ({status})", foreground=color)
        self.storage_progress['value'] = usage

    def upload_package(self):
        """上传包"""
        # 验证输入
        if not self.selected_file.get():
            messagebox.showerror("错误", "请选择要上传的文件")
            return

        if not self.version.get():
            messagebox.showerror("错误", "请输入目标版本")
            return

        if self.package_type.get() == "patch" and not self.from_version.get():
            messagebox.showerror("错误", "增量包必须指定源版本")
            return

        def upload_thread():
            try:
                self.root.after(0, lambda: self.progress_bar.start())
                self.root.after(0, lambda: self.log_message("开始上传..."))

                # 准备上传数据
                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                files = {'file': open(self.selected_file.get(), 'rb')}
                data = {
                    'version': self.version.get(),
                    'package_type': self.package_type.get(),
                    'description': self.description.get(),
                    'is_stable': str(self.is_stable.get()).lower(),
                    'is_critical': str(self.is_critical.get()).lower(),
                    'platform': self.platform.get(),
                    'arch': self.architecture.get(),
                    'api_key': api_key
                }

                if self.package_type.get() == "patch":
                    data['from_version'] = self.from_version.get()

                # 执行上传
                response = requests.post(
                    f"{server_url}/api/v1/upload/package",
                    files=files,
                    data=data,
                    timeout=3600,  # 1小时超时
                    proxies={}
                )

                files['file'].close()

                if response.status_code == 200:
                    result = response.json()
                    self.root.after(0, lambda: self.log_message("上传成功!"))
                    self.root.after(0, lambda: self.log_message(f"包ID: {result.get('package_id')}"))
                    self.root.after(0, lambda: self.log_message(f"SHA256: {result.get('sha256')}"))
                    self.root.after(0, lambda: messagebox.showinfo("成功", "包上传成功!"))
                    self.root.after(0, self.refresh_storage_stats)
                else:
                    error_msg = f"上传失败: {response.status_code}"
                    try:
                        error_detail = response.json().get('detail', '')
                        if error_detail:
                            error_msg += f" - {error_detail}"
                    except:
                        pass
                    self.root.after(0, lambda: self.log_message(error_msg))
                    self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

            except Exception as e:
                error_msg = f"上传失败: {e}"
                self.root.after(0, lambda: self.log_message(error_msg))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.root.after(0, lambda: self.progress_bar.stop())

        threading.Thread(target=upload_thread, daemon=True).start()

    def cleanup_storage(self):
        """清理存储"""
        if not messagebox.askyesno("确认", "确定要执行存储清理吗？这将删除旧的更新包。"):
            return

        def cleanup_thread():
            try:
                self.root.after(0, lambda: self.progress_bar.start())
                self.root.after(0, lambda: self.log_message("开始清理存储..."))

                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                # 创建新的session以确保没有代理
                session = requests.Session()
                session.trust_env = False

                response = session.post(
                    f"{server_url}/api/v1/storage/cleanup",
                    data={'api_key': api_key},
                    timeout=300,
                    proxies={}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        freed_gb = result.get('space_freed', 0) / (1024*1024*1024)
                        self.root.after(0, lambda: self.log_message(f"清理成功! 释放了 {freed_gb:.2f} GB 空间"))
                        self.root.after(0, lambda: self.log_message(f"删除了 {result.get('packages_deleted', 0)} 个包"))
                        self.root.after(0, lambda: messagebox.showinfo("成功", f"清理完成!\n释放空间: {freed_gb:.2f} GB"))
                    else:
                        error_msg = result.get('error', '清理失败')
                        self.root.after(0, lambda: self.log_message(f"清理失败: {error_msg}"))
                        self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
                else:
                    self.root.after(0, lambda: self.log_message(f"清理请求失败: {response.status_code} - {response.text}"))
                    self.root.after(0, lambda: messagebox.showerror("错误", f"清理请求失败: {response.status_code}"))

                self.root.after(0, self.refresh_storage_stats)

            except Exception as e:
                error_msg = f"清理失败: {type(e).__name__}: {e}"
                self.root.after(0, lambda: self.log_message(error_msg))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            finally:
                self.root.after(0, lambda: self.progress_bar.stop())

        threading.Thread(target=cleanup_thread, daemon=True).start()

    def view_packages(self):
        """查看包列表"""
        def fetch_packages():
            try:
                server_url = self.get_server_url()
                response = requests.get(f"{server_url}/api/v1/packages", timeout=30, proxies={})

                if response.status_code == 200:
                    packages = response.json()
                    self.root.after(0, lambda: self.show_packages_window(packages))
                else:
                    self.root.after(0, lambda: messagebox.showerror("错误", f"获取包列表失败: {response.status_code}"))
            except Exception as e:
                error_msg = f"连接服务器失败: {e}"
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

        threading.Thread(target=fetch_packages, daemon=True).start()

    def show_packages_window(self, packages):
        """显示包列表窗口"""
        packages_window = tk.Toplevel(self.root)
        packages_window.title("包列表")
        packages_window.geometry("900x500")

        # 创建表格
        columns = ("ID", "版本", "类型", "大小", "源版本", "创建时间", "下载次数")
        tree = ttk.Treeview(packages_window, columns=columns, show="headings", height=20)

        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # 添加数据
        for pkg in packages:
            size_mb = pkg.get('package_size', 0) / (1024 * 1024)
            tree.insert("", tk.END, values=(
                pkg.get('id', ''),
                pkg.get('version', ''),
                pkg.get('package_type', ''),
                f"{size_mb:.1f} MB",
                pkg.get('from_version', '') or '-',
                pkg.get('created_at', '')[:19] if pkg.get('created_at') else '',
                pkg.get('download_count', 0)
            ))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(packages_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def main():
    """主函数"""
    root = tk.Tk()
    AdvancedUploadGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
