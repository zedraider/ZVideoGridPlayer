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
from collections import defaultdict
import ctypes
from ctypes import wintypes

# Попытка импортировать дополнительные библиотеки для Win11 стиля
try:
    import sv_ttk  # Sun Valley theme (Windows 11 style)
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False
    print("Для лучшего стиля Windows 11 установите: pip install sv-ttk")

class CustomTitleBar:
    """Кастомный заголовок окна в стиле Windows 11"""
    def __init__(self, root, app):
        self.root = root
        self.app = app
        
        # Убираем стандартный заголовок
        root.overrideredirect(True)
        
        # Создаем кастомный заголовок
        self.title_bar = tk.Frame(root, bg='#1c1c1c', height=32)
        self.title_bar.pack(fill=tk.X)
        
        # Заголовок окна
        self.title_label = tk.Label(self.title_bar, text="Мульти-видео плеер в сетке", 
                                    bg='#1c1c1c', fg='#ffffff', 
                                    font=('Segoe UI', 10))
        self.title_label.pack(side=tk.LEFT, padx=12, pady=6)
        
        # Кнопки управления
        button_bg = '#1c1c1c'
        button_hover_bg = '#2c2c2c'
        button_close_hover_bg = '#e81123'
        
        # Кнопка минимизации
        self.min_btn = tk.Label(self.title_bar, text="─", bg=button_bg, fg='#ffffff',
                                font=('Segoe UI', 12), width=3, cursor='hand2')
        self.min_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.min_btn.bind('<Enter>', lambda e: self.min_btn.configure(bg=button_hover_bg))
        self.min_btn.bind('<Leave>', lambda e: self.min_btn.configure(bg=button_bg))
        self.min_btn.bind('<Button-1>', lambda e: root.iconify())
        
        # Кнопка разворачивания/сворачивания
        self.max_btn = tk.Label(self.title_bar, text="□", bg=button_bg, fg='#ffffff',
                                font=('Segoe UI', 10), width=3, cursor='hand2')
        self.max_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.max_btn.bind('<Enter>', lambda e: self.max_btn.configure(bg=button_hover_bg))
        self.max_btn.bind('<Leave>', lambda e: self.max_btn.configure(bg=button_bg))
        self.max_btn.bind('<Button-1>', self.toggle_maximize)
        
        # Кнопка закрытия
        self.close_btn = tk.Label(self.title_bar, text="✕", bg=button_bg, fg='#ffffff',
                                  font=('Segoe UI', 10), width=3, cursor='hand2')
        self.close_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        self.close_btn.bind('<Enter>', lambda e: self.close_btn.configure(bg=button_close_hover_bg))
        self.close_btn.bind('<Leave>', lambda e: self.close_btn.configure(bg=button_bg))
        self.close_btn.bind('<Button-1>', lambda e: root.destroy())
        
        # Для перетаскивания окна
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        
        self.x = 0
        self.y = 0
        
        # Сохраняем размеры для восстановления
        self.normal_size = None
        
        # Закругляем углы окна
        self.round_corners()
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def toggle_maximize(self, event):
        if self.normal_size is None:
            # Разворачиваем
            self.normal_size = (self.root.winfo_width(), self.root.winfo_height(),
                              self.root.winfo_x(), self.root.winfo_y())
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.max_btn.configure(text="❐")
        else:
            # Восстанавливаем
            w, h, x, y = self.normal_size
            self.root.geometry(f"{w}x{h}+{x}+{y}")
            self.normal_size = None
            self.max_btn.configure(text="□")
            
    def round_corners(self):
        """Закругление углов окна (только для Windows 11)"""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            # Устанавливаем стиль окна с закругленными углами
            from ctypes import wintypes
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWM_WINDOW_CORNER_PREFERENCE = 2  # Round corners
            
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
        self.root.title("Мульти-видео плеер в сетке")
        self.root.geometry("1300x850")
        
        # Устанавливаем цвет фона для всего окна
        self.root.configure(bg='#1c1c1c')
        
        # Создаем кастомный заголовок
        self.title_bar = CustomTitleBar(root, self)
        
        # Создаем основной контент
        self.create_main_content()
        
        # Настройка для Windows 11
        self.setup_windows11_style()
        
        # Поддерживаемые форматы видео
        self.video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v')
        
        # Список видео и их элементов
        self.videos = []
        self.is_playing = False
        self.play_thread = None
        self.cols = 3
        self.show_names = False
        
        # Применяем тему Windows 11 если доступна
        if HAS_SV_TTK:
            sv_ttk.set_theme("dark")
        
    def create_main_content(self):
        """Создание основного контента окна"""
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#1c1c1c')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        
        # Верхняя панель с кнопками
        self.create_control_panel(main_frame)
        
        # Создание canvas с прокруткой для сетки видео
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
        
        # Привязка прокрутки колесиком мыши
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def create_control_panel(self, parent):
        """Создание панели управления"""
        # Контейнер для панели управления с фоном
        control_frame = tk.Frame(parent, bg='#1c1c1c')
        control_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Стили для кнопок
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
                                   length=180)
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
                                    length=180)
        self.cols_slider.pack(side=tk.LEFT, padx=8)
        
        self.cols_label = tk.Label(cols_frame, text="3", width=4,
                                  bg='#1c1c1c', fg='#ffffff',
                                  font=('Segoe UI', 10, 'bold'))
        self.cols_label.pack(side=tk.LEFT)
        self.cols_slider.configure(command=lambda x: self.cols_label.configure(text=str(int(float(x)))))
        
        apply_btn = tk.Button(cols_frame, text="Применить", 
                            command=self.apply_grid_size, **btn_style)
        apply_btn.pack(side=tk.LEFT, padx=8)
        
        # Чекбокс для имен файлов
        self.show_names_var = tk.BooleanVar(value=False)
        self.show_names_check = tk.Checkbutton(settings_frame, 
                                             text="📝 Показывать имена файлов", 
                                             variable=self.show_names_var,
                                             command=self.toggle_names_display,
                                             bg='#1c1c1c', fg='#ffffff',
                                             selectcolor='#1c1c1c',
                                             activebackground='#1c1c1c',
                                             font=('Segoe UI', 10))
        self.show_names_check.pack(side=tk.LEFT, padx=20)
        
    def setup_windows11_style(self):
        """Настройка стиля Windows 11"""
        try:
            # Включаем современные визуальные стили
            self.root.tk.call('tk', 'scaling', 1.2)
            
            # Пытаемся включить DPI awareness для Windows
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
                
        except Exception as e:
            print(f"Ошибка настройки стиля: {e}")
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
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
        if self.videos:
            new_cols = self.cols_var.get()
            if new_cols != self.cols:
                self.cols = new_cols
                self.rearrange_grid()
    
    def rearrange_grid(self):
        """Перестроение сетки с новым количеством колонок"""
        if not self.videos:
            return
            
        was_playing = self.is_playing
        if was_playing:
            self.stop_playback()
        
        current_videos = self.videos.copy()
        
        for video in current_videos:
            video['frame'].destroy()
        
        self.videos = []
        
        cols = self.cols
        canvas_width = max(800, self.canvas.winfo_width())
        video_width = max(200, (canvas_width - 40) // cols)
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
        
        self.info_label.config(text=f"📹 Загружено: {len(self.videos)} | Сетка: {self.cols}x{len(self.videos)//self.cols + (1 if len(self.videos)%self.cols else 0)}")
        
        if was_playing:
            self.start_playback()
    
    def load_folder(self):
        """Загрузка всех видео из выбранной папки"""
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
            messagebox.showwarning("Предупреждение", "В выбранной папке не найдено видеофайлов!")
            return
            
        self.clear_videos()
        
        self.videos = []
        self.cols = self.cols_var.get()
        
        canvas_width = max(800, self.canvas.winfo_width())
        video_width = max(200, (canvas_width - 40) // self.cols)
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
            
        self.info_label.config(text=f"📹 Загружено: {len(self.videos)} | Сетка: {self.cols}x{len(self.videos)//self.cols + (1 if len(self.videos)%self.cols else 0)}")
        
        if len(unique_videos) < len(video_files):
            messagebox.showinfo("Готово", 
                               f"Загружено {len(self.videos)} видеофайлов\n"
                               f"(Пропущено дубликатов: {len(video_files) - len(unique_videos)})")
        else:
            messagebox.showinfo("Готово", f"Загружено {len(self.videos)} видеофайлов")
    
    def clear_videos(self):
        """Очистка всех видео элементов"""
        self.stop_playback()
        for video in self.videos:
            if video['cap']:
                video['cap'].release()
            if video['frame']:
                video['frame'].destroy()
        self.videos.clear()
    
    def start_playback(self):
        """Запуск воспроизведения всех видео"""
        if not self.videos:
            messagebox.showwarning("Предупреждение", "Сначала загрузите видео!")
            return
            
        if self.is_playing:
            return
            
        valid_videos = []
        for video in self.videos:
            if video['cap']:
                video['cap'].release()
            video['cap'] = cv2.VideoCapture(video['path'])
            if not video['cap'].isOpened():
                print(f"Не удалось открыть видео: {video['name']}")
                video['valid'] = False
                continue
            video['fps'] = video['cap'].get(cv2.CAP_PROP_FPS)
            if video['fps'] <= 0:
                video['fps'] = 30
            video['valid'] = True
            valid_videos.append(video)
        
        if not valid_videos:
            messagebox.showerror("Ошибка", "Не удалось открыть ни одно видео!")
            return
            
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()
    
    def stop_playback(self):
        """Остановка воспроизведения"""
        self.is_playing = False
        if self.play_thread:
            self.play_thread.join(timeout=1)
        for video in self.videos:
            if video.get('cap'):
                video['cap'].release()
                video['cap'] = None
    
    def _play_loop(self):
        """Основной цикл воспроизведения"""
        target_fps = self.fps_var.get()
        frame_time = 1.0 / target_fps if target_fps > 0 else 0.033
        
        while self.is_playing:
            start_time = time.time()
            
            for idx, video in enumerate(self.videos):
                if not video.get('valid', False) or not video.get('cap') or not video['cap'].isOpened():
                    continue
                    
                ret, frame = video['cap'].read()
                if not ret:
                    video['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = video['cap'].read()
                    if not ret:
                        continue
                
                frame = cv2.resize(frame, (video['width'], video['height']))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.root.after(0, self._update_canvas, idx, imgtk)
            
            elapsed = time.time() - start_time
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
            
            target_fps = self.fps_var.get()
            frame_time = 1.0 / target_fps if target_fps > 0 else 0.033
    
    def _update_canvas(self, idx, imgtk):
        """Обновление canvas в главном потоке"""
        if idx < len(self.videos) and self.is_playing:
            video = self.videos[idx]
            if video.get('canvas') and imgtk:
                try:
                    video['canvas'].delete("all")
                    video['canvas'].create_image(0, 0, anchor=tk.NW, image=imgtk)
                    video['canvas'].image = imgtk
                except:
                    pass
    
    def on_closing(self):
        """Обработка закрытия окна"""
        self.stop_playback()
        self.root.destroy()


def main():
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