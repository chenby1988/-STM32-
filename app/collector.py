"""
数据采集器模块
模拟STM32主循环中的数据采集逻辑
"""

import threading
import time
from typing import Dict, Optional, Callable
from datetime import datetime

from core.mcu import VirtualSTM32
from drivers.dht11 import DHT11Driver
from drivers.mq135 import MQ135Driver
from drivers.bh1750 import BH1750Driver
from drivers.noise import NoiseSensorDriver
from drivers.bmp280 import BMP280Driver
from app.storage import DataStorage
from app.alarm import AlarmSystem
from config.settings import COLLECTOR_CONFIG


class DataCollector:
    """
    环境数据采集器
    模拟STM32的main()函数中的数据采集循环
    """
    
    def __init__(self, mcu: VirtualSTM32, storage: DataStorage, alarm: AlarmSystem):
        self.mcu = mcu
        self.storage = storage
        self.alarm = alarm
        
        # 初始化传感器
        self.dht11 = DHT11Driver(mcu, "PA0", simulate_noise=True)
        self.mq135 = MQ135Driver(mcu, adc_channel=0, calibration_r0=10.0)
        self.bh1750 = BH1750Driver(mcu, i2c_address=0x23)
        self.noise = NoiseSensorDriver(mcu, adc_channel=1)
        self.bmp280 = BMP280Driver(mcu, i2c_address=0x76)
        
        # 最新数据缓存
        self._latest_data: Dict = {}
        self._data_lock = threading.Lock()
        
        # 运行状态
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._save_counter = 0
        
        # 数据更新回调（供Web界面使用）
        self._update_callbacks: List[Callable[[Dict], None]] = []
        
        print("[Collector] 数据采集器初始化完成")
    
    def register_update_callback(self, callback: Callable[[Dict], None]):
        """注册数据更新回调"""
        self._update_callbacks.append(callback)
    
    def start(self):
        """启动采集循环"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        self.mcu.printf("Collector: 采集循环启动")
    
    def stop(self):
        """停止采集循环"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.mcu.printf("Collector: 采集循环停止")
    
    def _collect_loop(self):
        """
        主采集循环
        模拟STM32的 while(1) { ... } 主循环
        """
        while self._running:
            loop_start = time.time()
            
            try:
                # 读取所有传感器
                data = self._read_sensors()
                
                # 告警检查
                alarm_result = self.alarm.check_all(data)
                data['alarm_flags'] = alarm_result
                
                # 更新缓存
                with self._data_lock:
                    self._latest_data = data.copy()
                
                # 保存到数据库
                self._save_counter += 1
                if self._save_counter >= COLLECTOR_CONFIG['save_interval_s']:
                    self.storage.save_sensor_data(data)
                    self._save_counter = 0
                
                # 触发更新回调
                for cb in self._update_callbacks:
                    try:
                        cb(data)
                    except Exception as e:
                        print(f"[Collector] 回调错误: {e}")
                
            except Exception as e:
                self.mcu.printf("Collector: 采集错误 %s", str(e))
                self.storage.log_system("ERROR", f"采集错误: {e}")
            
            # 控制采样率
            elapsed = time.time() - loop_start
            sleep_time = max(0, COLLECTOR_CONFIG['sample_interval_ms'] / 1000.0 - elapsed)
            time.sleep(sleep_time)
    
    def _read_sensors(self) -> Dict:
        """读取所有传感器数据（单个传感器失败不影响其他）"""
        temp, hum = None, None
        air = {}
        light = None
        noise = None
        
        # DHT11温湿度
        try:
            temp, hum = self.dht11.read()
        except Exception as e:
            self.mcu.printf("DHT11读取失败: %s", str(e))
        
        # MQ135空气质量
        try:
            air = self.mq135.read()
        except Exception as e:
            self.mcu.printf("MQ135读取失败: %s", str(e))
        
        # BH1750光照
        try:
            light = self.bh1750.read()
        except Exception as e:
            self.mcu.printf("BH1750读取失败: %s", str(e))
        
        # 噪音
        try:
            noise = self.noise.read()
        except Exception as e:
            self.mcu.printf("Noise读取失败: %s", str(e))
        
        # BMP280气压
        bmp = {}
        try:
            bmp = self.bmp280.read()
        except Exception as e:
            self.mcu.printf("BMP280读取失败: %s", str(e))
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'temperature': temp,
            'humidity': hum,
            'air_quality_ppm': air.get('ppm') if air else None,
            'air_quality_aqi': air.get('aqi') if air else None,
            'light_lux': light,
            'noise_db': noise,
            'pressure_hpa': bmp.get('pressure') if bmp else None,
            'bmp280_temp': bmp.get('temperature') if bmp else None,
            'uptime_s': round(self.mcu.get_uptime_s(), 1),
        }
        
        self.mcu.printf("Data: T=%s H=%s AQI=%s L=%s N=%s P=%s",
                        temp if temp is not None else '--',
                        hum if hum is not None else '--',
                        air.get('aqi', '--') if air else '--',
                        light if light is not None else '--',
                        noise if noise is not None else '--',
                        bmp.get('pressure', '--') if bmp else '--')
        
        return data
    
    def get_latest_data(self) -> Dict:
        """获取最新数据"""
        with self._data_lock:
            return self._latest_data.copy()
    
    def set_environment_values(self, temp=None, humidity=None, 
                               air_quality=None, light=None, noise=None, pressure=None):
        """
        设置环境真实值（由环境模拟器调用）
        这相当于调整传感器所在的真实物理环境
        """
        if temp is not None:
            self.dht11.set_real_values(temp, self.dht11._humidity if humidity is None else humidity)
        if humidity is not None:
            self.dht11.set_real_values(self.dht11._temperature if temp is None else temp, humidity)
        if air_quality is not None:
            self.mq135.set_real_values(air_quality, air_quality)
        if light is not None:
            self.bh1750.set_real_values(light)
        if noise is not None:
            self.noise.set_real_values(noise)
        if pressure is not None:
            self.bmp280.set_real_values(pressure, temp if temp is not None else 25.0)
