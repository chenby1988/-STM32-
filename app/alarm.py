"""
告警系统模块
模拟STM32中的告警判断和指示逻辑
"""

import threading
from typing import Dict, List, Callable
from datetime import datetime

from config.settings import ALARM_CONFIG


class AlarmSystem:
    """
    环境告警系统
    当传感器数据超出设定阈值时触发告警
    """
    
    def __init__(self, storage=None):
        self.config = ALARM_CONFIG
        self.storage = storage
        self._alarm_state: Dict[str, bool] = {}  # 当前告警状态
        self._callbacks: List[Callable[[str, str, float], None]] = []
        self._lock = threading.Lock()
    
    def register_callback(self, callback: Callable[[str, str, float], None]):
        """注册告警回调函数"""
        self._callbacks.append(callback)
    
    def check_all(self, data: Dict) -> Dict[str, str]:
        """
        检查所有传感器数据是否超出阈值
        返回: {传感器名: 告警信息}
        """
        alarms = {}
        
        # 温度检查
        temp = data.get('temperature')
        if temp is not None:
            msg = self._check_value('temperature', temp, 
                                    self.config['temperature'].get('min'),
                                    self.config['temperature'].get('max'))
            if msg:
                alarms['temperature'] = msg
        
        # 湿度检查
        hum = data.get('humidity')
        if hum is not None:
            msg = self._check_value('humidity', hum,
                                    self.config['humidity'].get('min'),
                                    self.config['humidity'].get('max'))
            if msg:
                alarms['humidity'] = msg
        
        # 空气质量检查
        aqi = data.get('air_quality_aqi')
        if aqi is not None:
            msg = self._check_value('air_quality', aqi,
                                    None,
                                    self.config['air_quality'].get('max'))
            if msg:
                alarms['air_quality'] = msg
        
        # 光照检查
        light = data.get('light_lux')
        if light is not None:
            msg = self._check_value('light', light,
                                    self.config['light'].get('min'),
                                    self.config['light'].get('max'))
            if msg:
                alarms['light'] = msg
        
        # 噪音检查
        noise = data.get('noise_db')
        if noise is not None:
            msg = self._check_value('noise', noise,
                                    None,
                                    self.config['noise'].get('max'))
            if msg:
                alarms['noise'] = msg
        
        # 气压检查
        pressure = data.get('pressure_hpa')
        if pressure is not None:
            msg = self._check_value('pressure', pressure,
                                    self.config['pressure'].get('min'),
                                    self.config['pressure'].get('max'))
            if msg:
                alarms['pressure'] = msg
        
        # 更新状态并触发回调
        with self._lock:
            self._alarm_state = {k: True for k in alarms}
        
        for sensor, msg in alarms.items():
            for cb in self._callbacks:
                try:
                    cb(sensor, msg, data.get(sensor))
                except Exception:
                    pass
            
            # 记录到数据库
            if self.storage:
                cfg = self.config.get(sensor, {})
                threshold = cfg.get('max') if '过高' in msg else cfg.get('min')
                alarm_type = 'HIGH' if '过高' in msg else 'LOW'
                self.storage.save_alarm(sensor, data.get(sensor), threshold, alarm_type, msg)
        
        return alarms
    
    def _check_value(self, name: str, value: float, min_val, max_val) -> str:
        """检查单个值是否越界"""
        if min_val is not None and value < min_val:
            return f"{self._get_sensor_name(name)}过低: {value} (最低{min_val})"
        if max_val is not None and value > max_val:
            return f"{self._get_sensor_name(name)}过高: {value} (最高{max_val})"
        return ""
    
    def _get_sensor_name(self, key: str) -> str:
        """获取传感器中文名"""
        names = {
            'temperature': '温度',
            'humidity': '湿度',
            'air_quality': '空气质量',
            'light': '光照',
            'noise': '噪音',
            'pressure': '气压',
        }
        return names.get(key, key)
    
    def get_alarm_state(self) -> Dict[str, bool]:
        """获取当前告警状态"""
        with self._lock:
            return self._alarm_state.copy()
    
    def is_alarming(self) -> bool:
        """是否有活跃告警"""
        with self._lock:
            return any(self._alarm_state.values())
    
    def reset(self):
        """重置所有告警"""
        with self._lock:
            self._alarm_state.clear()
    
    def get_status_summary(self, data: Dict) -> Dict:
        """获取状态摘要（含告警信息）"""
        alarms = self.check_all(data)
        status = "告警" if alarms else "正常"
        return {
            'status': status,
            'alarm_count': len(alarms),
            'alarms': alarms,
            'timestamp': datetime.now().isoformat(),
        }
