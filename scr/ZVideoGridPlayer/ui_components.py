"""Custom UI components: title bar, resize handles, settings window."""
import ctypes
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import UIConfig, PerformanceConfig, WindowConfig, ColorConfig
from .language_manager import LanguageManager
from .settings_manager import SettingsManager

logger = logging.getLogger(__name__)

try:
    import sv_ttk
    HAS_SV_TTK: bool = True
except ImportError:
    HAS_SV_TTK = False


class ThemeColors:
    """Modern color palettes for dark and light themes."""
    
    DARK: Dict[str, str] = {
        'bg_primary': '#0d1117',
        'bg_secondary': '#161b22',
        'bg_tertiary': '#21262d',
        'bg_hover': '#30363d',
        'border': '#30363d',
        'border_focus': '#58a6ff',
        'text_primary': '#f0f6fc',
        'text_secondary': '#8b949e',
        'text_muted': '#6e7681',
        'accent': '#58a6ff',
        'accent_hover': '#79c0ff',
        'success': '#3fb950',
        'success_active': '#2ea043',
        'warning': '#d29922',
        'danger': '#f85149',
        'danger_active': '#da3633',
        'gradient_start': '#1f6feb',
        'gradient_end': '#388bfd',
        'button_play_bg': '#238636',
        'button_play_hover': '#2ea043',
        'button_stop_bg': '#da3633',
        'button_stop_hover': '#f85149',
        'button_pause_bg': '#9e6a03',
        'button_pause_hover': '#d29922',
        'button_neutral_bg': '#21262d',
        'button_neutral_hover': '#30363d',
        'input_bg': '#0d1117',
        'input_fg': '#f0f6fc',
        'input_border': '#30363d',
        'input_border_focus': '#58a6ff',
    }
    
    LIGHT: Dict[str, str] = {
        'bg_primary': '#ffffff',
        'bg_secondary': '#ffffff',
        'bg_tertiary': '#f6f8fa',
        'bg_hover': '#eaeef2',
        'border': '#d0d7de',
        'border_focus': '#0969da',
        'text_primary': '#1f2328',
        'text_secondary': '#656d76',
        'text_muted': '#8c959f',
        'accent': '#0969da',
        'accent_hover': '#0550ae',
        'success': '#1a7f37',
        'success_active': '#116329',
        'warning': '#9a6700',
        'danger': '#cf222e',
        'danger_active': '#a40e26',
        'gradient_start': '#0969da',
        'gradient_end': '#388bfd',
        'button_play_bg': '#1a7f37',
        'button_play_hover': '#116329',
        'button_stop_bg': '#cf222e',
        'button_stop_hover': '#a40e26',
        'button_pause_bg': '#9a6700',
        'button_pause_hover': '#7d4e00',
        'button_neutral_bg': '#eaeef2',
        'button_neutral_hover': '#d0d7de',
        'input_bg': '#ffffff',
        'input_fg': '#1f2328',
        'input_border': '#d0d7de',
        'input_border_focus': '#0969da',
    }


class ModernTitleBar:
    """Modern window title bar with gradient and smooth animations."""
    
    def __init__(
        self, 
        root: tk.Tk, 
        on_minimize: Callable[[], None], 
        on_close: Callable[[], None],
        title: str = "ZVideoGridPlayer"
    ) -> None:
        self._root: tk.Tk = root
        self._on_minimize: Callable[[], None] = on_minimize
        self._on_close: Callable[[], None] = on_close
        self._is_maximized: bool = False
        self._normal_size: Optional[Tuple[int, int, int, int]] = None
        self._is_dragging: bool = False
        self._drag_x: int = 0
        self._drag_y: int = 0
        self._colors: Dict[str, str] = ThemeColors.DARK
        
        root.overrideredirect(True)
        
        self._title_bar: tk.Frame = tk.Frame(
            root, bg=self._colors['bg_secondary'], height=UIConfig.TITLE_BAR_HEIGHT
        )
        self._title_bar.pack(fill=tk.X)
        self._title_bar.bind('<Double-Button-1>', self._toggle_maximize)
        
        self._accent_bar: tk.Canvas = tk.Canvas(
            self._title_bar, bg=self._colors['bg_secondary'],
            height=UIConfig.TITLE_BAR_HEIGHT, width=4, highlightthickness=0
        )
        self._accent_bar.pack(side=tk.LEFT, fill=tk.Y)
        self._draw_gradient_accent()
        
        self._icon_frame: tk.Frame = tk.Frame(
            self._title_bar, bg=self._colors['bg_secondary']
        )
        self._icon_frame.pack(side=tk.LEFT, padx=(16, 12), pady=8)
        
        self._icon_label: tk.Label = tk.Label(
            self._icon_frame, text="🎬", bg=self._colors['bg_secondary'],
            font=('Segoe UI Emoji', 16)
        )
        self._icon_label.pack()
        self._icon_label.bind('<Double-Button-1>', self._toggle_maximize)
        
        self._title_label: tk.Label = tk.Label(
            self._title_bar, text=title, bg=self._colors['bg_secondary'],
            fg=self._colors['text_primary'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL, 'bold')
        )
        self._title_label.pack(side=tk.LEFT, padx=0, pady=12)
        self._title_label.bind('<Double-Button-1>', self._toggle_maximize)
        
        self._create_window_controls()
        
        self._title_bar.bind('<Button-1>', self._start_move)
        self._title_bar.bind('<B1-Motion>', self._on_move)
        self._title_bar.bind('<ButtonRelease-1>', self._stop_move)
        
        self._round_corners()
        self._root.bind('<Map>', self._on_window_restore)
        
        logger.debug("ModernTitleBar initialized")

    def _draw_gradient_accent(self) -> None:
        self._accent_bar.delete("all")
        for i in range(UIConfig.TITLE_BAR_HEIGHT):
            ratio: float = i / UIConfig.TITLE_BAR_HEIGHT
            r: int = int(31 + (56 - 31) * ratio)
            g: int = int(111 + (139 - 111) * ratio)
            b: int = int(235 + (253 - 235) * ratio)
            color: str = f'#{r:02x}{g:02x}{b:02x}'
            self._accent_bar.create_line(2, i, 2, i+1, fill=color, width=2)

    def _create_window_controls(self) -> None:
        btn_frame: tk.Frame = tk.Frame(
            self._title_bar, bg=self._colors['bg_secondary']
        )
        btn_frame.pack(side=tk.RIGHT, padx=8, pady=6)
        
        self._min_btn: tk.Label = self._create_control_button(
            btn_frame, "─", self._on_minimize
        )
        self._min_btn.pack(side=tk.LEFT, padx=2)
        
        self._max_btn: tk.Label = self._create_control_button(
            btn_frame, "□", self._toggle_maximize
        )
        self._max_btn.pack(side=tk.LEFT, padx=2)
        
        self._close_btn: tk.Label = self._create_control_button(
            btn_frame, "✕", self._on_close, is_close=True
        )
        self._close_btn.pack(side=tk.LEFT, padx=2)

    def _create_control_button(
        self, 
        parent: tk.Widget, 
        text: str,
        command: Callable[[], None], 
        is_close: bool = False
    ) -> tk.Label:
        btn: tk.Label = tk.Label(
            parent, text=text, bg=self._colors['bg_secondary'],
            fg=self._colors['text_secondary'],
            font=(UIConfig.FONT_FAMILY, 
                  UIConfig.FONT_SIZE_LABEL if not is_close else UIConfig.FONT_SIZE_BUTTON),
            width=3, cursor='hand2', pady=6
        )
        
        if is_close:
            btn.bind(
                '<Enter>', 
                lambda e: btn.configure(bg=self._colors['danger'], fg='#ffffff')
            )
            btn.bind(
                '<Leave>', 
                lambda e: btn.configure(
                    bg=self._colors['bg_secondary'],
                    fg=self._colors['text_secondary']
                )
            )
        else:
            btn.bind(
                '<Enter>', 
                lambda e: btn.configure(
                    bg=self._colors['bg_hover'],
                    fg=self._colors['text_primary']
                )
            )
            btn.bind(
                '<Leave>', 
                lambda e: btn.configure(
                    bg=self._colors['bg_secondary'],
                    fg=self._colors['text_secondary']
                )
            )
        
        btn.bind('<Button-1>', lambda e: command())
        return btn

    def _on_window_restore(self, event: tk.Event) -> None:
        self._root.after(
            WindowConfig.TITLE_BAR_RESTORE_DELAY, 
            self._ensure_custom_titlebar
        )

    def _ensure_custom_titlebar(self) -> None:
        try:
            if self._root.winfo_viewable():
                self._root.overrideredirect(True)
                self._root.update_idletasks()
                self._root.lift()
        except tk.TclError as e:
            logger.error(f"Error ensuring custom titlebar: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in titlebar: {e}")

    def _start_move(self, event: tk.Event) -> None:
        self._is_dragging = True
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event: tk.Event) -> None:
        if not self._is_maximized and self._is_dragging:
            x: int = self._root.winfo_x() + (event.x - self._drag_x)
            y: int = self._root.winfo_y() + (event.y - self._drag_y)
            self._root.geometry(f"+{x}+{y}")

    def _stop_move(self, event: tk.Event) -> None:
        self._is_dragging = False

    def _get_monitor_rect(self) -> Tuple[int, int, int, int]:
        try:
            hwnd: int = ctypes.windll.user32.GetParent(self._root.winfo_id())
            hmon: int = ctypes.windll.user32.MonitorFromWindow(
                hwnd, WindowConfig.MONITOR_DEFAULT
            )
            
            class MONITORINFO(ctypes.Structure):
                _fields_: List[Tuple[str, Any]] = [
                    ("cbSize", ctypes.c_int),
                    ("rcMonitor", ctypes.c_int * 4),
                    ("rcWork", ctypes.c_int * 4),
                    ("dwFlags", ctypes.c_int)
                ]
            
            mi: MONITORINFO = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            ctypes.windll.user32.GetMonitorInfoA(hmon, ctypes.byref(mi))
            
            left: int = mi.rcWork[0]
            top: int = mi.rcWork[1]
            right: int = mi.rcWork[2]
            bottom: int = mi.rcWork[3]
            return (left, top, right - left, bottom - top)
        except OSError as e:
            logger.warning(f"Could not get monitor info: {e}, using primary monitor")
            return (
                0, 0, 
                self._root.winfo_screenwidth(), 
                self._root.winfo_screenheight()
            )
        except Exception as e:
            logger.error(f"Unexpected error getting monitor rect: {e}")
            return (
                0, 0, 
                self._root.winfo_screenwidth(), 
                self._root.winfo_screenheight()
            )

    def _toggle_maximize(self, event: Optional[tk.Event] = None) -> None:
        try:
            if not self._is_maximized:
                self._normal_size = (
                    self._root.winfo_width(), 
                    self._root.winfo_height(),
                    self._root.winfo_x(), 
                    self._root.winfo_y()
                )
                x, y, width, height = self._get_monitor_rect()
                self._root.geometry(f"{width}x{height}+{x}+{y}")
                self._max_btn.configure(text="❐")
                self._is_maximized = True
            else:
                if self._normal_size:
                    w, h, x, y = self._normal_size
                    self._root.geometry(f"{w}x{h}+{x}+{y}")
                    self._max_btn.configure(text="□")
                    self._is_maximized = False
            self._root.after(
                WindowConfig.MAXIMIZE_UPDATE_DELAY, 
                self._update_resize_handles
            )
        except tk.TclError as e:
            logger.error(f"Error toggling maximize: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in maximize: {e}")

    def _update_resize_handles(self) -> None:
        for child in self._root.children.values():
            if hasattr(child, 'update_handles'):
                try:
                    child.update_handles()
                except tk.TclError as e:
                    logger.error(f"Error updating resize handles: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error updating handles: {e}")
                break

    def _round_corners(self) -> None:
        try:
            hwnd: int = ctypes.windll.user32.GetParent(self._root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                WindowConfig.DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(
                    ctypes.c_int(WindowConfig.DWM_WINDOW_CORNER_PREFERENCE_ROUND)
                ),
                ctypes.sizeof(ctypes.c_int)
            )
        except OSError:
            logger.debug("Could not set rounded corners (Windows version may not support)")
        except Exception as e:
            logger.debug(f"Unexpected error setting corners: {e}")

    def update_title(self, title: str) -> None:
        self._title_label.configure(text=title)

    def set_theme(self, is_dark: bool) -> None:
        self._colors = ThemeColors.DARK if is_dark else ThemeColors.LIGHT
        self._title_bar.configure(bg=self._colors['bg_secondary'])
        self._icon_frame.configure(bg=self._colors['bg_secondary'])
        self._icon_label.configure(bg=self._colors['bg_secondary'])
        self._title_label.configure(
            bg=self._colors['bg_secondary'],
            fg=self._colors['text_primary']
        )
        self._accent_bar.configure(bg=self._colors['bg_secondary'])
        self._draw_gradient_accent()


class ModernResizeHandle:
    """Modern 8-edge window resizing with visual feedback."""
    
    def __init__(
        self, 
        root: tk.Tk, 
        on_resize_start: Callable[[], None],
        on_resize_end: Callable[[], None]
    ) -> None:
        self._root: tk.Tk = root
        self._on_resize_start: Callable[[], None] = on_resize_start
        self._on_resize_end: Callable[[], None] = on_resize_end
        self._resize_size: int = UIConfig.RESIZE_HANDLE_SIZE
        self._resizing: bool = False
        self._resize_direction: Optional[str] = None
        self._handles: Dict[str, tk.Frame] = {}
        self._colors: Dict[str, str] = ThemeColors.DARK
        
        self._start_x: int = 0
        self._start_y: int = 0
        self._start_w: int = 0
        self._start_h: int = 0
        self._start_root_x: int = 0
        self._start_root_y: int = 0
        
        self._create_handles()
        logger.debug("ModernResizeHandle initialized")

    def _create_handles(self) -> None:
        s: int = self._resize_size
        
        for handle in self._handles.values():
            try:
                handle.destroy()
            except tk.TclError:
                pass
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
        self._handles = {}
        
        corners: List[Tuple[str, float, float, str, str]] = [
            ('se', 1.0, 1.0, 'se', 'size_nw_se'),
            ('sw', 0.0, 1.0, 'sw', 'size_ne_sw'),
            ('ne', 1.0, 0.0, 'ne', 'size_ne_sw'),
            ('nw', 0.0, 0.0, 'nw', 'size_nw_se'),
        ]
        
        for name, relx, rely, anchor, cursor in corners:
            handle: tk.Frame = tk.Frame(
                self._root, bg=self._colors['bg_secondary'], cursor=cursor
            )
            handle.place(relx=relx, rely=rely, anchor=anchor, width=s, height=s)
            handle.bind('<ButtonPress-1>', lambda e, d=name: self._start_resize(e, d))
            handle.bind('<B1-Motion>', self._on_resize)
            handle.bind('<ButtonRelease-1>', self._stop_resize)
            handle.bind(
                '<Enter>', 
                lambda e, h=handle: h.configure(bg=self._colors['accent'])
            )
            handle.bind(
                '<Leave>', 
                lambda e, h=handle: h.configure(bg=self._colors['bg_secondary'])
            )
            self._handles[name] = handle
        
        edges: List[Tuple[str, float, float, str, str, int, int]] = [
            ('e', 1.0, 0.5, 'e', 'size_we', s, UIConfig.RESIZE_HANDLE_EDGE_WIDTH),
            ('w', 0.0, 0.5, 'w', 'size_we', s, UIConfig.RESIZE_HANDLE_EDGE_WIDTH),
            ('s', 0.5, 1.0, 's', 'size_ns', UIConfig.RESIZE_HANDLE_EDGE_WIDTH, s),
            ('n', 0.5, 0.0, 'n', 'size_ns', UIConfig.RESIZE_HANDLE_EDGE_WIDTH, s),
        ]
        
        for name, relx, rely, anchor, cursor, width, height in edges:
            handle = tk.Frame(
                self._root, bg=self._colors['bg_secondary'], cursor=cursor
            )
            handle.place(relx=relx, rely=rely, anchor=anchor, width=width, height=height)
            handle.bind('<ButtonPress-1>', lambda e, d=name: self._start_resize(e, d))
            handle.bind('<B1-Motion>', self._on_resize)
            handle.bind('<ButtonRelease-1>', self._stop_resize)
            handle.bind(
                '<Enter>', 
                lambda e, h=handle: h.configure(bg=self._colors['accent'])
            )
            handle.bind(
                '<Leave>', 
                lambda e, h=handle: h.configure(bg=self._colors['bg_secondary'])
            )
            self._handles[name] = handle

    def _start_resize(self, event: tk.Event, direction: str) -> None:
        self._resizing = True
        self._resize_direction = direction
        self._start_x = self._root.winfo_pointerx()
        self._start_y = self._root.winfo_pointery()
        self._start_w = self._root.winfo_width()
        self._start_h = self._root.winfo_height()
        self._start_root_x = self._root.winfo_x()
        self._start_root_y = self._root.winfo_y()
        self._on_resize_start()

    def _on_resize(self, event: tk.Event) -> None:
        if not self._resizing or self._resize_direction is None:
            return
        
        dx: int = self._root.winfo_pointerx() - self._start_x
        dy: int = self._root.winfo_pointery() - self._start_y
        new_w: int = self._start_w
        new_h: int = self._start_h
        new_x: int = self._start_root_x
        new_y: int = self._start_root_y
        
        min_w: int = WindowConfig.MIN_WINDOW_WIDTH
        min_h: int = WindowConfig.MIN_WINDOW_HEIGHT
        
        if self._resize_direction == 'se':
            new_w = max(min_w, self._start_w + dx)
            new_h = max(min_h, self._start_h + dy)
        elif self._resize_direction == 'sw':
            new_w = max(min_w, self._start_w - dx)
            new_x = self._start_root_x + (self._start_w - new_w)
            new_h = max(min_h, self._start_h + dy)
        elif self._resize_direction == 'ne':
            new_w = max(min_w, self._start_w + dx)
            new_h = max(min_h, self._start_h - dy)
            new_y = self._start_root_y + (self._start_h - new_h)
        elif self._resize_direction == 'nw':
            new_w = max(min_w, self._start_w - dx)
            new_x = self._start_root_x + (self._start_w - new_w)
            new_h = max(min_h, self._start_h - dy)
            new_y = self._start_root_y + (self._start_h - new_h)
        elif self._resize_direction == 'e':
            new_w = max(min_w, self._start_w + dx)
        elif self._resize_direction == 'w':
            new_w = max(min_w, self._start_w - dx)
            new_x = self._start_root_x + (self._start_w - new_w)
        elif self._resize_direction == 's':
            new_h = max(min_h, self._start_h + dy)
        elif self._resize_direction == 'n':
            new_h = max(min_h, self._start_h - dy)
            new_y = self._start_root_y + (self._start_h - new_h)
        
        self._root.geometry(f"{int(new_w)}x{int(new_h)}+{int(new_x)}+{int(new_y)}")

    def _stop_resize(self, event: tk.Event) -> None:
        self._resizing = False
        self._resize_direction = None
        self._on_resize_end()

    def update_handles(self) -> None:
        self._create_handles()

    def set_theme(self, is_dark: bool) -> None:
        self._colors = ThemeColors.DARK if is_dark else ThemeColors.LIGHT
        for handle in self._handles.values():
            handle.configure(bg=self._colors['bg_secondary'])


class ModernSettingsWindow:
    """Beautiful settings window with modern design."""
    
    def __init__(
        self,
        parent: tk.Widget,
        settings_manager: SettingsManager,
        lang_manager: LanguageManager,
        on_save: Callable[[], None],
    ) -> None:
        self._parent: tk.Widget = parent
        self._settings: SettingsManager = settings_manager
        self._lang: LanguageManager = lang_manager
        self._on_save: Callable[[], None] = on_save
        self._window: Optional[tk.Toplevel] = None
        self._is_visible: bool = False
        self._colors: Dict[str, str] = ThemeColors.DARK
        self._drag_x: int = 0
        self._drag_y: int = 0
        
        logger.debug("ModernSettingsWindow initialized")

    def _create_window(self) -> None:
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
        
        # ИСПРАВЛЕНО: Используем константы из UIConfig
        self._window = tk.Toplevel(self._parent)
        self._window.title(self._lang.get('settings_title'))
        self._window.geometry(
            f"{UIConfig.SETTINGS_PANEL_WIDTH}x{UIConfig.SETTINGS_PANEL_HEIGHT}"
        )
        self._window.configure(bg=self._colors['bg_secondary'])
        self._window.resizable(False, False)
        self._window.overrideredirect(True)
        
        self._window.update_idletasks()
        x: int = self._parent.winfo_x() + (
            self._parent.winfo_width() // 2
        ) - (UIConfig.SETTINGS_PANEL_WIDTH // 2)
        y: int = self._parent.winfo_y() + (
            self._parent.winfo_height() // 2
        ) - (UIConfig.SETTINGS_PANEL_HEIGHT // 2)
        self._window.geometry(
            f"{UIConfig.SETTINGS_PANEL_WIDTH}x{UIConfig.SETTINGS_PANEL_HEIGHT}+{x}+{y}"
        )
        
        self._window.configure(
            highlightbackground=self._colors['border'],
            highlightthickness=2
        )
        
        self._window.bind('<Button-1>', self._start_move)
        self._window.bind('<B1-Motion>', self._on_move)
        
        self._create_content()
        self._is_visible = True

    def _start_move(self, event: tk.Event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_move(self, event: tk.Event) -> None:
        x: int = self._window.winfo_x() + (event.x - self._drag_x)
        y: int = self._window.winfo_y() + (event.y - self._drag_y)
        self._window.geometry(f"+{x}+{y}")

    def _create_content(self) -> None:
        try:
            header: tk.Frame = tk.Frame(
                self._window, bg=self._colors['bg_tertiary'], 
                height=60
            )
            header.pack(fill=tk.X)
            header.pack_propagate(False)
            
            accent_canvas: tk.Canvas = tk.Canvas(
                header, bg=self._colors['bg_tertiary'],
                height=4, width=UIConfig.SETTINGS_PANEL_WIDTH, 
                highlightthickness=0
            )
            accent_canvas.pack(side=tk.BOTTOM, fill=tk.X)
            for i in range(UIConfig.SETTINGS_PANEL_WIDTH):
                ratio: float = i / UIConfig.SETTINGS_PANEL_WIDTH
                r: int = int(31 + (56 - 31) * ratio)
                g: int = int(111 + (139 - 111) * ratio)
                b: int = int(235 + (253 - 235) * ratio)
                color: str = f'#{r:02x}{g:02x}{b:02x}'
                accent_canvas.create_line(i, 0, i, 4, fill=color)
            
            title_label: tk.Label = tk.Label(
                header, text=self._lang.get('settings_title'),
                bg=self._colors['bg_tertiary'], 
                fg=self._colors['text_primary'],
                font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_TITLE, 'bold')
            )
            title_label.place(x=25, y=15)
            
            close_btn: tk.Label = tk.Label(
                header, text="✕", bg=self._colors['bg_tertiary'],
                fg=self._colors['text_secondary'],
                font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_TITLE, 'bold'), 
                cursor='hand2'
            )
            close_btn.place(
                x=UIConfig.SETTINGS_PANEL_WIDTH - 50, y=12
            )
            close_btn.bind('<Button-1>', lambda e: self.hide())
            close_btn.bind(
                '<Enter>', 
                lambda e: close_btn.configure(
                    bg=self._colors['danger'], fg='#ffffff'
                )
            )
            close_btn.bind(
                '<Leave>', 
                lambda e: close_btn.configure(
                    bg=self._colors['bg_tertiary'],
                    fg=self._colors['text_secondary']
                )
            )
            
            canvas_frame: tk.Frame = tk.Frame(
                self._window, bg=self._colors['bg_secondary']
            )
            canvas_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
            
            canvas: tk.Canvas = tk.Canvas(
                canvas_frame, bg=self._colors['bg_secondary'], 
                highlightthickness=0
            )
            scrollbar: ttk.Scrollbar = ttk.Scrollbar(
                canvas_frame, orient=tk.VERTICAL, command=canvas.yview
            )
            scrollable_frame: tk.Frame = tk.Frame(
                canvas, bg=self._colors['bg_secondary']
            )
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            canvas.create_window(
                (0, 0), window=scrollable_frame, anchor="nw"
            )
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self._scrollable_frame: tk.Frame = scrollable_frame
            self._create_settings_widgets(scrollable_frame)
            
        except tk.TclError as e:
            logger.error(f"Error creating settings window content: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error creating settings content: {e}", 
                exc_info=True
            )

    def _create_settings_widgets(self, parent: tk.Frame) -> None:
        try:
            for widget in parent.winfo_children():
                widget.destroy()
            
            row: int = 0
            padx: int = UIConfig.SETTINGS_PADDING_X
            pady_section: int = UIConfig.SETTINGS_PADDING_Y
            pady_item: int = 12
            
            self._create_section_header(parent, self._lang.get('language'), row)
            row += 1
            self._create_language_combo(parent, row, padx)
            row += 1
            
            tk.Frame(
                parent, bg=self._colors['border'], height=1
            ).grid(row=row, column=0, sticky='ew', padx=padx, pady=pady_section)
            row += 1
            
            self._create_section_header(
                parent, self._lang.get('video_backend'), row
            )
            row += 1
            self._create_backend_combo(parent, row, padx)
            row += 1
            
            tk.Frame(
                parent, bg=self._colors['border'], height=1
            ).grid(row=row, column=0, sticky='ew', padx=padx, pady=pady_section)
            row += 1
            
            self._create_input_section(
                parent, row, 'max_videos',
                PerformanceConfig.MAX_VIDEOS_MIN,
                PerformanceConfig.MAX_VIDEOS_MAX,
                PerformanceConfig.MAX_VIDEOS_DEFAULT, 
                padx, "videos"
            )
            row += 1
            
            self._create_input_section(
                parent, row, 'max_fps',
                PerformanceConfig.MIN_FPS,
                PerformanceConfig.MAX_FPS,
                PerformanceConfig.DEFAULT_FPS, 
                padx, "FPS"
            )
            row += 1
            
            self._create_input_section(
                parent, row, 'min_video_size',
                PerformanceConfig.MIN_VIDEO_SIZE_MIN,
                PerformanceConfig.MIN_VIDEO_SIZE_MAX,
                PerformanceConfig.MIN_VIDEO_SIZE_DEFAULT, 
                padx, "px"
            )
            row += 1
            
            self._create_input_section(
                parent, row, 'queue_size', 1, 5, 1, padx, "frames"
            )
            row += 1
            
            tk.Frame(
                parent, bg=self._colors['border'], height=1
            ).grid(row=row, column=0, sticky='ew', padx=padx, pady=pady_section)
            row += 1
            
            self._create_section_header(
                parent, self._lang.get('optimization'), row
            )
            row += 1
            self._create_optimization_section(parent, row, padx)
            row += 1
            
            tk.Frame(
                parent, bg=self._colors['border'], height=1
            ).grid(row=row, column=0, sticky='ew', padx=padx, pady=pady_section)
            row += 1
            
            self._create_section_header(
                parent, self._lang.get('resize_quality'), row
            )
            row += 1
            self._create_quality_section(parent, row, padx)
            row += 1
            
            self._create_section_header(parent, self._lang.get('theme'), row)
            row += 1
            self._create_theme_section(parent, row, padx)
            row += 1
            
            tk.Frame(
                parent, bg=self._colors['border'], height=1
            ).grid(row=row, column=0, sticky='ew', padx=padx, pady=pady_section)
            row += 1
            
            self._create_section_header(parent, self._lang.get('opacity'), row)
            row += 1
            self._create_opacity_section(parent, row, padx)
            row += 1
            
            tk.Frame(
                parent, bg=self._colors['border'], height=1
            ).grid(row=row, column=0, sticky='ew', padx=padx, pady=pady_section)
            row += 1
            
            self._create_input_section(
                parent, row, 'open_delay',
                PerformanceConfig.OPEN_DELAY_MIN,
                PerformanceConfig.OPEN_DELAY_MAX,
                PerformanceConfig.OPEN_DELAY_DEFAULT, 
                padx, "ms"
            )
            row += 1
            
            save_btn: tk.Button = self._create_modern_button(
                parent, self._lang.get('apply_settings'),
                self._save_settings, is_primary=True
            )
            save_btn.grid(row=row, column=0, padx=padx, pady=30, sticky='ew')
            
        except tk.TclError as e:
            logger.error(f"Error creating settings widgets: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error creating widgets: {e}", 
                exc_info=True
            )

    def _create_section_header(
        self, parent: tk.Frame, text: str, row: int
    ) -> None:
        header_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        header_frame.grid(
            row=row, column=0, sticky='w', padx=UIConfig.SETTINGS_PADDING_X, 
            pady=(20, 8)
        )
        
        label: tk.Label = tk.Label(
            header_frame, text=text.upper(), 
            bg=self._colors['bg_secondary'],
            fg=self._colors['accent'], 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL, 'bold')
        )
        label.pack(side=tk.LEFT)
        
        line: tk.Frame = tk.Frame(
            header_frame, bg=self._colors['border'], height=1
        )
        line.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(15, 0))

    def _create_language_combo(
        self, parent: tk.Frame, row: int, padx: int
    ) -> None:
        self._language_var: tk.StringVar = tk.StringVar(
            value=self._settings.get('language', 'en')
        )
        lang_options: List[Tuple[str, str]] = (
            self._lang.get_available_languages()
        )
        
        lang_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        lang_frame.grid(row=row, column=0, sticky='w', padx=padx, pady=10)
        
        lang_values: List[str] = [text for value, text in lang_options]
        self._language_combo: ttk.Combobox = ttk.Combobox(
            lang_frame, textvariable=self._language_var,
            values=lang_values, state='readonly', 
            width=UIConfig.BUTTON_WIDTH_MEDIUM,
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL)
        )
        self._language_combo.pack()
        
        for value, text in lang_options:
            if value == self._settings.get('language', 'en'):
                self._language_combo.set(text)
                break

    def _create_backend_combo(
        self, parent: tk.Frame, row: int, padx: int
    ) -> None:
        self._backend_var: tk.StringVar = tk.StringVar(
            value=self._settings.get('backend', 'AUTO')
        )
        
        backend_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        backend_frame.grid(row=row, column=0, sticky='w', padx=padx, pady=10)
        
        backends: List[Tuple[str, str]] = [
            ('AUTO', self._lang.get('backend_auto')),
            ('FFMPEG', self._lang.get('backend_ffmpeg')),
            ('MSMF', self._lang.get('backend_msmf')),
            ('DSHOW', self._lang.get('backend_dshow')),
        ]
        
        backend_values: List[str] = [text for value, text in backends]
        self._backend_combo: ttk.Combobox = ttk.Combobox(
            backend_frame, textvariable=self._backend_var,
            values=backend_values, state='readonly',
            width=UIConfig.BUTTON_WIDTH_MEDIUM,
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL)
        )
        self._backend_combo.pack()
        
        for value, text in backends:
            if value == self._settings.get('backend', 'AUTO'):
                self._backend_combo.set(text)
                break

    def _create_input_section(
        self, 
        parent: tk.Frame, 
        row: int, 
        key: str,
        min_val: int, 
        max_val: int, 
        default: int,
        padx: int, 
        unit: str
    ) -> None:
        label_text: str = self._lang.get(key)
        
        input_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        input_frame.grid(row=row, column=0, sticky='ew', padx=padx, pady=10)
        
        label: tk.Label = tk.Label(
            input_frame, text=label_text, 
            bg=self._colors['bg_secondary'],
            fg=self._colors['text_primary'], 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL)
        )
        label.pack(side=tk.LEFT)
        
        var: tk.IntVar = tk.IntVar(value=self._settings.get(key, default))
        setattr(self, f"_{key}_var", var)
        
        right_frame: tk.Frame = tk.Frame(
            input_frame, bg=self._colors['bg_secondary']
        )
        right_frame.pack(side=tk.RIGHT)
        
        entry: tk.Entry = tk.Entry(
            right_frame, textvariable=var, width=UIConfig.INPUT_WIDTH,
            bg=self._colors['input_bg'], fg=self._colors['input_fg'],
            font=(UIConfig.FONT_FAMILY, UIConfig.INPUT_FONT_SIZE, 'bold'),
            relief=tk.FLAT, bd=0,
            highlightbackground=self._colors['input_border'],
            highlightthickness=UIConfig.INPUT_BORDER_WIDTH,
            justify='center',
            highlightcolor=self._colors['input_border_focus']
        )
        entry.pack(side=tk.LEFT, padx=(10, 5))
        
        entry.bind(
            '<FocusIn>', 
            lambda e: entry.configure(
                highlightbackground=self._colors['input_border_focus']
            )
        )
        entry.bind(
            '<FocusOut>', 
            lambda e: entry.configure(
                highlightbackground=self._colors['input_border']
            )
        )
        
        unit_label: tk.Label = tk.Label(
            right_frame, text=unit, 
            bg=self._colors['bg_secondary'],
            fg=self._colors['text_secondary'], 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
        )
        unit_label.pack(side=tk.LEFT)

    def _create_optimization_section(
        self, parent: tk.Frame, row: int, padx: int
    ) -> None:
        opt_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        opt_frame.grid(row=row, column=0, sticky='ew', padx=padx, pady=10)
        
        self._skip_frames_var: tk.BooleanVar = tk.BooleanVar(
            value=self._settings.get('skip_frames', True)
        )
        cb: tk.Checkbutton = tk.Checkbutton(
            opt_frame, text=self._lang.get('skip_frames'),
            variable=self._skip_frames_var,
            bg=self._colors['bg_secondary'], 
            fg=self._colors['text_primary'],
            selectcolor=self._colors['accent'],
            activebackground=self._colors['bg_secondary'],
            activeforeground=self._colors['text_primary'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL), 
            indicatoron=0, width=40,
            relief=tk.FLAT, bd=2, padx=10, pady=5
        )
        cb.pack(anchor='w', pady=(0, 10))
        
        threshold_frame: tk.Frame = tk.Frame(
            opt_frame, bg=self._colors['bg_secondary']
        )
        threshold_frame.pack(anchor='w', fill=tk.X)
        
        threshold_label: tk.Label = tk.Label(
            threshold_frame, text=self._lang.get('optimize_threshold'),
            bg=self._colors['bg_secondary'], 
            fg=self._colors['text_secondary'],
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
        )
        threshold_label.pack(side=tk.LEFT)
        
        self._optimize_threshold_var: tk.IntVar = tk.IntVar(
            value=self._settings.get(
                'optimize_threshold', 
                PerformanceConfig.OPTIMIZE_THRESHOLD_DEFAULT
            )
        )
        
        entry_frame: tk.Frame = tk.Frame(
            threshold_frame, bg=self._colors['bg_secondary']
        )
        entry_frame.pack(side=tk.RIGHT)
        
        entry: tk.Entry = tk.Entry(
            entry_frame, textvariable=self._optimize_threshold_var, 
            width=UIConfig.INPUT_WIDTH,
            bg=self._colors['input_bg'], fg=self._colors['input_fg'],
            font=(UIConfig.FONT_FAMILY, UIConfig.INPUT_FONT_SIZE, 'bold'),
            relief=tk.FLAT, bd=0,
            highlightbackground=self._colors['input_border'],
            highlightthickness=UIConfig.INPUT_BORDER_WIDTH,
            justify='center',
            highlightcolor=self._colors['input_border_focus']
        )
        entry.pack(side=tk.LEFT, padx=(10, 5))
        
        entry.bind(
            '<FocusIn>', 
            lambda e: entry.configure(
                highlightbackground=self._colors['input_border_focus']
            )
        )
        entry.bind(
            '<FocusOut>', 
            lambda e: entry.configure(
                highlightbackground=self._colors['input_border']
            )
        )
        
        unit_label: tk.Label = tk.Label(
            entry_frame, text="videos", 
            bg=self._colors['bg_secondary'],
            fg=self._colors['text_secondary'], 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_SMALL)
        )
        unit_label.pack(side=tk.LEFT)

    def _create_quality_section(
        self, parent: tk.Frame, row: int, padx: int
    ) -> None:
        self._resize_quality_var: tk.StringVar = tk.StringVar(
            value=self._settings.get(
                'resize_quality', self._lang.get('quality_medium')
            )
        )
        
        quality_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        quality_frame.grid(row=row, column=0, sticky='w', padx=padx, pady=10)
        
        quality_combo: ttk.Combobox = ttk.Combobox(
            quality_frame, textvariable=self._resize_quality_var,
            values=[
                self._lang.get('quality_low'),
                self._lang.get('quality_medium'),
                self._lang.get('quality_high')
            ],
            state='readonly', width=UIConfig.BUTTON_WIDTH_MEDIUM, 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL)
        )
        quality_combo.pack()

    def _create_theme_section(
        self, parent: tk.Frame, row: int, padx: int
    ) -> None:
        self._theme_var: tk.StringVar = tk.StringVar(
            value=self._settings.get('theme', 'dark')
        )
        
        theme_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        theme_frame.grid(row=row, column=0, sticky='w', padx=padx, pady=10)
        
        theme_combo: ttk.Combobox = ttk.Combobox(
            theme_frame, textvariable=self._theme_var,
            values=['dark', 'light'],
            state='readonly', width=UIConfig.BUTTON_WIDTH_MEDIUM, 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL)
        )
        theme_combo.pack()

    def _create_opacity_section(
        self, parent: tk.Frame, row: int, padx: int
    ) -> None:
        opacity_value: float = self._settings.get('opacity', 1.0)
        opacity_percent: int = int(opacity_value * 100)
        
        self._opacity_var: tk.StringVar = tk.StringVar(
            value=str(opacity_percent)
        )
        
        opacity_frame: tk.Frame = tk.Frame(
            parent, bg=self._colors['bg_secondary']
        )
        opacity_frame.grid(row=row, column=0, sticky='w', padx=padx, pady=10)
        
        entry: tk.Entry = tk.Entry(
            opacity_frame, textvariable=self._opacity_var, 
            width=UIConfig.INPUT_WIDTH,
            bg=self._colors['input_bg'], fg=self._colors['input_fg'],
            font=(UIConfig.FONT_FAMILY, UIConfig.INPUT_FONT_SIZE, 'bold'),
            relief=tk.FLAT, bd=0,
            highlightbackground=self._colors['input_border'],
            highlightthickness=UIConfig.INPUT_BORDER_WIDTH,
            justify='center',
            highlightcolor=self._colors['input_border_focus']
        )
        entry.pack(side=tk.LEFT, padx=(10, 5))
        
        entry.bind(
            '<FocusIn>', 
            lambda e: entry.configure(
                highlightbackground=self._colors['input_border_focus']
            )
        )
        entry.bind(
            '<FocusOut>', 
            lambda e: entry.configure(
                highlightbackground=self._colors['input_border']
            )
        )
        
        percent_label: tk.Label = tk.Label(
            opacity_frame, text="%", 
            bg=self._colors['bg_secondary'],
            fg=self._colors['text_secondary'], 
            font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL, 'bold')
        )
        percent_label.pack(side=tk.LEFT)

    def _create_modern_button(
        self, 
        parent: tk.Frame, 
        text: str, 
        command: Callable[[], None],
        is_primary: bool = False
    ) -> tk.Button:
        if is_primary:
            btn: tk.Button = tk.Button(
                parent, text=text, command=command,
                bg=self._colors['accent'], fg='#ffffff',
                font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_BUTTON, 'bold'),
                padx=UIConfig.BUTTON_WIDTH_LARGE, 
                pady=UIConfig.BUTTON_PADY, 
                relief=tk.FLAT, cursor='hand2',
                activebackground=self._colors['accent_hover'],
                activeforeground='#ffffff'
            )
        else:
            btn = tk.Button(
                parent, text=text, command=command,
                bg=self._colors['bg_tertiary'], 
                fg=self._colors['text_primary'],
                font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_BUTTON),
                padx=UIConfig.BUTTON_WIDTH_LARGE, 
                pady=UIConfig.BUTTON_PADY, 
                relief=tk.FLAT, cursor='hand2',
                activebackground=self._colors['bg_hover'],
                activeforeground=self._colors['text_primary']
            )
        
        btn.bind(
            '<Enter>', 
            lambda e: btn.configure(
                bg=self._colors['accent_hover'] if is_primary
                else self._colors['bg_hover']
            )
        )
        btn.bind(
            '<Leave>', 
            lambda e: btn.configure(
                bg=self._colors['accent'] if is_primary
                else self._colors['bg_tertiary']
            )
        )
        return btn

    def _save_settings(self) -> None:
        try:
            lang_value: str = self._settings.get('language', 'en')
            for value, text in self._lang.get_available_languages():
                if text == self._language_var.get():
                    lang_value = value
                    break
            
            backend_value: str = self._settings.get('backend', 'AUTO')
            backends: List[Tuple[str, str]] = [
                ('AUTO', self._lang.get('backend_auto')),
                ('FFMPEG', self._lang.get('backend_ffmpeg')),
                ('MSMF', self._lang.get('backend_msmf')),
                ('DSHOW', self._lang.get('backend_dshow'))
            ]
            for value, text in backends:
                if text == self._backend_var.get():
                    backend_value = value
                    break
            
            opacity_str: str = self._opacity_var.get()
            opacity_percent: int = 100
            if opacity_str and opacity_str.strip():
                try:
                    opacity_percent = int(opacity_str)
                    opacity_percent = max(
                        int(WindowConfig.OPACITY_MIN * 100),
                        min(int(WindowConfig.OPACITY_MAX * 100), opacity_percent)
                    )
                except ValueError:
                    logger.warning(f"Invalid opacity value: {opacity_str}")
                    opacity_percent = 100
            
            opacity_value: float = opacity_percent / 100.0
            
            max_videos: int = 64
            try:
                max_videos = self._max_videos_var.get()
            except (tk.TclError, AttributeError) as e:
                logger.warning(f"Could not get max_videos: {e}")
            
            max_fps: int = 60
            try:
                max_fps = self._max_fps_var.get()
            except (tk.TclError, AttributeError) as e:
                logger.warning(f"Could not get max_fps: {e}")
            
            min_video_size: int = 150
            try:
                min_video_size = self._min_video_size_var.get()
            except (tk.TclError, AttributeError) as e:
                logger.warning(f"Could not get min_video_size: {e}")
            
            queue_size: int = 1
            try:
                queue_size = self._queue_size_var.get()
            except (tk.TclError, AttributeError) as e:
                logger.warning(f"Could not get queue_size: {e}")
            
            optimize_threshold: int = 16
            try:
                optimize_threshold = self._optimize_threshold_var.get()
            except (tk.TclError, AttributeError) as e:
                logger.warning(f"Could not get optimize_threshold: {e}")
            
            open_delay: int = 0
            try:
                open_delay = self._open_delay_var.get()
            except (tk.TclError, AttributeError) as e:
                logger.warning(f"Could not get open_delay: {e}")
            
            self._settings.update({
                'language': lang_value,
                'backend': backend_value,
                'max_videos': max_videos,
                'max_fps': max_fps,
                'min_video_size': min_video_size,
                'resize_quality': self._resize_quality_var.get(),
                'queue_size': queue_size,
                'optimize_threshold': optimize_threshold,
                'skip_frames': self._skip_frames_var.get(),
                'theme': self._theme_var.get(),
                'opacity': opacity_value,
                'open_delay': open_delay,
            })
            self._settings.save()
            self._on_save()
            self._show_notification(self._lang.get('settings_saved'))
        except json.JSONDecodeError as e:
            logger.error(f"JSON error saving settings: {e}")
        except OSError as e:
            logger.error(f"OS error saving settings: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving settings: {e}", exc_info=True)

    def _show_notification(self, message: str) -> None:
        try:
            notification: tk.Toplevel = tk.Toplevel(self._window)
            notification.overrideredirect(True)
            notification.configure(bg=self._colors['accent'])
            x: int = self._window.winfo_rootx() + (
                ColorConfig.NOTIFICATION_WIDTH // 2
            ) - 100
            y: int = self._window.winfo_rooty() + ColorConfig.NOTIFICATION_OFFSET_Y
            notification.geometry(
                f"{ColorConfig.NOTIFICATION_WIDTH}x"
                f"{ColorConfig.NOTIFICATION_HEIGHT}+{x}+{y}"
            )
            
            notification.configure(
                highlightbackground=self._colors['border_focus'],
                highlightthickness=2
            )
            
            tk.Label(
                notification, text=message, 
                bg=self._colors['accent'], fg='#ffffff',
                font=(UIConfig.FONT_FAMILY, UIConfig.FONT_SIZE_LABEL, 'bold')
            ).pack(expand=True, fill=tk.BOTH)
            notification.after(ColorConfig.NOTIFICATION_DURATION, notification.destroy)
        except tk.TclError:
            pass  # Window may be closed
        except Exception as e:
            logger.debug(f"Could not show notification: {e}")

    def show(self) -> None:
        try:
            if not self._is_visible or self._window is None:
                self._create_window()
                self._window.lift()
                self._window.focus_force()
        except tk.TclError as e:
            logger.error(f"Error showing settings window: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error showing window: {e}", 
                exc_info=True
            )

    def hide(self) -> None:
        try:
            if self._is_visible and self._window is not None:
                self._window.withdraw()
                self._is_visible = False
        except tk.TclError as e:
            logger.error(f"Error hiding settings window: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error hiding window: {e}", 
                exc_info=True
            )

    def toggle(self) -> None:
        try:
            if self._is_visible:
                self.hide()
            else:
                self.show()
        except tk.TclError as e:
            logger.error(f"Error toggling settings window: {e}")
        except Exception as e:
            logger.error(
                f"Unexpected error toggling window: {e}", 
                exc_info=True
            )

    def set_theme(self, is_dark: bool) -> None:
        self._colors = ThemeColors.DARK if is_dark else ThemeColors.LIGHT
        if self._window:
            self._window.configure(bg=self._colors['bg_secondary'])