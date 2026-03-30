ZVideoGridPlayer 🎬
A powerful Python application for viewing multiple videos simultaneously in a customizable grid layout. Perfect for surveillance monitoring, video comparison, or managing large video collections.
✨ Features
🖥️ Display
Masonry-style grid layout – Videos automatically arrange with different heights based on aspect ratio, saving up to 40% screen space
Dynamic resizing – Resize window from any edge or corner (8 resize handles)
Custom title bar – Native-looking controls with minimize, maximize, and close
Rounded window corners (Windows 11)
🎥 Video Playback
Multi-format support – MP4, AVI, MOV, MKV, FLV, WMV, M4V
Multiple backends – Auto, FFMPEG, MSMF, DirectShow
Real-time aspect ratio preservation – Videos scale correctly without distortion
Configurable FPS limit – Reduce CPU usage by limiting frame rate
Frame skipping optimization – Automatically skip frames under high load
🌍 Localization
Multi-language support – English, Russian, Chinese (easily extensible)
Dynamic language loading – Add new languages by creating a JSON file in lang/
Instant language switching – Apply changes without restart
⚙️ Settings Panel
Video backend selection
Maximum video count limit
FPS limiter (1-120)
Minimum video size (80-300px)
Scaling quality: Low/Medium/High
Frame queue size
Optimization threshold
Theme: Dark/Light
Window opacity (50-100%)
Open delay between videos (prevents FFMPEG conflicts)
⌨️ Keyboard Shortcuts
Key
Action
Space
Toggle Play/Pause
S
Stop playback
P
Pause all
R
Resume all
F
Toggle fullscreen
H
Hide/Show control panel
F1
Open Settings
📦 Installation
Prerequisites
Python 3.10 or higher
Windows 10/11 (for rounded corners and DWM features)
Steps
# Clone the repository
git clone https://github.com/zedraider/ZVideoGridPlayer.git
cd ZVideoGridPlayer

# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python scr/ZVideoGridPlayer/ZVideoGridPlayer.py

Requirements (requirements.txt)
opencv-python>=4.8.0
pillow>=10.0.0
numpy>=1.24.0
sv-ttk>=2.5.0  # Optional: for modern themed widgets

🗂️ Project Structure
ZVideoGridPlayer/
├── scr/
│   ├── ZVideoGridPlayer/
│   │   ├── ZVideoGridPlayer.py    # Main application
│   │   └── oldver/                 # Previous versions (archive)
│   └── lang/                       # Language files
│       ├── en.json                 # English
│       ├── ru.json                 # Russian
│       └── zh.json                 # Chinese
├── .venv/                          # Virtual environment
├── icon.ico                        # Application icon
├── icon.png                        # Alternative icon
├── requirements.txt                # Python dependencies
├── settings.json                   # User settings (auto-generated)
└── README.md                       # This file

🌐 Adding a New Language
Create a new file lang/{code}.json (e.g., lang/fr.json)
Copy structure from lang/en.json and translate values
Add "lang_{code}": "NativeName" key for display in settings
Restart the app – language appears automatically!
Example lang/fr.json:
{
    "app_title": "ZVideoGridPlayer",
    "settings_title": "⚙️ PARAMÈTRES",
    "language": "Langue de l'interface:",
    "lang_fr": "Français",
    "select_folder": "📁 Sélectionner un dossier",
    "start": "▶ Démarrer",
    "...": "..."
}

⚠️ Troubleshooting
FFMPEG Assertion Error
Assertion fctx->async_lock failed at libavcodec/pthread_frame.c:173
Solution: Increase "Delay between video opens" in Settings (default: 50ms)
Videos Not Loading
Check file paths contain only ASCII characters
Ensure videos are not corrupted
Try different backend in Settings (FFMPEG → MSMF → DirectShow)
UI Scaling Issues
Disable DPI scaling for python.exe: Right-click → Properties → Compatibility → Change high DPI settings
🛠️ Development
Code Style
Follow PEP 8 guidelines
Use type hints where possible
Keep functions under 50 lines when feasible
Adding Features
Fork the repository
Create a feature branch: git checkout -b feature/your-feature
Commit changes: git commit -m 'Add: your feature'
Push and open a Pull Request
📄 License
This project is licensed under the MIT License – see the LICENSE file for details.
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
Fork the Project
Create your Feature Branch (git checkout -b feature/AmazingFeature)
Commit your Changes (git commit -m 'Add: AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request
📬 Contact
zedraider – GitHub
Project Link: https://github.com/zedraider/ZVideoGridPlayer