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

class VideoGridPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Мульти-видео плеер в сетке")
        self.root.geometry("1300x850")
        
        # Настройка для Windows 11 (акцентные цвета, закругления)
        self.setup_windows11_style()
        
        # Поддерживаемые форматы видео
        self.video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v')
        
        # Список видео и их элементов
        self.videos = []
        self.is_playing = False
        self.play_thread = None
        self.cols = 3
        self.show_names = False
        
        # Создание интерфейса
        self.create_widgets()
        
        # Применяем тему Windows 11 если доступна
        if HAS_SV_TTK:
            sv_ttk.set_theme("dark")  # или "light" для светлой темы
            # Настройка цветов
            self.root.configure(bg='#1c1c1c' if sv_ttk.get_theme() == "dark" else '#f3f3f3')
        
    def setup_windows11_style(self):
        """Настройка стиля Windows 11"""
        try:
            # Включаем современные визуальные стили
            self.root.tk.call('tk', 'scaling', 1.2)  # Масштабирование для высоких DPI
            
            # Пытаемся включить DPI awareness для Windows
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass
                
            # Настройка иконки окна (можно добавить свою)
            # self.root.iconbitmap('icon.ico')
            
            # Создаем стили для компонентов
            style = ttk.Style()
            
            # Настройка стиля для кнопок (закругленные углы)
            style.configure('Win11.TButton', 
                          padding=(15, 8),
                          font=('Segoe UI', 10),
                          borderwidth=0,
                          focusthickness=0)
            
            style.map('Win11.TButton',
                     background=[('active', '#e6e6e6'), ('pressed', '#cccccc')])
            
            # Настройка стиля для слайдеров
            style.configure('Win11.Horizontal.TScale',
                          background='#0078d4',
                          troughcolor='#e0e0e0',
                          sliderlength=15)
            
            # Настройка стиля для меток
            style.configure('Win11.TLabel',
                          font=('Segoe UI', 10),
                          background='transparent')
            
            # Настройка стиля для фреймов
            style.configure('Win11.TFrame',
                          background='transparent')
            
            # Настройка стиля для Canvas
            style.configure('Win11.TCanvas',
                          background='#1e1e1e')
            
        except Exception as e:
            print(f"Ошибка настройки стиля: {e}")
        
    def create_widgets(self):
        # Основной контейнер с отступами в стиле Win11
        main_container = ttk.Frame(self.root, style='Win11.TFrame')
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Верхняя панель с кнопками (акцентная)
        top_frame = ttk.Frame(main_container, style='Win11.TFrame')
        top_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Первая строка кнопок
        button_frame = ttk.Frame(top_frame, style='Win11.TFrame')
        button_frame.pack(fill=tk.X)
        
        # Кнопки в стиле Win11
        self.load_btn = ttk.Button(button_frame, text="📁 Выбрать папку", 
                                  command=self.load_folder, style='Win11.TButton')
        self.load_btn.pack(side=tk.LEFT, padx=4)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Старт", 
                                   command=self.start_playback, style='Win11.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=4)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Стоп", 
                                  command=self.stop_playback, style='Win11.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=4)
        
        # Информационная панель в стиле Win11
        info_frame = ttk.Frame(button_frame, style='Win11.TFrame')
        info_frame.pack(side=tk.LEFT, padx=20)
        
        self.info_label = ttk.Label(info_frame, text="Нет загруженных видео", 
                                   font=('Segoe UI', 10, 'bold'), style='Win11.TLabel')
        self.info_label.pack()
        
        # Вторая строка - настройки
        settings_frame = ttk.Frame(top_frame, style='Win11.TFrame')
        settings_frame.pack(fill=tk.X, pady=8)
        
        # Карточка настроек с фоном
        settings_card = ttk.Frame(settings_frame, style='Win11.TFrame')
        settings_card.pack(fill=tk.X)
        
        # FPS контрол
        fps_frame = ttk.Frame(settings_card, style='Win11.TFrame')
        fps_frame.pack(side=tk.LEFT, padx=8)
        
        ttk.Label(fps_frame, text="🎬 FPS:", font=('Segoe UI', 10), 
                 style='Win11.TLabel').pack(side=tk.LEFT, padx=4)
        
        self.fps_var = tk.IntVar(value=30)
        self.fps_slider = ttk.Scale(fps_frame, from_=1, to=60, 
                                   orient=tk.HORIZONTAL, 
                                   variable=self.fps_var,
                                   length=180,
                                   style='Win11.Horizontal.TScale')
        self.fps_slider.pack(side=tk.LEFT, padx=8)
        
        self.fps_label = ttk.Label(fps_frame, text="30", width=4,
                                  font=('Segoe UI', 10, 'bold'), style='Win11.TLabel')
        self.fps_label.pack(side=tk.LEFT)
        self.fps_slider.configure(command=lambda x: self.fps_label.configure(text=str(int(float(x)))))
        
        # Колонки контрол
        cols_frame = ttk.Frame(settings_card, style='Win11.TFrame')
        cols_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(cols_frame, text="📐 Колонок:", font=('Segoe UI', 10),
                 style='Win11.TLabel').pack(side=tk.LEFT, padx=4)
        
        self.cols_var = tk.IntVar(value=3)
        self.cols_slider = ttk.Scale(cols_frame, from_=1, to=8, 
                                    orient=tk.HORIZONTAL, 
                                    variable=self.cols_var,
                                    length=180,
                                    style='Win11.Horizontal.TScale')
        self.cols_slider.pack(side=tk.LEFT, padx=8)
        
        self.cols_label = ttk.Label(cols_frame, text="3", width=4,
                                   font=('Segoe UI', 10, 'bold'), style='Win11.TLabel')
        self.cols_label.pack(side=tk.LEFT)
        self.cols_slider.configure(command=lambda x: self.cols_label.configure(text=str(int(float(x)))))
        
        ttk.Button(cols_frame, text="Применить", 
                  command=self.apply_grid_size, style='Win11.TButton').pack(side=tk.LEFT, padx=8)
        
        # Чекбокс для имен файлов
        self.show_names_var = tk.BooleanVar(value=False)
        self.show_names_check = ttk.Checkbutton(settings_card, 
                                               text="📝 Показывать имена файлов", 
                                               variable=self.show_names_var,
                                               command=self.toggle_names_display)
        self.show_names_check.pack(side=tk.LEFT, padx=20)
        
        # Создание canvas с прокруткой для сетки видео
        canvas_container = ttk.Frame(main_container, style='Win11.TFrame')
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Добавляем внутреннюю обводку в стиле Win11
        self.canvas = tk.Canvas(canvas_container, 
                               bg='#2b2b2b' if HAS_SV_TTK and sv_ttk.get_theme() == "dark" else '#f0f0f0',
                               highlightthickness=1,
                               highlightbackground='#404040')
        
        scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
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
        
        # Создаем подсказки для кнопок
        self.create_tooltips()
        
    def create_tooltips(self):
        """Создание всплывающих подсказок в стиле Win11"""
        self.tooltips = {}
        
        def create_tooltip(widget, text):
            def show_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = ttk.Label(tooltip, text=text, 
                                 background='#ffffff', 
                                 foreground='#1c1c1c',
                                 relief='solid', 
                                 borderwidth=1,
                                 padding=(8, 4),
                                 font=('Segoe UI', 9))
                label.pack()
                
                def hide_tooltip():
                    tooltip.destroy()
                
                widget.tooltip = tooltip
                widget.bind('<Leave>', lambda e: hide_tooltip())
            
            widget.bind('<Enter>', show_tooltip)
        
        create_tooltip(self.load_btn, "Выбрать папку с видеофайлами")
        create_tooltip(self.start_btn, "Начать воспроизведение всех видео")
        create_tooltip(self.stop_btn, "Остановить воспроизведение")
        
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
            
            frame = ttk.Frame(self.scrollable_frame, relief=tk.SUNKEN, borderwidth=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            name_label = ttk.Label(frame, text=video_data['name'], 
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
            
            frame = ttk.Frame(self.scrollable_frame, relief=tk.SUNKEN, borderwidth=1)
            frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            name_label = ttk.Label(frame, text=video_path.name, 
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
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()