"""
Web服务器模块
使用Flask提供REST API和Web界面
模拟STM32通过ESP8266/WiFi模块上传数据到服务器
"""

import json
import os
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

from config.settings import WEB_CONFIG, BASE_DIR
from app.storage import DataStorage
from app.alarm import AlarmSystem


def create_app(storage: DataStorage, alarm: AlarmSystem, get_latest_data_func):
    """创建Flask应用"""
    
    template_dir = os.path.join(BASE_DIR, 'web', 'templates')
    static_dir = os.path.join(BASE_DIR, 'web', 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config['JSON_AS_ASCII'] = False
    
    @app.route('/')
    def index():
        """主页面"""
        return render_template('index.html')
    
    @app.route('/api/current')
    def api_current():
        """获取当前传感器数据"""
        data = get_latest_data_func()
        alarm_state = alarm.get_status_summary(data) if data else {}
        return jsonify({
            'success': True,
            'data': data,
            'alarm': alarm_state,
            'server_time': datetime.now().isoformat(),
        })
    
    @app.route('/api/history')
    def api_history():
        """获取历史数据"""
        limit = request.args.get('limit', 100, type=int)
        data = storage.get_recent_data(limit)
        return jsonify({
            'success': True,
            'data': data,
        })
    
    @app.route('/api/history/range')
    def api_history_range():
        """获取指定时间范围的数据"""
        start = request.args.get('start')
        end = request.args.get('end')
        if not start or not end:
            return jsonify({'success': False, 'error': '缺少start或end参数'}), 400
        data = storage.get_data_range(start, end)
        return jsonify({
            'success': True,
            'data': data,
        })
    
    @app.route('/api/statistics')
    def api_statistics():
        """获取统计信息"""
        hours = request.args.get('hours', 24, type=int)
        stats = storage.get_statistics(hours)
        return jsonify({
            'success': True,
            'statistics': stats,
        })
    
    @app.route('/api/alarms')
    def api_alarms():
        """获取告警记录"""
        limit = request.args.get('limit', 50, type=int)
        alarms = storage.get_recent_alarms(limit)
        return jsonify({
            'success': True,
            'alarms': alarms,
        })
    
    @app.route('/api/alarms/current')
    def api_current_alarms():
        """获取当前活跃告警"""
        data = get_latest_data_func()
        if data:
            alarms = alarm.check_all(data)
            return jsonify({
                'success': True,
                'alarms': alarms,
                'is_alarming': len(alarms) > 0,
            })
        return jsonify({'success': True, 'alarms': {}, 'is_alarming': False})
    
    return app


class WebServer:
    """Web服务器管理器"""
    
    def __init__(self, storage: DataStorage, alarm: AlarmSystem, 
                 get_latest_data_func, config=None):
        self.storage = storage
        self.alarm = alarm
        self.get_latest_data = get_latest_data_func
        self.config = config or WEB_CONFIG
        self.app = create_app(storage, alarm, get_latest_data_func)
        self._thread: threading.Thread = None
    
    def start(self):
        """启动Web服务器"""
        host = self.config['host']
        port = self.config['port']
        print(f"[WebServer] 启动中 http://{host}:{port}")
        self._thread = threading.Thread(
            target=self.app.run,
            kwargs={'host': host, 'port': port, 'debug': False, 'use_reloader': False},
            daemon=True
        )
        self._thread.start()
    
    def stop(self):
        """停止Web服务器（Flask开发服务器不易干净停止，这里只是记录）"""
        print("[WebServer] 服务器停止")
