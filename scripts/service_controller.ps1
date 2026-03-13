#Requires -RunAsAdministrator
<#
.SYNOPSIS
    DPlayer Service Controller - 统一控制所有DPlayer服务
.DESCRIPTION
    提供对DPlayer所有服务的完整控制功能，包括启动、停止、重启、注册、卸载
.EXAMPLE
    .\service_controller.ps1 install
    .\service_controller.ps1 restart all
    .\service_controller.ps1 status admin
.NOTES
    需要管理员权限
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('install', 'uninstall', 'install-one', 'uninstall-one', 'start', 'stop', 'restart', 'status')]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [ValidateSet('admin', 'main', 'thumbnail', 'all')]
    [string]$Service = 'all',

    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# ============================================================
# 配置
# ============================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

$Services = @{
    'admin'      = @{
        Name = 'DPlayer-Admin'
        DisplayName = '管理服务'
        Script = Join-Path $ProjectDir 'services\admin_service.py'
        Port = 8080
    }
    'main'       = @{
        Name = 'DPlayer-Main'
        DisplayName = '主应用服务'
        Script = Join-Path $ProjectDir 'services\main_service.py'
        Port = 80
    }
    'thumbnail'  = @{
        Name = 'DPlayer-Thumbnail'
        DisplayName = '缩略图服务'
        Script = Join-Path $ProjectDir 'services\thumbnail_service_win.py'
        Port = 5001
    }
}

# ============================================================
# 工具函数
# ============================================================

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Gray
}

function Get-ServiceState {
    param([string]$ServiceName)

    try {
        $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($svc) {
            return $svc.Status
        }
    } catch {
        return "NOT_FOUND"
    }
}

function Test-PortListening {
    param([int]$Port)

    try {
        $listener = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                      Where-Object { $_.State -eq 'Listen' }
        return $listener -ne $null
    } catch {
        return $false
    }
}

function Get-ServicePID {
    param([string]$ServiceName)

    try {
        $result = & sc.exe queryex $ServiceName 2>&1
        if ($LASTEXITCODE -eq 0) {
            if ($result -match 'PID\s*:\s*(\d+)') {
                return $matches[1]
            }
        }
    } catch {
        return $null
    }
}

function Wait-ServiceState {
    param(
        [string]$ServiceName,
        [string]$DesiredState,
        [int]$Timeout = 30
    )

    Write-Host "  等待服务变为 $DesiredState..." -ForegroundColor Gray

    for ($i = 0; $i -lt $Timeout; $i++) {
        $state = Get-ServiceState $ServiceName
        if ($state -eq $DesiredState) {
            Write-Host "  [OK] 服务状态: $state" -ForegroundColor Green
            return $true
        }
        if ($state -eq "NOT_FOUND") {
            Write-Host "  [ERROR] 服务未找到" -ForegroundColor Red
            return $false
        }
        Start-Sleep -Seconds 1
    }

    Write-Host "  [TIMEOUT] 等待超时，当前状态: $state" -ForegroundColor Yellow
    return $false
}

# ============================================================
# 服务操作函数
# ============================================================

function Install-Service {
    param([string]$ServiceKey)

    $svc = $Services[$ServiceKey]
    Write-Info "注册 $($svc.DisplayName)..."

    # 检查旧服务
    $oldSvc = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if ($oldSvc) {
        Write-Host "  删除旧服务..." -ForegroundColor Gray
        try {
            Remove-Service -Name $svc.Name -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        } catch {
            Write-Warn "删除旧服务失败: $_"
        }
    }

    # 注册新服务
    $result = & python.exe $svc.Script install 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "$($svc.DisplayName) 已注册"
        return $true
    } else {
        Write-Error "$($svc.DisplayName) 注册失败"
        Write-Host "  错误: $result" -ForegroundColor Red
        return $false
    }
}

function Uninstall-Service {
    param([string]$ServiceKey)

    $svc = $Services[$ServiceKey]
    Write-Info "卸载 $($svc.DisplayName)..."

    # 先停止服务
    Stop-ServiceInternal $ServiceKey

    # 删除服务
    try {
        Remove-Service -Name $svc.Name -Force -ErrorAction Stop
        Write-Success "$($svc.DisplayName) 已卸载"
        return $true
    } catch {
        # 尝试使用 sc.exe
        $result = & sc.exe delete $svc.Name 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$($svc.DisplayName) 已卸载"
            return $true
        } else {
            Write-Error "$($svc.DisplayName) 卸载失败"
            Write-Host "  错误: $result" -ForegroundColor Red
            return $false
        }
    }
}

function Start-ServiceInternal {
    param([string]$ServiceKey)

    $svc = $Services[$ServiceKey]
    Write-Info "启动 $($svc.DisplayName)..."

    # 检查服务是否存在
    $exists = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if (-not $exists) {
        Write-Error "$($svc.DisplayName) 未注册，请先运行: service_controller.ps1 install $ServiceKey"
        return $false
    }

    # 启动服务
    try {
        Start-Service -Name $svc.Name -ErrorAction Stop
        Write-Success "$($svc.DisplayName) 启动中..."
    } catch {
        Write-Error "$($svc.DisplayName) 启动失败: $_"
        return $false
    }

    # 等待服务启动
    $success = Wait-ServiceState $svc.Name 'Running'
    if ($success) {
        Start-Sleep -Seconds 2
        
        # 检查端口监听
        $listening = Test-PortListening $svc.Port
        if ($listening) {
            Write-Success "$($svc.DisplayName) 启动成功，端口 $($svc.Port) 正在监听"
            return $true
        } else {
            Write-Warn "$($svc.DisplayName) 已启动但端口 $($svc.Port) 未监听，可能还在初始化"
            return $true
        }
    } else {
        return $false
    }
}

function Stop-ServiceInternal {
    param([string]$ServiceKey)

    $svc = $Services[$ServiceKey]
    Write-Info "停止 $($svc.DisplayName)..."

    # 检查服务是否存在
    $exists = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if (-not $exists) {
        Write-Info "$($svc.DisplayName) 未注册，跳过"
        return $true
    }

    # 检查是否已停止
    $state = Get-ServiceState $svc.Name
    if ($state -eq 'Stopped') {
        Write-Info "$($svc.DisplayName) 已经停止"
        return $true
    }

    # 停止服务
    try {
        Stop-Service -Name $svc.Name -Force -ErrorAction Stop
        Write-Success "$($svc.DisplayName) 停止中..."
    } catch {
        Write-Error "$($svc.DisplayName) 停止失败: $_"
        return $false
    }

    # 等待服务停止
    $success = Wait-ServiceState $svc.Name 'Stopped'
    if ($success) {
        # 检查端口释放
        $listening = Test-PortListening $svc.Port
        if (-not $listening) {
            Write-Success "$($svc.DisplayName) 已停止，端口 $($svc.Port) 已释放"
            return $true
        } else {
            Write-Warn "$($svc.DisplayName) 已停止但端口 $($svc.Port) 仍被占用"
            return $true
        }
    } else {
        return $false
    }
}

function Restart-ServiceInternal {
    param([string]$ServiceKey)

    $svc = $Services[$ServiceKey]

    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray
    Write-Host "重启 $($svc.DisplayName)" -ForegroundColor Cyan
    Write-Host "------------------------------------------------------------" -ForegroundColor Gray

    # 获取重启前的PID
    $oldPid = Get-ServicePID $svc.Name
    Write-Host "重启前 PID: $oldPid" -ForegroundColor Gray

    # 停止服务
    $stopSuccess = Stop-ServiceInternal $ServiceKey
    if (-not $stopSuccess) {
        Write-Error "停止失败，无法继续重启"
        return $false
    }

    # 等待完全停止
    Start-Sleep -Seconds 2

    # 启动服务
    $startSuccess = Start-ServiceInternal $ServiceKey
    if (-not $startSuccess) {
        Write-Error "启动失败，重启未完成"
        return $false
    }

    # 验证PID变化
    Start-Sleep -Seconds 2
    $newPid = Get-ServicePID $svc.Name
    Write-Host "重启后 PID: $newPid" -ForegroundColor Gray

    if ($oldPid -and $newPid -and $oldPid -ne $newPid) {
        Write-Success "PID 已变更 ($oldPid -> $newPid)，服务重启成功！"
        return $true
    } elseif ($oldPid -eq $newPid) {
        Write-Warn "PID 未变化，服务可能未正确重启"
        return $true
    } else {
        Write-Info "无法验证PID变化"
        return $true
    }
}

function Show-ServiceStatus {
    param([string]$ServiceKey)

    $svc = $Services[$ServiceKey]

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $($svc.DisplayName) ($($svc.Name))" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan

    # 服务注册状态
    $exists = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if (-not $exists) {
        Write-Host "状态: [NOT REGISTERED]" -ForegroundColor Red
        Write-Host "端口: $($svc.Port)"
        return
    }

    # 服务运行状态
    $state = Get-ServiceState $svc.Name
    if ($state -eq 'Running') {
        Write-Host "状态: [RUNNING]" -ForegroundColor Green
    } elseif ($state -eq 'Stopped') {
        Write-Host "状态: [STOPPED]" -ForegroundColor Red
    } elseif ($state -eq 'StartPending') {
        Write-Host "状态: [STARTING]" -ForegroundColor Yellow
    } else {
        Write-Host "状态: [$state]" -ForegroundColor Gray
    }

    # PID信息
    $pid = Get-ServicePID $svc.Name
    Write-Host "PID: $pid"

    # 端口监听
    $listening = Test-PortListening $svc.Port
    if ($listening) {
        Write-Host "端口: $($svc.Port) [LISTENING]" -ForegroundColor Green
    } else {
        Write-Host "端口: $($svc.Port) [NOT LISTENING]" -ForegroundColor Red
    }

    # 启动类型
    $svcObj = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if ($svcObj) {
        Write-Host "启动类型: $($svcObj.StartType)"
    }

    Write-Host ""
}

# ============================================================
# 主操作流程
# ============================================================

Write-Header "DPlayer Service Controller"

# 获取要操作的服务列表
if ($Service -eq 'all') {
    $targetServices = $Services.Keys
} else {
    if (-not $Services.ContainsKey($Service)) {
        Write-Error "未知的服务: $Service"
        Write-Host ""
        Write-Host "可用服务: $($Services.Keys -join ', ')"
        exit 1
    }
    $targetServices = @($Service)
}

# ============================================================
# 执行操作
# ============================================================

switch ($Action) {
    'install' {
        Write-Header "注册所有DPlayer服务"
        Write-Host ""
        Write-Host "[1/3] 删除旧服务..." -ForegroundColor Gray
        foreach ($key in $targetServices) {
            Uninstall-Service $key
        }

        Write-Host ""
        Write-Host "[2/3] 注册新服务..." -ForegroundColor Gray
        $allSuccess = $true
        foreach ($key in $targetServices) {
            $success = Install-Service $key
            if (-not $success) {
                $allSuccess = $false
            }
            Write-Host ""
        }

        if ($allSuccess) {
            Write-Host ""
            Write-Header "验证服务注册"
            foreach ($key in $targetServices) {
                Show-ServiceStatus $key
            }
            Write-Host ""
            Write-Success "所有服务注册完成！"
        } else {
            Write-Error "部分服务注册失败，请检查错误信息"
        }
    }

    'uninstall' {
        Write-Header "卸载所有DPlayer服务"
        Write-Host ""

        # 先停止所有服务
        Write-Host "[1/2] 停止所有服务..." -ForegroundColor Gray
        foreach ($key in $targetServices) {
            Stop-ServiceInternal $key
            Write-Host ""
        }

        # 卸载所有服务
        Write-Host "[2/2] 卸载服务..." -ForegroundColor Gray
        $allSuccess = $true
        foreach ($key in $targetServices) {
            $success = Uninstall-Service $key
            if (-not $success) {
                $allSuccess = $false
            }
            Write-Host ""
        }

        if ($allSuccess) {
            Write-Host ""
            Write-Success "所有服务卸载完成！"
        } else {
            Write-Error "部分服务卸载失败，请检查错误信息"
        }
    }

    'install-one' {
        if ($targetServices.Count -ne 1) {
            Write-Error "install-one 操作只能指定单个服务"
            exit 1
        }
        $key = $targetServices[0]

        Write-Header "注册单个服务"
        Write-Host ""

        Install-Service $key

        if ($?) {
            Write-Host ""
            Show-ServiceStatus $key
            Write-Success "服务注册完成！"
        }
    }

    'uninstall-one' {
        if ($targetServices.Count -ne 1) {
            Write-Error "uninstall-one 操作只能指定单个服务"
            exit 1
        }
        $key = $targetServices[0]

        Write-Header "卸载单个服务"
        Write-Host ""

        Uninstall-Service $key

        if ($?) {
            Write-Success "服务卸载完成！"
        }
    }

    'start' {
        Write-Header "启动DPlayer服务"
        Write-Host ""

        $allSuccess = $true
        foreach ($key in $targetServices) {
            $success = Start-ServiceInternal $key
            Write-Host ""
            if (-not $success) {
                $allSuccess = $false
            }
        }

        if ($allSuccess) {
            Write-Header "验证服务状态"
            foreach ($key in $targetServices) {
                Show-ServiceStatus $key
            }
        } else {
            Write-Error "部分服务启动失败，请检查错误信息"
        }
    }

    'stop' {
        Write-Header "停止DPlayer服务"
        Write-Host ""

        $allSuccess = $true
        foreach ($key in $targetServices) {
            $success = Stop-ServiceInternal $key
            Write-Host ""
            if (-not $success) {
                $allSuccess = $false
            }
        }

        if ($allSuccess) {
            Write-Header "验证服务状态"
            foreach ($key in $targetServices) {
                Show-ServiceStatus $key
            }
        } else {
            Write-Error "部分服务停止失败，请检查错误信息"
        }
    }

    'restart' {
        Write-Header "重启DPlayer服务"
        Write-Host ""

        $allSuccess = $true
        foreach ($key in $targetServices) {
            $success = Restart-ServiceInternal $key
            Write-Host ""
            if (-not $success) {
                $allSuccess = $false
            }
        }

        if ($allSuccess) {
            Write-Header "验证服务状态"
            foreach ($key in $targetServices) {
                Show-ServiceStatus $key
            }
            Write-Success "所有服务重启完成！"
        } else {
            Write-Error "部分服务重启失败，请检查错误信息"
        }
    }

    'status' {
        Write-Header "DPlayer服务状态"

        foreach ($key in $targetServices) {
            Show-ServiceStatus $key
        }

        # 统计摘要
        $runningCount = 0
        $stoppedCount = 0
        $notRegisteredCount = 0

        foreach ($key in $targetServices) {
            $svc = $Services[$key]
            $state = Get-ServiceState $svc.Name

            if ($state -eq 'Running') {
                $runningCount++
            } elseif ($state -eq 'Stopped') {
                $stoppedCount++
            } else {
                $notRegisteredCount++
            }
        }

        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "  摘要统计" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Cyan
        Write-Host "运行中: $runningCount"
        Write-Host "已停止: $stoppedCount"
        Write-Host "未注册: $notRegisteredCount"
    }

    default {
        Write-Host ""
        Write-Host "用法: .\service_controller.ps1 [操作] [服务]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "操作:" -ForegroundColor Gray
        Write-Host "  install        - 注册所有DPlayer服务" -ForegroundColor Gray
        Write-Host "  uninstall      - 卸载所有DPlayer服务" -ForegroundColor Gray
        Write-Host "  install-one    - 注册单个服务" -ForegroundColor Gray
        Write-Host "  uninstall-one  - 卸载单个服务" -ForegroundColor Gray
        Write-Host "  start         - 启动服务" -ForegroundColor Gray
        Write-Host "  stop          - 停止服务" -ForegroundColor Gray
        Write-Host "  restart       - 重启服务" -ForegroundColor Gray
        Write-Host "  status        - 查询服务状态" -ForegroundColor Gray
        Write-Host ""
        Write-Host "服务:" -ForegroundColor Gray
        Write-Host "  admin         - 管理服务 (DPlayer-Admin)" -ForegroundColor Gray
        Write-Host "  main          - 主应用服务 (DPlayer-Main)" -ForegroundColor Gray
        Write-Host "  thumbnail      - 缩略图服务 (DPlayer-Thumbnail)" -ForegroundColor Gray
        Write-Host "  all           - 所有DPlayer服务(默认)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "示例:" -ForegroundColor Gray
        Write-Host "  .\service_controller.ps1 install" -ForegroundColor Gray
        Write-Host "  .\service_controller.ps1 start all" -ForegroundColor Gray
        Write-Host "  .\service_controller.ps1 restart admin" -ForegroundColor Gray
        Write-Host "  .\service_controller.ps1 status" -ForegroundColor Gray
        Write-Host ""
        Write-Host "注意: 需要管理员权限运行此脚本" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "操作完成！" -ForegroundColor Green
Write-Host ""
