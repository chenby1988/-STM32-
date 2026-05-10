"""
虚拟STM32 MCU主控制器
整合所有外设，模拟完整的STM32运行环境
"""

import time
import threading
from typing import Optional

from .memory import Flash, SRAM, RegisterMap
from .peripherals import GPIO, ADC, I2C, UART, TIM


class VirtualSTM32:
    """
    虚拟STM32F103 MCU
    模拟完整的芯片运行环境，包括：
    - Flash程序存储器
    - SRAM数据存储器
    - 寄存器映射
    - GPIO/ADC/I2C/UART/TIM外设
    - SysTick系统节拍
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config["name"]
        
        # 创建内存区域
        self.flash = Flash(config["flash_kb"])
        self.sram = SRAM(config["ram_kb"])
        self.registers = RegisterMap()
        
        # 创建外设
        self.gpioa = GPIO("GPIOA", self.registers)
        self.gpiob = GPIO("GPIOB", self.registers)
        self.gpioc = GPIO("GPIOC", self.registers)
        
        self.adc1 = ADC("ADC1", config["adc_resolution"], config["adc_vref"], self.registers)
        
        self.i2c1 = I2C("I2C1", self.registers)
        
        self.usart1 = UART("USART1", 115200)
        
        self.tim2 = TIM("TIM2", self.registers)
        self.tim3 = TIM("TIM3", self.registers)
        
        # 系统状态
        self._running = False
        self._start_time = 0.0
        self._sys_tick_ms = 0
        self._tick_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        print(f"[MCU] {self.name} 初始化完成")
        print(f"      Flash: {config['flash_kb']}KB, SRAM: {config['ram_kb']}KB")
        print(f"      主频: {config['clock_mhz']}MHz, ADC: {config['adc_resolution']}bit/{config['adc_vref']}V")
    
    def reset(self):
        """复位MCU"""
        with self._lock:
            self._sys_tick_ms = 0
            self._start_time = time.time()
            print(f"[MCU] 系统复位")
    
    def run(self):
        """启动MCU运行"""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._start_time = time.time()
            
            # 启动SysTick（1ms周期）
            self._tick_thread = threading.Thread(target=self._sys_tick, daemon=True)
            self._tick_thread.start()
            
            print(f"[MCU] 系统运行中...")
    
    def stop(self):
        """停止MCU"""
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._tick_thread.join(timeout=1.0)
            print(f"[MCU] 系统停止")
    
    def _sys_tick(self):
        """系统节拍（模拟SysTick定时器，1ms中断）"""
        while self._running:
            time.sleep(0.001)
            self._sys_tick_ms += 1
    
    def get_tick_ms(self) -> int:
        """获取系统运行毫秒数（模拟HAL_GetTick）"""
        return self._sys_tick_ms
    
    def delay_ms(self, ms: int):
        """阻塞延时（模拟HAL_Delay）"""
        if not self._running:
            # MCU未运行时，回退到普通sleep（用于传感器初始化阶段）
            time.sleep(ms / 1000.0)
            return
        target = self._sys_tick_ms + ms
        while self._sys_tick_ms < target:
            time.sleep(0.001)
    
    def get_uptime_s(self) -> float:
        """获取运行时间（秒）"""
        return time.time() - self._start_time
    
    def printf(self, fmt: str, *args):
        """模拟串口printf输出"""
        msg = fmt % args
        self.usart1.send_string(f"[STM32] {msg}")
        print(f"[USART1] {msg}")
    
    def __repr__(self):
        return f"VirtualSTM32({self.name}, tick={self._sys_tick_ms}ms)"
