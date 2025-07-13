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
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
import hashlib

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
        self.selected_folder = tk.StringVar()
        self.package_type = tk.StringVar(value="full")
        self.version = tk.StringVar()
        self.from_version = tk.StringVar()
        self.description = tk.StringVar()
        self.is_stable = tk.BooleanVar(value=True)
        self.is_critical = tk.BooleanVar(value=False)
        self.platform = tk.StringVar(value="windows")
        self.architecture = tk.StringVar(value="x64")

        # 文件夹分析结果
        self.folder_analysis = None
        
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
        """设置文件夹选择框架"""
        file_frame = ttk.LabelFrame(parent, text="文件夹选择", padding="10")
        file_frame.grid(row=row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)

        # 文件夹路径
        folder_path_frame = ttk.Frame(file_frame)
        folder_path_frame.grid(row=0, column=0, sticky="we")
        folder_path_frame.columnconfigure(0, weight=1)

        self.folder_entry = ttk.Entry(folder_path_frame, textvariable=self.selected_folder, state="readonly")
        self.folder_entry.grid(row=0, column=0, sticky="we", padx=(0, 10))

        ttk.Button(folder_path_frame, text="选择文件夹", command=self.select_folder).grid(row=0, column=1)
        ttk.Button(folder_path_frame, text="预览内容", command=self.preview_folder).grid(row=0, column=2, padx=(5, 0))

        # 文件夹信息
        self.folder_info = ttk.Label(file_frame, text="", foreground="gray")
        self.folder_info.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # 冲突处理选项
        conflict_frame = ttk.LabelFrame(file_frame, text="文件冲突处理", padding="5")
        conflict_frame.grid(row=2, column=0, sticky="we", pady=(10, 0))

        self.conflict_action = tk.StringVar(value="skip")
        ttk.Radiobutton(conflict_frame, text="跳过已存在的文件", variable=self.conflict_action, value="skip").pack(anchor=tk.W)
        ttk.Radiobutton(conflict_frame, text="覆盖已存在的文件", variable=self.conflict_action, value="overwrite").pack(anchor=tk.W)
        ttk.Radiobutton(conflict_frame, text="询问每个冲突文件", variable=self.conflict_action, value="ask").pack(anchor=tk.W)
        
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
        ttk.Button(buttons_frame, text="存储管理", command=self.show_storage_management).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(buttons_frame, text="退出", command=self.root.quit).grid(row=0, column=4)
        
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
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = filedialog.askdirectory(
            title="选择要上传的文件夹"
        )

        if folder_path:
            self.selected_folder.set(folder_path)
            self.analyze_folder(folder_path)

    def analyze_folder(self, folder_path):
        """分析文件夹内容"""
        try:
            folder_path = Path(folder_path)
            if not folder_path.exists() or not folder_path.is_dir():
                self.folder_info.config(text="无效的文件夹路径")
                return

            # 分析文件夹内容
            total_size = 0
            file_count = 0
            file_types = {}

            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    file_count += 1

                    # 统计文件类型
                    ext = file_path.suffix.lower()
                    if ext:
                        file_types[ext] = file_types.get(ext, 0) + 1
                    else:
                        file_types['无扩展名'] = file_types.get('无扩展名', 0) + 1

            # 保存分析结果
            self.folder_analysis = {
                'path': str(folder_path),
                'total_size': total_size,
                'file_count': file_count,
                'file_types': file_types
            }

            # 显示信息
            size_mb = total_size / (1024 * 1024)
            size_gb = total_size / (1024 * 1024 * 1024)

            if size_gb >= 1:
                size_text = f"{size_gb:.2f} GB"
            else:
                size_text = f"{size_mb:.2f} MB"

            info_text = f"文件夹: {file_count} 个文件, {size_text}"
            self.folder_info.config(text=info_text)

        except Exception as e:
            self.folder_info.config(text=f"分析文件夹失败: {e}")
            self.folder_analysis = None

    def preview_folder(self):
        """预览文件夹内容"""
        if not self.folder_analysis:
            messagebox.showwarning("警告", "请先选择文件夹")
            return

        # 创建预览窗口
        preview_window = tk.Toplevel(self.root)
        preview_window.title("文件夹内容预览")
        preview_window.geometry("600x500")

        # 基本信息
        info_frame = ttk.LabelFrame(preview_window, text="基本信息", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(info_frame, text=f"路径: {self.folder_analysis['path']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"文件数量: {self.folder_analysis['file_count']}").pack(anchor=tk.W)

        size_mb = self.folder_analysis['total_size'] / (1024 * 1024)
        ttk.Label(info_frame, text=f"总大小: {size_mb:.2f} MB").pack(anchor=tk.W)

        # 文件类型统计
        types_frame = ttk.LabelFrame(preview_window, text="文件类型统计", padding="10")
        types_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建表格
        columns = ("文件类型", "数量")
        tree = ttk.Treeview(types_frame, columns=columns, show="headings", height=15)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # 添加数据
        for file_type, count in sorted(self.folder_analysis['file_types'].items()):
            tree.insert("", tk.END, values=(file_type, count))

        # 添加滚动条
        scrollbar = ttk.Scrollbar(types_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
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

    def create_zip_from_folder(self, folder_path, progress_callback=None):
        """将文件夹压缩为zip文件"""
        try:
            folder_path = Path(folder_path)

            # 创建临时zip文件
            temp_dir = Path(tempfile.gettempdir())
            zip_filename = f"omega-{self.version.get()}-{self.package_type.get()}-{self.platform.get()}-{self.architecture.get()}.zip"
            zip_path = temp_dir / zip_filename

            # 获取所有文件
            all_files = list(folder_path.rglob('*'))
            file_files = [f for f in all_files if f.is_file()]
            total_files = len(file_files)

            if progress_callback:
                progress_callback(0, total_files, "开始压缩...")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                for i, file_path in enumerate(file_files):
                    # 计算相对路径
                    relative_path = file_path.relative_to(folder_path)

                    # 添加文件到zip
                    zipf.write(file_path, relative_path)

                    if progress_callback:
                        progress_callback(i + 1, total_files, f"压缩: {relative_path}")

            if progress_callback:
                progress_callback(total_files, total_files, "压缩完成")

            return str(zip_path)

        except Exception as e:
            raise Exception(f"压缩文件夹失败: {e}")

    def upload_package(self):
        """上传文件夹（逐个文件上传）"""
        # 验证输入
        if not self.selected_folder.get():
            messagebox.showerror("错误", "请选择要上传的文件夹")
            return

        if not self.version.get():
            messagebox.showerror("错误", "请输入目标版本")
            return

        if not self.folder_analysis:
            messagebox.showerror("错误", "请先分析文件夹内容")
            return

        # 创建进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("文件上传进度")
        progress_window.geometry("600x400")
        progress_window.transient(self.root)
        progress_window.grab_set()

        # 进度框架
        progress_frame = ttk.Frame(progress_window, padding="20")
        progress_frame.pack(fill=tk.BOTH, expand=True)

        # 总体进度
        ttk.Label(progress_frame, text="总体进度:").pack(anchor=tk.W)
        overall_progress_var = tk.DoubleVar()
        overall_progress_bar = ttk.Progressbar(progress_frame, variable=overall_progress_var, maximum=100)
        overall_progress_bar.pack(fill=tk.X, pady=(5, 10))

        # 当前文件进度
        ttk.Label(progress_frame, text="当前文件:").pack(anchor=tk.W)
        current_file_label = ttk.Label(progress_frame, text="准备中...", foreground="blue")
        current_file_label.pack(anchor=tk.W, pady=(0, 10))

        # 统计信息
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行统计
        stats_row1 = ttk.Frame(stats_frame)
        stats_row1.pack(fill=tk.X)

        uploaded_label = ttk.Label(stats_row1, text="已上传: 0")
        uploaded_label.pack(side=tk.LEFT)

        skipped_label = ttk.Label(stats_row1, text="跳过: 0")
        skipped_label.pack(side=tk.LEFT, padx=(20, 0))

        failed_label = ttk.Label(stats_row1, text="失败: 0")
        failed_label.pack(side=tk.LEFT, padx=(20, 0))

        # 第二行统计（速度和时间）
        stats_row2 = ttk.Frame(stats_frame)
        stats_row2.pack(fill=tk.X, pady=(5, 0))

        speed_label = ttk.Label(stats_row2, text="上传速度: 0 KB/s")
        speed_label.pack(side=tk.LEFT)

        eta_label = ttk.Label(stats_row2, text="剩余时间: --")
        eta_label.pack(side=tk.LEFT, padx=(20, 0))

        total_size_label = ttk.Label(stats_row2, text="总大小: 0 MB")
        total_size_label.pack(side=tk.LEFT, padx=(20, 0))

        # 详细日志
        ttk.Label(progress_frame, text="详细日志:").pack(anchor=tk.W)
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scrollbar.set)

        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 控制按钮
        button_frame = ttk.Frame(progress_frame)
        button_frame.pack(fill=tk.X)

        cancel_var = tk.BooleanVar()
        cancel_button = ttk.Button(button_frame, text="取消",
                                  command=lambda: cancel_var.set(True))
        cancel_button.pack(side=tk.LEFT)

        pause_var = tk.BooleanVar()
        pause_button = ttk.Button(button_frame, text="暂停",
                                 command=lambda: pause_var.set(not pause_var.get()))
        pause_button.pack(side=tk.LEFT, padx=(10, 0))

        close_button = ttk.Button(button_frame, text="关闭",
                                 command=progress_window.destroy, state=tk.DISABLED)
        close_button.pack(side=tk.RIGHT)

        def log_to_window(message, level="INFO"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {level}: {message}\n"
            log_text.insert(tk.END, log_message)
            log_text.see(tk.END)
            progress_window.update()

        def upload_files_thread():
            try:
                folder_path = Path(self.selected_folder.get())
                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                # 获取所有文件
                all_files = []
                total_size = 0
                for file_path in folder_path.rglob('*'):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(folder_path)
                        file_size = file_path.stat().st_size
                        all_files.append((file_path, str(relative_path).replace('\\', '/'), file_size))
                        total_size += file_size

                total_files = len(all_files)
                uploaded_count = 0
                skipped_count = 0
                failed_count = 0
                uploaded_size = 0
                start_time = datetime.now()

                # 更新总大小显示
                total_size_mb = total_size / (1024 * 1024)
                total_size_label.config(text=f"总大小: {total_size_mb:.1f} MB")

                log_to_window(f"开始上传 {total_files} 个文件到版本 {self.version.get()}")
                log_to_window(f"总大小: {total_size_mb:.1f} MB")

                for i, (file_path, relative_path, file_size) in enumerate(all_files):
                    if cancel_var.get():
                        log_to_window("用户取消上传", "WARN")
                        break

                    # 检查暂停状态
                    while pause_var.get() and not cancel_var.get():
                        pause_button.config(text="继续")
                        current_file_label.config(text="已暂停...")
                        progress_window.update()
                        import time
                        time.sleep(0.1)  # 等待100ms

                    if not pause_var.get():
                        pause_button.config(text="暂停")

                    # 更新进度
                    progress = (i / total_files) * 100
                    overall_progress_var.set(progress)
                    current_file_label.config(text=f"正在上传: {relative_path}")

                    try:
                        # 计算文件哈希
                        file_hash = hashlib.sha256()
                        with open(file_path, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                file_hash.update(chunk)
                        file_hash_str = file_hash.hexdigest()

                        # 上传文件
                        with open(file_path, 'rb') as f:
                            files = {'file': f}
                            data = {
                                'version': self.version.get(),
                                'platform': self.platform.get(),
                                'arch': self.architecture.get(),
                                'relative_path': relative_path,
                                'file_hash': file_hash_str,
                                'conflict_action': self.conflict_action.get(),
                                'api_key': api_key
                            }

                            response = requests.post(
                                f"{server_url}/api/v1/upload/file",
                                files=files,
                                data=data,
                                timeout=300,  # 5分钟超时
                                proxies={}
                            )

                        if response.status_code == 200:
                            result = response.json()
                            action = result.get('action', 'uploaded')

                            if action == 'skipped':
                                skipped_count += 1
                                reason = result.get('message', '文件已存在')
                                log_to_window(f"跳过: {relative_path} ({reason})")
                            elif action == 'conflict':
                                # 处理文件冲突
                                conflict_info = result.get('conflict_info', {})
                                existing_size = conflict_info.get('existing_size', 0)

                                conflict_msg = f"文件冲突: {relative_path}\n"
                                conflict_msg += f"本地文件: {file_size} 字节\n"
                                conflict_msg += f"服务器文件: {existing_size} 字节\n"
                                conflict_msg += "是否覆盖服务器上的文件？"

                                # 询问用户
                                user_choice = messagebox.askyesno("文件冲突", conflict_msg)

                                if user_choice:
                                    # 用户选择覆盖，重新上传
                                    data['conflict_action'] = 'overwrite'
                                    with open(file_path, 'rb') as f:
                                        files = {'file': f}
                                        retry_response = requests.post(
                                            f"{server_url}/api/v1/upload/file",
                                            files=files,
                                            data=data,
                                            timeout=300,
                                            proxies={}
                                        )

                                    if retry_response.status_code == 200:
                                        uploaded_count += 1
                                        uploaded_size += file_size
                                        file_size_kb = file_size / 1024
                                        log_to_window(f"覆盖: {relative_path} ({file_size_kb:.1f} KB)")
                                    else:
                                        failed_count += 1
                                        log_to_window(f"覆盖失败: {relative_path}", "ERROR")
                                else:
                                    # 用户选择跳过
                                    skipped_count += 1
                                    log_to_window(f"用户跳过: {relative_path}")
                            else:
                                uploaded_count += 1
                                uploaded_size += file_size
                                file_size_kb = file_size / 1024
                                log_to_window(f"上传: {relative_path} ({file_size_kb:.1f} KB)")
                        else:
                            failed_count += 1
                            error_msg = f"HTTP {response.status_code}"
                            try:
                                error_detail = response.json().get('detail', '')
                                if error_detail:
                                    error_msg = error_detail
                            except:
                                pass
                            log_to_window(f"失败: {relative_path} - {error_msg}", "ERROR")

                    except Exception as e:
                        failed_count += 1
                        log_to_window(f"失败: {relative_path} - {str(e)}", "ERROR")

                    # 计算速度和剩余时间
                    elapsed_time = (datetime.now() - start_time).total_seconds()
                    if elapsed_time > 0 and uploaded_size > 0:
                        speed_bps = uploaded_size / elapsed_time
                        speed_kbps = speed_bps / 1024

                        # 估算剩余时间
                        remaining_size = total_size - uploaded_size
                        if speed_bps > 0:
                            eta_seconds = remaining_size / speed_bps
                            eta_minutes = eta_seconds / 60
                            if eta_minutes < 1:
                                eta_text = f"{eta_seconds:.0f}秒"
                            elif eta_minutes < 60:
                                eta_text = f"{eta_minutes:.1f}分钟"
                            else:
                                eta_hours = eta_minutes / 60
                                eta_text = f"{eta_hours:.1f}小时"
                        else:
                            eta_text = "--"

                        speed_label.config(text=f"上传速度: {speed_kbps:.1f} KB/s")
                        eta_label.config(text=f"剩余时间: {eta_text}")

                    # 更新统计
                    uploaded_label.config(text=f"已上传: {uploaded_count}")
                    skipped_label.config(text=f"跳过: {skipped_count}")
                    failed_label.config(text=f"失败: {failed_count}")

                # 完成
                overall_progress_var.set(100)
                current_file_label.config(text="上传完成!")

                if not cancel_var.get():
                    log_to_window(f"上传完成! 总计: {total_files}, 成功: {uploaded_count}, 跳过: {skipped_count}, 失败: {failed_count}")

                    if failed_count == 0:
                        self.root.after(0, lambda: messagebox.showinfo("成功", f"文件夹上传完成!\n成功: {uploaded_count}, 跳过: {skipped_count}"))
                        self.root.after(0, self.refresh_storage_stats)
                    else:
                        self.root.after(0, lambda: messagebox.showwarning("部分失败", f"上传完成，但有 {failed_count} 个文件失败"))

                # 启用关闭按钮
                cancel_button.config(state=tk.DISABLED)
                close_button.config(state=tk.NORMAL)

            except Exception as e:
                log_to_window(f"上传过程发生错误: {str(e)}", "ERROR")
                self.root.after(0, lambda: messagebox.showerror("错误", f"上传失败: {str(e)}"))
                cancel_button.config(state=tk.DISABLED)
                close_button.config(state=tk.NORMAL)

        # 启动上传线程
        threading.Thread(target=upload_files_thread, daemon=True).start()

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

    def show_storage_management(self):
        """显示存储管理窗口"""
        storage_window = tk.Toplevel(self.root)
        storage_window.title("存储管理")
        storage_window.geometry("1000x700")

        # 创建笔记本控件
        notebook = ttk.Notebook(storage_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 存储结构标签页
        structure_frame = ttk.Frame(notebook)
        notebook.add(structure_frame, text="存储结构")
        self.setup_storage_structure_tab(structure_frame)

        # 版本管理标签页
        version_frame = ttk.Frame(notebook)
        notebook.add(version_frame, text="版本管理")
        self.setup_version_management_tab(version_frame)

        # 文件验证标签页
        verify_frame = ttk.Frame(notebook)
        notebook.add(verify_frame, text="文件验证")
        self.setup_file_verification_tab(verify_frame)

    def setup_storage_structure_tab(self, parent):
        """设置存储结构标签页"""
        # 刷新按钮
        refresh_btn = ttk.Button(parent, text="刷新存储结构", command=lambda: self.load_storage_structure(parent))
        refresh_btn.pack(pady=10)

        # 创建树形视图
        self.structure_tree = ttk.Treeview(parent, height=25)
        self.structure_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加滚动条
        structure_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.structure_tree.yview)
        self.structure_tree.configure(yscrollcommand=structure_scrollbar.set)
        structure_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 加载初始数据
        self.load_storage_structure(parent)

    def load_storage_structure(self, parent):
        """加载存储结构"""
        def fetch_structure():
            try:
                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                response = requests.get(
                    f"{server_url}/api/v1/storage/structure",
                    params={'api_key': api_key},
                    timeout=30,
                    proxies={}
                )

                if response.status_code == 200:
                    structure = response.json()
                    self.root.after(0, lambda: self.update_structure_tree(structure))
                else:
                    error_msg = f"获取存储结构失败: {response.status_code}"
                    self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

            except Exception as e:
                error_msg = f"连接服务器失败: {e}"
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

        threading.Thread(target=fetch_structure, daemon=True).start()

    def update_structure_tree(self, structure):
        """更新存储结构树"""
        # 清空现有内容
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)

        # 添加根节点
        root_node = self.structure_tree.insert("", tk.END, text=f"存储根目录 ({structure.get('base_path', '')})")

        # 添加统计信息
        total_files = structure.get('total_files', 0)
        total_size_gb = structure.get('total_size', 0) / (1024*1024*1024)
        stats_node = self.structure_tree.insert(root_node, tk.END,
                                               text=f"总计: {total_files} 个文件, {total_size_gb:.2f} GB")

        # 添加目录信息
        directories = structure.get('directories', {})
        for dir_name, dir_info in directories.items():
            dir_size_mb = dir_info.get('total_size', 0) / (1024*1024)
            dir_node = self.structure_tree.insert(root_node, tk.END,
                                                 text=f"{dir_name} ({dir_info.get('file_count', 0)} 文件, {dir_size_mb:.1f} MB)")

            # 添加版本信息
            versions = dir_info.get('versions', [])
            for version in versions:
                version_size_mb = version.get('size', 0) / (1024*1024)
                version_node = self.structure_tree.insert(dir_node, tk.END,
                                                         text=f"版本 {version.get('version', '')} ({len(version.get('files', []))} 文件, {version_size_mb:.1f} MB)")

                # 添加文件信息
                files = version.get('files', [])
                for file_info in files:
                    file_size_mb = file_info.get('size', 0) / (1024*1024)
                    file_text = f"{file_info.get('name', '')} ({file_size_mb:.1f} MB)"
                    if file_info.get('package_type'):
                        file_text += f" [{file_info.get('package_type')}]"
                    self.structure_tree.insert(version_node, tk.END, text=file_text)

        # 展开根节点
        self.structure_tree.item(root_node, open=True)

    def setup_version_management_tab(self, parent):
        """设置版本管理标签页"""
        # 版本保留策略配置
        config_frame = ttk.LabelFrame(parent, text="版本保留策略配置", padding="10")
        config_frame.pack(fill=tk.X, padx=10, pady=10)

        # 完整包保留数量
        ttk.Label(config_frame, text="完整包保留数量:").grid(row=0, column=0, sticky=tk.W)
        self.full_retention = tk.StringVar(value="2")
        ttk.Entry(config_frame, textvariable=self.full_retention, width=10).grid(row=0, column=1, padx=5)

        # 增量包保留数量
        ttk.Label(config_frame, text="增量包保留数量:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.patch_retention = tk.StringVar(value="5")
        ttk.Entry(config_frame, textvariable=self.patch_retention, width=10).grid(row=0, column=3, padx=5)

        # 热修复包保留数量
        ttk.Label(config_frame, text="热修复包保留数量:").grid(row=0, column=4, sticky=tk.W, padx=(20, 0))
        self.hotfix_retention = tk.StringVar(value="10")
        ttk.Entry(config_frame, textvariable=self.hotfix_retention, width=10).grid(row=0, column=5, padx=5)

        # 操作按钮
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(pady=10)

        ttk.Button(buttons_frame, text="应用保留策略", command=self.apply_retention_policy).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="配置策略", command=self.configure_retention_policy).pack(side=tk.LEFT, padx=5)

        # 结果显示区域
        result_frame = ttk.LabelFrame(parent, text="操作结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.version_result_text = tk.Text(result_frame, height=15, wrap=tk.WORD)
        version_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.version_result_text.yview)
        self.version_result_text.configure(yscrollcommand=version_scrollbar.set)

        self.version_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        version_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def apply_retention_policy(self):
        """应用版本保留策略"""
        def apply_policy():
            try:
                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                response = requests.post(
                    f"{server_url}/api/v1/storage/retention/apply",
                    data={'api_key': api_key},
                    timeout=300,
                    proxies={}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        cleaned_count = len(result.get('cleaned_packages', []))
                        space_freed_gb = result.get('space_freed', 0) / (1024*1024*1024)

                        result_text = f"版本保留策略应用成功!\n"
                        result_text += f"清理了 {cleaned_count} 个包\n"
                        result_text += f"释放空间: {space_freed_gb:.2f} GB\n\n"
                        result_text += "清理详情:\n"

                        for pkg in result.get('cleaned_packages', []):
                            result_text += f"- {pkg.get('package_name')} (版本: {pkg.get('version')}, 大小: {pkg.get('size', 0)/(1024*1024):.1f} MB)\n"

                        self.root.after(0, lambda: self.version_result_text.insert(tk.END, result_text))
                        self.root.after(0, lambda: messagebox.showinfo("成功", f"清理完成!\n清理了 {cleaned_count} 个包\n释放空间: {space_freed_gb:.2f} GB"))
                    else:
                        error_msg = result.get('error', '应用策略失败')
                        self.root.after(0, lambda: self.version_result_text.insert(tk.END, f"错误: {error_msg}\n"))
                        self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
                else:
                    error_msg = f"请求失败: {response.status_code}"
                    self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

            except Exception as e:
                error_msg = f"应用保留策略失败: {e}"
                self.root.after(0, lambda: self.version_result_text.insert(tk.END, f"错误: {error_msg}\n"))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

        threading.Thread(target=apply_policy, daemon=True).start()

    def configure_retention_policy(self):
        """配置版本保留策略"""
        def configure_policy():
            try:
                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                # 配置各种包类型的保留策略
                policies = [
                    ("full", int(self.full_retention.get())),
                    ("patch", int(self.patch_retention.get())),
                    ("hotfix", int(self.hotfix_retention.get()))
                ]

                results = []
                for package_type, max_versions in policies:
                    response = requests.post(
                        f"{server_url}/api/v1/storage/retention/configure",
                        data={
                            'package_type': package_type,
                            'max_versions': max_versions,
                            'api_key': api_key
                        },
                        timeout=30,
                        proxies={}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            results.append(f"{package_type}: {result.get('old_max_versions')} -> {result.get('new_max_versions')}")
                        else:
                            results.append(f"{package_type}: 配置失败 - {result.get('error')}")
                    else:
                        results.append(f"{package_type}: 请求失败 - {response.status_code}")

                result_text = "版本保留策略配置结果:\n" + "\n".join(results) + "\n\n"
                self.root.after(0, lambda: self.version_result_text.insert(tk.END, result_text))
                self.root.after(0, lambda: messagebox.showinfo("完成", "版本保留策略配置完成"))

            except ValueError:
                error_msg = "请输入有效的数字"
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            except Exception as e:
                error_msg = f"配置保留策略失败: {e}"
                self.root.after(0, lambda: self.version_result_text.insert(tk.END, f"错误: {error_msg}\n"))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

        threading.Thread(target=configure_policy, daemon=True).start()

    def setup_file_verification_tab(self, parent):
        """设置文件验证标签页"""
        # 文件路径输入
        path_frame = ttk.LabelFrame(parent, text="文件验证", padding="10")
        path_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(path_frame, text="文件路径:").grid(row=0, column=0, sticky=tk.W)
        self.verify_file_path = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.verify_file_path, width=50).grid(row=0, column=1, sticky="we", padx=5)

        ttk.Label(path_frame, text="期望哈希:").grid(row=1, column=0, sticky=tk.W)
        self.expected_hash = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.expected_hash, width=50).grid(row=1, column=1, sticky="we", padx=5, pady=5)

        path_frame.columnconfigure(1, weight=1)

        # 验证按钮
        ttk.Button(path_frame, text="验证文件", command=self.verify_file).grid(row=2, column=0, columnspan=2, pady=10)

        # 结果显示
        result_frame = ttk.LabelFrame(parent, text="验证结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.verify_result_text = tk.Text(result_frame, height=20, wrap=tk.WORD)
        verify_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.verify_result_text.yview)
        self.verify_result_text.configure(yscrollcommand=verify_scrollbar.set)

        self.verify_result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        verify_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def verify_file(self):
        """验证文件完整性"""
        file_path = self.verify_file_path.get().strip()
        expected_hash = self.expected_hash.get().strip()

        if not file_path or not expected_hash:
            messagebox.showerror("错误", "请输入文件路径和期望哈希值")
            return

        def verify_thread():
            try:
                server_url = self.get_server_url()
                api_key = self.config["api"]["key"]

                response = requests.post(
                    f"{server_url}/api/v1/file/verify",
                    data={
                        'file_path': file_path,
                        'expected_hash': expected_hash,
                        'api_key': api_key
                    },
                    timeout=60,
                    proxies={}
                )

                if response.status_code == 200:
                    result = response.json()

                    result_text = f"文件验证结果:\n"
                    result_text += f"文件路径: {result.get('file_path', '')}\n"
                    result_text += f"文件大小: {result.get('file_size', 0)} 字节\n"
                    result_text += f"期望哈希: {result.get('expected_hash', '')}\n"
                    result_text += f"实际哈希: {result.get('actual_hash', '')}\n"
                    result_text += f"验证结果: {'通过' if result.get('valid') else '失败'}\n"

                    if not result.get('valid') and result.get('error'):
                        result_text += f"错误信息: {result.get('error')}\n"

                    result_text += "\n" + "="*50 + "\n\n"

                    self.root.after(0, lambda: self.verify_result_text.insert(tk.END, result_text))

                    if result.get('valid'):
                        self.root.after(0, lambda: messagebox.showinfo("成功", "文件验证通过"))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("失败", "文件验证失败"))
                else:
                    error_msg = f"验证请求失败: {response.status_code}"
                    self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

            except Exception as e:
                error_msg = f"文件验证失败: {e}"
                self.root.after(0, lambda: self.verify_result_text.insert(tk.END, f"错误: {error_msg}\n"))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))

        threading.Thread(target=verify_thread, daemon=True).start()

def main():
    """主函数"""
    root = tk.Tk()
    AdvancedUploadGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
