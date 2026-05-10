"""
数据存储模块
模拟STM32中的数据存储逻辑，使用SQLite代替Flash/EEPROM
"""

import sqlite3
import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional

from config.settings import DATA_DIR


class DataStorage:
    """
    环境监测数据存储器
    使用SQLite数据库持久化存储传感器数据
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(DATA_DIR, "env_data.db")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 传感器数据主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    air_quality_ppm REAL,
                    air_quality_aqi REAL,
                    light_lux REAL,
                    noise_db REAL,
                    pressure_hpa REAL,
                    bmp280_temp REAL,
                    alarm_flags TEXT
                )
            ''')
            # 告警记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarm_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    alarm_type TEXT NOT NULL,
                    message TEXT
                )
            ''')
            # 系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            ''')
            conn.commit()
    
    def save_sensor_data(self, data: Dict) -> int:
        """
        保存一组传感器数据
        返回: 插入的记录ID
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sensor_data 
                    (timestamp, temperature, humidity, air_quality_ppm, air_quality_aqi, 
                     light_lux, noise_db, pressure_hpa, bmp280_temp, alarm_flags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    data.get('temperature'),
                    data.get('humidity'),
                    data.get('air_quality_ppm'),
                    data.get('air_quality_aqi'),
                    data.get('light_lux'),
                    data.get('noise_db'),
                    data.get('pressure_hpa'),
                    data.get('bmp280_temp'),
                    json.dumps(data.get('alarm_flags', {}))
                ))
                conn.commit()
                return cursor.lastrowid
    
    def get_recent_data(self, limit: int = 100) -> List[Dict]:
        """获取最近的传感器数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sensor_data 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d['alarm_flags'] = json.loads(d.get('alarm_flags', '{}'))
                result.append(d)
            return result
    
    def get_data_range(self, start_time: str, end_time: str) -> List[Dict]:
        """获取指定时间范围的数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sensor_data 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            ''', (start_time, end_time))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d['alarm_flags'] = json.loads(d.get('alarm_flags', '{}'))
                result.append(d)
            return result
    
    def save_alarm(self, sensor_type: str, value: float, threshold: float, 
                   alarm_type: str, message: str):
        """保存告警记录"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alarm_log 
                    (timestamp, sensor_type, value, threshold, alarm_type, message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    sensor_type, value, threshold, alarm_type, message
                ))
                conn.commit()
    
    def get_recent_alarms(self, limit: int = 50) -> List[Dict]:
        """获取最近的告警记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM alarm_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def log_system(self, level: str, message: str):
        """记录系统日志"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_log (timestamp, level, message)
                    VALUES (?, ?, ?)
                ''', (datetime.now().isoformat(), level, message))
                conn.commit()
    
    def get_statistics(self, hours: int = 24) -> Dict:
        """获取统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_records,
                    AVG(temperature) as avg_temp,
                    MIN(temperature) as min_temp,
                    MAX(temperature) as max_temp,
                    AVG(humidity) as avg_humidity,
                    AVG(air_quality_aqi) as avg_aqi,
                    AVG(light_lux) as avg_light,
                    AVG(noise_db) as avg_noise,
                    AVG(pressure_hpa) as avg_pressure
                FROM sensor_data 
                WHERE timestamp > datetime('now', ?)
            ''', (f'-{hours} hours',))
            row = cursor.fetchone()
            return {
                'total_records': row[0] or 0,
                'avg_temperature': round(row[1], 2) if row[1] else None,
                'min_temperature': round(row[2], 2) if row[2] else None,
                'max_temperature': round(row[3], 2) if row[3] else None,
                'avg_humidity': round(row[4], 2) if row[4] else None,
                'avg_aqi': round(row[5], 2) if row[5] else None,
                'avg_light': round(row[6], 2) if row[6] else None,
                'avg_noise': round(row[7], 2) if row[7] else None,
                'avg_pressure': round(row[8], 2) if row[8] else None,
            }
    
    def clear_old_data(self, days: int = 30):
        """清理旧数据"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM sensor_data 
                    WHERE timestamp < datetime('now', ?)
                ''', (f'-{days} days',))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
