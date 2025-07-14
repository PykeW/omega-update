#!/usr/bin/env python3
"""
Omega更新服务器 - 重构后的独立上传工具
模块化设计，专门用于文件上传、存储管理和版本控制
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional
from pathlib import Path

# 导入共享模块
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import (
    get_config, LogManager, AppConstants, ValidationUtils
)

# 导入新的模块化组件
from tools.common.ui_factory import UIComponentFactory, WindowFactory
from tools.upload.upload_handler import UploadHandler
from tools.common.storage_handler import StorageHandler


class UploadToolRefactored:
    """重构后的上传工具主类"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化上传工具
        
        Args:
            root: 主窗口
        """
        self.root = root
        self.root.title(AppConstants.UPLOAD_TOOL_TITLE)
        self.root.geometry(AppConstants.UPLOAD_WINDOW_SIZE)
        
        # 配置
        self.config = get_config()
        
        # 界面变量
        self.selected_folder = tk.StringVar()
        self.package_type = tk.StringVar(value="full")
        self.version = tk.StringVar()
        self.from_version = tk.StringVar()
        self.description = tk.StringVar()
        self.is_stable = tk.BooleanVar(value=True)
        self.is_critical = tk.BooleanVar(value=False)
        self.platform = tk.StringVar(value="windows")
        self.architecture = tk.StringVar(value="x64")
        
        # 业务逻辑处理器
        self.log_manager: Optional[LogManager] = None
        self.upload_handler: Optional[UploadHandler] = None
        self.storage_handler: Optional[StorageHandler] = None
        
        # UI组件引用
        self.ui_components: Dict[str, Any] = {}
        
        self.setup_ui()
        self.initialize_handlers()
        self.refresh_storage_stats()
    
    def setup_ui(self):
        """设置用户界面"""
        # 设置主布局
        main_frame = WindowFactory.setup_main_layout(self.root)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        
        current_row = 0
        
        # 存储状态框架
        storage_components = UIComponentFactory.create_storage_status_frame(main_frame)
        storage_components['frame'].grid(row=current_row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        storage_components['refresh_button'].config(command=self.refresh_storage_stats)
        self.ui_components.update(storage_components)
        current_row += 1
        
        # 包类型选择框架
        package_frame = UIComponentFactory.create_package_type_frame(
            main_frame, self.package_type, self.on_package_type_change
        )
        package_frame.grid(row=current_row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        current_row += 1
        
        # 版本信息框架
        version_variables = {
            'version': self.version,
            'platform': self.platform,
            'architecture': self.architecture,
            'description': self.description
        }
        version_frame = UIComponentFactory.create_version_info_frame(main_frame, version_variables)
        version_frame.grid(row=current_row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        
        # 添加来源版本控件（增量包用）
        self.from_version_label = ttk.Label(version_frame, text="来源版本:")
        self.from_version_entry = ttk.Entry(version_frame, textvariable=self.from_version, width=20)
        current_row += 1
        
        # 文件夹选择框架
        folder_components = UIComponentFactory.create_folder_selection_frame(
            main_frame, self.selected_folder, self.select_folder, self.preview_folder
        )
        folder_components['frame'].grid(row=current_row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        self.ui_components.update(folder_components)
        current_row += 1
        
        # 选项框架
        options_variables = {
            'is_stable': self.is_stable,
            'is_critical': self.is_critical
        }
        options_frame = UIComponentFactory.create_options_frame(main_frame, options_variables)
        options_frame.grid(row=current_row, column=0, columnspan=3, sticky="we", pady=(0, 10))
        current_row += 1
        
        # 操作按钮框架
        buttons_config = [
            ("上传", self.upload_package),
            ("清理存储", self.cleanup_storage),
            ("查看包列表", self.view_packages),
            ("存储管理", self.show_storage_management),
            ("退出", self.root.quit)
        ]
        buttons_frame = UIComponentFactory.create_button_frame(main_frame, buttons_config)
        buttons_frame.grid(row=current_row, column=0, columnspan=3, pady=(0, 10))
        current_row += 1
        
        # 进度和日志框架
        progress_components = UIComponentFactory.create_progress_frame(main_frame)
        progress_components['frame'].grid(row=current_row, column=0, columnspan=3, sticky="wens", pady=(0, 10))
        main_frame.rowconfigure(current_row, weight=1)
        self.ui_components.update(progress_components)
    
    def initialize_handlers(self):
        """初始化业务逻辑处理器"""
        # 初始化日志管理器
        self.log_manager = LogManager(self.ui_components['log_text'])
        
        # 初始化业务处理器
        self.upload_handler = UploadHandler(self.log_manager)
        self.storage_handler = StorageHandler(self.log_manager)
    
    def on_package_type_change(self):
        """包类型改变事件"""
        pkg_type = self.package_type.get()
        
        if pkg_type == "patch":
            # 显示来源版本输入
            self.from_version_label.grid(row=1, column=2, sticky="w", pady=(10, 0))
            self.from_version_entry.grid(row=1, column=3, padx=(10, 20), pady=(10, 0), sticky="w")
        else:
            # 隐藏来源版本输入
            self.from_version_label.grid_remove()
            self.from_version_entry.grid_remove()
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = filedialog.askdirectory(title="选择要上传的文件夹")
        if folder_path:
            self.selected_folder.set(folder_path)
            self.analyze_folder(folder_path)
    
    def analyze_folder(self, folder_path: str):
        """分析文件夹内容"""
        if self.upload_handler:
            result_text = self.upload_handler.analyze_folder(folder_path)
            self.ui_components['folder_info'].config(text=result_text)
    
    def preview_folder(self):
        """预览文件夹内容"""
        if not self.upload_handler or not self.upload_handler.get_folder_analysis():
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        
        self._show_folder_preview()
    
    def _show_folder_preview(self):
        """显示文件夹预览窗口"""
        analysis = self.upload_handler.get_folder_analysis()
        if not analysis:
            return
        
        # 创建预览窗口
        preview_window = WindowFactory.create_dialog_window(
            self.root, "文件夹内容预览", "600x500"
        )
        
        # 创建文件树
        columns = ("大小", "类型", "修改时间")
        tree_components = UIComponentFactory.create_file_tree(preview_window, columns)
        tree_components['tree'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        tree_components['scrollbar'].pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # 填充文件信息
        self._populate_preview_tree(tree_components['tree'], analysis['path'])
        
        # 添加统计信息
        stats_frame = ttk.Frame(preview_window)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        from common_utils import FileUtils
        stats_text = (f"总文件数: {analysis['total_files']}, "
                      f"总大小: {FileUtils.format_file_size(analysis['total_size'])}")
        ttk.Label(stats_frame, text=stats_text).pack()
    
    def _populate_preview_tree(self, tree: ttk.Treeview, folder_path: str):
        """填充预览树"""
        from datetime import datetime
        
        folder_path = Path(folder_path)
        
        def add_files_to_tree(parent_item, current_path):
            try:
                items = list(current_path.iterdir())
                items.sort(key=lambda x: (x.is_file(), x.name.lower()))
                
                for item in items:
                    relative_path = item.relative_to(folder_path)
                    
                    if item.is_dir():
                        # 添加目录
                        dir_item = tree.insert(parent_item, tk.END, text=str(relative_path), 
                                             values=("", "文件夹", ""))
                        add_files_to_tree(dir_item, item)
                    else:
                        # 添加文件
                        try:
                            stat = item.stat()
                            from common_utils import FileUtils
                            size = FileUtils.format_file_size(stat.st_size)
                            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                            file_type = item.suffix.lower() if item.suffix else "无扩展名"
                            
                            tree.insert(parent_item, tk.END, text=str(relative_path),
                                       values=(size, file_type, mod_time))
                        except Exception:
                            tree.insert(parent_item, tk.END, text=str(relative_path),
                                       values=("错误", "未知", "未知"))
            except Exception as e:
                if self.log_manager:
                    self.log_manager.log_error(f"读取目录失败 {current_path}: {e}")
        
        # 开始填充
        add_files_to_tree("", folder_path)
    
    def upload_package(self):
        """上传文件夹"""
        # 准备上传配置
        upload_config = {
            'folder_path': self.selected_folder.get(),
            'version': self.version.get().strip(),
            'platform': self.platform.get(),
            'architecture': self.architecture.get(),
            'package_type': self.package_type.get(),
            'description': self.description.get().strip(),
            'is_stable': self.is_stable.get(),
            'is_critical': self.is_critical.get(),
            'from_version': self.from_version.get().strip() if self.package_type.get() == "patch" else ""
        }
        
        # 确认上传
        if not messagebox.askyesno("确认", f"确定要上传版本 {upload_config['version']} 吗？"):
            return
        
        # 开始上传
        self.ui_components['progress']['value'] = 0
        self.ui_components['status_label'].config(text="准备上传...")
        
        def progress_callback(progress, status):
            self.root.after(0, lambda: self._update_upload_progress(progress, status))
        
        def upload_complete_callback(success):
            self.root.after(0, lambda: self._upload_complete(success))
        
        # 在新线程中执行上传
        import threading
        def upload_thread():
            success = self.upload_handler.start_upload(upload_config, progress_callback)
            upload_complete_callback(success)
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def _update_upload_progress(self, progress: float, status: str):
        """更新上传进度"""
        self.ui_components['progress']['value'] = progress
        self.ui_components['status_label'].config(text=status)
    
    def _upload_complete(self, success: bool):
        """上传完成"""
        self.ui_components['progress']['value'] = 100
        
        if success:
            self.ui_components['status_label'].config(text="上传完成")
            messagebox.showinfo("成功", "文件上传成功！")
        else:
            self.ui_components['status_label'].config(text="上传失败")
            messagebox.showerror("失败", "文件上传失败，请查看日志了解详情")
        
        # 刷新存储统计
        self.refresh_storage_stats()
    
    def refresh_storage_stats(self):
        """刷新存储统计"""
        if self.storage_handler:
            def callback(usage, status):
                self.root.after(0, lambda: self._update_storage_ui(usage, status))
            
            self.storage_handler.get_storage_stats(callback)
    
    def _update_storage_ui(self, usage: float, status: str):
        """更新存储UI"""
        color_map = {
            "healthy": "green",
            "warning": "orange", 
            "critical": "red",
            "error": "red"
        }
        
        self.ui_components['storage_progress']['value'] = usage
        color = color_map.get(status, "gray")
        self.ui_components['storage_label'].config(
            text=f"存储使用情况: {usage:.1f}% ({status})", 
            foreground=color
        )
    
    def cleanup_storage(self):
        """清理存储"""
        if not messagebox.askyesno("确认", "确定要执行存储清理吗？这将删除旧的更新包。"):
            return
        
        if self.storage_handler:
            def callback(success, message):
                self.root.after(0, lambda: self._cleanup_complete(success, message))
            
            self.storage_handler.cleanup_storage(callback)
    
    def _cleanup_complete(self, success: bool, message: str):
        """清理完成"""
        if success:
            messagebox.showinfo("成功", message)
        else:
            messagebox.showerror("错误", message)
        
        # 刷新存储统计
        self.refresh_storage_stats()
    
    def view_packages(self):
        """查看包列表"""
        if self.storage_handler:
            def callback(packages):
                self.root.after(0, lambda: self._show_packages_window(packages))
            
            self.storage_handler.get_packages_list(
                self.platform.get(), self.architecture.get(), 50, callback
            )
    
    def _show_packages_window(self, packages: list):
        """显示包列表窗口"""
        packages_window = WindowFactory.create_dialog_window(
            self.root, "包列表", "800x600"
        )
        
        # 创建包列表树
        columns = ("版本", "类型", "平台", "架构", "大小", "状态", "创建时间")
        tree_components = UIComponentFactory.create_file_tree(packages_window, columns)
        tree_components['tree'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        tree_components['scrollbar'].pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        
        # 填充包数据
        self._populate_packages_tree(tree_components['tree'], packages)
    
    def _populate_packages_tree(self, tree: ttk.Treeview, packages: list):
        """填充包列表树"""
        from datetime import datetime
        from common_utils import FileUtils
        
        for package in packages:
            created_at = package.get('created_at', '')
            if created_at:
                try:
                    # 格式化时间
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            tree.insert("", tk.END, values=(
                package.get('version', ''),
                AppConstants.PACKAGE_TYPE_NAMES.get(package.get('package_type', ''), package.get('package_type', '')),
                package.get('platform', ''),
                package.get('architecture', ''),
                FileUtils.format_file_size(package.get('total_size', 0)),
                package.get('status', ''),
                created_at
            ))
    
    def show_storage_management(self):
        """显示存储管理窗口"""
        # 这里可以实现更复杂的存储管理界面
        # 为了简化，暂时显示一个简单的信息窗口
        messagebox.showinfo("存储管理", "存储管理功能正在开发中...")


def main():
    """主函数"""
    root = WindowFactory.create_main_window(
        AppConstants.UPLOAD_TOOL_TITLE, 
        AppConstants.UPLOAD_WINDOW_SIZE
    )
    app = UploadToolRefactored(root)
    root.mainloop()


if __name__ == "__main__":
    main()
