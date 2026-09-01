# 🐸 Building Squishy Light Controller Executable

This guide will help you create a standalone `.exe` file for the Squishy Light Controller with your custom toad icon!

## 📋 Prerequisites

- Python 3.7+ installed on your system
- All project files in the same folder:
  - `squishy_light_controller.py`
  - `toad.png` (your custom icon)
  - `requirements.txt`
  - Build files (created automatically)

## 🚀 Quick Build (Recommended)

### Option 1: Python Script (Cross-platform)
```bash
python build_exe.py
```

### Option 2: Batch File (Windows only)
```bash
build_exe.bat
```

## 🔧 Manual Build Process

If the automatic scripts don't work, you can build manually:

1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Convert icon (optional):**
   ```bash
   python -c "from PIL import Image; img = Image.open('toad.png'); img.save('toad.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])"
   ```

3. **Build executable:**
   ```bash
   pyinstaller --clean squishy_light_controller.spec
   ```

## 📁 Output

After building, you'll find:
- **`dist/SquishyLightController.exe`** - Your standalone executable! 🎉
- **`build/`** - Temporary build files (can be deleted)
- **`toad.ico`** - Converted icon file

## 🎯 Features of the EXE

✅ **Standalone** - No Python installation required  
✅ **Custom Icon** - Your toad.png as the application icon  
✅ **All Features** - Complete functionality including:
- Basic LED controls (Red/Green/Off)
- Custom RGB color picker with live preview
- Pomodoro timer with focus/break sessions
- 14+ stunning lighting effects optimized for silicone diffusion
- Real-time effect parameter control
- Serial communication with Arduino

## 📦 Distribution

The `SquishyLightController.exe` file can be:
- Copied to any Windows computer and run directly
- Shared with others who don't have Python
- Run from a USB drive
- Added to Windows startup folder for auto-launch

## 🐛 Troubleshooting

**Build fails?**
- Make sure Python and pip are properly installed
- Try running as administrator
- Check that all required files are present

**Icon doesn't show?**
- The build will continue without the icon if conversion fails
- Make sure `toad.png` exists and is a valid image file

**EXE won't run?**
- Try running from command prompt to see error messages
- Make sure Windows Defender isn't blocking the file
- Some antivirus software may flag PyInstaller executables (false positive)

## 🎨 Customizing the Icon

Want to change the icon? Simply replace `toad.png` with your desired image and rebuild!

## 🌟 File Size

The final executable will be approximately 80-120 MB, which includes:
- Python runtime
- PySide6 GUI framework  
- All application code and resources

This is normal for PyInstaller executables and allows the app to run on any Windows system without dependencies.

---

**Happy building! Your squishy light controller will soon be a professional standalone application! 🌈✨**


