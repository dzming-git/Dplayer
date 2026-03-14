# 管理后台独立Flask应用
from flask import Flask, render_template, request, jsonify, abort, send_file
import subprocess
import os
import sys
import signal
import psutil
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import sqlite3
import threading
import hashlib
import requests
import json
import time
import socket
from utils.network_optimize import optimize_flask_app
from utils.system_optimizer import optimize_system

# ========== 全局服务状态缓存 ==========

services_status_cache = {
    'services': [],
    'system': {},
    'last_update': 0
}
cache_lock = threading.Lock()
CACHE_INTERVAL = 2  # 缓存刷新间隔（秒）

# ========== 日志配置 ==========

LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 管理后台日志
admin_logger = logging.getLogger('admin')
admin_logger.setLevel(logging.INFO)
admin_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'admin.log'),
    maxBytes=10*1024*1024,
    backupCount=5,
    encoding='utf-8'
)
admin_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
admin_logger.addHandler(admin_handler)

# 初始化：确保日志文件存在
try:
    # 触发一次日志写入以创建文件
    admin_logger.info("管理后台日志初始化")
except Exception as e:
    print(f"创建日志文件失败: {e}")

# ========== 配置 ==========

# 使用绝对路径确保文件位置正确
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# 配置文件路径
CONFIG_FILE = os.path.join(BASEDIR, 'config', 'config.json')
MAIN_APP_PID_FILE = os.path.join(BASEDIR, 'instance', 'main_app.pid')
DB_FILE = os.path.join(BASEDIR, 'instance', 'dplayer.db')

# ========== 端口管理函数 ==========

def is_port_in_use(port):
    """检查指定端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result == 0
    except Exception as e:
        admin_logger.error(f"检查端口 {port} 占用状态失败: {e}")
        return False


def find_process_using_port(port):
    """查找占用指定端口的进程"""
    processes = []
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    admin_logger.warning(f"无法访问进程 {conn.pid}")
    except Exception as e:
        admin_logger.error(f"查找端口 {port} 的进程失败: {e}")
    return processes


def kill_process(process):
    """强制终止指定进程"""
    try:
        pid = process.pid
        name = process.name()
        process.terminate()  # 先尝试正常终止
        try:
            process.wait(timeout=5)
            admin_logger.info(f"成功终止进程 {name} (PID: {pid})")
            return True
        except psutil.TimeoutExpired:
            # 正常终止超时，强制杀死
            process.kill()
            process.wait(timeout=2)
            admin_logger.info(f"强制杀死进程 {name} (PID: {pid})")
            return True
    except psutil.NoSuchProcess:
        admin_logger.warning(f"进程已不存在")
        return True
    except psutil.AccessDenied:
        admin_logger.error(f"没有权限终止进程 (PID: {process.pid})")
        return False
    except Exception as e:
        admin_logger.error(f"终止进程失败: {e}")
        return False


def kill_all_processes_using_port(port):
    """强制终止占用指定端口的所有进程"""
    result = {
        'success': True,
        'killed_count': 0,
        'processes': []
    }
    processes = find_process_using_port(port)
    if not processes:
        admin_logger.info(f"端口 {port} 没有被占用")
        return result
    admin_logger.warning(f"端口 {port} 被 {len(processes)} 个进程占用")
    for proc in processes:
        proc_info = {
            'pid': proc.pid,
            'name': proc.name(),
            'status': 'failed'
        }
        if kill_process(proc):
            result['killed_count'] += 1
            proc_info['status'] = 'killed'
        result['processes'].append(proc_info)
    # 验证端口是否已释放
    if is_port_in_use(port):
        result['success'] = False
        admin_logger.error(f"端口 {port} 仍然被占用，可能有新进程启动")
    else:
        admin_logger.info(f"端口 {port} 已成功释放")
    return result


def ensure_port_available(port):
    """确保端口可用，如果被占用则强制释放"""
    if not is_port_in_use(port):
        admin_logger.info(f"端口 {port} 可用")
        return {
            'success': True,
            'action': 'none',
            'message': f'端口 {port} 可用'
        }
    admin_logger.warning(f"端口 {port} 被占用，正在强制释放...")
    result = kill_all_processes_using_port(port)
    result['action'] = 'killed'
    result['message'] = f'已终止 {result["killed_count"]} 个进程以释放端口 {port}'
    return result


# 读取配置
def load_config():
    """读取配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            admin_logger.warning(f"配置文件 {CONFIG_FILE} 不存在，使用默认配置")
            return {}
    except Exception as e:
        admin_logger.error(f"读取配置文件失败: {e}")
        return {}

# 全局配置
config = load_config()
ADMIN_PORT = config.get('ports', {}).get('admin_app', 8080)
MAIN_APP_PORT = config.get('ports', {}).get('main_app', 8081)  # 改为8081避免需要管理员权限
HOST = config.get('host', '0.0.0.0')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin-secret-key-change-in-production'


# 优化网络连接配置，解决局域网访问偶现失败问题
# try:
#     optimize_flask_app(app)
#     admin_logger.info('网络连接优化已启用')
# except Exception as e:
#     admin_logger.warning(f'网络优化失败: {e}')

# 配置数据库
# 注意：admin_app使用原生SQL查询，不使用SQLAlchemy ORM
# 这是为了避免与app.py的SQLAlchemy实例冲突




# ========== 应用管理功能 ==========

def get_main_app_pid():
    """获取主应用进程ID"""
    try:
        if os.path.exists(MAIN_APP_PID_FILE):
            with open(MAIN_APP_PID_FILE, 'r') as f:
                pid = int(f.read().strip())
                # 检查进程是否还在运行
                if psutil.pid_exists(pid):
                    return pid
                else:
                    # 进程不存在，删除PID文件
                    os.remove(MAIN_APP_PID_FILE)
                    return None
        return None
    except Exception as e:
        admin_logger.error(f"获取主应用PID失败: {e}")
        return None


def start_main_app():
    """启动主应用"""
    try:
        # 检查是否已经运行
        pid = get_main_app_pid()
        if pid:
            admin_logger.warning(f"主应用已在运行 (PID: {pid})")
            return {'success': False, 'message': f'主应用已在运行 (PID: {pid})'}

        # 检查端口是否被占用
        if is_port_in_use(MAIN_APP_PORT):
            admin_logger.warning(f"端口 {MAIN_APP_PORT} 已被占用")
            return {'success': False, 'message': f'端口 {MAIN_APP_PORT} 已被占用'}

        # 启动主应用
        admin_logger.info("启动主应用...")

        # 创建日志文件
        service_log_file = os.path.join(LOG_DIR, 'main_startup.log')
        with open(service_log_file, 'w', encoding='utf-8') as log_file:
            log_file.write(f"=== 启动服务: 主应用 ===\n")
            log_file.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"脚本: app.py\n")
            log_file.write(f"端口: {MAIN_APP_PORT}\n")
            log_file.write(f"工作目录: {BASEDIR}\n\n")

        # 打开日志文件用于写入子进程输出
        stdout_file = open(os.path.join(LOG_DIR, 'main_stdout.log'), 'w', encoding='utf-8')
        stderr_file = open(os.path.join(LOG_DIR, 'main_stderr.log'), 'w', encoding='utf-8')

        process = subprocess.Popen(
            [sys.executable, os.path.join(BASEDIR, 'app.py')],
            cwd=BASEDIR,
            stdout=stdout_file,
            stderr=stderr_file,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )

        # 立即关闭文件句柄,让子进程自己管理
        stdout_file.close()
        stderr_file.close()

        # 保存PID
        with open(MAIN_APP_PID_FILE, 'w') as f:
            f.write(str(process.pid))

        admin_logger.info(f"主应用进程已启动 (PID: {process.pid})")

        # 等待端口就绪（最多10秒）
        for i in range(20):
            time.sleep(0.5)
            if is_port_in_use(MAIN_APP_PORT):
                admin_logger.info(f"主应用启动成功 (PID: {process.pid}, 端口: {MAIN_APP_PORT})")
                return {'success': True, 'message': f'主应用启动成功', 'pid': process.pid}

        # 端口未就绪，检查进程状态
        if not psutil.pid_exists(process.pid):
            admin_logger.error(f"主应用进程已退出 (PID: {process.pid})")
            # 读取错误日志
            stderr_log = os.path.join(LOG_DIR, 'main_stderr.log')
            if os.path.exists(stderr_log):
                with open(stderr_log, 'r', encoding='utf-8') as f:
                    error_content = f.read()
                    admin_logger.error(f"启动错误日志:\n{error_content}")
            return {'success': False, 'message': f'主应用启动失败，进程已退出(查看日志: logs/main_stderr.log)'}
        else:
            admin_logger.info(f"主应用进程存在但端口未就绪 (PID: {process.pid})")
            return {'success': True, 'message': f'主应用进程已启动，等待端口就绪', 'pid': process.pid}

    except Exception as e:
        admin_logger.error(f"启动主应用失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


def stop_main_app():
    """停止主应用"""
    try:
        pid = get_main_app_pid()
        if not pid:
            admin_logger.warning("主应用未运行")
            return {'success': False, 'message': '主应用未运行'}

        # 尝试优雅关闭
        process = psutil.Process(pid)
        process.terminate()

        # 等待进程结束
        try:
            process.wait(timeout=10)
            admin_logger.info(f"主应用已停止 (PID: {pid})")
        except psutil.TimeoutExpired:
            # 超时，强制关闭
            process.kill()
            admin_logger.warning(f"强制关闭主应用 (PID: {pid})")

        # 删除PID文件
        if os.path.exists(MAIN_APP_PID_FILE):
            os.remove(MAIN_APP_PID_FILE)

        return {'success': True, 'message': '主应用已停止'}
    except Exception as e:
        admin_logger.error(f"停止主应用失败: {e}")
        return {'success': False, 'message': f'停止失败: {str(e)}'}


def restart_main_app():
    """重启主应用"""
    admin_logger.info("重启主应用...")
    stop_result = stop_main_app()
    if not stop_result['success']:
        admin_logger.warning(f"停止主应用失败，继续启动: {stop_result['message']}")

    # 等待一小段时间
    import time
    time.sleep(2)

    start_result = start_main_app()
    return start_result


def get_main_app_status():
    """获取主应用状态"""
    try:
        # 检查PID文件是否存在
        if not os.path.exists(MAIN_APP_PID_FILE):
            return {
                'running': False,
                'pid': None,
                'status': '未运行',
                'cpu_percent': 0,
                'memory_mb': 0
            }

        # 读取PID
        with open(MAIN_APP_PID_FILE, 'r') as f:
            pid_str = f.read().strip()
            if not pid_str:
                # PID文件为空，删除并返回未运行
                os.remove(MAIN_APP_PID_FILE)
                return {
                    'running': False,
                    'pid': None,
                    'status': '未运行',
                    'cpu_percent': 0,
                    'memory_mb': 0
                }
            
            try:
                pid = int(pid_str)
            except ValueError:
                # PID不是有效的数字，删除并返回未运行
                os.remove(MAIN_APP_PID_FILE)
                return {
                    'running': False,
                    'pid': None,
                    'status': '未运行',
                    'cpu_percent': 0,
                    'memory_mb': 0
                }

        # 检查进程是否还在运行
        if not psutil.pid_exists(pid):
            # 进程不存在，删除PID文件
            os.remove(MAIN_APP_PID_FILE)
            return {
                'running': False,
                'pid': None,
                'status': '未运行',
                'cpu_percent': 0,
                'memory_mb': 0
            }

        # 获取进程信息
        try:
            process = psutil.Process(pid)
            return {
                'running': True,
                'pid': pid,
                'status': '运行中',
                'cpu_percent': process.cpu_percent(interval=0.5),
                'memory_mb': process.memory_info().rss / 1024 / 1024
            }
        except psutil.NoSuchProcess:
            # 进程在检查过程中结束了
            os.remove(MAIN_APP_PID_FILE)
            return {
                'running': False,
                'pid': None,
                'status': '未运行',
                'cpu_percent': 0,
                'memory_mb': 0
            }
        except psutil.AccessDenied:
            # 没有权限访问进程
            return {
                'running': True,
                'pid': pid,
                'status': '运行中（无权限监控）',
                'cpu_percent': 0,
                'memory_mb': 0
            }

    except Exception as e:
        admin_logger.error(f"获取主应用状态失败: {e}")
        return {
            'running': False,
            'pid': None,
            'status': '异常',
            'error': str(e),
            'cpu_percent': 0,
            'memory_mb': 0
        }


def get_system_stats():
    """获取系统统计信息"""
    try:
        # 使用更长的采样间隔以获得更稳定的CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1.0)  # 增加到1秒
        memory = psutil.virtual_memory()

        # 获取磁盘信息
        try:
            if os.name == 'nt':  # Windows
                cwd = os.getcwd()
                drive = os.path.splitdrive(cwd)[0]
                disk = psutil.disk_usage(drive)
            else:  # Linux/Mac
                disk = psutil.disk_usage('/')
        except Exception as e:
            admin_logger.warning(f"获取磁盘信息失败: {e}")
            disk = None

        stats = {
            'cpu_percent': cpu_percent,
            'memory_total': memory.total / 1024 / 1024 / 1024,  # GB
            'memory_used': memory.used / 1024 / 1024 / 1024,    # GB
            'memory_percent': memory.percent,
        }

        if disk:
            stats.update({
                'disk_total': disk.total / 1024 / 1024 / 1024,      # GB
                'disk_used': disk.used / 1024 / 1024 / 1024,        # GB
                'disk_percent': disk.percent
            })
        else:
            stats.update({
                'disk_total': 0,
                'disk_used': 0,
                'disk_percent': 0
            })

        return stats
    except Exception as e:
        admin_logger.error(f"获取系统统计失败: {e}")
        # 返回默认值
        return {
            'cpu_percent': 0,
            'memory_total': 0,
            'memory_used': 0,
            'memory_percent': 0,
            'disk_total': 0,
            'disk_used': 0,
            'disk_percent': 0
        }


# ========== 三服务统一管理 ==========

# 服务定义：名称、端口、启动脚本、PID文件、Windows任务名称
SERVICES = {
    'main': {
        'name': '主应用',
        'description': 'app.py - 用户界面',
        'port': MAIN_APP_PORT,
        'script': os.path.join(BASEDIR, 'app.py'),
        'pid_file': os.path.join(BASEDIR, 'instance', 'main_app.pid'),
        'url': f'http://127.0.0.1:{MAIN_APP_PORT}/',
        'task_name': 'dplayer-main',  # Windows 计划任务名称
    },
    'admin': {
        'name': '管理后台',
        'description': 'admin_app.py - 管理界面',
        'port': ADMIN_PORT,
        'script': os.path.join(BASEDIR, 'admin_app.py'),
        'pid_file': os.path.join(BASEDIR, 'instance', 'admin_app.pid'),
        'url': f'http://127.0.0.1:{ADMIN_PORT}/',
        'task_name': 'dplayer-admin',  # Windows 计划任务名称
    },
    'thumbnail': {
        'name': '缩略图服务',
        'description': 'thumbnail_service.py - 缩略图生成',
        'port': 5001,
        'script': os.path.join(BASEDIR, 'services', 'thumbnail_service.py'),
        'pid_file': os.path.join(BASEDIR, 'instance', 'thumbnail_app.pid'),
        'url': 'http://127.0.0.1:5001/health',
        'task_name': 'dplayer-thumbnail',  # Windows 计划任务名称
    },
}

# 检查是否为 Windows 系统
IS_WINDOWS = os.name == 'nt'


def _run_powershell(script):
    """执行 PowerShell 命令并返回结果"""
    import subprocess
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', script],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'PowerShell 执行超时'
    except Exception as e:
        return -1, '', str(e)


def _get_scheduled_task_status(task_name):
    """通过 Get-ScheduledTask 获取任务状态"""
    if not IS_WINDOWS:
        return None, 'Not a Windows system'

    script = f'Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue | Select-Object -Property TaskName,State | ConvertTo-Json'
    code, stdout, stderr = _run_powershell(script)

    if code != 0 or not stdout.strip():
        return None, stderr or 'Task not found'

    try:
        import json
        data = json.loads(stdout)
        # State: 3=Ready, 4=Running, 5=Disabled, etc.
        state_map = {3: 'Ready', 4: 'Running', 5: 'Disabled', 0: 'Unknown'}
        state = state_map.get(data.get('State', 0), 'Unknown')
        return {'task_name': data.get('TaskName'), 'state': state}, ''
    except Exception as e:
        return None, str(e)


def _get_pid_from_file(pid_file):
    """从 PID 文件读取 PID，验证进程存活"""
    try:
        if not os.path.exists(pid_file):
            return None
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        if psutil.pid_exists(pid):
            return pid
        os.remove(pid_file)
        return None
    except Exception:
        return None


def _port_listening(port):
    """检查指定端口是否处于 LISTEN 状态（进程存活的最终判据）"""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
    except Exception:
        pass
    return False


def _pid_for_port(port):
    """返回监听指定端口的 PID，没有则返回 None"""
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return conn.pid
    except Exception:
        pass
    return None


def _get_processes_using_port(port):
    """返回占用指定端口的所有进程信息列表"""
    processes = []
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    processes.append({
                        'pid': conn.pid,
                        'name': proc.name(),
                        'exe': proc.exe() if hasattr(proc, 'exe') else None
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    processes.append({
                        'pid': conn.pid,
                        'name': 'Unknown',
                        'exe': None
                    })
    except Exception as e:
        admin_logger.error(f"获取端口 {port} 进程信息失败: {e}")
    return processes


def get_service_status(svc_key):
    """获取单个服务的完整状态（优先使用 Get-ScheduledTask，结合端口检测）"""
    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']
    task_name = svc.get('task_name')

    # Windows 下优先使用 Get-ScheduledTask 获取任务状态
    task_state = None
    task_info = None
    if IS_WINDOWS and task_name:
        task_result, _ = _get_scheduled_task_status(task_name)
        if task_result:
            task_state = task_result.get('state')
            task_info = _get_task_run_info(task_name)

    # 任务状态：Running=运行中, Ready=就绪(未启动), Disabled=禁用
    task_running = task_state == 'Running'

    # 同时用端口检测作为辅助判据（更可靠）
    live_pid = _pid_for_port(port)
    port_running = live_pid is not None

    # 如果端口没监听，再查 PID 文件作为辅助（防止服务启动中）
    if not port_running:
        live_pid = _get_pid_from_file(pid_file)
        if live_pid:
            port_running = psutil.pid_exists(live_pid)

    # 综合判断：优先信任任务状态（如果已注册），其次看端口
    if task_state:
        # 任务已注册，以任务状态为准
        running = task_running or port_running
        if task_running and not port_running:
            # 任务显示运行但端口未监听，可能还在启动
            live_pid = _get_pid_from_file(pid_file)
    else:
        # 任务未注册，以端口检测为准
        running = port_running

    status_info = {
        'key': svc_key,
        'name': svc['name'],
        'description': svc['description'],
        'port': port,
        'running': running,
        'pid': live_pid,
        'status': '运行中' if running else '已停止',
        'task_state': task_state,  # 计划任务状态
        'task_info': task_info,    # 任务运行信息
        'cpu_percent': 0.0,
        'memory_mb': 0.0,
        'memory_percent': 0.0,
    }

    if running and live_pid:
        try:
            proc = psutil.Process(live_pid)
            # cpu_percent 首次调用返回0，需连续两次或用interval
            proc.cpu_percent()  # 初始化
            time.sleep(0.1)
            status_info['cpu_percent'] = round(proc.cpu_percent(), 1)
            mem = proc.memory_info()
            status_info['memory_mb'] = round(mem.rss / 1024 / 1024, 1)
            status_info['memory_percent'] = round(proc.memory_percent(), 1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return status_info


def get_all_services_status():
    """获取所有服务状态列表（优先使用 Get-ScheduledTask）"""
    return [get_service_status(k) for k in SERVICES]


def update_services_cache():
    """更新服务状态缓存（后台线程调用）"""
    try:
        services = get_all_services_status()
        sys_stats = get_system_stats()

        with cache_lock:
            services_status_cache['services'] = services
            services_status_cache['system'] = sys_stats
            services_status_cache['last_update'] = time.time()

        admin_logger.debug(f"服务状态缓存已更新: {len(services)} 个服务")
    except Exception as e:
        admin_logger.error(f"更新服务状态缓存失败: {e}")


def get_cached_services_status():
    """从缓存获取服务状态（前台API调用）"""
    with cache_lock:
        return {
            'services': services_status_cache['services'],
            'system': services_status_cache['system'],
            'last_update': services_status_cache['last_update']
        }


def _get_task_run_info(task_name):
    """获取任务运行信息（当前运行的进程信息）"""
    if not IS_WINDOWS:
        return None

    # 获取正在运行的任务信息
    script = f'''
$task = Get-ScheduledTask -TaskName "{task_name}" -ErrorAction SilentlyContinue
if ($task -and $task.State -eq 4) {{
    $info = Get-ScheduledTaskInfo -TaskName "{task_name}" -ErrorAction SilentlyContinue
    if ($info) {{
        @{{
            LastRunTime = if ($info.LastRunTime) {{ $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss") }} else {{ $null }}
            LastTaskResult = $info.LastTaskResult
            NumberOfMissedRuns = $info.NumberOfMissedRuns
        }} | ConvertTo-Json
    }} else {{ "{{}}" }}
}} else {{ "{{}}" }}
'''
    code, stdout, stderr = _run_powershell(script)
    if code != 0 or not stdout.strip():
        return None

    try:
        import json
        data = json.loads(stdout.strip() or '{}')
        if not data:
            return None
        return data
    except:
        return None


def start_service(svc_key):
    """启动指定服务（优先使用计划任务，任务不存在时直接启动以保留代码热重载特性）"""
    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']
    script = svc['script']
    task_name = svc.get('task_name')

    # 检查是否需要强制终止占用进程
    force_kill = False
    port_conflict_processes = []

    # 检查端口是否被其他进程占用
    if _port_listening(port):
        # 检查是否是本服务
        pid_for_port = _pid_for_port(port)
        if pid_for_port:
            # 读取PID文件
            service_pid = None
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        service_pid = int(f.read().strip())
                except:
                    pass

            # 如果是自己的进程，说明已在运行
            if service_pid and pid_for_port == service_pid:
                return {'success': False, 'message': f'{svc["name"]} 已在运行（端口 {port}）', 'port_conflict': False}

        # 端口被其他进程占用，返回占用进程信息
        port_conflict_processes = _get_processes_using_port(port)
        if not request.get_json(silent=True) or not request.get_json(silent=True).get('force', False):
            return {
                'success': False,
                'message': f'端口 {port} 已被占用',
                'port_conflict': True,
                'port': port,
                'processes': port_conflict_processes
            }
        else:
            # 强制终止占用进程
            force_kill = True
            if port_conflict_processes:
                for proc in port_conflict_processes:
                    try:
                        p = psutil.Process(proc['pid'])
                        p.terminate()
                        try:
                            p.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            p.kill()
                        admin_logger.info(f"强制终止占用进程 {proc['name']} (PID: {proc['pid']})")
                    except Exception as e:
                        admin_logger.warning(f"终止进程 {proc['pid']} 失败: {e}")
                time.sleep(1)  # 等待端口释放

    # Windows 下优先尝试使用计划任务
    if IS_WINDOWS and task_name:
        task_result, _ = _get_scheduled_task_status(task_name)
        if task_result:
            # 任务存在，使用 Start-ScheduledTask 启动
            script_ps = f'Start-ScheduledTask -TaskName "{task_name}"'
            code, stdout, stderr = _run_powershell(script_ps)
            if code == 0:
                # 等待端口就绪
                for _ in range(20):
                    time.sleep(0.5)
                    if _port_listening(port):
                        admin_logger.info(f"服务 {svc['name']} 通过计划任务启动成功")
                        return {'success': True, 'message': f'{svc["name"]} 启动成功（计划任务）'}
                return {'success': True, 'message': f'{svc["name"]} 计划任务已启动，等待端口就绪'}
            else:
                admin_logger.warning(f"计划任务启动失败: {stderr}，尝试直接启动")

    # 计划任务不存在或失败时，直接启动（保留代码热重载特性）
    try:
        env = os.environ.copy()
        if svc_key == 'thumbnail':
            env['THUMBNAIL_SERVICE_PORT'] = str(port)

        # 创建日志文件
        service_log_file = os.path.join(LOG_DIR, f'{svc_key}_startup.log')
        with open(service_log_file, 'w', encoding='utf-8') as log_file:
            log_file.write(f"=== 启动服务: {svc['name']} ===\n")
            log_file.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"脚本: {script}\n")
            log_file.write(f"端口: {port}\n")
            log_file.write(f"工作目录: {BASEDIR}\n\n")

        # 打开日志文件用于写入子进程输出
        stdout_file = open(os.path.join(LOG_DIR, f'{svc_key}_stdout.log'), 'w', encoding='utf-8')
        stderr_file = open(os.path.join(LOG_DIR, f'{svc_key}_stderr.log'), 'w', encoding='utf-8')

        proc = subprocess.Popen(
            [sys.executable, script],
            cwd=BASEDIR,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )

        # 立即关闭文件句柄,让子进程自己管理
        stdout_file.close()
        stderr_file.close()

        # 写入 PID 文件
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        with open(pid_file, 'w') as f:
            f.write(str(proc.pid))

        admin_logger.info(f"启动服务 {svc['name']} (PID: {proc.pid}, 脚本: {script})")

        # 等待端口就绪（最多10秒）
        for i in range(20):
            time.sleep(0.5)
            if _port_listening(port):
                admin_logger.info(f"服务 {svc['name']} 启动成功 (PID: {proc.pid}, 端口: {port})")
                return {'success': True, 'message': f'{svc["name"]} 启动成功', 'pid': proc.pid}

        # 端口未就绪，检查进程状态
        if not psutil.pid_exists(proc.pid):
            admin_logger.error(f"服务 {svc['name']} 进程已退出 (PID: {proc.pid})")
            # 读取错误日志
            stderr_log = os.path.join(LOG_DIR, f'{svc_key}_stderr.log')
            if os.path.exists(stderr_log):
                with open(stderr_log, 'r', encoding='utf-8') as f:
                    error_content = f.read()
                    admin_logger.error(f"启动错误日志:\n{error_content}")
            return {'success': False, 'message': f'{svc["name"]} 启动失败，进程已退出(查看日志: logs/{svc_key}_stderr.log)'}
        else:
            admin_logger.info(f"服务 {svc['name']} 进程存在但端口未就绪 (PID: {proc.pid})")
            return {'success': True, 'message': f'{svc["name"]} 进程已启动，等待端口就绪', 'pid': proc.pid}

    except Exception as e:
        admin_logger.error(f"启动服务 {svc['name']} 失败: {e}", exc_info=True)
        return {'success': False, 'message': str(e)}


def stop_service(svc_key):
    """停止指定服务（优先通过计划任务，其次通过端口/PID文件）"""
    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']
    task_name = svc.get('task_name')

    # 自己不能停止自己
    if svc_key == 'admin':
        return {'success': False, 'message': '管理后台不能停止自身'}

    # Windows 下优先尝试使用计划任务停止
    if IS_WINDOWS and task_name:
        task_result, _ = _get_scheduled_task_status(task_name)
        if task_result and task_result.get('state') == 'Running':
            # 任务正在运行，使用 Stop-ScheduledTask 停止
            script_ps = f'Stop-ScheduledTask -TaskName "{task_name}"'
            code, stdout, stderr = _run_powershell(script_ps)
            if code == 0:
                # 等待端口释放
                for _ in range(10):
                    time.sleep(0.5)
                    if not _port_listening(port):
                        admin_logger.info(f"服务 {svc['name']} 通过计划任务已停止")
                        return {'success': True, 'message': f'{svc["name"]} 已停止（计划任务）'}

    # 计划任务不存在或失败时，直接终止进程
    pid = _pid_for_port(port) or _get_pid_from_file(pid_file)
    if not pid:
        return {'success': False, 'message': f'{svc["name"]} 未在运行'}

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)

        # 清理 PID 文件
        if os.path.exists(pid_file):
            os.remove(pid_file)

        admin_logger.info(f"服务 {svc['name']} 已停止 (PID: {pid})")
        return {'success': True, 'message': f'{svc["name"]} 已停止'}

    except psutil.NoSuchProcess:
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return {'success': True, 'message': f'{svc["name"]} 进程已不存在'}
    except Exception as e:
        admin_logger.error(f"停止服务 {svc['name']} 失败: {e}")
        return {'success': False, 'message': str(e)}


def restart_service(svc_key):
    """重启指定服务"""
    if svc_key == 'admin':
        return {'success': False, 'message': '管理后台不支持通过界面重启，请手动操作'}
    stop_result = stop_service(svc_key)
    time.sleep(2)
    start_result = start_service(svc_key)
    if start_result['success']:
        return {'success': True, 'message': f'{SERVICES[svc_key]["name"]} 重启成功'}
    return {'success': False, 'message': f'重启失败: {start_result["message"]}'}


# ===== 服务管理页面 & API 路由 =====

@app.route('/services')
def page_services():
    """服务管理页面"""
    # 定义服务列表
    services_list = [
        {'key': 'main', 'name': '主应用', 'description': 'app.py - 用户界面', 'port': 80},
        {'key': 'admin', 'name': '管理后台', 'description': 'admin_app.py - 管理界面', 'port': 8080},
        {'key': 'thumbnail', 'name': '缩略图服务', 'description': 'thumbnail_service.py - 缩略图生成', 'port': 5001}
    ]
    return render_template('admin/services.html', services=services_list)


@app.route('/api/services/status')
def api_services_status():
    """获取所有服务状态（从缓存读取）"""
    try:
        cached = get_cached_services_status()
        return jsonify({
            'success': True,
            'services': cached['services'],
            'system': cached['system'],
            'last_update': cached['last_update'],
        })
    except Exception as e:
        admin_logger.error(f"获取服务状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/services/<svc_key>/status')
def api_service_status(svc_key):
    """获取单个服务的状态（用于异步加载）"""
    try:
        if svc_key not in SERVICES:
            return jsonify({'success': False, 'message': '未知服务'}), 404
        status = get_service_status(svc_key)
        return jsonify({
            'success': True,
            'service': status
        })
    except Exception as e:
        admin_logger.error(f"获取服务 {svc_key} 状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/services/<svc_key>/check-port', methods=['GET'])
def api_service_check_port(svc_key):
    """检查服务端口是否可用"""
    if svc_key not in SERVICES:
        return jsonify({'success': False, 'message': '未知服务'}), 404

    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']

    # 检查端口是否被占用
    if not _port_listening(port):
        return jsonify({'success': True, 'port': port, 'in_use': False})

    # 端口被占用，检查是否是本服务
    pid_for_port = _pid_for_port(port)
    service_pid = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                service_pid = int(f.read().strip())
        except:
            pass

    # 如果是自己的进程，说明已在运行
    if service_pid and pid_for_port == service_pid:
        return jsonify({
            'success': True,
            'port': port,
            'in_use': True,
            'is_self': True,
            'message': f'{svc["name"]} 已在运行'
        })

    # 端口被其他进程占用
    processes = _get_processes_using_port(port)
    return jsonify({
        'success': False,
        'port': port,
        'in_use': True,
        'is_self': False,
        'processes': processes
    })


@app.route('/api/services/<svc_key>/start', methods=['POST'])
def api_service_start(svc_key):
    """启动指定服务"""
    if svc_key not in SERVICES:
        return jsonify({'success': False, 'message': '未知服务'}), 404
    result = start_service(svc_key)
    return jsonify(result)


@app.route('/api/services/<svc_key>/stop', methods=['POST'])
def api_service_stop(svc_key):
    """停止指定服务"""
    if svc_key not in SERVICES:
        return jsonify({'success': False, 'message': '未知服务'}), 404
    result = stop_service(svc_key)
    return jsonify(result)


@app.route('/api/services/<svc_key>/restart', methods=['POST'])
def api_service_restart(svc_key):
    """重启指定服务"""
    if svc_key not in SERVICES:
        return jsonify({'success': False, 'message': '未知服务'}), 404
    result = restart_service(svc_key)
    return jsonify(result)


# ========== 布局调试日志功能 ==========

DEBUG_LOG_FILE = os.path.join(LOG_DIR, 'layout_debug.log')


@app.route('/api/debug/log', methods=['POST'])
def api_debug_log():
    """接收前端布局调试日志并保存到文件"""
    try:
        layout_info = request.json
        if not layout_info:
            return jsonify({'success': False, 'message': '无效数据'}), 400

        # 格式化日志信息
        log_lines = [
            "=" * 60,
            f"时间: {layout_info.get('timestamp', 'N/A')}",
            f"窗口宽度: {layout_info.get('windowWidth', 'N/A')}px",
            f"表格宽度: {layout_info.get('tableWidth', 'N/A')}px",
            f"表格列数: {layout_info.get('columnCount', 'N/A')}",
            f"表格布局模式: {layout_info.get('tableLayout', 'N/A')}",
            f"表格 min-width: {layout_info.get('tableMinWidth', 'N/A')}",
            f"表格 max-width: {layout_info.get('tableMaxWidth', 'N/A')}",
            "",
            "媒体查询状态:",
            f"  - max-width: 768px: {layout_info.get('mediaQueries', {}).get('max768px', 'N/A')}",
            f"  - max-width: 480px: {layout_info.get('mediaQueries', {}).get('max480px', 'N/A')}",
            "",
            "列宽详情:"
        ]

        columns = layout_info.get('columns', [])
        for col in columns:
            log_lines.extend([
                f"  第{col.get('index', 'N/A')}列:",
                f"    - th宽度: {col.get('headerWidth', 'N/A')}px",
                f"    - th显示: {col.get('headerDisplay', 'N/A')}",
                f"    - th width: {col.get('headerCssWidth', 'N/A')}",
                f"    - th max-width: {col.get('headerMaxWidth', 'N/A')}",
                f"    - th min-width: {col.get('headerMinWidth', 'N/A')}",
                f"    - td宽度: {col.get('bodyWidth', 'N/A')}px",
                f"    - td显示: {col.get('bodyDisplay', 'N/A')}",
                f"    - td width: {col.get('bodyCssWidth', 'N/A')}",
                f"    - td max-width: {col.get('bodyMaxWidth', 'N/A')}",
                f"    - td min-width: {col.get('bodyMinWidth', 'N/A')}",
                ""
            ])

        log_lines.append("=" * 60)
        log_lines.append("")

        # 写入日志文件
        with open(DEBUG_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write('\n'.join(log_lines))

        admin_logger.info(f"收到布局调试日志, 窗口宽度: {layout_info.get('windowWidth', 'N/A')}px")
        return jsonify({'success': True, 'message': '日志已保存'})
    except Exception as e:
        admin_logger.error(f"保存调试日志失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== 数据库清理功能 ==========

def get_db_stats():
    """获取数据库统计信息"""
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(DB_FILE):
            return {
                'success': False,
                'message': '数据库文件不存在'
            }

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        stats = {}

        try:
            # 视频统计
            cursor.execute('SELECT COUNT(*) FROM videos')
            stats['video_count'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM videos WHERE duration IS NOT NULL')
            stats['video_with_duration'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM videos WHERE is_downloaded = 1')
            stats['video_downloaded'] = cursor.fetchone()[0]

            # 标签统计
            cursor.execute('SELECT COUNT(*) FROM tags')
            stats['tag_count'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM video_tags')
            stats['video_tag_count'] = cursor.fetchone()[0]

            # 用户交互统计
            cursor.execute('SELECT COUNT(*) FROM user_interactions')
            stats['interaction_count'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE interaction_type = "favorite"')
            stats['favorite_count'] = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM user_interactions WHERE interaction_type = "view"')
            stats['view_count'] = cursor.fetchone()[0]

            # 数据库文件大小
            db_size = os.path.getsize(DB_FILE) / 1024 / 1024  # MB
            stats['db_size_mb'] = round(db_size, 2)

            conn.close()
            return {'success': True, 'stats': stats}

        except sqlite3.OperationalError as e:
            conn.close()
            admin_logger.error(f"数据库查询失败: {e}")
            return {
                'success': False,
                'message': f'数据库查询失败: {str(e)}'
            }

    except Exception as e:
        admin_logger.error(f"获取数据库统计失败: {e}")
        return {
            'success': False,
            'message': f'获取数据库统计失败: {str(e)}'
        }


def clear_data(data_type, dry_run=False):
    """清理数据

    Args:
        data_type: 数据类型 ('interactions', 'favorites', 'views', 'tags', 'thumbnails', 'all')
        dry_run: 是否只是预览，不实际删除

    Returns:
        dict: 清理结果
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        affected_count = 0
        result_message = ''

        if data_type == 'interactions':
            # 清空所有用户交互
            if not dry_run:
                cursor.execute('DELETE FROM user_interactions')
            affected_count = cursor.rowcount
            result_message = f'将删除 {affected_count} 条用户交互记录'

        elif data_type == 'favorites':
            # 只清空收藏
            if not dry_run:
                cursor.execute('DELETE FROM user_interactions WHERE interaction_type = "favorite"')
            affected_count = cursor.rowcount
            result_message = f'将删除 {affected_count} 条收藏记录'

        elif data_type == 'views':
            # 只清空浏览记录
            if not dry_run:
                cursor.execute('DELETE FROM user_interactions WHERE interaction_type = "view"')
            affected_count = cursor.rowcount
            result_message = f'将删除 {affected_count} 条浏览记录'

        elif data_type == 'tags':
            # 清空所有标签
            if not dry_run:
                cursor.execute('DELETE FROM video_tags')
                cursor.execute('DELETE FROM tags')
            affected_count = '所有'
            result_message = '将删除所有标签和标签关联'

        elif data_type == 'thumbnails':
            # 清空缩略图缓存
            thumbnail_dir = 'static/thumbnails'
            if os.path.exists(thumbnail_dir):
                files = os.listdir(thumbnail_dir)
                if not dry_run:
                    for file in files:
                        os.remove(os.path.join(thumbnail_dir, file))
                affected_count = len(files)
                result_message = f'将删除 {affected_count} 个缩略图文件'
            else:
                result_message = '缩略图目录不存在'

        elif data_type == 'all':
            # 清空所有数据（除了视频记录）
            if not dry_run:
                cursor.execute('DELETE FROM user_interactions')
                cursor.execute('DELETE FROM video_tags')
                cursor.execute('DELETE FROM tags')
                cursor.execute('DELETE FROM user_preferences')

                # 清空缩略图
                thumbnail_dir = 'static/thumbnails'
                if os.path.exists(thumbnail_dir):
                    files = os.listdir(thumbnail_dir)
                    for file in files:
                        os.remove(os.path.join(thumbnail_dir, file))
                    thumbnail_count = len(files)
                else:
                    thumbnail_count = 0

                affected_count = f'所有（{thumbnail_count}个缩略图）'
            else:
                affected_count = '所有'
            result_message = '将清空所有数据（除了视频记录）'

        if not dry_run:
            conn.commit()
            conn.close()
            admin_logger.info(f"清理数据完成: {data_type}, {result_message}")
            return {
                'success': True,
                'message': f'清理完成: {result_message}',
                'dry_run': False
            }
        else:
            conn.close()
            return {
                'success': True,
                'message': result_message,
                'dry_run': True,
                'affected_count': affected_count
            }

    except Exception as e:
        admin_logger.error(f"清理数据失败: {e}")
        return {'success': False, 'message': f'清理失败: {str(e)}'}


# ========== 路由 ==========

@app.route('/')
def index():
    """管理后台首页"""
    # 定义服务列表
    services_list = [
        {'key': 'main', 'name': '主应用', 'description': '用户界面', 'entry_point': 'app.py', 'port': 80},
        {'key': 'admin', 'name': '管理后台', 'description': '管理界面', 'entry_point': 'admin_app.py', 'port': 8080},
        {'key': 'thumbnail', 'name': '缩略图服务', 'description': '缩略图生成', 'entry_point': 'thumbnail_service.py', 'port': 5001}
    ]
    return render_template('admin/index.html', services=services_list)


@app.route('/api/status')
def api_status():
    """获取状态信息"""
    try:
        main_app_status = get_main_app_status()
        system_stats = get_system_stats()
        db_stats_result = get_db_stats()

        # 构建数据库统计信息（适配前端期望的格式）
        database = {}
        if db_stats_result.get('success'):
            stats = db_stats_result['stats']
            database = {
                'videos': {
                    'total': stats.get('video_count', 0)
                },
                'tags': {
                    'total': stats.get('tag_count', 0)
                },
                'total_views': stats.get('view_count', 0),
                'total_likes': 0,  # 暂无likes统计
                'db_size_mb': stats.get('db_size_mb', 0)
            }

        return jsonify({
            'success': True,
            'main_app': main_app_status,
            'system': system_stats,
            'database': database,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        admin_logger.error(f"获取状态失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/app/start', methods=['POST'])
def api_start_app():
    """启动主应用"""
    result = start_main_app()
    return jsonify(result)


@app.route('/api/app/stop', methods=['POST'])
def api_stop_app():
    """停止主应用"""
    result = stop_main_app()
    return jsonify(result)


@app.route('/api/app/restart', methods=['POST'])
def api_restart_app():
    """重启主应用"""
    result = restart_main_app()
    return jsonify(result)


@app.route('/api/db/stats')
def api_db_stats():
    """获取数据库统计"""
    try:
        result = get_db_stats()

        if not result.get('success'):
            return jsonify(result)

        # 扁平化数据结构
        stats = result['stats']
        return jsonify({
            'success': True,
            'videos': stats['video_count'],
            'tags': stats['tag_count'],
            'total_views': stats['view_count'],
            'total_likes': 0,  # 暂无likes字段
            'db_size_mb': stats['db_size_mb'],
            'interaction_count': stats['interaction_count'],
            'favorite_count': stats['favorite_count']
        })
    except Exception as e:
        admin_logger.error(f"获取数据库统计失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/db/clear', methods=['POST'])
def api_db_clear():
    """清理数据库"""
    try:
        data = request.get_json()
        data_type = data.get('type', 'all')
        dry_run = data.get('dry_run', False)

        result = clear_data(data_type, dry_run)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ========== 视频管理 API ==========

@app.route('/api/videos')
def api_videos():
    """获取视频列表（分页）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 限制每页数量范围
        per_page = max(10, min(100, per_page))

        # 计算偏移量
        offset = (page - 1) * per_page

        # 使用原生SQL查询
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取总数
        cursor.execute('SELECT COUNT(*) as count FROM videos')
        total = cursor.fetchone()['count']

        # 分页查询（包含min_role字段）
        cursor.execute('''
            SELECT id, hash, title, description, url, thumbnail, duration,
                   file_size, view_count, like_count, download_count, priority,
                   is_downloaded, local_path, created_at, updated_at,
                   COALESCE(min_role, 0) as min_role
            FROM videos
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

        rows = cursor.fetchall()
        conn.close()

        # 角色名称映射
        role_names = {0: '游客', 1: '用户', 2: '管理员', 3: '超级管理员'}

        # 转换为字典格式
        videos_data = []
        for row in rows:
            videos_data.append({
                'id': row['id'],
                'hash': row['hash'],
                'title': row['title'],
                'description': row['description'],
                'url': row['url'],
                'thumbnail': row['thumbnail'],
                'duration': row['duration'],
                'file_size': row['file_size'],
                'view_count': row['view_count'],
                'like_count': row['like_count'],
                'download_count': row['download_count'],
                'priority': row['priority'],
                'min_role': row['min_role'],
                'min_role_name': role_names.get(row['min_role'], '游客'),
                'is_downloaded': row['is_downloaded'],
                'local_path': row['local_path'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'tags': []  # 标签信息需要额外查询
            })

        # 计算总页数
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        return jsonify({
            'success': True,
            'videos': videos_data,
            'total': total,
            'pages': pages,
            'current_page': page
        })
    except Exception as e:
        admin_logger.error(f"获取视频列表失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/video/add', methods=['POST'])
def api_add_video():
    """添加视频"""
    try:
        data = request.get_json()

        # 生成视频hash
        video_hash = hashlib.sha256(data['url'].encode('utf-8')).hexdigest()

        # 检查是否已存在
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM videos WHERE hash = ?', (video_hash,))
        existing = cursor.fetchone()
        conn.close()

        if existing:
            return jsonify({'success': False, 'message': '视频已存在'})

        # 插入视频
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO videos (hash, title, url, thumbnail, description, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', (
            video_hash,
            data['title'],
            data['url'],
            data.get('thumbnail'),
            data.get('description'),
            data.get('priority', 0)
        ))
        conn.commit()
        conn.close()

        admin_logger.info(f"添加视频: {data['title']}")
        return jsonify({'success': True, 'message': '视频添加成功'})
    except Exception as e:
        admin_logger.error(f"添加视频失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/video/<video_hash>', methods=['DELETE'])
def api_delete_video(video_hash):
    """删除视频"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 获取视频标题
        cursor.execute('SELECT title FROM videos WHERE hash = ?', (video_hash,))
        video = cursor.fetchone()
        if not video:
            conn.close()
            return jsonify({'success': False, 'message': '视频不存在'})

        title = video[0]

        # 删除视频（包括关联的标签）
        cursor.execute('DELETE FROM video_tags WHERE video_id IN (SELECT id FROM videos WHERE hash = ?)', (video_hash,))
        cursor.execute('DELETE FROM user_interactions WHERE video_id IN (SELECT id FROM videos WHERE hash = ?)', (video_hash,))
        cursor.execute('DELETE FROM videos WHERE hash = ?', (video_hash,))

        conn.commit()
        conn.close()

        admin_logger.info(f"删除视频: {title}")
        return jsonify({'success': True, 'message': '视频删除成功'})
    except Exception as e:
        admin_logger.error(f"删除视频失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/video/<video_hash>', methods=['GET'])
def api_get_video(video_hash):
    """获取视频详情"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 获取视频信息
        cursor.execute('''
            SELECT id, hash, title, description, url, thumbnail, duration,
                   file_size, view_count, like_count, download_count, priority,
                   is_downloaded, local_path, created_at, updated_at
            FROM videos
            WHERE hash = ?
        ''', (video_hash,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': '视频不存在'})

        # 构建视频数据
        video = {
            'id': row[0],
            'hash': row[1],
            'title': row[2],
            'description': row[3],
            'url': row[4],
            'thumbnail': row[5],
            'duration': row[6],
            'file_size': row[7],
            'view_count': row[8],
            'like_count': row[9],
            'download_count': row[10],
            'priority': row[11],
            'is_downloaded': row[12],
            'local_path': row[13],
            'created_at': row[14],
            'updated_at': row[15],
            'tags': []
        }

        # 获取视频标签
        cursor.execute('''
            SELECT t.id, t.name, t.category
            FROM tags t
            INNER JOIN video_tags vt ON t.id = vt.tag_id
            INNER JOIN videos v ON vt.video_id = v.id
            WHERE v.hash = ?
            ORDER BY t.name
        ''', (video_hash,))

        for tag_row in cursor.fetchall():
            video['tags'].append({
                'id': tag_row[0],
                'name': tag_row[1],
                'category': tag_row[2]
            })

        # 检查是否已收藏
        cursor.execute('''
            SELECT COUNT(*)
            FROM user_interactions
            WHERE interaction_type = 'favorite'
        ''')
        is_favorited = cursor.fetchone()[0] > 0
        video['is_favorited'] = is_favorited

        conn.close()
        return jsonify({'success': True, 'video': video})
    except Exception as e:
        admin_logger.error(f"获取视频详情失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/video/<video_hash>/permission', methods=['PUT'])
def api_update_video_permission(video_hash):
    """更新视频权限要求（管理员及以上）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        min_role = data.get('min_role', 0)

        # 验证角色值
        if min_role not in [0, 1, 2, 3]:
            return jsonify({'success': False, 'message': '无效的权限值'}), 400

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 检查视频是否存在
        cursor.execute('SELECT id, title FROM videos WHERE hash = ?', (video_hash,))
        video = cursor.fetchone()
        if not video:
            conn.close()
            return jsonify({'success': False, 'message': '视频不存在'}), 404

        video_id, title = video

        # 更新权限
        cursor.execute('UPDATE videos SET min_role = ?, updated_at = datetime("now") WHERE hash = ?',
                      (min_role, video_hash))
        conn.commit()
        conn.close()

        role_names = {0: '游客', 1: '用户', 2: '管理员', 3: '超级管理员'}
        admin_logger.info(f"更新视频权限: {title} -> {role_names.get(min_role, '游客')}")
        return jsonify({
            'success': True,
            'message': f'视频权限已更新为{role_names.get(min_role, "游客")}',
            'min_role': min_role,
            'min_role_name': role_names.get(min_role, '游客')
        })
    except Exception as e:
        admin_logger.error(f"更新视频权限失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/video/<video_hash>/tags', methods=['GET'])
def api_get_video_tags(video_hash):
    """获取视频的标签"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.id, t.name, t.category
            FROM tags t
            INNER JOIN video_tags vt ON t.id = vt.tag_id
            INNER JOIN videos v ON vt.video_id = v.id
            WHERE v.hash = ?
            ORDER BY t.name
        ''', (video_hash,))

        tags = []
        for row in cursor.fetchall():
            tags.append({
                'id': row[0],
                'name': row[1],
                'category': row[2]
            })

        conn.close()
        return jsonify({'success': True, 'tags': tags})
    except Exception as e:
        admin_logger.error(f"获取视频标签失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/video/<video_hash>/tags', methods=['PUT'])
def api_update_video_tags(video_hash):
    """更新视频的标签"""
    try:
        data = request.get_json()
        tag_ids = data.get('tags', [])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 获取视频ID
        cursor.execute('SELECT id FROM videos WHERE hash = ?', (video_hash,))
        video = cursor.fetchone()
        if not video:
            conn.close()
            return jsonify({'success': False, 'message': '视频不存在'})

        video_id = video[0]

        # 删除旧标签关联
        cursor.execute('DELETE FROM video_tags WHERE video_id = ?', (video_id,))

        # 添加新标签关联
        for tag_id in tag_ids:
            cursor.execute('INSERT INTO video_tags (video_id, tag_id) VALUES (?, ?)',
                         (video_id, tag_id))

        conn.commit()
        conn.close()

        admin_logger.info(f"更新视频标签: {video_hash}, 标签数: {len(tag_ids)}")
        return jsonify({'success': True, 'message': '标签更新成功'})
    except Exception as e:
        admin_logger.error(f"更新视频标签失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/videos/clear', methods=['POST'])
def api_clear_videos():
    """清空所有视频"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 获取视频数量
        cursor.execute('SELECT COUNT(*) FROM videos')
        count = cursor.fetchone()[0]

        # 清空视频表（包括关联）
        cursor.execute('DELETE FROM video_tags')
        cursor.execute('DELETE FROM user_interactions WHERE video_id IS NOT NULL')
        cursor.execute('DELETE FROM videos')

        conn.commit()
        conn.close()

        admin_logger.info(f"清空所有视频: {count} 个")
        return jsonify({'success': True, 'message': f'已清空 {count} 个视频'})
    except Exception as e:
        admin_logger.error(f"清空视频失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


# ========== 标签管理 API ==========

@app.route('/api/tags')
def api_tags():
    """获取标签列表"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT t.id, t.name, t.category, COUNT(vt.video_id) as video_count
            FROM tags t
            LEFT JOIN video_tags vt ON t.id = vt.tag_id
            GROUP BY t.id, t.name, t.category
            ORDER BY t.name
        ''')

        rows = cursor.fetchall()
        conn.close()

        tags_data = []
        for row in rows:
            tags_data.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'video_count': row[3] or 0
            })

        return jsonify({
            'success': True,
            'tags': tags_data
        })
    except Exception as e:
        admin_logger.error(f"获取标签列表失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/tags/add', methods=['POST'])
def api_add_tag():
    """添加标签"""
    try:
        data = request.get_json()

        # 检查是否已存在
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM tags WHERE name = ?', (data['name'],))
        existing = cursor.fetchone()
        conn.close()

        if existing:
            return jsonify({'success': False, 'message': '标签已存在'})

        # 插入标签
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tags (name, category, created_at)
            VALUES (?, ?, datetime('now'))
        ''', (
            data['name'],
            data.get('category')
        ))
        conn.commit()
        conn.close()

        admin_logger.info(f"添加标签: {data['name']}")
        return jsonify({'success': True, 'message': '标签添加成功'})
    except Exception as e:
        admin_logger.error(f"添加标签失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def api_delete_tag(tag_id):
    """删除标签"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # 获取标签名称
        cursor.execute('SELECT name FROM tags WHERE id = ?', (tag_id,))
        tag = cursor.fetchone()
        if not tag:
            conn.close()
            return jsonify({'success': False, 'message': '标签不存在'})

        name = tag[0]

        # 删除标签（包括关联）
        cursor.execute('DELETE FROM video_tags WHERE tag_id = ?', (tag_id,))
        cursor.execute('DELETE FROM tags WHERE id = ?', (tag_id,))

        conn.commit()
        conn.close()

        admin_logger.info(f"删除标签: {name}")
        return jsonify({'success': True, 'message': '标签删除成功'})
    except Exception as e:
        admin_logger.error(f"删除标签失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logs')
def api_logs():
    """获取日志"""
    try:
        log_type = request.args.get('type', 'admin')
        lines = int(request.args.get('lines', 100))

        log_file = os.path.join(LOG_DIR, f'{log_type}.log')

        # 如果日志文件不存在，返回空结果而不是错误
        if not os.path.exists(log_file):
            admin_logger.info(f"日志文件不存在: {log_file}")
            return jsonify({
                'success': True,
                'logs': [f'日志文件 {log_type}.log 不存在'],
                'total_lines': 0
            })

        # 读取最后N行
        with open(log_file, 'r', encoding='utf-8') as f:
            lines_list = f.readlines()
            last_lines = lines_list[-lines:] if len(lines_list) > lines else lines_list

        return jsonify({
            'success': True,
            'logs': last_lines,
            'total_lines': len(lines_list)
        })
    except Exception as e:
        admin_logger.error(f"获取日志失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logs/list')
def api_logs_list():
    """获取日志文件列表"""
    try:
        files = []
        for filename in os.listdir(LOG_DIR):
            if filename.endswith('.log'):
                filepath = os.path.join(LOG_DIR, filename)
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

        # 按修改时间排序
        files.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({'success': True, 'files': files})
    except Exception as e:
        admin_logger.error(f"获取日志列表失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logs/download/<filename>')
def api_logs_download(filename):
    """下载日志文件"""
    try:
        # 安全检查：防止路径遍历攻击
        if '..' in filename or '/' in filename:
            return jsonify({'success': False, 'message': '非法的文件名'}), 400

        filepath = os.path.join(LOG_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        return send_file(filepath, as_attachment=True)
    except Exception as e:
        admin_logger.error(f"下载日志失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/logs/clear', methods=['POST'])
def api_logs_clear():
    """清空日志"""
    try:
        data = request.get_json()
        log_type = data.get('type', 'all')

        if log_type == 'all':
            # 清空所有日志文件
            count = 0
            for filename in os.listdir(LOG_DIR):
                if filename.endswith('.log'):
                    filepath = os.path.join(LOG_DIR, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('')
                    count += 1
            admin_logger.info(f"清空所有日志文件: {count} 个")
            return jsonify({'success': True, 'message': f'已清空 {count} 个日志文件'})
        else:
            # 清空指定类型的日志
            log_file = os.path.join(LOG_DIR, f'{log_type}.log')
            if os.path.exists(log_file):
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write('')
                admin_logger.info(f"清空日志文件: {log_type}.log")
                return jsonify({'success': True, 'message': f'已清空 {log_type}.log'})
            else:
                return jsonify({'success': False, 'message': '日志文件不存在'})
    except Exception as e:
        admin_logger.error(f"清空日志失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/logs/size')
def api_logs_size():
    """获取日志目录总大小"""
    try:
        total_size = 0
        file_count = 0

        for filename in os.listdir(LOG_DIR):
            if filename.endswith('.log'):
                filepath = os.path.join(LOG_DIR, filename)
                total_size += os.path.getsize(filepath)
                file_count += 1

        return jsonify({
            'success': True,
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count
        })
    except Exception as e:
        admin_logger.error(f"获取日志大小失败: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/thumbnails/regenerate', methods=['POST'])
def api_thumbnails_regenerate():
    """批量重新生成缩略图"""
    try:
        # 检查主应用是否在运行
        status = get_main_app_status()
        if not status['running']:
            return jsonify({
                'success': False,
                'message': '主应用未运行，无法重新生成缩略图'
            })

        # 这个功能需要调用主应用的API
        # 因为缩略图生成在主应用中实现
        import requests

        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/thumbnails/regenerate"
        admin_logger.info(f"触发缩略图批量重新生成: {main_app_url}")
        response = requests.post(main_app_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            admin_logger.info(f"触发缩略图批量重新生成: {data.get('message', '')}")
            return jsonify({
                'success': True,
                'message': '缩略图批量重新生成已触发',
                'task_id': data.get('task_id')
            })
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"触发缩略图生成失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"缩略图生成失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


# ========== 系统配置 API ==========

@app.route('/api/config')
def api_get_config():
    """获取系统配置（从主应用）"""
    try:
        # 首先检查主应用是否在运行
        status = get_main_app_status()
        if not status['running']:
            return jsonify({
                'success': False,
                'message': '主应用未运行，无法获取配置'
            })

        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/config"
        admin_logger.info(f"请求配置: {main_app_url}")
        response = requests.get(main_app_url, timeout=5)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"获取配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"获取配置失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/config', methods=['PUT'])
def api_update_config():
    """更新系统配置（通过主应用）"""
    try:
        # 检查主应用是否在运行
        status = get_main_app_status()
        if not status['running']:
            return jsonify({
                'success': False,
                'message': '主应用未运行，无法更新配置'
            })

        data = request.get_json()
        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/config"
        admin_logger.info(f"更新配置: {main_app_url}")
        response = requests.put(main_app_url, json=data, timeout=5)

        if response.status_code == 200:
            admin_logger.info(f"更新配置成功")
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"更新配置失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"更新配置失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """扫描配置目录（通过主应用）"""
    try:
        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/scan"
        response = requests.post(main_app_url, timeout=30)  # 扫描可能需要较长时间

        if response.status_code == 200:
            data = response.json()
            admin_logger.info(f"扫描完成: {data.get('message', '')}")
            return jsonify(data)
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"扫描失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"扫描失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/dependencies/check')
def api_check_dependencies():
    """检查依赖（通过主应用）"""
    try:
        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/dependencies/check"
        response = requests.get(main_app_url, timeout=5)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"检查依赖失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"检查依赖失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/favorites')
def api_favorites():
    """获取收藏列表（通过主应用）"""
    try:
        # 检查主应用是否在运行
        status = get_main_app_status()
        if not status['running']:
            return jsonify({
                'success': False,
                'message': '主应用未运行，无法获取收藏列表'
            })

        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/favorites"
        admin_logger.info(f"获取收藏列表: {main_app_url}")
        response = requests.get(main_app_url, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"获取收藏列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"获取收藏列表失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/ranking')
def api_ranking():
    """获取排行榜（通过主应用）"""
    try:
        # 检查主应用是否在运行
        status = get_main_app_status()
        if not status['running']:
            return jsonify({
                'success': False,
                'message': '主应用未运行，无法获取排行榜'
            })

        main_app_url = f"http://127.0.0.1:{MAIN_APP_PORT}/api/ranking"
        admin_logger.info(f"获取排行榜: {main_app_url}")
        response = requests.get(main_app_url, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'success': False,
                'message': f'主应用返回错误: {response.status_code}'
            })
    except requests.exceptions.RequestException as e:
        admin_logger.error(f"获取排行榜失败: {e}")
        return jsonify({
            'success': False,
            'message': f'无法连接到主应用: {str(e)}'
        })
    except Exception as e:
        admin_logger.error(f"获取排行榜失败: {e}")
        import traceback
        admin_logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)})


def start_cache_updater():
    """启动后台缓存更新线程"""
    def cache_updater_loop():
        admin_logger.info("服务状态缓存更新线程已启动")
        while True:
            try:
                update_services_cache()
                time.sleep(CACHE_INTERVAL)
            except Exception as e:
                admin_logger.error(f"缓存更新线程异常: {e}")
                time.sleep(5)  # 出错后等待5秒再重试

    thread = threading.Thread(target=cache_updater_loop, daemon=True)
    thread.start()
    admin_logger.info(f"服务状态缓存更新器已启动，刷新间隔: {CACHE_INTERVAL}秒")


if __name__ == '__main__':
    # ========== Windows 服务模式支持 ==========
    # 确保在作为 Windows 服务运行时工作目录正确
    # 服务启动时默认工作目录是 C:\Windows\System32，需要切换到项目目录
    import os
    import sys
    
    # 获取此脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 如果当前工作目录不是脚本所在目录，则切换
    if os.getcwd() != script_dir:
        os.chdir(script_dir)
        admin_logger.info(f"工作目录已设置为: {os.getcwd()}")
    
    # 更新 BASEDIR（确保使用正确的工作目录）
    BASEDIR = script_dir
    
    # 更新所有使用 BASEDIR 的路径
    CONFIG_FILE = os.path.join(BASEDIR, 'config', 'config.json')
    MAIN_APP_PID_FILE = os.path.join(BASEDIR, 'instance', 'main_app.pid')
    DB_FILE = os.path.join(BASEDIR, 'instance', 'dplayer.db')
    
    # 更新 SERVICES 配置中的路径
    SERVICES['main']['script'] = os.path.join(BASEDIR, 'app.py')
    SERVICES['main']['pid_file'] = os.path.join(BASEDIR, 'instance', 'main_app.pid')
    SERVICES['admin']['script'] = os.path.join(BASEDIR, 'admin_app.py')
    SERVICES['admin']['pid_file'] = os.path.join(BASEDIR, 'instance', 'admin_app.pid')
    SERVICES['thumbnail']['script'] = os.path.join(BASEDIR, 'services', 'thumbnail_service.py')
    SERVICES['thumbnail']['pid_file'] = os.path.join(BASEDIR, 'instance', 'thumbnail_app.pid')

    # ========== 启动后台缓存更新器 ==========
    # 初始化一次缓存
    update_services_cache()
    # 启动后台定时更新线程
    start_cache_updater()
    
    # ========== 启动应用 ==========
    # 重新加载配置（确保获取最新的端口配置）
    config = load_config()
    ADMIN_PORT = config.get('ports', {}).get('admin_app', 8080)
    MAIN_APP_PORT = config.get('ports', {}).get('main_app', 80)

    admin_logger.info(f"启动管理后台，端口: {ADMIN_PORT}")
    admin_logger.info(f"工作目录: {os.getcwd()}")

    # 执行系统网络优化（防火墙、TCP、DNS等）
    # admin_logger.info("执行系统网络优化...")
    # try:
    #     optimize_system(
    #         ports=[ADMIN_PORT],
    #         service_names=['管理后台']
    #     )
    # except Exception as e:
    #     admin_logger.warning(f"系统优化失败: {e}")

    # 作为 Windows 服务运行时，跳过端口检查（避免杀死自己的进程）
    is_service = 'windows_service' in os.environ.get('RUN_MODE', '').lower()
    
    if not is_service:
        print(f'[*] 正在检查端口 {ADMIN_PORT}...')
        port_result = ensure_port_available(ADMIN_PORT)

        if port_result['action'] == 'killed':
            print(f'[!] {port_result["message"]}')
            time.sleep(1)  # 等待端口完全释放

        if is_port_in_use(ADMIN_PORT):
            print(f'[!] 错误: 端口 {ADMIN_PORT} 仍然被占用，无法启动管理后台')
            print(f'[!] 请手动检查并终止占用该端口的进程:')
            processes = find_process_using_port(ADMIN_PORT)
            for proc in processes:
                print(f'    - PID: {proc.pid}, Name: {proc.name()}')
            sys.exit(1)

        print(f'[*] Starting Admin Dashboard on {HOST}:{ADMIN_PORT}')
        print(f'[*] Main app port: {MAIN_APP_PORT}')
        print(f'[*] Admin dashboard: http://{HOST}:{ADMIN_PORT}')
        print(f'[*] Main application: http://{HOST}:{MAIN_APP_PORT}')
    else:
        admin_logger.info("以 Windows 服务模式运行")

    # 注意：不使用SQLAlchemy ORM，使用原生SQL查询
    # 数据库表由app.py负责创建
    # 服务模式下禁用 debug，不使用 reloader
    app.run(host=HOST, port=ADMIN_PORT, debug=False, use_reloader=False)