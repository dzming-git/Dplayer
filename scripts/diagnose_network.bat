@echo off
chcp 65001 >nul
echo ========================================
echo DPlayer 网络连接诊断工具
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

echo [1/6] 检查网络适配器状态...
powershell -Command "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, LinkSpeed | Format-Table -AutoSize"
echo.

echo [2/6] 检查IP地址配置...
ipconfig /all
echo.

echo [3/6] 检查端口监听状态...
echo 检查端口80和8080:
netstat -ano | findstr ":80"
netstat -ano | findstr ":8080"
echo.

echo [4/6] 检查防火墙规则...
echo 检查DPlayer相关防火墙规则:
netsh advfirewall firewall show rule name="DPlayer 主应用端口80" 2>nul
netsh advfirewall firewall show rule name="DPlayer 管理后台端口8080" 2>nul
echo.

echo [5/6] 检查TCP连接池状态...
echo 检查TIME_WAIT状态的连接:
netstat -ano | findstr "TIME_WAIT" | find /c "TIME_WAIT"
echo 检查ESTABLISHED状态的连接:
netstat -ano | findstr "ESTABLISHED" | find /c "ESTABLISHED"
echo.

echo [6/6] 网络连接测试...
echo 测试本地回环:
ping -n 2 127.0.0.1
echo.
echo 测试局域网IP:
ping -n 2 192.168.1.104
echo.
echo 测试端口80:
powershell -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 80 | Select-Object ComputerName, RemotePort, TcpTestSucceeded"
echo.
echo 测试端口8080:
powershell -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 8080 | Select-Object ComputerName, RemotePort, TcpTestSucceeded"
echo.

echo ========================================
echo 诊断完成！
echo ========================================
echo.
echo 常见问题及解决方案:
echo.
echo 1. 如果防火墙规则不存在：
echo    运行 scripts\setup_firewall.bat 添加防火墙规则
echo.
echo 2. 如果TIME_WAIT连接过多：
echo    运行 netsh int ipv4 set dynamicport tcp start=1025 num=64512
echo.
echo 3. 如果网络适配器有异常：
echo    运行 netsh winsock reset
echo    运行 netsh int ip reset
echo    然后重启电脑
echo.
echo 4. 如果端口未被监听：
echo    检查DPlayer服务是否正在运行
echo.
pause
