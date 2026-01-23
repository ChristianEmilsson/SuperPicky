#!/usr/bin/env python3
"""
SuperPicky BirdID 服务器管理器
管理 API 服务器的生命周期：启动、停止、状态检查
支持守护进程模式，使服务器可以独立于 GUI 运行

V4.0.0 修复：打包模式下使用线程方式启动，避免重复启动整个应用
"""

import os
import sys
import signal
import socket
import subprocess
import time
import json
import threading

# V4.2.1: I18n support
from i18n import get_i18n

def get_t():
    """Get translator function"""
    try:
        # Try to get language from config file if possible, or default
        # For server manager, we might just default to system locale or english if config not loaded
        # But get_i18n handles defaults.
        return get_i18n().t
    except Exception:
        # Fallback if core module not found (e.g. running check script standalone without path)
        return lambda k, **kw: k

# PID 文件位置
def get_pid_file_path():
    """获取 PID 文件路径"""
    if sys.platform == 'darwin':
        pid_dir = os.path.expanduser('~/Library/Application Support/SuperPicky')
    else:
        pid_dir = os.path.expanduser('~/.superpicky')
    os.makedirs(pid_dir, exist_ok=True)
    return os.path.join(pid_dir, 'birdid_server.pid')


def get_server_script_path():
    """获取服务器脚本路径"""
    # 支持开发模式和打包模式
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'birdid_server.py')


def is_port_in_use(port, host='127.0.0.1'):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


def check_server_health(port=5156, host='127.0.0.1', timeout=2):
    """检查服务器健康状态"""
    try:
        import urllib.request
        url = f'http://{host}:{port}/health'
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('status') == 'ok'
    except Exception:
        pass
    return False


def read_pid():
    """读取 PID 文件"""
    pid_file = get_pid_file_path()
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            pass
    return None


def write_pid(pid):
    """写入 PID 文件"""
    pid_file = get_pid_file_path()
    with open(pid_file, 'w') as f:
        f.write(str(pid))


def remove_pid():
    """删除 PID 文件"""
    pid_file = get_pid_file_path()
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except OSError:
            pass


def is_process_running(pid):
    """检查进程是否存在"""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)  # 发送信号 0 检查进程是否存在
        return True
    except (OSError, ProcessLookupError):
        return False


def get_server_status(port=5156):
    """
    获取服务器状态
    
    Returns:
        dict: {
            'running': bool,
            'pid': int or None,
            'healthy': bool,
            'port': int
        }
    """
    pid = read_pid()
    process_running = is_process_running(pid)
    port_in_use = is_port_in_use(port)
    healthy = check_server_health(port)
    
    return {
        'running': process_running or port_in_use,
        'pid': pid if process_running else None,
        'healthy': healthy,
        'port': port
    }


# 全局变量：跟踪线程模式的服务器
_server_thread = None
_server_instance = None


def start_server_thread(port=5156, log_callback=None):
    """
    在线程中启动服务器（用于打包模式）
    
    Args:
        port: 监听端口
        log_callback: 日志回调函数
        
    Returns:
        tuple: (success: bool, message: str, thread: Thread or None)
    """
    global _server_thread, _server_instance
    
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)
    
    # 检查是否已经运行
    t = get_t()
    if check_server_health(port):
        log(t("server.server_already_running", port=port))
        return True, "Server already running", _server_thread
    
    try:
        # 导入服务器模块
        from birdid_server import app, ensure_models_loaded
        from werkzeug.serving import make_server
        
        log(t("server.packaged_mode_thread"))
        
        def run_server():
            global _server_instance
            try:
                # 预加载模型
                log(t("server.loading_models"))
                ensure_models_loaded()
                log(t("server.models_loaded"))
                
                # 创建并运行服务器
                _server_instance = make_server('127.0.0.1', port, app, threaded=True)
                log(t("server.server_started", port=port))
                _server_instance.serve_forever()
            except Exception as e:
                log(t("server.server_thread_error", error=e))
        
        # 创建并启动守护线程
        _server_thread = threading.Thread(target=run_server, daemon=True, name="BirdID-API-Server")
        _server_thread.start()
        
        # 等待服务器启动（最多 30 秒，因为模型加载需要时间）
        for i in range(60):
            time.sleep(0.5)
            if check_server_health(port):
                log(t("server.server_health_ok", port=port))
                return True, "Server start success", _server_thread
        
        log(t("server.server_timeout"))
        return True, "Server starting", _server_thread
        
    except Exception as e:
        log(t("server.thread_start_failed", error=e))
        import traceback
        traceback.print_exc()
        return False, str(e), None


def start_server_daemon(port=5156, log_callback=None):
    """
    启动服务器
    
    打包模式下使用线程方式启动（避免重复启动整个应用）
    开发模式下使用子进程方式启动
    
    Args:
        port: 监听端口
        log_callback: 日志回调函数
        
    Returns:
        tuple: (success: bool, message: str, pid: int or None)
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)
    
    # 检查是否已经运行
    t = get_t()
    status = get_server_status(port)
    if status['healthy']:
        log(t("server.server_already_running", port=port))
        return True, "Server already running", status['pid']
    
    # 如果端口被占用但不健康，可能是僵尸进程
    if status['running'] and not status['healthy']:
        log(t("server.zombie_process"))
        stop_server()
        time.sleep(1)
    
    # 检测运行模式
    is_frozen = getattr(sys, 'frozen', False)
    
    if is_frozen:
        # 打包模式：使用线程方式启动
        log(t("server.packaged_mode_detected"))
        success, message, thread = start_server_thread(port, log_callback)
        # 线程模式没有独立 PID，返回主进程 PID
        return success, message, os.getpid() if success else None
    else:
        # 开发模式：使用子进程方式启动
        log(t("server.dev_mode_subprocess"))
        return _start_server_subprocess(port, log_callback)


def _start_server_subprocess(port=5156, log_callback=None):
    """
    以子进程方式启动服务器（仅开发模式使用）
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)
    
    python_exe = sys.executable
    server_script = get_server_script_path()
    
    t = get_t()
    
    if not os.path.exists(server_script):
        return False, f"Server script not found: {server_script}", None
    
    cmd = [python_exe, server_script, '--port', str(port)]
    log(t("server.starting_daemon", cmd=' '.join(cmd)))
    
    try:
        # 以守护进程方式启动（分离子进程）
        if sys.platform == 'darwin':
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True
            )
        else:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS if sys.platform == 'win32' else 0,
                start_new_session=True if sys.platform != 'win32' else False
            )
        
        write_pid(process.pid)
        log(t("server.server_pid", pid=process.pid))
        
        # 等待服务器启动
        for i in range(10):
            time.sleep(0.5)
            if check_server_health(port):
                log(t("server.server_health_ok", port=port))
                return True, "Server start success", process.pid
        
        if is_process_running(process.pid):
            log(t("server.server_started_health_fail"))
            return True, "Server starting", process.pid
        else:
            log(t("server.server_process_exited"))
            remove_pid()
            return False, "服务器启动失败", None
            
    except Exception as e:
        log(t("server.start_failed", error=e))
        return False, str(e), None


def stop_server(log_callback=None):
    """
    停止服务器
    
    Returns:
        tuple: (success: bool, message: str)
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(msg)
    
    t = get_t()
    pid = read_pid()
    
    if pid and is_process_running(pid):
        log(t("server.stop_server", pid=pid))
        try:
            os.kill(pid, signal.SIGTERM)
            
            # 等待进程退出
            for i in range(10):
                time.sleep(0.3)
                if not is_process_running(pid):
                    break
            
            # 如果还没退出，强制终止
            if is_process_running(pid):
                log(t("server.force_kill"))
                os.kill(pid, signal.SIGKILL)
                time.sleep(0.5)
            
            remove_pid()
            log(t("server.server_stopped"))
            return True, "Server stopped"
            
        except (ProcessLookupError, PermissionError) as e:
            log(t("server.stop_failed", error=e))
            remove_pid()
            return False, str(e)
    else:
        # 清理可能的僵尸 PID 文件
        remove_pid()
        log(t("server.server_not_running"))
        return True, "Server not running"


def restart_server(port=5156, log_callback=None):
    """重启服务器"""
    stop_server(log_callback)
    time.sleep(1)
    return start_server_daemon(port, log_callback)


# 命令行入口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='BirdID 服务器管理器')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'],
                        help='操作: start/stop/restart/status')
    parser.add_argument('--port', type=int, default=5156, help='端口号')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        success, msg, pid = start_server_daemon(args.port)
        print(msg)
        sys.exit(0 if success else 1)
        
    elif args.action == 'stop':
        success, msg = stop_server()
        print(msg)
        sys.exit(0 if success else 1)
        
    elif args.action == 'restart':
        success, msg, pid = restart_server(args.port)
        print(msg)
        sys.exit(0 if success else 1)
        
    elif args.action == 'status':
        status = get_server_status(args.port)
        print(f"运行状态: {'运行中' if status['running'] else '未运行'}")
        print(f"健康状态: {'正常' if status['healthy'] else '异常'}")
        print(f"PID: {status['pid'] or 'N/A'}")
        print(f"端口: {status['port']}")
        sys.exit(0 if status['healthy'] else 1)
