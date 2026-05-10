"""
虚拟DHT11温湿度传感器驱动
模拟单总线协议读取温度和湿度

真实DHT11参数：
- 温度范围: 0~50°C, 精度±2°C
- 湿度范围: 20~90%RH, 精度±5%
- 采样周期: 最小2秒
- 数据格式: 40bit（湿度整数+湿度小数+温度整数+温度小数+校验和）
"""

import random
import time
from typing import Tuple

from core.mcu import VirtualSTM32


class DHT11Driver:
    """DHT11传感器驱动"""
    
    def __init__(self, mcu: VirtualSTM32, pin_name: str, simulate_noise: bool = True):
        self.mcu = mcu
        self.pin_name = pin_name
        self.simulate_noise = simulate_noise
        
        # 解析引脚名（如 "PA0" -> GPIOA, 0）
        self.gpio = self._parse_pin(pin_name)
        self.gpio.configure_pin(self.pin_num, "input")
        
        # 当前读数
        self._temperature = 25.0
        self._humidity = 50.0
        self._last_read_time = 0
        
        print(f"[DHT11] 驱动初始化，连接 {pin_name}")
    
    def _parse_pin(self, pin_name: str):
        """解析引脚名称"""
        port = pin_name[:2]  # PA, PB, PC
        self.pin_num = int(pin_name[2:])
        if port == "PA":
            return self.mcu.gpioa
        elif port == "PB":
            return self.mcu.gpiob
        elif port == "PC":
            return self.mcu.gpioc
        else:
            raise ValueError(f"未知端口: {port}")
    
    def set_real_values(self, temperature: float, humidity: float):
        """
        设置传感器的真实环境值（由环境模拟器调用）
        这模拟了真实世界中传感器感知到的物理量
        """
        self._temperature = temperature
        self._humidity = humidity
    
    def read(self) -> Tuple[float, float]:
        """
        读取温湿度（模拟单总线时序）
        返回: (温度°C, 湿度%)
        """
        now = self.mcu.get_tick_ms()
        if now - self._last_read_time < 2000:
            # DHT11要求最小2秒间隔
            self.mcu.printf("DHT11: 读取过快，返回缓存值")
        self._last_read_time = now
        
        # 模拟启动信号时序
        self._simulate_start_signal()
        
        # 模拟数据读取时序（40bit）
        self._simulate_data_transfer()
        
        # 添加传感器噪声和误差
        temp = self._temperature
        hum = self._humidity
        
        if self.simulate_noise:
            # DHT11精度：温度±2°C，湿度±5%
            temp += random.uniform(-0.5, 0.5)
            hum += random.uniform(-2.0, 2.0)
        
        # 限制在传感器有效范围内
        temp = max(0.0, min(50.0, temp))
        hum = max(20.0, min(90.0, hum))
        
        self.mcu.printf("DHT11: T=%.1fC, H=%.1f%%", temp, hum)
        return temp, hum
    
    def _simulate_start_signal(self):
        """模拟DHT11启动信号时序"""
        # MCU拉低至少18ms
        self.gpio.configure_pin(self.pin_num, "output")
        self.gpio.write_pin(self.pin_num, 0)
        self.mcu.delay_ms(20)
        
        # MCU拉高等待DHT响应
        self.gpio.write_pin(self.pin_num, 1)
        self.mcu.delay_ms(1)
        
        # DHT拉低响应（模拟）
        self.gpio.configure_pin(self.pin_num, "input")
        self.mcu.delay_ms(1)
    
    def _simulate_data_transfer(self):
        """模拟40bit数据传输"""
        # 每bit约传输时间
        for _ in range(40):
            self.mcu.delay_ms(1)  # 简化模拟
    
    def __repr__(self):
        return f"DHT11(pin={self.pin_name})"
