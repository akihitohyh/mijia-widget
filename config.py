# 米家桌面插件配置
import os
import json

# 认证文件路径
AUTH_FILE = os.path.expanduser("~/.config/mijia-api/auth.json")

# 配置文件路径
CONFIG_FILE = os.path.expanduser("~/.config/mijia-api/widget_config.json")

# UI配置
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 400
REFRESH_INTERVAL = 30   # 设备列表刷新间隔（秒）

# 默认样式配置
DEFAULT_STYLE = {
    "bg_color": "#1e1e1e",
    "card_bg": "#2d2d2d",
    "text_color": "#ffffff",
    "accent_color": "#00b8ff",
    "online_color": "#4caf50",
    "offline_color": "#f44336",
    "font_family": "Microsoft YaHei",
    "border_radius": "10px",
}

# 全局样式（会被配置文件覆盖）
STYLE = DEFAULT_STYLE.copy()

# 窗口透明度 (0.2 - 1.0)
WINDOW_OPACITY = 1.0

# 是否置顶
WINDOW_TOPMOST = True

# 插座显示选项（按设备DID存储）
PLUG_OPTIONS = {}

# 默认插座显示选项
DEFAULT_PLUG_OPTIONS = {
    'show_power': True,      # 显示当前功率
    'show_today_energy': True,  # 显示今日用电
    'show_total_energy': False,  # 显示累计用电
    'show_status': True,     # 显示开关状态
}

# 设备名称映射表（英文名称 -> 中文名称）
DEVICE_NAME_MAP = {
    # 小米/米家设备
    'Mijia Smart Plug 3': '米家智能插座3',
    'Mijia Smart Plug': '米家智能插座',
    'Xiaomi Smart Plug': '小米智能插座',
    'Xiaomi Smart Speaker': '小米智能音箱',
    'Xiaomi AI Speaker': '小米AI音箱',
    'Mi AI Speaker': '小爱音箱',
    'Xiaomi Router': '小米路由器',
    'Mi Router': '小米路由器',
    'Redmi Router': '红米路由器',
    'Xiaomi Camera': '小米摄像头',
    'Mi Camera': '小米摄像头',
    'Xiaomi Air Purifier': '小米空气净化器',
    'Mi Air Purifier': '米家空气净化器',
    'Xiaomi Humidifier': '小米加湿器',
    'Mi Humidifier': '米家加湿器',
    'Xiaomi Fan': '小米电风扇',
    'Mi Fan': '米家电风扇',
    'Xiaomi Lamp': '小米台灯',
    'Mi Lamp': '米家台灯',
    'Xiaomi Bulb': '小米灯泡',
    'Mi LED Bulb': '米家LED灯泡',
    'Xiaomi Switch': '小米开关',
    'Mi Wireless Switch': '米家无线开关',
    'Xiaomi Door Sensor': '小米门窗传感器',
    'Mi Door Sensor': '米家门窗传感器',
    'Xiaomi Temperature': '小米温湿度计',
    'Mi Temperature': '米家温湿度计',
    'Xiaomi Motion Sensor': '小米人体传感器',
    'Mi Motion Sensor': '米家人体传感器',
    'Xiaomi Water Sensor': '小米水浸传感器',
    'Mi Water Sensor': '米家水浸传感器',
    'Xiaomi Smoke Detector': '小米烟雾报警器',
    'Mi Smoke Detector': '米家烟雾报警器',
    'Xiaomi Gateway': '小米网关',
    'Mi Gateway': '米家网关',
    'Xiaomi Curtain': '小米窗帘电机',
    'Mi Curtain': '米家窗帘电机',
    'Xiaomi Vacuum': '小米扫地机器人',
    'Mi Robot Vacuum': '米家扫地机器人',
    'Roborock Vacuum': '石头扫地机器人',
    'Xiaomi TV': '小米电视',
    'Mi TV': '小米电视',
    'Xiaomi Projector': '小米投影仪',
    'Mi Projector': '米家投影仪',
}

def get_device_display_name(name: str) -> str:
    """获取设备的中文显示名称"""
    if not name:
        return '未知设备'
    # 直接匹配
    if name in DEVICE_NAME_MAP:
        return DEVICE_NAME_MAP[name]
    # 部分匹配（包含关键字）
    for en_name, cn_name in DEVICE_NAME_MAP.items():
        if en_name.lower() in name.lower():
            return cn_name
    # 返回原名
    return name


def load_config():
    """从配置文件加载设置"""
    global STYLE, WINDOW_OPACITY, WINDOW_TOPMOST, PLUG_OPTIONS

    if not os.path.exists(CONFIG_FILE):
        return

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 加载样式配置
        if 'style' in config:
            for key, value in config['style'].items():
                if key in STYLE:
                    STYLE[key] = value

        # 加载透明度
        if 'opacity' in config:
            WINDOW_OPACITY = max(0.2, min(1.0, config['opacity']))

        # 加载置顶设置
        if 'topmost' in config:
            WINDOW_TOPMOST = config['topmost']

        # 加载插座显示选项
        if 'plug_options' in config:
            PLUG_OPTIONS.update(config['plug_options'])

    except Exception as e:
        print(f"加载配置文件失败: {e}")


def save_config(opacity=None, style=None, topmost=None, plug_options=None):
    """保存配置到文件"""
    global WINDOW_OPACITY, WINDOW_TOPMOST, PLUG_OPTIONS

    # 确保配置目录存在
    config_dir = os.path.dirname(CONFIG_FILE)
    os.makedirs(config_dir, exist_ok=True)

    # 更新全局变量
    if opacity is not None:
        WINDOW_OPACITY = opacity
    if topmost is not None:
        WINDOW_TOPMOST = topmost
    if plug_options is not None:
        PLUG_OPTIONS.update(plug_options)

    # 构建配置字典
    config = {
        "opacity": WINDOW_OPACITY,
        "topmost": WINDOW_TOPMOST,
        "style": STYLE,
        "plug_options": PLUG_OPTIONS
    }

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False


# 程序启动时加载配置
load_config()
