# ZVideoGridPlayer 🎬

[English](#english) | [Русский](#russian)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d7)](https://www.microsoft.com/windows)
[![GitHub stars](https://img.shields.io/github/stars/zedraider/ZVideoGridPlayer?style=social)](https://github.com/zedraider/ZVideoGridPlayer/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/zedraider/ZVideoGridPlayer?style=social)](https://github.com/zedraider/ZVideoGridPlayer/network/members)

---

<a name="english"></a>
## English

**Multi-video grid player for Windows**  
Watch multiple videos simultaneously in a dynamic masonry layout. Perfect for surveillance monitoring, video comparison, and managing large video collections.

### ✨ Features

#### 🖥️ Smart Grid Layout
- **Masonry-style arrangement** – videos automatically adjust height based on aspect ratio, saving up to 40% of screen space
- **8-edge window resizing** – resize from any corner or edge with native handles
- **Custom title bar** – modern window controls (minimize, maximize, close) with rounded corners (Windows 11)

#### 🎥 Advanced Video Playback
- **Wide format support** – MP4, AVI, MOV, MKV, FLV, WMV, M4V
- **Multiple backends** – Auto, FFMPEG, MSMF, DirectShow – switch anytime
- **Real-time aspect ratio** – videos scale correctly without distortion
- **Performance optimizations** – configurable FPS limit, frame skipping under load

#### 🌍 Localization
- **Multi-language support** – English, Russian, Chinese (easily extensible)
- **Instant language switching** – no restart required

#### ⚙️ Customizable Settings
- Video backend selection
- Maximum number of videos
- FPS limiter (1–120)
- Minimum video size (80–300 px)
- Scaling quality (Low/Medium/High)
- Theme: Dark / Light
- Window opacity (50–100%)
- Delay between video opens – prevents FFMPEG conflicts

#### ⌨️ Keyboard Shortcuts

| Key         | Action                 |
|-------------|------------------------|
| `Space`     | Play / Pause           |
| `S`         | Stop                   |
| `P`         | Pause all              |
| `R`         | Resume all             |
| `F`         | Toggle fullscreen      |
| `H`         | Hide/show control panel|
| `F1`        | Open settings          |

### 📦 Installation

#### Prerequisites
- **Python 3.10 or higher**
- **Windows 10/11** (for rounded corners and DWM features)

#### Step-by-Step

    # Clone the repository
    git clone https://github.com/zedraider/ZVideoGridPlayer.git
    cd ZVideoGridPlayer

    # Create and activate a virtual environment (recommended)
    python -m venv .venv
    .venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

    # Run the application
    python scr/ZVideoGridPlayer/ZVideoGridPlayer.py

#### `requirements.txt` (minimum)

    opencv-python>=4.8.0
    pillow>=10.0.0
    numpy>=1.24.0
    sv-ttk>=2.5.0   # optional: modern themed widgets

### 🗂️ Project Structure

    ZVideoGridPlayer/
    ├── scr/
    │   ├── ZVideoGridPlayer/
    │   │   ├── ZVideoGridPlayer.py   # main entry point
    │   │   └── oldver/               # archived versions
    │   └── lang/                     # language files
    │       ├── en.json
    │       ├── ru.json
    │       └── zh.json
    ├── .venv/                        # virtual environment (optional)
    ├── icon.ico                      # application icon
    ├── icon.png
    ├── requirements.txt
    ├── settings.json                 # auto-generated user settings
    └── README.md

### 🌐 Adding a New Language

1. Create a new file `lang/{code}.json` (e.g. `lang/fr.json`)
2. Copy the structure from `lang/en.json` and translate the values
3. Add a `"lang_{code}": "NativeName"` entry for the display name in settings
4. Restart the application – the new language will appear automatically

**Example `lang/fr.json`:**

    {
        "app_title": "ZVideoGridPlayer",
        "settings_title": "⚙️ PARAMÈTRES",
        "language": "Langue de l'interface:",
        "lang_fr": "Français",
        "select_folder": "📁 Sélectionner un dossier",
        "start": "▶ Démarrer"
    }

### 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| **FFMPEG assertion error** (`assertion fctx->async_lock failed`) | Increase **"Delay between video opens"** in settings (default 50 ms) |
| **Videos not loading** | Ensure file paths contain **only ASCII characters**; try a different backend (FFMPEG → MSMF → DirectShow) |
| **UI scaling issues** | Disable DPI scaling for `python.exe`: right‑click → Properties → Compatibility → Change high DPI settings |

### 🧑‍💻 Development

#### Code Style
- Follow **PEP 8** guidelines
- Use type hints where possible
- Keep functions under 50 lines when feasible

#### Adding Features
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add: your feature'`
4. Push and open a Pull Request

### 🤝 Contributing

Contributions are welcome! Feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add: AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

### 📬 Contact

**zedraider** – [GitHub Profile](https://github.com/zedraider)  
Project Link: [https://github.com/zedraider/ZVideoGridPlayer](https://github.com/zedraider/ZVideoGridPlayer)

---

<a name="russian"></a>
## Русский

**Мультивидео плеер с сеткой для Windows**  
Просматривайте несколько видео одновременно в динамическом макетe. Идеально подходит для видеонаблюдения, сравнения видео и управления большими коллекциями.

### ✨ Возможности

#### 🖥️ Умная сетка
- **Масонская компоновка** – видео автоматически подстраивают высоту под соотношение сторон, экономя до 40% экранного пространства
- **Изменение размера с 8 сторон** – изменяйте размер окна за любой угол или край
- **Пользовательская строка заголовка** – современные элементы управления с закруглёнными углами (Windows 11)

#### 🎥 Продвинутое воспроизведение
- **Поддержка множества форматов** – MP4, AVI, MOV, MKV, FLV, WMV, M4V
- **Несколько бэкендов** – Auto, FFMPEG, MSMF, DirectShow – переключайтесь в любой момент
- **Сохранение пропорций** – видео масштабируется правильно без искажений
- **Оптимизация производительности** – ограничение FPS, пропуск кадров при высокой нагрузке

#### 🌍 Локализация
- **Поддержка нескольких языков** – русский, английский, китайский (легко расширяется)
- **Мгновенное переключение языка** – без перезапуска

#### ⚙️ Настраиваемые параметры
- Выбор видеобэкенда
- Лимит количества видео
- Ограничитель FPS (1–120)
- Минимальный размер видео (80–300 px)
- Качество масштабирования: Низкое/Среднее/Высокое
- Тема: Тёмная / Светлая
- Прозрачность окна (50–100%)
- Задержка открытия видео – предотвращает конфликты FFMPEG

#### ⌨️ Горячие клавиши

| Клавиша   | Действие                   |
|-----------|----------------------------|
| `Space`   | Воспроизвести / Пауза      |
| `S`       | Стоп                       |
| `P`       | Пауза для всех             |
| `R`       | Возобновить все            |
| `F`       | Полноэкранный режим        |
| `H`       | Скрыть/Показать панель     |
| `F1`      | Открыть настройки          |

### 📦 Установка

#### Требования
- **Python 3.10 или выше**
- **Windows 10/11** (для закруглённых углов и функций DWM)

#### Пошаговая инструкция

    # Клонируйте репозиторий
    git clone https://github.com/zedraider/ZVideoGridPlayer.git
    cd ZVideoGridPlayer

    # Создайте виртуальное окружение (рекомендуется)
    python -m venv .venv
    .venv\Scripts\activate

    # Установите зависимости
    pip install -r requirements.txt

    # Запустите приложение
    python scr/ZVideoGridPlayer/ZVideoGridPlayer.py

#### `requirements.txt` (минимум)

    opencv-python>=4.8.0
    pillow>=10.0.0
    numpy>=1.24.0
    sv-ttk>=2.5.0   # опционально: современные виджеты

### 🗂️ Структура проекта

    ZVideoGridPlayer/
    ├── scr/
    │   ├── ZVideoGridPlayer/
    │   │   ├── ZVideoGridPlayer.py   # главный файл
    │   │   └── oldver/               # архивные версии
    │   └── lang/                     # языковые файлы
    │       ├── en.json
    │       ├── ru.json
    │       └── zh.json
    ├── .venv/                        # виртуальное окружение (опционально)
    ├── icon.ico                      # иконка приложения
    ├── icon.png
    ├── requirements.txt
    ├── settings.json                 # настройки пользователя (создаётся автоматически)
    └── README.md

### 🌐 Добавление нового языка

1. Создайте файл `lang/{code}.json` (например, `lang/fr.json`)
2. Скопируйте структуру из `lang/en.json` и переведите значения
3. Добавьте ключ `"lang_{code}": "NativeName"` для отображения в настройках
4. Перезапустите приложение – новый язык появится автоматически

**Пример `lang/fr.json`:**

    {
        "app_title": "ZVideoGridPlayer",
        "settings_title": "⚙️ PARAMÈTRES",
        "language": "Langue de l'interface:",
        "lang_fr": "Français",
        "select_folder": "📁 Sélectionner un dossier",
        "start": "▶ Démarrer"
    }

### 🛠️ Устранение неполадок

| Проблема | Решение |
|----------|---------|
| **Ошибка FFMPEG** (`assertion fctx->async_lock failed`) | Увеличьте **"Задержку открытия видео"** в настройках (по умолчанию 50 мс) |
| **Видео не загружаются** | Убедитесь, что пути содержат **только ASCII-символы**; попробуйте другой бэкенд (FFMPEG → MSMF → DirectShow) |
| **Проблемы с масштабированием интерфейса** | Отключите масштабирование DPI для `python.exe`: правый клик → Свойства → Совместимость → Изменить параметры высокого DPI |

### 🧑‍💻 Разработка

#### Стиль кода
- Следуйте рекомендациям **PEP 8**
- Используйте аннотации типов
- Старайтесь держать функции не длиннее 50 строк

#### Добавление функций
1. Форкните репозиторий
2. Создайте ветку для вашей функции: `git checkout -b feature/your-feature`
3. Зафиксируйте изменения: `git commit -m 'Add: your feature'`
4. Отправьте изменения и откройте Pull Request

### 🤝 Участие в разработке

Приветствуются любые вклады! Смело отправляйте Pull Request.

1. Форкните проект
2. Создайте ветку (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add: AmazingFeature'`)
4. Отправьте в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

### 📄 Лицензия

Распространяется под лицензией **MIT**. Подробности в файле `LICENSE`.

### 📬 Контакты

**zedraider** – [GitHub профиль](https://github.com/zedraider)  
Ссылка на проект: [https://github.com/zedraider/ZVideoGridPlayer](https://github.com/zedraider/ZVideoGridPlayer)

---

*Если этот инструмент оказался полезен, поставьте звезду ⭐ на GitHub!*