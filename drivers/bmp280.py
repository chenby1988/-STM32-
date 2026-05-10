"""
虚拟BMP280气压/温度传感器驱动
模拟I2C通信读取气压值

真实BMP280参数：
- 气压测量范围: 300 ~ 1100 hPa
- 绝对精度: ±1 hPa
- 相对精度: ±0.12 hPa
- 温度测量范围: -40 ~ 85°C（用于气压补偿）
- 接口: I2C / SPI
- I2C地址: 0x76(SDO=GND) 或 0x77(SDO=VCC)
- 数据输出: 24位ADC原始值，需通过校准系数转换
"""

import random
import struct
from core.mcu import VirtualSTM32
from core.peripherals import I2CDevice


class BMP280Device(I2CDevice):
    """虚拟BMP280 I2C设备"""
    
    # BMP280寄存器地址
    REG_ID = 0xD0          # 芯片ID (应为0x58)
    REG_RESET = 0xE0       # 软复位
    REG_STATUS = 0xF3      # 状态寄存器
    REG_CTRL_MEAS = 0xF4   # 测量控制
    REG_CONFIG = 0xF5      # 配置寄存器
    REG_PRESS_MSB = 0xF7   # 气压数据MSB
    REG_TEMP_MSB = 0xFA    # 温度数据MSB
    REG_CALIB_START = 0x88 # 校准数据起始地址
    
    # 芯片ID
    CHIP_ID = 0x58
    
    # 软复位命令
    CMD_RESET = 0xB6
    
    def __init__(self):
        self._pressure_hpa = 1013.25  # 标准大气压
        self._temperature = 25.0
        self._chip_id = self.CHIP_ID
        self._calibrated = True
        
        # 模拟校准系数（真实BMP280有26字节校准数据）
        self._dig_T1 = 27504
        self._dig_T2 = 26435
        self._dig_T3 = -1000
        self._dig_P1 = 36477
        self._dig_P2 = -10685
        self._dig_P3 = 3024
        self._dig_P4 = 2855
        self._dig_P5 = 140
        self._dig_P6 = -7
        self._dig_P7 = 15500
        self._dig_P8 = -14600
        self._dig_P9 = 6000
    
    def set_pressure(self, hpa: float):
        """设置真实气压值"""
        self._pressure_hpa = max(300.0, min(1100.0, hpa))
    
    def on_receive(self, data: bytes):
        """处理主设备发来的命令"""
        if len(data) < 1:
            return
        reg = data[0]
        
        if reg == self.REG_RESET and len(data) > 1 and data[1] == self.CMD_RESET:
            # 软复位
            self._calibrated = True
        elif reg == self.REG_CTRL_MEAS and len(data) > 1:
            # 设置测量模式
            pass
    
    def on_request(self, length: int) -> bytes:
        """响应主设备的数据请求"""
        # 添加传感器噪声
        pressure = self._pressure_hpa + random.uniform(-0.2, 0.2)
        temp = self._temperature + random.uniform(-0.1, 0.1)
        
        # 模拟BMP280的24位ADC原始值输出
        # 简化计算：将气压映射到原始ADC值
        # 真实BMP280有更复杂的补偿公式
        press_raw = int((pressure / 1013.25) * 415148)
        temp_raw = int((temp + 40) * 1000)
        
        # 返回3字节MSB/LSB/XLSB格式
        if length == 1:
            return bytes([self._chip_id])
        elif length == 3:
            # 气压数据
            return struct.pack('>I', press_raw << 4)[1:4]
        elif length == 6:
            # 气压+温度
            p_bytes = struct.pack('>I', press_raw << 4)[1:4]
            t_bytes = struct.pack('>I', temp_raw << 4)[1:4]
            return p_bytes + t_bytes
        
        return bytes(length)


class BMP280Driver:
    """BMP280气压传感器驱动"""
    
    def __init__(self, mcu: VirtualSTM32, i2c_address: int = 0x76):
        self.mcu = mcu
        self.address = i2c_address
        
        # 创建虚拟设备并挂载到I2C总线
        self.device = BMP280Device()
        mcu.i2c1.attach_device(i2c_address, self.device)
        
        # 初始化
        self._init_sensor()
        
        print(f"[BMP280] 驱动初始化，I2C地址0x{i2c_address:02X}")
    
    def _init_sensor(self):
        """初始化传感器"""
        # 读取芯片ID（验证通信）
        chip_id = self.mcu.i2c1.read(self.address, 1)
        if chip_id and chip_id[0] == BMP280Device.CHIP_ID:
            self.mcu.printf("BMP280: 芯片ID验证通过 0x%02X", chip_id[0])
        else:
            self.mcu.printf("BMP280: 芯片ID异常")
        
        # 软复位
        self.mcu.i2c1.write(self.address, bytes([BMP280Device.REG_RESET, BMP280Device.CMD_RESET]))
        self.mcu.delay_ms(10)
        
        # 配置测量模式：温度过采样x1，气压过采样x1，正常模式
        self.mcu.i2c1.write(self.address, bytes([BMP280Device.REG_CTRL_MEAS, 0x27]))
        self.mcu.delay_ms(10)
    
    def set_real_values(self, pressure: float, temperature: float = 25.0):
        """设置真实气压值"""
        self.device.set_pressure(pressure)
        self.device._temperature = temperature
    
    def read(self) -> dict:
        """
        读取气压和温度
        返回: {"pressure": float(hPa), "temperature": float(°C)}
        """
        # 读取6字节数据（气压3字节 + 温度3字节）
        data = self.mcu.i2c1.read(self.address, 6)
        
        if len(data) == 6:
            # 解析24位原始数据
            press_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
            temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
            
            # 简化补偿计算（真实BMP280有更复杂的公式）
            # 这里直接将原始值映射回真实物理量
            pressure = (press_raw / 415148.0) * 1013.25
            temperature = (temp_raw / 1000.0) - 40.0
            
            # 添加随机噪声
            pressure += random.uniform(-0.3, 0.3)
            temperature += random.uniform(-0.2, 0.2)
            
            pressure = max(300.0, min(1100.0, pressure))
            temperature = max(-40.0, min(85.0, temperature))
            
            self.mcu.printf("BMP280: P=%.2f hPa, T=%.1f°C (raw_p=%d, raw_t=%d)",
                            pressure, temperature, press_raw, temp_raw)
            
            return {
                "pressure": round(pressure, 2),
                "temperature": round(temperature, 1),
            }
        
        # 简化模式：直接返回模拟值
        pressure = self.device._pressure_hpa + random.uniform(-0.3, 0.3)
        pressure = max(300.0, min(1100.0, pressure))
        
        self.mcu.printf("BMP280: P=%.2f hPa (简化模式)", pressure)
        return {"pressure": round(pressure, 2)}
    
    def __repr__(self):
        return f"BMP280(0x{self.address:02X})"
