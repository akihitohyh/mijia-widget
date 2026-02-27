"""
打包米家桌面插件为 EXE
"""
import subprocess
import sys
import os

def build():
    """使用 PyInstaller 打包"""

    # 安装 pyinstaller
    print("正在安装 PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller", "-q"], check=True)

    # 打包命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "米家桌面插件",
        "--onefile",           # 打包成单个文件
        "--windowed",          # 不显示控制台窗口
        "--icon", "NONE",      # 可以添加图标
        "--clean",
        "--add-data", f"{os.path.expanduser('~/.config/mijia-api/auth.json')};.",  # 包含认证文件
        "main_widget.py"
    ]

    print("开始打包...")
    subprocess.run(cmd, check=True)
    print("\n打包完成！")
    print(f"输出目录: {os.path.abspath('dist')}")
    print("运行 dist/米家桌面插件.exe 启动程序")

if __name__ == "__main__":
    build()
