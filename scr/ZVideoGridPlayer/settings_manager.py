"""Settings management with JSON persistence."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages application settings with automatic save/load."""
    
    # Базовые размеры (будут увеличены на 40% если нужно)
    BASE_WINDOW_WIDTH: int = 1300
    BASE_WINDOW_HEIGHT: int = 850
    BASE_SETTINGS_WIDTH: int = 320
    BASE_SETTINGS_HEIGHT: int = 600
    
    DEFAULT_SETTINGS: Dict[str, Any] = {
        'backend': 'AUTO',
        'max_videos': 64,
        'max_fps': 60,
        'min_video_size': 150,
        'resize_quality': 'Medium',
        'queue_size': 1, 
        'optimize_threshold': 16,
        'skip_frames': True,
        'theme': 'dark',
        'opacity': 1.0,
        'auto_save': True,
        'open_delay': 50,
        'language': 'en',
        'max_cols': 16,
        'default_fps': 30,
        'default_cols': 3,
        'show_names': False,
        'optimization_enabled': True,
        # Размеры окон (добавлено)
        'window_width': 1820,  # 1300 * 1.4 = 1820
        'window_height': 1190,  # 850 * 1.4 = 1190
        'settings_width': 448,  # 320 * 1.4 = 448
        'settings_height': 840,  # 600 * 1.4 = 840
    }

    def __init__(self, settings_path: Optional[str] = None) -> None:
        """Initialize settings manager."""
        if settings_path:
            self._settings_path = Path(settings_path)
        else:
            self._settings_path = Path(__file__).parent.parent.parent / 'settings.json'
        self._settings: Dict[str, Any] = self.DEFAULT_SETTINGS.copy()
        self._load()
        logger.info(f"Settings path: {self._settings_path}")

    def _load(self) -> None:
        """Load settings from JSON file."""
        try:
            if self._settings_path.exists():
                with open(self._settings_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
                logger.info(f"Settings loaded from {self._settings_path}")
            else:
                self.save()
                logger.info(f"Settings file created: {self._settings_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading settings: {e}")
            self.save()

    def save(self) -> None:
        """Save settings to JSON file."""
        if not self._settings.get('auto_save', True):
            return
        
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            logger.info(f"Settings saved to {self._settings_path}")
        except OSError as e:
            logger.error(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple settings at once ."""
        self._settings.update(updates)

    @property
    def all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()