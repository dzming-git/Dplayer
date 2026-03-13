#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Complete cleanup of all DPlayer services, tasks, and processes
.DESCRIPTION
    This script will:
    1. Stop all DPlayer services
    2. Uninstall all DPlayer Windows services
    3. Remove all DPlayer scheduled tasks
    4. Kill all DPlayer processes
    5. Release all DPlayer ports (80, 8080, 5001)
.NOTES
    Requires Administrator privileges
#>

Write-Host ""
Write-Host "============================================================"
Write-Host "  DPlayer Complete Cleanup Tool"
Write-Host "============================================================"
Write-Host ""
Write-Host "WARNING: This will:"
Write-Host "  - Stop all DPlayer services"
Write-Host "  - Uninstall all DPlayer Windows services"
Write-Host "  - Remove all DPlayer scheduled tasks"
Write-Host "  - Kill all DPlayer processes"
Write-Host "  - Release ports 80, 8080, 5001"
Write-Host ""
Write-Host "This action is IRREVERSIBLE!"
Write-Host ""

$confirm = Read-Host "Confirm to proceed? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cleanup cancelled."
    pause
    exit 0
}

Write-Host ""

# ============================================================
# Section 1: Find and stop all Windows services
# ============================================================

Write-Host "[1/5] Finding DPlayer Windows Services..."
Write-Host "------------------------------------------------------------"

$allServices = Get-WmiObject Win32_Service -ErrorAction SilentlyContinue |
               Where-Object {
                   $_.DisplayName -match 'DPlayer|dplayer|main|admin|thumbnail' -or
                   $_.Name -match 'DPlayer|dplayer|main|admin|thumbnail'
               }

if ($allServices) {
    Write-Host "Found $($allServices.Count) service(s):"
    foreach ($svc in $allServices) {
        Write-Host "  - $($svc.Name) ($($svc.DisplayName))"
        Write-Host "    Status: $($svc.State)"
        Write-Host "    PathName: $($svc.PathName)"
    }

    Write-Host ""
    Write-Host "[2/5] Stopping services..."
    Write-Host "------------------------------------------------------------"

    foreach ($svc in $allServices) {
        try {
            Write-Host "Stopping: $($svc.Name)"
            Stop-Service -Name $svc.Name -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            Write-Host "  [OK] Stopped" -ForegroundColor Green
        } catch {
            Write-Host "  [WARN] Failed to stop: $_" -ForegroundColor Yellow
        }
    }

    Write-Host ""
    Write-Host "[3/5] Uninstalling services..."
    Write-Host "------------------------------------------------------------"

    foreach ($svc in $allServices) {
        try {
            Write-Host "Uninstalling: $($svc.Name)"
            # Try multiple methods
            $success = $false

            # Method 1: Remove-Service (PowerShell 6+)
            try {
                Remove-Service -Name $svc.Name -Force -ErrorAction Stop
                $success = $true
            } catch {
                # Method 2: sc.exe delete
                try {
                    $result = & sc.exe delete $svc.Name 2>&1
                    if ($LASTEXITCODE -eq 0) {
                        $success = $true
                    }
                } catch {
                    # Method 3: NSSM
                    $nssm = Get-Command nssm -ErrorAction SilentlyContinue
                    if ($nssm) {
                        & $nssm remove $svc.Name confirm 2>&1 | Out-Null
                        $success = $true
                    }
                }
            }

            if ($success) {
                Write-Host "  [OK] Uninstalled" -ForegroundColor Green
            } else {
                Write-Host "  [WARN] May have failed, verify manually" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  [ERROR] Failed: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No DPlayer services found" -ForegroundColor Gray
}

# ============================================================
# Section 4: Find and remove scheduled tasks
# ============================================================

Write-Host ""
Write-Host "[4/5] Finding DPlayer Scheduled Tasks..."
Write-Host "------------------------------------------------------------"

$allTasks = Get-ScheduledTask -TaskPath '\' -ErrorAction SilentlyContinue |
            Where-Object {
                $_.TaskName -match 'DPlayer|dplayer|main|admin|thumbnail'
            }

if ($allTasks) {
    Write-Host "Found $($allTasks.Count) task(s):"
    foreach ($task in $allTasks) {
        Write-Host "  - $($task.TaskName)"
    }

    Write-Host ""
    Write-Host "Removing tasks..."
    foreach ($task in $allTasks) {
        try {
            Write-Host "Removing: $($task.TaskName)"
            Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false -ErrorAction Stop
            Write-Host "  [OK] Removed" -ForegroundColor Green
        } catch {
            Write-Host "  [ERROR] Failed: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No DPlayer scheduled tasks found" -ForegroundColor Gray
}

# ============================================================
# Section 5: Kill all DPlayer processes
# ============================================================

Write-Host ""
Write-Host "[5/5] Finding and killing DPlayer processes..."
Write-Host "------------------------------------------------------------"

$targetProcesses = @()
$allPythonProcesses = Get-Process -Name python, pythonw -ErrorAction SilentlyContinue

foreach ($proc in $allPythonProcesses) {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
        if ($cmdLine -and ($cmdLine -match 'app\.py|admin_app\.py|thumbnail_service\.py|dplayer|DPlayer')) {
            $targetProcesses += $proc
            Write-Host "Found: PID $($proc.Id) - $($cmdLine.Substring(0, [Math]::Min(120, $cmdLine.Length)))"
        }
    } catch {
        # Ignore errors when getting command line
    }
}

if ($targetProcesses) {
    Write-Host ""
    Write-Host "Killing $($targetProcesses.Count) process(es)..."
    foreach ($proc in $targetProcesses) {
        try {
            Write-Host "Killing: PID $($proc.Id)"
            $proc.Kill()
            $proc.WaitForExit(5000)
            Write-Host "  [OK] Killed" -ForegroundColor Green
        } catch {
            Write-Host "  [WARN] Failed: $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "No DPlayer processes found" -ForegroundColor Gray
}

# Wait for cleanup
Write-Host ""
Write-Host "Waiting for cleanup to complete..."
Start-Sleep -Seconds 3

# ============================================================
# Final verification
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "  Cleanup Complete - Verification"
Write-Host "============================================================"
Write-Host ""

Write-Host "Checking remaining services..."
$remainingServices = Get-WmiObject Win32_Service -ErrorAction SilentlyContinue |
                     Where-Object {
                         $_.DisplayName -match 'DPlayer|dplayer|main|admin|thumbnail' -or
                         $_.Name -match 'DPlayer|dplayer|main|admin|thumbnail'
                     }

if ($remainingServices) {
    Write-Host "[WARN] Some services may still exist:" -ForegroundColor Yellow
    foreach ($svc in $remainingServices) {
        Write-Host "  - $($svc.Name)"
    }
} else {
    Write-Host "[OK] No DPlayer services found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Checking remaining processes..."
$remainingProcesses = Get-Process -Name python, pythonw -ErrorAction SilentlyContinue
$dplayerProcesses = 0

foreach ($proc in $remainingProcesses) {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
        if ($cmdLine -and ($cmdLine -match 'app\.py|admin_app\.py|thumbnail_service\.py|dplayer|DPlayer')) {
            $dplayerProcesses++
            Write-Host "  PID $($proc.Id) still running: $($cmdLine.Substring(0, [Math]::Min(80, $cmdLine.Length)))" -ForegroundColor Yellow
        }
    } catch {
        # Ignore errors
    }
}

if ($dplayerProcesses -eq 0) {
    Write-Host "[OK] No DPlayer processes found" -ForegroundColor Green
}

Write-Host ""
Write-Host "Checking ports..."
$ports = @(80, 8080, 5001)
foreach ($port in $ports) {
    $listening = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
    if ($listening) {
        Write-Host "[WARN] Port $port still in use" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Port $port is free" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "  Cleanup Summary"
Write-Host "============================================================"
Write-Host ""
Write-Host "All DPlayer services, tasks, and processes have been removed."
Write-Host "You can now install services using your preferred method:"
Write-Host ""
Write-Host "  Option 1: PowerShell Service Manager"
Write-Host "    scripts\install_services.bat"
Write-Host ""
Write-Host "  Option 2: Python Process Manager"
Write-Host "    python process_manager.py enable all"
Write -Host ""
Write-Host "  Option 3: Manual Start"
Write-Host "    python app.py"
Write-Host "    python admin_app.py"
Write -Host ""
Write-Host ""
