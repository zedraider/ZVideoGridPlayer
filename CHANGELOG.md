# Changelog

## [1.2.1] - 2026-04-29

### Added
- Windows batch launcher (`start.bat`) with validation
- Standalone `.exe` build with PyInstaller
- Automatic creation of `lang` folder and `settings.json` on first run
- Application icon support

### Changed
- Improved path handling for frozen executables
- Settings and language files now work from any installation location

### Fixed
- Language files loading from executable directory
- Settings persistence in standalone build
- Relative imports for PyInstaller compatibility

## [1.2.0] - 2026-03-31

### ✨ Added
- Modern UI with custom title bar and resize handles
- Full localization support (EN/RU)
- Dark/Light theme switching
- Settings persistence (JSON)
- Video grid optimization
- Hotkey support

### 🐛 Fixed
- Window resize handling
- Video playback synchronization
- Settings save/load errors

### ⚡ Improved
- UI scaling (+40% for better visibility)
- Performance optimization for multiple videos
- Frame queue management

## [1.0.0] - 2026-01
- Initial release