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
import subprocess

# Отключаем предупреждения OpenCV
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOG_LEVEL'] = '-8'
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'

# Попытка импорта PyAV для лучшей поддержки H264
try:
    import av
    HAS_PYAV = True
except ImportError:
    HAS_PYAV = False
    print("Для лучшей поддержки H264 установите: pip install av")

# Попытка импортировать дополнительные библиотеки для Win11 стиля
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

class CustomTitleBar:
    """Кастомный заголовок окна в стиле Windows 11"""
    def __init__(self, root, app, title="ZVideoGridPlayer"):
        self.root = root
        self.app = app
        self.title_text = title
        self.is_maximized = False
        self.normal_size = None
        
        # Убираем стандартный заголовок
        root.overrideredirect(True)
        
        # Создаем кастомный заголовок
        self.title_bar = tk.Frame(root, bg='#1c1c1c', height=32)
        self.title_bar.pack(fill=tk.X)
        
        # Привязываем двойной клик для разворачивания
        self.title_bar.bind('<Double-Button-1>', self.toggle_maximize)
        
        # Иконка приложения
        self.icon_label = tk.Label(self.title_bar, text="🎬", 
                                   bg='#1c1c1c', fg='#0078d4',
                                   font=('Segoe UI', 12))
        self.icon_label.pack(side=tk.LEFT, padx=(12, 6), pady=6)
        self.icon_label.bind('<Double-Button-1>', self.toggle_maximize)
        
        # Заголовок окна
        self.title_label = tk.Label(self.title_bar, text=title, 
                                    bg='#1c1c1c', fg='#ffffff', 
                                    font=('Segoe UI', 10))
        self.title_label.pack(side=tk.LEFT, padx=0, pady=6)
        self.title_label.bind('<Double-Button-1>', self.toggle_maximize)
        
        # Кнопки управления
        button_bg = '#1c1c1c'
        button_hover_bg = '#2c2c2c'
        button_close_hover_bg = '#e81123'
        
        # Кнопка закрытия
        self.close_btn = tk.Label(self.title_bar, text="✕", bg=button_bg, fg='#ffffff',
                                  font=('Segoe UI', 10), width=3, cursor='hand2')
        self.close_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.close_btn.bind('<Enter>', lambda e: self.close_btn.configure(bg=button_close_hover_bg))
        self.close_btn.bind('<Leave>', lambda e: self.close_btn.configure(bg=button_bg))
        self.close_btn.bind('<Button-1>', lambda e: root.destroy())
        
        # Кнопка разворачивания
        self.max_btn = tk.Label(self.title_bar, text="□", bg=button_bg, fg='#ffffff',
                                font=('Segoe UI', 10), width=3, cursor='hand2')
        self.max_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.max_btn.bind('<Enter>', lambda e: self.max_btn.configure(bg=button_hover_bg))
        self.max_btn.bind('<Leave>', lambda e: self.max_btn.configure(bg=button_bg))
        self.max_btn.bind('<Button-1>', self.toggle_maximize)
        
        # Кнопка минимизации
        self.min_btn = tk.Label(self.title_bar, text="─", bg=button_bg, fg='#ffffff',
                                font=('Segoe UI', 12), width=3, cursor='hand2')
        self.min_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.min_btn.bind('<Enter>', lambda e: self.min_btn.configure(bg=button_hover_bg))
        self.min_btn.bind('<Leave>', lambda e: self.min_btn.configure(bg=button_bg))
        self.min_btn.bind('<Button-1>', self.minimize_window)
        
        # Для перетаскивания окна
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        self.icon_label.bind('<Button-1>', self.start_move)
        self.icon_label.bind('<B1-Motion>', self.on_move)
        
        self.x = 0
        self.y = 0
        
        # Для изменения размера окна
        self.setup_resize_handles()
        
        # Закругляем углы окна
        self.round_corners()
        
        # Отслеживаем состояние окна
        self.root.bind('<Map>', self.on_window_restore)
        
    def on_window_restore(self, event):
        """При восстановлении окна"""
        self.root.after(50, self.ensure_custom_titlebar)
        
    def ensure_custom_titlebar(self):
        """Гарантируем, что кастомный заголовок виден"""
        try:
            if self.root.winfo_viewable():
                self.root.overrideredirect(True)
                self.root.lift()
                self.root.update_idletasks()
        except:
            pass
        
    def setup_resize_handles(self):
        """Добавление возможности изменения размера окна"""
        resize_size = 6
        
        # Нижний правый угол
        self.bottom_right = tk.Frame(self.root, bg='#1c1c1c', cursor='size_nw_se')
        self.bottom_right.place(relx=1.0, rely=1.0, anchor='se', width=resize_size*2, height=resize_size*2)
        self.bottom_right.bind('<B1-Motion>', self.resize_bottom_right)
        
        # Нижний левый угол
        self.bottom_left = tk.Frame(self.root, bg='#1c1c1c', cursor='size_ne_sw')
        self.bottom_left.place(relx=0.0, rely=1.0, anchor='sw', width=resize_size*2, height=resize_size*2)
        self.bottom_left.bind('<B1-Motion>', self.resize_bottom_left)
        
        # Правый край
        self.right_edge = tk.Frame(self.root, bg='#1c1c1c', cursor='size_we')
        self.right_edge.place(relx=1.0, rely=0.5, anchor='e', width=resize_size, height=1)
        self.right_edge.bind('<B1-Motion>', self.resize_right)
        
        # Нижний край
        self.bottom_edge = tk.Frame(self.root, bg='#1c1c1c', cursor='size_ns')
        self.bottom_edge.place(relx=0.5, rely=1.0, anchor='s', width=1, height=resize_size)
        self.bottom_edge.bind('<B1-Motion>', self.resize_bottom)
        
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
        """Минимизация окна"""
        self.app.stop_playback()
        
        try:
            self.root.overrideredirect(False)
            self.root.iconify()
        except:
            pass
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        if not self.is_maximized:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
        
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
        
        self.root.after(100, self.ensure_custom_titlebar)
            
    def round_corners(self):
        """Закругление углов окна"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_PREFERENCE = 2
            
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
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
        
        # Устанавливаем минимальный размер окна
        self.root.minsize(800, 600)
        
        # Устанавливаем цвет фона
        self.root.configure(bg='#1c1c1c')
        
        # Создаем кастомный заголовок
        self.title_bar = CustomTitleBar(root, self, "ZVideoGridPlayer")
        
        # Поддерживаемые форматы видео
        self.video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mp4v')
        
        # Доступные бэкенды с понятными названиями
        self.backend_options = {
            'AUTO': 'Авто (рекомендуется)',
            'FFMPEG_SW': 'FFMPEG (CPU, стабильный)',
            'FFMPEG_HW': 'FFMPEG (аппаратное ускорение)',
        }
        
        # Добавляем PyAV если доступен
        if HAS_PYAV:
            self.backend_options['PYAV'] = 'PyAV (H264 оптимизированный)'
        
        # Текущий выбранный бэкенд
        self.current_backend = tk.StringVar(value='AUTO')
        
        # Список видео и их элементов
        self.videos = []
        self.is_playing = False
        self.play_thread = None
        self.cols = 3
        self.show_names = False
        self.frame_skip_counter = 0
        
        # Создаем основной контент
        self.create_main_content()
        
        # Настройка для Windows 11
        self.setup_windows11_style()
        
        # Привязываем событие изменения размера окна
        self.root.bind('<Configure>', self.on_window_resize)
        
        # Применяем тему Windows 11 если доступна
        if HAS_SV_TTK:
            sv_ttk.set_theme("dark")
        
        # Задержка для обновления размеров
        self.after_id = None
        
        # Флаг для блокировки обновлений
        self.updating = False
        
        # Проверяем наличие аппаратного ускорения
        self.check_hardware_acceleration()
        
    def check_hardware_acceleration(self):
        """Проверка наличия аппаратного ускорения"""
        try:
            # Проверяем CUDA
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                print("CUDA доступен")
                self.backend_options['FFMPEG_HW'] = 'FFMPEG (CUDA)'
            
            # Проверяем Intel Media SDK
            test_cap = cv2.VideoCapture(0, cv2.CAP_INTEL_MFX)
            if test_cap.isOpened():
                print("Intel Media SDK доступен")
                test_cap.release()
        except:
            pass
    
    def create_main_content(self):
        """Создание основного контента окна"""
        main_frame = tk.Frame(self.root, bg='#1c1c1c')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        
        # Верхняя панель с кнопками
        self.create_control_panel(main_frame)
        
        # Создание canvas с прокруткой
        canvas_container = tk.Frame(main_frame, bg='#1c1c1c')
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, 
                               bg='#2b2b2b',
                               highlightthickness=0)
        
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='#2b2b2b')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Привязка прокрутки
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def create_control_panel(self, parent):
        """Создание панели управления"""
        control_frame = tk.Frame(parent, bg='#1c1c1c')
        control_frame.pack(fill=tk.X, pady=(0, 12))
        
        btn_style = {
            'bg': '#2c2c2c',
            'fg': '#ffffff',
            'font': ('Segoe UI', 10),
            'padx': 15,
            'pady': 8,
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'activebackground': '#3c3c3c',
            'activeforeground': '#ffffff'
        }
        
        # Первая строка кнопок
        button_frame = tk.Frame(control_frame, bg='#1c1c1c')
        button_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.load_btn = tk.Button(button_frame, text="📁 Выбрать папку", 
                                 command=self.load_folder, **btn_style)
        self.load_btn.pack(side=tk.LEFT, padx=4)
        
        self.start_btn = tk.Button(button_frame, text="▶ Старт", 
                                  command=self.start_playback, **btn_style)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        
        self.stop_btn = tk.Button(button_frame, text="⏹ Стоп", 
                                 command=self.stop_playback, **btn_style)
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        
        # Информационная метка
        self.info_label = tk.Label(button_frame, text="Нет загруженных видео", 
                                  bg='#1c1c1c', fg='#8c8c8c',
                                  font=('Segoe UI', 10))
        self.info_label.pack(side=tk.LEFT, padx=20)
        
        # Вторая строка - настройки
        settings_frame = tk.Frame(control_frame, bg='#1c1c1c')
        settings_frame.pack(fill=tk.X)
        
        # FPS контрол
        fps_frame = tk.Frame(settings_frame, bg='#1c1c1c')
        fps_frame.pack(side=tk.LEFT, padx=8)
        
        tk.Label(fps_frame, text="🎬 FPS:", bg='#1c1c1c', fg='#ffffff',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=4)
        
        self.fps_var = tk.IntVar(value=30)
        self.fps_slider = ttk.Scale(fps_frame, from_=1, to=60, 
                                   orient=tk.HORIZONTAL, 
                                   variable=self.fps_var,
                                   length=150)
        self.fps_slider.pack(side=tk.LEFT, padx=8)
        
        self.fps_label = tk.Label(fps_frame, text="30", width=4,
                                 bg='#1c1c1c', fg='#ffffff',
                                 font=('Segoe UI', 10, 'bold'))
        self.fps_label.pack(side=tk.LEFT)
        self.fps_slider.configure(command=lambda x: self.fps_label.configure(text=str(int(float(x)))))
        
        # Колонки контрол
        cols_frame = tk.Frame(settings_frame, bg='#1c1c1c')
        cols_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(cols_frame, text="📐 Колонок:", bg='#1c1c1c', fg='#ffffff',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=4)
        
        self.cols_var = tk.IntVar(value=3)
        self.cols_slider = ttk.Scale(cols_frame, from_=1, to=8, 
                                    orient=tk.HORIZONTAL, 
                                    variable=self.cols_var,
                                    length=150)
        self.cols_slider.pack(side=tk.LEFT, padx=8)
        
        self.cols_label = tk.Label(cols_frame, text="3", width=4,
                                  bg='#1c1c1c', fg='#ffffff',
                                  font=('Segoe UI', 10, 'bold'))
        self.cols_label.pack(side=tk.LEFT)
        self.cols_slider.configure(command=lambda x: self.cols_label.configure(text=str(int(float(x)))))
        
        apply_btn = tk.Button(cols_frame, text="Применить", 
                            command=self.apply_grid_size, **btn_style)
        apply_btn.pack(side=tk.LEFT, padx=8)
        
        # Выбор бэкенда
        backend_frame = tk.Frame(settings_frame, bg='#1c1c1c')
        backend_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(backend_frame, text="🎞 Кодек:", bg='#1c1c1c', fg='#ffffff',
                font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=4)
        
        backend_values = list(self.backend_options.values())
        self.backend_combo = ttk.Combobox(backend_frame, 
                                          values=backend_values,
                                          state='readonly',
                                          width=32)
        self.backend_combo.pack(side=tk.LEFT, padx=4)
        self.backend_combo.set(self.backend_options['AUTO'])
        self.backend_combo.bind('<<ComboboxSelected>>', self.on_backend_change)
        
        # Чекбокс для имен файлов
        self.show_names_var = tk.BooleanVar(value=False)
        self.show_names_check = tk.Checkbutton(settings_frame, 
                                             text="📝 Имена файлов", 
                                             variable=self.show_names_var,
                                             command=self.toggle_names_display,
                                             bg='#1c1c1c', fg='#ffffff',
                                             selectcolor='#1c1c1c',
                                             activebackground='#1c1c1c',
                                             font=('Segoe UI', 10))
        self.show_names_check.pack(side=tk.LEFT, padx=10)
        
        # Чекбокс для оптимизации
        self.optimize_var = tk.BooleanVar(value=True)
        self.optimize_check = tk.Checkbutton(settings_frame, 
                                             text="⚡ Оптимизация", 
                                             variable=self.optimize_var,
                                             bg='#1c1c1c', fg='#ffffff',
                                             selectcolor='#1c1c1c',
                                             activebackground='#1c1c1c',
                                             font=('Segoe UI', 10))
        self.optimize_check.pack(side=tk.LEFT, padx=10)
        
        # Информация о H264
        h264_info = tk.Label(settings_frame, text="🎥 H264/AVC поддержка", 
                            bg='#1c1c1c', fg='#0078d4',
                            font=('Segoe UI', 9))
        h264_info.pack(side=tk.RIGHT, padx=10)
        
    def on_backend_change(self, event):
        """При смене бэкенда"""
        selected_display = self.backend_combo.get()
        for backend_id, display_name in self.backend_options.items():
            if display_name == selected_display:
                self.current_backend.set(backend_id)
                break
        
        if self.videos:
            result = messagebox.askyesno("Смена кодека", 
                                        "Для применения нового кодека нужно перезагрузить видео. Перезагрузить?")
            if result:
                self.reload_videos()
    
    def get_video_capture(self, path):
        """Создание VideoCapture с выбранным бэкендом с оптимизацией для H264"""
        backend = self.current_backend.get()
        
        try:
            if backend == 'PYAV' and HAS_PYAV:
                # Используем PyAV для лучшей поддержки H264
                try:
                    container = av.open(path)
                    stream = container.streams.video[0]
                    return PyAVCapture(container, stream)
                except:
                    # Fallback на OpenCV
                    return cv2.VideoCapture(path)
                    
            elif backend == 'FFMPEG_HW':
                # Пробуем аппаратное ускорение
                # Windows: DXVA2
                # NVIDIA: CUDA
                # Intel: QSV
                
                # Пробуем разные варианты аппаратного ускорения
                hw_options = [
                    ('h264_cuvid', 'cuda'),  # NVIDIA
                    ('h264_qsv', 'qsv'),      # Intel
                    ('h264_dxva2', 'dxva2'),  # Windows
                ]
                
                for hw_codec, hw_device in hw_options:
                    try:
                        cap = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
                        if cap.isOpened():
                            # Устанавливаем опции для аппаратного ускорения
                            cap.set(cv2.CAP_PROP_HW_ACCELERATION, 1)
                            return cap
                    except:
                        continue
                
                # Если не получилось, используем обычный FFMPEG
                return cv2.VideoCapture(path, cv2.CAP_FFMPEG)
                
            elif backend == 'FFMPEG_SW':
                # Используем FFMPEG с программным декодированием
                cap = cv2.VideoCapture(path, cv2.CAP_FFMPEG)
                if cap.isOpened():
                    return cap
                return cv2.VideoCapture(path)
                
            else:  # AUTO
                # Пробуем PyAV если доступен
                if HAS_PYAV:
                    try:
                        container = av.open(path)
                        stream = container.streams.video[0]
                        return PyAVCapture(container, stream)
                    except:
                        pass
                
                # Стандартный OpenCV
                cap = cv2.VideoCapture(path)
                if cap.isOpened():
                    return cap
                
                # Пробуем FFMPEG напрямую
                return cv2.VideoCapture(path, cv2.CAP_FFMPEG)
                
        except Exception as e:
            print(f"Ошибка открытия видео {path}: {e}")
            return cv2.VideoCapture(path)
    
    def reload_videos(self):
        """Перезагрузка видео с новым кодеком"""
        if not self.videos:
            return
        
        self.updating = True
        video_paths = [(v['path'], v['name']) for v in self.videos]
        was_playing = self.is_playing
        
        if was_playing:
            self.stop_playback()
        
        self.clear_videos()
        
        self.cols = self.cols_var.get()
        canvas_width = self.canvas.winfo_width() - 20
        if canvas_width < 100:
            canvas_width = 1200
        
        video_width = max(150, (canvas_width - (self.cols * 6)) // self.cols)
        video_height = int(video_width * 0.75)
        
        for i, (path, name) in enumerate(video_paths):
            row = i // self.cols
            col = i % self.cols
            
            frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b', relief=tk.SUNKEN, bd=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            name_label = tk.Label(frame, text=name, 
                                 bg='#2b2b2b', fg='#8c8c8c',
                                 wraplength=video_width, font=('Segoe UI', 9))
            
            if self.show_names:
                name_label.pack()
            
            video_canvas = tk.Canvas(frame, width=video_width, height=video_height, 
                                     bg='black', highlightthickness=1,
                                     highlightbackground='#404040')
            video_canvas.pack(padx=2, pady=2, expand=True)
            
            self.videos.append({
                'path': path,
                'frame': frame,
                'canvas': video_canvas,
                'name_label': name_label,
                'cap': None,
                'fps': 0,
                'name': name,
                'width': video_width,
                'height': video_height,
                'valid': True
            })
        
        self.info_label.config(text=f"📹 {len(self.videos)} | {self.cols} колонок | {self.backend_combo.get()}")
        
        if was_playing:
            self.start_playback()
        
        self.updating = False
    
    def setup_windows11_style(self):
        """Настройка стиля Windows 11"""
        try:
            self.root.tk.call('tk', 'scaling', 1.2)
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
        except:
            pass
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_window_resize(self, event):
        """Обработка изменения размера окна"""
        if event.widget == self.root and not self.updating:
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.after_id = self.root.after(100, self.update_grid_size)
    
    def update_grid_size(self):
        """Обновление размеров видео при изменении окна"""
        if self.videos and not self.updating:
            self.rearrange_grid(keep_playing=True)
    
    def toggle_names_display(self):
        """Переключение отображения имен файлов"""
        self.show_names = self.show_names_var.get()
        for video in self.videos:
            if 'name_label' in video:
                if self.show_names:
                    video['name_label'].pack()
                else:
                    video['name_label'].pack_forget()
    
    def apply_grid_size(self):
        """Применение нового размера сетки"""
        if self.videos and not self.updating:
            new_cols = self.cols_var.get()
            if new_cols != self.cols:
                self.cols = new_cols
                self.rearrange_grid()
    
    def rearrange_grid(self, keep_playing=False):
        """Перестроение сетки"""
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
        
        video_width = max(150, (canvas_width - (cols * 6)) // cols)
        video_height = int(video_width * 0.75)
        
        for i, video_data in enumerate(current_videos):
            row = i // cols
            col = i % cols
            
            frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b', relief=tk.SUNKEN, bd=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            name_label = tk.Label(frame, text=video_data['name'], 
                                 bg='#2b2b2b', fg='#8c8c8c',
                                 wraplength=video_width, font=('Segoe UI', 9))
            
            if self.show_names:
                name_label.pack()
            
            video_canvas = tk.Canvas(frame, width=video_width, height=video_height, 
                                     bg='black', highlightthickness=1,
                                     highlightbackground='#404040')
            video_canvas.pack(padx=2, pady=2, expand=True)
            
            video_data['frame'] = frame
            video_data['canvas'] = video_canvas
            video_data['name_label'] = name_label
            video_data['width'] = video_width
            video_data['height'] = video_height
            self.videos.append(video_data)
        
        self.info_label.config(text=f"📹 {len(self.videos)} | {self.cols} колонок | {self.backend_combo.get()}")
        
        if was_playing:
            self.start_playback()
        
        self.updating = False
    
    def load_folder(self):
        """Загрузка видео из папки"""
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
        
        video_width = max(150, (canvas_width - (self.cols * 6)) // self.cols)
        video_height = int(video_width * 0.75)
        
        for i, video_path in enumerate(unique_videos):
            row = i // self.cols
            col = i % self.cols
            
            frame = tk.Frame(self.scrollable_frame, bg='#2b2b2b', relief=tk.SUNKEN, bd=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            name_label = tk.Label(frame, text=video_path.name, 
                                 bg='#2b2b2b', fg='#8c8c8c',
                                 wraplength=video_width, font=('Segoe UI', 9))
            
            if self.show_names:
                name_label.pack()
            
            video_canvas = tk.Canvas(frame, width=video_width, height=video_height, 
                                     bg='black', highlightthickness=1,
                                     highlightbackground='#404040')
            video_canvas.pack(padx=2, pady=2, expand=True)
            
            self.videos.append({
                'path': str(video_path),
                'frame': frame,
                'canvas': video_canvas,
                'name_label': name_label,
                'cap': None,
                'fps': 0,
                'name': video_path.name,
                'width': video_width,
                'height': video_height,
                'valid': True
            })
            
        self.info_label.config(text=f"📹 {len(self.videos)} | {self.cols} колонок | {self.backend_combo.get()}")
    
    def clear_videos(self):
        """Очистка видео"""
        self.stop_playback()
        for video in self.videos:
            if video['cap']:
                try:
                    video['cap'].release()
                except:
                    pass
            if video['frame']:
                try:
                    video['frame'].destroy()
                except:
                    pass
        self.videos.clear()
    
    def start_playback(self):
        """Запуск воспроизведения"""
        if not self.videos:
            messagebox.showwarning("Предупреждение", "Сначала загрузите видео!")
            return
            
        if self.is_playing:
            return
            
        valid_videos = []
        for video in self.videos:
            if video['cap']:
                try:
                    video['cap'].release()
                except:
                    pass
            try:
                video['cap'] = self.get_video_capture(video['path'])
                if not video['cap'].isOpened():
                    print(f"Не удалось открыть: {video['name']}")
                    video['valid'] = False
                    continue
                
                video['fps'] = video['cap'].get(cv2.CAP_PROP_FPS)
                if video['fps'] <= 0:
                    video['fps'] = 30
                video['valid'] = True
                valid_videos.append(video)
            except Exception as e:
                print(f"Ошибка: {video['name']} - {e}")
                video['valid'] = False
                continue
        
        if not valid_videos:
            messagebox.showerror("Ошибка", "Не удалось открыть видео!")
            return
            
        self.is_playing = True
        self.frame_skip_counter = 0
        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()
    
    def stop_playback(self):
        """Остановка воспроизведения"""
        self.is_playing = False
        if self.play_thread:
            try:
                self.play_thread.join(timeout=0.5)
            except:
                pass
        for video in self.videos:
            if video.get('cap'):
                try:
                    video['cap'].release()
                except:
                    pass
                video['cap'] = None
    
    def _play_loop(self):
        """Цикл воспроизведения с оптимизацией для H264"""
        target_fps = self.fps_var.get()
        optimize = self.optimize_var.get()
        
        # Ограничиваем FPS для стабильности
        if optimize and len(self.videos) > 16:
            target_fps = min(target_fps, 20)
        
        frame_time = 1.0 / target_fps if target_fps > 0 else 0.033
        
        while self.is_playing:
            try:
                start_time = time.time()
                
                # Обновляем все видео
                for idx, video in enumerate(self.videos):
                    if not video.get('valid', False) or not video.get('cap'):
                        continue
                        
                    try:
                        # Для PyAV особая обработка
                        if isinstance(video['cap'], PyAVCapture):
                            frame = video['cap'].read()
                            if frame is None:
                                video['cap'].seek(0)
                                frame = video['cap'].read()
                                if frame is None:
                                    continue
                            
                            # Конвертируем в формат для отображения
                            frame = cv2.resize(frame, (video['width'], video['height']))
                            img = Image.fromarray(frame)
                            imgtk = ImageTk.PhotoImage(image=img)
                            self.root.after(0, self._safe_update_canvas, idx, imgtk)
                        else:
                            # Стандартный OpenCV
                            ret, frame = video['cap'].read()
                            if not ret:
                                video['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                                ret, frame = video['cap'].read()
                                if not ret:
                                    continue
                            
                            # Оптимизация: пропускаем кадры при высокой нагрузке
                            if optimize and len(self.videos) > 24:
                                self.frame_skip_counter += 1
                                if self.frame_skip_counter % 2 == 0:
                                    continue
                            
                            # Масштабируем кадр
                            frame = cv2.resize(frame, (video['width'], video['height']))
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            img = Image.fromarray(frame)
                            imgtk = ImageTk.PhotoImage(image=img)
                            self.root.after(0, self._safe_update_canvas, idx, imgtk)
                            
                    except Exception as e:
                        continue
                
                # Контроль FPS
                elapsed = time.time() - start_time
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                
                # Динамическая подстройка FPS
                if optimize and len(self.videos) > 20:
                    current_fps = 1.0 / max(0.001, time.time() - start_time)
                    if current_fps < target_fps * 0.7:
                        target_fps = max(15, target_fps - 1)
                        frame_time = 1.0 / target_fps
                
                # Обновляем целевой FPS из интерфейса
                interface_fps = self.fps_var.get()
                if optimize and len(self.videos) > 16:
                    interface_fps = min(interface_fps, 20)
                frame_time = 1.0 / max(1, interface_fps)
                
            except Exception as e:
                print(f"Ошибка в цикле воспроизведения: {e}")
                time.sleep(0.1)
    
    def _safe_update_canvas(self, idx, imgtk):
        """Безопасное обновление canvas"""
        try:
            if idx < len(self.videos) and self.is_playing:
                video = self.videos[idx]
                if video.get('canvas') and imgtk:
                    video['canvas'].delete("all")
                    video['canvas'].create_image(0, 0, anchor=tk.NW, image=imgtk)
                    video['canvas'].image = imgtk
        except:
            pass
    
    def on_closing(self):
        """Закрытие окна"""
        self.stop_playback()
        try:
            self.root.destroy()
        except:
            sys.exit(0)


class PyAVCapture:
    """Обертка для PyAV для совместимости с OpenCV интерфейсом"""
    def __init__(self, container, stream):
        self.container = container
        self.stream = stream
        self.current_frame = 0
        
    def isOpened(self):
        return self.container is not None
    
    def read(self):
        try:
            for packet in self.container.demux(self.stream):
                for frame in packet.decode():
                    if frame.type == 'video':
                        # Конвертируем PyAV frame в numpy array
                        img = frame.to_ndarray(format='bgr24')
                        self.current_frame += 1
                        return True, img
            return False, None
        except:
            return False, None
    
    def set(self, prop, value):
        if prop == cv2.CAP_PROP_POS_FRAMES:
            try:
                self.container.seek(int(value))
                return True
            except:
                pass
        return False
    
    def get(self, prop):
        if prop == cv2.CAP_PROP_FPS:
            return float(self.stream.average_rate)
        elif prop == cv2.CAP_PROP_FRAME_COUNT:
            return self.stream.frames
        return 0
    
    def release(self):
        try:
            self.container.close()
        except:
            pass


def main():
    # Отключаем вывод предупреждений
    import warnings
    warnings.filterwarnings("ignore")
    
    # Проверяем наличие PyAV
    if not HAS_PYAV:
        print("Для лучшей поддержки H264 рекомендуется установить PyAV:")
        print("pip install av")
    
    root = tk.Tk()
    app = VideoGridPlayer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Центрируем окно
    root.update_idletasks()
    width = 1300
    height = 850
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()