@echo off
pyinstaller --onefile --noconsole --icon ../Assets/IconSmall.ico --name LegacyPlay_Updater --distpath ./../ main.py
pause