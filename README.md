# 🖥️ STM32 智能环境监测站（虚拟硬件模拟版）

> **无需任何硬件，在电脑上完整模拟 STM32F103C8T6 + 传感器阵列 的智能环境监测系统**

---

## 📋 项目概述

本项目是一个**纯软件模拟**的基于 STM32 的智能环境监测站，专为没有硬件的初学者设计。它完整模拟了：

- **STM32F103C8T6** MCU 核心（Flash、SRAM、寄存器、SysTick）
- **虚拟传感器**：DHT11（温湿度）、MQ-135（空气质量）、BH1750（光照）、噪音传感器、**BMP280（气压）**
- **虚拟外设**：GPIO、ADC、I2C、UART、定时器
- **Web 可视化面板**：实时数据、历史图表、告警提示
- **环境控制面板**：手动调整环境参数，测试告警功能

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动监测站

```bash
python main.py
```

启动成功后，在浏览器打开：

```
http://127.0.0.1:5000
```

### 3. （可选）启动环境控制面板

在**另一个终端窗口**中运行：

```bash
python control_panel.py
```

然后输入命令调整环境，例如：

```
control> set temp 40       # 设置温度40°C，触发高温告警
control> set humidity 20   # 设置湿度20%，触发低湿告警
control> set pressure 920  # 设置气压920hPa，触发低气压告警
control> status            # 查看当前环境状态
```

---

## 📁 项目结构

```
stm32_env_monitor/
├── core/                   # 虚拟STM32核心（模拟硬件层）
│   ├── mcu.py             # MCU主控制器
│   ├── memory.py          # Flash/SRAM/寄存器模拟
│   └── peripherals.py     # GPIO/ADC/I2C/UART/TIM外设
├── drivers/                # 虚拟传感器驱动（模拟HAL驱动层）
│   ├── dht11.py           # DHT11温湿度传感器
│   ├── mq135.py           # MQ-135空气质量传感器
│   ├── bh1750.py          # BH1750光照传感器
│   ├── noise.py           # 噪音传感器
│   └── bmp280.py          # BMP280气压传感器
├── app/                    # 应用层（业务逻辑）
│   ├── collector.py       # 数据采集器（模拟main循环）
│   ├── storage.py         # SQLite数据持久化
│   └── alarm.py           # 告警系统
├── web/                    # Web可视化界面
│   ├── server.py          # Flask服务器
│   ├── templates/
│   │   └── index.html     # 前端页面
│   └── static/
│       └── style.css      # 样式
├── config/
│   └── settings.py        # 系统配置（模拟config.h）
├── main.py                 # 程序入口（模拟main.c）
├── control_panel.py        # 环境控制面板
└── requirements.txt
```

---

## 🧩 核心模块详解

### 1. 虚拟STM32核心 (`core/`)

| 模块 | 说明 |
|------|------|
| `VirtualSTM32` | 模拟STM32F103C8T6，含72MHz主频、64KB Flash、20KB SRAM |
| `MemoryRegion` | 模拟内存区域，支持8/16/32位读写（小端模式） |
| `RegisterMap` | 模拟外设寄存器映射（GPIOA/B/C、ADC1、TIM2/3等） |
| `GPIO` | 16引脚GPIO，支持输入/输出/翻转/回调 |
| `ADC` | 12位ADC，模拟量化噪声 |
| `I2C` | I2C主模式，支持挂载虚拟从设备 |
| `UART` | 串口通信，模拟printf调试输出 |
| `TIM` | 定时器，产生周期性中断回调 |

### 2. 传感器驱动 (`drivers/`)

| 传感器 | 接口 | 测量范围 | 特性 |
|--------|------|----------|------|
| DHT11 | GPIO单总线 | 0~50°C, 20~90%RH | 2秒最小采样间隔，模拟启动时序 |
| MQ-135 | ADC通道0 | 0~1000+ PPM | 20秒预热，模拟加热响应 |
| BH1750 | I2C (0x23) | 1~65535 lux | 支持连续/单次测量模式 |
| 噪音 | ADC通道1 | 30~120 dB | 模拟麦克风分压输出 |
| **BMP280** | **I2C (0x76)** | **300~1100 hPa** | **芯片ID验证，24位ADC，温度补偿** |

### 3. Web界面功能

- **实时数据卡片**：6个传感器的大字显示，告警时红色闪烁
- **趋势图表**：温湿度曲线、AQI与光照曲线（自动更新）
- **告警面板**：实时显示越限告警
- **统计数据**：24小时平均值、记录数
- **历史查询**：REST API 支持按时间范围查询

---

## ⚙️ 配置说明

编辑 `config/settings.py` 可调整：

```python
# MCU配置
MCU_CONFIG = {
    "name": "STM32F103C8T6",
    "clock_mhz": 72,
    "flash_kb": 64,
    "ram_kb": 20,
}

# 告警阈值
ALARM_CONFIG = {
    "temperature": {"min": 10.0, "max": 35.0},
    "humidity": {"min": 30.0, "max": 70.0},
    "air_quality": {"max": 200.0},
    "light": {"min": 50.0, "max": 10000.0},
    "noise": {"max": 70.0},
    "pressure": {"min": 950.0, "max": 1050.0},
}

# Web端口
WEB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
}
```

---

## 🛠️ 技术栈

- **Python 3.8+**：主程序语言
- **Flask**：Web服务器与REST API
- **SQLite**：数据持久化（替代Flash存储）
- **Chart.js**：前端实时图表
- **原生HTML/CSS**：响应式暗色主题UI

---

## 📚 学习路径建议

作为STM32小白，你可以按以下顺序学习：

1. **理解硬件模拟**：阅读 `core/` 目录，了解STM32的基本组成
2. **看懂传感器驱动**：阅读 `drivers/` 目录，学习各传感器的通信协议
3. **理解采集流程**：阅读 `app/collector.py`，理解 `while(1)` 主循环
4. **尝试修改配置**：调整 `config/settings.py` 中的告警阈值
5. **添加新传感器**：参照现有驱动，模拟一个新的虚拟传感器
6. **了解真实硬件**：在理解软件模拟后，购买真实的STM32开发板和传感器，将软件逻辑迁移到真机上

---

## 📡 API接口

| 接口 | 说明 |
|------|------|
| `GET /` | Web主页面 |
| `GET /api/current` | 当前传感器数据 + 告警状态 |
| `GET /api/history?limit=100` | 最近N条历史数据 |
| `GET /api/history/range?start=...&end=...` | 时间范围查询 |
| `GET /api/statistics?hours=24` | 统计信息 |
| `GET /api/alarms?limit=50` | 告警记录 |

---

## 📝 注意事项

1. **Flask开发服务器**：本项目使用Flask内置服务器，仅用于学习和演示。生产环境请使用Gunicorn/uWSGI。
2. **数据存储**：SQLite数据库位于 `data/env_data.db`，可定期清理。
3. **虚拟传感器噪声**：所有传感器都模拟了真实噪声，数值会有轻微波动。
4. **MQ-135预热**：模拟真实传感器的20秒预热时间，预热期间数据可能不稳定。

---

## 🔮 未来可扩展

- [x] 添加更多虚拟传感器（气压、PM2.5、CO2等）
- [ ] 模拟ESP8266 WiFi模块，实现MQTT上传
- [ ] 添加用户登录和数据权限管理
- [ ] 模拟低功耗模式（Stop/Standby）
- [ ] 导出CSV/Excel数据报表
- [ ] 模拟FreeRTOS多任务调度

---

**Happy Coding! 🎉**
