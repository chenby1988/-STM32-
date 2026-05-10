"""
虚拟STM32外设模块
模拟 GPIO、ADC、I2C、UART、TIM 等外设行为
"""

import threading
import time
import random
from typing import Callable, Dict, List, Optional

from .memory import RegisterMap


class GPIO:
    """
    通用输入输出端口模拟
    STM32的GPIO有16个引脚（Pin0-Pin15），每个可配置为输入/输出
    """
    
    def __init__(self, name: str, reg_map: RegisterMap):
        self.name = name          # 如 "GPIOA"
        self._reg = reg_map
        self._pin_states = [0] * 16    # 16个引脚状态
        self._pin_modes = [0] * 16     # 16个引脚模式 (0=输入, 1=输出)
        self._callbacks: Dict[int, List[Callable]] = {i: [] for i in range(16)}
        self._lock = threading.Lock()
    
    def configure_pin(self, pin: int, mode: str):
        """配置引脚模式"""
        with self._lock:
            if not 0 <= pin <= 15:
                raise ValueError(f"引脚号必须在0-15之间")
            if mode == "input":
                self._pin_modes[pin] = 0
            elif mode == "output":
                self._pin_modes[pin] = 1
            else:
                raise ValueError(f"未知模式: {mode}")
    
    def write_pin(self, pin: int, value: int):
        """写入引脚电平 (0=低, 1=高)"""
        with self._lock:
            if self._pin_modes[pin] != 1:
                raise RuntimeError(f"[{self.name}] Pin{pin} 未配置为输出模式")
            self._pin_states[pin] = 1 if value else 0
            # 更新IDR和ODR寄存器
            self._update_registers()
            # 触发回调
            for cb in self._callbacks[pin]:
                cb(self._pin_states[pin])
    
    def read_pin(self, pin: int) -> int:
        """读取引脚电平"""
        with self._lock:
            return self._pin_states[pin]
    
    def toggle_pin(self, pin: int):
        """翻转引脚电平"""
        self.write_pin(pin, 1 - self.read_pin(pin))
    
    def register_callback(self, pin: int, callback: Callable):
        """注册引脚变化回调"""
        self._callbacks[pin].append(callback)
    
    def _update_registers(self):
        """同步内部状态到寄存器"""
        idr = sum((self._pin_states[i] << i) for i in range(16))
        odr = idr
        self._reg.write_reg(self.name, 'GPIO_IDR', idr, 2)
        self._reg.write_reg(self.name, 'GPIO_ODR', odr, 2)
    
    def __repr__(self):
        return f"GPIO({self.name})"


class ADC:
    """
    模数转换器模拟
    STM32F103有12位ADC，范围0-4095对应0-3.3V
    """
    
    def __init__(self, name: str, resolution: int, vref: float, reg_map: RegisterMap):
        self.name = name
        self.resolution = resolution       # 位数（如12）
        self.vref = vref                   # 参考电压
        self._reg = reg_map
        self._max_value = (1 << resolution) - 1
        self._channel_values: Dict[int, float] = {}  # 通道当前电压值
        self._enabled = False
        self._lock = threading.Lock()
    
    def enable(self):
        """使能ADC"""
        with self._lock:
            self._enabled = True
            self._reg.write_reg(self.name, 'ADC_CR2', 0x01)  # ADON=1
    
    def disable(self):
        """关闭ADC"""
        with self._lock:
            self._enabled = False
            self._reg.write_reg(self.name, 'ADC_CR2', 0x00)
    
    def set_channel_voltage(self, channel: int, voltage: float):
        """设置通道输入电压（模拟传感器接入）"""
        with self._lock:
            self._channel_values[channel] = max(0.0, min(voltage, self.vref))
    
    def read_channel(self, channel: int) -> int:
        """
        读取ADC通道值
        返回: 数字量 (0 ~ 2^resolution - 1)
        """
        with self._lock:
            if not self._enabled:
                raise RuntimeError(f"[{self.name}] ADC未使能")
            
            voltage = self._channel_values.get(channel, 0.0)
            # 添加一些随机噪声，模拟真实ADC的量化误差
            noise = random.uniform(-0.005, 0.005)
            voltage = max(0.0, min(voltage + noise, self.vref))
            
            digital_value = int((voltage / self.vref) * self._max_value)
            digital_value = max(0, min(digital_value, self._max_value))
            
            # 写入数据寄存器
            self._reg.write_reg(self.name, 'ADC_DR', digital_value, 2)
            # 设置EOC标志
            sr = self._reg.read_reg(self.name, 'ADC_SR', 2)
            self._reg.write_reg(self.name, 'ADC_SR', sr | 0x02, 2)
            
            return digital_value
    
    def voltage_to_digital(self, voltage: float) -> int:
        """电压转数字量"""
        return int((voltage / self.vref) * self._max_value)
    
    def digital_to_voltage(self, digital: int) -> float:
        """数字量转电压"""
        return (digital / self._max_value) * self.vref
    
    def __repr__(self):
        return f"ADC({self.name}, {self.resolution}bit, Vref={self.vref}V)"


class I2C:
    """
    I2C总线模拟
    支持主模式读写，模拟START、STOP、ACK等时序
    """
    
    def __init__(self, name: str, reg_map: RegisterMap):
        self.name = name
        self._reg = reg_map
        self._devices: Dict[int, 'I2CDevice'] = {}  # 地址 -> 设备
        self._enabled = False
        self._lock = threading.Lock()
    
    def enable(self):
        with self._lock:
            self._enabled = True
    
    def disable(self):
        with self._lock:
            self._enabled = False
    
    def attach_device(self, address: int, device: 'I2CDevice'):
        """挂载I2C从设备"""
        with self._lock:
            self._devices[address] = device
    
    def write(self, addr: int, data: bytes):
        """向从设备写入数据"""
        with self._lock:
            if not self._enabled:
                raise RuntimeError(f"[{self.name}] I2C未使能")
            if addr not in self._devices:
                raise RuntimeError(f"[{self.name}] I2C设备 0x{addr:02X} 未响应")
            self._devices[addr].on_receive(data)
    
    def read(self, addr: int, length: int) -> bytes:
        """从从设备读取数据"""
        with self._lock:
            if not self._enabled:
                raise RuntimeError(f"[{self.name}] I2C未使能")
            if addr not in self._devices:
                raise RuntimeError(f"[{self.name}] I2C设备 0x{addr:02X} 未响应")
            return self._devices[addr].on_request(length)
    
    def write_then_read(self, addr: int, write_data: bytes, read_length: int) -> bytes:
        """先写后读（常用于传感器读取）"""
        self.write(addr, write_data)
        return self.read(addr, read_length)
    
    def __repr__(self):
        return f"I2C({self.name})"


class I2CDevice:
    """I2C从设备基类"""
    
    def on_receive(self, data: bytes):
        """接收到数据时调用"""
        pass
    
    def on_request(self, length: int) -> bytes:
        """主设备请求数据时调用"""
        return bytes(length)


class UART:
    """
    串口通信模拟
    用于调试输出和数据上传
    """
    
    def __init__(self, name: str, baudrate: int = 115200):
        self.name = name
        self.baudrate = baudrate
        self._enabled = False
        self._tx_buffer = bytearray()
        self._rx_buffer = bytearray()
        self._callbacks: List[Callable[[bytes], None]] = []
        self._lock = threading.Lock()
    
    def enable(self):
        with self._lock:
            self._enabled = True
    
    def disable(self):
        with self._lock:
            self._enabled = False
    
    def send(self, data: bytes):
        """发送数据"""
        with self._lock:
            if not self._enabled:
                return
            self._tx_buffer.extend(data)
            for cb in self._callbacks:
                cb(data)
    
    def send_string(self, s: str):
        """发送字符串（自动加换行，模拟printf）"""
        self.send((s + "\r\n").encode('utf-8'))
    
    def receive(self, length: int = 1) -> bytes:
        """接收数据"""
        with self._lock:
            data = bytes(self._rx_buffer[:length])
            self._rx_buffer = self._rx_buffer[length:]
            return data
    
    def register_callback(self, callback: Callable[[bytes], None]):
        """注册接收回调"""
        self._callbacks.append(callback)
    
    def get_tx_log(self) -> str:
        """获取发送日志（用于调试）"""
        with self._lock:
            log = self._tx_buffer.decode('utf-8', errors='replace')
            self._tx_buffer.clear()
            return log
    
    def __repr__(self):
        return f"UART({self.name}, {self.baudrate}bps)"


class TIM:
    """
    定时器模拟
    产生周期性中断，模拟SysTick或通用定时器
    """
    
    def __init__(self, name: str, reg_map: RegisterMap):
        self.name = name
        self._reg = reg_map
        self._enabled = False
        self._period_ms = 1000
        self._callbacks: List[Callable] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
    
    def configure(self, period_ms: int):
        """配置定时周期（毫秒）"""
        with self._lock:
            self._period_ms = period_ms
            # 模拟写入ARR和PSC寄存器
            self._reg.write_reg(self.name, 'TIM_ARR', period_ms, 2)
    
    def start(self):
        """启动定时器"""
        with self._lock:
            if self._enabled:
                return
            self._enabled = True
            self._stop_event.clear()
            self._reg.write_reg(self.name, 'TIM_CR1', 0x01)  # CEN=1
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
    
    def stop(self):
        """停止定时器"""
        with self._lock:
            if not self._enabled:
                return
            self._enabled = False
            self._stop_event.set()
            self._reg.write_reg(self.name, 'TIM_CR1', 0x00)
            if self._thread:
                self._thread.join(timeout=1.0)
    
    def register_callback(self, callback: Callable):
        """注册定时回调"""
        self._callbacks.append(callback)
    
    def _run(self):
        """定时器线程"""
        while not self._stop_event.is_set():
            # 模拟计数器递增
            cnt = self._reg.read_reg(self.name, 'TIM_CNT', 2)
            self._reg.write_reg(self.name, 'TIM_CNT', cnt + 1, 2)
            
            # 触发回调
            for cb in self._callbacks:
                try:
                    cb()
                except Exception as e:
                    print(f"[{self.name}] 回调错误: {e}")
            
            self._stop_event.wait(self._period_ms / 1000.0)
    
    def __repr__(self):
        return f"TIM({self.name}, {self._period_ms}ms)"
