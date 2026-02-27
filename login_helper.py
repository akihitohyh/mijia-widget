"""
登录辅助程序 - 用于在控制台显示二维码
"""
import sys
import os

def main():
    """执行扫码登录"""
    try:
        from mijiaAPI import mijiaAPI

        auth_file = os.path.expanduser("~/.config/mijia-api/auth.json")
        api = mijiaAPI(auth_file)

        print("=" * 50)
        print("米家账号扫码登录")
        print("=" * 50)
        print()

        # 尝试获取二维码
        try:
            qr_url = api.QRlogin()
            if qr_url:
                print(f"请扫描二维码登录: {qr_url}")
                print()
                # 尝试生成二维码图像
                try:
                    import qrcode
                    qr = qrcode.QRCode(box_size=1, border=1)
                    qr.add_data(qr_url)
                    qr.make()
                    qr.print_ascii(invert=True)
                    print()
                except:
                    pass
        except Exception as e:
            print(f"无法显示二维码: {e}")

        print("请使用米家APP扫描二维码...")
        print()

        # 轮询登录状态
        import time
        for i in range(60):
            time.sleep(1)
            try:
                if api.login():
                    print("登录成功！")
                    return 0
            except:
                pass
            if i % 10 == 0:
                print(f"等待登录... ({i}s)")

        print("登录超时")
        return 1

    except Exception as e:
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
