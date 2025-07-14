#!/usr/bin/env python3
"""
简化下载工具
实现新的三版本类型下载界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import threading
import requests
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.common.common_utils import get_config, get_server_url, get_api_key


class SimplifiedDownloadTool:
    """简化下载工具"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Omega更新服务器 - 简化下载工具")
        self.root.geometry("600x450")
        self.root.resizable(True, True)
        
        # 配置
        self.config = get_config()
        self.server_url = get_server_url()
        self.api_key = get_api_key()
        
        # 变量
        self.version_type_var = tk.StringVar(value="stable")
        self.platform_var = tk.StringVar(value="windows")
        self.architecture_var = tk.StringVar(value="x64")
        self.download_path_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        
        # 状态变量
        self.is_downloading = False
        self.current_version_info = None
        
        # 创建界面
        self.create_widgets()
        
        # 初始化检查
        self.check_server_connection()
        self.load_version_info()
    
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
        title_label = ttk.Label(main_frame, text="Omega更新服务器 - 简化下载工具", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(0, 20))
        row += 1
        
        # 版本选择
        version_frame = ttk.LabelFrame(main_frame, text="📥 版本选择", padding="10")
        version_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        version_frame.columnconfigure(1, weight=1)
        
        ttk.Label(version_frame, text="版本类型:").grid(row=0, column=0, sticky=tk.W)
        
        version_combo = ttk.Combobox(version_frame, textvariable=self.version_type_var,
                                   values=[
                                       ("stable", "稳定版 (Stable)"),
                                       ("beta", "测试版 (Beta)"),
                                       ("alpha", "新功能测试版 (Alpha)")
                                   ],
                                   state="readonly", width=30)
        version_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        version_combo.bind('<<ComboboxSelected>>', self.on_version_changed)
        
        # 设置显示值
        version_combo.set("稳定版 (Stable)")
        
        row += 1
        
        # 版本信息
        info_frame = ttk.LabelFrame(main_frame, text="📋 版本信息", padding="10")
        info_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        # 描述
        ttk.Label(info_frame, text="描述:").grid(row=0, column=0, sticky=(tk.W, tk.N))
        self.description_var = tk.StringVar(value="正在加载...")
        desc_label = ttk.Label(info_frame, textvariable=self.description_var, 
                              wraplength=400, justify=tk.LEFT)
        desc_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # 上传时间
        ttk.Label(info_frame, text="上传时间:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.upload_time_var = tk.StringVar(value="正在加载...")
        ttk.Label(info_frame, textvariable=self.upload_time_var).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # 文件大小
        ttk.Label(info_frame, text="文件大小:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.file_size_var = tk.StringVar(value="正在加载...")
        ttk.Label(info_frame, textvariable=self.file_size_var).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        row += 1
        
        # 下载路径
        path_frame = ttk.LabelFrame(main_frame, text="📁 下载路径", padding="10")
        path_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(0, weight=1)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var, width=50)
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        path_button = ttk.Button(path_frame, text="选择文件夹...", 
                                command=self.select_download_path)
        path_button.grid(row=0, column=1)
        
        row += 1
        
        # 高级选项
        advanced_frame = ttk.LabelFrame(main_frame, text="⚙️ 高级选项", padding="10")
        advanced_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(advanced_frame, text="平台:").grid(row=0, column=0, sticky=tk.W)
        platform_combo = ttk.Combobox(advanced_frame, textvariable=self.platform_var,
                                     values=["windows", "linux", "macos"], 
                                     state="readonly", width=15)
        platform_combo.grid(row=0, column=1, padx=(5, 20))
        platform_combo.bind('<<ComboboxSelected>>', self.on_platform_changed)
        
        ttk.Label(advanced_frame, text="架构:").grid(row=0, column=2, sticky=tk.W)
        arch_combo = ttk.Combobox(advanced_frame, textvariable=self.architecture_var,
                                 values=["x64", "x86", "arm64"], 
                                 state="readonly", width=15)
        arch_combo.grid(row=0, column=3, padx=(5, 0))
        arch_combo.bind('<<ComboboxSelected>>', self.on_architecture_changed)
        
        row += 1
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        self.check_button = ttk.Button(button_frame, text="检查更新", 
                                      command=self.check_for_updates)
        self.check_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.download_button = ttk.Button(button_frame, text="开始下载", 
                                         command=self.start_download, 
                                         style="Accent.TButton")
        self.download_button.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_button = ttk.Button(button_frame, text="取消", 
                                  command=self.cancel_download)
        cancel_button.pack(side=tk.LEFT)
        
        row += 1
        
        # 进度显示
        progress_frame = ttk.LabelFrame(main_frame, text="📊 下载进度", padding="10")
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
    
    def select_download_path(self):
        """选择下载路径"""
        folder = filedialog.askdirectory(title="选择下载文件夹")
        if folder:
            self.download_path_var.set(folder)
            self.status_var.set(f"下载路径: {folder}")
    
    def on_version_changed(self, event=None):
        """版本类型改变事件"""
        # 从显示文本中提取版本类型
        display_text = self.version_type_var.get()
        if "稳定版" in display_text:
            self.version_type_var.set("stable")
        elif "测试版" in display_text:
            self.version_type_var.set("beta")
        elif "新功能测试版" in display_text:
            self.version_type_var.set("alpha")
        
        self.load_version_info()
    
    def on_platform_changed(self, event=None):
        """平台改变事件"""
        self.load_version_info()
    
    def on_architecture_changed(self, event=None):
        """架构改变事件"""
        self.load_version_info()
    
    def check_server_connection(self):
        """检查服务器连接"""
        def check():
            try:
                response = requests.get(f"{self.server_url}/api/v2/status/simple", timeout=5)
                if response.status_code == 200:
                    self.root.after(0, lambda: self.status_var.set("服务器连接正常"))
                else:
                    self.root.after(0, lambda: self.status_var.set("服务器连接异常"))
            except:
                self.root.after(0, lambda: self.status_var.set("无法连接到服务器"))
        
        threading.Thread(target=check, daemon=True).start()
    
    def load_version_info(self):
        """加载版本信息"""
        def load():
            try:
                version_type = self.version_type_var.get()
                platform = self.platform_var.get()
                architecture = self.architecture_var.get()
                
                response = requests.get(
                    f"{self.server_url}/api/v2/version/simple/{version_type}",
                    params={"platform": platform, "architecture": architecture},
                    timeout=10
                )
                
                if response.status_code == 200:
                    version_info = response.json()
                    self.current_version_info = version_info
                    
                    # 更新界面
                    self.root.after(0, lambda: self._update_version_display(version_info))
                elif response.status_code == 404:
                    self.root.after(0, lambda: self._update_version_display(None))
                else:
                    self.root.after(0, lambda: self.status_var.set("获取版本信息失败"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"加载版本信息失败: {e}"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def _update_version_display(self, version_info: Optional[Dict]):
        """更新版本显示信息"""
        if version_info:
            self.description_var.set(version_info.get('description', '无描述'))
            
            upload_date = version_info.get('upload_date')
            if upload_date:
                try:
                    dt = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    self.upload_time_var.set(dt.strftime('%Y-%m-%d %H:%M:%S'))
                except:
                    self.upload_time_var.set(upload_date)
            else:
                self.upload_time_var.set('未知')
            
            file_size = version_info.get('file_size', 0)
            self.file_size_var.set(self._format_file_size(file_size))
            
            self.download_button.config(state="normal")
            self.status_var.set("版本信息已加载")
        else:
            self.description_var.set("该版本类型暂无可用版本")
            self.upload_time_var.set("无")
            self.file_size_var.set("无")
            self.download_button.config(state="disabled")
            self.status_var.set("无可用版本")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size_float = float(size_bytes)
        while size_float >= 1024 and i < len(size_names) - 1:
            size_float /= 1024.0
            i += 1
        
        return f"{size_float:.1f} {size_names[i]}"
    
    def check_for_updates(self):
        """检查更新"""
        self.load_version_info()
        messagebox.showinfo("检查更新", "版本信息已刷新")
    
    def start_download(self):
        """开始下载"""
        if self.is_downloading:
            return
        
        if not self.current_version_info:
            messagebox.showwarning("警告", "没有可下载的版本")
            return
        
        download_path = self.download_path_var.get()
        if not download_path:
            messagebox.showwarning("警告", "请选择下载路径")
            return
        
        if not Path(download_path).exists():
            messagebox.showerror("错误", "下载路径不存在")
            return
        
        # 确认下载
        version_type = self.version_type_var.get()
        platform = self.platform_var.get()
        architecture = self.architecture_var.get()
        
        confirm_msg = f"""
确认下载信息：
版本类型: {version_type}
平台: {platform}
架构: {architecture}
下载路径: {download_path}
文件大小: {self.file_size_var.get()}
        """
        
        if not messagebox.askyesno("确认下载", confirm_msg.strip()):
            return
        
        # 开始下载
        self.is_downloading = True
        self.download_button.config(state="disabled")
        self.progress_var.set("开始下载...")
        self.progress_bar.config(value=0)
        
        # 在后台线程中执行下载
        download_thread = threading.Thread(
            target=self._download_worker,
            args=(version_type, platform, architecture, download_path),
            daemon=True
        )
        download_thread.start()
    
    def _download_worker(self, version_type: str, platform: str, 
                        architecture: str, download_path: str):
        """下载工作线程"""
        try:
            # 构建下载URL
            download_url = f"{self.server_url}/api/v2/download/simple/{version_type}/{platform}/{architecture}"
            
            self.root.after(0, lambda: self.progress_var.set("正在下载..."))
            
            # 发送下载请求
            response = requests.get(download_url, stream=True, timeout=600)
            
            if response.status_code == 200:
                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                
                # 构建文件名
                filename = f"{version_type}_{platform}_{architecture}.zip"
                file_path = Path(download_path) / filename
                
                # 下载文件
                downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                self.root.after(0, lambda p=progress: self.progress_bar.config(value=p))
                
                self.root.after(0, lambda: self._download_success(str(file_path)))
            else:
                self.root.after(0, lambda: self._download_failed(f"下载失败: {response.status_code}"))
                
        except Exception as e:
            self.root.after(0, lambda: self._download_failed(str(e)))
    
    def _download_success(self, file_path: str):
        """下载成功回调"""
        self.progress_var.set("下载完成！")
        self.status_var.set(f"文件已保存到: {file_path}")
        self.is_downloading = False
        self.download_button.config(state="normal")
        messagebox.showinfo("成功", f"下载完成！\n文件保存到: {file_path}")
    
    def _download_failed(self, error_msg: str):
        """下载失败回调"""
        self.progress_var.set("下载失败")
        self.status_var.set(f"下载失败: {error_msg}")
        self.is_downloading = False
        self.download_button.config(state="normal")
        self.progress_bar.config(value=0)
        messagebox.showerror("失败", f"下载失败: {error_msg}")
    
    def cancel_download(self):
        """取消下载"""
        if self.is_downloading:
            # 这里可以添加取消下载的逻辑
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
    
    app = SimplifiedDownloadTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
