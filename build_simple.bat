@echo off
echo ===============================================
echo    Building Squishy Light Controller EXE
echo ===============================================
echo.

echo Installing requirements...
pip install -r requirements.txt

echo.
echo Converting icon...
python -c "from PIL import Image; img = Image.open('toad.png'); img.save('toad.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])"

echo.
echo Building executable...
pyinstaller --clean --noconfirm squishy_light_controller.spec

echo.
echo ===============================================
echo Build complete! 
echo.
echo Your executable is located at:
echo   dist\SquishyLightController.exe
echo.
echo If Windows asks what to open it with:
echo   1. Right-click the .exe
echo   2. Select "Open with" then "Choose another app"
echo   3. Check "Always use this app to open .exe files"
echo   4. Select "Windows Explorer" or click OK
echo ===============================================
pause


