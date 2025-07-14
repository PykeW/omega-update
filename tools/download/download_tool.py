#!/usr/bin/env python3
"""
Omega更新服务器 - 重构后的独立下载工具
模块化设计，专门用于文件下载、更新检查和版本同步
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional, List

# 导入共享模块
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import (
    get_config, LogManager, AppConstants, FileUtils
)

# 导入新的模块化组件
from tools.common.ui_factory import UIComponentFactory, WindowFactory, NotebookFactory
from tools.download.download_handler import DownloadHandler
from tools.download.download_manager import DownloadStatus


class DownloadToolRefactored:
    """重构后的下载工具主类"""

    def __init__(self, root: tk.Tk):
        """
        初始化下载工具

        Args:
            root: 主窗口
        """
        self.root = root
        self.root.title(AppConstants.DOWNLOAD_TOOL_TITLE)
        self.root.geometry(AppConstants.DOWNLOAD_WINDOW_SIZE)

        # 配置
        self.config = get_config()

        # 界面变量
        self.local_folder_var = tk.StringVar()
        self.target_version_var = tk.StringVar()
        self.update_platform_var = tk.StringVar(value="windows")
        self.update_arch_var = tk.StringVar(value="x64")

        # 业务逻辑处理器
        self.log_manager: Optional[LogManager] = None
        self.download_handler: Optional[DownloadHandler] = None

        # UI组件引用
        self.ui_components: Dict[str, Any] = {}

        self.setup_ui()
        self.initialize_handlers()

    def setup_ui(self):
        """设置用户界面"""
        # 设置主布局
        main_frame = WindowFactory.setup_main_layout(self.root)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # 创建笔记本控件
        self.notebook = NotebookFactory.create_notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 检查更新标签页
        check_frame = NotebookFactory.add_tab(self.notebook, "检查更新")
        self.setup_update_check_tab(check_frame)

        # 下载管理标签页
        download_frame = NotebookFactory.add_tab(self.notebook, "下载管理")
        self.setup_download_management_tab(download_frame)

    def setup_update_check_tab(self, parent: ttk.Frame):
        """设置检查更新标签页"""
        # 本地文件夹选择
        folder_components = UIComponentFactory.create_folder_selection_frame(
            parent, self.local_folder_var, self.select_local_folder
        )
        folder_components['frame'].pack(fill=tk.X, padx=10, pady=5)
        self.ui_components.update(folder_components)

        # 目标版本设置
        version_frame = UIComponentFactory.create_labeled_frame(parent, "目标版本")
        version_frame.pack(fill=tk.X, padx=10, pady=5)

        UIComponentFactory.create_entry_with_label(
            version_frame, "版本号:", self.target_version_var, width=20, row=0, column=0
        )

        UIComponentFactory.create_combobox_with_label(
            version_frame, "平台:", self.update_platform_var,
            AppConstants.PLATFORMS, width=15, row=0, column=2
        )

        UIComponentFactory.create_combobox_with_label(
            version_frame, "架构:", self.update_arch_var,
            AppConstants.ARCHITECTURES, width=15, row=0, column=4
        )

        # 操作按钮
        action_buttons_config = [
            ("扫描本地文件", self.scan_local_files),
            ("检查更新", self.check_for_updates)
        ]
        action_frame = UIComponentFactory.create_button_frame(parent, action_buttons_config)
        action_frame.pack(fill=tk.X, padx=10, pady=10)

        # 结果显示区域
        result_frame = UIComponentFactory.create_labeled_frame(parent, "检查结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建树形视图显示文件差异
        columns = ("文件路径", "状态", "大小", "本地哈希", "远程哈希")
        tree_components = UIComponentFactory.create_file_tree(result_frame, columns, height=15)
        tree_components['tree'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_components['scrollbar'].pack(side=tk.RIGHT, fill=tk.Y)
        self.ui_components['update_tree'] = tree_components['tree']

        # 摘要信息
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        self.ui_components['update_summary_label'] = ttk.Label(summary_frame, text="", foreground="blue")
        self.ui_components['update_summary_label'].pack()

        # 下载按钮
        download_buttons_config = [
            ("下载选中文件", self.start_selective_download),
            ("下载全部更新", self.start_full_download)
        ]
        download_frame = UIComponentFactory.create_button_frame(parent, download_buttons_config)
        download_frame.pack(fill=tk.X, padx=10, pady=10)

    def setup_download_management_tab(self, parent: ttk.Frame):
        """设置下载管理标签页"""
        # 下载进度显示
        progress_components = UIComponentFactory.create_download_progress_frame(parent)
        progress_components['frame'].pack(fill=tk.X, padx=10, pady=5)
        self.ui_components.update(progress_components)

        # 控制按钮
        control_buttons_config = [
            ('pause_button', "暂停", self.pause_download, tk.DISABLED),
            ('resume_button', "继续", self.resume_download, tk.DISABLED),
            ('cancel_button', "取消", self.cancel_download, tk.DISABLED),
            ('exit_button', "退出", self.root.quit, tk.NORMAL)
        ]
        control_components = UIComponentFactory.create_control_buttons_frame(parent, control_buttons_config)
        control_components['frame'].pack(fill=tk.X, padx=10, pady=10)
        self.ui_components.update(control_components)

        # 下载日志
        log_frame = UIComponentFactory.create_labeled_frame(parent, "下载日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.ui_components['download_log'] = tk.Text(log_frame, height=15, wrap=tk.WORD)
        download_log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                              command=self.ui_components['download_log'].yview)
        self.ui_components['download_log'].configure(yscrollcommand=download_log_scrollbar.set)

        self.ui_components['download_log'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        download_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def initialize_handlers(self):
        """初始化业务逻辑处理器"""
        # 初始化日志管理器
        self.log_manager = LogManager(self.ui_components['download_log'])

        # 初始化下载处理器
        self.download_handler = DownloadHandler(self.log_manager)

    def select_local_folder(self):
        """选择本地文件夹"""
        folder = filedialog.askdirectory(title="选择本地文件夹")
        if folder:
            self.local_folder_var.set(folder)
            if self.log_manager:
                self.log_manager.log_info(f"选择本地文件夹: {folder}")

    def scan_local_files(self):
        """扫描本地文件"""
        local_folder = self.local_folder_var.get()
        if not local_folder:
            messagebox.showerror("错误", "请先选择本地文件夹")
            return

        def progress_callback(current, total, current_file):
            self.root.after(0, lambda: self.log_manager.log_info(
                f"扫描进度: {current}/{total} - {current_file}") if self.log_manager else None)

        if self.download_handler is None:
            messagebox.showerror("错误", "下载处理器未初始化")
            return

        success = self.download_handler.scan_local_files(local_folder, progress_callback)
        if not success:
            messagebox.showerror("错误", "扫描本地文件失败")

    def check_for_updates(self):
        """检查更新"""
        if self.download_handler is None:
            messagebox.showerror("错误", "下载处理器未初始化")
            return

        local_files = self.download_handler.get_local_files()
        if not local_files:
            messagebox.showerror("错误", "请先扫描本地文件")
            return

        target_version = self.target_version_var.get().strip()
        if not target_version:
            messagebox.showerror("错误", "请输入目标版本号")
            return

        platform = self.update_platform_var.get()
        arch = self.update_arch_var.get()

        def result_callback(update_plan):
            self.root.after(0, lambda: self.display_update_results(update_plan))

        if self.download_handler is None:
            messagebox.showerror("错误", "下载处理器未初始化")
            return

        success = self.download_handler.check_for_updates(
            target_version, platform, arch, result_callback
        )
        if not success:
            messagebox.showerror("错误", "检查更新失败")

    def display_update_results(self, update_plan):
        """显示更新检查结果"""
        if not update_plan:
            return

        # 清空树形视图
        tree = self.ui_components['update_tree']
        for item in tree.get_children():
            tree.delete(item)

        # 添加需要下载的文件
        download_node = tree.insert("", tk.END, text="需要下载", open=True)
        for file_change in update_plan.files_to_download:
            local_hash = file_change.local_info.sha256_hash if file_change.local_info else "无"
            tree.insert(download_node, tk.END,
                       text=file_change.relative_path,
                       values=(file_change.relative_path,
                              file_change.change_type.value,
                              FileUtils.format_file_size(file_change.file_size),
                              local_hash[:16] + "..." if local_hash != "无" else "无",
                              file_change.sha256_hash[:16] + "..."))

        # 添加相同的文件
        if update_plan.files_same:
            same_node = tree.insert("", tk.END, text="相同文件", open=False)
            for file_change in update_plan.files_same:
                tree.insert(same_node, tk.END,
                           text=file_change.relative_path,
                           values=(file_change.relative_path,
                                  "相同",
                                  FileUtils.format_file_size(file_change.file_size),
                                  file_change.sha256_hash[:16] + "...",
                                  file_change.sha256_hash[:16] + "..."))

        # 添加需要删除的文件
        if update_plan.files_to_delete:
            delete_node = tree.insert("", tk.END, text="需要删除", open=False)
            for file_change in update_plan.files_to_delete:
                tree.insert(delete_node, tk.END,
                           text=file_change.relative_path,
                           values=(file_change.relative_path,
                                  "删除",
                                  FileUtils.format_file_size(file_change.file_size),
                                  file_change.sha256_hash[:16] + "...",
                                  "无"))

        # 更新摘要信息
        summary = update_plan.get_summary()
        summary_text = (f"目标版本: {summary['target_version']} | "
                       f"需要下载: {summary['files_to_download']} 个文件 "
                       f"({summary['download_size_mb']} MB) | "
                       f"相同文件: {summary['files_same']} 个 | "
                       f"需要删除: {summary['files_to_delete']} 个")

        self.ui_components['update_summary_label'].config(text=summary_text)
        if self.log_manager:
            self.log_manager.log_info(f"更新检查完成: {summary_text}")

    def start_selective_download(self):
        """开始选择性下载"""
        if self.download_handler is None:
            messagebox.showerror("错误", "下载处理器未初始化")
            return

        update_plan = self.download_handler.get_update_plan()
        if not update_plan:
            messagebox.showerror("错误", "请先检查更新")
            return

        # 获取选中的文件
        tree = self.ui_components['update_tree']
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showerror("错误", "请选择要下载的文件")
            return

        selected_files = []
        for item in selected_items:
            item_text = tree.item(item, "text")
            # 只添加文件项，不添加分组项
            if item_text and not item_text.startswith(("需要下载", "相同文件", "需要删除")):
                selected_files.append(item_text)

        if not selected_files:
            messagebox.showerror("错误", "请选择具体的文件")
            return

        self.start_download(selected_files)

    def start_full_download(self):
        """开始完整下载"""
        if self.download_handler is None:
            messagebox.showerror("错误", "下载处理器未初始化")
            return

        update_plan = self.download_handler.get_update_plan()
        if not update_plan:
            messagebox.showerror("错误", "请先检查更新")
            return

        if not update_plan.files_to_download:
            messagebox.showinfo("信息", "没有需要下载的文件")
            return

        self.start_download()

    def start_download(self, selected_files: Optional[List[str]] = None):
        """开始下载"""
        local_folder = self.local_folder_var.get()
        if not local_folder:
            messagebox.showerror("错误", "请选择本地文件夹")
            return

        if self.download_handler is None:
            messagebox.showerror("错误", "下载处理器未初始化")
            return

        success = self.download_handler.start_download(
            local_folder, selected_files, self.download_progress_callback
        )

        if success:
            if self.log_manager:
                self.log_manager.log_info("开始下载...")
            # 切换到下载管理标签页
            self.notebook.select(1)
        else:
            messagebox.showerror("错误", "无法开始下载，可能已有下载任务在进行")

    def download_progress_callback(self, progress):
        """下载进度回调"""
        # 在主线程中更新UI
        self.root.after(0, lambda: self.update_download_progress(progress))

    def update_download_progress(self, progress):
        """更新下载进度显示"""
        # 更新当前文件
        self.ui_components['current_label'].config(text=f"当前文件: {progress.current_file}")

        # 更新当前文件进度
        self.ui_components['current_progress']['value'] = progress.current_file_progress * 100

        # 更新总体进度
        self.ui_components['overall_label'].config(text=f"总体进度: {progress.overall_progress:.1%}")
        self.ui_components['overall_progress']['value'] = progress.overall_progress * 100

        # 更新统计信息
        speed_mb = progress.download_speed / 1024 / 1024
        eta_min = progress.eta_seconds // 60
        eta_sec = progress.eta_seconds % 60

        stats_text = (f"已完成: {progress.files_completed}/{progress.files_total} 个文件 | "
                     f"失败: {progress.files_failed} | 跳过: {progress.files_skipped} | "
                     f"速度: {speed_mb:.2f} MB/s | 剩余时间: {eta_min:02d}:{eta_sec:02d}")

        self.ui_components['stats_label'].config(text=stats_text)

        # 更新按钮状态
        if progress.status == DownloadStatus.DOWNLOADING:
            self.ui_components['pause_button'].config(state=tk.NORMAL)
            self.ui_components['resume_button'].config(state=tk.DISABLED)
        elif progress.status == DownloadStatus.PENDING:
            self.ui_components['pause_button'].config(state=tk.DISABLED)
            self.ui_components['resume_button'].config(state=tk.NORMAL)
        elif progress.status in [DownloadStatus.COMPLETED, DownloadStatus.CANCELLED]:
            self.ui_components['pause_button'].config(state=tk.DISABLED)
            self.ui_components['resume_button'].config(state=tk.DISABLED)
            self.ui_components['cancel_button'].config(state=tk.DISABLED)

        # 记录日志
        if progress.current_file and self.log_manager:
            self.log_manager.log_info(f"下载: {progress.current_file} - {progress.current_file_progress:.1%}")

    def pause_download(self):
        """暂停下载"""
        if self.download_handler is not None:
            self.download_handler.pause_download()

    def resume_download(self):
        """恢复下载"""
        if self.download_handler is not None:
            self.download_handler.resume_download()

    def cancel_download(self):
        """取消下载"""
        if self.download_handler is not None:
            self.download_handler.cancel_download()


def main():
    """主函数"""
    root = WindowFactory.create_main_window(
        AppConstants.DOWNLOAD_TOOL_TITLE,
        AppConstants.DOWNLOAD_WINDOW_SIZE
    )
    DownloadToolRefactored(root)
    root.mainloop()


if __name__ == "__main__":
    main()
