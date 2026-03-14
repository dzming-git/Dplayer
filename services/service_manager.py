"""
DPlayer统一服务管理器
提供通用的服务启动/停止/重启接口,供admin_app.py和service_controller.py共同使用
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# psutil用于进程和端口管理
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Windows特定导入
IS_WINDOWS = os.name == 'nt'
if IS_WINDOWS:
    try:
        import win32service
        import win32serviceutil
        import win32con
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

# 获取项目根目录
PROJECT_DIR = Path(__file__).parent.parent.resolve()
BASEDIR = str(PROJECT_DIR)
LOG_DIR = os.path.join(BASEDIR, 'logs')

# 配置日志
service_logger = logging.getLogger('service_manager')
service_logger.setLevel(logging.INFO)
if not service_logger.handlers:
    handler = logging.FileHandler(os.path.join(LOG_DIR, 'service_manager.log'), encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    service_logger.addHandler(handler)


# ============================================================
# 配置加载
# ============================================================

def load_config():
    """加载配置文件"""
    config_path = PROJECT_DIR / 'config' / 'config.json'
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        service_logger.warning(f"加载配置文件失败: {e}")
        return {}

config = load_config()

# 服务定义
SERVICES = {
    'admin': {
        'name': 'DPlayer-Admin',
        'display_name': '管理服务',
        'port': config.get('ports', {}).get('admin_app', 8080),
        'script': os.path.join(BASEDIR, 'admin_app.py'),
        'pid_file': os.path.join(BASEDIR, '.admin.pid'),
    },
    'main': {
        'name': 'DPlayer-Main',
        'display_name': '主应用',
        'port': config.get('ports', {}).get('main_app', 8081),
        'script': os.path.join(BASEDIR, 'app.py'),
        'pid_file': os.path.join(BASEDIR, '.main.pid'),
    },
    'thumbnail': {
        'name': 'DPlayer-Thumbnail',
        'display_name': '缩略图服务',
        'port': config.get('ports', {}).get('thumbnail', 5001),
        'script': os.path.join(BASEDIR, 'thumbnail_service.py'),
        'pid_file': os.path.join(BASEDIR, '.thumbnail.pid'),
    }
}


# ============================================================
# 辅助函数
# ============================================================

def _port_listening(port):
    """检查端口是否在监听"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False


def _pid_for_port(port):
    """获取占用端口的进程PID"""
    if not HAS_PSUTIL:
        return None

    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                return conn.pid
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    except:
        pass

    return None


def _get_pid_from_file(pid_file):
    """从PID文件读取进程ID"""
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return None


def _get_processes_using_port(port):
    """获取占用指定端口的进程列表"""
    if not HAS_PSUTIL:
        service_logger.warning("psutil未安装，无法查询进程信息")
        return []

    processes = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                pid = conn.pid
                if pid is None:
                    continue

                try:
                    proc = psutil.Process(pid)
                    processes.append({
                        'pid': pid,
                        'name': proc.name(),
                        'cmdline': " ".join(proc.cmdline())[:120] if proc.cmdline() else "",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    processes.append({'pid': pid, 'name': '?', 'cmdline': ''})
    except psutil.AccessDenied:
        service_logger.warning("权限不足，无法查询网络连接")
    except Exception as e:
        service_logger.warning(f"查询端口进程失败: {e}")

    return processes


def _kill_processes_on_port(port):
    """强制终止占用端口的进程"""
    if not HAS_PSUTIL:
        return False, "psutil未安装"

    processes = _get_processes_using_port(port)
    if not processes:
        return True, "端口未被占用"

    success_count = 0
    for proc_info in processes:
        try:
            proc = psutil.Process(proc_info['pid'])
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
            success_count += 1
            service_logger.info(f"已终止进程 {proc_info['name']} (PID: {proc_info['pid']})")
        except Exception as e:
            service_logger.warning(f"终止进程 {proc_info['pid']} 失败: {e}")

    time.sleep(1)

    # 验证端口是否已释放
    if _port_listening(port):
        return False, f"部分进程未能终止，端口仍被占用"
    else:
        return True, f"已终止 {success_count}/{len(processes)} 个进程"


# ============================================================
# 核心服务管理函数
# ============================================================

def start_service(svc_key, force=False, silent=False):
    """
    启动指定服务

    Args:
        svc_key: 服务键名 ('admin', 'main', 'thumbnail')
        force: 是否强制启动（忽略端口冲突）
        silent: 静默模式（减少日志输出）

    Returns:
        dict: {'success': bool, 'message': str, 'pid': int|None}
    """
    if svc_key not in SERVICES:
        return {'success': False, 'message': f'未知服务: {svc_key}'}

    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']
    script = svc['script']

    if not silent:
        service_logger.info(f"准备启动服务: {svc['display_name']} (端口: {port})")

    # 检查端口是否被占用
    if _port_listening(port):
        pid_for_port = _pid_for_port(port)
        service_pid = _get_pid_from_file(pid_file)

        # 如果是自己的进程，说明已在运行
        if service_pid and pid_for_port == service_pid:
            if not silent:
                service_logger.info(f"服务 {svc['display_name']} 已在运行 (PID: {service_pid})")
            return {'success': True, 'message': f'{svc["display_name"]} 已在运行', 'pid': service_pid}

        # 端口被其他进程占用
        port_processes = _get_processes_using_port(port)

        if not force:
            if not silent:
                service_logger.warning(f"端口 {port} 已被占用")
            return {
                'success': False,
                'message': f'端口 {port} 已被占用',
                'port_conflict': True,
                'port': port,
                'processes': port_processes
            }

        # 强制模式：终止占用进程
        if not silent:
            service_logger.info(f"强制模式：清理端口 {port} 占用")
        success, msg = _kill_processes_on_port(port)
        if not success:
            return {'success': False, 'message': f'清理端口失败: {msg}'}
        if not silent:
            service_logger.info(f"端口 {port} 已清理: {msg}")

        time.sleep(1)  # 等待端口完全释放

    # 启动进程
    try:
        # 设置环境变量
        env = os.environ.copy()
        if svc_key == 'thumbnail':
            env['THUMBNAIL_SERVICE_PORT'] = str(port)

        # 创建日志目录
        os.makedirs(LOG_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)

        # 创建启动日志
        startup_log = os.path.join(LOG_DIR, f'{svc_key}_startup.log')
        with open(startup_log, 'w', encoding='utf-8') as f:
            f.write(f"=== 启动服务: {svc['display_name']} ===\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"脚本: {script}\n")
            f.write(f"端口: {port}\n")
            f.write(f"工作目录: {BASEDIR}\n")
            f.write(f"Python: {sys.executable}\n\n")

        # 打开标准输出和错误文件
        stdout_file = open(os.path.join(LOG_DIR, f'{svc_key}_stdout.log'), 'w', encoding='utf-8')
        stderr_file = open(os.path.join(LOG_DIR, f'{svc_key}_stderr.log'), 'w', encoding='utf-8')

        # 启动子进程
        if not silent:
            service_logger.info(f"启动命令: python {script}")
            service_logger.info(f"工作目录: {BASEDIR}")

        creation_flags = 0
        if IS_WINDOWS:
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(
            [sys.executable, script],
            cwd=BASEDIR,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
            creationflags=creation_flags
        )

        # 立即关闭文件句柄（子进程已继承）
        stdout_file.close()
        stderr_file.close()

        # 写入PID文件
        with open(pid_file, 'w') as f:
            f.write(str(proc.pid))

        if not silent:
            service_logger.info(f"进程已启动: PID={proc.pid}")

        # 等待0.5秒，检查进程是否立即退出
        time.sleep(0.5)
        if not psutil.pid_exists(proc.pid):
            error_log = os.path.join(LOG_DIR, f'{svc_key}_stderr.log')
            error_msg = "进程启动后立即退出"
            if os.path.exists(error_log):
                try:
                    with open(error_log, 'r', encoding='utf-8') as f:
                        error_content = f.read()
                    error_msg += f"\n错误日志: {error_content}"
                except:
                    pass
            service_logger.error(f"启动失败: {error_msg}")
            return {'success': False, 'message': error_msg}

        # 等待端口就绪（最多10秒）
        if not silent:
            service_logger.info(f"等待端口 {port} 就绪...")
        for i in range(20):
            time.sleep(0.5)
            if _port_listening(port):
                if not silent:
                    service_logger.info(f"服务 {svc['display_name']} 启动成功 (PID: {proc.pid}, 端口: {port})")
                return {'success': True, 'message': f'{svc["display_name"]} 启动成功', 'pid': proc.pid}

        # 端口未就绪
        if not psutil.pid_exists(proc.pid):
            error_msg = "启动失败，进程已退出"
            service_logger.error(error_msg)
            return {'success': False, 'message': error_msg}
        else:
            msg = f"进程已启动但端口未就绪"
            service_logger.warning(msg)
            return {'success': True, 'message': msg, 'pid': proc.pid, 'port_ready': False}

    except Exception as e:
        error_msg = f"启动失败: {str(e)}"
        service_logger.error(error_msg, exc_info=True)
        return {'success': False, 'message': error_msg}


def stop_service(svc_key, silent=False):
    """
    停止指定服务

    Args:
        svc_key: 服务键名
        silent: 静默模式

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if svc_key not in SERVICES:
        return {'success': False, 'message': f'未知服务: {svc_key}'}

    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']

    if not silent:
        service_logger.info(f"准备停止服务: {svc['display_name']}")

    # 获取进程PID
    pid = _pid_for_port(port) or _get_pid_from_file(pid_file)

    if not pid:
        if not silent:
            service_logger.info(f"服务 {svc['display_name']} 未在运行")
        return {'success': True, 'message': f'{svc["display_name"]} 未在运行'}

    try:
        proc = psutil.Process(pid)
        if not silent:
            service_logger.info(f"终止进程: PID={pid}")

        proc.terminate()
        try:
            proc.wait(timeout=8)
        except psutil.TimeoutExpired:
            if not silent:
                service_logger.warning(f"进程未响应terminate，使用kill")
            proc.kill()
            proc.wait(timeout=3)

        # 清理PID文件
        if os.path.exists(pid_file):
            os.remove(pid_file)

        if not silent:
            service_logger.info(f"服务 {svc['display_name']} 已停止 (PID: {pid})")
        return {'success': True, 'message': f'{svc["display_name"]} 已停止'}

    except psutil.NoSuchProcess:
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return {'success': True, 'message': f'{svc["display_name"]} 进程已不存在'}
    except Exception as e:
        error_msg = f"停止失败: {str(e)}"
        service_logger.error(error_msg, exc_info=True)
        return {'success': False, 'message': error_msg}


def restart_service(svc_key, force=False, silent=False):
    """
    重启指定服务

    Args:
        svc_key: 服务键名
        force: 是否强制启动
        silent: 静默模式

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if svc_key not in SERVICES:
        return {'success': False, 'message': f'未知服务: {svc_key}'}

    svc = SERVICES[svc_key]

    if not silent:
        service_logger.info(f"准备重启服务: {svc['display_name']}")

    # 停止服务
    stop_result = stop_service(svc_key, silent=silent)
    if not stop_result['success']:
        return stop_result

    # 等待端口释放
    if _port_listening(svc['port']):
        time.sleep(1)

    # 启动服务
    start_result = start_service(svc_key, force=force, silent=silent)

    if start_result['success']:
        if not silent:
            service_logger.info(f"服务 {svc['display_name']} 重启成功")
        return {'success': True, 'message': f'{svc["display_name"]} 重启成功', 'pid': start_result.get('pid')}
    else:
        return start_result


def get_service_status(svc_key):
    """
    获取服务状态

    Args:
        svc_key: 服务键名

    Returns:
        dict: {'running': bool, 'pid': int|None, 'port': int, 'port_listening': bool}
    """
    if svc_key not in SERVICES:
        return {'running': False, 'error': f'未知服务: {svc_key}'}

    svc = SERVICES[svc_key]
    port = svc['port']
    pid_file = svc['pid_file']

    pid = _pid_for_port(port) or _get_pid_from_file(pid_file)
    port_listening = _port_listening(port)

    return {
        'running': port_listening,
        'pid': pid,
        'port': port,
        'port_listening': port_listening,
        'name': svc['display_name'],
        'script': svc['script']
    }


def get_all_services_status():
    """获取所有服务状态"""
    return {key: get_service_status(key) for key in SERVICES.keys()}


# ============================================================
# Windows服务管理函数（可选，用于service_controller.py）
# ============================================================

def get_service_status_win(service_name):
    """获取Windows服务状态"""
    if not HAS_WIN32:
        return "NOT_SUPPORTED"

    try:
        scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_READ)
        if scm_handle == 0:
            return "NO_ACCESS"

        service_handle = win32service.OpenService(scm_handle, service_name, win32con.GENERIC_READ)
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            return "NOT_FOUND"

        status = win32service.QueryServiceStatus(service_handle)
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        state_map = {
            win32service.SERVICE_STOPPED: 'STOPPED',
            win32service.SERVICE_START_PENDING: 'START_PENDING',
            win32service.SERVICE_STOP_PENDING: 'STOP_PENDING',
            win32service.SERVICE_RUNNING: 'RUNNING',
            win32service.SERVICE_CONTINUE_PENDING: 'CONTINUE_PENDING',
            win32service.SERVICE_PAUSE_PENDING: 'PAUSE_PENDING',
            win32service.SERVICE_PAUSED: 'PAUSED'
        }

        return state_map.get(status[1], 'UNKNOWN')

    except Exception as e:
        return f"ERROR: {str(e)}"


def start_service_win(service_name):
    """启动Windows服务"""
    if not HAS_WIN32:
        return False, "pywin32未安装"

    try:
        scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_EXECUTE)
        if scm_handle == 0:
            return False, "无法打开服务控制管理器"

        service_handle = win32service.OpenService(scm_handle, service_name, win32service.SERVICE_START)
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            return False, "无法打开服务"

        win32service.StartService(service_handle, None)
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        return True, "服务启动中"
    except Exception as e:
        return False, str(e)


def stop_service_win(service_name):
    """停止Windows服务"""
    if not HAS_WIN32:
        return False, "pywin32未安装"

    try:
        scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_EXECUTE)
        if scm_handle == 0:
            return False, "无法打开服务控制管理器"

        service_handle = win32service.OpenService(scm_handle, service_name, win32service.SERVICE_ALL_ACCESS)
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            return False, "无法打开服务"

        win32service.ControlService(service_handle, win32service.SERVICE_CONTROL_STOP)
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        return True, "服务停止中"
    except Exception as e:
        return False, str(e)


# ============================================================
# 导出的公共接口
# ============================================================

__all__ = [
    'SERVICES',
    'start_service',
    'stop_service',
    'restart_service',
    'get_service_status',
    'get_all_services_status',
    'get_service_status_win',
    'start_service_win',
    'stop_service_win',
]
