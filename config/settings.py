"""
STM32 智能环境监测站 - 配置文件
模拟真实STM32项目中的 config.h / settings 文件
"""

import os

# ========== 项目路径 ==========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ========== 虚拟STM32配置 ==========
MCU_CONFIG = {
    "name": "STM32F103C8T6",           # 模拟STM32F103C8T6（最常见的开发板芯片）
    "clock_mhz": 72,                    # 主频72MHz
    "flash_kb": 64,                     # Flash 64KB
    "ram_kb": 20,                       # SRAM 20KB
    "adc_resolution": 12,               # ADC 12位分辨率
    "adc_vref": 3.3,                    # ADC参考电压3.3V
}

# ========== 传感器配置 ==========
SENSOR_CONFIG = {
    "dht11": {
        "enabled": True,
        "pin": "PA0",                  # 连接GPIOA Pin0
        "read_interval_ms": 2000,       # 读取间隔2秒（DHT11最快2秒）
        "simulate_noise": True,         # 模拟传感器噪声
    },
    "mq135": {
        "enabled": True,
        "adc_channel": 0,              # ADC通道0
        "read_interval_ms": 1000,       # 读取间隔1秒
        "calibration_r0": 10.0,         # 校准电阻值（kΩ）
    },
    "bh1750": {
        "enabled": True,
        "i2c_address": 0x23,           # I2C地址0x23
        "read_interval_ms": 1000,       # 读取间隔1秒
    },
    "noise": {
        "enabled": True,
        "adc_channel": 1,              # ADC通道1
        "read_interval_ms": 500,        # 读取间隔0.5秒
    },
    "bmp280": {
        "enabled": True,
        "i2c_address": 0x76,           # I2C地址0x76
        "read_interval_ms": 1000,       # 读取间隔1秒
    },
}

# ========== 告警阈值配置 ==========
ALARM_CONFIG = {
    "temperature": {"min": 10.0, "max": 35.0},   # 温度范围 10-35°C
    "humidity": {"min": 30.0, "max": 70.0},      # 湿度范围 30-70%
    "air_quality": {"max": 200.0},               # 空气质量指数 < 200
    "light": {"min": 50.0, "max": 10000.0},      # 光照范围 50-10000 lux
    "noise": {"max": 70.0},                      # 噪音 < 70 dB
    "pressure": {"min": 950.0, "max": 1050.0},   # 气压范围 950-1050 hPa
}

# ========== 数据采集配置 ==========
COLLECTOR_CONFIG = {
    "sample_interval_ms": 1000,        # 采样间隔1秒
    "buffer_size": 100,                # 环形缓冲区大小
    "save_interval_s": 10,             # 每10秒保存一次数据
}

# ========== Web服务器配置 ==========
WEB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": False,
}

# ========== 环境模拟配置（控制面板用）==========
ENV_SIMULATION = {
    "initial_temp": 25.0,              # 初始温度
    "initial_humidity": 50.0,          # 初始湿度
    "initial_air_quality": 80.0,       # 初始空气质量
    "initial_light": 300.0,            # 初始光照
    "initial_noise": 45.0,             # 初始噪音
    "initial_pressure": 1013.25,       # 初始气压（标准大气压）
    "change_rate": 0.5,                # 环境变化速率
}
