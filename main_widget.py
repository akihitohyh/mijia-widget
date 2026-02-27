"""
米家桌面小插件 - PyQt6实现
"""
import sys
import asyncio
import threading
from datetime import datetime
from typing import List, Dict

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QDialog, QGridLayout, QSizeGrip, QColorDialog,
    QFormLayout, QGroupBox, QCheckBox, QMessageBox,
    QSystemTrayIcon, QMenu, QComboBox, QSlider
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QMetaObject, Q_ARG
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

from mijia_client import MijiaClient
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, REFRESH_INTERVAL, STYLE,
    WINDOW_TOPMOST, save_config, PLUG_OPTIONS, DEFAULT_PLUG_OPTIONS,
    get_device_display_name
)

VERSION = "v1.0.1"


class SettingsDialog(QDialog):
    """设置面板对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(350, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE['bg_color']};
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QGroupBox {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
                border: 1px solid {STYLE['card_bg']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("⚙️ 插件设置")
        title.setFont(QFont(STYLE['font_family'], 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {STYLE['accent_color']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 颜色设置
        color_group = QGroupBox("颜色设置")
        color_layout = QFormLayout()

        self.bg_color_btn = QPushButton("选择背景色")
        self.bg_color_btn.clicked.connect(lambda: self.pick_color('bg_color'))
        color_layout.addRow("背景色:", self.bg_color_btn)

        self.text_color_btn = QPushButton("选择文字色")
        self.text_color_btn.clicked.connect(lambda: self.pick_color('text_color'))
        color_layout.addRow("文字色:", self.text_color_btn)

        self.accent_color_btn = QPushButton("选择强调色")
        self.accent_color_btn.clicked.connect(lambda: self.pick_color('accent_color'))
        color_layout.addRow("强调色:", self.accent_color_btn)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 账号管理
        account_group = QGroupBox("账号管理")
        account_layout = QVBoxLayout()

        self.login_btn = QPushButton("📱 扫码登录")
        self.login_btn.clicked.connect(self.qr_login)
        account_layout.addWidget(self.login_btn)

        self.logout_btn = QPushButton("🚪 退出登录")
        self.logout_btn.clicked.connect(self.logout)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        account_layout.addWidget(self.logout_btn)

        account_group.setLayout(account_layout)
        layout.addWidget(account_group)

        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    def pick_color(self, color_key):
        current_color = QColor(STYLE[color_key])
        color = QColorDialog.getColor(current_color, self, f"选择{self.get_color_name(color_key)}")
        if color.isValid():
            STYLE[color_key] = color.name()
            self.update_color_preview()

    def get_color_name(self, key):
        names = {'bg_color': '背景色', 'text_color': '文字色', 'accent_color': '强调色'}
        return names.get(key, key)

    def update_color_preview(self):
        # 只更新样式表，不重新创建布局
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE['bg_color']};
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QGroupBox {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
                border: 1px solid {STYLE['card_bg']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)
        # 通知父窗口更新样式
        if self.parent():
            self.parent().update_stylesheet()

    def qr_login(self):
        """扫码登录 - 显示图形化二维码"""
        dialog = QRLoginDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "登录成功", "登录成功！请刷新设备列表。")
            # 通知父窗口刷新设备
            if self.parent():
                self.parent().refresh_devices()

    def logout(self):
        """退出登录 - 删除认证文件"""
        from config import AUTH_FILE
        import os

        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出登录吗？\n这将清除所有设备信息。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除认证文件
                auth_path = os.path.expanduser("~/.config/mijia-api/auth.json")
                if os.path.exists(auth_path):
                    os.remove(auth_path)
                    QMessageBox.information(self, "退出成功", "已退出登录，重启程序后需要重新登录。")
                else:
                    QMessageBox.warning(self, "提示", "未找到登录信息。")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"退出登录失败: {e}")

    def save_settings(self):
        save_config(style=STYLE)
        self.accept()


class QRLoginDialog(QDialog):
    """扫码登录对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("扫码登录")
        self.setFixedSize(300, 350)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)

        self.setup_ui()
        self.start_login()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE['bg_color']};
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("📱 扫码登录")
        title.setFont(QFont(STYLE['font_family'], 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {STYLE['accent_color']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 二维码显示区域
        self.qr_label = QLabel("正在获取二维码...")
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border: 2px solid {STYLE['card_bg']};
                border-radius: 10px;
            }}
        """)
        layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # 状态提示
        self.status_label = QLabel("请使用米家APP扫描二维码")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {STYLE['accent_color']}; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addStretch()

    def start_login(self):
        """开始登录流程"""
        import threading
        self.login_thread = threading.Thread(target=self._do_login, daemon=True)
        self.login_thread.start()

    def _do_login(self):
        """执行登录（在后台线程）"""
        try:
            from mijiaAPI import mijiaAPI

            # 创建临时 API 实例用于登录
            auth_file = os.path.expanduser("~/.config/mijia-api/auth.json")
            api = mijiaAPI(auth_file)

            # 尝试使用 QRlogin 获取二维码
            try:
                # 获取登录二维码
                login_url = api.QRlogin()
            except Exception as e:
                # 如果 QRlogin 不存在，使用 login 方法
                print(f"QRlogin failed: {e}")
                login_url = None

            if login_url:
                # 生成二维码图片
                self._show_qr_code(login_url)
                self.status_label.setText("请使用米家APP扫描二维码")

                # 轮询检查登录状态
                import time
                for _ in range(60):  # 最多等待60秒
                    time.sleep(1)
                    # 检查是否已登录
                    try:
                        if api.login():
                            self.status_label.setText("登录成功！")
                            self.accept()
                            return
                    except:
                        pass

                self.status_label.setText("登录超时，请重试")
            else:
                # 没有二维码URL，使用备用方案
                self._show_manual_login(auth_file)
        except Exception as e:
            self.status_label.setText(f"登录出错: {str(e)[:50]}")

    def _show_manual_login(self, auth_file):
        """显示手动登录说明"""
        from PyQt6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(
            self.qr_label,
            "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, "请手动运行命令登录:\nmijiaAPI --login")
        )
        QMetaObject.invokeMethod(
            self.status_label,
            "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, "请在命令行运行: mijiaAPI --login")
        )

    def _show_qr_code(self, url: str):
        """显示二维码"""
        try:
            import qrcode
            from PyQt6.QtGui import QPixmap
            from PyQt6.QtCore import Qt

            # 生成二维码
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(url)
            qr.make(fit=True)

            # 创建图像
            img = qr.make_image(fill_color="black", back_color="white")

            # 转换为 QPixmap
            from PIL.ImageQt import ImageQt
            qt_img = ImageQt(img)
            pixmap = QPixmap.fromImage(qt_img)

            # 缩放以适应标签
            scaled_pixmap = pixmap.scaled(
                180, 180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # 在主线程更新UI
            from PyQt6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                self.qr_label,
                "setPixmap",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(QPixmap, scaled_pixmap)
            )
        except ImportError:
            # 如果没有 qrcode 库，显示URL文本
            self.qr_label.setText(f"请访问:\n{url[:50]}...")
        except Exception as e:
            self.qr_label.setText(f"二维码生成失败:\n{str(e)[:50]}")


class PlugDetailDialog(QDialog):
    """智能插座详情弹窗"""

    def __init__(self, device: Dict, client: MijiaClient, parent=None):
        super().__init__(parent)
        self.device = device
        self.client = client
        display_name = get_device_display_name(device.get('name', '插座'))
        self.setWindowTitle(f"{display_name} - 实时用电")
        self.setFixedSize(300, 280)

        # 设置为模态对话框，确保显示在最前
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)

        self.setup_ui()
        self.load_data()

        # 移动到父窗口中央
        if parent:
            parent_geo = parent.geometry()
            self_geo = self.geometry()
            x = parent_geo.x() + (parent_geo.width() - self_geo.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self_geo.height()) // 2
            self.move(x, y)

    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE['bg_color']};
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        display_name = get_device_display_name(self.device.get('name', '智能插座'))
        title = QLabel(f"⚡ {display_name}")
        title.setFont(QFont(STYLE['font_family'], 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {STYLE['accent_color']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 用电信息网格
        grid = QGridLayout()
        grid.setSpacing(15)

        # 当前功率（大字显示）
        self.power_label = QLabel("--")
        self.power_label.setFont(QFont(STYLE['font_family'], 36, QFont.Weight.Bold))
        self.power_label.setStyleSheet(f"color: {STYLE['online_color']}; text-align: center;")
        self.power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.power_label, 0, 0, 1, 2)

        self.power_unit_label = QLabel("W")
        self.power_unit_label.setFont(QFont(STYLE['font_family'], 14))
        self.power_unit_label.setStyleSheet(f"color: {STYLE['text_color']};")
        self.power_unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.power_unit_label, 1, 0, 1, 2)

        # 今日用电
        self.today_energy_label = QLabel("今日用电: -- 度")
        self.today_energy_label.setFont(QFont(STYLE['font_family'], 12))
        self.today_energy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.today_energy_label, 2, 0, 1, 2)

        # 开关状态
        self.status_label = QLabel("状态: --")
        self.status_label.setFont(QFont(STYLE['font_family'], 11))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(self.status_label, 3, 0, 1, 2)

        layout.addLayout(grid)

        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)

        layout.addStretch()

    def load_data(self):
        """加载用电数据"""
        did = self.device.get('did')
        info = self.client.get_plug_power_info(did)

        if info:
            power = info.get('power_w', 0)
            energy = info.get('energy_kwh', 0)
            is_on = info.get('is_on', False)

            # 显示当前功率（大字）
            if power is not None:
                self.power_label.setText(f"{power}")
            else:
                self.power_label.setText("--")

            # 显示今日用电量（优先使用 today_energy_kwh，否则显示累计）
            today_energy = info.get('today_energy_kwh', energy)
            self.today_energy_label.setText(f"今日用电: {today_energy} 度")

            # 显示开关状态
            status_text = "开启" if is_on else "关闭"
            self.status_label.setText(f"状态: {status_text}")
        else:
            self.power_label.setText("--")
            self.today_energy_label.setText("今日用电: 获取失败")
            self.status_label.setText("状态: 未知")


class PlugOptionsDialog(QDialog):
    """插座显示选项对话框"""

    def __init__(self, device: Dict, current_options: Dict, parent=None):
        super().__init__(parent)
        self.device = device
        self.current_options = current_options.copy()
        self.setWindowTitle(f"{device.get('name', '插座')} - 显示选项")
        self.setFixedSize(350, 280)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE['bg_color']};
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QCheckBox {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid {STYLE['accent_color']};
                background-color: {STYLE['card_bg']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {STYLE['accent_color']};
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-family: "{STYLE['font_family']}";
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        display_name = get_device_display_name(self.device.get('name', '插座'))
        title = QLabel(f"⚙️ {display_name} 显示设置")
        title.setFont(QFont(STYLE['font_family'], 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {STYLE['accent_color']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 选项
        self.checkboxes = {}

        options = [
            ('show_power', '显示当前功率 (W)'),
            ('show_today_energy', '显示今日用电 (度)'),
            ('show_total_energy', '显示累计用电 (度)'),
            ('show_status', '显示开关状态'),
        ]

        for key, label in options:
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.current_options.get(key, True))
            self.checkboxes[key] = checkbox
            layout.addWidget(checkbox)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {STYLE['card_bg']};
                color: {STYLE['text_color']};
                border: 1px solid {STYLE['accent_color']};
                border-radius: 5px;
                padding: 8px 20px;
            }}
            QPushButton:hover {{
                background-color: {STYLE['accent_color']};
                color: white;
            }}
        """)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_options)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def save_options(self):
        """保存选项"""
        for key, checkbox in self.checkboxes.items():
            self.current_options[key] = checkbox.isChecked()
        self.accept()

    def get_options(self) -> Dict:
        """获取选项"""
        return self.current_options


class DeviceCard(QFrame):
    """设备卡片组件"""

    def __init__(self, device: Dict, client: MijiaClient = None, on_detail=None, on_options=None, parent=None):
        super().__init__(parent)
        self.device = device
        self.client = client
        self.on_detail = on_detail
        self.on_options = on_options
        self.options = DEFAULT_PLUG_OPTIONS.copy()
        self.power_labels = {}  # 存储用电信息标签
        self.setup_ui()

    def is_plug_device(self) -> bool:
        """判断是否为插座设备"""
        model = self.device.get('model', '').lower()
        name = self.device.get('name', '').lower()
        return 'plug' in model or '插座' in name or 'plug' in name

    def is_ac_device(self) -> bool:
        """判断是否为空调设备"""
        model = self.device.get('model', '').lower()
        name = self.device.get('name', '').lower()
        return 'air' in model or 'ac' in model or '空调' in name

    def setup_ui(self):
        self.setObjectName("deviceCard")
        self.setStyleSheet(f"""
            #deviceCard {{
                background-color: {STYLE['card_bg']};
                border-radius: {STYLE['border_radius']};
                padding: 10px;
                margin: 5px;
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton#detailBtn {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
            }}
            QPushButton#detailBtn:hover {{
                background-color: #0095cc;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)

        # 设备名称和状态
        header = QHBoxLayout()

        # 使用中文名称显示
        display_name = get_device_display_name(self.device.get('name', '未知设备'))
        name_label = QLabel(display_name)
        name_label.setFont(QFont(STYLE['font_family'], 12, QFont.Weight.Bold))
        header.addWidget(name_label)

        header.addStretch()

        # 在线状态
        is_online = self.device.get('is_online', False)
        status_text = "在线" if is_online else "离线"
        status_color = STYLE['online_color'] if is_online else STYLE['offline_color']

        status_label = QLabel(f"● {status_text}")
        status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
        header.addWidget(status_label)

        # 如果是空调，显示开关状态
        if self.is_ac_device() and is_online:
            self.ac_power_label = QLabel("")
            self.ac_power_label.setStyleSheet("font-size: 11px;")
            header.addWidget(self.ac_power_label)
            # 立即获取开关状态
            self.update_ac_power_status()

        # 如果是插座，添加选项按钮
        if self.is_plug_device() and is_online:
            options_btn = QPushButton("选项")
            options_btn.setObjectName("detailBtn")
            options_btn.setFixedSize(35, 20)
            options_btn.clicked.connect(self.show_options)
            header.addWidget(options_btn)

        # 如果是空调，添加开关按钮
        if self.is_ac_device() and is_online:
            self.ac_switch_btn = QPushButton("开关")
            self.ac_switch_btn.setObjectName("detailBtn")
            self.ac_switch_btn.setFixedSize(35, 20)
            self.ac_switch_btn.clicked.connect(self.toggle_ac_power)
            header.addWidget(self.ac_switch_btn)

        layout.addLayout(header)

        # 用电信息区域（仅插座显示）
        if self.is_plug_device():
            self.power_info_widget = QWidget()
            self.power_info_widget.setStyleSheet(f"background-color: {STYLE['card_bg']};")
            power_layout = QHBoxLayout(self.power_info_widget)
            power_layout.setSpacing(10)
            power_layout.setContentsMargins(0, 5, 0, 0)

            # 当前功率
            self.power_labels['power'] = QLabel("")
            self.power_labels['power'].setStyleSheet(f"color: {STYLE['accent_color']}; font-size: 11px;")
            power_layout.addWidget(self.power_labels['power'])

            # 今日用电
            self.power_labels['today'] = QLabel("")
            self.power_labels['today'].setStyleSheet("color: #888888; font-size: 11px;")
            power_layout.addWidget(self.power_labels['today'])

            # 累计用电
            self.power_labels['total'] = QLabel("")
            self.power_labels['total'].setStyleSheet("color: #666666; font-size: 10px;")
            power_layout.addWidget(self.power_labels['total'])

            # 开关状态
            self.power_labels['status'] = QLabel("")
            self.power_labels['status'].setStyleSheet("color: #888888; font-size: 11px;")
            power_layout.addWidget(self.power_labels['status'])

            power_layout.addStretch()
            layout.addWidget(self.power_info_widget)

            # 初始隐藏所有标签
            self.update_power_display()

        # 设备型号
        model = self.device.get('model', '')
        if model:
            model_label = QLabel(f"型号: {model}")
            model_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(model_label)

        # 房间信息
        room_name = self.device.get('room_name', '')
        if room_name:
            room_label = QLabel(f"房间: {room_name}")
            room_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(room_label)

    def update_power_display(self):
        """根据选项更新显示哪些用电信息"""
        if not self.is_plug_device():
            return
        # 检查控件是否还存在（防止设备刷新后旧控件被删除）
        if not self.power_labels:
            return
        try:
            if 'power' in self.power_labels:
                self.power_labels['power'].setVisible(self.options.get('show_power', True))
            if 'today' in self.power_labels:
                self.power_labels['today'].setVisible(self.options.get('show_today_energy', True))
            if 'total' in self.power_labels:
                self.power_labels['total'].setVisible(self.options.get('show_total_energy', False))
            if 'status' in self.power_labels:
                self.power_labels['status'].setVisible(self.options.get('show_status', True))
        except RuntimeError:
            # 控件已被删除，忽略
            pass

    def update_power_info(self, info: Dict):
        """更新用电信息"""
        if not self.is_plug_device() or not info or not self.power_labels:
            return

        try:
            # 当前功率
            power = info.get('power_w')
            if power is not None and self.options.get('show_power', True) and 'power' in self.power_labels:
                self.power_labels['power'].setText(f"⚡ {power}W")
            elif 'power' in self.power_labels:
                self.power_labels['power'].setText("")

            # 今日用电
            today = info.get('today_energy_kwh')
            if today and self.options.get('show_today_energy', True) and 'today' in self.power_labels:
                self.power_labels['today'].setText(f"今日 {today}度")
            elif 'today' in self.power_labels:
                self.power_labels['today'].setText("")

            # 累计用电
            total = info.get('energy_kwh')
            if total and self.options.get('show_total_energy', False) and 'total' in self.power_labels:
                self.power_labels['total'].setText(f"累计 {total}度")
            elif 'total' in self.power_labels:
                self.power_labels['total'].setText("")

            # 开关状态
            is_on = info.get('is_on')
            if is_on is not None and self.options.get('show_status', True) and 'status' in self.power_labels:
                status = "开启" if is_on else "关闭"
                color = STYLE['online_color'] if is_on else STYLE['offline_color']
                self.power_labels['status'].setText(f"● {status}")
                self.power_labels['status'].setStyleSheet(f"color: {color}; font-size: 11px;")
            elif 'status' in self.power_labels:
                self.power_labels['status'].setText("")
        except RuntimeError:
            # 控件已被删除，忽略
            pass

    def set_options(self, options: Dict):
        """设置显示选项"""
        self.options.update(options)
        try:
            self.update_power_display()
        except RuntimeError:
            # 控件已被删除，忽略
            pass

    def show_options(self):
        """显示选项对话框"""
        if self.on_options:
            self.on_options(self.device, self.options, self.set_options)

    def update_ac_power_status(self):
        """更新空调开关状态显示"""
        if not self.client:
            return
        try:
            did = self.device.get('did')
            status = self.client.get_ac_status(did)
            if status and 'power' in status:
                power = status['power']
                if power:
                    self.ac_power_label.setText("● 开启")
                    self.ac_power_label.setStyleSheet("color: #4caf50; font-size: 11px;")  # 绿色
                else:
                    self.ac_power_label.setText("● 关闭")
                    self.ac_power_label.setStyleSheet("color: #888888; font-size: 11px;")  # 灰色
            else:
                self.ac_power_label.setText("")
        except Exception as e:
            print(f"获取空调状态失败: {e}")
            self.ac_power_label.setText("")

    def toggle_ac_power(self):
        """切换空调电源"""
        if not self.client:
            return
        try:
            did = self.device.get('did')
            # 先获取当前状态
            status = self.client.get_ac_status(did)
            current_power = status.get('power', False) if status else False

            # 切换状态
            new_power = not current_power
            result = self.client.set_ac_property(did, 'power', new_power)

            if result:
                # 更新显示
                if new_power:
                    self.ac_power_label.setText("● 开启")
                    self.ac_power_label.setStyleSheet("color: #4caf50; font-size: 11px;")
                else:
                    self.ac_power_label.setText("● 关闭")
                    self.ac_power_label.setStyleSheet("color: #888888; font-size: 11px;")
                print(f"空调 {'开启' if new_power else '关闭'} 成功")
            else:
                print(f"空调 {'开启' if new_power else '关闭'} 失败")
        except Exception as e:
            print(f"切换空调电源失败: {e}")


class ACControlDialog(QDialog):
    """空调控制对话框 - 简化版，只保留开关和状态显示"""

    def __init__(self, device: Dict, client: MijiaClient, parent=None):
        super().__init__(parent)
        self.device = device
        self.client = client
        self.did = device.get('did', '')

        # 使用设备全名
        display_name = get_device_display_name(device.get('name', '空调'))
        self.setWindowTitle(f"{display_name} - 控制面板")
        self.setFixedSize(300, 280)

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )
        self.setModal(True)

        self.setup_ui()
        self.load_status()

    def setup_ui(self):
        """设置UI"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE['bg_color']};
            }}
            QLabel {{
                color: {STYLE['text_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-family: "{STYLE['font_family']}";
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
            QPushButton#powerBtn {{
                background-color: #4caf50;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
            }}
            QPushButton#powerBtn:hover {{
                background-color: #45a049;
            }}
            QPushButton#powerBtn[off="true"] {{
                background-color: #f44336;
            }}
            QPushButton#powerBtn[off="true"]:hover {{
                background-color: #da190b;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题 - 使用全名
        name = self.device.get('name', '空调')
        title = QLabel(f"❄️ {get_device_display_name(name)}")
        title.setFont(QFont(STYLE['font_family'], 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {STYLE['accent_color']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        # 状态显示区域
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {STYLE['card_bg']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(8)

        # 当前温度
        self.room_temp_label = QLabel("🌡️ 室内温度: --°C")
        self.room_temp_label.setFont(QFont(STYLE['font_family'], 12))
        status_layout.addWidget(self.room_temp_label)

        # 目标温度
        self.target_temp_label = QLabel("🎯 目标温度: --°C")
        self.target_temp_label.setFont(QFont(STYLE['font_family'], 12))
        status_layout.addWidget(self.target_temp_label)

        # 当前功率
        self.power_label = QLabel("⚡ 当前功率: --W")
        self.power_label.setFont(QFont(STYLE['font_family'], 12))
        status_layout.addWidget(self.power_label)

        # 今日用电
        self.energy_label = QLabel("🔋 今日用电: --度")
        self.energy_label.setFont(QFont(STYLE['font_family'], 12))
        status_layout.addWidget(self.energy_label)

        layout.addWidget(status_frame)

        # 电源按钮
        self.power_btn = QPushButton("🔌 电源 (开)")
        self.power_btn.setObjectName("powerBtn")
        self.power_btn.clicked.connect(self.toggle_power)
        layout.addWidget(self.power_btn)

        # 状态提示
        self.status_label = QLabel("正在获取状态...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(f"color: {STYLE['accent_color']}; font-size: 11px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_status(self):
        """加载空调当前状态"""
        try:
            # 获取电源状态
            status = self.client.get_ac_status(self.did)
            if status:
                power = status.get('power', False)
                if power:
                    self.power_btn.setProperty("off", "false")
                    self.power_btn.setText("🔌 电源 (开)")
                else:
                    self.power_btn.setProperty("off", "true")
                    self.power_btn.setText("🔌 电源 (关)")

                # 显示目标温度
                target_temp = status.get('temperature', '--')
                self.target_temp_label.setText(f"🎯 目标温度: {target_temp}°C")

            # 获取用电信息
            power_info = self.client.get_ac_power_info(self.did)
            if power_info:
                # 室内温度
                room_temp = power_info.get('room_temp', '--')
                self.room_temp_label.setText(f"🌡️ 室内温度: {room_temp}°C")

                # 功率
                current_power = power_info.get('power_w', '--')
                self.power_label.setText(f"⚡ 当前功率: {current_power}W")

                # 今日用电 (空调通常不支持)
                today_energy = power_info.get('today_energy_kwh')
                if today_energy is not None:
                    self.energy_label.setText(f"🔋 今日用电: {today_energy}度")
                    self.energy_label.show()
                else:
                    self.energy_label.hide()

                self.status_label.setText("已连接")
            else:
                self.status_label.setText("部分数据获取失败")

            self.power_btn.style().unpolish(self.power_btn)
            self.power_btn.style().polish(self.power_btn)

        except Exception as e:
            self.status_label.setText(f"获取状态失败: {str(e)[:30]}")

    def toggle_power(self):
        """切换电源"""
        current_state = self.power_btn.property("off")
        if current_state == "true":
            self.power_btn.setProperty("off", "false")
            self.power_btn.setText("🔌 电源 (开)")
            self.set_ac_property('power', True)
        else:
            self.power_btn.setProperty("off", "true")
            self.power_btn.setText("🔌 电源 (关)")
            self.set_ac_property('power', False)
        self.power_btn.style().unpolish(self.power_btn)
        self.power_btn.style().polish(self.power_btn)

    def set_ac_property(self, property_name: str, value):
        """设置空调属性"""
        try:
            print(f"设置空调 {self.did}: {property_name} = {value}")
            result = self.client.set_ac_property(self.did, property_name, value)
            if result:
                self.status_label.setText(f"设置成功: {property_name}")
            else:
                self.status_label.setText(f"设置失败: {property_name}")
        except Exception as e:
            self.status_label.setText(f"设置失败: {str(e)[:30]}")
            print(f"设置空调属性失败: {e}")


class MijiaWidget(QWidget):
    """米家桌面插件主窗口"""

    devices_updated = pyqtSignal(list)
    plug_power_updated = pyqtSignal(str, dict)  # did, info

    def __init__(self):
        super().__init__()
        self.client = MijiaClient()
        self.devices: List[Dict] = []
        self.drag_position = None
        self.is_topmost = WINDOW_TOPMOST
        self.is_click_through = False  # 点击穿透状态
        self.plug_cards: Dict[str, DeviceCard] = {}  # 存储插座卡片引用

        self.setup_ui()
        self.setup_tray()  # 设置系统托盘
        self.setup_timer()

        # 连接信号
        self.devices_updated.connect(self.update_device_list)
        self.plug_power_updated.connect(self._update_plug_card)

        # 首次加载
        self.refresh_devices()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle(f"米家设备 {VERSION}")
        self.setMinimumSize(300, 400)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 设置窗口标志
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.is_topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # 设置样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {STYLE['bg_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QLabel {{
                background-color: transparent;
                color: {STYLE['text_color']};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {STYLE['card_bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {STYLE['accent_color']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet(f"background-color: {STYLE['card_bg']};")
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 5, 10, 5)

        # 标题
        title_label = QLabel("🏠 米家设备")
        title_label.setFont(QFont(STYLE['font_family'], 13, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {STYLE['text_color']};")
        title_layout.addWidget(title_label)

        title_layout.addStretch()

        # 创建按钮容器
        btn_container = QWidget()
        btn_container_layout = QHBoxLayout(btn_container)
        btn_container_layout.setSpacing(5)
        btn_container_layout.setContentsMargins(0, 0, 0, 0)

        # 按钮样式 - 直接在按钮上设置
        accent_color = STYLE['accent_color']
        close_color = "#ff4444"
        hover_color = "#0095cc"
        close_hover = "#cc0000"

        # 创建按钮的辅助函数
        def create_btn(text, tooltip, bg_color, hover_color, callback):
            btn = QPushButton(text)
            btn.setFixedSize(28, 22)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)
            btn.clicked.connect(callback)
            return btn

        # 最小化按钮 (_ 符号) - 点击隐藏到托盘
        self.minimize_btn = create_btn("—", "最小化到托盘", "#4a90d9", "#357abd", self.hide_to_tray)
        btn_container_layout.addWidget(self.minimize_btn)

        # 置顶切换按钮 (📌/📍 图标)
        self.topmost_btn = create_btn("📌" if self.is_topmost else "📍", "切换置顶", accent_color, "#0095cc", self.toggle_topmost)
        btn_container_layout.addWidget(self.topmost_btn)

        # 点击穿透按钮 (👁 图标)
        self.click_through_btn = create_btn("👁", "点击穿透", "#9b59b6", "#8e44ad", self.toggle_click_through)
        btn_container_layout.addWidget(self.click_through_btn)

        # 设置按钮 (⚙ 图标)
        self.settings_btn = create_btn("⚙", "设置", accent_color, "#0095cc", self.show_settings)
        btn_container_layout.addWidget(self.settings_btn)

        # 关闭按钮 (X)
        self.close_btn = create_btn("×", "关闭", "#e74c3c", "#c0392b", self.close)
        btn_container_layout.addWidget(self.close_btn)

        title_layout.addWidget(btn_container)
        main_layout.addWidget(self.title_bar)

        # 状态栏
        self.status_label = QLabel("正在加载...")
        self.status_label.setStyleSheet(f"color: {STYLE['accent_color']}; padding: 5px 15px; font-size: 11px;")
        main_layout.addWidget(self.status_label)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 设备容器
        self.devices_container = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_container)
        self.devices_layout.setSpacing(5)
        self.devices_layout.setContentsMargins(10, 10, 10, 10)
        self.devices_layout.addStretch()

        scroll.setWidget(self.devices_container)
        main_layout.addWidget(scroll)

        # 底部信息
        footer = QWidget()
        footer.setFixedHeight(30)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(15, 5, 15, 5)

        self.count_label = QLabel("设备: 0")
        self.count_label.setStyleSheet(f"color: #888888; font-size: 11px;")
        footer_layout.addWidget(self.count_label)

        footer_layout.addStretch()

        self.time_label = QLabel("")
        self.time_label.setStyleSheet(f"color: #888888; font-size: 11px;")
        footer_layout.addWidget(self.time_label)

        main_layout.addWidget(footer)

        # 添加右下角调整大小抓手
        self.size_grip = QSizeGrip(self)
        main_layout.addWidget(self.size_grip, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    def update_stylesheet(self):
        """更新样式表"""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {STYLE['bg_color']};
                font-family: "{STYLE['font_family']}";
            }}
            QLabel {{
                background-color: transparent;
                color: {STYLE['text_color']};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {STYLE['card_bg']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {STYLE['accent_color']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QPushButton {{
                background-color: {STYLE['accent_color']};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #0095cc;
            }}
        """)

    def enterEvent(self, event):
        """鼠标进入窗口时显示标题栏"""
        super().enterEvent(event)
        # 标题栏始终显示，不再自动隐藏
        pass

    def leaveEvent(self, event):
        """鼠标离开窗口时延迟隐藏标题栏"""
        super().leaveEvent(event)
        # 标题栏始终显示，不再自动隐藏
        pass

    def hide_title_bar(self):
        """隐藏标题栏"""
        # 标题栏始终显示，不再自动隐藏
        pass

    def setup_tray(self):
        """设置系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)

        # 创建图标（使用简单的文字图标）
        # 如果没有图标文件，使用程序内置图标
        tray_pixmap = QPixmap(64, 64)
        tray_pixmap.fill(QColor(STYLE['accent_color']))
        self.tray_icon.setIcon(QIcon(tray_pixmap))
        self.tray_icon.setToolTip(f"米家桌面插件 {VERSION}")

        # 创建托盘菜单
        tray_menu = QMenu()

        # 显示/隐藏
        show_action = tray_menu.addAction("显示窗口")
        show_action.triggered.connect(self.show_from_tray)

        # 置顶切换
        self.tray_topmost_action = tray_menu.addAction("置顶显示")
        self.tray_topmost_action.setCheckable(True)
        self.tray_topmost_action.setChecked(self.is_topmost)
        self.tray_topmost_action.triggered.connect(self.toggle_topmost)

        tray_menu.addSeparator()

        # 刷新设备
        refresh_action = tray_menu.addAction("刷新设备")
        refresh_action.triggered.connect(self.refresh_devices)

        tray_menu.addSeparator()

        # 设置
        settings_action = tray_menu.addAction("设置")
        settings_action.triggered.connect(self.show_settings)

        tray_menu.addSeparator()

        # 退出
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)

        # 单击托盘图标显示/隐藏窗口
        self.tray_icon.activated.connect(self.tray_icon_activated)

        # 显示托盘图标
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        """托盘图标被点击"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击切换显示/隐藏
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()

    def hide_to_tray(self):
        """隐藏窗口到托盘"""
        self.hide()
        self.tray_icon.showMessage(
            "米家桌面插件",
            "程序已最小化到系统托盘，双击图标恢复显示",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def show_from_tray(self):
        """从托盘显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        """退出程序"""
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        """关闭窗口时最小化到托盘而不是退出"""
        event.ignore()
        self.hide_to_tray()

    def toggle_topmost(self):
        """切换窗口置顶状态"""
        self.is_topmost = not self.is_topmost

        # 保存设置
        save_config(topmost=self.is_topmost)

        # 更新按钮图标
        self.topmost_btn.setText("📌" if self.is_topmost else "📍")

        # 更新托盘菜单
        if hasattr(self, 'tray_topmost_action'):
            self.tray_topmost_action.setChecked(self.is_topmost)

        # 重新设置窗口标志（需要重新show）
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.is_topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def toggle_click_through(self):
        """切换点击穿透状态（Windows平台）"""
        import ctypes

        self.is_click_through = not self.is_click_through

        # 获取窗口句柄 (转换为整数)
        hwnd = int(self.winId())

        # Windows 常量
        GWL_EXSTYLE = -20
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_LAYERED = 0x00080000

        # 获取当前扩展样式
        user32 = ctypes.windll.user32
        current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

        if self.is_click_through:
            # 开启点击穿透
            new_style = current_style | WS_EX_TRANSPARENT | WS_EX_LAYERED
            self.click_through_btn.setText("👁️‍🗨️")
            self.click_through_btn.setToolTip("点击穿透已开启（点击恢复按钮关闭）")
            # 创建恢复按钮窗口
            self._show_restore_button()
        else:
            # 关闭点击穿透
            new_style = current_style & ~WS_EX_TRANSPARENT
            self.click_through_btn.setText("👁")
            self.click_through_btn.setToolTip("点击穿透")
            # 关闭恢复按钮
            self._hide_restore_button()

        # 设置新的扩展样式
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

        # 强制刷新窗口
        user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                           0x0001 | 0x0002 | 0x0004 | 0x0020)

    def _show_restore_button(self):
        """显示恢复按钮（一个小窗口，始终可点击）"""
        if hasattr(self, '_restore_btn') and self._restore_btn:
            self._restore_btn.close()

        self._restore_btn = QWidget(None, Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        # 与原点击穿透按钮尺寸一致
        self._restore_btn.setFixedSize(28, 22)

        btn = QPushButton("👁️‍🗨️", self._restore_btn)
        btn.setFixedSize(28, 22)
        btn.move(0, 0)
        # 与原按钮样式一致
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90d9;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        btn.clicked.connect(self._restore_from_click_through)

        # 定位在原来的点击穿透按钮位置
        btn_pos = self.click_through_btn.mapToGlobal(self.click_through_btn.rect().topLeft())
        self._restore_btn.move(btn_pos)
        self._restore_btn.show()

    def _hide_restore_button(self):
        """隐藏恢复按钮"""
        if hasattr(self, '_restore_btn') and self._restore_btn:
            self._restore_btn.close()
            self._restore_btn = None

    def _restore_from_click_through(self):
        """从点击穿透模式恢复"""
        self._hide_restore_button()
        self.toggle_click_through()

    def show_settings(self):
        """显示设置面板"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 重新应用样式
            self.update_stylesheet()
            # 刷新设备列表以应用新样式
            self.refresh_devices()

    def setup_timer(self):
        """设置定时刷新"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_devices)
        self.timer.start(REFRESH_INTERVAL * 1000)

        # 更新时间显示
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()

        # 插座用电信息1秒刷新定时器
        self.plug_timer = QTimer(self)
        self.plug_timer.timeout.connect(self.refresh_plug_power)
        self.plug_timer.start(1000)  # 1秒刷新一次

    def update_time(self):
        """更新时间显示"""
        current = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"更新于: {current}")

    def refresh_devices(self):
        """刷新设备列表"""
        self.status_label.setText("正在刷新...")

        # 在后台线程获取设备
        def fetch():
            devices = self.client.get_devices(force_refresh=True)
            self.devices_updated.emit(devices)

        threading.Thread(target=fetch, daemon=True).start()

    def update_device_list(self, devices: List[Dict]):
        """更新设备列表UI"""
        self.devices = devices

        # 清空现有卡片
        while self.devices_layout.count() > 1:
            item = self.devices_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not devices:
            empty_label = QLabel("暂无设备或登录失败\n请先运行: mijiaAPI --login")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet(f"color: #888888; padding: 50px;")
            self.devices_layout.insertWidget(0, empty_label)
            self.status_label.setText("未获取到设备")
        else:
            online_count = sum(1 for d in devices if d.get('is_online'))
            self.status_label.setText(f"共 {len(devices)} 个设备，{online_count} 个在线")

            # 按在线状态排序
            sorted_devices = sorted(devices, key=lambda x: (not x.get('is_online'), x.get('name', '')))

            # 清空插座卡片引用
            self.plug_cards.clear()

            for device in sorted_devices:
                did = device.get('did', '')
                # 检查是否是插座
                is_plug = 'plug' in device.get('model', '').lower() or '插座' in device.get('name', '') or 'plug' in device.get('name', '').lower()

                if is_plug:
                    # 插座使用选项回调
                    card = DeviceCard(device, self.client, self.show_plug_detail, self.show_plug_options)
                    # 恢复保存的选项
                    if did in PLUG_OPTIONS:
                        card.set_options(PLUG_OPTIONS[did])
                    # 存储引用
                    self.plug_cards[did] = card
                else:
                    card = DeviceCard(device, self.client, self.show_plug_detail)

                self.devices_layout.insertWidget(self.devices_layout.count() - 1, card)

            # 启动后立即获取一次插座用电信息
            if self.plug_cards:
                for did in self.plug_cards.keys():
                    threading.Thread(target=self._fetch_plug_power, args=(did,), daemon=True).start()

    def _fetch_plug_power(self, did: str):
        """获取单个插座的用电信息"""
        try:
            info = self.client.get_plug_power_info(did)
            if info:
                # 发射信号，由主线程更新UI
                self.plug_power_updated.emit(did, info)
        except Exception as e:
            print(f"获取插座用电信息失败 {did}: {e}")

    def _update_plug_card(self, did: str, info: Dict):
        """更新插座卡片显示（在主线程调用）"""
        if did in self.plug_cards:
            self.plug_cards[did].update_power_info(info)

    def refresh_plug_power(self):
        """刷新所有插座的用电信息"""
        for did in list(self.plug_cards.keys()):
            threading.Thread(target=self._fetch_plug_power, args=(did,), daemon=True).start()

    def show_plug_options(self, device: Dict, current_options: Dict, callback):
        """显示插座选项对话框"""
        dialog = PlugOptionsDialog(device, current_options, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_options = dialog.get_options()
            callback(new_options)
            # 保存选项到配置文件
            did = device.get('did', '')
            if did:
                PLUG_OPTIONS[did] = new_options
                save_config(plug_options=PLUG_OPTIONS)

    def show_plug_detail(self, device: Dict):
        """显示插座详情弹窗"""
        dialog = PlugDetailDialog(device, self.client, self)
        dialog.exec()

        self.count_label.setText(f"设备: {len(self.devices)}")
        self.update_time()

    # 鼠标拖拽移动窗口
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def keyPressEvent(self, event):
        """快捷键：ESC 最小化，R 刷新"""
        if event.key() == Qt.Key.Key_Escape:
            self.showMinimized()
        elif event.key() == Qt.Key.Key_R:
            self.refresh_devices()
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # 设置应用程序字体
    font = QFont(STYLE['font_family'], 10)
    app.setFont(font)

    widget = MijiaWidget()

    # 显示在屏幕中央
    screen = app.primaryScreen().geometry()
    x = (screen.width() - WINDOW_WIDTH) // 2
    y = (screen.height() - WINDOW_HEIGHT) // 2
    widget.move(x, y)

    widget.show()
    widget.activateWindow()  # 激活窗口到最前

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
