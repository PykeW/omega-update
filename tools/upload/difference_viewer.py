#!/usr/bin/env python3
"""
差异查看器
显示文件差异报告的GUI组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.upload.incremental_uploader import DifferenceReport, ChangeType, FileInfo
from tools.common.common_utils import FileUtils


class DifferenceViewerWindow:
    """差异查看器窗口"""
    
    def __init__(self, parent: tk.Tk, report: DifferenceReport, 
                 on_confirm: Optional[Callable] = None,
                 on_cancel: Optional[Callable] = None):
        self.parent = parent
        self.report = report
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.result = False
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("文件差异报告")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        self.window.transient(parent)
        self.window.grab_set()
        
        # 居中显示
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.window.winfo_screenheight() // 2) - (600 // 2)
        self.window.geometry(f"800x600+{x}+{y}")
        
        self.create_widgets()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📊 文件差异分析报告", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 摘要信息
        self.create_summary_section(main_frame)
        
        # 详细信息
        self.create_details_section(main_frame)
        
        # 操作按钮
        self.create_buttons_section(main_frame)
    
    def create_summary_section(self, parent):
        """创建摘要信息区域"""
        summary_frame = ttk.LabelFrame(parent, text="📋 摘要信息", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建摘要网格
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X)
        
        # 配置列权重
        for i in range(4):
            summary_grid.columnconfigure(i, weight=1)
        
        # 新增文件
        new_frame = ttk.Frame(summary_grid)
        new_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(new_frame, text="🆕 新增文件", font=("Arial", 10, "bold")).pack()
        ttk.Label(new_frame, text=str(len(self.report.new_files)), 
                 font=("Arial", 12), foreground="green").pack()
        
        # 修改文件
        modified_frame = ttk.Frame(summary_grid)
        modified_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(modified_frame, text="📝 修改文件", font=("Arial", 10, "bold")).pack()
        ttk.Label(modified_frame, text=str(len(self.report.modified_files)), 
                 font=("Arial", 12), foreground="orange").pack()
        
        # 删除文件
        deleted_frame = ttk.Frame(summary_grid)
        deleted_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(deleted_frame, text="🗑️ 删除文件", font=("Arial", 10, "bold")).pack()
        ttk.Label(deleted_frame, text=str(len(self.report.deleted_files)), 
                 font=("Arial", 12), foreground="red").pack()
        
        # 相同文件
        same_frame = ttk.Frame(summary_grid)
        same_frame.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W+tk.E)
        ttk.Label(same_frame, text="✅ 相同文件", font=("Arial", 10, "bold")).pack()
        ttk.Label(same_frame, text=str(len(self.report.same_files)), 
                 font=("Arial", 12), foreground="gray").pack()
        
        # 上传大小信息
        size_info_frame = ttk.Frame(summary_frame)
        size_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        upload_size = FileUtils.format_file_size(self.report.total_upload_size)
        ttk.Label(size_info_frame, text=f"📦 需要上传: {self.report.total_files_to_upload} 个文件, "
                                       f"总大小: {upload_size}", 
                 font=("Arial", 10)).pack(side=tk.LEFT)
        
        if self.report.total_files_to_delete > 0:
            ttk.Label(size_info_frame, text=f"🗑️ 需要删除: {self.report.total_files_to_delete} 个文件", 
                     font=("Arial", 10), foreground="red").pack(side=tk.RIGHT)
    
    def create_details_section(self, parent):
        """创建详细信息区域"""
        details_frame = ttk.LabelFrame(parent, text="📄 详细信息", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建标签页
        notebook = ttk.Notebook(details_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 新增文件标签页
        if self.report.new_files:
            new_tab = self.create_file_list_tab(notebook, self.report.new_files, "新增文件", "green")
            notebook.add(new_tab, text=f"🆕 新增 ({len(self.report.new_files)})")
        
        # 修改文件标签页
        if self.report.modified_files:
            modified_tab = self.create_file_list_tab(notebook, self.report.modified_files, "修改文件", "orange")
            notebook.add(modified_tab, text=f"📝 修改 ({len(self.report.modified_files)})")
        
        # 删除文件标签页
        if self.report.deleted_files:
            deleted_tab = self.create_file_list_tab(notebook, self.report.deleted_files, "删除文件", "red")
            notebook.add(deleted_tab, text=f"🗑️ 删除 ({len(self.report.deleted_files)})")
        
        # 相同文件标签页（可选显示）
        if self.report.same_files:
            same_tab = self.create_file_list_tab(notebook, self.report.same_files, "相同文件", "gray")
            notebook.add(same_tab, text=f"✅ 相同 ({len(self.report.same_files)})")
    
    def create_file_list_tab(self, parent, file_list, title, color):
        """创建文件列表标签页"""
        tab_frame = ttk.Frame(parent)
        
        # 创建树形视图
        columns = ("文件路径", "大小", "状态")
        tree = ttk.Treeview(tab_frame, columns=columns, show="tree headings", height=15)
        
        # 配置列
        tree.heading("#0", text="", anchor=tk.W)
        tree.column("#0", width=0, stretch=False)
        
        tree.heading("文件路径", text="文件路径", anchor=tk.W)
        tree.column("文件路径", width=400, anchor=tk.W)
        
        tree.heading("大小", text="大小", anchor=tk.E)
        tree.column("大小", width=100, anchor=tk.E)
        
        tree.heading("状态", text="状态", anchor=tk.CENTER)
        tree.column("状态", width=100, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 填充数据
        for file_diff in file_list:
            file_info = file_diff.local_info or file_diff.remote_info
            if file_info:
                size_str = FileUtils.format_file_size(file_info.file_size)
                status = self.get_status_text(file_diff.change_type)
                
                tree.insert("", tk.END, values=(
                    file_diff.relative_path,
                    size_str,
                    status
                ))
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return tab_frame
    
    def get_status_text(self, change_type: ChangeType) -> str:
        """获取状态文本"""
        status_map = {
            ChangeType.NEW: "新增",
            ChangeType.MODIFIED: "修改",
            ChangeType.DELETED: "删除",
            ChangeType.SAME: "相同"
        }
        return status_map.get(change_type, "未知")
    
    def create_buttons_section(self, parent):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 警告信息
        if self.report.total_files_to_delete > 0:
            warning_frame = ttk.Frame(button_frame)
            warning_frame.pack(fill=tk.X, pady=(0, 10))
            
            warning_label = ttk.Label(warning_frame, 
                                    text="⚠️ 警告：将删除云端的多余文件，此操作不可撤销！",
                                    font=("Arial", 10, "bold"), foreground="red")
            warning_label.pack()
        
        # 按钮
        buttons_container = ttk.Frame(button_frame)
        buttons_container.pack()
        
        # 确认按钮
        confirm_text = "确认上传" if self.report.total_files_to_upload > 0 else "确认同步"
        confirm_button = ttk.Button(buttons_container, text=confirm_text,
                                   command=self.on_confirm_click, style="Accent.TButton")
        confirm_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_button = ttk.Button(buttons_container, text="取消",
                                  command=self.on_cancel_click)
        cancel_button.pack(side=tk.LEFT)
        
        # 如果没有需要操作的文件，禁用确认按钮
        if self.report.total_files_to_upload == 0 and self.report.total_files_to_delete == 0:
            confirm_button.config(state="disabled")
            confirm_button.config(text="无需操作")
    
    def on_confirm_click(self):
        """确认按钮点击事件"""
        self.result = True
        if self.on_confirm:
            self.on_confirm()
        self.window.destroy()
    
    def on_cancel_click(self):
        """取消按钮点击事件"""
        self.result = False
        if self.on_cancel:
            self.on_cancel()
        self.window.destroy()
    
    def on_window_close(self):
        """窗口关闭事件"""
        self.result = False
        if self.on_cancel:
            self.on_cancel()
        self.window.destroy()
    
    def show_modal(self) -> bool:
        """模态显示窗口"""
        self.window.wait_window()
        return self.result


def show_difference_report(parent: tk.Tk, report: DifferenceReport) -> bool:
    """
    显示差异报告对话框
    
    Args:
        parent: 父窗口
        report: 差异报告
        
    Returns:
        用户是否确认继续
    """
    viewer = DifferenceViewerWindow(parent, report)
    return viewer.show_modal()
