#!/usr/bin/env python3
"""
Omega更新包管理GUI工具
提供可视化界面来管理更新包的上传、查看和管理
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import os
import threading
from datetime import datetime
import hashlib
import subprocess
import sys
import shutil
import zipfile
import io
import mimetypes

class OmegaUpdateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Omega更新包管理工具")
        self.root.geometry("800x600")

        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(__file__), "gui_config.json")

        # 默认配置
        self.default_config = {
            "server_url": "http://update.chpyke.cn",
            "api_key": "dac450db3ec47d79196edb7a34defaed",
            "old_version_path": "",
            "new_version_path": "",
            "output_path": "updates",
            "package_prefix": "omega",
            "package_type": "both",  # incremental, full, both
            "auto_upload": True,
            "high_compression": True,
            "analyze_differences": True,
            "stream_upload": True  # 启用流式上传
        }

        # 加载配置
        self.load_config()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()
        self.load_versions()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 服务器配置区域
        config_frame = ttk.LabelFrame(main_frame, text="服务器配置", padding="5")
        config_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="服务器地址:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.server_entry = ttk.Entry(config_frame, width=50)
        self.server_entry.insert(0, self.server_url)
        self.server_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))

        ttk.Label(config_frame, text="API密钥:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.api_key_entry = ttk.Entry(config_frame, width=50, show="*")
        self.api_key_entry.insert(0, self.api_key)
        self.api_key_entry.grid(row=1, column=1, sticky="ew", padx=(0, 5))
        
        ttk.Button(config_frame, text="测试连接", command=self.test_connection).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(config_frame, text="显示/隐藏密钥", command=self.toggle_api_key).grid(row=1, column=2, padx=(5, 0))
        ttk.Button(config_frame, text="重置配置", command=self.reset_config).grid(row=0, column=3, padx=(5, 0))
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        main_frame.rowconfigure(1, weight=1)

        # 更新包制作标签页
        self.package_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.package_frame, text="制作更新包")
        self.setup_package_tab()

        # 上传标签页
        self.upload_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.upload_frame, text="上传更新包")
        self.setup_upload_tab()

        # 版本管理标签页
        self.versions_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.versions_frame, text="版本管理")
        self.setup_versions_tab()

        # 日志标签页
        self.log_frame = ttk.Frame(notebook, padding="10")
        notebook.add(self.log_frame, text="操作日志")
        self.setup_log_tab()

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    
    def setup_upload_tab(self):
        """设置上传标签页"""
        # 文件选择
        file_frame = ttk.LabelFrame(self.upload_frame, text="选择文件", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="更新包文件:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(file_frame, text="浏览", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))

        # 版本信息
        info_frame = ttk.LabelFrame(self.upload_frame, text="版本信息", padding="5")
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="版本号:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.version_entry = ttk.Entry(info_frame, width=20)
        self.version_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(info_frame, text="平台:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.platform_combo = ttk.Combobox(info_frame, values=["windows", "linux", "macos"], state="readonly", width=10)
        self.platform_combo.set("windows")
        self.platform_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(info_frame, text="架构:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.arch_combo = ttk.Combobox(info_frame, values=["x64", "x86", "arm64"], state="readonly", width=10)
        self.arch_combo.set("x64")
        self.arch_combo.grid(row=0, column=5, sticky=tk.W)
        
        ttk.Label(info_frame, text="描述:").grid(row=1, column=0, sticky="wn", padx=(0, 5), pady=(5, 0))
        self.description_text = tk.Text(info_frame, height=3, width=50)
        self.description_text.grid(row=1, column=1, columnspan=5, sticky="ew", padx=(0, 0), pady=(5, 0))

        # 选项
        options_frame = ttk.LabelFrame(self.upload_frame, text="选项", padding="5")
        options_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.is_stable_var = tk.BooleanVar(value=True)
        self.is_critical_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(options_frame, text="稳定版本", variable=self.is_stable_var).grid(row=0, column=0, sticky="w", padx=(0, 20))
        ttk.Checkbutton(options_frame, text="重要更新", variable=self.is_critical_var).grid(row=0, column=1, sticky="w")

        # 上传按钮和进度条
        upload_frame = ttk.Frame(self.upload_frame)
        upload_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        upload_frame.columnconfigure(0, weight=1)

        self.upload_button = ttk.Button(upload_frame, text="上传更新包", command=self.upload_version)
        self.upload_button.grid(row=0, column=0, pady=(0, 5))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(upload_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
    
    def setup_versions_tab(self):
        """设置版本管理标签页"""
        # 版本列表
        list_frame = ttk.LabelFrame(self.versions_frame, text="版本列表", padding="5")
        list_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        self.versions_frame.columnconfigure(0, weight=1)
        self.versions_frame.rowconfigure(0, weight=1)

        # 创建Treeview
        columns = ("版本", "平台", "架构", "大小", "状态", "发布时间")
        self.versions_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.versions_tree.heading(col, text=col)
            self.versions_tree.column(col, width=100)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.versions_tree.yview)
        self.versions_tree.configure(yscrollcommand=scrollbar.set)

        self.versions_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 按钮框架
        button_frame = ttk.Frame(self.versions_frame)
        button_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(button_frame, text="刷新列表", command=self.load_versions).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="查看详情", command=self.view_version_details).grid(row=0, column=1, padx=(5, 5))
        ttk.Button(button_frame, text="下载链接", command=self.copy_download_link).grid(row=0, column=2, padx=(5, 0))
    
    def setup_log_tab(self):
        """设置日志标签页"""
        log_frame = ttk.LabelFrame(self.log_frame, text="操作日志", padding="5")
        log_frame.grid(row=0, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_frame.columnconfigure(0, weight=1)
        self.log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # 清除日志按钮
        ttk.Button(self.log_frame, text="清除日志", command=self.clear_log).grid(row=1, column=0, pady=(10, 0))

    def setup_package_tab(self):
        """设置更新包制作标签页"""
        # 版本目录选择
        dirs_frame = ttk.LabelFrame(self.package_frame, text="版本目录选择", padding="5")
        dirs_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        dirs_frame.columnconfigure(1, weight=1)

        # 旧版本目录
        ttk.Label(dirs_frame, text="旧版本目录:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.old_version_var = tk.StringVar()
        self.old_version_var.set(self.config.get("old_version_path", ""))
        self.old_version_entry = ttk.Entry(dirs_frame, textvariable=self.old_version_var, state="readonly")
        self.old_version_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(dirs_frame, text="浏览", command=self.browse_old_version).grid(row=0, column=2, padx=(5, 0))

        # 新版本目录
        ttk.Label(dirs_frame, text="新版本目录:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.new_version_var = tk.StringVar()
        self.new_version_var.set(self.config.get("new_version_path", ""))
        self.new_version_entry = ttk.Entry(dirs_frame, textvariable=self.new_version_var, state="readonly")
        self.new_version_entry.grid(row=1, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(dirs_frame, text="浏览", command=self.browse_new_version).grid(row=1, column=2, padx=(5, 0))

        # 输出设置
        output_frame = ttk.LabelFrame(self.package_frame, text="输出设置", padding="5")
        output_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="输出目录:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.output_dir_var = tk.StringVar()
        self.output_dir_var.set(self.config.get("output_path", "updates"))
        self.output_dir_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var)
        self.output_dir_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_dir).grid(row=0, column=2, padx=(5, 0))

        ttk.Label(output_frame, text="包名前缀:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.package_prefix_var = tk.StringVar()
        self.package_prefix_var.set(self.config.get("package_prefix", "omega"))
        self.package_prefix_entry = ttk.Entry(output_frame, textvariable=self.package_prefix_var)
        self.package_prefix_entry.grid(row=1, column=1, sticky="ew", padx=(0, 5))

        # 更新包类型选择
        type_frame = ttk.LabelFrame(self.package_frame, text="更新包类型", padding="5")
        type_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.package_type_var = tk.StringVar(value=self.config.get("package_type", "both"))
        ttk.Radiobutton(type_frame, text="仅增量包", variable=self.package_type_var, value="incremental").grid(row=0, column=0, sticky="w", padx=(0, 20))
        ttk.Radiobutton(type_frame, text="仅完整包", variable=self.package_type_var, value="full").grid(row=0, column=1, sticky="w", padx=(0, 20))
        ttk.Radiobutton(type_frame, text="两种都制作", variable=self.package_type_var, value="both").grid(row=0, column=2, sticky="w")

        # 高级选项
        advanced_frame = ttk.LabelFrame(self.package_frame, text="高级选项", padding="5")
        advanced_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.auto_upload_var = tk.BooleanVar(value=self.config.get("auto_upload", True))
        self.compress_var = tk.BooleanVar(value=self.config.get("high_compression", True))
        self.analyze_first_var = tk.BooleanVar(value=self.config.get("analyze_differences", True))
        self.stream_upload_var = tk.BooleanVar(value=self.config.get("stream_upload", True))

        ttk.Checkbutton(advanced_frame, text="制作完成后自动上传", variable=self.auto_upload_var).grid(row=0, column=0, sticky="w", padx=(0, 20))
        ttk.Checkbutton(advanced_frame, text="高压缩率", variable=self.compress_var).grid(row=0, column=1, sticky="w", padx=(0, 20))
        ttk.Checkbutton(advanced_frame, text="先分析版本差异", variable=self.analyze_first_var).grid(row=0, column=2, sticky="w")
        ttk.Checkbutton(advanced_frame, text="流式上传(推荐)", variable=self.stream_upload_var).grid(row=1, column=0, sticky="w", padx=(0, 20))

        # 操作按钮
        button_frame = ttk.Frame(self.package_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)

        buttons_container = ttk.Frame(button_frame)
        buttons_container.grid(row=0, column=0)

        ttk.Button(buttons_container, text="分析版本差异", command=self.analyze_versions).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(buttons_container, text="制作更新包", command=self.create_update_packages).grid(row=0, column=1, padx=(5, 5))
        ttk.Button(buttons_container, text="一键制作并上传", command=self.create_and_upload).grid(row=0, column=2, padx=(5, 5))
        ttk.Button(buttons_container, text="上传完整包", command=self.upload_full_package).grid(row=0, column=3, padx=(5, 0))

        # 进度显示
        progress_frame = ttk.Frame(self.package_frame)
        progress_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.package_progress_var = tk.DoubleVar()
        self.package_progress_bar = ttk.Progressbar(progress_frame, variable=self.package_progress_var, maximum=100)
        self.package_progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.package_status_var = tk.StringVar()
        self.package_status_var.set("就绪")
        ttk.Label(progress_frame, textvariable=self.package_status_var).grid(row=1, column=0)

        # 绑定事件以自动保存配置
        self.setup_config_bindings()

    def setup_config_bindings(self):
        """设置配置自动保存的事件绑定"""
        # 绑定输入框的修改事件
        self.package_prefix_var.trace_add('write', lambda *args: self.save_config())
        self.output_dir_var.trace_add('write', lambda *args: self.save_config())
        self.package_type_var.trace_add('write', lambda *args: self.save_config())
        self.auto_upload_var.trace_add('write', lambda *args: self.save_config())
        self.compress_var.trace_add('write', lambda *args: self.save_config())
        self.analyze_first_var.trace_add('write', lambda *args: self.save_config())
        self.stream_upload_var.trace_add('write', lambda *args: self.save_config())

    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)

    def browse_old_version(self):
        """浏览选择旧版本目录"""
        directory = filedialog.askdirectory(title="选择旧版本目录")
        if directory:
            self.old_version_var.set(directory)
            self.save_config()

    def browse_new_version(self):
        """浏览选择新版本目录"""
        directory = filedialog.askdirectory(title="选择新版本目录")
        if directory:
            self.new_version_var.set(directory)
            self.save_config()

    def browse_output_dir(self):
        """浏览选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)
            self.save_config()

    def analyze_versions(self):
        """分析版本差异"""
        old_version = self.old_version_var.get()
        new_version = self.new_version_var.get()

        if not old_version or not new_version:
            messagebox.showerror("错误", "请选择旧版本和新版本目录")
            return

        if not os.path.exists(old_version) or not os.path.exists(new_version):
            messagebox.showerror("错误", "选择的目录不存在")
            return

        self.package_status_var.set("分析版本差异中...")
        self.package_progress_var.set(10)

        def analyze():
            try:
                # 调用版本分析工具
                script_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(script_dir)
                analyzer_script = os.path.join(parent_dir, "version_analyzer.py")

                if not os.path.exists(analyzer_script):
                    raise FileNotFoundError("找不到版本分析工具")

                # 生成分析报告
                report_file = os.path.join(self.output_dir_var.get(), "version_analysis_report.txt")
                os.makedirs(os.path.dirname(report_file), exist_ok=True)

                cmd = [
                    sys.executable, analyzer_script,
                    "--old-version", old_version,
                    "--new-version", new_version,
                    "--output-report", report_file
                ]

                self.log_message(f"执行命令: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=parent_dir)

                self.package_progress_var.set(80)

                if result.returncode == 0:
                    self.log_message("版本分析完成")
                    self.package_progress_var.set(100)
                    self.package_status_var.set("分析完成")

                    # 显示分析结果
                    if os.path.exists(report_file):
                        with open(report_file, 'r', encoding='utf-8') as f:
                            report_content = f.read()

                        # 创建新窗口显示报告
                        self.show_analysis_report(report_content)

                    messagebox.showinfo("完成", f"版本分析完成！\n报告已保存到: {report_file}")
                else:
                    error_msg = result.stderr or result.stdout or "未知错误"
                    self.log_message(f"版本分析失败: {error_msg}")
                    self.package_status_var.set("分析失败")
                    messagebox.showerror("错误", f"版本分析失败: {error_msg}")

            except Exception as e:
                self.log_message(f"版本分析异常: {e}")
                self.package_status_var.set("分析失败")
                messagebox.showerror("错误", f"版本分析异常: {e}")
            finally:
                self.package_progress_var.set(0)

        threading.Thread(target=analyze, daemon=True).start()

    def show_analysis_report(self, content):
        """显示分析报告"""
        report_window = tk.Toplevel(self.root)
        report_window.title("版本分析报告")
        report_window.geometry("800x600")

        text_widget = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(report_window, text="关闭", command=report_window.destroy).pack(pady=10)

    def create_update_packages(self):
        """制作更新包"""
        old_version = self.old_version_var.get()
        new_version = self.new_version_var.get()
        output_dir = self.output_dir_var.get()
        package_prefix = self.package_prefix_var.get()
        package_type = self.package_type_var.get()

        if not new_version:
            messagebox.showerror("错误", "请选择新版本目录")
            return

        if not os.path.exists(new_version):
            messagebox.showerror("错误", "新版本目录不存在")
            return

        if package_type in ["incremental", "both"] and (not old_version or not os.path.exists(old_version)):
            messagebox.showerror("错误", "制作增量包需要选择有效的旧版本目录")
            return

        self.package_status_var.set("制作更新包中...")
        self.package_progress_var.set(10)

        def create_packages():
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                generator_script = os.path.join(script_dir, "simple_package_maker.py")

                if not os.path.exists(generator_script):
                    raise FileNotFoundError(f"找不到更新包生成工具: {generator_script}")

                os.makedirs(output_dir, exist_ok=True)
                created_packages = []

                # 制作增量包
                if package_type in ["incremental", "both"]:
                    self.log_message("制作增量更新包...")
                    self.package_status_var.set("制作增量包...")

                    incremental_name = f"{package_prefix}_incremental_{os.path.basename(old_version)}_to_{os.path.basename(new_version)}"
                    package_file = os.path.join(output_dir, f"{incremental_name}.zip")

                    cmd = [
                        sys.executable, generator_script,
                        "incremental",
                        old_version,
                        new_version,
                        package_file
                    ]

                    self.log_message(f"执行命令: {' '.join(cmd)}")
                    self.log_message(f"工作目录: {script_dir}")

                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

                    self.log_message(f"命令返回码: {result.returncode}")
                    if result.stdout:
                        self.log_message(f"标准输出: {result.stdout}")
                    if result.stderr:
                        self.log_message(f"错误输出: {result.stderr}")

                    if result.returncode == 0:
                        if os.path.exists(package_file):
                            created_packages.append(("incremental", package_file))
                            size_mb = os.path.getsize(package_file) / 1024 / 1024
                            self.log_message(f"增量包制作完成: {package_file} ({size_mb:.1f} MB)")
                        else:
                            self.log_message(f"增量包制作完成，但找不到输出文件: {package_file}")
                            # 检查输出目录中的所有文件
                            if os.path.exists(output_dir):
                                files = os.listdir(output_dir)
                                self.log_message(f"输出目录中的文件: {files}")
                    else:
                        error_msg = result.stderr or result.stdout or "未知错误"
                        self.log_message(f"增量包制作失败: {error_msg}")
                        # 继续尝试制作完整包

                self.package_progress_var.set(50)

                # 制作完整包
                if package_type in ["full", "both"]:
                    self.log_message("制作完整更新包...")
                    self.package_status_var.set("制作完整包...")

                    full_name = f"{package_prefix}_full_{os.path.basename(new_version)}"
                    package_file = os.path.join(output_dir, f"{full_name}.zip")

                    cmd = [
                        sys.executable, generator_script,
                        "full",
                        new_version,
                        package_file
                    ]

                    self.log_message(f"执行命令: {' '.join(cmd)}")
                    result = subprocess.run(cmd, capture_output=True, text=True, cwd=script_dir)

                    self.log_message(f"命令返回码: {result.returncode}")
                    if result.stdout:
                        self.log_message(f"标准输出: {result.stdout}")
                    if result.stderr:
                        self.log_message(f"错误输出: {result.stderr}")

                    if result.returncode == 0:
                        if os.path.exists(package_file):
                            created_packages.append(("full", package_file))
                            size_mb = os.path.getsize(package_file) / 1024 / 1024
                            self.log_message(f"完整包制作完成: {package_file} ({size_mb:.1f} MB)")
                        else:
                            self.log_message(f"完整包制作完成，但找不到输出文件: {package_file}")
                    else:
                        error_msg = result.stderr or result.stdout or "未知错误"
                        self.log_message(f"完整包制作失败: {error_msg}")

                self.package_progress_var.set(90)

                if created_packages:
                    self.package_status_var.set("制作完成")
                    self.package_progress_var.set(100)

                    # 显示制作结果
                    result_msg = "更新包制作完成！\n\n"
                    for pkg_type, pkg_file in created_packages:
                        size_mb = os.path.getsize(pkg_file) / 1024 / 1024
                        result_msg += f"{pkg_type}包: {os.path.basename(pkg_file)} ({size_mb:.1f} MB)\n"

                    self.log_message("所有更新包制作完成")

                    # 如果启用自动上传，询问是否上传
                    if self.auto_upload_var.get():
                        if messagebox.askyesno("自动上传", f"{result_msg}\n是否立即上传这些更新包？"):
                            self.upload_created_packages(created_packages)
                    else:
                        messagebox.showinfo("完成", result_msg)
                else:
                    self.package_status_var.set("制作失败")
                    messagebox.showerror("错误", "没有成功制作任何更新包")

            except Exception as e:
                self.log_message(f"制作更新包异常: {e}")
                self.package_status_var.set("制作失败")
                messagebox.showerror("错误", f"制作更新包异常: {e}")
            finally:
                self.package_progress_var.set(0)

        threading.Thread(target=create_packages, daemon=True).start()

    def upload_created_packages(self, packages):
        """上传制作好的更新包"""
        for _, pkg_file in packages:
            try:
                # 从文件名推断版本信息
                filename = os.path.basename(pkg_file)
                if "incremental" in filename:
                    # 增量包版本号处理
                    parts = filename.replace(".zip", "").split("_")
                    if len(parts) >= 4:
                        version = f"{parts[-1]}-patch"
                        description = f"增量更新包 - 从{parts[-3]}升级到{parts[-1]}"
                    else:
                        version = "unknown-patch"
                        description = "增量更新包"
                elif "full" in filename:
                    # 完整包版本号处理
                    parts = filename.replace(".zip", "").split("_")
                    if len(parts) >= 3:
                        version = parts[-1]
                        description = f"完整安装包 - 版本{parts[-1]}"
                    else:
                        version = "unknown"
                        description = "完整安装包"
                else:
                    version = "unknown"
                    description = "更新包"

                # 设置文件路径到上传界面
                self.file_path_var.set(pkg_file)
                self.version_entry.delete(0, tk.END)
                self.version_entry.insert(0, version)
                self.description_text.delete(1.0, tk.END)
                self.description_text.insert(1.0, description)

                # 设置为稳定版本
                self.is_stable_var.set(True)
                self.is_critical_var.set(False)

                self.log_message(f"准备上传: {filename}")

                # 自动上传
                self.upload_version()

            except Exception as e:
                self.log_message(f"上传 {pkg_file} 失败: {e}")

    def create_and_upload(self):
        """一键制作并上传"""
        # 先分析版本差异（如果启用）
        if self.analyze_first_var.get():
            old_version = self.old_version_var.get()
            new_version = self.new_version_var.get()

            if old_version and new_version and os.path.exists(old_version) and os.path.exists(new_version):
                # 显示确认对话框
                if messagebox.askyesno("确认", "是否先分析版本差异？\n\n点击'是'查看分析报告后再制作\n点击'否'直接制作更新包"):
                    self.analyze_versions()
                    return

        # 直接制作更新包
        self.create_update_packages()

    def upload_full_package(self):
        """上传完整包"""
        new_version_path = self.new_version_var.get()
        output_dir = self.output_dir_var.get()
        package_prefix = self.package_prefix_var.get()

        if not new_version_path:
            messagebox.showerror("错误", "请先选择新版本目录")
            return

        if not os.path.exists(new_version_path):
            messagebox.showerror("错误", "新版本目录不存在")
            return

        # 获取版本号
        version_name = os.path.basename(new_version_path)
        if version_name.startswith(package_prefix + "_"):
            version_number = version_name[len(package_prefix + "_"):]
        else:
            version_number = version_name

        # 构建完整包文件名
        full_package_name = f"{package_prefix}_full_{version_number}.zip"
        full_package_path = os.path.join(output_dir, full_package_name)

        # 检查完整包是否存在
        if not os.path.exists(full_package_path):
            # 如果不存在，询问是否先制作完整包
            result = messagebox.askyesno(
                "完整包不存在",
                f"完整包文件不存在: {full_package_name}\n\n是否先制作完整包？"
            )
            if result:
                self.log_message("开始制作完整包...")
                try:
                    self.create_full_package(new_version_path, output_dir, package_prefix, version_number)

                    # 检查制作是否成功
                    if not os.path.exists(full_package_path):
                        messagebox.showerror("错误", "完整包制作失败")
                        return
                except Exception as e:
                    messagebox.showerror("错误", f"完整包制作失败: {e}")
                    return
            else:
                return

        # 上传完整包
        self.log_message(f"准备上传完整包: {full_package_name}")
        self.upload_package_file(full_package_path, version_number, "完整更新包")

    def create_full_package(self, source_dir, output_dir, package_prefix, version_number):
        """制作完整包"""
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)

            # 完整包文件路径
            full_package_path = os.path.join(output_dir, f"{package_prefix}_full_{version_number}.zip")

            self.log_message(f"开始制作完整包: {os.path.basename(full_package_path)}")

            # 创建ZIP文件
            with zipfile.ZipFile(full_package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arc_name)

            # 获取文件大小
            file_size = os.path.getsize(full_package_path)
            file_size_mb = file_size / 1024 / 1024

            self.log_message(f"完整包制作完成: {os.path.basename(full_package_path)} ({file_size_mb:.1f} MB)")

        except Exception as e:
            self.log_message(f"制作完整包失败: {e}")
            raise

    def upload_package_file(self, file_path, version, description):
        """上传指定的包文件"""
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在: {file_path}")
            return

        # 设置文件路径到上传界面
        self.file_path_var.set(file_path)
        self.version_entry.delete(0, tk.END)
        self.version_entry.insert(0, version)
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(1.0, description)

        # 询问是否立即上传
        result = messagebox.askyesno(
            "确认上传",
            f"文件: {os.path.basename(file_path)}\n版本: {version}\n描述: {description}\n\n是否立即上传？"
        )

        if result:
            self.upload_version()

    def toggle_api_key(self):
        """切换API密钥显示/隐藏"""
        if self.api_key_entry.cget("show") == "*":
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def test_connection(self):
        """测试服务器连接"""
        self.status_var.set("测试连接中...")
        self.log_message("测试服务器连接...")
        
        def test():
            try:
                server_url = self.server_entry.get().strip()
                proxies = {'http': '', 'https': ''}
                response = requests.get(f"{server_url}/health", timeout=10, proxies=proxies)
                response.raise_for_status()
                
                result = response.json()
                self.log_message(f"连接成功: {result}")
                self.status_var.set("连接测试成功")
                messagebox.showinfo("连接测试", "服务器连接正常！")
                # 连接成功后保存配置
                self.save_config()
            except Exception as e:
                self.log_message(f"连接失败: {e}")
                self.status_var.set("连接测试失败")
                messagebox.showerror("连接测试", f"连接失败: {e}")
        
        threading.Thread(target=test, daemon=True).start()
    
    def browse_file(self):
        """浏览选择文件"""
        file_path = filedialog.askopenfilename(
            title="选择更新包文件",
            filetypes=[
                ("压缩文件", "*.zip *.tar.gz *.rar"),
                ("可执行文件", "*.exe *.msi"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.file_path_var.set(file_path)
            # 自动填充版本号（从文件名推测）
            filename = os.path.basename(file_path)
            if not self.version_entry.get():
                # 尝试从文件名提取版本号
                import re
                version_match = re.search(r'(\d+\.\d+\.\d+)', filename)
                if version_match:
                    self.version_entry.insert(0, version_match.group(1))
    
    def upload_version(self):
        """上传版本"""
        # 验证输入
        file_path = self.file_path_var.get()
        version = self.version_entry.get().strip()
        
        if not file_path:
            messagebox.showerror("错误", "请选择要上传的文件")
            return
        
        if not version:
            messagebox.showerror("错误", "请输入版本号")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("错误", "选择的文件不存在")
            return
        
        # 禁用上传按钮
        self.upload_button.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("准备上传...")
        
        def upload():
            try:
                server_url = self.server_entry.get().strip()
                api_key = self.api_key_entry.get().strip()
                description = self.description_text.get(1.0, tk.END).strip()
                
                self.log_message(f"开始上传版本 {version}")
                self.log_message(f"文件: {file_path}")
                
                # 计算文件大小
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / 1024 / 1024
                self.log_message(f"文件大小: {file_size_mb:.1f} MB")

                # 检查文件大小限制
                max_size_mb = 200  # 服务器限制200MB
                if file_size_mb > max_size_mb:
                    self.log_message(f"警告: 文件大小 {file_size_mb:.1f} MB 超过服务器限制 {max_size_mb} MB")
                    if not messagebox.askyesno("文件过大",
                        f"文件大小 {file_size_mb:.1f} MB 超过服务器限制 {max_size_mb} MB\n\n"
                        "建议:\n"
                        "1. 重新制作更新包，排除不必要的文件\n"
                        "2. 使用增量包而不是完整包\n"
                        "3. 分割大文件\n\n"
                        "是否仍要尝试上传？"):
                        self.log_message("用户取消上传")
                        return
                
                self.progress_var.set(10)
                self.status_var.set("上传中...")

                # 准备上传数据
                data = {
                    'version': version,
                    'description': description,
                    'is_stable': self.is_stable_var.get(),
                    'is_critical': self.is_critical_var.get(),
                    'platform': self.platform_combo.get(),
                    'arch': self.arch_combo.get(),
                    'api_key': api_key
                }

                # 检查是否启用流式上传
                use_stream_upload = self.stream_upload_var.get()
                self.log_message(f"上传方式: {'流式上传' if use_stream_upload else '传统上传'}")

                if use_stream_upload:
                    # 使用流式上传
                    def progress_callback(uploaded, total):
                        progress = (uploaded / total) * 90 + 10  # 10-100%
                        self.progress_var.set(progress)
                        self.status_var.set(f"上传中... {uploaded / 1024 / 1024:.1f}/{total / 1024 / 1024:.1f} MB")

                    result = self.stream_upload_file(file_path, server_url, data, progress_callback)
                    self.progress_var.set(100)
                else:
                    # 使用传统上传
                    with open(file_path, 'rb') as f:
                        files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}

                        self.progress_var.set(30)

                        # 上传文件（禁用代理）
                        proxies = {'http': '', 'https': ''}

                        response = requests.post(
                            f"{server_url}/api/v1/upload/version",
                            files=files,
                            data=data,
                            timeout=600,  # 10分钟超时
                            proxies=proxies
                        )

                        self.progress_var.set(90)
                        response.raise_for_status()
                        result = response.json()
                        self.progress_var.set(100)
                    
                    self.log_message(f"上传成功: {result}")
                    self.status_var.set("上传完成")
                    messagebox.showinfo("上传成功", f"版本 {version} 上传成功！")
                    
                    # 刷新版本列表
                    self.load_versions()
                    
            except Exception as e:
                self.log_message(f"上传失败: {e}")
                self.status_var.set("上传失败")
                messagebox.showerror("上传失败", f"上传失败: {e}")
            finally:
                self.upload_button.config(state="normal")
                self.progress_var.set(0)
        
        threading.Thread(target=upload, daemon=True).start()
    
    def load_versions(self):
        """加载版本列表"""
        def load():
            try:
                server_url = self.server_entry.get().strip()
                proxies = {'http': '', 'https': ''}
                response = requests.get(f"{server_url}/api/v1/versions", timeout=10, proxies=proxies)
                response.raise_for_status()
                
                versions = response.json()
                
                # 清空现有数据
                for item in self.versions_tree.get_children():
                    self.versions_tree.delete(item)
                
                # 添加版本数据
                for version in versions:
                    status = []
                    if version.get('is_stable'):
                        status.append("稳定")
                    if version.get('is_critical'):
                        status.append("重要")
                    status_text = ",".join(status) if status else "开发"
                    
                    size_mb = version.get('file_size', 0) / 1024 / 1024 if version.get('file_size') else 0
                    
                    self.versions_tree.insert("", tk.END, values=(
                        version.get('version', ''),
                        version.get('platform', 'windows'),
                        version.get('architecture', 'x64'),
                        f"{size_mb:.1f} MB",
                        status_text,
                        version.get('release_date', '')[:19] if version.get('release_date') else ''
                    ))
                
                self.log_message(f"加载了 {len(versions)} 个版本")
                
            except Exception as e:
                self.log_message(f"加载版本列表失败: {e}")
                messagebox.showerror("错误", f"加载版本列表失败: {e}")
        
        threading.Thread(target=load, daemon=True).start()
    
    def view_version_details(self):
        """查看版本详情"""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个版本")
            return
        
        item = self.versions_tree.item(selection[0])
        values = item['values']
        
        details = f"""版本详情:
版本号: {values[0]}
平台: {values[1]}
架构: {values[2]}
文件大小: {values[3]}
状态: {values[4]}
发布时间: {values[5]}"""
        
        messagebox.showinfo("版本详情", details)
    
    def copy_download_link(self):
        """复制下载链接"""
        selection = self.versions_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个版本")
            return
        
        server_url = self.server_entry.get().strip()

        # 这里需要版本ID，实际应用中需要从API获取
        download_url = f"{server_url}/api/v1/version/check?current_version=0.0.0"
        
        self.root.clipboard_clear()
        self.root.clipboard_append(download_url)
        messagebox.showinfo("提示", f"下载链接已复制到剪贴板:\n{download_url}")

    def stream_upload_file(self, file_path, server_url, data, progress_callback=None):
        """流式上传文件 - 内存友好的大文件上传方案"""
        try:
            file_size = os.path.getsize(file_path)
            self.log_message(f"开始流式上传: {os.path.basename(file_path)} ({file_size / 1024 / 1024:.1f} MB)")

            # 使用简化的流式上传方案
            class FileWithProgress:
                def __init__(self, file_path, progress_callback=None, logger=None):
                    self.file_path = file_path
                    self.progress_callback = progress_callback
                    self.logger = logger
                    self.file_size = os.path.getsize(file_path)
                    self.uploaded = 0
                    self._file = None
                    self._is_open = False

                def __enter__(self):
                    try:
                        self._file = open(self.file_path, 'rb')
                        self._is_open = True
                        return self
                    except Exception as e:
                        if self.logger:
                            self.logger(f"打开文件失败: {e}")
                        raise

                def __exit__(self, exc_type, exc_val, exc_tb):
                    self.close()

                def close(self):
                    """安全关闭文件"""
                    if self._file and self._is_open:
                        try:
                            self._file.close()
                        except Exception:
                            pass  # 忽略关闭时的错误
                        finally:
                            self._is_open = False
                            self._file = None

                def read(self, size=-1):
                    """读取文件数据并更新进度"""
                    if not self._file or not self._is_open:
                        raise ValueError("文件未打开或已关闭")

                    try:
                        chunk = self._file.read(size)
                        if chunk:
                            self.uploaded += len(chunk)
                            if self.progress_callback:
                                self.progress_callback(self.uploaded, self.file_size)
                        return chunk
                    except Exception as e:
                        if self.logger:
                            self.logger(f"读取文件失败: {e}")
                        raise

                def __len__(self):
                    return self.file_size

            # 创建进度回调
            def update_progress(uploaded, total):
                if progress_callback:
                    progress_callback(uploaded, total)

            # 使用文件包装器进行上传
            with FileWithProgress(file_path, update_progress, self.log_message) as file_wrapper:
                files = {'file': (os.path.basename(file_path), file_wrapper, 'application/octet-stream')}

                proxies = {'http': '', 'https': ''}

                response = requests.post(
                    f"{server_url}/api/v1/upload/version",
                    files=files,
                    data=data,
                    timeout=1800,  # 30分钟超时
                    proxies=proxies
                )

                response.raise_for_status()
                return response.json()

        except Exception as e:
            self.log_message(f"流式上传失败: {e}")
            raise

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)

                # 合并默认配置和保存的配置
                self.config = self.default_config.copy()
                self.config.update(saved_config)

                # 设置属性以保持向后兼容
                self.server_url = self.config["server_url"]
                self.api_key = self.config["api_key"]

                if hasattr(self, 'log_text'):
                    self.log_message(f"配置已加载: {self.config_file}")
            else:
                # 使用默认配置
                self.config = self.default_config.copy()
                self.server_url = self.config["server_url"]
                self.api_key = self.config["api_key"]
                if hasattr(self, 'log_text'):
                    self.log_message("使用默认配置")
        except Exception as e:
            if hasattr(self, 'log_text'):
                self.log_message(f"加载配置失败: {e}")
            # 使用默认配置
            self.config = self.default_config.copy()
            self.server_url = self.config["server_url"]
            self.api_key = self.config["api_key"]

    def save_config(self):
        """保存当前配置"""
        try:
            # 更新配置
            if hasattr(self, 'server_entry'):
                self.config["server_url"] = self.server_entry.get()
            if hasattr(self, 'api_key_entry'):
                self.config["api_key"] = self.api_key_entry.get()
            if hasattr(self, 'old_version_entry'):
                self.config["old_version_path"] = self.old_version_entry.get()
            if hasattr(self, 'new_version_entry'):
                self.config["new_version_path"] = self.new_version_entry.get()
            if hasattr(self, 'output_dir_var'):
                self.config["output_path"] = self.output_dir_var.get()
            if hasattr(self, 'package_prefix_var'):
                self.config["package_prefix"] = self.package_prefix_var.get()
            if hasattr(self, 'package_type_var'):
                self.config["package_type"] = self.package_type_var.get()
            if hasattr(self, 'auto_upload_var'):
                self.config["auto_upload"] = self.auto_upload_var.get()
            if hasattr(self, 'compress_var'):
                self.config["high_compression"] = self.compress_var.get()
            if hasattr(self, 'analyze_first_var'):
                self.config["analyze_differences"] = self.analyze_first_var.get()
            if hasattr(self, 'stream_upload_var'):
                self.config["stream_upload"] = self.stream_upload_var.get()

            # 保存到文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            if hasattr(self, 'log_text'):
                self.log_message("配置已保存")
        except Exception as e:
            if hasattr(self, 'log_text'):
                self.log_message(f"保存配置失败: {e}")

    def reset_config(self):
        """重置配置为默认值"""
        result = messagebox.askyesno("重置配置", "确定要重置所有配置为默认值吗？")
        if result:
            # 删除配置文件
            if os.path.exists(self.config_file):
                os.remove(self.config_file)

            # 重新加载默认配置
            self.config = self.default_config.copy()
            self.server_url = self.config["server_url"]
            self.api_key = self.config["api_key"]

            # 更新UI
            self.server_entry.delete(0, tk.END)
            self.server_entry.insert(0, self.config["server_url"])
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.insert(0, self.config["api_key"])

            self.old_version_var.set(self.config["old_version_path"])
            self.new_version_var.set(self.config["new_version_path"])
            self.output_dir_var.set(self.config["output_path"])
            self.package_prefix_var.set(self.config["package_prefix"])
            self.package_type_var.set(self.config["package_type"])
            self.auto_upload_var.set(self.config["auto_upload"])
            self.compress_var.set(self.config["high_compression"])
            self.analyze_first_var.set(self.config["analyze_differences"])
            self.stream_upload_var.set(self.config["stream_upload"])

            if hasattr(self, 'log_text'):
                self.log_message("配置已重置为默认值")

    def on_closing(self):
        """窗口关闭时的处理"""
        self.save_config()
        self.root.destroy()

def main():
    root = tk.Tk()
    OmegaUpdateGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
