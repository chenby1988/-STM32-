"""
虚拟噪音传感器驱动
模拟ADC读取环境噪音分贝值

使用简单模拟麦克风模块（如KY-038）:
- 输出: 模拟电压，与声音强度成正比
- 通过ADC读取后转换为分贝值
"""

import random
import math
from core.mcu import VirtualSTM32


class NoiseSensorDriver:
    """噪音传感器驱动"""
    
    def __init__(self, mcu: VirtualSTM32, adc_channel: int):
        self.mcu = mcu
        self.adc_channel = adc_channel
        
        # 真实环境值
        self._db = 45.0  # 默认安静环境
        
        # 校准参数（简化模型）
        self.DB_OFFSET = 30.0   # 基准分贝
        self.DB_SCALE = 50.0    # 缩放系数
        
        print(f"[Noise] 噪音传感器初始化，ADC通道{adc_channel}")
    
    def set_real_values(self, db: float):
        """设置真实噪音值"""
        self._db = db
    
    def read(self) -> float:
        """
        读取噪音分贝值
        返回: dB值
        """
        # 将dB映射到电压 (0-3.3V)
        # 假设 30dB -> 0V, 100dB -> 3.3V (对数关系近似)
        db = max(30.0, min(100.0, self._db))
        
        # 简化的电压映射
        normalized = (db - self.DB_OFFSET) / self.DB_SCALE
        vout = normalized * 3.3
        vout = max(0.0, min(3.3, vout))
        
        # 添加噪声（模拟环境波动）
        vout += random.uniform(-0.05, 0.05)
        vout = max(0.0, min(3.3, vout))
        
        # 设置ADC并读取
        self.mcu.adc1.set_channel_voltage(self.adc_channel, vout)
        raw_adc = self.mcu.adc1.read_channel(self.adc_channel)
        measured_v = self.mcu.adc1.digital_to_voltage(raw_adc)
        
        # 从电压反推dB
        if measured_v > 0.01:
            normalized_back = measured_v / 3.3
            db_calculated = self.DB_OFFSET + normalized_back * self.DB_SCALE
        else:
            db_calculated = db
        
        # 添加随机波动模拟真实环境
        db_calculated += random.uniform(-1.5, 1.5)
        db_calculated = max(30.0, min(120.0, db_calculated))
        
        self.mcu.printf("Noise: %.1f dB (V=%.2f, ADC=%d)", 
                        db_calculated, measured_v, raw_adc)
        
        return round(db_calculated, 1)
    
    def __repr__(self):
        return f"NoiseSensor(ADC_CH{self.adc_channel})"
