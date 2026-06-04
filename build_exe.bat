@echo off
title Build AutoClicker Pro EXE
echo Installing requirements...
pip install -r requirements.txt
echo Building EXE...
pyinstaller --onefile --windowed --name AutoClickerPro main.py
echo Done!
echo EXE file is here: dist\AutoClickerPro.exe
pause
