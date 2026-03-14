# DPlayer Service Controller - Usage Guide

## Overview

`service_controller.py` is unified service management tool for DPlayer. It provides cross-platform support for both Windows and Linux systems, replacing all previous batch and shell scripts.

## Features

- **Cross-platform**: Works on Windows and Linux
- **Unified interface**: Single command for all service operations
- **Status monitoring**: Real-time service status and port monitoring
- **Auto-start management**: Configure services to start automatically (Linux)
- **Port management**: Detect and clear port conflicts with process details
- **Comprehensive logging**: Detailed status information and error reporting

## Requirements

### Windows
- Python 3.x
- pywin32 package (for service control)
- psutil package (for port management)
- Administrator privileges for service operations

Install dependencies:
```bash
pip install pywin32 psutil
```

### Linux
- Python 3.x
- systemd service manager
- psutil package (for port management)
- Root privileges for service operations

Install psutil:
```bash
pip install psutil
```

## Usage

### Basic Syntax

```bash
python service_controller.py [operation] [service/port] [options]
```

### Operations

| Operation | Description | Privileges Required |
|-----------|-------------|---------------------|
| `start` | Start services | Admin/Root |
| `stop` | Stop services | Admin/Root |
| `restart` | Restart services | Admin/Root |
| `status` | Query service status | None |
| `clear-ports` | Clear all DPlayer service ports | Admin/Root |
| `clear-port` | Clear a specific service port or port number | Admin/Root |
| `autostart-enable` | Enable auto-start | Root (Linux only) |
| `autostart-disable` | Disable auto-start | Root (Linux only) |

### Services

| Service | System Name | Description | Default Port |
|---------|------------|-------------|---------------|
| `admin` | DPlayer-Admin | Admin Panel | 8080 |
| `main` | DPlayer-Main | Main Application | 8081 |
| `thumbnail` | DPlayer-Thumbnail | Thumbnail Service | 5001 |
| `all` | All services | All DPlayer services | - |

### Options

| Option | Description |
|--------|-------------|
| `-f, --force` | Force mode - skip confirmation for port clearing |
| `--dry-run` | Dry-run mode - show only, make no changes |

## Examples

### Service Management

#### Start all services
```bash
python service_controller.py start
```

#### Start a specific service
```bash
python service_controller.py start admin
```

#### Stop all services
```bash
python service_controller.py stop
```

#### Restart main service
```bash
python service_controller.py restart main
```

#### Check service status
```bash
python service_controller.py status
```

#### Check specific service status
```bash
python service_controller.py status admin
```

### Port Management (NEW!)

#### Clear all DPlayer service ports
```bash
python service_controller.py clear-ports
```

This will:
- Check all DPlayer service ports (8080, 8081, 5001)
- Detect any processes using these ports
- Show PID, process name, and command line
- Ask for confirmation before killing processes
- Verify port is free after clearing

#### Clear port for a specific service
```bash
python service_controller.py clear-port admin
python service_controller.py clear-port main
python service_controller.py clear-port thumbnail
```

This will:
- Read port from service configuration
- Detect processes using the port
- Show process details
- Ask for confirmation
- Verify port is free

#### Clear a specific port number
```bash
python service_controller.py clear-port 8080
python service_controller.py clear-port 9999
```

This allows clearing any port, not just DPlayer service ports.

#### Force mode (no confirmation)
```bash
python service_controller.py clear-ports --force
python service_controller.py clear-port 8080 -f
```

Useful for automation or when you're sure about the operation.

#### Dry-run mode (preview only)
```bash
python service_controller.py clear-ports --dry-run
python service_controller.py clear-port admin --dry-run
```

Shows what would be done without actually making changes. Great for debugging or before running force mode.

### Linux Auto-Start Management

#### Enable auto-start for all services
```bash
sudo python service_controller.py autostart-enable
```

#### Disable auto-start for specific service
```bash
sudo python service_controller.py autostart-disable main
```

## Output Format

The service controller provides color-coded output:

- **Green [OK]**: Success messages
- **Red [ERROR]**: Error messages
- **Yellow [WARN]**: Warning messages
- **Blue/Info**: Informational messages
- **Cyan**: Headers and section titles

### Status Output Example

```
============================================================
  Admin Service (DPlayer-Admin)
============================================================
Status: [RUNNING]
PID: 10468
Port: 8080 [LISTENING]
Start Type: 2   AUTO_START (Auto-start)
```

### Port Clearing Output Example

```
============================================================
  Clear Port for Admin Service [interactive]
============================================================
[INFO] Checking port 8080 for Admin Service...

[WARN] Port 8080 is occupied by 1 process(es):
  PID 2400  pythonservice.exe
  CMD C:\Users\...\pythonservice.exe
  Kill 1 process(es)? [y/N] y
  -> PID 2400 [killed]
[OK] Port 8080 is now free
```

### Summary Statistics

The `status` command provides a summary at end:

```
============================================================
  Summary Statistics
============================================================
Running: 3
Stopped: 0
Not Registered: 0
```

## Port Configuration

Ports are read from `config/config.json`. To change ports:

1. Edit `config/config.json`
2. Modify the `ports` section
3. Restart services

Example:
```json
{
  "ports": {
    "admin_app": 8080,
    "main_app": 8081,
    "thumbnail": 5001
  }
}
```

The service controller automatically reads this configuration for:
- Service status checking
- Port clearing operations
- Port listening verification

## Troubleshooting

### Windows

**Error: "This operation requires administrator privileges!"**

Solution: Run Command Prompt or PowerShell as Administrator.

**Error: "pywin32 not installed"**

Solution: Install pywin32:
```bash
pip install pywin32
```

**Error: "psutil not installed"**

Solution: Install psutil:
```bash
pip install psutil
```

**Error: "Insufficient permissions to query network connections"**

Solution: Run as Administrator to query all processes using ports.

### Linux

**Error: "This operation requires root privileges!"**

Solution: Use sudo:
```bash
sudo python service_controller.py start
```

**Error: "psutil not installed"**

Solution: Install psutil:
```bash
sudo pip install psutil
```

**Service not found**

Ensure services are registered. For Linux, make sure systemd service files exist in `/etc/systemd/system/`.

**Port still occupied after clearing**

Some processes may respawn. Check:
1. Is the service auto-starting?
2. Are there multiple instances running?
3. Try force mode with `--force`

## Migration from Old Scripts

### Replaced Windows Scripts

The following Windows batch scripts have been replaced:

- `restart_admin.bat` → Use: `python service_controller.py restart admin`
- `restart_all.bat` → Use: `python service_controller.py restart`
- `scripts/clean_all_dplayer.bat` → Use: `python service_controller.py stop`
- `scripts/diagnose_network.bat` → Integrated into main service controller
- `scripts/fix_network_issues.bat` → Integrated into main service controller
- `scripts/run_tests.bat` → Use standard test runners
- `scripts/setup_docker.bat` → Docker setup should be done separately
- `scripts/setup_firewall.bat` → Use system firewall configuration tools
- `scripts/setup_restart_perms.bat` → Integrated into service controller
- `scripts/start_all_services.bat` → Use: `python service_controller.py start`
- `scripts/stop_all_services.bat` → Use: `python service_controller.py stop`

### Replaced Linux Scripts

The following Linux shell scripts have been replaced:

- `scripts/setup_docker.sh` → Docker setup should be done separately
- `scripts/setup_firewall.sh` → Use system firewall configuration tools (ufw, firewalld)
- `scripts/service/install_linux_services.sh` → Use: `sudo systemctl enable dplayer-*.service`

### Replaced kill_ports.py

The port management functionality has been integrated:

```bash
# Old
python scripts/kill_ports.py

# New
python scripts/service_controller.py clear-ports
```

```bash
# Old - Force mode
python scripts/kill_ports.py -f

# New
python scripts/service_controller.py clear-ports --force
```

```bash
# Old - Dry-run
python scripts/kill_ports.py --dry-run

# New
python scripts/service_controller.py clear-ports --dry-run
```

```bash
# Old - Specific port
python scripts/kill_ports.py -f 8080

# New
python scripts/service_controller.py clear-port 8080 --force
```

## Advanced Usage

### Check specific service status
```bash
python service_controller.py status admin
```

### Start multiple services
```bash
python service_controller.py start admin main
```

### Restart with status verification
The `restart` command automatically verifies status after restart and checks if PID has changed.

### Chain operations for clean restart
```bash
# Clear ports, then restart
python service_controller.py clear-ports --force
python service_controller.py restart
```

### Debug port conflicts
```bash
# See what's using ports without killing
python service_controller.py clear-ports --dry-run
```

## Platform-Specific Notes

### Windows

- Uses Windows Service Manager (sc.exe) and pywin32
- Service names: DPlayer-Admin, DPlayer-Main, DPlayer-Thumbnail
- Install services using: `python <service_script>.py install`
- Configure auto-start using Windows Services Manager (services.msc)
- ANSI colors enabled for better output

### Linux

- Uses systemd service manager
- Service files are located in `scripts/service/` directory
- Service files should be symlinked to `/etc/systemd/system/`
- Auto-start management is fully supported via `autostart-enable` and `autostart-disable` commands
- Use sudo for privileged operations

## Getting Help

To see all available commands and options:

```bash
python service_controller.py
```

Or run without arguments to display help.

## Common Workflows

### Fresh Start
```bash
# Stop everything
python service_controller.py stop

# Clear any stuck ports
python service_controller.py clear-ports --force

# Start all services
python service_controller.py start

# Verify status
python service_controller.py status
```

### Restart Specific Service
```bash
# Restart just the admin panel
python service_controller.py restart admin
```

### Debug Port Issues
```bash
# Check what's using ports
python service_controller.py clear-ports --dry-run

# Clear if needed
python service_controller.py clear-ports
```

### Automated Restart
```bash
# Force restart without prompts
python service_controller.py clear-ports --force
python service_controller.py restart
```

## Best Practices

1. **Use dry-run first**: Before force operations, check with `--dry-run`
2. **Verify after changes**: Always run `status` after start/stop/restart
3. **Clear ports before restart**: If having issues, clear ports first
4. **Check logs**: If services won't start, check system logs
5. **Use specific service names**: When possible, target specific services vs. "all"

## Support

For issues or questions about the service controller:

1. Check this documentation first
2. Run `python service_controller.py status` to see current service states
3. Run `python service_controller.py clear-ports --dry-run` to check port usage
4. Check system logs for error messages:
   - Windows: Event Viewer → Windows Logs → Application
   - Linux: `journalctl -u dplayer-*`

## License

This service controller is part of DPlayer project.
