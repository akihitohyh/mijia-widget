@echo off
echo ======================================
echo    米家账号登录
echo ======================================
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo 正在启动登录程序...
echo 请按提示扫描二维码
echo.

python login.py

if exist "venv\Scripts\deactivate.bat" (
    deactivate
)
