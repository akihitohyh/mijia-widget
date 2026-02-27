@echo off
chcp 65001 >nul
if exist "dist\米家桌面插件.exe" (
    start "" "dist\米家桌面插件.exe"
) else (
    start pythonw main_widget.py
)
