# Service Control - Quick Reference

## Quick Commands

```bash
# Service Management
python scripts/service_controller.py start              # Start all services
python scripts/service_controller.py start --force      # Start with auto-kill port conflicts
python scripts/service_controller.py stop               # Stop all services
python scripts/service_controller.py restart            # Restart all services
python scripts/service_controller.py restart --force    # Restart with auto-kill port conflicts
python scripts/service_controller.py status             # Check service status

# Port Management
python scripts/service_controller.py clear-ports        # Clear all DPlayer ports
python scripts/service_controller.py clear-port admin   # Clear specific service port
python scripts/service_controller.py clear-port 8080    # Clear specific port number

# Options
python scripts/service_controller.py clear-ports --force    # Force clear without confirmation
python scripts/service_controller.py clear-ports --dry-run  # Preview only, no changes
```

## Important Notes

**All service control is now unified through `scripts/service_controller.py`**

- All old `.bat` and `.sh` scripts have been removed
- **kill_ports.py has been integrated** - use `clear-ports` and `clear-port` commands
- Use Python script for all service operations
- Supports both Windows and Linux
- Administrator/Root privileges required for start/stop/restart/port-clear operations
- **NEW: `start` and `restart` now detect port conflicts and offer to kill processes**

## Service Start/Restart with Port Conflict Handling

### Interactive Mode (Default)
When starting or restarting, if port is occupied:

```bash
python scripts/service_controller.py start admin
```

Output:
```
[INFO] Starting Admin Service...
[WARN] Port 8080 is occupied by 1 process(es):
  PID 1234  python.exe
  CMD C:\...\python.exe app.py
  Kill 1 process(es) and start service? [y/N]
```

### Force Mode (Auto-Kill)
Use `-f` or `--force` to automatically kill conflicting processes:

```bash
python scripts/service_controller.py start --force
python scripts/service_controller.py restart admin -f
```

Output:
```
[INFO] Starting Admin Service...
[WARN] Port 8080 is occupied by 1 process(es):
  PID 1234  python.exe
  CMD C:\...\python.exe app.py
[INFO] Force mode: killing processes...
  -> PID 1234 [killed]
[OK] Port 8080 cleared
```

## Port Management

### Clear all DPlayer service ports
```bash
python scripts/service_controller.py clear-ports
```

### Clear port for a specific service
```bash
python scripts/service_controller.py clear-port admin
python scripts/service_controller.py clear-port main
python scripts/service_controller.py clear-port thumbnail
```

### Clear a specific port number
```bash
python scripts/service_controller.py clear-port 8080
```

### Force mode (no confirmation)
```bash
python scripts/service_controller.py clear-ports --force
python scripts/service_controller.py clear-port 8080 --force
```

### Dry-run mode (preview only)
```bash
python scripts/service_controller.py clear-ports --dry-run
```

## Port Detection

The service controller:
- Reads port configuration from `config/config.json`
- Automatically detects processes using the port
- Shows PID, process name, and command line
- Supports interactive or force mode
- Validates port is free after clearing

## Common Workflows

### Fresh Start with Port Cleanup
```bash
# Clear all ports (interactive)
python scripts/service_controller.py clear-ports

# Start all services
python scripts/service_controller.py start
```

### Automated Restart
```bash
# Force restart with automatic port clearing
python scripts/service_controller.py restart --force
```

### Debug Port Conflicts
```bash
# See what's using ports
python scripts/service_controller.py clear-ports --dry-run
```

## Linux Auto-Start

```bash
sudo python scripts/service_controller.py autostart-enable
sudo python scripts/service_controller.py autostart-disable main
```

## Detailed Documentation

See `scripts/SERVICE_CONTROLLER_README.md` for comprehensive documentation.
