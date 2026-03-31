"""ZVideoGridPlayer - Main application entry point."""
import logging
import os
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Dict, Any, Optional, Tuple, Callable
import cv2
from PIL import Image, ImageTk

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger: logging.Logger = logging.getLogger(__name__)

# Environment variables for performance
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOG_LEVEL'] = '-8'
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
os.environ['OPENCV_FFMPEG_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from .config import UIConfig, PerformanceConfig, WindowConfig, PathConfig
from .language_manager import LanguageManager
from .settings_manager import SettingsManager
from .video_player import VideoPlayerThread
from .ui_components import ModernTitleBar, ModernResizeHandle, ModernSettingsWindow, ThemeColors


class VideoGridPlayer:
    """Main application class for multi-video grid player."""
    
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the main application."""
        logger.info("=== Application Starting ===")
        self.root = root
        self.lang = LanguageManager()
        self.settings = SettingsManager()
        self.colors = ThemeColors.DARK
        
        self.lang.set_language(self.settings.get('language', 'en'))
        
        self.root.title(self.lang.get('app_title'))
        # ИСПРАВЛЕНО: Используем константы из UIConfig
        self.root.geometry(f"{UIConfig.WINDOW_WIDTH}x{UIConfig.WINDOW_HEIGHT}")
        self.root.minsize(UIConfig.WINDOW_MIN_WIDTH, UIConfig.WINDOW_MIN_HEIGHT)
        self.root.configure(bg=self.colors['bg_primary'])
        self.root.attributes('-alpha', self.settings.get('opacity', WindowConfig.OPACITY_DEFAULT))
        
        self.title_bar: ModernTitleBar = ModernTitleBar(
            root, self._on_minimize, self._on_close, self.lang.get('app_title')
        )
        self.resize_handler: ModernResizeHandle = ModernResizeHandle(
            root, self._pause_playback, self._resume_playback
        )
        
        self.main_container: tk.Frame = tk.Frame(root, bg=self.colors['bg_primary'])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.control_panel: tk.Frame = tk.Frame(
            self.main_container, bg=self.colors['bg_secondary'], 
            height=UIConfig.CONTROL_PANEL_HEIGHT
        )
        self.control_panel.pack(fill=tk.X, side=tk.TOP)
        self.control_panel.pack_propagate(False)
        self.panel_visible: bool = True
        
        separator: tk.Frame = tk.Frame(
            self.main_container, bg=self.colors['border'], height=1
        )
        separator.pack(fill=tk.X, side=tk.TOP)
        
        canvas_container: tk.Frame = tk.Frame(
            self.main_container, bg=self.colors['bg_primary']
        )
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas: tk.Canvas = tk.Canvas(
            canvas_container, bg=self.colors['bg_primary'], highlightthickness=0
        )
        scrollbar: ttk.Scrollbar = ttk.Scrollbar(
            canvas_container, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.scrollable_frame: tk.Frame = tk.Frame(self.canvas, bg=self.colors['bg_primary'])
        
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.master = canvas_container
        
        self.settings_window: ModernSettingsWindow = ModernSettingsWindow(
            self.root, self.settings, self.lang, self._on_settings_saved
        )
        
        self._create_control_panel()
        
        self.videos: List[Dict[str, Any]] = []
        self.video_threads: List[VideoPlayerThread] = []
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.cols: int = UIConfig.DEFAULT_COLUMNS
        self.show_names: bool = False
        self.updating: bool = False
        self.after_id: Optional[str] = None
        self.update_timer: Optional[str] = None
        self.last_update_time: float = 0.0
        
        self._bind_hotkeys()
        self.root.bind('<Configure>', self._on_window_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self._apply_theme()
        
        logger.info("=== Application Initialized ===")

    def _bind_hotkeys(self) -> None:
        """Bind keyboard hotkeys."""
        self.root.bind('<space>', lambda e: self._toggle_playback())
        self.root.bind('<s>', lambda e: self.stop_playback())
        self.root.bind('<p>', lambda e: self._pause_all())
        self.root.bind('<r>', lambda e: self._resume_all())
        self.root.bind('<f>', lambda e: self.title_bar._toggle_maximize())
        self.root.bind('<h>', self._toggle_panel)
        self.root.bind('<H>', self._toggle_panel)
        self.root.bind('<F1>', lambda e: self.settings_window.toggle())

    def _apply_theme(self) -> None:
        """Apply current theme settings."""
        is_dark: bool = self.settings.get('theme', 'dark') == 'dark'
        self.colors = ThemeColors.DARK if is_dark else ThemeColors.LIGHT
        
        self.root.configure(bg=self.colors['bg_primary'])
        self.main_container.configure(bg=self.colors['bg_primary'])
        self.control_panel.configure(bg=self.colors['bg_secondary'])
        self.canvas.configure(bg=self.colors['bg_primary'])
        self.scrollable_frame.configure(bg=self.colors['bg_primary'])
        
        self.title_bar.set_theme(is_dark)
        self.resize_handler.set_theme(is_dark)
        self.settings_window.set_theme(is_dark)
        
        self._update_toggle_buttons()
        
        try:
            import sv_ttk
            sv_ttk.set_theme(self.settings.get('theme', 'dark'))
        except ImportError:
            logger.debug("sv_ttk not available, using default theme")

    def _on_settings_saved(self) -> None:
        """Callback when settings are saved."""
        logger.debug("Settings saved callback")
        self.lang.set_language(self.settings.get('language', 'en'))
        self.root.attributes('-alpha', self.settings.get('opacity', WindowConfig.OPACITY_DEFAULT))
        self._apply_theme()
        self._update_ui_texts()
        
        max_cols: int = min(UIConfig.MAX_COLUMNS, self.settings.get('max_videos', PerformanceConfig.MAX_VIDEOS_DEFAULT))
        self.cols_slider.configure(to=max_cols)
        if self.cols_var.get() > max_cols:
            self.cols_var.set(max_cols)
            self.apply_grid_size()
        
        if self.is_playing:
            self.stop_playback()
            self.start_playback()

    def _update_ui_texts(self) -> None:
        """Update all UI text labels with current language."""
        self.root.title(self.lang.get('app_title'))
        self.title_bar.update_title(self.lang.get('app_title'))
        
        if hasattr(self, 'load_btn'):
            self.load_btn.configure(text=self.lang.get('select_folder'))
            self._update_toggle_buttons()
            self.settings_btn.configure(text=self.lang.get('settings'))
            self.hide_btn.configure(text=self.lang.get('hide_panel'))
            self.info_label.configure(text=self.lang.get('no_videos'))
            self.show_names_check.configure(text=self.lang.get('show_names'))
            self.hotkeys_label.configure(text=self.lang.get('hotkeys'))
            self.fps_label_text.configure(text=self.lang.get('fps_label'))
            self.cols_label_text.configure(text=self.lang.get('cols_label'))
            self.apply_btn.configure(text=self.lang.get('apply'))
        
        if self.videos:
            self.info_label.configure(
                text=self.lang.get('videos_info', len(self.videos), self.cols)
            )

    def _update_toggle_buttons(self) -> None:
        """Update play/stop and pause/resume button states."""
        if hasattr(self, 'play_stop_btn') and self.play_stop_btn.winfo_exists():
            if self.is_playing:
                self.play_stop_btn.configure(
                    text=self.lang.get('stop'),
                    bg=self.colors['button_stop_bg'],
                    activebackground=self.colors['button_stop_hover']
                )
            else:
                self.play_stop_btn.configure(
                    text=self.lang.get('start'),
                    bg=self.colors['button_play_bg'],
                    activebackground=self.colors['button_play_hover']
                )
        
        if hasattr(self, 'pause_resume_btn') and self.pause_resume_btn.winfo_exists():
            if self.is_playing and self.is_paused:
                self.pause_resume_btn.configure(
                    text=self.lang.get('resume'),
                    bg=self.colors['button_play_bg'],
                    activebackground=self.colors['button_play_hover']
                )
            else:
                self.pause_resume_btn.configure(
                    text=self.lang.get('pause'),
                    bg=self.colors['button_pause_bg'],
                    activebackground=self.colors['button_pause_hover']
                )

    def _on_frame_configure(self, event: tk.Event) -> None:
        """Handle scrollable frame resize."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_window_resize(self, event: tk.Event) -> None:
        """Handle window resize with debounce."""
        if event.widget == self.root and not self.updating:
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.after_id = self.root.after(
                WindowConfig.TITLE_BAR_RESTORE_DELAY, 
                self.update_grid_size
            )

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_minimize(self) -> None:
        """Handle window minimize."""
        logger.debug("Minimizing window")
        self.stop_playback()
        try:
            self.root.overrideredirect(False)
            self.root.iconify()
        except tk.TclError as e:
            logger.error(f"Error minimizing: {e}")
        except Exception as e:
            logger.error(f"Unexpected error minimizing: {e}")

    def _on_close(self) -> None:
        """Handle window close."""
        logger.info("Closing application")
        self.stop_playback()
        self.root.destroy()

    def _pause_playback(self) -> None:
        """Pause all video threads."""
        for thread in self.video_threads:
            thread.pause()

    def _resume_playback(self) -> None:
        """Resume all video threads."""
        for thread in self.video_threads:
            thread.resume()

    def _pause_all(self) -> None:
        """Pause all videos and update UI."""
        self.is_paused = True
        for thread in self.video_threads:
            thread.pause()
        self._update_toggle_buttons()

    def _resume_all(self) -> None:
        """Resume all videos and update UI."""
        self.is_paused = False
        for thread in self.video_threads:
            thread.resume()
        self._update_toggle_buttons()

    def _toggle_playback(self) -> None:
        """Toggle playback state."""
        if self.is_playing:
            if self.is_paused:
                self._resume_all()
            else:
                self._pause_all()
        else:
            self.start_playback()

    def _toggle_panel(self, event: Optional[tk.Event] = None) -> None:
        """Toggle control panel visibility."""
        if self.panel_visible:
            self.control_panel.pack_forget()
            self.panel_visible = False
        else:
            self.control_panel.pack(
                fill=tk.X, side=tk.TOP, before=self.canvas.master
            )
            self.panel_visible = True

    def _toggle_play_stop(self) -> None:
        """Toggle between play and stop."""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()
        self._update_toggle_buttons()

    def _toggle_pause_resume(self) -> None:
        """Toggle between pause and resume."""
        if not self.is_playing:
            return
        if self.is_paused:
            self._resume_all()
        else:
            self._pause_all()
        self._update_toggle_buttons()

    def _create_control_panel(self) -> None:
        """Create the control panel with all buttons and controls."""
        button_frame: tk.Frame = tk.Frame(
            self.control_panel, bg=self.colors['bg_secondary']
        )
        button_frame.pack(fill=tk.X, pady=(12, 8), padx=UIConfig.CONTROL_PANEL_PADDING)
        
        btn_style: Dict[str, Any] = {
            'fg': '#ffffff',
            'font': (UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_BUTTON, 'bold'),
            'padx': UIConfig.BUTTON_PADX,
            'pady': UIConfig.BUTTON_PADY,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        self.load_btn: tk.Button = tk.Button(
            button_frame, text=self.lang.get('select_folder'),
            command=self._load_folder,
            bg=self.colors['button_neutral_bg'],
            activebackground=self.colors['button_neutral_hover'],
            **btn_style
        )
        self.load_btn.pack(side=tk.LEFT, padx=4)
        
        self.play_stop_btn: tk.Button = tk.Button(
            button_frame, text=self.lang.get('start'),
            command=self._toggle_play_stop,
            bg=self.colors['button_play_bg'],
            activebackground=self.colors['button_play_hover'],
            **btn_style
        )
        self.play_stop_btn.pack(side=tk.LEFT, padx=4)
        
        self.pause_resume_btn: tk.Button = tk.Button(
            button_frame, text=self.lang.get('pause'),
            command=self._toggle_pause_resume,
            bg=self.colors['button_pause_bg'],
            activebackground=self.colors['button_pause_hover'],
            **btn_style
        )
        self.pause_resume_btn.pack(side=tk.LEFT, padx=4)
        
        self.settings_btn: tk.Button = tk.Button(
            button_frame, text=self.lang.get('settings'),
            command=self.settings_window.toggle,
            bg=self.colors['button_neutral_bg'],
            activebackground=self.colors['button_neutral_hover'],
            **btn_style
        )
        self.settings_btn.pack(side=tk.LEFT, padx=4)
        
        self.hide_btn: tk.Button = tk.Button(
            button_frame, text=self.lang.get('hide_panel'),
            command=self._toggle_panel,
            bg=self.colors['button_neutral_bg'],
            activebackground=self.colors['button_neutral_hover'],
            **btn_style
        )
        self.hide_btn.pack(side=tk.LEFT, padx=4)
        
        self.info_label: tk.Label = tk.Label(
            button_frame, text=self.lang.get('no_videos'),
            bg=self.colors['bg_secondary'], fg=self.colors['accent'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL, 'bold')
        )
        self.info_label.pack(side=tk.LEFT, padx=25)
        
        quick_frame: tk.Frame = tk.Frame(
            self.control_panel, bg=self.colors['bg_secondary']
        )
        quick_frame.pack(fill=tk.X, pady=(0, 10), padx=UIConfig.CONTROL_PANEL_PADDING)
        
        # FPS Control
        fps_frame: tk.Frame = tk.Frame(quick_frame, bg=self.colors['bg_secondary'])
        fps_frame.pack(side=tk.LEFT, padx=10)
        
        self.fps_label_text: tk.Label = tk.Label(
            fps_frame, text=self.lang.get('fps_label'),
            bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
        )
        self.fps_label_text.pack(side=tk.LEFT, padx=6)
        
        self.fps_var: tk.IntVar = tk.IntVar(
            value=self.settings.get('default_fps', PerformanceConfig.DEFAULT_FPS)
        )
        self.fps_slider: ttk.Scale = ttk.Scale(
            fps_frame, from_=PerformanceConfig.MIN_FPS, to=PerformanceConfig.MAX_FPS,
            orient=tk.HORIZONTAL, variable=self.fps_var, length=120
        )
        self.fps_slider.pack(side=tk.LEFT, padx=8)
        
        self.fps_value_label: tk.Label = tk.Label(
            fps_frame, text="30", width=4,
            bg=self.colors['bg_tertiary'], fg=self.colors['accent'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL, 'bold'),
            padx=8, pady=3
        )
        self.fps_value_label.pack(side=tk.LEFT)
        self.fps_slider.configure(
            command=lambda x: self.fps_value_label.configure(text=str(int(float(x))))
        )
        
        # Columns Control
        cols_frame: tk.Frame = tk.Frame(quick_frame, bg=self.colors['bg_secondary'])
        cols_frame.pack(side=tk.LEFT, padx=25)
        
        self.cols_label_text: tk.Label = tk.Label(
            cols_frame, text=self.lang.get('cols_label'),
            bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
        )
        self.cols_label_text.pack(side=tk.LEFT, padx=6)
        
        max_cols: int = min(
            UIConfig.MAX_COLUMNS, 
            self.settings.get('max_videos', PerformanceConfig.MAX_VIDEOS_DEFAULT)
        )
        self.cols_var: tk.IntVar = tk.IntVar(value=min(UIConfig.DEFAULT_COLUMNS, max_cols))
        self.cols_slider: ttk.Scale = ttk.Scale(
            cols_frame, from_=1, to=max_cols, orient=tk.HORIZONTAL,
            variable=self.cols_var, length=120
        )
        self.cols_slider.pack(side=tk.LEFT, padx=8)
        
        self.cols_value_label: tk.Label = tk.Label(
            cols_frame, text="3", width=4,
            bg=self.colors['bg_tertiary'], fg=self.colors['accent'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL, 'bold'),
            padx=8, pady=3
        )
        self.cols_value_label.pack(side=tk.LEFT)
        self.cols_slider.configure(
            command=lambda x: self.cols_value_label.configure(text=str(int(float(x))))
        )
        
        self.apply_btn: tk.Button = tk.Button(
            cols_frame, text=self.lang.get('apply'),
            command=self.apply_grid_size,
            bg=self.colors['accent'], fg='#ffffff',
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL, 'bold'),
            padx=15, pady=5, relief=tk.FLAT, cursor='hand2'
        )
        self.apply_btn.pack(side=tk.LEFT, padx=10)
        
        # Checkboxes
        self.show_names_var: tk.BooleanVar = tk.BooleanVar(
            value=self.settings.get('show_names', False)
        )
        self.show_names_check: tk.Checkbutton = tk.Checkbutton(
            quick_frame, text=self.lang.get('show_names'),
            variable=self.show_names_var,
            command=self._toggle_names_display,
            bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
            selectcolor=self.colors['accent'],
            activebackground=self.colors['bg_secondary'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
        )
        self.show_names_check.pack(side=tk.LEFT, padx=15)
        
        self.hotkeys_label: tk.Label = tk.Label(
            quick_frame, text=self.lang.get('hotkeys'),
            bg=self.colors['bg_secondary'], fg=self.colors['text_muted'],
            font=(UIConfig.FONT_FAMILY, 8)
        )
        self.hotkeys_label.pack(side=tk.RIGHT, padx=10)

    def _load_folder(self) -> None:
        """Load video files from selected folder."""
        logger.debug("Load folder button clicked")
        folder: str = filedialog.askdirectory()
        if not folder:
            return
        
        video_files: List[Path] = []
        for ext in PathConfig.VIDEO_EXTENSIONS:
            video_files.extend(Path(folder).glob(f"*{ext}"))
            video_files.extend(Path(folder).glob(f"*{ext.upper()}"))
        
        video_files = sorted(set(video_files))
        
        max_videos: int = self.settings.get('max_videos', PerformanceConfig.MAX_VIDEOS_DEFAULT)
        if max_videos > 0 and len(video_files) > max_videos:
            video_files = video_files[:max_videos]
        
        if not video_files:
            messagebox.showwarning(
                self.lang.get('warning_no_videos'),
                self.lang.get('warning_no_videos')
            )
            return
        
        self._clear_videos()
        
        video_ratios: Dict[str, float] = {}
        for video_path in video_files:
            try:
                cap: cv2.VideoCapture = cv2.VideoCapture(str(video_path))
                if cap.isOpened():
                    w: float = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    h: float = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    video_ratios[str(video_path)] = w / h if w > 0 and h > 0 else 16 / 9
                cap.release()
                time.sleep(0.02)
            except cv2.error as e:
                logger.error(f"OpenCV error reading video {video_path}: {e}")
                video_ratios[str(video_path)] = 16 / 9
            except Exception as e:
                logger.error(f"Error reading video {video_path}: {e}")
                video_ratios[str(video_path)] = 16 / 9
        
        self._arrange_videos_in_grid(video_files, video_ratios)
        self.info_label.config(
            text=self.lang.get('videos_info', len(self.videos), self.cols)
        )

    def _arrange_videos_in_grid(
        self, 
        video_files: List[Path], 
        video_ratios: Dict[str, float]
    ) -> None:
        """Arrange videos in grid layout."""
        canvas_width: int = self.canvas.winfo_width() - UIConfig.CANVAS_MARGIN
        if canvas_width < 100:
            canvas_width = 1200
        
        min_size: int = self.settings.get('min_video_size', PerformanceConfig.MIN_VIDEO_SIZE_DEFAULT)
        video_width: int = max(
            min_size, 
            (canvas_width - (self.cols * UIConfig.VIDEO_SPACING)) // self.cols
        )
        
        col_heights: List[int] = [0] * self.cols
        col_videos: List[List[Tuple[Path, int, float]]] = [[] for _ in range(self.cols)]
        
        for video_path in video_files:
            aspect_ratio: float = video_ratios.get(str(video_path), 16 / 9)
            if aspect_ratio <= 0:
                aspect_ratio = 16 / 9
            video_height: int = int(video_width / aspect_ratio)
            video_height = max(UIConfig.VIDEO_MIN_SIZE_HALF, video_height)
            
            min_col: int = col_heights.index(min(col_heights))
            col_videos[min_col].append((video_path, video_height, aspect_ratio))
            col_heights[min_col] += video_height + UIConfig.VIDEO_SPACING
        
        for col_idx, col_items in enumerate(col_videos):
            y_offset: int = 0
            for video_path, video_height, aspect_ratio in col_items:
                frame: tk.Frame = tk.Frame(
                    self.scrollable_frame, bg=self.colors['bg_tertiary'],
                    relief=tk.FLAT, bd=0
                )
                frame.place(
                    x=col_idx * (video_width + UIConfig.VIDEO_SPACING), 
                    y=y_offset,
                    width=video_width, 
                    height=video_height
                )
                
                border: tk.Frame = tk.Frame(
                    frame, bg=self.colors['border'], height=UIConfig.VIDEO_BORDER_WIDTH
                )
                border.pack(side=tk.BOTTOM, fill=tk.X)
                
                name_label: tk.Label = tk.Label(
                    frame, text=video_path.name, bg=self.colors['bg_tertiary'],
                    fg=self.colors['text_muted'],
                    wraplength=video_width, 
                    font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
                )
                if self.show_names:
                    name_label.pack()
                
                video_canvas: tk.Canvas = tk.Canvas(
                    frame, width=video_width, 
                    height=video_height - (25 if self.show_names else 1),
                    bg='#000000', highlightthickness=0
                )
                video_canvas.pack(padx=3, pady=3, expand=True, fill=tk.BOTH)
                
                self.videos.append({
                    'path': str(video_path),
                    'frame': frame,
                    'canvas': video_canvas,
                    'name_label': name_label,
                    'name': video_path.name,
                    'width': video_width,
                    'height': video_height,
                    'valid': True,
                    'videos': None,
                    'aspect_ratio': aspect_ratio
                })
                
                y_offset += video_height + UIConfig.VIDEO_SPACING
        
        max_height: int = max(col_heights) if col_heights else 0
        self.scrollable_frame.configure(
            width=self.cols * (video_width + UIConfig.VIDEO_SPACING), 
            height=max_height
        )
        
        for video in self.videos:
            video['videos'] = self.videos

    def _clear_videos(self) -> None:
        """Clear all videos and stop playback."""
        self.stop_playback()
        for video in self.videos:
            if video.get('frame'):
                try:
                    video['frame'].destroy()
                except tk.TclError as e:
                    logger.error(f"Error destroying video frame: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error destroying frame: {e}")
        self.videos.clear()
        self.video_threads.clear()

    def _toggle_names_display(self) -> None:
        """Toggle file names visibility."""
        self.show_names = self.show_names_var.get()
        self.settings.set('show_names', self.show_names)
        if self.settings.get('auto_save', True):
            self.settings.save()
        logger.debug(f"Toggle names display: {self.show_names}")
        for video in self.videos:
            if 'name_label' in video:
                if self.show_names:
                    video['name_label'].pack()
                else:
                    video['name_label'].pack_forget()

    def start_playback(self) -> None:
        """Start video playback."""
        if not self.videos:
            messagebox.showwarning(
                self.lang.get('warning_no_videos'),
                self.lang.get('warning_load_first')
            )
            return
        if self.is_playing:
            return
        
        logger.info(f"Starting playback for {len(self.videos)} videos")
        self.video_threads = []
        settings_dict: Dict[str, Any] = self.settings.all
        
        for idx, video in enumerate(self.videos):
            thread: VideoPlayerThread = VideoPlayerThread(
                video,
                lambda: self.fps_var.get(),
                lambda: self.settings.get('optimization_enabled', True),
                settings_dict,
                idx
            )
            thread.start()
            video['valid'] = True
            self.video_threads.append(thread)
        
        if not self.video_threads:
            messagebox.showerror(
                self.lang.get('error_open_video'),
                self.lang.get('error_open_video')
            )
            return
        
        self.is_playing = True
        self.is_paused = False
        self._update_toggle_buttons()
        self._start_update_timer()
        logger.info(f"Started playback for {len(self.video_threads)} videos")

    def stop_playback(self) -> None:
        """Stop all video playback."""
        logger.info(f"Stopping playback for {len(self.video_threads)} videos")
        
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
            self.update_timer = None
        
        for thread in self.video_threads:
            thread.stop()
        
        for thread in self.video_threads:
            thread.wait_for_exit(timeout=PerformanceConfig.THREAD_EXIT_TIMEOUT)
        
        self.video_threads.clear()
        self.is_playing = False
        self.is_paused = False
        try:
            self._update_toggle_buttons()
        except tk.TclError as e:
            logger.debug(f"Could not update toggle buttons during stop: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error updating buttons: {e}")
        
        logger.info("Playback stopped")

    def update_grid_size(self) -> None:
        """Update grid size on window resize."""
        if self.videos and not self.updating:
            self._rearrange_grid(keep_playing=True)

    def apply_grid_size(self) -> None:
        """Apply new column count."""
        if self.videos and not self.updating:
            new_cols: int = self.cols_var.get()
            if new_cols != self.cols:
                self.cols = new_cols
                self._rearrange_grid()

    def _rearrange_grid(self, keep_playing: bool = False) -> None:
        """Rearrange video grid."""
        if not self.videos or self.updating:
            return
        
        self.updating = True
        was_playing: bool = self.is_playing if not keep_playing else self.is_playing
        was_paused: bool = self.is_paused
        
        if was_playing and not keep_playing:
            for thread in self.video_threads:
                thread.pause()
        
        current_videos: List[Dict[str, Any]] = self.videos.copy()
        for video in current_videos:
            if video.get('frame'):
                try:
                    video['frame'].destroy()
                except tk.TclError as e:
                    logger.error(f"Error destroying frame: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error destroying frame: {e}")
        self.videos = []
        
        canvas_width: int = self.canvas.winfo_width() - UIConfig.CANVAS_MARGIN
        if canvas_width < 100:
            canvas_width = 1200
        
        min_size: int = self.settings.get('min_video_size', PerformanceConfig.MIN_VIDEO_SIZE_DEFAULT)
        video_width: int = max(
            min_size, 
            (canvas_width - (self.cols * UIConfig.VIDEO_SPACING)) // self.cols
        )
        
        col_heights: List[int] = [0] * self.cols
        col_videos: List[List[Tuple[Dict[str, Any], int]]] = [[] for _ in range(self.cols)]
        
        for video_data in current_videos:
            aspect_ratio: float = video_data.get('aspect_ratio', 16 / 9)
            if aspect_ratio <= 0:
                aspect_ratio = 16 / 9
            video_height: int = int(video_width / aspect_ratio)
            video_height = max(PerformanceConfig.MIN_VIDEO_SIZE_HALF, video_height)
            
            min_col: int = col_heights.index(min(col_heights))
            col_videos[min_col].append((video_data, video_height))
            col_heights[min_col] += video_height + UIConfig.VIDEO_SPACING
        
        for col_idx, col_items in enumerate(col_videos):
            y_offset: int = 0
            for video_data, video_height in col_items:
                frame: tk.Frame = tk.Frame(
                    self.scrollable_frame, bg=self.colors['bg_tertiary'],
                    relief=tk.FLAT, bd=0
                )
                frame.place(
                    x=col_idx * (video_width + UIConfig.VIDEO_SPACING), 
                    y=y_offset,
                    width=video_width, 
                    height=video_height
                )
                
                border: tk.Frame = tk.Frame(
                    frame, bg=self.colors['border'], height=UIConfig.VIDEO_BORDER_WIDTH
                )
                border.pack(side=tk.BOTTOM, fill=tk.X)
                
                name_label: tk.Label = tk.Label(
                    frame, text=video_data['name'], bg=self.colors['bg_tertiary'],
                    fg=self.colors['text_muted'],
                    wraplength=video_width, 
                    font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
                )
                if self.show_names:
                    name_label.pack()
                
                video_canvas: tk.Canvas = tk.Canvas(
                    frame, width=video_width,
                    height=video_height - (25 if self.show_names else 1),
                    bg='#000000', highlightthickness=0
                )
                video_canvas.pack(padx=3, pady=3, expand=True, fill=tk.BOTH)
                
                video_data['frame'] = frame
                video_data['canvas'] = video_canvas
                video_data['name_label'] = name_label
                video_data['width'] = video_width
                video_data['height'] = video_height
                self.videos.append(video_data)
                
                y_offset += video_height + UIConfig.VIDEO_SPACING
        
        max_height: int = max(col_heights) if col_heights else 0
        self.scrollable_frame.configure(
            width=self.cols * (video_width + UIConfig.VIDEO_SPACING), 
            height=max_height
        )
        
        self.info_label.config(
            text=self.lang.get('videos_info', len(self.videos), self.cols)
        )
        
        if was_playing:
            if keep_playing:
                for thread in self.video_threads:
                    thread.resume()
            else:
                self.start_playback()
            if was_paused:
                self._pause_all()
        
        self.updating = False

    def _start_update_timer(self) -> None:
        """Start the canvas update timer."""
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        
        target_fps: int = min(
            self.fps_var.get(), 
            self.settings.get('max_fps', PerformanceConfig.MAX_FPS)
        )
        interval: int = int(1000 / target_fps) if target_fps > 0 else 33
        
        self.update_timer = self.root.after(interval, self._update_canvas_all)

    def _update_canvas_all(self) -> None:
        """Update all video canvases with new frames."""
        if not self.is_playing:
            return
        
        current_time: float = time.time()
        target_fps: int = min(
            self.fps_var.get(), 
            self.settings.get('max_fps', PerformanceConfig.MAX_FPS)
        )
        target_interval: float = 1.0 / target_fps if target_fps > 0 else 0.033
        
        for idx, thread in enumerate(self.video_threads):
            if idx < len(self.videos):
                frame: Optional[np.ndarray] = thread.get_frame()
                if frame is not None:
                    try:
                        img: Image.Image = Image.fromarray(frame)
                        imgtk: ImageTk.PhotoImage = ImageTk.PhotoImage(image=img)
                        self.videos[idx]['canvas'].delete("all")
                        self.videos[idx]['canvas'].create_image(
                            self.videos[idx]['width'] // 2,
                            self.videos[idx]['height'] // 2,
                            image=imgtk, anchor='center'
                        )
                        self.videos[idx]['canvas'].image = imgtk
                    except Exception as e:
                        logger.error(f"Error updating canvas: {e}")
        
        elapsed: float = time.time() - current_time
        next_interval: int = max(
            PerformanceConfig.UPDATE_TIMER_MIN_INTERVAL, 
            int((target_interval - elapsed) * 1000)
        )
        self.update_timer = self.root.after(next_interval, self._update_canvas_all)




def main() -> None:
    """Main entry point."""
    logger.info("=== MAIN START ===")
    root: tk.Tk = tk.Tk()
    
    icon_paths: List[Path] = [
        Path("icon.ico"),
        Path("icon.png"),
        Path(__file__).parent.parent / "icon.ico",
        Path(__file__).parent.parent / "icon.png",
    ]
    for path in icon_paths:
        if path.exists():
            try:
                root.iconbitmap(str(path))
                break
            except tk.TclError as e:
                logger.debug(f"TclError loading icon {path}: {e}")
                try:
                    icon_img: tk.PhotoImage = tk.PhotoImage(file=str(path))
                    root.iconphoto(True, icon_img)
                    break
                except tk.TclError as e:
                    logger.debug(f"TclError loading icon as photo {path}: {e}")
                except Exception as e:
                    logger.error(f"Error loading icon as photo {path}: {e}")
            except Exception as e:
                logger.error(f"Error loading icon {path}: {e}")

    app: VideoGridPlayer = VideoGridPlayer(root)

    try:
        logger.info("Starting mainloop")
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error in mainloop: {e}", exc_info=True)
    finally:
        try:
            app.stop_playback()
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")
        logger.info("=== MAIN END ===")


if __name__ == "__main__":
    main()