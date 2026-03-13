# Windows 防火墙配置脚本
# 自动为 Dplayer 应用端口添加防火墙白名单

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Dplayer 防火墙配置脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 端口配置
$MAIN_APP_PORT = 80
$ADMIN_PORT = 8080
$RULE_NAME_MAIN = "Dplayer Main App Port"
$RULE_NAME_ADMIN = "Dplayer Admin Dashboard Port"

# 检查管理员权限
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)

if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ 错误: 此脚本需要管理员权限运行" -ForegroundColor Red
    Write-Host "请右键点击脚本，选择'以管理员身份运行'" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "✅ 检测到管理员权限" -ForegroundColor Green
Write-Host ""

# 显示当前配置
Write-Host "配置信息:" -ForegroundColor Cyan
Write-Host "  主应用端口: $MAIN_APP_PORT (http://0.0.0.0:$MAIN_APP_PORT)" -ForegroundColor White
Write-Host "  管理端口: $ADMIN_PORT (http://0.0.0.0:$ADMIN_PORT)" -ForegroundColor White
Write-Host ""

# 获取本机IP地址
Write-Host "正在获取本机IP地址..." -ForegroundColor Yellow
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*" }
Write-Host ""

if ($ipAddresses.Count -gt 0) {
    Write-Host "本机IP地址:" -ForegroundColor Green
    foreach ($ip in $ipAddresses) {
        $interfaceAlias = $ip.InterfaceAlias
        $ipAddress = $ip.IPAddress
        Write-Host "  • $interfaceAlias: $ipAddress" -ForegroundColor White
        Write-Host "    主应用: http://$ipAddress`:$MAIN_APP_PORT" -ForegroundColor Cyan
        Write-Host "    管理后台: http://$ipAddress`:$ADMIN_PORT" -ForegroundColor Cyan
        Write-Host ""
    }
} else {
    Write-Host "⚠️  警告: 未找到有效的IP地址" -ForegroundColor Yellow
    Write-Host ""
}

# 配置防火墙规则
Write-Host "配置防火墙规则..." -ForegroundColor Yellow
Write-Host ""

# 检查并添加主应用端口规则
Write-Host "检查主应用端口规则 ($MAIN_APP_PORT)..." -ForegroundColor White
$existingRuleMain = Get-NetFirewallRule -DisplayName $RULE_NAME_MAIN -ErrorAction SilentlyContinue

if ($existingRuleMain) {
    Write-Host "  ℹ️  规则已存在，更新中..." -ForegroundColor Yellow

    # 删除现有规则
    Remove-NetFirewallRule -DisplayName $RULE_NAME_MAIN -ErrorAction SilentlyContinue

    # 重新添加规则
    New-NetFirewallRule -DisplayName $RULE_NAME_MAIN `
                        -Direction Inbound `
                        -LocalPort $MAIN_APP_PORT `
                        -Protocol TCP `
                        -Action Allow `
                        -Profile Any `
                        -Description "Dplayer 主应用端口 - 允许局域网访问"

    Write-Host "  ✅ 主应用端口规则已更新" -ForegroundColor Green
} else {
    Write-Host "  ➕ 添加主应用端口规则..." -ForegroundColor White

    New-NetFirewallRule -DisplayName $RULE_NAME_MAIN `
                        -Direction Inbound `
                        -LocalPort $MAIN_APP_PORT `
                        -Protocol TCP `
                        -Action Allow `
                        -Profile Any `
                        -Description "Dplayer 主应用端口 - 允许局域网访问"

    Write-Host "  ✅ 主应用端口规则已添加" -ForegroundColor Green
}

Write-Host ""

# 检查并添加管理后台端口规则
Write-Host "检查管理后台端口规则 ($ADMIN_PORT)..." -ForegroundColor White
$existingRuleAdmin = Get-NetFirewallRule -DisplayName $RULE_NAME_ADMIN -ErrorAction SilentlyContinue

if ($existingRuleAdmin) {
    Write-Host "  ℹ️  规则已存在，更新中..." -ForegroundColor Yellow

    # 删除现有规则
    Remove-NetFirewallRule -DisplayName $RULE_NAME_ADMIN -ErrorAction SilentlyContinue

    # 重新添加规则
    New-NetFirewallRule -DisplayName $RULE_NAME_ADMIN `
                        -Direction Inbound `
                        -LocalPort $ADMIN_PORT `
                        -Protocol TCP `
                        -Action Allow `
                        -Profile Any `
                        -Description "Dplayer 管理后台端口 - 允许局域网访问"

    Write-Host "  ✅ 管理后台端口规则已更新" -ForegroundColor Green
} else {
    Write-Host "  ➕ 添加管理后台端口规则..." -ForegroundColor White

    New-NetFirewallRule -DisplayName $RULE_NAME_ADMIN `
                        -Direction Inbound `
                        -LocalPort $ADMIN_PORT `
                        -Protocol TCP `
                        -Action Allow `
                        -Profile Any `
                        -Description "Dplayer 管理后台端口 - 允许局域网访问"

    Write-Host "  ✅ 管理后台端口规则已添加" -ForegroundColor Green
}

Write-Host ""

# 显示配置的规则
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "防火墙规则配置完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "已配置的规则:" -ForegroundColor Green
Write-Host ""

$rules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Dplayer*" }

foreach ($rule in $rules) {
    $displayName = $rule.DisplayName
    $enabled = if ($rule.Enabled) { "✅ 启用" } else { "❌ 禁用" }
    $action = if ($rule.Action -eq "Allow") { "允许" } else { "阻止" }
    $profile = $rule.Profile

    # 获取端口信息
    $portRule = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule
    $localPort = if ($portRule.LocalPort) { $portRule.LocalPort } else { "所有" }

    Write-Host "• $displayName" -ForegroundColor White
    Write-Host "  状态: $enabled" -ForegroundColor $(if ($rule.Enabled) { "Green" } else { "Red" })
    Write-Host "  动作: $action" -ForegroundColor Cyan
    Write-Host "  端口: $localPort" -ForegroundColor Yellow
    Write-Host "  配置: $profile" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 显示访问信息
Write-Host "🌐 局域网访问地址:" -ForegroundColor Green
Write-Host ""
Write-Host "本机访问:" -ForegroundColor White
Write-Host "  • 主应用: http://localhost:$MAIN_APP_PORT" -ForegroundColor Cyan
Write-Host "  • 管理后台: http://localhost:$ADMIN_PORT" -ForegroundColor Cyan
Write-Host ""

if ($ipAddresses.Count -gt 0) {
    Write-Host "局域网访问:" -ForegroundColor White
    foreach ($ip in $ipAddresses) {
        Write-Host "  • 主应用: http://$($ip.IPAddress):$MAIN_APP_PORT" -ForegroundColor Cyan
        Write-Host "  • 管理后台: http://$($ip.IPAddress):$ADMIN_PORT" -ForegroundColor Cyan
    }
    Write-Host ""
}

Write-Host "✅ 防火墙配置完成!" -ForegroundColor Green
Write-Host ""
Write-Host "注意事项:" -ForegroundColor Yellow
Write-Host "1. 确保两个应用都已启动" -ForegroundColor White
Write-Host "2. 局域网设备可以通过上述地址访问" -ForegroundColor White
Write-Host "3. 如需修改端口，请编辑此脚本中的端口号" -ForegroundColor White
Write-Host ""

Read-Host "按任意键退出"
