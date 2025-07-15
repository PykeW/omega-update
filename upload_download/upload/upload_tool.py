#!/usr/bin/env python3
"""
简化上传工具
实现新的三版本类型上传界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import threading
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import get_config, get_server_url, get_api_key, LogManager
from tools.upload.upload_handler import UploadHandler
from tools.upload.incremental_uploader import IncrementalUploader
from tools.upload.difference_viewer import show_difference_report


class SimplifiedUploadTool:
    """简化上传工具"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Omega更新服务器 - 简化上传工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        # 配置
        self.config = get_config()
        self.server_url = get_server_url()
        self.api_key = get_api_key()

        # 变量
        self.folder_path_var = tk.StringVar()
        self.version_type_var = tk.StringVar(value="stable")
        self.platform_var = tk.StringVar(value="windows")
        self.architecture_var = tk.StringVar(value="x64")
        self.description_var = tk.StringVar()
        self.incremental_mode_var = tk.BooleanVar(value=True)
        self.enable_sync_var = tk.BooleanVar(value=True)

        # 状态变量
        self.is_uploading = False
        self.upload_handler = UploadHandler()
        self.incremental_uploader = IncrementalUploader()
        self.log_manager = LogManager()

        # 创建界面
        self.create_widgets()

        # 初始化检查
        self.check_server_connection()

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # 标题
        title_label = ttk.Label(main_frame, text="Omega更新服务器 - 简化上传工具",
                               font=("Arial", 14, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(0, 20))
        row += 1

        # 文件夹选择
        folder_frame = ttk.LabelFrame(main_frame, text="📁 文件夹路径", padding="10")
        folder_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(0, 10))
        folder_frame.columnconfigure(0, weight=1)

        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=50)
        folder_entry.grid(row=0, column=0, sticky=tk.W + tk.E, padx=(0, 10))

        folder_button = ttk.Button(folder_frame, text="选择文件夹...",
                                  command=self.select_folder)
        folder_button.grid(row=0, column=1)

        preview_button = ttk.Button(folder_frame, text="预览内容",
                                   command=self.preview_folder)
        preview_button.grid(row=0, column=2, padx=(5, 0))

        row += 1

        # 版本类型选择
        version_frame = ttk.LabelFrame(main_frame, text="🏷️ 版本类型选择", padding="15")
        version_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(0, 15))
        version_frame.columnconfigure(1, weight=1)

        # 添加说明文字
        info_label = ttk.Label(version_frame,
                              text="选择版本类型，系统将自动覆盖同类型的旧版本：",
                              font=("Arial", 9))
        info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # 版本类型说明
        version_types = [
            ("stable", "🟢 稳定版 (Stable)", "生产环境使用，经过充分测试的正式版本"),
            ("beta", "🟡 测试版 (Beta)", "预发布测试，功能基本稳定，等待最终验证"),
            ("alpha", "🔴 新功能测试版 (Alpha)", "开发测试，包含最新功能，可能不稳定")
        ]

        for i, (value, text, desc) in enumerate(version_types):
            # 创建框架来包含单选按钮和描述
            type_frame = ttk.Frame(version_frame)
            type_frame.grid(row=i+1, column=0, columnspan=2, sticky=tk.W + tk.E, pady=3)
            type_frame.columnconfigure(1, weight=1)

            radio = ttk.Radiobutton(type_frame, text=text,
                                   variable=self.version_type_var, value=value,
                                   style="Large.TRadiobutton")
            radio.grid(row=0, column=0, sticky=tk.W)

            desc_label = ttk.Label(type_frame, text=desc,
                                  foreground="gray", font=("Arial", 8))
            desc_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

        row += 1

        # 版本描述（可选）
        desc_frame = ttk.LabelFrame(main_frame, text="📝 版本描述（可选）", padding="10")
        desc_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(0, 10))
        desc_frame.columnconfigure(0, weight=1)

        # 添加说明
        desc_info = ttk.Label(desc_frame,
                             text="可选填写本次更新的主要内容，留空将自动生成描述",
                             font=("Arial", 8), foreground="gray")
        desc_info.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        desc_entry = ttk.Entry(desc_frame, textvariable=self.description_var, width=60)
        desc_entry.grid(row=1, column=0, sticky=tk.W + tk.E)

        # 设置占位符
        self.description_var.set("例如：修复了登录问题，优化了性能...")

        row += 1

        # 上传模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="🚀 上传模式", padding="10")
        mode_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(0, 10))

        # 增量上传选项
        incremental_check = ttk.Checkbutton(mode_frame, text="启用增量上传（智能对比，只上传变化的文件）",
                                          variable=self.incremental_mode_var,
                                          command=self.on_incremental_mode_changed)
        incremental_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # 同步删除选项
        self.sync_check = ttk.Checkbutton(mode_frame, text="启用云端同步（删除云端多余的文件）",
                                        variable=self.enable_sync_var)
        self.sync_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=(20, 0))

        # 差异分析按钮
        self.analyze_button = ttk.Button(mode_frame, text="分析差异",
                                       command=self.analyze_differences)
        self.analyze_button.grid(row=2, column=0, pady=(10, 0), sticky=tk.W)

        row += 1

        # 高级选项
        advanced_frame = ttk.LabelFrame(main_frame, text="⚙️ 高级选项", padding="10")
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(0, 10))

        ttk.Label(advanced_frame, text="平台:").grid(row=0, column=0, sticky=tk.W)
        platform_combo = ttk.Combobox(advanced_frame, textvariable=self.platform_var,
                                     values=["windows", "linux", "macos"],
                                     state="readonly", width=15)
        platform_combo.grid(row=0, column=1, padx=(5, 20))

        ttk.Label(advanced_frame, text="架构:").grid(row=0, column=2, sticky=tk.W)
        arch_combo = ttk.Combobox(advanced_frame, textvariable=self.architecture_var,
                                 values=["x64", "x86", "arm64"],
                                 state="readonly", width=15)
        arch_combo.grid(row=0, column=3, padx=(5, 0))

        row += 1

        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))

        self.upload_button = ttk.Button(button_frame, text="开始上传",
                                       command=self.start_upload, style="Accent.TButton")
        self.upload_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = ttk.Button(button_frame, text="取消",
                                  command=self.cancel_upload)
        cancel_button.pack(side=tk.LEFT)

        row += 1

        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="📊 上传进度", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(20, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.StringVar(value="准备就绪")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W + tk.E)

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=tk.W + tk.E, pady=(5, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=row+1, column=0, columnspan=2, sticky=tk.W + tk.E, pady=(10, 0))

    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要上传的文件夹")
        if folder:
            self.folder_path_var.set(folder)
            self.status_var.set(f"已选择文件夹: {folder}")

    def on_incremental_mode_changed(self):
        """增量模式变化事件"""
        if self.incremental_mode_var.get():
            self.sync_check.config(state="normal")
            self.analyze_button.config(state="normal")
        else:
            self.sync_check.config(state="disabled")
            self.analyze_button.config(state="disabled")

    def analyze_differences(self):
        """分析文件差异"""
        folder_path = self.folder_path_var.get()
        if not folder_path:
            messagebox.showwarning("警告", "请先选择文件夹")
            return

        if not Path(folder_path).exists():
            messagebox.showerror("错误", "选择的文件夹不存在")
            return

        version_type = self.version_type_var.get()
        platform = self.platform_var.get()
        architecture = self.architecture_var.get()

        try:
            # 显示分析进度
            self.progress_var.set("正在分析文件差异...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            self.root.update()

            # 分析差异
            report = self.incremental_uploader.analyze_folder_differences(
                folder_path, version_type, platform, architecture
            )

            # 停止进度条
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate', value=0)
            self.progress_var.set("差异分析完成")

            # 显示差异报告
            show_difference_report(self.root, report)

        except Exception as e:
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate', value=0)
            self.progress_var.set("差异分析失败")
            messagebox.showerror("错误", f"差异分析失败: {e}")

    def preview_folder(self):
        """预览文件夹内容"""
        folder_path = self.folder_path_var.get()
        if not folder_path:
            messagebox.showwarning("警告", "请先选择文件夹")
            return

        try:
            # 分析文件夹
            analysis_text = self.upload_handler.analyze_folder(folder_path)
            if analysis_text:
                # 获取详细分析数据
                analysis_data = self.upload_handler.get_folder_analysis()
                if analysis_data:
                    from tools.upload.upload_handler import FolderAnalyzer
                    formatted_result = FolderAnalyzer.format_analysis_result(analysis_data)
                else:
                    formatted_result = analysis_text

                # 显示预览窗口
                preview_window = tk.Toplevel(self.root)
                preview_window.title("文件夹内容预览")
                preview_window.geometry("500x400")

                text_widget = tk.Text(preview_window, wrap=tk.WORD, padx=10, pady=10)
                text_widget.pack(fill=tk.BOTH, expand=True)

                text_widget.insert(tk.END, formatted_result)
                text_widget.config(state=tk.DISABLED)

            else:
                messagebox.showerror("错误", "无法分析文件夹内容")

        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {e}")

    def check_server_connection(self):
        """检查服务器连接"""
        def check():
            try:
                response = requests.get(f"{self.server_url}/api/v2/status/simple", timeout=5)
                if response.status_code == 200:
                    self.status_var.set("服务器连接正常")
                else:
                    self.status_var.set("服务器连接异常")
            except:
                self.status_var.set("无法连接到服务器")

        threading.Thread(target=check, daemon=True).start()

    def start_upload(self):
        """开始上传"""
        if self.is_uploading:
            return

        # 验证输入
        folder_path = self.folder_path_var.get()
        if not folder_path:
            messagebox.showwarning("警告", "请选择要上传的文件夹")
            return

        if not Path(folder_path).exists():
            messagebox.showerror("错误", "选择的文件夹不存在")
            return

        version_type = self.version_type_var.get()
        platform = self.platform_var.get()
        architecture = self.architecture_var.get()
        description = self.description_var.get().strip()

        # 自动生成描述（如果为空或是占位符）
        if not description or description.startswith("例如："):
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            version_names = {
                "stable": "稳定版",
                "beta": "测试版",
                "alpha": "新功能测试版"
            }
            description = f"{version_names.get(version_type, version_type)}更新 - {timestamp}"

        # 根据上传模式确认上传
        version_names = {
            "stable": "🟢 稳定版 (Stable)",
            "beta": "🟡 测试版 (Beta)",
            "alpha": "🔴 新功能测试版 (Alpha)"
        }

        if self.incremental_mode_var.get():
            # 增量上传模式：先分析差异，然后确认
            try:
                # 分析差异
                self.progress_var.set("分析文件差异...")
                self.progress_bar.config(mode='indeterminate')
                self.progress_bar.start()
                self.root.update()

                report = self.incremental_uploader.analyze_folder_differences(
                    folder_path, version_type, platform, architecture
                )

                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate', value=0)
                self.progress_var.set("差异分析完成")

                # 显示差异报告并获取用户确认
                if not show_difference_report(self.root, report):
                    self.progress_var.set("用户取消上传")
                    return

            except Exception as e:
                self.progress_bar.stop()
                self.progress_bar.config(mode='determinate', value=0)
                self.progress_var.set("差异分析失败")
                messagebox.showerror("错误", f"差异分析失败: {e}")
                return
        else:
            # 传统上传模式：直接确认
            confirm_msg = f"""
📤 确认上传信息：

📁 文件夹: {Path(folder_path).name}
🏷️  版本类型: {version_names.get(version_type, version_type)}
💻 平台: {platform} ({architecture})
📝 描述: {description}

⚠️  重要提醒：
• 将直接上传文件夹中的所有文件（保持原始结构）
• 上传将自动覆盖同类型的现有版本
• 旧版本将保存在历史记录中
• 此操作不可撤销

是否确认上传？
            """

            if not messagebox.askyesno("确认上传", confirm_msg.strip()):
                return

        # 开始上传
        self.is_uploading = True
        self.upload_button.config(state="disabled")
        self.progress_var.set("准备上传...")
        self.progress_bar.config(value=0)

        # 在后台线程中执行上传
        upload_thread = threading.Thread(
            target=self._upload_worker,
            args=(folder_path, version_type, platform, architecture, description),
            daemon=True
        )
        upload_thread.start()

    def _upload_worker(self, folder_path: str, version_type: str,
                      platform: str, architecture: str, description: str):
        """上传工作线程"""
        try:
            if self.incremental_mode_var.get():
                # 增量上传模式
                success = self._upload_incremental(
                    folder_path, version_type, platform, architecture, description
                )
            else:
                # 传统上传模式
                success = self._upload_simplified(
                    folder_path, version_type, platform, architecture, description
                )

            if success:
                self.root.after(0, lambda: self._upload_success())
            else:
                self.root.after(0, lambda: self._upload_failed("上传失败"))

        except Exception as e:
            self.root.after(0, lambda: self._upload_failed(str(e)))

    def _upload_incremental(self, folder_path: str, version_type: str,
                           platform: str, architecture: str, description: str) -> bool:
        """增量上传方法"""
        try:
            # 准备进度回调
            def progress_callback(progress, message):
                self.root.after(0, lambda: self.progress_var.set(message))
                self.root.after(0, lambda: self.progress_bar.config(value=progress))

            # 执行增量上传
            success = self.incremental_uploader.perform_incremental_upload(
                folder_path=folder_path,
                version_type=version_type,
                platform=platform,
                architecture=architecture,
                description=description,
                enable_sync=self.enable_sync_var.get(),
                progress_callback=progress_callback
            )

            return success

        except Exception as e:
            print(f"增量上传异常: {e}")
            return False

    def _upload_simplified(self, folder_path: str, version_type: str,
                          platform: str, architecture: str, description: str) -> bool:
        """使用简化API直接上传文件"""
        try:
            # 准备上传配置
            upload_config = {
                'version_type': version_type,
                'platform': platform,
                'architecture': architecture,
                'description': description
            }

            # 使用UploadHandler的直接上传功能
            def progress_callback(progress, message):
                self.root.after(0, lambda: self.progress_var.set(message))
                self.root.after(0, lambda: self.progress_bar.config(value=progress))

            self.root.after(0, lambda: self.progress_var.set("开始上传文件..."))
            self.root.after(0, lambda: self.progress_bar.config(value=0))

            # 直接上传文件夹
            success = self.upload_handler.upload_folder_directly(
                folder_path, upload_config, progress_callback
            )

            self.root.after(0, lambda: self.progress_bar.config(value=100))

            return success

        except Exception as e:
            print(f"上传异常: {e}")
            return False

    def _upload_success(self):
        """上传成功回调"""
        self.progress_var.set("上传完成！")
        self.status_var.set("上传成功")
        self.is_uploading = False
        self.upload_button.config(state="normal")
        messagebox.showinfo("成功", "版本上传成功！")

    def _upload_failed(self, error_msg: str):
        """上传失败回调"""
        self.progress_var.set("上传失败")
        self.status_var.set(f"上传失败: {error_msg}")
        self.is_uploading = False
        self.upload_button.config(state="normal")
        self.progress_bar.config(value=0)
        messagebox.showerror("失败", f"上传失败: {error_msg}")

    def cancel_upload(self):
        """取消上传"""
        if self.is_uploading:
            # 这里可以添加取消上传的逻辑
            pass
        self.root.quit()


def main():
    """主函数"""
    root = tk.Tk()

    # 设置主题
    try:
        root.tk.call("source", "azure.tcl")
        root.tk.call("set_theme", "light")
    except:
        pass  # 如果主题文件不存在，使用默认主题

    upload_tool = SimplifiedUploadTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
