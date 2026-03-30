# 🎬 ZVideoGridPlayer

**Multi‑video grid player for Windows**  
Watch multiple videos side‑by‑side with a dynamic masonry layout.  
Perfect for surveillance, video comparison, and monitoring.

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)

---

## ✨ Features

### 🖥️ Smart Grid Layout
- **Masonry‑style arrangement** – videos automatically adjust their height based on aspect ratio, saving up to 40% of screen space.
- **8‑edge window resizing** – resize from any corner or edge with native handles.
- **Custom title bar** – modern window controls (minimize, maximize, close) with rounded corners (Windows 11).

### 🎥 Advanced Video Playback
- **Wide format support** – MP4, AVI, MOV, MKV, FLV, WMV, M4V.
- **Multiple backends** – Auto, FFMPEG, MSMF, DirectShow – switch anytime.
- **Real‑time aspect ratio** – videos scale correctly without distortion.
- **Performance optimisations** – configurable FPS limit, frame skipping under load.

### 🌍 Localisation
- **Multi‑language support** – English, Russian, Chinese (easily extensible).
- **Instant language switching** – no restart required.

### ⚙️ Customisable Settings
- Video backend selection
- Maximum number of videos
- FPS limiter (1–120)
- Minimum video size (80–300 px)
- Scaling quality (Low/Medium/High)
- Theme: Dark / Light
- Window opacity (50–100%)
- Delay between video opens – prevents FFMPEG conflicts

### ⌨️ Keyboard Shortcuts
| Key         | Action                 |
|-------------|------------------------|
| `Space`     | Play / Pause           |
| `S`         | Stop                   |
| `P`         | Pause all              |
| `R`         | Resume all             |
| `F`         | Toggle fullscreen      |
| `H`         | Hide/show control panel|
| `F1`        | Open settings          |

---

## 📦 Installation

### Prerequisites
- **Python 3.10 or higher**
- **Windows 10/11** (for rounded corners and DWM features)

### Step‑by‑Step

```bash
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


requirements.txt (minimum)
text
opencv-python>=4.8.0
pillow>=10.0.0
numpy>=1.24.0
sv-ttk>=2.5.0   # optional: modern themed widgets


🗂️ Project Structure
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
├── settings.json                 # auto‑generated user settings
└── README.md

🌐 Adding a New Language
Create a new file lang/{code}.json (e.g. lang/fr.json).
Copy the structure from lang/en.json and translate the values.
Add a "lang_{code}": "NativeName" entry for the display name in the settings.
Restart the application – the new language will appear automatically.
Example lang/fr.json:
{
    "app_title": "ZVideoGridPlayer",
    "settings_title": "⚙️ PARAMÈTRES",
    "language": "Langue de l'interface:",
    "lang_fr": "Français",
    "select_folder": "📁 Sélectionner un dossier",
    "start": "▶ Démarrer"
}

🛠️ Troubleshooting
Issue	Solution
FFMPEG assertion error (assertion fctx->async_lock failed)	Increase “Delay between video opens” in settings (default 50 ms).
Videos not loading	Ensure file paths contain only ASCII characters; try a different backend (FFMPEG → MSMF → DirectShow).
UI scaling issues	Disable DPI scaling for python.exe: right‑click → Properties → Compatibility → Change high DPI settings.

🧑‍💻 Development
Code Style
Follow PEP 8 guidelines.
Use type hints where possible.
Keep functions under 50 lines when feasible.
Adding Features
Fork the repository.
Create a feature branch: git checkout -b feature/your-feature
Commit changes: git commit -m 'Add: your feature'
Push and open a Pull Request.

🤝 Contributing
Contributions are welcome! Feel free to submit a Pull Request.
Fork the Project
Create your Feature Branch (git checkout -b feature/AmazingFeature)
Commit your Changes (git commit -m 'Add: AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request

📄 License
Distributed under the MIT License. See LICENSE for more information.

📬 Contact
zedraider – GitHub Profile
Project Link: https://github.com/zedraider/ZVideoGridPlayer

If you find this project useful, consider giving it a ⭐ on GitHub!