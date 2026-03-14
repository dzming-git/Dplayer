# DPlayer Scripts Directory

## Windows Service Management (PowerShell Cmdlet)

### Main Scripts

#### service_manager.ps1
Core service management script using PowerShell cmdlets (Get-Service, Start-Service, etc.)

**Usage:**
```batch
service_manager.bat install DPlayer-Main
service_manager.bat status
service_manager.bat start All
service_manager.bat stop All
service_manager.bat restart All
service_manager.bat uninstall All
```

**Available Actions:**
- `install` - Install Windows service
- `uninstall` - Uninstall Windows service
- `start` - Start service
- `stop` - Stop service
- `restart` - Restart service
- `status` - Show service status
- `enable` - Set to auto-start
- `disable` - Set to manual start

**Service Names:**
- `DPlayer-Main` - Main application (Port 80)
- `DPlayer-Admin` - Admin panel (Port 8080)
- `DPlayer-Thumbnail` - Thumbnail service (Port 5001)
- `All` - All services

### Quick Actions

#### Install All Services
```batch
install_services.bat
```

#### Uninstall All Services
```batch
uninstall_services.bat
```

#### Reinstall All Services
```batch
reinstall_services.bat
```

### Diagnostic Tools

#### Diagnose Service Issues
```batch
diagnose_service.bat
```

Check service configuration, dependencies, and logs.

#### Find All DPlayer Artifacts
```batch
find_dplayer_artifacts.bat
```

Find all DPlayer services, tasks, and processes on the system.

#### Clean All DPlayer Artifacts
```batch
clean_all_dplayer.bat
```

Complete cleanup of all DPlayer services, tasks, and processes.

### Test Scripts

#### Test Service Manager
```batch
test_service_manager.bat
```

Run comprehensive test suite for service manager.

### Utility Scripts

#### Kill Port Occupying Processes
```batch
python scripts/kill_ports.py
```

Interactive mode - ask for confirmation
```batch
python scripts/kill_ports.py -f
```

Force mode - kill without confirmation
```batch
python scripts/kill_ports.py --dry-run
```

Dry-run - only show占用情况

## Cross-Platform Scripts (for Linux)

### Linux Service Management

#### process_manager.py
Cross-platform process manager using Python.

**Usage (Linux/Mac):**
```bash
python process_manager.py start all
python process_manager.py status
python process_manager.py stop all
python process_manager.py restart all
python process_manager.py enable all
python process_manager.py disable all
```

### systemd Services (Linux)

Linux systemd service unit files are in `scripts/service/`:
- `dplayer-main.service`
- `dplayer-admin.service`
- `dplayer-thumbnail.service`

## Development Scripts

### Database Migration
```batch
python scripts/migrate_db.py
```

### Run Tests
```batch
run_tests.bat
```

### Docker Setup
```batch
setup_docker.bat
```

## Service Architecture

### Windows
Uses PowerShell service cmdlets:
- `Get-Service` - Get service status
- `Start-Service` - Start service
- `Stop-Service` - Stop service
- `Restart-Service` - Restart service
- `Set-Service` - Configure service
- `New-Service` - Create service
- `Remove-Service` - Remove service

### Linux
Uses Python process manager or systemd.

## Important Notes

### Windows
- All Windows service management uses **only PowerShell cmdlets**
- No NSSM, no Task Scheduler for service management
- Requires Administrator privileges for service operations
- Services are configured with auto-restart on failure

### Linux
- Use process_manager.py for development
- Use systemd for production deployment
- No cross-platform service management script needed

## Troubleshooting

### Service Won't Start
1. Run diagnostic: `diagnose_service.bat`
2. Check logs: `type logs\*.log`
3. Reinstall: `reinstall_services.bat`

### Port Already in Use
1. Find artifact: `find_dplayer_artifacts.bat`
2. Clean up: `clean_all_dplayer.bat`
3. Kill ports: `python scripts/kill_ports.py -f`

### Multiple Processes Running
1. Find all artifacts: `find_dplayer_artifacts.bat`
2. Clean all: `clean_all_dplayer.bat`
3. Reinstall clean: `install_services.bat`

## Documentation

- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Detailed troubleshooting guide
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [docs/POWERSHELL_SERVICE_MANAGER.md](../docs/POWERSHELL_SERVICE_MANAGER.md) - PowerShell service manager documentation

## Removed Scripts

The following scripts have been removed (obsolete, use PowerShell service manager instead):
- All `start_*.bat` scripts
- All `stop_*.bat` scripts
- All `restart_*.bat` scripts
- `install_windows_autostart.*` scripts
- `uninstall_windows_autostart.*` scripts
- `run_*.bat` scripts in `service/` folder
- `migrate_to_services.*` scripts
