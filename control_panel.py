"""
环境控制面板
用于手动控制模拟环境的各项参数，测试告警功能

运行方式（在另一个终端中）:
    python control_panel.py

功能:
    交互式命令行，可以实时调整：
    - 温度
    - 湿度
    - 空气质量
    - 光照强度
    - 环境噪音
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    print("=" * 50)
    print("  🎛️  环境控制面板")
    print("=" * 50)
    print()
    print("  命令格式: set <参数> <值>")
    print()
    print("  可用参数:")
    print("    temp         - 温度 (°C)        范围: -10 ~ 50")
    print("    humidity     - 湿度 (%)         范围: 10 ~ 95")
    print("    air_quality  - 空气质量 (AQI)   范围: 0 ~ 1000")
    print("    light        - 光照 (lux)       范围: 0 ~ 50000")
    print("    noise        - 噪音 (dB)        范围: 20 ~ 100")
    print("    pressure     - 气压 (hPa)       范围: 900 ~ 1100")
    print()
    print("  示例:")
    print("    set temp 40        (设置温度为40°C，触发高温告警)")
    print("    set humidity 20    (设置湿度为20%，触发低湿告警)")
    print()
    print("  其他命令:")
    print("    status  - 查看当前环境状态")
    print("    help    - 显示帮助")
    print("    quit    - 退出")
    print()
    print("=" * 50)


def main():
    print_banner()
    
    # 当前环境值（与main.py中的模拟器同步）
    # 注意: 由于两个进程独立运行，这里通过简单的共享文件方式通信
    env_file = os.path.join(os.path.dirname(__file__), 'data', 'env_control.txt')
    os.makedirs(os.path.dirname(env_file), exist_ok=True)
    
    # 写入初始值
    with open(env_file, 'w') as f:
        f.write("temp=25.0\n")
        f.write("humidity=50.0\n")
        f.write("air_quality=80.0\n")
        f.write("light=300.0\n")
        f.write("noise=45.0\n")
        f.write("pressure=1013.25\n")
    
    def read_env():
        env = {}
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        env[k] = float(v)
        except Exception:
            pass
        return env
    
    def write_env(env):
        with open(env_file, 'w') as f:
            for k, v in env.items():
                f.write(f"{k}={v}\n")
    
    def show_status():
        env = read_env()
        print()
        print("  当前环境参数:")
        print(f"    🌡️  温度:      {env.get('temp', 25):.1f} °C")
        print(f"    💧 湿度:      {env.get('humidity', 50):.1f} %")
        print(f"    🌫️  空气质量:  {env.get('air_quality', 80):.1f} AQI")
        print(f"    ☀️  光照:      {env.get('light', 300):.1f} lux")
        print(f"    🔊 噪音:      {env.get('noise', 45):.1f} dB")
        print(f"    🌡️  气压:      {env.get('pressure', 1013.25):.1f} hPa")
        print()
    
    show_status()
    
    while True:
        try:
            cmd = input("control> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        
        if not cmd:
            continue
        
        parts = cmd.split()
        
        if cmd == 'quit' or cmd == 'exit':
            print("再见!")
            break
        
        elif cmd == 'help':
            print_banner()
        
        elif cmd == 'status':
            show_status()
        
        elif parts[0] == 'set' and len(parts) == 3:
            param = parts[1]
            try:
                value = float(parts[2])
            except ValueError:
                print("  ❌ 值必须是数字")
                continue
            
            valid_params = ['temp', 'humidity', 'air_quality', 'light', 'noise', 'pressure']
            if param not in valid_params:
                print(f"  ❌ 未知参数: {param}")
                continue
            
            env = read_env()
            env[param] = value
            write_env(env)
            
            names = {
                'temp': '温度',
                'humidity': '湿度',
                'air_quality': '空气质量',
                'light': '光照',
                'noise': '噪音'
            }
            print(f"  ✅ {names[param]} 已设置为 {value}")
            
            # 提示可能的告警
            if param == 'temp' and value > 35:
                print("  ⚠️  温度过高，将触发高温告警!")
            elif param == 'temp' and value < 10:
                print("  ⚠️  温度过低，将触发低温告警!")
            elif param == 'humidity' and value > 70:
                print("  ⚠️  湿度过高，将触发高湿告警!")
            elif param == 'humidity' and value < 30:
                print("  ⚠️  湿度过低，将触发低湿告警!")
            elif param == 'air_quality' and value > 200:
                print("  ⚠️  空气质量差，将触发AQI告警!")
            elif param == 'noise' and value > 70:
                print("  ⚠️  噪音过大，将触发噪音告警!")
            elif param == 'pressure' and (value < 950 or value > 1050):
                print("  ⚠️  气压异常，将触发气压告警!")
        
        else:
            print("  ❌ 未知命令，输入 help 查看帮助")


if __name__ == "__main__":
    main()
