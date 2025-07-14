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

from tools.common.common_utils import get_config, get_server_url, get_api_key
from tools.upload.upload_handler import UploadHandler


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
        
        # 状态变量
        self.is_uploading = False
        self.upload_handler = UploadHandler()
        
        # 创建界面
        self.create_widgets()
        
        # 初始化检查
        self.check_server_connection()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        folder_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(0, weight=1)
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=50)
        folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        folder_button = ttk.Button(folder_frame, text="选择文件夹...", 
                                  command=self.select_folder)
        folder_button.grid(row=0, column=1)
        
        preview_button = ttk.Button(folder_frame, text="预览内容", 
                                   command=self.preview_folder)
        preview_button.grid(row=0, column=2, padx=(5, 0))
        
        row += 1
        
        # 版本类型选择
        version_frame = ttk.LabelFrame(main_frame, text="🏷️ 版本类型", padding="10")
        version_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 版本类型说明
        version_types = [
            ("stable", "稳定版 (Stable)", "生产环境使用，经过充分测试"),
            ("beta", "测试版 (Beta)", "预发布测试，功能基本稳定"),
            ("alpha", "新功能测试版 (Alpha)", "开发测试，包含最新功能")
        ]
        
        for i, (value, text, desc) in enumerate(version_types):
            radio = ttk.Radiobutton(version_frame, text=text, 
                                   variable=self.version_type_var, value=value)
            radio.grid(row=i, column=0, sticky=tk.W, pady=2)
            
            desc_label = ttk.Label(version_frame, text=f"- {desc}", 
                                  foreground="gray")
            desc_label.grid(row=i, column=1, sticky=tk.W, padx=(20, 0))
        
        row += 1
        
        # 版本描述
        desc_frame = ttk.LabelFrame(main_frame, text="📝 版本描述", padding="10")
        desc_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        desc_frame.columnconfigure(0, weight=1)
        
        desc_entry = ttk.Entry(desc_frame, textvariable=self.description_var, width=60)
        desc_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        row += 1
        
        # 高级选项
        advanced_frame = ttk.LabelFrame(main_frame, text="⚙️ 高级选项", padding="10")
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        progress_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="准备就绪")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=row+1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要上传的文件夹")
        if folder:
            self.folder_path_var.set(folder)
            self.status_var.set(f"已选择文件夹: {folder}")
    
    def preview_folder(self):
        """预览文件夹内容"""
        folder_path = self.folder_path_var.get()
        if not folder_path:
            messagebox.showwarning("警告", "请先选择文件夹")
            return
        
        try:
            # 分析文件夹
            analysis = self.upload_handler.analyze_folder(folder_path)
            if analysis:
                formatted_result = self.upload_handler.format_analysis_result(analysis)
                
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
        description = self.description_var.get()
        
        if not description.strip():
            if not messagebox.askyesno("确认", "版本描述为空，是否继续上传？"):
                return
        
        # 确认上传
        confirm_msg = f"""
确认上传信息：
文件夹: {folder_path}
版本类型: {version_type}
平台: {platform}
架构: {architecture}
描述: {description or '(无)'}

注意：上传将覆盖同类型的现有版本！
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
            # 使用新的简化上传API
            success = self._upload_simplified(
                folder_path, version_type, platform, architecture, description
            )
            
            if success:
                self.root.after(0, lambda: self._upload_success())
            else:
                self.root.after(0, lambda: self._upload_failed("上传失败"))
                
        except Exception as e:
            self.root.after(0, lambda: self._upload_failed(str(e)))
    
    def _upload_simplified(self, folder_path: str, version_type: str,
                          platform: str, architecture: str, description: str) -> bool:
        """使用简化API上传"""
        try:
            # 创建ZIP文件
            self.root.after(0, lambda: self.progress_var.set("正在打包文件..."))
            self.root.after(0, lambda: self.progress_bar.config(value=20))
            
            zip_path = self.upload_handler.create_zip_file(folder_path)
            if not zip_path:
                return False
            
            self.root.after(0, lambda: self.progress_var.set("正在上传..."))
            self.root.after(0, lambda: self.progress_bar.config(value=50))
            
            # 上传到简化API
            with open(zip_path, 'rb') as f:
                files = {'file': (f'{version_type}.zip', f, 'application/zip')}
                data = {
                    'version_type': version_type,
                    'platform': platform,
                    'architecture': architecture,
                    'description': description,
                    'api_key': self.api_key
                }
                
                response = requests.post(
                    f"{self.server_url}/api/v2/upload/simple",
                    files=files,
                    data=data,
                    timeout=600  # 10分钟超时
                )
            
            # 清理临时文件
            Path(zip_path).unlink(missing_ok=True)
            
            self.root.after(0, lambda: self.progress_bar.config(value=100))
            
            if response.status_code == 200:
                return True
            else:
                print(f"上传失败: {response.status_code} - {response.text}")
                return False
                
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
    
    app = SimplifiedUploadTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
