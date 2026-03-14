"""DPlayer Service Controller - Cross-Platform Version
Unified service management for Windows and Linux
"""
import sys
import time
from pathlib import Path
import subprocess
import socket
import json
import platform
import os
import argparse

# Detect platform
IS_WINDOWS = platform.system() == 'Windows'

# Platform-specific imports
if IS_WINDOWS:
    try:
        import win32service
        import win32serviceutil
        import win32con
        import servicemanager
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

# psutil for port and process management
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ============================================================
# Configuration
# ============================================================

PROJECT_DIR = Path(__file__).parent.parent.resolve()

# Load configuration
def load_config():
    config_path = PROJECT_DIR / 'config' / 'config.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

config = load_config()
ADMIN_PORT = config.get('ports', {}).get('admin_app', 8080)
MAIN_APP_PORT = config.get('ports', {}).get('main_app', 8081)
THUMBNAIL_PORT = config.get('ports', {}).get('thumbnail', 5001)

# Service definitions
SERVICES = {
    'admin': {
        'name': 'DPlayer-Admin',
        'display_name': 'Admin Service',
        'port': ADMIN_PORT,
        'description': f'DPlayer Admin Panel, Port {ADMIN_PORT}'
    },
    'main': {
        'name': 'DPlayer-Main',
        'display_name': 'Main Service',
        'port': MAIN_APP_PORT,
        'description': f'DPlayer Main Application, Port {MAIN_APP_PORT}'
    },
    'thumbnail': {
        'name': 'DPlayer-Thumbnail',
        'display_name': 'Thumbnail Service',
        'port': THUMBNAIL_PORT,
        'description': f'DPlayer Thumbnail Service, Port {THUMBNAIL_PORT}'
    }
}


# ============================================================
# Console Colors
# ============================================================

class Colors:
    """Console color codes"""
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
    """Print section header"""
    print(f"\n{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  {title}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}\n")


def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}[OK] {message}{Colors.ENDC}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")


def print_warn(message):
    """Print warning message"""
    print(f"{Colors.WARNING}[WARN] {message}{Colors.ENDC}")


def print_info(message):
    """Print info message"""
    print(f"[INFO] {message}")


# ============================================================
# Platform Detection and Permissions
# ============================================================

def check_admin_rights():
    """Check if running with admin/root privileges"""
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        return os.geteuid() == 0


# ============================================================
# Port Management Functions (from kill_ports.py)
# ============================================================

def find_pids_for_port(port: int):
    """Find all processes using the specified port"""
    if not HAS_PSUTIL:
        print_error("psutil not installed. Install with: pip install psutil")
        return []

    result = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                pid = conn.pid
                if pid is None:
                    continue
                try:
                    proc = psutil.Process(pid)
                    result.append({
                        "pid": pid,
                        "name": proc.name(),
                        "cmdline": " ".join(proc.cmdline())[:120],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    result.append({"pid": pid, "name": "?", "cmdline": ""})
    except psutil.AccessDenied:
        print_warn("Insufficient permissions to query network connections")
    return result


def kill_pid(pid: int):
    """Kill a process by PID"""
    if not HAS_PSUTIL:
        print_error("psutil not installed")
        return False

    try:
        proc = psutil.Process(pid)
        proc.kill()
        proc.wait(timeout=5)
        return True
    except psutil.NoSuchProcess:
        return True  # Already gone, consider it success
    except psutil.AccessDenied:
        print_error(f"Access denied to kill PID {pid} (requires admin/root privileges)")
        return False
    except Exception as e:
        print_error(f"Failed to kill PID {pid}: {e}")
        return False


def get_service_port(service_key):
    """Get port for a service by name"""
    if service_key in SERVICES:
        return SERVICES[service_key]['port']
    return None


def clear_port(service_key, force=False, dry_run=False):
    """Clear port for a specific service"""
    port = get_service_port(service_key)
    if port is None:
        print_error(f"Unknown service: {service_key}")
        return False

    svc = SERVICES[service_key]
    print_info(f"Checking port {port} for {svc['display_name']}...")

    pids = find_pids_for_port(port)

    if not pids:
        print_success(f"Port {port} is free")
        return True

    # Port is occupied
    print_warn(f"Port {port} is occupied by {len(pids)} process(es):")
    for p in pids:
        print(f"  PID {p['pid']}  {p['name']}")
        if p["cmdline"]:
            print(f"  CMD {p['cmdline']}")

    if dry_run:
        print_info("Dry-run mode: no actions taken")
        return True

    if force:
        # Kill without confirmation
        for p in pids:
            ok = kill_pid(p["pid"])
            status = "[killed]" if ok else "[FAILED]"
            print(f"  -> PID {p['pid']} {status}")
    else:
        # Interactive confirmation
        try:
            ans = input(f"  Kill {len(pids)} process(es)? [y/N] ").strip().lower()
        except EOFError:
            ans = 'n'

        if ans == "y":
            for p in pids:
                ok = kill_pid(p["pid"])
                status = Colors.OKGREEN + "[killed]" + Colors.ENDC if ok else Colors.FAIL + "[FAILED]" + Colors.ENDC
                print(f"  -> PID {p['pid']} {status}")
        else:
            print_info("Skipped")
            return False

    # Wait a moment and verify
    time.sleep(1)
    pids_after = find_pids_for_port(port)
    if not pids_after:
        print_success(f"Port {port} is now free")
        return True
    else:
        print_warn(f"Port {port} still occupied by {len(pids_after)} process(es)")
        return False


def clear_ports_all(force=False, dry_run=False):
    """Clear all DPlayer service ports"""
    print_header("Clear All DPlayer Ports")

    all_cleared = True
    for service_key in SERVICES.keys():
        print()
        if not clear_port(service_key, force=force, dry_run=dry_run):
            all_cleared = False

    print()
    if all_cleared:
        print_success("All ports cleared successfully!")
    else:
        print_warn("Some ports could not be cleared")

    return all_cleared


def clear_port_by_number(port, force=False, dry_run=False):
    """Clear a specific port by number"""
    print_info(f"Checking port {port}...")

    pids = find_pids_for_port(port)

    if not pids:
        print_success(f"Port {port} is free")
        return True

    # Port is occupied
    print_warn(f"Port {port} is occupied by {len(pids)} process(es):")
    for p in pids:
        print(f"  PID {p['pid']}  {p['name']}")
        if p["cmdline"]:
            print(f"  CMD {p['cmdline']}")

    if dry_run:
        print_info("Dry-run mode: no actions taken")
        return True

    if force:
        # Kill without confirmation
        for p in pids:
            ok = kill_pid(p["pid"])
            status = "[killed]" if ok else "[FAILED]"
            print(f"  -> PID {p['pid']} {status}")
    else:
        # Interactive confirmation
        try:
            ans = input(f"  Kill {len(pids)} process(es)? [y/N] ").strip().lower()
        except EOFError:
            ans = 'n'

        if ans == "y":
            for p in pids:
                ok = kill_pid(p["pid"])
                status = Colors.OKGREEN + "[killed]" + Colors.ENDC if ok else Colors.FAIL + "[FAILED]" + Colors.ENDC
                print(f"  -> PID {p['pid']} {status}")
        else:
            print_info("Skipped")
            return False

    # Wait a moment and verify
    time.sleep(1)
    pids_after = find_pids_for_port(port)
    if not pids_after:
        print_success(f"Port {port} is now free")
        return True
    else:
        print_warn(f"Port {port} still occupied by {len(pids_after)} process(es)")
        return False


# ============================================================
# Windows Service Management Functions
# ============================================================

def get_service_status_win(service_name):
    """Get Windows service status"""
    if not HAS_WIN32:
        return "NOT_SUPPORTED"

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


def get_service_pid_win(service_name):
    """Get Windows service PID"""
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


def get_service_start_type_win(service_name):
    """Get Windows service start type"""
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
                    parts = line.split(':')
                    if len(parts) > 1:
                        return parts[1].strip()
    except:
        pass
    return None


def set_service_start_type_win(service_name, start_type):
    """Set Windows service start type"""
    try:
        start_type_map = {
            'auto': 'auto',
            'demand': 'demand',
            'disabled': 'disabled'
        }

        if start_type not in start_type_map:
            raise ValueError(f"Invalid start type: {start_type}")

        result = subprocess.run(
            ['sc', 'config', service_name, f'start={start_type_map[start_type]}'],
            capture_output=True,
            text=True,
            encoding='gbk',
            timeout=30
        )

        return result.returncode == 0

    except Exception as e:
        raise Exception(f"Failed to set start type: {e}")


def start_service_win(service_name, display_name):
    """Start Windows service"""
    if not HAS_WIN32:
        print_error("pywin32 not installed")
        return False

    # Check if service exists
    status = get_service_status_win(service_name)
    if status == "NOT_FOUND":
        print_error(f"{display_name} not registered")
        return False

    if status == "RUNNING":
        print_info(f"{display_name} already running")
        return True

    try:
        scm_handle = win32service.OpenSCManager(
            None, None, win32con.GENERIC_EXECUTE
        )
        if scm_handle == 0:
            raise Exception("Cannot open service control manager")

        service_handle = win32service.OpenService(
            scm_handle, service_name, win32service.SERVICE_START
        )
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            raise Exception("Cannot open service")

        win32service.StartService(service_handle, None)
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        print_success(f"{display_name} starting...")
        return True

    except Exception as e:
        print_error(f"{display_name} start failed: {e}")
        return False


def stop_service_win(service_name, display_name, silent=False):
    """Stop Windows service"""
    if not HAS_WIN32:
        if not silent:
            print_error("pywin32 not installed")
        return False

    # Check if service exists
    status = get_service_status_win(service_name)
    if status == "NOT_FOUND":
        if not silent:
            print_info(f"{display_name} not registered, skipping")
        return True

    if status == "STOPPED":
        if not silent:
            print_info(f"{display_name} already stopped")
        return True

    try:
        scm_handle = win32service.OpenSCManager(
            None, None, win32con.GENERIC_EXECUTE
        )
        if scm_handle == 0:
            raise Exception("Cannot open service control manager")

        service_handle = win32service.OpenService(
            scm_handle, service_name, win32service.SERVICE_ALL_ACCESS
        )
        if service_handle == 0:
            win32service.CloseServiceHandle(scm_handle)
            raise Exception("Cannot open service")

        win32service.ControlService(
            service_handle,
            win32service.SERVICE_CONTROL_STOP
        )
        win32service.CloseServiceHandle(service_handle)
        win32service.CloseServiceHandle(scm_handle)

        if not silent:
            print_success(f"{display_name} stopping...")
        return True

    except Exception as e:
        if not silent:
            print_error(f"{display_name} stop failed: {e}")
        return False


# ============================================================
# Linux Service Management Functions (systemd)
# ============================================================

def get_service_status_linux(service_name):
    """Get Linux systemd service status"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return result.stdout.strip()
        elif result.returncode == 3:
            return "STOPPED"
        else:
            return "NOT_FOUND"
    except:
        return "ERROR"


def get_service_pid_linux(service_name):
    """Get Linux service PID"""
    try:
        result = subprocess.run(
            ['systemctl', 'show', '--property', 'MainPID', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('MainPID='):
                    pid = line.split('=')[1].strip()
                    return pid if pid != '0' else None
    except:
        pass
    return None


def get_service_start_type_linux(service_name):
    """Get Linux service start type"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-enabled', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except:
        return None


def set_service_start_type_linux(service_name, start_type):
    """Set Linux service start type"""
    try:
        if start_type == 'auto':
            subprocess.run(
                ['systemctl', 'enable', service_name],
                capture_output=True,
                timeout=10
            )
        elif start_type == 'demand':
            subprocess.run(
                ['systemctl', 'disable', service_name],
                capture_output=True,
                timeout=10
            )
        else:
            raise ValueError(f"Invalid start type: {start_type}")

        return True
    except Exception as e:
        raise Exception(f"Failed to set start type: {e}")


def start_service_linux(service_name, display_name):
    """Start Linux systemd service"""
    try:
        # Check if service exists
        status = get_service_status_linux(service_name)
        if status == "NOT_FOUND":
            print_error(f"{display_name} not registered")
            return False

        if status == "active":
            print_info(f"{display_name} already running")
            return True

        result = subprocess.run(
            ['systemctl', 'start', service_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success(f"{display_name} starting...")
            return True
        else:
            print_error(f"{display_name} start failed: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"{display_name} start failed: {e}")
        return False


def stop_service_linux(service_name, display_name, silent=False):
    """Stop Linux systemd service"""
    try:
        # Check if service exists
        status = get_service_status_linux(service_name)
        if status == "NOT_FOUND":
            if not silent:
                print_info(f"{display_name} not registered, skipping")
            return True

        if status == "inactive" or status == "STOPPED":
            if not silent:
                print_info(f"{display_name} already stopped")
            return True

        result = subprocess.run(
            ['systemctl', 'stop', service_name],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            if not silent:
                print_success(f"{display_name} stopping...")
            return True
        else:
            if not silent:
                print_error(f"{display_name} stop failed: {result.stderr}")
            return False

    except Exception as e:
        if not silent:
            print_error(f"{display_name} stop failed: {e}")
        return False


# ============================================================
# Cross-Platform Utility Functions
# ============================================================

def check_port_listening(port):
    """Check if port is listening"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False


def wait_for_service_state(service_name, desired_state, timeout=30):
    """Wait for service to reach desired state"""
    print_info(f"Waiting for service to reach {desired_state}...")

    for i in range(timeout):
        if IS_WINDOWS:
            state = get_service_status_win(service_name)
        else:
            state = get_service_status_linux(service_name)

        if state == desired_state or (desired_state == 'RUNNING' and state == 'active'):
            print_success(f"Service status: {state}")
            return True
        if state == "NOT_FOUND":
            print_error("Service not found")
            return False
        time.sleep(1)

    print_warn(f"Timeout waiting, current state: {state}")
    return False


def get_service_status(service_name):
    """Get service status (cross-platform)"""
    if IS_WINDOWS:
        return get_service_status_win(service_name)
    else:
        return get_service_status_linux(service_name)


def get_service_pid(service_name):
    """Get service PID (cross-platform)"""
    if IS_WINDOWS:
        return get_service_pid_win(service_name)
    else:
        return get_service_pid_linux(service_name)


def get_service_start_type(service_name):
    """Get service start type (cross-platform)"""
    if IS_WINDOWS:
        return get_service_start_type_win(service_name)
    else:
        return get_service_start_type_linux(service_name)


def start_service(service_key, force=False):
    """Start service (cross-platform)"""
    svc = SERVICES[service_key]
    print_info(f"Starting {svc['display_name']}...")

    # Check if service exists
    status = get_service_status(svc['name'])
    if status == "NOT_FOUND":
        print_error(f"{svc['display_name']} not registered")
        return False

    if status == "RUNNING" or status == "active":
        print_info(f"{svc['display_name']} already running")
        return True

    # Check if port is occupied
    port = svc['port']
    pids = find_pids_for_port(port)
    if pids:
        print_warn(f"Port {port} is occupied by {len(pids)} process(es):")
        for p in pids:
            print(f"  PID {p['pid']}  {p['name']}")
            if p["cmdline"]:
                print(f"  CMD {p['cmdline']}")

        if force:
            # Force mode: kill without asking
            print_info("Force mode: killing processes...")
            for p in pids:
                ok = kill_pid(p["pid"])
                status_msg = "[killed]" if ok else "[FAILED]"
                print(f"  -> PID {p['pid']} {status_msg}")

            # Wait a moment
            time.sleep(1)
            pids_after = find_pids_for_port(port)
            if pids_after:
                print_error(f"Failed to clear port {port}")
                return False
            else:
                print_success(f"Port {port} cleared")
        else:
            # Interactive mode: ask user
            try:
                ans = input(f"  Kill {len(pids)} process(es) and start service? [y/N] ").strip().lower()
            except EOFError:
                ans = 'n'

            if ans == "y":
                for p in pids:
                    ok = kill_pid(p["pid"])
                    status_msg = Colors.OKGREEN + "[killed]" + Colors.ENDC if ok else Colors.FAIL + "[FAILED]" + Colors.ENDC
                    print(f"  -> PID {p['pid']} {status_msg}")

                # Wait a moment
                time.sleep(1)
                pids_after = find_pids_for_port(port)
                if pids_after:
                    print_error(f"Failed to clear port {port}")
                    return False
                else:
                    print_success(f"Port {port} cleared")
            else:
                print_info("Aborted")
                return False

    # Start service
    if IS_WINDOWS:
        success = start_service_win(svc['name'], svc['display_name'])
    else:
        success = start_service_linux(svc['name'], svc['display_name'])

    if not success:
        return False

    # Wait for service to start
    desired_state = 'RUNNING' if IS_WINDOWS else 'active'
    success = wait_for_service_state(svc['name'], desired_state)
    if success:
        time.sleep(2)

        # Check port listening
        listening = check_port_listening(svc['port'])
        if listening:
            print_success(f"{svc['display_name']} started successfully, port {svc['port']} is listening")
        else:
            print_warn(f"{svc['display_name']} started but port {svc['port']} is not listening yet")

    return success


def stop_service(service_key, silent=False):
    """Stop service (cross-platform)"""
    svc = SERVICES[service_key]

    if not silent:
        print_info(f"Stopping {svc['display_name']}...")

    # Check if service exists
    status = get_service_status(svc['name'])
    if status == "NOT_FOUND":
        if not silent:
            print_info(f"{svc['display_name']} not registered, skipping")
        return True

    if status == "STOPPED" or status == "inactive":
        if not silent:
            print_info(f"{svc['display_name']} already stopped")
        return True

    # Stop service
    if IS_WINDOWS:
        success = stop_service_win(svc['name'], svc['display_name'], silent)
    else:
        success = stop_service_linux(svc['name'], svc['display_name'], silent)

    if not success:
        return False

    # Wait for service to stop
    success = wait_for_service_state(svc['name'], 'STOPPED')
    if success and not silent:
        time.sleep(1)
        listening = check_port_listening(svc['port'])
        if not listening:
            print_success(f"{svc['display_name']} stopped successfully, port {svc['port']} released")
        else:
            print_warn(f"{svc['display_name']} stopped but port {svc['port']} still in use")

    return success


def restart_service(service_key, force=False):
    """Restart service (cross-platform)"""
    svc = SERVICES[service_key]

    print()
    print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Restart {svc['display_name']}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")

    # Get PID before restart
    old_pid = get_service_pid(svc['name'])
    print_info(f"PID before restart: {old_pid}")

    # Stop service
    stop_success = stop_service(service_key)
    if not stop_success:
        print_error("Stop failed, cannot continue restart")
        return False

    # Wait for complete stop
    time.sleep(2)

    # Start service (pass force flag)
    start_success = start_service(service_key, force=force)
    if not start_success:
        print_error("Start failed, restart incomplete")
        return False

    # Verify PID change
    time.sleep(2)
    new_pid = get_service_pid(svc['name'])
    print_info(f"PID after restart: {new_pid}")

    if old_pid and new_pid and old_pid != new_pid:
        print_success(f"PID changed ({old_pid} -> {new_pid}), service restarted successfully!")
    elif old_pid == new_pid:
        print_warn("PID unchanged, service may not have restarted properly")
    else:
        print_info("Unable to verify PID change")

    return True


def show_service_status(service_key):
    """Display service status (cross-platform)"""
    svc = SERVICES[service_key]

    print()
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}  {svc['display_name']} ({svc['name']}){Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")

    # Service registration status
    status = get_service_status(svc['name'])
    if status == "NOT_FOUND":
        print(f"Status: {Colors.FAIL}[NOT REGISTERED]{Colors.ENDC}")
        print(f"Port: {svc['port']}")
        return

    # Service running status
    if status == "RUNNING" or status == "active":
        print(f"Status: {Colors.OKGREEN}[RUNNING]{Colors.ENDC}")
    elif status == "STOPPED" or status == "inactive":
        print(f"Status: {Colors.FAIL}[STOPPED]{Colors.ENDC}")
    elif status == "START_PENDING":
        print(f"Status: {Colors.WARNING}[STARTING]{Colors.ENDC}")
    else:
        print(f"Status: {status}")

    # PID info
    pid = get_service_pid(svc['name'])
    print(f"PID: {pid}")

    # Port listening
    listening = check_port_listening(svc['port'])
    if listening:
        print(f"Port: {svc['port']} {Colors.OKGREEN}[LISTENING]{Colors.ENDC}")
    else:
        print(f"Port: {svc['port']} {Colors.FAIL}[NOT LISTENING]{Colors.ENDC}")

    # Start type
    start_type = get_service_start_type(svc['name'])
    if start_type:
        if IS_WINDOWS:
            if 'AUTO_START' in start_type:
                print(f"Start Type: {Colors.OKGREEN}{start_type} (Auto-start){Colors.ENDC}")
            elif 'DEMAND_START' in start_type:
                print(f"Start Type: {start_type} (Manual)")
            elif 'DISABLED' in start_type:
                print(f"Start Type: {Colors.FAIL}{start_type} (Disabled){Colors.ENDC}")
            else:
                print(f"Start Type: {start_type}")
        else:
            if start_type == 'enabled':
                print(f"Start Type: {Colors.OKGREEN}{start_type} (Auto-start){Colors.ENDC}")
            elif start_type == 'disabled':
                print(f"Start Type: {start_type} (Manual)")
            else:
                print(f"Start Type: {start_type}")
    else:
        print(f"Start Type: Unknown")

    print()


# ============================================================
# Main Function
# ============================================================

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        return

    # Parse command line arguments (skip options)
    args = []
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            args.append(arg)

    action = args[0].lower() if args else ''
    service_arg = args[1].lower() if len(args) > 1 else 'all'

    # Determine services to operate on
    if service_arg == 'all':
        target_services = list(SERVICES.keys())
    else:
        if service_arg in SERVICES:
            target_services = [service_arg]
        else:
            # Check if it's a port number for clear-port command
            if action == 'clear-port':
                try:
                    port = int(service_arg)
                except ValueError:
                    print_error(f"Unknown service: {service_arg}")
                    print(f"Available services: {', '.join(SERVICES.keys())}")
                    return
            else:
                print_error(f"Unknown service: {service_arg}")
                print(f"Available services: {', '.join(SERVICES.keys())}")
                return

    # Parse force flag
    force = '--force' in sys.argv or '-f' in sys.argv
    dry_run = '--dry-run' in sys.argv

    # Check admin/root privileges for privileged operations
    if action in ['start', 'stop', 'restart', 'clear-ports', 'clear-port']:
        if not check_admin_rights():
            if IS_WINDOWS:
                print_error("This operation requires administrator privileges!")
                print_info("Please run this script as administrator")
            else:
                print_error("This operation requires root privileges!")
                print_info("Please run this script with sudo")
            sys.exit(1)

    print_header("DPlayer Service Controller")

    # Execute operation
    if action == 'start':
        print_header("Start DPlayer Services")
        print()

        all_success = True
        for key in target_services:
            success = start_service(key, force=force)
            print()
            if not success:
                all_success = False

        if all_success:
            print_header("Verify Service Status")
            for key in target_services:
                show_service_status(key)
        else:
            print_error("Some services failed to start, please check error messages")

    elif action == 'stop':
        print_header("Stop DPlayer Services")
        print()

        all_success = True
        for key in target_services:
            success = stop_service(key)
            print()
            if not success:
                all_success = False

        if all_success:
            print_header("Verify Service Status")
            for key in target_services:
                show_service_status(key)
        else:
            print_error("Some services failed to stop, please check error messages")

    elif action == 'restart':
        print_header("Restart DPlayer Services")
        print()

        all_success = True
        for key in target_services:
            success = restart_service(key, force=force)
            print()
            if not success:
                all_success = False

        if all_success:
            print_header("Verify Service Status")
            for key in target_services:
                show_service_status(key)
            print_success("All services restarted successfully!")
        else:
            print_error("Some services failed to restart, please check error messages")

    elif action == 'status':
        print_header("DPlayer Service Status")

        for key in target_services:
            show_service_status(key)

        # Summary statistics
        running_count = 0
        stopped_count = 0
        not_registered_count = 0

        for key in target_services:
            status = get_service_status(SERVICES[key]['name'])
            if status == 'RUNNING' or status == 'active':
                running_count += 1
            elif status == 'STOPPED' or status == 'inactive':
                stopped_count += 1
            else:
                not_registered_count += 1

        print()
        print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}  Summary Statistics{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
        print(f"Running: {Colors.OKGREEN}{running_count}{Colors.ENDC}")
        print(f"Stopped: {stopped_count}")
        print(f"Not Registered: {not_registered_count}")

    elif action == 'clear-ports':
        # Parse additional arguments
        force = '--force' in sys.argv or '-f' in sys.argv
        dry_run = '--dry-run' in sys.argv

        mode_label = "dry-run" if dry_run else ("force" if force else "interactive")
        print_header(f"Clear DPlayer Ports [{mode_label}]")

        clear_ports_all(force=force, dry_run=dry_run)

    elif action == 'clear-port':
        # Parse additional arguments
        force = '--force' in sys.argv or '-f' in sys.argv
        dry_run = '--dry-run' in sys.argv

        mode_label = "dry-run" if dry_run else ("force" if force else "interactive")

        try:
            port = int(service_arg)
            print_header(f"Clear Port {port} [{mode_label}]")
            clear_port_by_number(port, force=force, dry_run=dry_run)
        except ValueError:
            # It's a service name
            if service_arg in SERVICES:
                print_header(f"Clear Port for {SERVICES[service_arg]['display_name']} [{mode_label}]")
                clear_port(service_arg, force=force, dry_run=dry_run)
            else:
                print_error(f"Unknown service or port: {service_arg}")

    elif action == 'autostart-enable':
        if IS_WINDOWS:
            print_error("Auto-start management not implemented for Windows yet")
            print_info("Use Windows Services Manager (services.msc) to configure auto-start")
        else:
            print_header("Enable Auto-Start")
            print()

            all_success = True
            for key in target_services:
                svc = SERVICES[key]
                print_info(f"Setting {svc['display_name']} to auto-start...")

                try:
                    success = set_service_start_type_linux(svc['name'], 'auto')
                    if success:
                        print_success(f"{svc['display_name']} auto-start enabled")
                    else:
                        print_error(f"{svc['display_name']} configuration failed")
                        all_success = False
                except Exception as e:
                    print_error(f"{svc['display_name']} configuration failed: {e}")
                    all_success = False
                print()

            if all_success:
                print_header("Verify Configuration")
                for key in target_services:
                    show_service_status(key)
                print_success("All services auto-start enabled!")
            else:
                print_error("Some services configuration failed, please check error messages")

    elif action == 'autostart-disable':
        if IS_WINDOWS:
            print_error("Auto-start management not implemented for Windows yet")
            print_info("Use Windows Services Manager (services.msc) to configure auto-start")
        else:
            print_header("Disable Auto-Start")
            print()

            all_success = True
            for key in target_services:
                svc = SERVICES[key]
                print_info(f"Setting {svc['display_name']} to manual start...")

                try:
                    success = set_service_start_type_linux(svc['name'], 'demand')
                    if success:
                        print_success(f"{svc['display_name']} auto-start disabled")
                    else:
                        print_error(f"{svc['display_name']} configuration failed")
                        all_success = False
                except Exception as e:
                    print_error(f"{svc['display_name']} configuration failed: {e}")
                    all_success = False
                print()

            if all_success:
                print_header("Verify Configuration")
                for key in target_services:
                    show_service_status(key)
                print_success("All services auto-start disabled!")
            else:
                print_error("Some services configuration failed, please check error messages")

    else:
        print_help()


def print_help():
    """Print help information"""
    print()
    print(f"{Colors.HEADER}DPlayer Service Controller - Cross-Platform Version{Colors.ENDC}")
    print(f"Platform: {platform.system()}")
    print()
    print(f"Usage: {sys.argv[0]} [operation] [service/port] [options]")
    print()
    print(f"  {Colors.OKCYAN}[Operation]{Colors.ENDC}:")
    print(f"    start             - Start services")
    print(f"    stop              - Stop services")
    print(f"    restart           - Restart services")
    print(f"    status            - Query service status")
    print(f"    clear-ports       - Clear all DPlayer service ports")
    print(f"    clear-port        - Clear a specific service port or port number")
    if not IS_WINDOWS:
        print(f"    autostart-enable  - Enable auto-start (Linux only)")
        print(f"    autostart-disable - Disable auto-start (Linux only)")
    print()
    print(f"  {Colors.OKCYAN}[Service]{Colors.ENDC}:")
    print(f"    admin             - Admin Service ({SERVICES['admin']['name']})")
    print(f"    main              - Main Service ({SERVICES['main']['name']})")
    print(f"    thumbnail         - Thumbnail Service ({SERVICES['thumbnail']['name']})")
    print(f"    all               - All DPlayer services (default)")
    print()
    print(f"  {Colors.OKCYAN}[Port Number]{Colors.ENDC} (for clear-port):")
    print(f"    8080, 8081, 5001 - Direct port number")
    print()
    print(f"  {Colors.OKCYAN}[Options]{Colors.ENDC}:")
    print(f"    -f, --force       - Force mode (no confirmation for port clearing and start/restart)")
    print(f"    --dry-run         - Dry-run mode (show only, no changes)")
    print()
    print(f"  {Colors.OKCYAN}Examples{Colors.ENDC}:")
    print(f"    {sys.argv[0]} start")
    print(f"    {sys.argv[0]} start --force        # Auto-kill port conflicts")
    print(f"    {sys.argv[0]} start all")
    print(f"    {sys.argv[0]} restart admin")
    print(f"    {sys.argv[0]} restart --force      # Auto-kill port conflicts")
    print(f"    {sys.argv[0]} status")
    print(f"    {sys.argv[0]} clear-ports")
    print(f"    {sys.argv[0]} clear-port admin")
    print(f"    {sys.argv[0]} clear-port 8080 --force")
    print(f"    {sys.argv[0]} clear-ports --dry-run")
    if not IS_WINDOWS:
        print(f"    {sys.argv[0]} autostart-enable")
        print(f"    {sys.argv[0]} autostart-disable main")
    print()
    if IS_WINDOWS:
        print(f"{Colors.WARNING}Note: Requires {Colors.ENDC}administrator privileges{Colors.WARNING} to control services{Colors.ENDC}")
        if not HAS_WIN32:
            print(f"{Colors.WARNING}Warning: pywin32 not installed, service control may not work properly{Colors.ENDC}")
        if not HAS_PSUTIL:
            print(f"{Colors.WARNING}Warning: psutil not installed, port clearing requires it (pip install psutil){Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}Note: Requires {Colors.ENDC}root privileges{Colors.WARNING} to control services{Colors.ENDC}")
        if not HAS_PSUTIL:
            print(f"{Colors.WARNING}Warning: psutil not installed, port clearing requires it (pip install psutil){Colors.ENDC}")
    print()


if __name__ == '__main__':
    # Windows: Enable ANSI colors
    if IS_WINDOWS:
        os.system("")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
    except Exception as e:
        print_error(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
