@echo off
echo ========================================
echo 配置Windows防火墙规则 - 开放Web服务端口
echo ========================================
echo.

echo [1/4] 删除旧的防火墙规则（如果有）...
netsh advfirewall firewall delete rule name="DPlayer 主应用端口80" >nul 2>&1
netsh advfirewall firewall delete rule name="DPlayer 管理后台端口8080" >nul 2>&1
echo   旧的规则已删除

echo.
echo [2/4] 添加主应用端口80的入站规则...
netsh advfirewall firewall add rule name="DPlayer 主应用端口80" dir=in action=allow protocol=TCP localport=80
if %errorlevel% equ 0 (
    echo   主应用端口80规则添加成功
) else (
    echo   主应用端口80规则添加失败
    goto :error
)

echo.
echo [3/4] 添加管理后台端口8080的入站规则...
netsh advfirewall firewall add rule name="DPlayer 管理后台端口8080" dir=in action=allow protocol=TCP localport=8080
if %errorlevel% equ 0 (
    echo   管理后台端口8080规则添加成功
) else (
    echo   管理后台端口8080规则添加失败
    goto :error
)

echo.
echo [4/4] 验证防火墙规则...
echo.
echo 当前规则列表:
netsh advfirewall firewall show rule name="DPlayer 主应用端口80"
netsh advfirewall firewall show rule name="DPlayer 管理后台端口8080"

echo.
echo ========================================
echo 防火墙规则配置完成！
echo ========================================
echo.
echo 请重启DPlayer服务以应用更改
pause
goto :eof

:error
echo.
echo ========================================
echo 配置失败！
echo 请以管理员身份运行此脚本
echo ========================================
pause
