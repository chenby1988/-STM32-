"""
STM32 智能环境监测站 - 主程序
模拟真实STM32项目的 main.c 入口

运行方式:
    python main.py

功能:
    1. 初始化虚拟STM32 MCU
    2. 初始化所有传感器驱动
    3. 启动数据采集循环
    4. 启动Web服务器（模拟WiFi模块上传数据）
    5. 启动环境控制面板（模拟外部环境变化）
"""

import sys
import os
import time
import signal
import threading

# 确保当前目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import MCU_CONFIG, ENV_SIMULATION
from core.mcu import VirtualSTM32
from app.storage import DataStorage
from app.alarm import AlarmSystem
from app.collector import DataCollector
from web.server import WebServer


class EnvSimulation:
    """
    环境模拟器
    模拟外部环境的变化，让传感器有真实的数据来源
    """
    
    def __init__(self, collector: DataCollector, config: dict):
        self.collector = collector
        self.config = config
        
        # 当前环境值
        self.temp = config['initial_temp']
        self.humidity = config['initial_humidity']
        self.air_quality = config['initial_air_quality']
        self.light = config['initial_light']
        self.noise = config['initial_noise']
        self.pressure = config['initial_pressure']
        
        self._running = False
        self._thread = None
    
    def start(self):
        """启动环境变化模拟"""
        self._running = True
        self._thread = threading.Thread(target=self._simulate, daemon=True)
        self._thread.start()
        print("[EnvSim] 环境模拟器启动")
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def _simulate(self):
        """模拟环境参数的缓慢变化"""
        import random
        rate = self.config['change_rate']
        env_file = os.path.join(os.path.dirname(__file__), 'data', 'env_control.txt')
        
        while self._running:
            # 检查是否有外部控制指令
            try:
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        for line in f:
                            if '=' in line:
                                k, v = line.strip().split('=', 1)
                                if k == 'temp':
                                    self.temp = float(v)
                                elif k == 'humidity':
                                    self.humidity = float(v)
                                elif k == 'air_quality':
                                    self.air_quality = float(v)
                                elif k == 'light':
                                    self.light = float(v)
                                elif k == 'noise':
                                    self.noise = float(v)
                                elif k == 'pressure':
                                    self.pressure = float(v)
            except Exception:
                pass
            
            # 模拟环境的缓慢随机波动
            self.temp += random.uniform(-rate, rate)
            self.humidity += random.uniform(-rate * 2, rate * 2)
            self.air_quality += random.uniform(-rate * 3, rate * 3)
            self.light += random.uniform(-rate * 10, rate * 10)
            self.noise += random.uniform(-rate * 2, rate * 2)
            
            # 限制在合理范围
            self.temp = max(-10, min(50, self.temp))
            self.humidity = max(10, min(95, self.humidity))
            self.air_quality = max(0, min(1000, self.air_quality))
            self.light = max(0, min(50000, self.light))
            self.noise = max(20, min(100, self.noise))
            self.pressure = max(900, min(1100, self.pressure))
            
            # 更新到传感器
            self.collector.set_environment_values(
                temp=self.temp,
                humidity=self.humidity,
                air_quality=self.air_quality,
                light=self.light,
                noise=self.noise,
                pressure=self.pressure
            )
            
            time.sleep(2)
    
    def set_values(self, **kwargs):
        """手动设置环境值（用于交互式控制）"""
        if 'temp' in kwargs:
            self.temp = kwargs['temp']
        if 'humidity' in kwargs:
            self.humidity = kwargs['humidity']
        if 'air_quality' in kwargs:
            self.air_quality = kwargs['air_quality']
        if 'light' in kwargs:
            self.light = kwargs['light']
        if 'noise' in kwargs:
            self.noise = kwargs['noise']
        
        self.collector.set_environment_values(
            temp=self.temp,
            humidity=self.humidity,
            air_quality=self.air_quality,
            light=self.light,
            noise=self.noise
        )


class MonitoringStation:
    """
    智能环境监测站主控类
    整合所有模块，提供统一的生命周期管理
    """
    
    def __init__(self):
        self.running = False
        
        # 初始化虚拟MCU
        print("=" * 60)
        print("  STM32 智能环境监测站 - 虚拟硬件模拟系统")
        print("=" * 60)
        print()
        
        self.mcu = VirtualSTM32(MCU_CONFIG)
        self.mcu.reset()
        
        # 初始化应用层
        self.storage = DataStorage()
        self.alarm = AlarmSystem(storage=self.storage)
        self.collector = DataCollector(self.mcu, self.storage, self.alarm)
        
        # 初始化Web服务器
        self.web = WebServer(self.storage, self.alarm, self.collector.get_latest_data)
        
        # 初始化环境模拟器
        self.env_sim = EnvSimulation(self.collector, ENV_SIMULATION)
        
        # 注册告警回调
        self.alarm.register_callback(self._on_alarm)
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        
        print()
        print("=" * 60)
    
    def _on_alarm(self, sensor: str, message: str, value: float):
        """告警回调"""
        print(f"[ALARM] 🚨 {message}")
    
    def _signal_handler(self, signum, frame):
        """处理Ctrl+C信号"""
        print("\n[MAIN] 收到停止信号，正在关闭...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """启动监测站"""
        self.running = True
        
        # 启动MCU
        self.mcu.run()
        self.mcu.adc1.enable()
        self.mcu.usart1.enable()
        self.mcu.i2c1.enable()
        
        # 启动各模块
        self.collector.start()
        self.env_sim.start()
        self.web.start()
        
        print()
        print("[MAIN] ✅ 监测站启动成功!")
        print(f"[MAIN] 🌐 Web界面: http://{self.web.config['host']}:{self.web.config['port']}")
        print("[MAIN] 📊 请在浏览器中打开上述地址查看实时数据")
        print("[MAIN] ⏹️  按 Ctrl+C 停止程序")
        print()
        
        # 主循环（模拟STM32的while(1)）
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止监测站"""
        self.running = False
        self.env_sim.stop()
        self.collector.stop()
        self.mcu.stop()
        print("[MAIN] 监测站已停止")


def main():
    """程序入口"""
    station = MonitoringStation()
    station.start()


if __name__ == "__main__":
    main()
