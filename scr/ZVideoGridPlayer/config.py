"""Application configuration constants."""
from typing import Final


class UIConfig:
    """UI layout and dimension constants."""
    
    # Window dimensions - УВЕЛИЧЕНО НА 40%
    WINDOW_WIDTH: Final[int] = 1820      # Было 1300, стало 1820 (+40%)
    WINDOW_HEIGHT: Final[int] = 850       # Без изменений
    WINDOW_MIN_WIDTH: Final[int] = 800
    WINDOW_MIN_HEIGHT: Final[int] = 600
    
    # Title bar
    TITLE_BAR_HEIGHT: Final[int] = 32
    TITLE_BAR_BG: Final[str] = '#1c1c1c'
    
    # Settings panel - УВЕЛИЧЕНО НА 40%
    SETTINGS_PANEL_WIDTH: Final[int] = 450   # Было 320, стало 450 (+40%)
    SETTINGS_PANEL_HEIGHT: Final[int] = 840  # Было 600, стало 840 (+40%)
    SETTINGS_PADDING_X: Final[int] = 25      # Увеличено с 15
    SETTINGS_PADDING_Y: Final[int] = 15      # Увеличено с 10
    
    # Control panel - УВЕЛИЧЕНО НА 40%
    CONTROL_PANEL_HEIGHT: Final[int] = 140   # Было 120, стало 140
    CONTROL_PANEL_PADDING: Final[int] = 15   # Увеличено с 10
    
    # Canvas
    CANVAS_MARGIN: Final[int] = 20
    VIDEO_SPACING: Final[int] = 6
    VIDEO_BORDER_WIDTH: Final[int] = 1
    
    # Video grid
    VIDEO_MIN_SIZE: Final[int] = 150
    VIDEO_MIN_SIZE_HALF: Final[int] = 75
    MAX_COLUMNS: Final[int] = 16
    DEFAULT_COLUMNS: Final[int] = 4  # Увеличено с 3 для большего окна
    
    # Resize handles
    RESIZE_HANDLE_SIZE: Final[int] = 10
    RESIZE_HANDLE_EDGE_WIDTH: Final[int] = 4
    
    # Fonts
    FONT_FAMILY: Final[str] = 'Segoe UI'
    FONT_SIZE_TITLE: Final[int] = 14   # Увеличено с 12
    FONT_SIZE_BUTTON: Final[int] = 11  # Увеличено с 10
    FONT_SIZE_LABEL: Final[int] = 11   # Увеличено с 10
    FONT_SIZE_SMALL: Final[int] = 9
    
    # Button dimensions - УВЕЛИЧЕНО НА 40%
    BUTTON_PADX: Final[int] = 20       # Было 15, стало 20
    BUTTON_PADY: Final[int] = 10       # Было 8, стало 10
    BUTTON_WIDTH_SMALL: Final[int] = 15
    BUTTON_WIDTH_MEDIUM: Final[int] = 30  # Увеличено с 25
    BUTTON_WIDTH_LARGE: Final[int] = 35   # Увеличено с 30
    
    # Input field - УВЕЛИЧЕНО НА 40%
    INPUT_WIDTH: Final[int] = 10       # Было 8, стало 10
    INPUT_FONT_SIZE: Final[int] = 14   # Было 13, стало 14
    INPUT_BORDER_WIDTH: Final[int] = 2
    
    # Scrollbar
    SCROLLBAR_WIDTH: Final[int] = 12


class PerformanceConfig:
    """Performance and timing constants."""
    
    # Video playback
    DEFAULT_FPS: Final[int] = 30
    MAX_FPS: Final[int] = 60
    MIN_FPS: Final[int] = 1
    FRAME_QUEUE_SIZE: Final[int] = 1
    
    # Threading
    THREAD_EXIT_TIMEOUT: Final[float] = 0.3
    THREAD_PAUSE_SLEEP: Final[float] = 0.01
    THREAD_READ_RETRY: Final[int] = 3
    
    # Timing
    UPDATE_TIMER_MIN_INTERVAL: Final[int] = 10
    WINDOW_RESIZE_DELAY: Final[int] = 100
    TITLE_BAR_RESTORE_DELAY: Final[int] = 50
    MAXIMIZE_UPDATE_DELAY: Final[int] = 100
    
    # Optimization
    OPTIMIZE_THRESHOLD_MIN: Final[int] = 4
    OPTIMIZE_THRESHOLD_MAX: Final[int] = 32
    OPTIMIZE_THRESHOLD_DEFAULT: Final[int] = 16
    
    # Video open delay (ms)
    OPEN_DELAY_MIN: Final[int] = 0
    OPEN_DELAY_MAX: Final[int] = 500
    OPEN_DELAY_DEFAULT: Final[int] = 50
    
    # Frame skip
    SKIP_FRAMES_DEFAULT: Final[bool] = True
    
    # Video limits
    MAX_VIDEOS_MIN: Final[int] = 0
    MAX_VIDEOS_MAX: Final[int] = 256
    MAX_VIDEOS_DEFAULT: Final[int] = 64
    
    # Min video size
    MIN_VIDEO_SIZE_MIN: Final[int] = 80
    MIN_VIDEO_SIZE_MAX: Final[int] = 300
    MIN_VIDEO_SIZE_DEFAULT: Final[int] = 150
    MIN_VIDEO_SIZE_HALF: Final[int] = 75
    
    # Queue size
    QUEUE_SIZE_MIN: Final[int] = 1
    QUEUE_SIZE_MAX: Final[int] = 5
    QUEUE_SIZE_DEFAULT: Final[int] = 1


class WindowConfig:
    """Window behavior constants."""
    
    # Opacity
    OPACITY_MIN: Final[float] = 0.5
    OPACITY_MAX: Final[float] = 1.0
    OPACITY_DEFAULT: Final[float] = 1.0
    OPACITY_STEP: Final[float] = 0.05
    
    # Window controls
    MIN_WINDOW_WIDTH: Final[int] = 800
    MIN_WINDOW_HEIGHT: Final[int] = 600
    
    # Corner radius (Windows 11)
    DWMWA_WINDOW_CORNER_PREFERENCE: Final[int] = 33
    DWM_WINDOW_CORNER_PREFERENCE_ROUND: Final[int] = 2
    
    # Monitor detection
    MONITOR_DEFAULT: Final[int] = 2  # MONITOR_DEFAULTTONEAREST
    
    # Timing delays
    TITLE_BAR_RESTORE_DELAY: Final[int] = 50
    MAXIMIZE_UPDATE_DELAY: Final[int] = 100


class ColorConfig:
    """Color constants (referenced from ThemeColors)."""
    
    # Common
    BLACK: Final[str] = '#000000'
    WHITE: Final[str] = '#ffffff'
    TRANSPARENT: Final[str] = '#00000000'
    
    # Notification
    NOTIFICATION_WIDTH: Final[int] = 200
    NOTIFICATION_HEIGHT: Final[int] = 40
    NOTIFICATION_DURATION: Final[int] = 1500
    NOTIFICATION_OFFSET_Y: Final[int] = 50


class PathConfig:
    """File and path constants."""
    
    # Settings
    SETTINGS_FILENAME: Final[str] = 'settings.json'
    
    # Languages
    LANG_FOLDER_NAME: Final[str] = 'lang'
    LANG_FILE_EXTENSION: Final[str] = '.json'
    
    # Video extensions
    VIDEO_EXTENSIONS: Final[tuple[str, ...]] = (
        '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v'
    )
    
    # Icon
    ICON_FILENAME_ICO: Final[str] = 'icon.ico'
    ICON_FILENAME_PNG: Final[str] = 'icon.png'