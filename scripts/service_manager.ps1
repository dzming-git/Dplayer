#Requires -RunAsAdministrator

<#
.SYNOPSIS
    DPlayer PowerShell Service Manager
.DESCRIPTION
    Manage DPlayer services using PowerShell service cmdlets (Get-Service, Start-Service, etc.)
.NOTES
    File Name      : service_manager.ps1
    Prerequisite   : PowerShell 5.1+
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = (Resolve-Path (Join-Path $ScriptDir "..")).Path

# ============================================================
# Service Configuration
# ============================================================

$ServiceConfig = @{
    "DPlayer-Main" = @{
        DisplayName    = "DPlayer Main Application Service"
        Description    = "DPlayer Main Application, Port 80"
        BinaryPath     = Join-Path $ScriptDir "start_main_service.bat"
        Port           = 80
        LogFile        = Join-Path $ProjectDir "logs\main_app.log"
        Script         = "app.py"
        BatchFile      = "start_main_service.bat"
    }
    "DPlayer-Admin" = @{
        DisplayName    = "DPlayer Admin Panel Service"
        Description    = "DPlayer Admin Panel, Port 8080"
        BinaryPath     = Join-Path $ScriptDir "start_admin_service.bat"
        Port           = 8080
        LogFile        = Join-Path $ProjectDir "logs\admin_app.log"
        Script         = "admin_app.py"
        BatchFile      = "start_admin_service.bat"
    }
    "DPlayer-Thumbnail" = @{
        DisplayName    = "DPlayer Thumbnail Service"
        Description    = "DPlayer Thumbnail Microservice, Port 5001"
        BinaryPath     = Join-Path $ScriptDir "start_thumbnail_service.bat"
        Port           = 5001
        LogFile        = Join-Path $ProjectDir "logs\thumbnail.log"
        Script         = "services\thumbnail_service.py"
        BatchFile      = "start_thumbnail_service.bat"
    }
}

# Find Python executable
function Get-PythonExe {
    # Use python.exe for better compatibility with services
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    throw "Python not found. Please add Python to PATH."
}

# ============================================================
# Service Management Functions
# ============================================================

<#
.SYNOPSIS
    Get service status
#>
function Get-DPlayerStatus {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        try {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue

            if ($svc) {
                # Get process information
                $process = $null
                if ($svc.Status -eq "Running") {
                    $processId = (Get-CimInstance -ClassName Win32_Service -Filter "Name='$svcName'").ProcessId
                    if ($processId) {
                        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    }
                }

                $result = [PSCustomObject]@{
                    ServiceName   = $svcName
                    DisplayName   = $svc.DisplayName
                    Status        = $svc.Status
                    StartType     = $svc.StartType
                    PID           = if ($process) { $process.Id } else { $null }
                    CPU           = if ($process) { $process.CPU } else { $null }
                    MemoryMB      = if ($process) { [math]::Round($process.WorkingSet64 / 1MB, 2) } else { $null }
                    StartTime     = if ($process) { $process.StartTime } else { $null }
                    Port          = $ServiceConfig[$svcName].Port
                }
            } else {
                $result = [PSCustomObject]@{
                    ServiceName   = $svcName
                    DisplayName   = $ServiceConfig[$svcName].DisplayName
                    Status        = "Not Installed"
                    StartType     = "-"
                    PID           = $null
                    CPU           = $null
                    MemoryMB      = $null
                    StartTime     = $null
                    Port          = $ServiceConfig[$svcName].Port
                }
            }
            $results += $result
        } catch {
            Write-Warning "Failed to get status for $svcName`: $_"
        }
    }

    return $results
}

<#
.SYNOPSIS
    Install service
#>
function Install-DPlayerService {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $pythonExe = Get-PythonExe
    Write-Host "Using Python: $pythonExe"
    Write-Host "Working Directory: $ProjectDir"

    # Ensure log directory exists
    $logDir = Join-Path $ProjectDir "logs"
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        $config = $ServiceConfig[$svcName]

        # Check if service already exists
        $existing = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Warning "Service '$svcName' already exists, skipping installation"
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = "Service already exists"
            }
            continue
        }

        try {
            # Build service command using batch file (sets correct working directory)
            $batchFile = $config.BatchFile
            $binaryPath = "`"cmd.exe`" /c `"$batchFile`""

            # Create service
            New-Service -Name $svcName `
                        -BinaryPathName $binaryPath `
                        -DisplayName $config.DisplayName `
                        -StartupType Automatic `
                        -Description $config.Description `
                        -DependsOn "EventLog" `
                        -ErrorAction Stop | Out-Null

            # Configure service recovery options
            sc.exe failure $svcName reset= 86400 actions= restart/60000/restart/60000/restart/60000 | Out-Null

            Write-Host "[OK] Installed service: $svcName" -ForegroundColor Green
            Write-Host "     BinaryPath: $binaryPath"
            Write-Host "     BatchFile: $batchFile"
            Write-Host "     ProjectDir: $ProjectDir"
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $true
                Message     = "Installation successful"
            }
        } catch {
            Write-Host "[ERROR] Failed to install $svcName`: $_" -ForegroundColor Red
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = $_.Exception.Message
            }
        }
    }

    return $results
}

<#
.SYNOPSIS
    Uninstall service
#>
function Uninstall-DPlayerService {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        try {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if (-not $svc) {
                Write-Warning "Service '$svcName' does not exist"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $false
                    Message     = "Service does not exist"
                }
                continue
            }

            # Stop service if running
            if ($svc.Status -eq "Running") {
                Stop-Service -Name $svcName -Force
                Start-Sleep -Seconds 2
            }

            # Remove service
            Remove-Service -Name $svcName -Force
            Write-Host "[OK] Uninstalled service: $svcName" -ForegroundColor Green
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $true
                Message     = "Uninstallation successful"
            }
        } catch {
            Write-Host "[ERROR] Failed to uninstall $svcName`: $_" -ForegroundColor Red
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = $_.Exception.Message
            }
        }
    }

    return $results
}

<#
.SYNOPSIS
    Start service
#>
function Start-DPlayerService {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        try {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if (-not $svc) {
                Write-Warning "Service '$svcName' does not exist"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $false
                    Message     = "Service does not exist"
                }
                continue
            }

            if ($svc.Status -eq "Running") {
                Write-Warning "Service '$svcName' is already running"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $true
                    Message     = "Already running"
                }
                continue
            }

            Start-Service -Name $svcName -ErrorAction Stop
            Write-Host "[OK] Started service: $svcName" -ForegroundColor Green
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $true
                Message     = "Start successful"
            }
        } catch {
            Write-Host "[ERROR] Failed to start $svcName`: $_" -ForegroundColor Red
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = $_.Exception.Message
            }
        }
    }

    return $results
}

<#
.SYNOPSIS
    Stop service
#>
function Stop-DPlayerService {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        try {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if (-not $svc) {
                Write-Warning "Service '$svcName' does not exist"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $false
                    Message     = "Service does not exist"
                }
                continue
            }

            if ($svc.Status -eq "Stopped") {
                Write-Warning "Service '$svcName' is already stopped"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $true
                    Message     = "Already stopped"
                }
                continue
            }

            Stop-Service -Name $svcName -Force -ErrorAction Stop
            Write-Host "[OK] Stopped service: $svcName" -ForegroundColor Green
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $true
                Message     = "Stop successful"
            }
        } catch {
            Write-Host "[ERROR] Failed to stop $svcName`: $_" -ForegroundColor Red
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = $_.Exception.Message
            }
        }
    }

    return $results
}

<#
.SYNOPSIS
    Restart service
#>
function Restart-DPlayerService {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        try {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if (-not $svc) {
                Write-Warning "Service '$svcName' does not exist"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $false
                    Message     = "Service does not exist"
                }
                continue
            }

            Restart-Service -Name $svcName -Force -ErrorAction Stop
            Write-Host "[OK] Restarted service: $svcName" -ForegroundColor Green
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $true
                Message     = "Restart successful"
            }
        } catch {
            Write-Host "[ERROR] Failed to restart $svcName`: $_" -ForegroundColor Red
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = $_.Exception.Message
            }
        }
    }

    return $results
}

<#
.SYNOPSIS
    Set service startup type
#>
function Set-DPlayerServiceStartup {
    param(
        [ValidateSet("All", "DPlayer-Main", "DPlayer-Admin", "DPlayer-Thumbnail")]
        [string]$ServiceName = "All",
        [ValidateSet("Automatic", "Manual", "Disabled")]
        [string]$StartupType = "Automatic"
    )

    if ($ServiceName -eq "All") {
        $targetServices = $ServiceConfig.Keys
    } else {
        $targetServices = @($ServiceName)
    }

    $results = @()
    foreach ($svcName in $targetServices) {
        try {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if (-not $svc) {
                Write-Warning "Service '$svcName' does not exist"
                $results += [PSCustomObject]@{
                    ServiceName = $svcName
                    Success     = $false
                    Message     = "Service does not exist"
                }
                continue
            }

            Set-Service -Name $svcName -StartupType $StartupType -ErrorAction Stop
            Write-Host "[OK] Set $svcName startup type to: $StartupType" -ForegroundColor Green
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $true
                Message     = "Configuration successful"
            }
        } catch {
            Write-Host "[ERROR] Failed to set startup type for $svcName`: $_" -ForegroundColor Red
            $results += [PSCustomObject]@{
                ServiceName = $svcName
                Success     = $false
                Message     = $_.Exception.Message
            }
        }
    }

    return $results
}

<#
.SYNOPSIS
    Display formatted service status table
#>
function Show-StatusTable {
    param([array]$StatusData)

    Write-Host "`n========================================"
    Write-Host "  DPlayer Service Status"
    Write-Host "========================================`n"

    # Header
    Write-Host ("{0,-20} {1,-12} {2,-10} {3,-8} {4,-8} {5,-10} {6,-8}" -f `
        "Service", "Status", "StartType", "PID", "Port", "Memory(MB)", "StartTime")
    Write-Host ("-" * 90)

    # Data rows
    foreach ($item in $StatusData) {
        $statusColor = if ($item.Status -eq "Running") { "Green" } `
                       elseif ($item.Status -eq "Stopped") { "Yellow" } `
                       else { "Red" }

        $memoryStr = if ($item.MemoryMB) { $item.MemoryMB.ToString("F1") } else { "-" }
        $timeStr = if ($item.StartTime) { $item.StartTime.ToString("HH:mm:ss") } else { "-" }
        $pidStr = if ($item.PID) { $item.PID } else { "-" }

        Write-Host ("{0,-20} {1,-12} {2,-10} {3,-8} {4,-8} {5,-10} {6,-8}" -f `
            $item.ServiceName, $item.Status, $item.StartType, $pidStr, $item.Port, $memoryStr, $timeStr) `
            -ForegroundColor $statusColor
    }

    Write-Host ""
}

# ============================================================
# Main Function
# ============================================================

function Main {
    param([string[]]$Arguments)

    if ($Arguments.Count -eq 0) {
        Show-Help
        return
    }

    $action = $Arguments[0].ToLower()
    $serviceName = if ($Arguments.Count -gt 1) { $Arguments[1] } else { "All" }

    switch ($action) {
        "install" {
            Write-Host "`nInstalling DPlayer services...`n"
            $results = Install-DPlayerService -ServiceName $serviceName
        }
        "uninstall" {
            Write-Host "`nUninstalling DPlayer services...`n"
            $results = Uninstall-DPlayerService -ServiceName $serviceName
        }
        "start" {
            Write-Host "`nStarting DPlayer services...`n"
            $results = Start-DPlayerService -ServiceName $serviceName
        }
        "stop" {
            Write-Host "`nStopping DPlayer services...`n"
            $results = Stop-DPlayerService -ServiceName $serviceName
        }
        "restart" {
            Write-Host "`nRestarting DPlayer services...`n"
            $results = Restart-DPlayerService -ServiceName $serviceName
        }
        "status" {
            $results = Get-DPlayerStatus -ServiceName $serviceName
            Show-StatusTable -StatusData $results
            return
        }
        "enable" {
            Write-Host "`nEnabling services (auto-start)...`n"
            $results = Set-DPlayerServiceStartup -ServiceName $serviceName -StartupType Automatic
        }
        "disable" {
            Write-Host "`nDisabling services (manual start)...`n"
            $results = Set-DPlayerServiceStartup -ServiceName $serviceName -StartupType Manual
        }
        default {
            Write-Host "Unknown action: $action" -ForegroundColor Red
            Show-Help
            return
        }
    }

    # Display operation results
    Write-Host "`nOperation Results:"
    Write-Host "-" * 40
    foreach ($r in $results) {
        $icon = if ($r.Success) { "[OK]" } else { "[FAIL]" }
        $color = if ($r.Success) { "Green" } else { "Red" }
        Write-Host "$($icon) $($r.ServiceName): $($r.Message)" -ForegroundColor $color
    }
    Write-Host ""
}

function Show-Help {
    Write-Host @"

DPlayer Service Manager - PowerShell Edition

Usage: .\service_manager.ps1 <action> [service_name]

Actions:
    install     Install services
    uninstall   Uninstall services
    start       Start services
    stop        Stop services
    restart     Restart services
    status      Show status
    enable      Set to auto-start
    disable     Set to manual start

Service Names:
    All                    All services (default)
    DPlayer-Main           Main application (Port 80)
    DPlayer-Admin          Admin panel (Port 8080)
    DPlayer-Thumbnail      Thumbnail service (Port 5001)

Examples:
    .\service_manager.ps1 install All
    .\service_manager.ps1 start DPlayer-Main
    .\service_manager.ps1 status
    .\service_manager.ps1 stop DPlayer-Thumbnail
    .\service_manager.ps1 enable All
    .\service_manager.ps1 uninstall All

Notes:
    - Requires Administrator privileges
    - Ensure Python is installed and in PATH
    - Service logs are saved in logs/ directory
"@
}

# Execute main function
Main -Arguments $args
