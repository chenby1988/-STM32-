"""
虚拟MQ-135空气质量传感器驱动
模拟ADC读取和PPM计算

真实MQ-135参数：
- 检测气体: NH3, NOx, 酒精, 苯, 烟雾, CO2等
- 加热电压: 5V
- 负载电阻: 可调
- 输出: 模拟电压（通过ADC读取）
- 需预热: 20秒以上
"""

import math
import random
import time
from typing import Optional

from core.mcu import VirtualSTM32


class MQ135Driver:
    """MQ-135空气质量传感器驱动"""
    
    # 标准大气下的典型电阻比
    RLOAD = 10.0           # 负载电阻 kΩ
    RZERO_CLEAN_AIR = 76.63  # 清洁空气中传感器电阻 kΩ
    
    # CO2浓度计算公式参数
    PARA = 116.6020682
    PARB = 2.769034857
    
    def __init__(self, mcu: VirtualSTM32, adc_channel: int, calibration_r0: float = 10.0):
        self.mcu = mcu
        self.adc_channel = adc_channel
        self.calibration_r0 = calibration_r0
        
        # 当前真实环境值
        self._ppm = 400.0       # CO2等效PPM
        self._aqi = 50.0        # 空气质量指数
        
        # 预热状态
        self._preheat_start = time.time()
        self._preheated = False
        
        print(f"[MQ135] 驱动初始化，ADC通道{adc_channel}，校准R0={calibration_r0}kΩ")
        print(f"[MQ135] 开始预热，需要20秒...")
    
    def set_real_values(self, ppm: float, aqi: float):
        """设置真实环境空气质量值"""
        self._ppm = ppm
        self._aqi = aqi
    
    def _check_preheat(self) -> bool:
        """检查预热是否完成"""
        if self._preheated:
            return True
        elapsed = time.time() - self._preheat_start
        if elapsed >= 20:
            self._preheated = True
            self.mcu.printf("MQ135: 预热完成")
            return True
        return False
    
    def read(self) -> dict:
        """
        读取空气质量数据
        返回: {"ppm": float, "aqi": float, "voltage": float, "raw_adc": int}
        """
        if not self._check_preheat():
            self.mcu.printf("MQ135: 预热中...(%d/20s)", int(time.time() - self._preheat_start))
        
        # 将PPM转换为电压输出
        # RS/R0 = para * ppm^(-parb)
        ppm = max(10.0, self._ppm)  # 避免log(0)
        ratio = self.PARA * math.pow(ppm, -self.PARB)
        rs = ratio * self.calibration_r0
        
        # 分压公式: Vout = Vcc * RL / (RS + RL)
        vout = 3.3 * self.RLOAD / (rs + self.RLOAD)
        vout = max(0.0, min(3.3, vout))
        
        # 添加噪声
        vout += random.uniform(-0.02, 0.02)
        vout = max(0.0, min(3.3, vout))
        
        # 设置ADC通道电压
        self.mcu.adc1.set_channel_voltage(self.adc_channel, vout)
        raw_adc = self.mcu.adc1.read_channel(self.adc_channel)
        measured_v = self.mcu.adc1.digital_to_voltage(raw_adc)
        
        # 从测量电压反推PPM
        if measured_v > 0.1:
            rs_measured = self.RLOAD * (3.3 / measured_v - 1.0)
            if rs_measured > 0 and self.calibration_r0 > 0:
                ratio_measured = rs_measured / self.calibration_r0
                if ratio_measured > 0:
                    ppm_calculated = math.pow(self.PARA / ratio_measured, 1.0 / self.PARB)
                else:
                    ppm_calculated = ppm
            else:
                ppm_calculated = ppm
        else:
            ppm_calculated = ppm
        
        aqi = self._ppm_to_aqi(ppm_calculated)
        
        self.mcu.printf("MQ135: PPM=%.1f, AQI=%.1f, V=%.2fV, ADC=%d", 
                        ppm_calculated, aqi, measured_v, raw_adc)
        
        return {
            "ppm": round(ppm_calculated, 1),
            "aqi": round(aqi, 1),
            "voltage": round(measured_v, 3),
            "raw_adc": raw_adc,
            "preheated": self._preheated,
        }
    
    def _ppm_to_aqi(self, ppm: float) -> float:
        """将PPM转换为空气质量指数（简化计算）"""
        # 这是一个简化的AQI映射
        if ppm < 400:
            return 0.0 + (ppm - 0) * 50 / 400
        elif ppm < 800:
            return 50.0 + (ppm - 400) * 50 / 400
        elif ppm < 1200:
            return 100.0 + (ppm - 800) * 50 / 400
        elif ppm < 1600:
            return 150.0 + (ppm - 1200) * 50 / 400
        else:
            return 200.0 + (ppm - 1600) * 100 / 400
    
    def __repr__(self):
        return f"MQ135(ADC_CH{self.adc_channel})"
