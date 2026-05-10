"""
虚拟BH1750光照传感器驱动
模拟I2C通信读取光照强度

真实BH1750参数：
- 测量范围: 1~65535 lux
- 分辨率: 1 lux
- 供电: 3.3V/5V
- 接口: I2C
- 地址: 0x23(ADDR=GND) 或 0x5C(ADDR=VCC)
"""

import random
import struct
from core.mcu import VirtualSTM32
from core.peripherals import I2CDevice


class BH1750Device(I2CDevice):
    """虚拟BH1750 I2C设备"""
    
    # 命令码
    CMD_POWER_DOWN = 0x00
    CMD_POWER_ON = 0x01
    CMD_RESET = 0x07
    CMD_CONT_HRES = 0x10    # 连续高分辨率模式（1 lux分辨率）
    CMD_CONT_HRES2 = 0x11   # 连续高分辨率模式2（0.5 lux分辨率）
    CMD_CONT_LRES = 0x13    # 连续低分辨率模式（4 lux分辨率）
    CMD_OT_HRES = 0x20      # 一次性高分辨率
    CMD_OT_HRES2 = 0x21
    CMD_OT_LRES = 0x23
    
    def __init__(self):
        self.powered_on = False
        self.mode = self.CMD_CONT_HRES
        self._lux = 300.0
        self._command_buffer = bytearray()
    
    def set_lux(self, lux: float):
        """设置真实光照值"""
        self._lux = lux
    
    def on_receive(self, data: bytes):
        """处理主设备发来的命令"""
        if not data:
            return
        cmd = data[0]
        if cmd == self.CMD_POWER_ON:
            self.powered_on = True
        elif cmd == self.CMD_POWER_DOWN:
            self.powered_on = False
        elif cmd == self.CMD_RESET:
            self._lux = 300.0
        elif cmd in (self.CMD_CONT_HRES, self.CMD_CONT_HRES2, 
                     self.CMD_CONT_LRES, self.CMD_OT_HRES,
                     self.CMD_OT_HRES2, self.CMD_OT_LRES):
            self.mode = cmd
    
    def on_request(self, length: int) -> bytes:
        """响应主设备的数据请求"""
        if not self.powered_on:
            return bytes(length)
        
        # 添加传感器噪声
        lux = self._lux + random.uniform(-2.0, 2.0)
        lux = max(1.0, min(65535.0, lux))
        
        # BH1750数据格式: 2字节，高字节在前
        # 公式: data = lux * 1.2 (在HRES模式下)
        raw = int(lux / 1.2)
        raw = max(0, min(65535, raw))
        
        return struct.pack('>H', raw)


class BH1750Driver:
    """BH1750光照传感器驱动"""
    
    def __init__(self, mcu: VirtualSTM32, i2c_address: int = 0x23):
        self.mcu = mcu
        self.address = i2c_address
        
        # 创建虚拟设备并挂载到I2C总线
        self.device = BH1750Device()
        mcu.i2c1.attach_device(i2c_address, self.device)
        
        # 初始化
        mcu.i2c1.enable()
        self._init_sensor()
        
        print(f"[BH1750] 驱动初始化，I2C地址0x{i2c_address:02X}")
    
    def _init_sensor(self):
        """初始化传感器"""
        self.mcu.i2c1.write(self.address, bytes([BH1750Device.CMD_POWER_ON]))
        self.mcu.delay_ms(10)
        self.mcu.i2c1.write(self.address, bytes([BH1750Device.CMD_RESET]))
        self.mcu.delay_ms(10)
        self.mcu.i2c1.write(self.address, bytes([BH1750Device.CMD_CONT_HRES]))
        self.mcu.delay_ms(180)  # 高分辨率模式测量时间
    
    def set_real_values(self, lux: float):
        """设置真实光照值"""
        self.device.set_lux(lux)
    
    def read(self) -> float:
        """读取光照强度 (lux)"""
        data = self.mcu.i2c1.read(self.address, 2)
        if len(data) == 2:
            raw = (data[0] << 8) | data[1]
            lux = raw * 1.2
            lux += random.uniform(-1.0, 1.0)
            lux = max(1.0, min(65535.0, lux))
            self.mcu.printf("BH1750: %.1f lux (raw=%d)", lux, raw)
            return round(lux, 1)
        return 0.0
    
    def __repr__(self):
        return f"BH1750(0x{self.address:02X})"
