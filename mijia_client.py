"""
米家API客户端封装
"""
from mijiaAPI import mijiaAPI
from typing import List, Dict, Any, Optional
import json
import os
import time
import requests


class MijiaClient:
    """米家API客户端"""

    def __init__(self, auth_file: str = None):
        self.auth_file = auth_file or os.path.expanduser("~/.config/mijia-api/auth.json")
        self.api: Optional[mijiaAPI] = None
        self._devices_cache: List[Dict] = []
        self._spec_cache: Dict[str, Dict] = {}  # 缓存设备规格

    def _get_device_spec(self, model: str) -> Optional[Dict]:
        """从 home.miot-spec.com 获取设备MIOT规格"""
        if model in self._spec_cache:
            return self._spec_cache[model]

        try:
            url = f"https://home.miot-spec.com/spec/{model}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                self._spec_cache[model] = response.json()
                return self._spec_cache[model]
        except Exception as e:
            print(f"获取设备规格失败: {e}")
        return None

    def connect(self) -> bool:
        """连接并登录米家账号"""
        try:
            self.api = mijiaAPI(self.auth_file)
            self.api.login()
            print("米家账号登录成功")
            return True
        except Exception as e:
            print(f"登录失败: {e}")
            return False

    def get_devices(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """获取所有设备列表"""
        if not self.api:
            if not self.connect():
                return []

        if not force_refresh and self._devices_cache:
            return self._devices_cache

        try:
            devices = self.api.get_devices_list()
            # 获取共享设备
            shared_devices = self.api.get_shared_devices_list()
            all_devices = devices + shared_devices

            # 补充设备信息
            for device in all_devices:
                # 米家API使用驼峰命名 isOnline
                is_online = device.get('isOnline', False)
                device['is_online'] = is_online  # 统一字段名
                device['status_text'] = '在线' if is_online else '离线'
                device['status_icon'] = '🟢' if is_online else '🔴'

            self._devices_cache = all_devices
            return all_devices
        except Exception as e:
            error_msg = str(e)
            suggestion = '\n建议执行: mijiaAPI --login 重新登录' if 'auth' in error_msg.lower() else ''
            print(f"获取设备列表失败: {error_msg}{suggestion}")
            return self._devices_cache if self._devices_cache else []

    def get_device_status(self, device: Dict) -> Dict[str, Any]:
        """获取单个设备的详细状态"""
        if not self.api:
            return {}

        did = device.get('did')
        if not did:
            return {}

        try:
            # 尝试获取设备基本信息
            from mijiaAPI import mijiaDevice
            dev = mijiaDevice(self.api, did=did)
            info = dev.get_device_info()

            status = {
                'online': device.get('is_online', False),
                'name': device.get('name', '未知设备'),
                'model': device.get('model', ''),
            }

            # 如果是支持的设备类型，获取更多属性
            if info and 'services' in info:
                for service in info['services']:
                    for prop in service.get('properties', []):
                        prop_name = prop.get('description') or prop.get('type', 'unknown')
                        try:
                            value = dev.get(prop_name)
                            status[prop_name] = value
                        except:
                            pass

            return status
        except Exception as e:
            print(f"获取设备状态失败 {device.get('name')}: {e}")
            return {
                'online': device.get('is_online', False),
                'name': device.get('name', '未知设备'),
                'model': device.get('model', ''),
            }

    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return os.path.exists(self.auth_file)

    def get_plug_power_info(self, did: str) -> Optional[Dict[str, Any]]:
        """获取智能插座实时用电信息（支持cuco.plug.v3等型号）

        MIOT规格：
        - 服务11, 属性2: Electric Power (当前功率，单位W，float)
        - 服务11, 属性1: Power Consumption (累计用电量)
        - 服务2, 属性1: Switch Status (开关状态)

        Returns:
            dict: 包含power_w(功率W)、energy_kwh(累计电量kWh)、is_on等字段
            None: 获取失败
        """
        if not self.api:
            return None

        result = {}

        # 获取当前功率 (服务11, 属性2)
        try:
            power_res = self.api.get_devices_prop({
                "did": did,
                "siid": 11,
                "piid": 2
            })
            if power_res.get('code') == 0:
                result['power_w'] = power_res.get('value')
        except Exception as e:
            print(f"获取功率失败: {e}")

        # 获取累计用电量 (服务11, 属性1)
        try:
            energy_res = self.api.get_devices_prop({
                "did": did,
                "siid": 11,
                "piid": 1
            })
            if energy_res.get('code') == 0:
                energy = energy_res.get('value', 0)
                if isinstance(energy, (int, float)):
                    result['energy_raw'] = energy
                    # MIOT协议中 uint16 类型的电量值，单位通常是 0.01 kWh
                    result['energy_kwh'] = round(energy * 0.01, 2)
        except Exception as e:
            print(f"获取累计电量失败: {e}")

        # 从云端获取今日用电和累计用电统计
        try:
            # 获取今日用电统计 (stat_day_v3 获取今天的数据)
            today_start = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')))
            today_end = int(time.time())

            # 尝试获取电量统计 (key格式: siid.piid)
            # 对于智能插座，通常是 "11.1" 表示电量统计
            stats = self.api.get_statistics({
                "did": did,
                "key": "11.1",
                "data_type": "stat_day_v3",
                "limit": 1,
                "time_start": today_start,
                "time_end": today_end
            })

            if stats and len(stats) > 0:
                # 解析今日用电量
                today_value = stats[0].get('value')
                if today_value:
                    try:
                        # value 是一个字符串列表，如 "[0.5]"
                        today_energy = eval(today_value)[0]
                        # 云端返回的单位是 0.01 kWh，需要除以 100
                        result['today_energy_kwh'] = round(today_energy / 100, 2)
                    except:
                        pass

            # 获取累计用电统计 (获取最近30天的数据并累加)
            month_start = int(time.time() - 30 * 24 * 3600)
            total_stats = self.api.get_statistics({
                "did": did,
                "key": "11.1",
                "data_type": "stat_day_v3",
                "limit": 30,
                "time_start": month_start,
                "time_end": today_end
            })

            if total_stats and len(total_stats) > 0:
                total_energy = 0
                for stat in total_stats:
                    try:
                        value = eval(stat.get('value', '[0]'))[0]
                        total_energy += value
                    except:
                        pass
                if total_energy > 0:
                    # 云端返回的单位是 0.01 kWh，需要除以 100
                    result['energy_kwh'] = round(total_energy / 100, 2)

        except Exception as e:
            print(f"获取云端用电统计失败: {e}")

        # 获取开关状态 (服务2, 属性1)
        try:
            on_res = self.api.get_devices_prop({
                "did": did,
                "siid": 2,
                "piid": 1
            })
            if on_res.get('code') == 0:
                result['is_on'] = on_res.get('value')
        except Exception as e:
            print(f"获取开关状态失败: {e}")

        return result if result else None

    def _get_device_model(self, did: str) -> Optional[str]:
        """根据did获取设备model"""
        devices = self.get_devices()
        for device in devices:
            if device.get('did') == did:
                return device.get('model')
        return None

    def set_ac_property(self, did: str, property_name: str, value) -> bool:
        """设置空调属性（开关、温度、模式、风速）"""
        if not self.api:
            print("API未初始化")
            return False

        try:
            # 获取设备model
            model = self._get_device_model(did)
            if not model:
                print(f"找不到设备: {did}")
                return False

            # 获取设备规格
            spec = self._get_device_spec(model)
            if not spec or 'services' not in spec:
                print(f"无法获取设备规格: {model}")
                return False

            # 属性名映射：通用名称 -> 可能的关键词
            prop_keywords = {
                'power': ['switch', 'power', 'on'],
                'temperature': ['target-temperature', 'temperature', 'temp'],
                'mode': ['mode'],
                'fan_speed': ['fan-level', 'fan-speed', 'wind-level', 'wind-speed'],
            }

            # 转换值为设备可接受的格式
            if property_name == 'power':
                value = bool(value)
            elif property_name == 'temperature':
                value = int(value)
            elif property_name == 'mode':
                mode_value_map = {'cool': 1, 'heat': 2, 'dry': 3, 'fan': 4, 'auto': 0}
                value = mode_value_map.get(value, 0)
            elif property_name == 'fan_speed':
                fan_value_map = {'auto': 0, 'low': 1, 'medium': 2, 'high': 3, 'strong': 4}
                value = fan_value_map.get(value, 0)

            keywords = prop_keywords.get(property_name, [property_name])

            for service in spec['services']:
                siid = service.get('iid')
                for prop in service.get('properties', []):
                    prop_type = prop.get('type', '').lower()
                    prop_desc = (prop.get('description') or '').lower()
                    piid = prop.get('iid')
                    access = prop.get('access', [])

                    for keyword in keywords:
                        if keyword.lower() in prop_type or keyword.lower() in prop_desc:
                            if 2 not in access:  # 检查是否可写
                                continue

                            try:
                                result = self.api.set_devices_prop({
                                    "did": did,
                                    "siid": siid,
                                    "piid": piid,
                                    "value": value
                                })

                                if result.get('code') == 0:
                                    print(f"设置成功: {property_name} = {value}")
                                    return True
                                else:
                                    print(f"设置失败: {result.get('message', result)}")
                            except Exception as e:
                                print(f"设置属性失败: {e}")

            print(f"未找到可写的属性: {property_name}")
            return False

        except Exception as e:
            print(f"设置空调属性失败: {e}")
            return False

    def get_ac_status(self, did: str) -> Optional[Dict[str, Any]]:
        """获取空调当前状态"""
        if not self.api:
            return None

        try:
            # 获取设备model
            model = self._get_device_model(did)
            if not model:
                return None

            # 获取设备规格
            spec = self._get_device_spec(model)
            if not spec or 'services' not in spec:
                return None

            prop_map = {
                'power': ['switch', 'power', 'on'],
                'temperature': ['target-temperature', 'temperature', 'temp'],
                'mode': ['mode'],
                'fan_speed': ['fan-level', 'fan-speed', 'wind-level', 'wind-speed'],
            }

            result = {}
            for key, names in prop_map.items():
                for service in spec['services']:
                    siid = service.get('iid')
                    for prop in service.get('properties', []):
                        prop_type = prop.get('type', '').lower()
                        piid = prop.get('iid')

                        for name in names:
                            if name.lower() in prop_type:
                                try:
                                    res = self.api.get_devices_prop({
                                        "did": did,
                                        "siid": siid,
                                        "piid": piid
                                    })

                                    if res.get('code') == 0:
                                        value = res.get('value')
                                        if key == 'mode':
                                            mode_map = {0: 'auto', 1: 'cool', 2: 'heat', 3: 'dry', 4: 'fan'}
                                            result[key] = mode_map.get(value, 'auto')
                                        elif key == 'fan_speed':
                                            fan_map = {0: 'auto', 1: 'low', 2: 'medium', 3: 'high', 4: 'strong'}
                                            result[key] = fan_map.get(value, 'auto')
                                        elif key == 'temperature':
                                            result[key] = int(value) if value else 26
                                        else:
                                            result[key] = value
                                        break
                                except:
                                    pass
                        if key in result:
                            break
                    if key in result:
                        break

            return result if result else None

        except Exception as e:
            print(f"获取空调状态失败: {e}")
            return None
