import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import threading
import time
import numpy as np
from pathlib import Path
import ctypes
import sys
import queue
import json

# Отключаем предупреждения OpenCV и FFMPEG
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOG_LEVEL'] = '-8'
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
os.environ['OPENCV_FFMPEG_THREADS'] = '1'

try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

def get_icon_path():
    icon_paths = [
        Path("icon.ico"),
        Path("icon.png"),
        Path("H:/MySoft/ZVideoGridPlayer/icon.ico"),
        Path("H:/MySoft/ZVideoGridPlayer/icon.png"),
        Path(__file__).parent / "icon.ico",
        Path(__file__).parent / "icon.png",
        Path(__file__).parent.parent / "icon.ico",
        Path(__file__).parent.parent / "icon.png",
    ]
    for path in icon_paths:
        if path.exists():
            return str(path)
    return None


class SettingsPanel:
    def __init__(self, parent, settings, app):
        self.parent = parent
        self.settings = settings
        self.app = app
        self.is_visible = False
        self.panel_width = 320
        
        self.panel = tk.Frame(parent, bg='#2c2c2c', width=self.panel_width)
        self.panel.pack(side=tk.RIGHT, fill=tk.Y)
        self.panel.pack_propagate(False)
        self.create_content()
        self.panel.pack_forget()
        
    def create_content(self):
        header = tk.Frame(self.panel, bg='#2c2c2c', height=40)
        header.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(header, text="⚙️ НАСТРОЙКИ", 
                bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 12, 'bold')).pack(side=tk.LEFT, padx=15)
        
        close_btn = tk.Label(header, text="✕", bg='#2c2c2c', fg='#ffffff',
                            font=('Segoe UI', 12), cursor='hand2')
        close_btn.pack(side=tk.RIGHT, padx=15)
        close_btn.bind('<Button-1>', lambda e: self.hide())
        close_btn.bind('<Enter>', lambda e: close_btn.configure(bg='#e81123'))
        close_btn.bind('<Leave>', lambda e: close_btn.configure(bg='#2c2c2c'))
        
        tk.Frame(self.panel, bg='#3c3c3c', height=1).pack(fill=tk.X, pady=10)
        
        canvas_frame = tk.Frame(self.panel, bg='#2c2c2c')
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(canvas_frame, bg='#2c2c2c', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2c2c2c')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Прокрутка мышкой ТОЛЬКО для этой панели
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        self.create_settings_widgets(scrollable_frame)
        
    def create_settings_widgets(self, parent):
        row = 0
        
        tk.Label(parent, text="Видео бэкенд:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.backend = tk.StringVar(value=self.settings.get('backend', 'AUTO'))
        backends = [('AUTO', 'Авто (рекомендуется)'), ('FFMPEG', 'FFMPEG (универсальный)'), 
                    ('MSMF', 'Microsoft Media Foundation'), ('DSHOW', 'DirectShow (классический)')]
        
        backend_frame = tk.Frame(parent, bg='#2c2c2c')
        backend_frame.grid(row=row, column=0, sticky='w', padx=15, pady=5)
        for value, text in backends:
            rb = tk.Radiobutton(backend_frame, text=text, variable=self.backend, value=value,
                               bg='#2c2c2c', fg='#cccccc', selectcolor='#2c2c2c',
                               activebackground='#2c2c2c', font=('Segoe UI', 9))
            rb.pack(anchor='w')
        row += 1
        
        tk.Frame(parent, bg='#3c3c3c', height=1).grid(row=row, column=0, sticky='ew', padx=15, pady=10)
        row += 1
        
        tk.Label(parent, text="Максимальный FPS:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.fps_limit = tk.IntVar(value=self.settings.get('max_fps', 60))
        fps_frame = tk.Frame(parent, bg='#2c2c2c')
        fps_frame.grid(row=row, column=0, sticky='ew', padx=15, pady=5)
        ttk.Scale(fps_frame, from_=1, to=120, orient=tk.HORIZONTAL, variable=self.fps_limit, length=250).pack(side=tk.LEFT)
        self.fps_limit_label = tk.Label(fps_frame, text=str(self.fps_limit.get()), bg='#2c2c2c', fg='#0078d4', width=4)
        self.fps_limit_label.pack(side=tk.LEFT, padx=10)
        self.fps_limit.trace('w', lambda *a: self.fps_limit_label.config(text=str(self.fps_limit.get())))
        row += 1
        
        tk.Label(parent, text="Минимальный размер видео:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.min_video_size = tk.IntVar(value=self.settings.get('min_video_size', 150))
        size_frame = tk.Frame(parent, bg='#2c2c2c')
        size_frame.grid(row=row, column=0, sticky='ew', padx=15, pady=5)
        ttk.Scale(size_frame, from_=80, to=300, orient=tk.HORIZONTAL, variable=self.min_video_size, length=250).pack(side=tk.LEFT)
        self.min_size_label = tk.Label(size_frame, text=str(self.min_video_size.get()), bg='#2c2c2c', fg='#0078d4', width=4)
        self.min_size_label.pack(side=tk.LEFT, padx=10)
        self.min_video_size.trace('w', lambda *a: self.min_size_label.config(text=str(self.min_video_size.get())))
        row += 1
        
        tk.Label(parent, text="Качество масштабирования:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.resize_quality = tk.StringVar(value=self.settings.get('resize_quality', 'Среднее'))
        quality_combo = ttk.Combobox(parent, textvariable=self.resize_quality,
                                     values=['Низкое (быстро)', 'Среднее', 'Высокое (медленно)'],
                                     state='readonly', width=25)
        quality_combo.grid(row=row, column=0, padx=15, pady=5, sticky='w')
        row += 1
        
        tk.Frame(parent, bg='#3c3c3c', height=1).grid(row=row, column=0, sticky='ew', padx=15, pady=10)
        row += 1
        
        tk.Label(parent, text="Размер очереди кадров:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.queue_size = tk.IntVar(value=self.settings.get('queue_size', 1))
        queue_frame = tk.Frame(parent, bg='#2c2c2c')
        queue_frame.grid(row=row, column=0, sticky='ew', padx=15, pady=5)
        ttk.Scale(queue_frame, from_=1, to=5, orient=tk.HORIZONTAL, variable=self.queue_size, length=250).pack(side=tk.LEFT)
        self.queue_label = tk.Label(queue_frame, text=str(self.queue_size.get()), bg='#2c2c2c', fg='#0078d4', width=4)
        self.queue_label.pack(side=tk.LEFT, padx=10)
        self.queue_size.trace('w', lambda *a: self.queue_label.config(text=str(self.queue_size.get())))
        row += 1
        
        tk.Label(parent, text="Порог оптимизации (кол-во видео):", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.optimize_threshold = tk.IntVar(value=self.settings.get('optimize_threshold', 16))
        threshold_frame = tk.Frame(parent, bg='#2c2c2c')
        threshold_frame.grid(row=row, column=0, sticky='ew', padx=15, pady=5)
        ttk.Scale(threshold_frame, from_=4, to=32, orient=tk.HORIZONTAL, variable=self.optimize_threshold, length=250).pack(side=tk.LEFT)
        self.threshold_label = tk.Label(threshold_frame, text=str(self.optimize_threshold.get()), bg='#2c2c2c', fg='#0078d4', width=4)
        self.threshold_label.pack(side=tk.LEFT, padx=10)
        self.optimize_threshold.trace('w', lambda *a: self.threshold_label.config(text=str(self.optimize_threshold.get())))
        row += 1
        
        self.skip_frames = tk.BooleanVar(value=self.settings.get('skip_frames', True))
        tk.Checkbutton(parent, text="Пропускать кадры при высокой нагрузке",
                      variable=self.skip_frames, bg='#2c2c2c', fg='#ffffff',
                      selectcolor='#2c2c2c', font=('Segoe UI', 9)).grid(row=row, column=0, sticky='w', padx=15, pady=5)
        row += 1
        
        tk.Label(parent, text="Цветовая тема:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.theme = tk.StringVar(value=self.settings.get('theme', 'dark'))
        theme_combo = ttk.Combobox(parent, textvariable=self.theme, values=['dark', 'light'],
                                   state='readonly', width=25)
        theme_combo.grid(row=row, column=0, padx=15, pady=5, sticky='w')
        row += 1
        
        tk.Label(parent, text="Прозрачность окна:", bg='#2c2c2c', fg='#ffffff',
                font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='w', padx=15, pady=(10,5))
        row += 1
        
        self.opacity = tk.DoubleVar(value=self.settings.get('opacity', 1.0))
        opacity_frame = tk.Frame(parent, bg='#2c2c2c')
        opacity_frame.grid(row=row, column=0, sticky='ew', padx=15, pady=5)
        ttk.Scale(opacity_frame, from_=0.5, to=1.0, orient=tk.HORIZONTAL, variable=self.opacity, length=250).pack(side=tk.LEFT)
        self.opacity_label = tk.Label(opacity_frame, text=f"{self.opacity.get():.1f}", bg='#2c2c2c', fg='#0078d4', width=4)
        self.opacity_label.pack(side=tk.LEFT, padx=10)
        self.opacity.trace('w', lambda *a: self.opacity_label.config(text=f"{self.opacity.get():.1f}"))
        row += 1
        
        tk.Frame(parent, bg='#3c3c3c', height=1).grid(row=row, column=0, sticky='ew', padx=15, pady=10)
        row += 1
        
        save_btn = tk.Button(parent, text="💾 Применить настройки", command=self.save_settings,
                            bg='#0078d4', fg='white', font=('Segoe UI', 10),
                            padx=20, pady=8, relief=tk.FLAT, cursor='hand2')
        save_btn.grid(row=row, column=0, padx=15, pady=15)
        
    def save_settings(self):
        old_backend = self.settings.get('backend', 'AUTO')
        old_queue_size = self.settings.get('queue_size', 1)
        
        self.settings.update({
            'backend': self.backend.get(),
            'max_fps': self.fps_limit.get(),
            'min_video_size': self.min_video_size.get(),
            'resize_quality': self.resize_quality.get(),
            'queue_size': self.queue_size.get(),
            'optimize_threshold': self.optimize_threshold.get(),
            'skip_frames': self.skip_frames.get(),
            'theme': self.theme.get(),
            'opacity': self.opacity.get(),
        })
        
        self.app.root.attributes('-alpha', self.settings.get('opacity', 1.0))
        if HAS_SV_TTK:
            sv_ttk.set_theme(self.settings.get('theme', 'dark'))
        self.app.save_settings()
        
        if (old_backend != self.settings.get('backend', 'AUTO') or 
            old_queue_size != self.settings.get('queue_size', 1)) and self.app.is_playing:
            self.app.stop_playback()
            self.app.start_playback()
        
        self.show_notification("Настройки сохранены")
        
    def show_notification(self, message):
        notification = tk.Toplevel(self.panel)
        notification.overrideredirect(True)
        notification.configure(bg='#0078d4')
        x = self.panel.winfo_rootx() + self.panel_width//2 - 100
        y = self.panel.winfo_rooty() + 50
        notification.geometry(f"200x40+{x}+{y}")
        tk.Label(notification, text=message, bg='#0078d4', fg='white',
                font=('Segoe UI', 10)).pack(expand=True, fill=tk.BOTH)
        notification.after(1500, notification.destroy)
        
    def show(self):
        if not self.is_visible:
            self.is_visible = True
            self.panel.pack(side=tk.RIGHT, fill=tk.Y, before=self.app.canvas.master)
            self.panel.lift()
            
    def hide(self):
        if self.is_visible:
            self.is_visible = False
            self.panel.pack_forget()
        
    def toggle(self):
        if self.is_visible:
            self.hide()
        else:
            self.show()


class VideoPlayerThread:
    def __init__(self, video_data, fps_control, optimize_flag, settings):
        self.video_data = video_data
        self.fps_control = fps_control
        self.optimize_flag = optimize_flag
        self.settings = settings
        self.is_playing = False
        self.is_paused = False
        self.frame_queue = queue.Queue(maxsize=settings.get('queue_size', 1))
        self.thread = None
        self.cap = None
        self.last_frame_time = 0
        
    def start(self):
        self.is_playing = True
        self.is_paused = False
        self.thread = threading.Thread(target=self._play_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.is_playing = False
        if self.thread:
            self.thread.join(timeout=0.3)
        if self.cap:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
            
    def pause(self):
        self.is_paused = True
        
    def resume(self):
        self.is_paused = False
            
    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None
            
    def _get_video_capture(self, path):
        backend = self.settings.get('backend', 'AUTO')
        try:
            if backend == 'FFMPEG':
                return cv2.VideoCapture(path, cv2.CAP_FFMPEG)
            elif backend == 'MSMF':
                return cv2.VideoCapture(path, cv2.CAP_MSMF)
            elif backend == 'DSHOW':
                return cv2.VideoCapture(path, cv2.CAP_DSHOW)
            else:
                return cv2.VideoCapture(path)
        except:
            return cv2.VideoCapture(path)
            
    def _play_loop(self):
        try:
            self.cap = self._get_video_capture(self.video_data['path'])
            if not self.cap or not self.cap.isOpened():
                return
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30
            target_fps = min(fps, self.fps_control())
            frame_time = 1.0 / target_fps if target_fps > 0 else 0.033
            frame_skip = 0
            while self.is_playing:
                try:
                    if self.is_paused:
                        time.sleep(0.05)
                        continue
                    current_time = time.time()
                    if current_time - self.last_frame_time < frame_time:
                        time.sleep(0.001)
                        continue
                    ret, frame = self.cap.read()
                    if not ret:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                        if not ret:
                            time.sleep(0.01)
                            continue
                    if self.optimize_flag() and self.settings.get('skip_frames', True):
                        threshold = self.settings.get('optimize_threshold', 16)
                        skip_rate = max(1, len(self.video_data.get('videos', [])) // threshold)
                        frame_skip = (frame_skip + 1) % skip_rate
                        if frame_skip != 0:
                            self.last_frame_time = current_time
                            continue
                    quality = self.settings.get('resize_quality', 'Среднее')
                    if quality == 'Низкое (быстро)':
                        interpolation = cv2.INTER_NEAREST
                    elif quality == 'Высокое (медленно)':
                        interpolation = cv2.INTER_LANCZOS4
                    else:
                        interpolation = cv2.INTER_LINEAR
                    if frame.shape[0] != self.video_data['height'] or frame.shape[1] != self.video_data['width']:
                        frame = cv2.resize(frame, (self.video_data['width'], self.video_data['height']), interpolation=interpolation)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    try:
                        if self.frame_queue.full():
                            self.frame_queue.get_nowait()
                        self.frame_queue.put(frame)
                    except:
                        pass
                    self.last_frame_time = current_time
                    target_fps = min(fps, self.fps_control())
                    frame_time = 1.0 / target_fps if target_fps > 0 else 0.033
                except Exception:
                    time.sleep(0.01)
        except Exception:
            pass


class CustomTitleBar:
    def __init__(self, root, app, title="ZVideoGridPlayer"):
        self.root = root
        self.app = app
        self.is_maximized = False
        self.normal_size = None
        self.is_dragging = False
        
        root.overrideredirect(True)
        
        self.title_bar = tk.Frame(root, bg='#1c1c1c', height=32)
        self.title_bar.pack(fill=tk.X)
        
        self.title_bar.bind('<Double-Button-1>', self.toggle_maximize)
        
        self.icon_label = tk.Label(self.title_bar, text="🎬", bg='#1c1c1c', fg='#0078d4', font=('Segoe UI', 12))
        self.icon_label.pack(side=tk.LEFT, padx=(12, 6), pady=6)
        self.icon_label.bind('<Double-Button-1>', self.toggle_maximize)
        
        self.title_label = tk.Label(self.title_bar, text=title, bg='#1c1c1c', fg='#ffffff', font=('Segoe UI', 10))
        self.title_label.pack(side=tk.LEFT, padx=0, pady=6)
        self.title_label.bind('<Double-Button-1>', self.toggle_maximize)
        
        button_bg = '#1c1c1c'
        button_hover_bg = '#2c2c2c'
        button_close_hover_bg = '#e81123'
        
        self.close_btn = tk.Label(self.title_bar, text="✕", bg=button_bg, fg='#ffffff',
                                  font=('Segoe UI', 10), width=3, cursor='hand2')
        self.close_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.close_btn.bind('<Enter>', lambda e: self.close_btn.configure(bg=button_close_hover_bg))
        self.close_btn.bind('<Leave>', lambda e: self.close_btn.configure(bg=button_bg))
        self.close_btn.bind('<Button-1>', lambda e: root.destroy())
        
        self.max_btn = tk.Label(self.title_bar, text="□", bg=button_bg, fg='#ffffff',
                                font=('Segoe UI', 10), width=3, cursor='hand2')
        self.max_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.max_btn.bind('<Enter>', lambda e: self.max_btn.configure(bg=button_hover_bg))
        self.max_btn.bind('<Leave>', lambda e: self.max_btn.configure(bg=button_bg))
        self.max_btn.bind('<Button-1>', self.toggle_maximize)
        
        self.min_btn = tk.Label(self.title_bar, text="─", bg=button_bg, fg='#ffffff',
                                font=('Segoe UI', 12), width=3, cursor='hand2')
        self.min_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.min_btn.bind('<Enter>', lambda e: self.min_btn.configure(bg=button_hover_bg))
        self.min_btn.bind('<Leave>', lambda e: self.min_btn.configure(bg=button_bg))
        self.min_btn.bind('<Button-1>', self.minimize_window)
        
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        self.title_bar.bind('<ButtonRelease-1>', self.stop_move)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<ButtonRelease-1>', self.stop_move)
        self.icon_label.bind('<Button-1>', self.start_move)
        self.icon_label.bind('<B1-Motion>', self.on_move)
        self.icon_label.bind('<ButtonRelease-1>', self.stop_move)
        
        self.x = 0
        self.y = 0
        
        self.setup_resize_handles()
        self.round_corners()
        
        # Отслеживаем восстановление окна
        self.root.bind('<Map>', self.on_window_restore)
        
    def on_window_restore(self, event):
        """При восстановлении окна - убираем белую полосу"""
        self.root.after(50, self.ensure_custom_titlebar)
        
    def ensure_custom_titlebar(self):
        """Гарантируем, что кастомный заголовок виден и нет белой полосы"""
        try:
            if self.root.winfo_viewable():
                self.root.overrideredirect(True)
                self.root.update_idletasks()
                self.root.lift()
        except:
            pass
        
    def setup_resize_handles(self):
        resize_size = 8  # Увеличиваем зону захвата для удобства
        
        self.bottom_right = tk.Frame(self.root, bg='#1c1c1c', cursor='size_nw_se')
        self.bottom_right.place(relx=1.0, rely=1.0, anchor='se', width=resize_size*2, height=resize_size*2)
        self.bottom_right.bind('<ButtonPress-1>', self.start_resize)
        self.bottom_right.bind('<B1-Motion>', self.resize_bottom_right)
        self.bottom_right.bind('<ButtonRelease-1>', self.stop_resize)
        
        self.bottom_left = tk.Frame(self.root, bg='#1c1c1c', cursor='size_ne_sw')
        self.bottom_left.place(relx=0.0, rely=1.0, anchor='sw', width=resize_size*2, height=resize_size*2)
        self.bottom_left.bind('<ButtonPress-1>', self.start_resize)
        self.bottom_left.bind('<B1-Motion>', self.resize_bottom_left)
        self.bottom_left.bind('<ButtonRelease-1>', self.stop_resize)
        
        self.right_edge = tk.Frame(self.root, bg='#1c1c1c', cursor='size_we')
        self.right_edge.place(relx=1.0, rely=0.5, anchor='e', width=resize_size, height=1)
        self.right_edge.bind('<ButtonPress-1>', self.start_resize)
        self.right_edge.bind('<B1-Motion>', self.resize_right)
        self.right_edge.bind('<ButtonRelease-1>', self.stop_resize)
        
        self.bottom_edge = tk.Frame(self.root, bg='#1c1c1c', cursor='size_ns')
        self.bottom_edge.place(relx=0.5, rely=1.0, anchor='s', width=1, height=resize_size)
        self.bottom_edge.bind('<ButtonPress-1>', self.start_resize)
        self.bottom_edge.bind('<B1-Motion>', self.resize_bottom)
        self.bottom_edge.bind('<ButtonRelease-1>', self.stop_resize)
        
    def start_resize(self, event):
        self.app.pause_playback()
        
    def stop_resize(self, event):
        self.app.resume_playback()
        
    def resize_bottom_right(self, event):
        x = max(800, self.root.winfo_pointerx() - self.root.winfo_rootx())
        y = max(600, self.root.winfo_pointery() - self.root.winfo_rooty())
        self.root.geometry(f"{x}x{y}")
        self.app.update_grid_size()
            
    def resize_bottom_left(self, event):
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        width = self.root.winfo_width() + (root_x - x)
        height = max(600, y - root_y)
        if width > 800:
            self.root.geometry(f"{width}x{height}+{x}+{root_y}")
            self.app.update_grid_size()
            
    def resize_right(self, event):
        x = max(800, self.root.winfo_pointerx() - self.root.winfo_rootx())
        self.root.geometry(f"{x}x{self.root.winfo_height()}")
        self.app.update_grid_size()
        
    def resize_bottom(self, event):
        y = max(600, self.root.winfo_pointery() - self.root.winfo_rooty())
        self.root.geometry(f"{self.root.winfo_width()}x{y}")
        self.app.update_grid_size()
        
    def minimize_window(self, event):
        self.app.stop_playback()
        try:
            self.root.overrideredirect(False)
            self.root.iconify()
        except:
            pass
        
    def start_move(self, event):
        self.is_dragging = True
        self.x = event.x
        self.y = event.y
        self.app.pause_playback()
        
    def on_move(self, event):
        if not self.is_maximized and self.is_dragging:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
        
    def stop_move(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.app.resume_playback()
        
    def toggle_maximize(self, event=None):
        if not self.is_maximized:
            self.normal_size = (self.root.winfo_width(), self.root.winfo_height(),
                              self.root.winfo_x(), self.root.winfo_y())
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.max_btn.configure(text="❐")
            self.is_maximized = True
        else:
            if self.normal_size:
                w, h, x, y = self.normal_size
                self.root.geometry(f"{w}x{h}+{x}+{y}")
                self.max_btn.configure(text="□")
                self.is_maximized = False
                self.app.update_grid_size()
        
        # Восстанавливаем кастомный заголовок после разворачивания
        self.root.after(100, self.ensure_custom_titlebar)
            
    def round_corners(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_PREFERENCE = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWM_WINDOW_CORNER_PREFERENCE)),
                ctypes.sizeof(ctypes.c_int)
            )
        except:
            pass


class VideoGridPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("ZVideoGridPlayer")
        self.root.geometry("1300x850")
        self.root.minsize(800, 600)
        self.root.configure(bg='#1c1c1c')
        
        self.settings = self.load_settings()
        self.root.attributes('-alpha', self.settings.get('opacity', 1.0))
        
        self.title_bar = CustomTitleBar(root, self, "ZVideoGridPlayer")
        
        self.main_container = tk.Frame(root, bg='#1c1c1c')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.control_panel = tk.Frame(self.main_container, bg='#1c1c1c', height=120)
        self.control_panel.pack(fill=tk.X, side=tk.TOP)
        self.control_panel.pack_propagate(False)
        self.panel_visible = True
        
        canvas_container = tk.Frame(self.main_container, bg='#1c1c1c')
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, bg='#2b2b2b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#2b2b2b')
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.master = canvas_container
        
        self.settings_panel = SettingsPanel(self.main_container, self.settings, self)
        self.create_control_panel_content(self.control_panel)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.root.bind('<space>', self.toggle_playback)
        self.root.bind('<s>', lambda e: self.stop_playback())
        self.root.bind('<f>', lambda e: self.title_bar.toggle_maximize())
        self.root.bind('<h>', self.toggle_panel)
        self.root.bind('<H>', self.toggle_panel)
        self.root.bind('<F1>', lambda e: self.settings_panel.toggle())
        
        self.video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v')
        self.videos = []
        self.video_threads = []
        self.is_playing = False
        self.cols = 3
        self.show_names = False
        self.updating = False
        self.after_id = None
        self.update_timer = None
        
        if HAS_SV_TTK:
            sv_ttk.set_theme(self.settings.get('theme', 'dark'))
        
        self.root.bind('<Configure>', self.on_window_resize)
        
    def pause_playback(self):
        for thread in self.video_threads:
            thread.pause()
            
    def resume_playback(self):
        for thread in self.video_threads:
            thread.resume()
        
    def toggle_panel(self, event=None):
        if self.panel_visible:
            self.control_panel.pack_forget()
            self.panel_visible = False
        else:
            self.control_panel.pack(fill=tk.X, side=tk.TOP, before=self.canvas.master)
            self.panel_visible = True
        
    def load_settings(self):
        default_settings = {
            'backend': 'AUTO', 'max_fps': 60, 'min_video_size': 150,
            'resize_quality': 'Среднее', 'queue_size': 1, 'thread_timeout': 0.3,
            'optimize_threshold': 16, 'skip_frames': True, 'theme': 'dark',
            'opacity': 1.0, 'auto_save': True
        }
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
        except:
            pass
        return default_settings
        
    def save_settings(self):
        if self.settings.get('auto_save', True):
            try:
                with open('settings.json', 'w') as f:
                    json.dump(self.settings, f, indent=2)
            except:
                pass
                
    def toggle_playback(self, event=None):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
            
    def create_control_panel_content(self, parent):
        btn_style = {
            'bg': '#2c2c2c', 'fg': '#ffffff', 'font': ('Segoe UI', 10),
            'padx': 15, 'pady': 8, 'relief': tk.FLAT, 'cursor': 'hand2',
            'activebackground': '#3c3c3c', 'activeforeground': '#ffffff'
        }
        
        button_frame = tk.Frame(parent, bg='#1c1c1c')
        button_frame.pack(fill=tk.X, pady=(10, 8))
        
        self.load_btn = tk.Button(button_frame, text="📁 Выбрать папку", command=self.load_folder, **btn_style)
        self.load_btn.pack(side=tk.LEFT, padx=4)
        
        self.start_btn = tk.Button(button_frame, text="▶ Старт (Пробел)", command=self.start_playback, **btn_style)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        
        self.stop_btn = tk.Button(button_frame, text="⏹ Стоп (S)", command=self.stop_playback, **btn_style)
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        
        self.settings_btn = tk.Button(button_frame, text="⚙️ Настройки (F1)", command=self.settings_panel.toggle, **btn_style)
        self.settings_btn.pack(side=tk.LEFT, padx=4)
        
        self.hide_btn = tk.Button(button_frame, text="🔽 Скрыть панель (H)", command=self.toggle_panel, **btn_style)
        self.hide_btn.pack(side=tk.LEFT, padx=4)
        
        self.info_label = tk.Label(button_frame, text="Нет загруженных видео", bg='#1c1c1c', fg='#8c8c8c', font=('Segoe UI', 10))
        self.info_label.pack(side=tk.LEFT, padx=20)
        
        quick_frame = tk.Frame(parent, bg='#1c1c1c')
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        fps_frame = tk.Frame(quick_frame, bg='#1c1c1c')
        fps_frame.pack(side=tk.LEFT, padx=8)
        tk.Label(fps_frame, text="🎬 FPS:", bg='#1c1c1c', fg='#ffffff', font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=4)
        
        self.fps_var = tk.IntVar(value=30)
        self.fps_slider = ttk.Scale(fps_frame, from_=1, to=60, orient=tk.HORIZONTAL, variable=self.fps_var, length=150)
        self.fps_slider.pack(side=tk.LEFT, padx=8)
        self.fps_label = tk.Label(fps_frame, text="30", width=4, bg='#1c1c1c', fg='#ffffff', font=('Segoe UI', 10, 'bold'))
        self.fps_label.pack(side=tk.LEFT)
        self.fps_slider.configure(command=lambda x: self.fps_label.configure(text=str(int(float(x)))))
        
        cols_frame = tk.Frame(quick_frame, bg='#1c1c1c')
        cols_frame.pack(side=tk.LEFT, padx=20)
        tk.Label(cols_frame, text="📐 Колонок:", bg='#1c1c1c', fg='#ffffff', font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=4)
        
        self.cols_var = tk.IntVar(value=3)
        self.cols_slider = ttk.Scale(cols_frame, from_=1, to=8, orient=tk.HORIZONTAL, variable=self.cols_var, length=150)
        self.cols_slider.pack(side=tk.LEFT, padx=8)
        self.cols_label = tk.Label(cols_frame, text="3", width=4, bg='#1c1c1c', fg='#ffffff', font=('Segoe UI', 10, 'bold'))
        self.cols_label.pack(side=tk.LEFT)
        self.cols_slider.configure(command=lambda x: self.cols_label.configure(text=str(int(float(x)))))
        
        apply_btn = tk.Button(cols_frame, text="Применить", command=self.apply_grid_size, **btn_style)
        apply_btn.pack(side=tk.LEFT, padx=8)
        
        self.show_names_var = tk.BooleanVar(value=False)
        self.show_names_check = tk.Checkbutton(quick_frame, text="📝 Имена файлов", variable=self.show_names_var,
                                             command=self.toggle_names_display, bg='#1c1c1c', fg='#ffffff',
                                             selectcolor='#1c1c1c', activebackground='#1c1c1c', font=('Segoe UI', 10))
        self.show_names_check.pack(side=tk.LEFT, padx=10)
        
        self.optimize_var = tk.BooleanVar(value=True)
        self.optimize_check = tk.Checkbutton(quick_frame, text="⚡ Оптимизация", variable=self.optimize_var,
                                           bg='#1c1c1c', fg='#ffffff', selectcolor='#1c1c1c',
                                           activebackground='#1c1c1c', font=('Segoe UI', 10))
        self.optimize_check.pack(side=tk.LEFT, padx=10)
        
        hotkeys_label = tk.Label(quick_frame, text="⌨️ Пробел:Старт/Стоп | S:Стоп | F:Полный экран | H:Скрыть панель | F1:Настройки", 
                                 bg='#1c1c1c', fg='#8c8c8c', font=('Segoe UI', 9))
        hotkeys_label.pack(side=tk.RIGHT, padx=10)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_window_resize(self, event):
        if event.widget == self.root and not self.updating:
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.after_id = self.root.after(100, self.update_grid_size)
    
    def update_grid_size(self):
        if self.videos and not self.updating:
            self.rearrange_grid(keep_playing=True)
    
    def toggle_names_display(self):
        self.show_names = self.show_names_var.get()
        for video in self.videos:
            if 'name_label' in video:
                if self.show_names:
                    video['name_label'].pack()
                else:
                    video['name_label'].pack_forget()
    
    def apply_grid_size(self):
        if self.videos and not self.updating:
            new_cols = self.cols_var.get()
            if new_cols != self.cols:
                self.cols = new_cols
                self.rearrange_grid()
    
    def rearrange_grid(self, keep_playing=False):
        if not self.videos or self.updating:
            return
        self.updating = True
        was_playing = self.is_playing if not keep_playing else self.is_playing
        if was_playing:
            self.stop_playback()
        current_videos = self.videos.copy()
        for video in current_videos:
            if video['frame']:
                video['frame'].destroy()
        self.videos = []
        cols = self.cols
        canvas_width = self.canvas.winfo_width() - 20
        if canvas_width < 100:
            canvas_width = 1200
        min_size = self.settings.get('min_video_size', 150)
        video_width = max(min_size, (canvas_width - (cols * 6)) // cols)
        video_height = int(video_width * 0.75)
        for i, video_data in enumerate(current_videos):
            row = i // cols
            col = i % cols
            frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b', relief=tk.SUNKEN, bd=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            name_label = tk.Label(frame, text=video_data['name'], bg='#2b2b2b', fg='#8c8c8c',
                                 wraplength=video_width, font=('Segoe UI', 9))
            if self.show_names:
                name_label.pack()
            video_canvas = tk.Canvas(frame, width=video_width, height=video_height, bg='black', 
                                     highlightthickness=1, highlightbackground='#404040')
            video_canvas.pack(padx=2, pady=2, expand=True)
            video_data['frame'] = frame
            video_data['canvas'] = video_canvas
            video_data['name_label'] = name_label
            video_data['width'] = video_width
            video_data['height'] = video_height
            self.videos.append(video_data)
        self.info_label.config(text=f"📹 {len(self.videos)} | {self.cols} колонок")
        if was_playing:
            self.start_playback()
        self.updating = False
    
    def load_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        video_files = set()
        for ext in self.video_extensions:
            video_files.update(Path(folder).glob(f"*{ext}"))
            video_files.update(Path(folder).glob(f"*{ext.upper()}"))
        video_files = sorted(list(video_files))
        seen_names = set()
        unique_videos = []
        for video_path in video_files:
            if video_path.name not in seen_names:
                seen_names.add(video_path.name)
                unique_videos.append(video_path)
        if not unique_videos:
            messagebox.showwarning("Предупреждение", "Видео не найдены!")
            return
        self.clear_videos()
        self.videos = []
        self.cols = self.cols_var.get()
        canvas_width = self.canvas.winfo_width() - 20
        if canvas_width < 100:
            canvas_width = 1200
        min_size = self.settings.get('min_video_size', 150)
        video_width = max(min_size, (canvas_width - (self.cols * 6)) // self.cols)
        video_height = int(video_width * 0.75)
        for i, video_path in enumerate(unique_videos):
            row = i // self.cols
            col = i % self.cols
            frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b', relief=tk.SUNKEN, bd=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            name_label = tk.Label(frame, text=video_path.name, bg='#2b2b2b', fg='#8c8c8c',
                                 wraplength=video_width, font=('Segoe UI', 9))
            if self.show_names:
                name_label.pack()
            video_canvas = tk.Canvas(frame, width=video_width, height=video_height, bg='black',
                                     highlightthickness=1, highlightbackground='#404040')
            video_canvas.pack(padx=2, pady=2, expand=True)
            self.videos.append({
                'path': str(video_path), 'frame': frame, 'canvas': video_canvas,
                'name_label': name_label, 'name': video_path.name, 'width': video_width,
                'height': video_height, 'valid': True, 'videos': None
            })
        for video in self.videos:
            video['videos'] = self.videos
        self.info_label.config(text=f"📹 {len(self.videos)} | {self.cols} колонок")
    
    def clear_videos(self):
        self.stop_playback()
        for video in self.videos:
            if video['frame']:
                try:
                    video['frame'].destroy()
                except:
                    pass
        self.videos.clear()
        self.video_threads.clear()
    
    def start_playback(self):
        if not self.videos:
            messagebox.showwarning("Предупреждение", "Сначала загрузите видео!")
            return
        if self.is_playing:
            return
        self.video_threads = []
        for video in self.videos:
            thread = VideoPlayerThread(video, lambda: self.fps_var.get(), lambda: self.optimize_var.get(), self.settings)
            thread.start()
            video['valid'] = True
            self.video_threads.append(thread)
        if not self.video_threads:
            messagebox.showerror("Ошибка", "Не удалось открыть видео!")
            return
        self.is_playing = True
        self._start_update_timer()
    
    def _start_update_timer(self):
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        self._update_canvas_all()
    
    def _update_canvas_all(self):
        if not self.is_playing:
            return
        for idx, thread in enumerate(self.video_threads):
            if idx < len(self.videos):
                frame = thread.get_frame()
                if frame is not None:
                    try:
                        img = Image.fromarray(frame)
                        imgtk = ImageTk.PhotoImage(image=img)
                        video = self.videos[idx]
                        if video['canvas']:
                            video['canvas'].delete("all")
                            video['canvas'].create_image(0, 0, anchor=tk.NW, image=imgtk)
                            video['canvas'].image = imgtk
                    except:
                        pass
        fps = self.fps_var.get()
        delay = int(1000 / max(1, fps))
        self.update_timer = self.root.after(delay, self._update_canvas_all)
    
    def stop_playback(self):
        self.is_playing = False
        if self.update_timer:
            try:
                self.root.after_cancel(self.update_timer)
            except:
                pass
            self.update_timer = None
        for thread in self.video_threads:
            thread.stop()
        self.video_threads.clear()
    
    def on_closing(self):
        """Закрытие окна - быстрое и без задержек"""
        self.is_playing = False
        if self.update_timer:
            try:
                self.root.after_cancel(self.update_timer)
            except:
                pass
            self.update_timer = None
        for thread in self.video_threads:
            try:
                thread.is_playing = False
                if thread.cap:
                    thread.cap.release()
            except:
                pass
        self.video_threads.clear()
        self.save_settings()
        try:
            self.root.destroy()
        except:
            pass
        sys.exit(0)


def main():
    import warnings
    warnings.filterwarnings("ignore")
    
    root = tk.Tk()
    icon_path = get_icon_path()
    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except:
            try:
                icon_img = ImageTk.PhotoImage(file=icon_path)
                root.iconphoto(True, icon_img)
            except:
                pass
    
    app = VideoGridPlayer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.update_idletasks()
    width = 1300
    height = 850
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()