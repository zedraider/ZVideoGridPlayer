"""Language management module with full localization support."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

from .config import PathConfig

logger: logging.Logger = logging.getLogger(__name__)


class LanguageManager:
    """Manages application localization with JSON language files."""
    
    FALLBACK_TRANSLATIONS: Dict[str, str] = {
        "app_title": "ZVideoGridPlayer",
        "settings_title": "⚙️ SETTINGS",
        "language": "Interface language:",
        "lang_ru": "Русский",
        "lang_en": "English",
        "lang_zh": "中文",
        "video_backend": "Video Backend:",
        "backend_auto": "Auto (recommended)",
        "backend_ffmpeg": "FFMPEG (universal)",
        "backend_msmf": "Microsoft Media Foundation",
        "backend_dshow": "DirectShow (classic)",
        "max_videos": "Max. number of videos:",
        "max_fps": "Maximum FPS:",
        "min_video_size": "Minimum video size (px):",
        "resize_quality": "Scaling quality:",
        "quality_low": "Low (fast)",
        "quality_medium": "Medium",
        "quality_high": "High (slow)",
        "queue_size": "Frame queue size:",
        "optimize_threshold": "Optimization threshold:",
        "skip_frames": "Skip frames under high load",
        "theme": "Color theme:",
        "theme_dark": "Dark",
        "theme_light": "Light",
        "opacity": "Window opacity:",
        "open_delay": "Delay between video opens (ms):",
        "apply_settings": "💾 Apply Settings",
        "settings_saved": "Settings saved",
        "select_folder": "📁 Select Folder",
        "start": "▶ Start",
        "pause": "⏸ Pause",
        "resume": "▶ Resume",
        "stop": "⏹ Stop",
        "settings": "⚙️ Settings",
        "hide_panel": "🔽 Hide Panel",
        "no_videos": "No videos loaded",
        "fps_label": "🎬 FPS:",
        "cols_label": "📐 Columns:",
        "apply": "Apply",
        "show_names": "📝 File names",
        "optimization": "⚡ Optimization",
        "hotkeys": "⌨️ Space:Pause/Resume | S:Stop | P:Pause all | R:Resume all | F:Fullscreen | H:Hide Panel | F1:Settings",
        "warning_no_videos": "No videos found!",
        "warning_load_first": "Load videos first!",
        "error_open_video": "Failed to open video!",
        "videos_info": "📹 {} | {} columns",
        "error_loading_lang": "Error loading language file",
    }

    def __init__(self) -> None:
        """Initialize language manager with available translations."""
        self._current_language: str = 'en'
        self._translations: Dict[str, Dict[str, str]] = {}
        self._language_names: Dict[str, str] = {}
        self._load_languages()

    def _find_lang_folder(self) -> Path:
        """Find the language folder in project root."""
        script_path: Path = Path(__file__).resolve()
        project_root: Path = script_path.parent.parent.parent
        
        lang_dir: Path = project_root / PathConfig.LANG_FOLDER_NAME
        
        if not lang_dir.exists():
            try:
                lang_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created lang folder: {lang_dir}")
            except OSError as e:
                logger.error(f"Could not create lang folder: {e}")
        
        return lang_dir

    def _load_languages(self) -> None:
        """Load all language JSON files from the lang folder."""
        lang_dir: Path = self._find_lang_folder()
        
        if not lang_dir.exists():
            self._translations = {'en': self.FALLBACK_TRANSLATIONS.copy()}
            self._language_names = {'en': 'English'}
            return
        
        json_files: List[Path] = list(lang_dir.glob(f"*{PathConfig.LANG_FILE_EXTENSION}"))
        
        if not json_files:
            self._create_default_lang_files(lang_dir)
            json_files = list(lang_dir.glob(f"*{PathConfig.LANG_FILE_EXTENSION}"))
        
        for lang_file in json_files:
            lang_code: str = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self._translations[lang_code] = json.load(f)
                    
                    lang_name_key: str = f'lang_{lang_code}'
                    self._language_names[lang_code] = self._translations[lang_code].get(
                        lang_name_key, lang_code.upper()
                    )
                    logger.debug(f"Loaded language: {lang_code}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON error loading {lang_file}: {e}")
                self._translations[lang_code] = {}
                self._language_names[lang_code] = lang_code.upper()
            except OSError as e:
                logger.error(f"OS error loading {lang_file}: {e}")
                self._translations[lang_code] = {}
                self._language_names[lang_code] = lang_code.upper()
            except Exception as e:
                logger.error(f"Unexpected error loading {lang_file}: {e}")
                self._translations[lang_code] = {}
                self._language_names[lang_code] = lang_code.upper()
        
        if not self._translations:
            self._create_default_lang_files(lang_dir)
            self._translations = {'en': self.FALLBACK_TRANSLATIONS.copy()}
            self._language_names = {'en': 'English'}

    def _create_default_lang_files(self, lang_dir: Path) -> None:
        """Create default language files."""
        en_path: Path = lang_dir / 'en.json'
        if not en_path.exists():
            try:
                with open(en_path, 'w', encoding='utf-8') as f:
                    json.dump(self.FALLBACK_TRANSLATIONS, f, indent=4, ensure_ascii=False)
                logger.info(f"Created default language file: {en_path}")
            except OSError as e:
                logger.error(f"Could not create {en_path}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error creating {en_path}: {e}")

    def set_language(self, lang_code: str) -> None:
        """Set the current language."""
        if lang_code in self._translations:
            self._current_language = lang_code
            logger.info(f"Language set to: {lang_code}")
        else:
            logger.warning(f"Language {lang_code} not found")

    def get(self, key: str, *args: Any) -> str:
        """Get a translated string, optionally formatting with args."""
        lang_data: Dict[str, str] = self._translations.get(self._current_language, {})
        value: str = lang_data.get(key, self.FALLBACK_TRANSLATIONS.get(key, key))
        
        if args and '{}' in value:
            try:
                return value.format(*args)
            except (IndexError, KeyError):
                return value
        return value

    def get_available_languages(self) -> List[Tuple[str, str]]:
        """Return list of (language_code, display_name) tuples."""
        return [(code, name) for code, name in self._language_names.items()]

    @property
    def current_language(self) -> str:
        """Get current language code."""
        return self._current_language