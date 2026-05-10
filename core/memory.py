"""
虚拟STM32内存系统
模拟 Flash、SRAM 和寄存器映射
"""

import threading
import time


class MemoryRegion:
    """内存区域基类，模拟STM32的内存段"""
    
    def __init__(self, name: str, size_bytes: int, base_addr: int = 0):
        self.name = name
        self.size = size_bytes
        self.base_addr = base_addr
        self._data = bytearray(size_bytes)
        self._lock = threading.Lock()
    
    def read(self, addr: int, size: int = 1) -> bytes:
        """读取内存"""
        with self._lock:
            offset = addr - self.base_addr
            if offset < 0 or offset + size > self.size:
                raise MemoryError(f"[{self.name}] 地址越界: 0x{addr:08X}")
            return bytes(self._data[offset:offset + size])
    
    def write(self, addr: int, data: bytes):
        """写入内存"""
        with self._lock:
            offset = addr - self.base_addr
            if offset < 0 or offset + len(data) > self.size:
                raise MemoryError(f"[{self.name}] 地址越界: 0x{addr:08X}")
            self._data[offset:offset + len(data)] = data
    
    def read_u32(self, addr: int) -> int:
        """读取32位无符号整数（小端模式，符合ARM Cortex-M）"""
        data = self.read(addr, 4)
        return int.from_bytes(data, byteorder='little', signed=False)
    
    def write_u32(self, addr: int, value: int):
        """写入32位无符号整数（小端模式）"""
        self.write(addr, value.to_bytes(4, byteorder='little', signed=False))
    
    def read_u16(self, addr: int) -> int:
        """读取16位无符号整数"""
        data = self.read(addr, 2)
        return int.from_bytes(data, byteorder='little', signed=False)
    
    def write_u16(self, addr: int, value: int):
        """写入16位无符号整数"""
        self.write(addr, value.to_bytes(2, byteorder='little', signed=False))
    
    def read_u8(self, addr: int) -> int:
        """读取8位无符号整数"""
        data = self.read(addr, 1)
        return data[0]
    
    def write_u8(self, addr: int, value: int):
        """写入8位无符号整数"""
        self.write(addr, bytes([value]))
    
    def __repr__(self):
        return f"MemoryRegion({self.name}, {self.size} bytes @ 0x{self.base_addr:08X})"


class RegisterMap:
    """
    STM32寄存器映射
    模拟真实的寄存器地址映射，如GPIOA->ODR, ADC1->DR等
    """
    
    # 模拟STM32F103的主要外设基地址
    BASE_ADDRS = {
        'GPIOA': 0x40010800,
        'GPIOB': 0x40010C00,
        'GPIOC': 0x40011000,
        'ADC1':  0x40012400,
        'TIM2':  0x40000000,
        'TIM3':  0x40000400,
        'USART1': 0x40013800,
        'I2C1':  0x40005400,
        'SPI1':  0x40013000,
        'RCC':   0x40021000,
    }
    
    # 寄存器偏移量（简化模拟）
    REG_OFFSETS = {
        'GPIO_CRL':   0x00,   # 配置低寄存器
        'GPIO_CRH':   0x04,   # 配置高寄存器
        'GPIO_IDR':   0x08,   # 输入数据寄存器
        'GPIO_ODR':   0x0C,   # 输出数据寄存器
        'GPIO_BSRR':  0x10,   # 位设置/清除寄存器
        'GPIO_BRR':   0x14,   # 位清除寄存器
        'ADC_SR':     0x00,   # 状态寄存器
        'ADC_CR1':    0x04,   # 控制寄存器1
        'ADC_CR2':    0x08,   # 控制寄存器2
        'ADC_DR':     0x4C,   # 数据寄存器
        'TIM_CR1':    0x00,   # 控制寄存器1
        'TIM_SR':     0x10,   # 状态寄存器
        'TIM_CNT':    0x24,   # 计数器
        'TIM_PSC':    0x28,   # 预分频器
        'TIM_ARR':    0x2C,   # 自动重装载寄存器
    }
    
    def __init__(self):
        # 为每个外设创建寄存器存储区（每个外设256字节寄存器空间）
        self._regions = {}
        for name, base in self.BASE_ADDRS.items():
            self._regions[name] = MemoryRegion(f"REG_{name}", 256, base)
    
    def get_reg_addr(self, peripheral: str, reg_name: str) -> int:
        """获取寄存器绝对地址"""
        if peripheral not in self.BASE_ADDRS:
            raise KeyError(f"未知外设: {peripheral}")
        if reg_name not in self.REG_OFFSETS:
            raise KeyError(f"未知寄存器: {reg_name}")
        return self.BASE_ADDRS[peripheral] + self.REG_OFFSETS[reg_name]
    
    def read_reg(self, peripheral: str, reg_name: str, size: int = 4) -> int:
        """读取寄存器值"""
        addr = self.get_reg_addr(peripheral, reg_name)
        region = self._regions[peripheral]
        data = region.read(addr, size)
        return int.from_bytes(data, byteorder='little')
    
    def write_reg(self, peripheral: str, reg_name: str, value: int, size: int = 4):
        """写入寄存器值"""
        addr = self.get_reg_addr(peripheral, reg_name)
        region = self._regions[peripheral]
        region.write(addr, value.to_bytes(size, byteorder='little'))
    
    def __repr__(self):
        return f"RegisterMap(peripherals={list(self.BASE_ADDRS.keys())})"


class Flash(MemoryRegion):
    """Flash存储器（程序存储）"""
    def __init__(self, size_kb: int):
        super().__init__("Flash", size_kb * 1024, base_addr=0x08000000)


class SRAM(MemoryRegion):
    """SRAM静态随机存取存储器（数据存储）"""
    def __init__(self, size_kb: int):
        super().__init__("SRAM", size_kb * 1024, base_addr=0x20000000)
