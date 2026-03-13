"""
DPlayer Service Controller - Python版本
使用 win32service API 提供更强大的服务控制功能
"""
import win32service
import win32serviceutil
import win32con
import servicemanager
import sys
import time
from pathlib import Path
import subprocess
import socket


# ============================================================
# 配置
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent.resolve()

SERVICES = {
    'admin': {
        'name': 'DPlayer-Admin',
        'display_name': '管理服务',
        'script': PROJECT_DIR / 'services' / 'admin_service.py',
        'port': 8080,
        'description': 'DPlayer Admin Panel, Port 8080'
    },
    'main': {
        'name': 'DPlayer-Main',
        'display_name': '主应用服务',
        'script': PROJECT_DIR / 'services' / 'main_service.py',
        'port': 80,
        'description': 'DPlayer Main Application, Port 80'
    },
    'thumbnail': {
        'name': 'DPlayer-Thumbnail',
        'display_name': '缩略图服务',
        'script': PROJECT_DIR / 'services' / 'thumbnail_service_win.py',
        'port': 5001,
        'description': 'DPlayer Thumbnail Service, Port 5001'
    }
}


# ============================================================
# 颜色输出
# ============================================================

class Colors:
    """控制台颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(title):
    """打印标题"""
    print(f"\n{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  {title}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    """打印成功消息"""
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message):
    """打印错误消息"""
    print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")


def print_warn(message):
    """打印警告消息"""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message):
    """打印信息消息"""
    print(f"[INFO] {message}")


# ============================================================
# 服务工具函数
# ============================================================

def check_admin_rights():
    """检查管理员权限"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


def get_service_start_type(service_name):
    """获取服务启动类型"""
    try:
        result = subprocess.run(
            ['sc', 'qc', service_name],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'START_TYPE' in line:
                    # START_TYPE: 2 AUTO_START
                    parts = line.split(':')
                    if len(parts) > 1:
                        start_info = parts[1].strip()
                        # 返回类型和名称
                        return start_info
    except:
        pass
    return None


def set_service_start_type(service_name, start_type):
    """设置服务启动类型

    Args:
        service_name: 服务名称
        start_type: 启动类型 ('auto', 'demand', 'disabled')
    """
    try:
        start_type_map = {
            'auto': 'auto',
            'demand': 'demand',
            'disabled': 'disabled'
        }

        if start_type not in start_type_map:
            raise ValueError(f"无效的启动类型: {start_type}")

        result = subprocess.run(
            ['sc', 'config', service_name, f'start={start_type_map[start_type]}'],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=30
        )

        return result.returncode == 0

    except Exception as e:
        raise Exception(f"设置启动类型失败: {e}")


def get_service_status(service_name):
    """获取服务状态"""
    try:
        scm_handle = win32service.OpenSCManager(
            None, None, win32con.GENERIC_READ
        )
        if scm_handle == 0:
            return "NO_ACCESS"

        service_handle = win32service.OpenService(
            scm_handle, service_name, win32con.GENERIC_READ
        )
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


def get_service_pid(service_name):
    """获取服务PID"""
    try:
        result = subprocess.run(
            ['sc', 'queryex', service_name],
            capture_output=True,
            text=True,
            encoding='gbk'
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'PID' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        return parts[1].strip()
    except:
        pass
    return None


def check_port_listening(port):
    """检查端口是否在监听"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False


def wait_for_service_state(service_name, desired_state, timeout=30):
    """等待服务达到指定状态"""
    print_info(f"等待服务变为 {desired_state}...")

    for i in range(timeout):
        state = get_service_status(service_name)
        if state == desired_state:
            print_success(f"服务状态: {state}")
            return True
        if state == "NOT_FOUND":
            print_error("服务未找到")
            return False
        time.sleep(1)

    print_warn(f"等待超时，当前状态: {state}")
    return False


# ============================================================
# 服务操作函数
# ============================================================

def install_service(service_key):
    """安装服务"""
    svc = SERVICES[service_key]
    print_info(f"注册 {svc['display_name']}...")

    # 检查旧服务
    old_status = get_service_status(svc['name'])
    if old_status != "NOT_FOUND":
        print_info("删除旧服务...")
        try:
            uninstall_service(service_key, silent=True)
            time.sleep(2)
        except:
            print_warn("删除旧服务失败，继续...")

    # 使用服务脚本自带的安装功能
    script_path = svc['script']
    if not script_path.exists():
        print_error(f"服务脚本不存在: {script_path}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), 'install'],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=60
        )

        if result.returncode == 0:
            print_success(f"{svc['display_name']} 已注册")
            return True
        else:
            print_error(f"{svc['display_name']} 注册失败")
            print_error(f"错误: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"安装过程异常: {e}")
        return False


def uninstall_service(service_key, silent=False):
    """卸载服务"""
    svc = SERVICES[service_key]

    if not silent:
        print_info(f"卸载 {svc['display_name']}...")

    # 先停止服务
    status = get_service_status(svc['name'])
    if status == "RUNNING":
        stop_service(service_key, silent=True)

    # 删除服务
    try:
        scm_handle = win32service.OpenSCManager(
            None, None, win32con.GENERIC_WRITE
        )
        if scm_handle == 0:
            raise Exception("无法打开服务控制管理器")

        service_handle = win32service.OpenService(
            scm_handle, svc['name'], win32con.DELETE
        )
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            raise Exception("无法打开服务")

        win32service.DeleteService(service_handle)
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        if not silent:
            print_success(f"{svc['display_name']} 已卸载")
        return True

    except Exception as e:
        # 尝试使用 sc.exe
        try:
            result = subprocess.run(
                ['sc', 'delete', svc['name']],
                capture_output=True,
                text=True,
                encoding='gbk',
                timeout=30
            )
            if result.returncode == 0:
                if not silent:
                    print_success(f"{svc['display_name']} 已卸载")
                return True
        except:
            pass

        if not silent:
            print_error(f"{svc['display_name']} 卸载失败: {e}")
        return False


def start_service(service_key):
    """启动服务"""
    svc = SERVICES[service_key]
    print_info(f"启动 {svc['display_name']}...")

    # 检查服务是否存在
    status = get_service_status(svc['name'])
    if status == "NOT_FOUND":
        print_error(f"{svc['display_name']} 未注册，请先运行: service_controller.py install {service_key}")
        return False

    if status == "RUNNING":
        print_info(f"{svc['display_name']} 已经在运行")
        return True

    # 启动服务
    try:
        scm_handle = win32service.OpenSCManager(
            None, None, win32con.GENERIC_EXECUTE
        )
        if scm_handle == 0:
            raise Exception("无法打开服务控制管理器")

        service_handle = win32service.OpenService(
            scm_handle, svc['name'], win32service.SERVICE_START
        )
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            raise Exception("无法打开服务")

        win32service.StartService(service_handle, None)
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        print_success(f"{svc['display_name']} 启动中...")

    except Exception as e:
        print_error(f"{svc['display_name']} 启动失败: {e}")
        return False

    # 等待服务启动
    success = wait_for_service_state(svc['name'], 'RUNNING')
    if success:
        time.sleep(2)

        # 检查端口监听
        listening = check_port_listening(svc['port'])
        if listening:
            print_success(f"{svc['display_name']} 启动成功，端口 {svc['port']} 正在监听")
        else:
            print_warn(f"{svc['display_name']} 已启动但端口 {svc['port']} 未监听，可能还在初始化")

    return success


def stop_service(service_key, silent=False):
    """停止服务"""
    svc = SERVICES[service_key]

    if not silent:
        print_info(f"停止 {svc['display_name']}...")

    # 检查服务是否存在
    status = get_service_status(svc['name'])
    if status == "NOT_FOUND":
        if not silent:
            print_info(f"{svc['display_name']} 未注册，跳过")
        return True

    if status == "STOPPED":
        if not silent:
            print_info(f"{svc['display_name']} 已经停止")
        return True

    # 停止服务
    try:
        scm_handle = win32service.OpenSCManager(
            None, None, win32con.GENERIC_EXECUTE
        )
        if scm_handle == 0:
            raise Exception("无法打开服务控制管理器")

        service_handle = win32service.OpenService(
            scm_handle, svc['name'], win32service.SERVICE_ALL_ACCESS
        )
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            raise Exception("无法打开服务")

        win32service.ControlService(
            service_handle,
            win32service.SERVICE_CONTROL_STOP
        )
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        if not silent:
            print_success(f"{svc['display_name']} 停止中...")

    except Exception as e:
        if not silent:
            print_error(f"{svc['display_name']} 停止失败: {e}")
        return False

    # 等待服务停止
    success = wait_for_service_state(svc['name'], 'STOPPED')
    if success and not silent:
        time.sleep(1)
        listening = check_port_listening(svc['port'])
        if not listening:
            print_success(f"{svc['display_name']} 已停止，端口 {svc['port']} 已释放")
        else:
            print_warn(f"{svc['display_name']} 已停止但端口 {svc['port']} 仍被占用")

    return success


def restart_service(service_key):
    """重启服务"""
    svc = SERVICES[service_key]

    print()
    print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}重启 {svc['display_name']}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")

    # 获取重启前的PID
    old_pid = get_service_pid(svc['name'])
    print_info(f"重启前 PID: {old_pid}")

    # 停止服务
    stop_success = stop_service(service_key)
    if not stop_success:
        print_error("停止失败，无法继续重启")
        return False

    # 等待完全停止
    time.sleep(2)

    # 启动服务
    start_success = start_service(service_key)
    if not start_success:
        print_error("启动失败，重启未完成")
        return False

    # 验证PID变化
    time.sleep(2)
    new_pid = get_service_pid(svc['name'])
    print_info(f"重启后 PID: {new_pid}")

    if old_pid and new_pid and old_pid != new_pid:
        print_success(f"PID 已变更 ({old_pid} -> {new_pid})，服务重启成功！")
    elif old_pid == new_pid:
        print_warn("PID 未变化，服务可能未正确重启")
    else:
        print_info("无法验证PID变化")

    return True


def show_service_status(service_key):
    """显示服务状态"""
    svc = SERVICES[service_key]

    print()
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  {svc['display_name']} ({svc['name']}){Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")

    # 服务注册状态
    status = get_service_status(svc['name'])
    if status == "NOT_FOUND":
        print(f"状态: {Colors.FAIL}[NOT REGISTERED]{Colors.ENDC}")
        print(f"端口: {svc['port']}")
        return

    # 服务运行状态
    if status == "RUNNING":
        print(f"状态: {Colors.OKGREEN}[RUNNING]{Colors.ENDC}")
    elif status == "STOPPED":
        print(f"状态: {Colors.FAIL}[STOPPED]{Colors.ENDC}")
    elif status == "START_PENDING":
        print(f"状态: {Colors.WARNING}[STARTING]{Colors.ENDC}")
    else:
        print(f"状态: {status}")

    # PID信息
    pid = get_service_pid(svc['name'])
    print(f"PID: {pid}")

    # 端口监听
    listening = check_port_listening(svc['port'])
    if listening:
        print(f"端口: {svc['port']} {Colors.OKGREEN}[LISTENING]{Colors.ENDC}")
    else:
        print(f"端口: {svc['port']} {Colors.FAIL}[NOT LISTENING]{Colors.ENDC}")

    # 启动类型
    start_type = get_service_start_type(svc['name'])
    if start_type:
        if 'AUTO_START' in start_type:
            print(f"启动类型: {Colors.OKGREEN}{start_type} (开机自启){Colors.ENDC}")
        elif 'DEMAND_START' in start_type:
            print(f"启动类型: {start_type} (手动)")
        elif 'DISABLED' in start_type:
            print(f"启动类型: {Colors.FAIL}{start_type} (已禁用){Colors.ENDC}")
        else:
            print(f"启动类型: {start_type}")
    else:
        print(f"启动类型: 未知")

    print()


# ============================================================
# 主操作流程
# ============================================================

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        return

    action = sys.argv[1].lower()
    service_arg = sys.argv[2].lower() if len(sys.argv) > 2 else 'all'

    # 确定要操作的服务
    if service_arg == 'all':
        target_services = list(SERVICES.keys())
    else:
        if service_arg not in SERVICES:
            print_error(f"未知的服务: {service_arg}")
            print(f"可用服务: {', '.join(SERVICES.keys())}")
            return
        target_services = [service_arg]

    # 检查管理员权限
    if action in ['install', 'uninstall', 'install-one', 'uninstall-one', 'start', 'stop', 'restart',
                  'autostart-enable', 'autostart-disable']:
        if not check_admin_rights():
            print_error("此操作需要管理员权限！")
            print_info("请以管理员身份运行此脚本")
            sys.exit(1)

    print_header("DPlayer Service Controller")

    # 执行操作
    if action == 'install':
        print_header("注册所有DPlayer服务")
        print()
        print_info("[1/3] 删除旧服务...")
        for key in target_services:
            uninstall_service(key, silent=True)

        print()
        print_info("[2/3] 注册新服务...")
        all_success = True
        for key in target_services:
            success = install_service(key)
            if not success:
                all_success = False
            print()

        if all_success:
            print_header("验证服务注册")
            for key in target_services:
                show_service_status(key)
            print()
            print_success("所有服务注册完成！")
        else:
            print_error("部分服务注册失败，请检查错误信息")

    elif action == 'uninstall':
        print_header("卸载所有DPlayer服务")
        print()

        print_info("[1/2] 停止所有服务...")
        for key in target_services:
            stop_service(key, silent=True)
            print()

        print_info("[2/2] 卸载服务...")
        all_success = True
        for key in target_services:
            success = uninstall_service(key)
            if not success:
                all_success = False
            print()

        if all_success:
            print_success("所有服务卸载完成！")
        else:
            print_error("部分服务卸载失败，请检查错误信息")

    elif action == 'install-one':
        if len(target_services) != 1:
            print_error("install-one 操作只能指定单个服务")
            return

        key = target_services[0]
        print_header("注册单个服务")
        print()

        install_service(key)
        if install_service(key):
            print()
            show_service_status(key)
            print_success("服务注册完成！")

    elif action == 'uninstall-one':
        if len(target_services) != 1:
            print_error("uninstall-one 操作只能指定单个服务")
            return

        key = target_services[0]
        print_header("卸载单个服务")
        print()

        uninstall_service(key)
        print_success("服务卸载完成！")

    elif action == 'start':
        print_header("启动DPlayer服务")
        print()

        all_success = True
        for key in target_services:
            success = start_service(key)
            print()
            if not success:
                all_success = False

        if all_success:
            print_header("验证服务状态")
            for key in target_services:
                show_service_status(key)
        else:
            print_error("部分服务启动失败，请检查错误信息")

    elif action == 'stop':
        print_header("停止DPlayer服务")
        print()

        all_success = True
        for key in target_services:
            success = stop_service(key)
            print()
            if not success:
                all_success = False

        if all_success:
            print_header("验证服务状态")
            for key in target_services:
                show_service_status(key)
        else:
            print_error("部分服务停止失败，请检查错误信息")

    elif action == 'restart':
        print_header("重启DPlayer服务")
        print()

        all_success = True
        for key in target_services:
            success = restart_service(key)
            print()
            if not success:
                all_success = False

        if all_success:
            print_header("验证服务状态")
            for key in target_services:
                show_service_status(key)
            print_success("所有服务重启完成！")
        else:
            print_error("部分服务重启失败，请检查错误信息")

    elif action == 'status':
        print_header("DPlayer服务状态")

        for key in target_services:
            show_service_status(key)

        # 统计摘要
        running_count = 0
        stopped_count = 0
        not_registered_count = 0

        for key in target_services:
            status = get_service_status(SERVICES[key]['name'])
            if status == 'RUNNING':
                running_count += 1
            elif status == 'STOPPED':
                stopped_count += 1
            else:
                not_registered_count += 1

        print()
        print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}  摘要统计{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
        print(f"运行中: {Colors.OKGREEN}{running_count}{Colors.ENDC}")
        print(f"已停止: {stopped_count}")
        print(f"未注册: {not_registered_count}")

    elif action == 'autostart-enable':
        print_header("启用开机自启动")
        print()

        all_success = True
        for key in target_services:
            svc = SERVICES[key]
            print_info(f"设置 {svc['display_name']} 为开机自启动...")

            try:
                success = set_service_start_type(svc['name'], 'auto')
                if success:
                    print_success(f"{svc['display_name']} 已设置为开机自启动")
                else:
                    print_error(f"{svc['display_name']} 设置失败")
                    all_success = False
            except Exception as e:
                print_error(f"{svc['display_name']} 设置失败: {e}")
                all_success = False
            print()

        if all_success:
            print_header("验证启动配置")
            for key in target_services:
                show_service_status(key)
            print_success("所有服务已启用开机自启动！")
        else:
            print_error("部分服务设置失败，请检查错误信息")

    elif action == 'autostart-disable':
        print_header("禁用开机自启动")
        print()

        all_success = True
        for key in target_services:
            svc = SERVICES[key]
            print_info(f"设置 {svc['display_name']} 为手动启动...")

            try:
                success = set_service_start_type(svc['name'], 'demand')
                if success:
                    print_success(f"{svc['display_name']} 已设置为手动启动")
                else:
                    print_error(f"{svc['display_name']} 设置失败")
                    all_success = False
            except Exception as e:
                print_error(f"{svc['display_name']} 设置失败: {e}")
                all_success = False
            print()

        if all_success:
            print_header("验证启动配置")
            for key in target_services:
                show_service_status(key)
            print_success("所有服务已禁用开机自启动！")
        else:
            print_error("部分服务设置失败，请检查错误信息")

    elif action == 'autostart-status':
        print_header("开机自启动状态")

        autostart_count = 0
        manual_count = 0
        disabled_count = 0
        unknown_count = 0

        for key in target_services:
            svc = SERVICES[key]

            print()
            print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}  {svc['display_name']} ({svc['name']}){Colors.ENDC}")
            print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")

            start_type = get_service_start_type(svc['name'])
            if start_type:
                if 'AUTO_START' in start_type:
                    print(f"启动类型: {Colors.OKGREEN}{start_type} (开机自启){Colors.ENDC}")
                    autostart_count += 1
                elif 'DEMAND_START' in start_type:
                    print(f"启动类型: {start_type} (手动启动)")
                    manual_count += 1
                elif 'DISABLED' in start_type:
                    print(f"启动类型: {Colors.FAIL}{start_type} (已禁用){Colors.ENDC}")
                    disabled_count += 1
                else:
                    print(f"启动类型: {start_type}")
                    unknown_count += 1
            else:
                print(f"启动类型: 未知")
                unknown_count += 1

            print()

        # 统计摘要
        print()
        print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}  摘要统计{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
        print(f"开机自启: {Colors.OKGREEN}{autostart_count}{Colors.ENDC}")
        print(f"手动启动: {manual_count}")
        print(f"已禁用: {disabled_count}")
        print(f"未知状态: {unknown_count}")

    else:
        print_help()


def print_help():
    """打印帮助信息"""
    print()
    print(f"{Colors.HEADER}DPlayer Service Controller - Python版本{Colors.ENDC}")
    print()
    print(f"用法: {sys.argv[0]} [操作] [服务]")
    print()
    print(f"  {Colors.OKCYAN}[操作]{Colors.ENDC}:")
    print(f"    install           - 注册所有DPlayer服务")
    print(f"    uninstall         - 卸载所有DPlayer服务")
    print(f"    install-one       - 注册单个服务")
    print(f"    uninstall-one     - 卸载单个服务")
    print(f"    start             - 启动服务")
    print(f"    stop              - 停止服务")
    print(f"    restart           - 重启服务")
    print(f"    status            - 查询服务状态")
    print(f"    autostart-enable  - 启用开机自启动")
    print(f"    autostart-disable - 禁用开机自启动")
    print(f"    autostart-status  - 查看开机自启动状态")
    print()
    print(f"  {Colors.OKCYAN}[服务]{Colors.ENDC}:")
    print(f"    admin             - 管理服务 ({SERVICES['admin']['name']})")
    print(f"    main              - 主应用服务 ({SERVICES['main']['name']})")
    print(f"    thumbnail         - 缩略图服务 ({SERVICES['thumbnail']['name']})")
    print(f"    all               - 所有DPlayer服务(默认)")
    print()
    print(f"  {Colors.OKCYAN}示例{Colors.ENDC}:")
    print(f"    {sys.argv[0]} install")
    print(f"    {sys.argv[0]} start all")
    print(f"    {sys.argv[0]} restart admin")
    print(f"    {sys.argv[0]} status")
    print(f"    {sys.argv[0]} autostart-enable")
    print(f"    {sys.argv[0]} autostart-status")
    print(f"    {sys.argv[0]} autostart-disable main")
    print()
    print(f"{Colors.WARNING}注意: 需要 {Colors.ENDC}管理员权限{Colors.WARNING} 运行此脚本{Colors.ENDC}")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print_error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
