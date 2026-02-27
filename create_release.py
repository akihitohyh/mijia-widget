"""
创建发布包（7z格式）
"""
import os
import sys
import py7zr
from datetime import datetime

# 需要排除的文件/目录
EXCLUDE_PATTERNS = [
    '.git',
    '.claude',
    '__pycache__',
    'build',
    'dist',
    'venv',
    '.gitignore',
    '.spec',  # PyInstaller spec文件
    'create_release.py',  # 本脚本
    'mijia-widget.7z',  # 已有的压缩包
]

def should_exclude(path):
    """检查是否应该排除该路径"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path:
            return True
    return False

def create_release():
    """创建7z发布包"""
    version = "v1.0.1"
    output_name = f"mijia-widget-{version}.7z"

    print(f"正在创建发布包: {output_name}")
    print("-" * 50)

    # 获取项目根目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # 收集要压缩的文件
    files_to_add = []
    for root, dirs, files in os.walk('.'):
        # 过滤掉排除的目录
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]

        for file in files:
            file_path = os.path.join(root, file)
            # 移除开头的 .\
            if file_path.startswith('.\\'):
                file_path = file_path[2:]

            if not should_exclude(file_path):
                files_to_add.append(file_path)

    print(f"共 {len(files_to_add)} 个文件")
    print("\n主要文件:")
    for f in sorted(files_to_add)[:15]:
        print(f"  - {f}")
    if len(files_to_add) > 15:
        print(f"  ... 还有 {len(files_to_add) - 15} 个文件")

    # 创建7z文件
    with py7zr.SevenZipFile(output_name, 'w') as archive:
        for file_path in files_to_add:
            archive.write(file_path)

    print("\n" + "-" * 50)
    print(f"✅ 发布包创建成功: {output_name}")

    # 显示文件大小
    size = os.path.getsize(output_name)
    size_mb = size / (1024 * 1024)
    print(f"📦 文件大小: {size_mb:.2f} MB")
    print(f"\n发布说明:")
    print(f"  - 版本: {version}")
    print(f"  - 日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"  - 包含完整源码和脚本")
    print(f"  - 不包含编译后的EXE（需要自行打包）")

    return output_name

if __name__ == "__main__":
    try:
        create_release()
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
