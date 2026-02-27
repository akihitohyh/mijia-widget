"""
米家账号登录脚本
"""
from mijiaAPI import mijiaAPI
import os

print("=" * 50)
print("米家账号登录")
print("=" * 50)
print()

# 确保配置目录存在
auth_dir = os.path.expanduser("~/.config/mijia-api")
os.makedirs(auth_dir, exist_ok=True)

auth_file = os.path.join(auth_dir, "auth.json")

print(f"认证文件将保存到: {auth_file}")
print()

# 初始化API并登录
api = mijiaAPI(auth_file)
api.login()

print()
print("=" * 50)
print("登录成功！")
print("=" * 50)
print()
print("现在可以运行 start.bat 启动桌面插件了")
input("按回车键退出...")
