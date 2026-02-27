@echo off
chcp 65001 >nul
echo 正在安装依赖...
pip install pyinstaller qrcode pillow -q

echo 正在打包米家桌面插件...
pyinstaller --name "米家桌面插件" --onefile --windowed --clean --runtime-hook hook_stdio.py main_widget.py

echo.
echo 打包完成！
echo 输出文件: dist\米家桌面插件.exe
echo.
pause
