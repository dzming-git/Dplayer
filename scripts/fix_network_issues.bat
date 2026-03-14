@echo off
chcp 65001 >nul
echo ========================================
echo DPlayer 网络问题一键修复工具
echo ========================================
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本
    echo 右键点击此文件 - 以管理员身份运行
    pause
    exit /b 1
)

echo 此脚本将执行以下操作:
echo   1. 配置Windows防火墙规则
echo   2. 优化TCP连接池设置
echo   3. 清理TIME_WAIT连接
echo   4. 刷新DNS缓存
echo.
echo 按任意键继续，或按Ctrl+C取消...
pause >nul

echo.
echo [1/5] 配置防火墙规则...
echo 删除旧规则...
netsh advfirewall firewall delete rule name="DPlayer 主应用端口80" >nul 2>&1
netsh advfirewall firewall delete rule name="DPlayer 管理后台端口8080" >nul 2>&1
echo 添加主应用端口80规则...
netsh advfirewall firewall add rule name="DPlayer 主应用端口80" dir=in action=allow protocol=TCP localport=80 profile=any
echo 添加管理后台端口8080规则...
netsh advfirewall firewall add rule name="DPlayer 管理后台端口8080" dir=in action=allow protocol=TCP localport=8080 profile=any
echo 防火墙规则配置完成

echo.
echo [2/5] 优化TCP连接池...
echo 增加动态端口范围...
netsh int ipv4 set dynamicport tcp start=1025 num=64512
echo 减少TIME_WAIT超时时间（30秒）...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v TcpTimedWaitDelay /t REG_DWORD /d 30 /f >nul 2>&1
echo TCP连接池优化完成

echo.
echo [3/5] 启用TCP保活机制...
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v KeepAliveTime /t REG_DWORD /d 3c000 /f >nul 2>&1
reg add "HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" /v KeepAliveInterval /t REG_DWORD /d 2710 /f >nul 2>&1
echo TCP保活机制已启用

echo.
echo [4/5] 刷新DNS缓存...
ipconfig /flushdns
echo DNS缓存已刷新

echo.
echo [5/5] 清理现有连接...
echo 查找并清理TIME_WAIT连接...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "TIME_WAIT"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo 连接清理完成

echo.
echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 后续步骤:
echo 1. 重启DPlayer服务:
echo    net stop dplayer_main
echo    net stop dplayer_admin
echo    net start dplayer_main
echo    net start dplayer_admin
echo.
echo 2. 从其他设备访问测试:
echo    http://192.168.1.104:80
echo    http://192.168.1.104:8080
echo.
echo 3. 如果问题仍然存在，请运行诊断脚本:
echo    scripts\diagnose_network.bat
echo.
echo 4. 查看详细文档:
echo    docs\NETWORK_TROUBLESHOOTING.md
echo.
pause
