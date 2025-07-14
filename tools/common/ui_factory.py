#!/usr/bin/env python3
"""
GUI组件工厂模块
提供创建GUI组件的工厂方法，支持上传和下载工具的界面构建
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Callable
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import AppConstants


class UIComponentFactory:
    """GUI组件工厂类"""
    
    @staticmethod
    def create_labeled_frame(parent: tk.Widget, text: str, padding: str = "10") -> ttk.LabelFrame:
        """创建带标签的框架"""
        frame = ttk.LabelFrame(parent, text=text, padding=padding)
        return frame
    
    @staticmethod
    def create_entry_with_label(parent: tk.Widget, label_text: str, variable: tk.StringVar, 
                               width: int = 20, row: int = 0, column: int = 0) -> tuple:
        """创建带标签的输入框"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=column, sticky=tk.W)
        
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row, column=column+1, padx=(10, 20), sticky="w")
        
        return label, entry
    
    @staticmethod
    def create_combobox_with_label(parent: tk.Widget, label_text: str, variable: tk.StringVar,
                                  values: list, width: int = 15, row: int = 0, column: int = 0) -> tuple:
        """创建带标签的下拉框"""
        label = ttk.Label(parent, text=label_text)
        label.grid(row=row, column=column, sticky=tk.W)
        
        combobox = ttk.Combobox(parent, textvariable=variable, values=values, width=width)
        combobox.grid(row=row, column=column+1, padx=(10, 20), sticky="w")
        
        return label, combobox
    
    @staticmethod
    def create_button_frame(parent: tk.Widget, buttons_config: list) -> ttk.Frame:
        """
        创建按钮框架
        
        Args:
            parent: 父组件
            buttons_config: 按钮配置列表，每个元素为 (text, command) 元组
        """
        frame = ttk.Frame(parent)
        
        for i, (text, command) in enumerate(buttons_config):
            button = ttk.Button(frame, text=text, command=command)
            button.grid(row=0, column=i, padx=(0, 10) if i < len(buttons_config)-1 else 0)
        
        return frame
    
    @staticmethod
    def create_progress_frame(parent: tk.Widget) -> Dict[str, tk.Widget]:
        """创建进度显示框架"""
        frame = ttk.LabelFrame(parent, text="进度和日志", padding="10")
        
        # 进度条
        progress = ttk.Progressbar(frame, mode='determinate')
        progress.pack(fill=tk.X, pady=(0, 10))
        
        # 状态标签
        status_label = ttk.Label(frame, text="就绪")
        status_label.pack(anchor=tk.W)
        
        # 日志文本框
        log_frame = ttk.Frame(frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)
        
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return {
            'frame': frame,
            'progress': progress,
            'status_label': status_label,
            'log_text': log_text,
            'scrollbar': scrollbar
        }
    
    @staticmethod
    def create_file_tree(parent: tk.Widget, columns: tuple, height: int = 15) -> Dict[str, tk.Widget]:
        """创建文件树形视图"""
        tree = ttk.Treeview(parent, columns=columns, show="tree headings", height=height)
        
        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        return {
            'tree': tree,
            'scrollbar': scrollbar
        }
    
    @staticmethod
    def create_storage_status_frame(parent: tk.Widget) -> Dict[str, tk.Widget]:
        """创建存储状态框架"""
        frame = ttk.LabelFrame(parent, text="存储状态", padding="10")
        
        # 存储使用情况
        storage_label = ttk.Label(frame, text="存储使用情况: 加载中...")
        storage_label.grid(row=0, column=0, sticky="w")
        
        # 刷新按钮
        refresh_button = ttk.Button(frame, text="刷新")
        refresh_button.grid(row=0, column=2)
        
        # 进度条
        storage_progress = ttk.Progressbar(frame, mode='determinate')
        storage_progress.grid(row=1, column=0, columnspan=3, sticky="we", pady=(5, 0))
        
        frame.columnconfigure(0, weight=1)
        
        return {
            'frame': frame,
            'storage_label': storage_label,
            'refresh_button': refresh_button,
            'storage_progress': storage_progress
        }
    
    @staticmethod
    def create_package_type_frame(parent: tk.Widget, variable: tk.StringVar, 
                                 command: Optional[Callable] = None) -> ttk.LabelFrame:
        """创建包类型选择框架"""
        frame = ttk.LabelFrame(parent, text="包类型", padding="10")
        
        for i, (pkg_type, display_name) in enumerate(AppConstants.PACKAGE_TYPE_NAMES.items()):
            radio = ttk.Radiobutton(
                frame, 
                text=display_name, 
                variable=variable, 
                value=pkg_type,
                command=command
            )
            radio.grid(row=0, column=i, padx=(0, 20), sticky="w")
        
        return frame
    
    @staticmethod
    def create_version_info_frame(parent: tk.Widget, variables: Dict[str, tk.StringVar]) -> ttk.LabelFrame:
        """创建版本信息框架"""
        frame = ttk.LabelFrame(parent, text="版本信息", padding="10")
        
        # 版本号
        UIComponentFactory.create_entry_with_label(
            frame, "版本号:", variables['version'], width=20, row=0, column=0
        )
        
        # 平台和架构
        UIComponentFactory.create_combobox_with_label(
            frame, "平台:", variables['platform'], 
            AppConstants.PLATFORMS, width=15, row=0, column=2
        )
        
        UIComponentFactory.create_combobox_with_label(
            frame, "架构:", variables['architecture'],
            AppConstants.ARCHITECTURES, width=15, row=0, column=4
        )
        
        # 描述
        if 'description' in variables:
            ttk.Label(frame, text="描述:").grid(row=1, column=0, sticky="w", pady=(10, 0))
            desc_entry = ttk.Entry(frame, textvariable=variables['description'], width=60)
            desc_entry.grid(row=1, column=1, columnspan=5, padx=(10, 0), pady=(10, 0), sticky="we")
        
        frame.columnconfigure(1, weight=1)
        return frame
    
    @staticmethod
    def create_folder_selection_frame(parent: tk.Widget, variable: tk.StringVar,
                                     select_command: Callable, preview_command: Optional[Callable] = None) -> Dict[str, tk.Widget]:
        """创建文件夹选择框架"""
        frame = ttk.LabelFrame(parent, text="文件夹选择", padding="10")
        
        # 文件夹路径
        folder_path_frame = ttk.Frame(frame)
        folder_path_frame.pack(fill=tk.X)
        
        entry = ttk.Entry(folder_path_frame, textvariable=variable, width=60)
        entry.grid(row=0, column=0, sticky="we")
        
        select_button = ttk.Button(folder_path_frame, text="选择文件夹", command=select_command)
        select_button.grid(row=0, column=1)
        
        preview_button = None
        if preview_command:
            preview_button = ttk.Button(folder_path_frame, text="预览内容", command=preview_command)
            preview_button.grid(row=0, column=2, padx=(5, 0))
        
        # 文件夹信息
        folder_info = ttk.Label(frame, text="", foreground="gray")
        folder_info.pack(anchor=tk.W, pady=(5, 0))
        
        folder_path_frame.columnconfigure(0, weight=1)
        
        return {
            'frame': frame,
            'entry': entry,
            'select_button': select_button,
            'preview_button': preview_button,
            'folder_info': folder_info
        }
    
    @staticmethod
    def create_options_frame(parent: tk.Widget, variables: Dict[str, tk.BooleanVar]) -> ttk.LabelFrame:
        """创建选项框架"""
        frame = ttk.LabelFrame(parent, text="选项", padding="10")
        
        for i, (key, var) in enumerate(variables.items()):
            # 将变量名转换为显示文本
            display_text = {
                'is_stable': '稳定版本',
                'is_critical': '关键更新'
            }.get(key, key)
            
            checkbox = ttk.Checkbutton(frame, text=display_text, variable=var)
            checkbox.pack(side=tk.LEFT, padx=(0, 20) if i < len(variables)-1 else 0)
        
        return frame
    
    @staticmethod
    def create_download_progress_frame(parent: tk.Widget) -> Dict[str, tk.Widget]:
        """创建下载进度框架"""
        frame = ttk.LabelFrame(parent, text="下载进度", padding="10")
        
        # 当前文件
        current_label = ttk.Label(frame, text="当前文件: 无")
        current_label.pack(anchor=tk.W)
        
        # 当前文件进度
        current_progress = ttk.Progressbar(frame, mode='determinate')
        current_progress.pack(fill=tk.X, pady=(5, 0))
        
        # 总体进度
        overall_label = ttk.Label(frame, text="总体进度: 0%")
        overall_label.pack(anchor=tk.W, pady=(10, 0))
        
        overall_progress = ttk.Progressbar(frame, mode='determinate')
        overall_progress.pack(fill=tk.X, pady=(5, 0))
        
        # 统计信息
        stats_frame = ttk.Frame(frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        stats_label = ttk.Label(stats_frame, text="")
        stats_label.pack(anchor=tk.W)
        
        return {
            'frame': frame,
            'current_label': current_label,
            'current_progress': current_progress,
            'overall_label': overall_label,
            'overall_progress': overall_progress,
            'stats_label': stats_label
        }
    
    @staticmethod
    def create_control_buttons_frame(parent: tk.Widget, buttons_config: list) -> Dict[str, tk.Widget]:
        """创建控制按钮框架"""
        frame = ttk.Frame(parent)
        
        buttons = {}
        for i, (key, text, command, state) in enumerate(buttons_config):
            button = ttk.Button(frame, text=text, command=command, state=state)
            button.pack(side=tk.LEFT, padx=(0, 10) if i < len(buttons_config)-1 else 0)
            buttons[key] = button
        
        return {
            'frame': frame,
            **buttons
        }


class NotebookFactory:
    """笔记本组件工厂"""
    
    @staticmethod
    def create_notebook(parent: tk.Widget) -> ttk.Notebook:
        """创建笔记本控件"""
        notebook = ttk.Notebook(parent)
        return notebook
    
    @staticmethod
    def add_tab(notebook: ttk.Notebook, text: str) -> ttk.Frame:
        """添加标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=text)
        return frame


class WindowFactory:
    """窗口工厂"""
    
    @staticmethod
    def create_main_window(title: str, geometry: str) -> tk.Tk:
        """创建主窗口"""
        root = tk.Tk()
        root.title(title)
        root.geometry(geometry)
        return root
    
    @staticmethod
    def create_dialog_window(parent: tk.Widget, title: str, geometry: str, 
                           modal: bool = True) -> tk.Toplevel:
        """创建对话框窗口"""
        window = tk.Toplevel(parent)
        window.title(title)
        window.geometry(geometry)
        window.transient(parent)
        
        if modal:
            window.grab_set()
        
        return window
    
    @staticmethod
    def setup_main_layout(root: tk.Tk) -> ttk.Frame:
        """设置主窗口布局"""
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="wens")
        
        # 配置网格权重
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        return main_frame
