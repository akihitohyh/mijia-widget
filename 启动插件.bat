@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 检查认证文件是否存在
if not exist "%USERPROFILE%\.config\mijia-api\auth.json" (
    echo ============================================
    echo  首次使用 - 需要先登录米家账号
    echo ============================================
    echo.
    echo 请选择登录方式：
    echo 1. 扫码登录（推荐）
    echo 2. 命令行登录
    echo.
    choice /c 12 /n /m "请选择 (1/2): "

    if errorlevel 2 (
        echo.
        echo 正在打开命令行登录...
        echo 请按提示扫描二维码
        echo.
        mijiaAPI --login
    ) else (
        echo.
        echo 正在启动图形化登录...
        echo.
        python login_helper.py
    )

    echo.
    echo ============================================
    echo  登录完成！正在启动米家桌面插件...
    echo ============================================
    timeout /t 2 >nul
)

:: 启动插件
echo 正在启动米家桌面插件...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main_widget.py
) else (
    python main_widget.py
)

if errorlevel 1 pause
