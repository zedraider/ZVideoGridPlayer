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

class VideoGridPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Мульти-видео плеер в сетке")
        self.root.geometry("1200x800")
        
        # Поддерживаемые форматы видео
        self.video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v')
        
        # Список видео и их элементов
        self.videos = []  # список словарей с информацией о видео
        self.is_playing = False
        self.play_thread = None
        self.cols = 3  # количество колонок по умолчанию
        self.show_names = False  # показывать имена файлов или нет
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Первая строка кнопок
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Выбрать папку с видео", 
                  command=self.load_folder).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Старт", 
                  command=self.start_playback).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Стоп", 
                  command=self.stop_playback).pack(side=tk.LEFT, padx=5)
        
        # Информация о загруженных видео
        self.info_label = ttk.Label(button_frame, text="Нет загруженных видео")
        self.info_label.pack(side=tk.LEFT, padx=20)
        
        # Вторая строка - настройки
        settings_frame = ttk.Frame(top_frame)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Слайдер для FPS
        ttk.Label(settings_frame, text="FPS:").pack(side=tk.LEFT, padx=(5, 5))
        self.fps_var = tk.IntVar(value=30)
        self.fps_slider = ttk.Scale(settings_frame, from_=1, to=60, 
                                    orient=tk.HORIZONTAL, 
                                    variable=self.fps_var,
                                    length=150)
        self.fps_slider.pack(side=tk.LEFT)
        self.fps_label = ttk.Label(settings_frame, text="30")
        self.fps_label.pack(side=tk.LEFT, padx=5)
        self.fps_slider.configure(command=lambda x: self.fps_label.configure(text=str(int(float(x)))))
        
        # Слайдер для размера сетки (количество колонок)
        ttk.Label(settings_frame, text="Колонок:").pack(side=tk.LEFT, padx=(20, 5))
        self.cols_var = tk.IntVar(value=3)
        self.cols_slider = ttk.Scale(settings_frame, from_=1, to=8,  # Максимум 8 колонок
                                     orient=tk.HORIZONTAL, 
                                     variable=self.cols_var,
                                     length=150)
        self.cols_slider.pack(side=tk.LEFT)
        self.cols_label = ttk.Label(settings_frame, text="3")
        self.cols_label.pack(side=tk.LEFT, padx=5)
        self.cols_slider.configure(command=lambda x: self.cols_label.configure(text=str(int(float(x)))))
        
        # Кнопка применения размера сетки
        ttk.Button(settings_frame, text="Применить сетку", 
                  command=self.apply_grid_size).pack(side=tk.LEFT, padx=10)
        
        # Чекбокс для отображения имен файлов
        self.show_names_var = tk.BooleanVar(value=False)
        self.show_names_check = ttk.Checkbutton(settings_frame, 
                                                text="Показывать имена файлов", 
                                                variable=self.show_names_var,
                                                command=self.toggle_names_display)
        self.show_names_check.pack(side=tk.LEFT, padx=(20, 5))
        
        # Создание canvas с прокруткой для сетки видео
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
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
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def toggle_names_display(self):
        """Переключение отображения имен файлов"""
        self.show_names = self.show_names_var.get()
        # Обновляем отображение имен для всех видео
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
            
        # Останавливаем воспроизведение
        was_playing = self.is_playing
        if was_playing:
            self.stop_playback()
        
        # Сохраняем текущие видео
        current_videos = self.videos.copy()
        
        # Очищаем фреймы, но не удаляем видео данные
        for video in current_videos:
            video['frame'].destroy()
        
        self.videos = []
        
        # Перестраиваем сетку
        cols = self.cols
        for i, video_data in enumerate(current_videos):
            row = i // cols
            col = i % cols
            
            # Создаем новый фрейм
            frame = ttk.Frame(self.scrollable_frame, relief=tk.SUNKEN, borderwidth=1)
            frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # Настройка веса колонок и строк
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            # Метка с именем файла
            name_label = ttk.Label(frame, text=video_data['name'], 
                                  wraplength=250, font=("Arial", 8))
            
            # Показываем или скрываем имя в зависимости от настройки
            if self.show_names:
                name_label.pack()
            
            # Canvas для отображения видео
            video_canvas = tk.Canvas(frame, width=320, height=240, 
                                     bg='black', highlightthickness=0)
            video_canvas.pack(padx=2, pady=2)
            
            # Обновляем данные
            video_data['frame'] = frame
            video_data['canvas'] = video_canvas
            video_data['name_label'] = name_label
            self.videos.append(video_data)
        
        self.info_label.config(text=f"Загружено видео: {len(self.videos)}")
        
        # Если было воспроизведение, запускаем заново
        if was_playing:
            self.start_playback()
        
    def load_folder(self):
        """Загрузка всех видео из выбранной папки"""
        folder = filedialog.askdirectory()
        if not folder:
            return
            
        # Поиск видео файлов с использованием set для устранения дубликатов
        video_files = set()  # Используем set для автоматического удаления дубликатов
        
        for ext in self.video_extensions:
            # Добавляем файлы с разными расширениями
            video_files.update(Path(folder).glob(f"*{ext}"))
            video_files.update(Path(folder).glob(f"*{ext.upper()}"))
        
        # Конвертируем обратно в список и сортируем
        video_files = sorted(list(video_files))
        
        # Дополнительная проверка на дубликаты по имени файла
        seen_names = set()
        unique_videos = []
        for video_path in video_files:
            if video_path.name not in seen_names:
                seen_names.add(video_path.name)
                unique_videos.append(video_path)
            else:
                print(f"Пропущен дубликат: {video_path.name}")
        
        if not unique_videos:
            messagebox.showwarning("Предупреждение", "В выбранной папке не найдено видеофайлов!")
            return
            
        # Очистка предыдущих видео
        self.clear_videos()
        
        # Создание элементов для каждого видео
        self.videos = []
        self.cols = self.cols_var.get()
        
        # Динамический расчет размера видео в зависимости от количества колонок
        canvas_width = 1200 // self.cols - 20  # Примерный расчет ширины
        video_width = min(400, max(200, canvas_width))
        video_height = int(video_width * 0.75)  # Соотношение сторон 4:3
        
        for i, video_path in enumerate(unique_videos):
            # Определяем позицию в сетке
            row = i // self.cols
            col = i % self.cols
            
            # Создаем фрейм для видео
            frame = ttk.Frame(self.scrollable_frame, relief=tk.SUNKEN, borderwidth=1)
            frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # Настройка веса колонок и строк
            self.scrollable_frame.grid_columnconfigure(col, weight=1)
            self.scrollable_frame.grid_rowconfigure(row, weight=1)
            
            # Метка с именем файла
            name_label = ttk.Label(frame, text=video_path.name, 
                                  wraplength=video_width, font=("Arial", 8))
            
            # Показываем или скрываем имя в зависимости от настройки
            if self.show_names:
                name_label.pack()
            
            # Canvas для отображения видео
            video_canvas = tk.Canvas(frame, width=video_width, height=video_height, 
                                     bg='black', highlightthickness=0)
            video_canvas.pack(padx=2, pady=2)
            
            # Сохраняем информацию о видео
            self.videos.append({
                'path': str(video_path),
                'frame': frame,
                'canvas': video_canvas,
                'name_label': name_label,
                'cap': None,
                'fps': 0,
                'frame_count': 0,
                'name': video_path.name,
                'width': video_width,
                'height': video_height
            })
            
        self.info_label.config(text=f"Загружено видео: {len(self.videos)} (сетка {self.cols}x{len(self.videos)//self.cols + (1 if len(self.videos)%self.cols else 0)})")
        
        # Показываем сообщение о количестве видео и возможных дубликатах
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
            
        # Инициализация видеопотоков
        valid_videos = []
        for video in self.videos:
            if video['cap']:
                video['cap'].release()
            video['cap'] = cv2.VideoCapture(video['path'])
            if not video['cap'].isOpened():
                print(f"Не удалось открыть видео: {video['name']}")
                # Отмечаем видео как невалидное
                video['valid'] = False
                continue
            # Получаем FPS видео
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
        
        # Создаем метки для отслеживания текущего кадра каждого видео
        current_frames = [0] * len(self.videos)
        
        while self.is_playing:
            start_time = time.time()
            
            # Обновляем все видео
            for idx, video in enumerate(self.videos):
                if not video.get('valid', False) or not video.get('cap') or not video['cap'].isOpened():
                    continue
                    
                # Читаем кадр
                ret, frame = video['cap'].read()
                if not ret:
                    # Если видео закончилось, перематываем в начало
                    video['cap'].set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = video['cap'].read()
                    if not ret:
                        continue
                    current_frames[idx] = 0
                
                # Масштабируем кадр под размер canvas
                frame = cv2.resize(frame, (video['width'], video['height']))
                # Конвертируем BGR в RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Конвертируем в ImageTk
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Обновляем canvas в главном потоке
                self.root.after(0, self._update_canvas, idx, imgtk)
                current_frames[idx] += 1
            
            # Контроль FPS
            elapsed = time.time() - start_time
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
            
            # Обновляем целевой FPS, если он изменился
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
                    video['canvas'].image = imgtk  # Сохраняем ссылку
                except:
                    pass  # Игнорируем ошибки если canvas уже уничтожен
        
    def on_closing(self):
        """Обработка закрытия окна"""
        self.stop_playback()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VideoGridPlayer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()