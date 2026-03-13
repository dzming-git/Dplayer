@echo off
chcp 65001 >nul
echo Setup AI Restart Permission for DPlayer Services
echo =========================================================
echo.
echo This will create a scheduled task that allows AI to restart services
echo.
echo IMPORTANT: Run this script as ADMINISTRATOR
echo.
pause

schtasks /create /tn "DPlayer_Restart_Admin" /tr "\"'c:\Users\71555\WorkBuddy\Dplayer\scripts\restart_services.py' admin\"" /sc weekly /d SUN /st 00:00 /ru SYSTEM /rl highest /f
schtasks /create /tn "DPlayer_Restart_Main" /tr "\"'c:\Users\71555\WorkBuddy\Dplayer\scripts\restart_services.py' main\"" /sc weekly /d SUN /st 00:00 /ru SYSTEM /rl highest /f
schtasks /create /tn "DPlayer_Restart_Thumbnail" /tr "\"'c:\Users\71555\WorkBuddy\Dplayer\scripts\restart_services.py' thumbnail\"" /sc weekly /d SUN /st 00:00 /ru SYSTEM /rl highest /f
schtasks /create /tn "DPlayer_Restart_All" /tr "\"'c:\Users\71555\WorkBuddy\Dplayer\scripts\restart_services.py' all\"" /sc weekly /d SUN /st 00:00 /ru SYSTEM /rl highest /f

echo.
echo =========================================================
echo Scheduled tasks created successfully!
echo.
echo Now AI can restart services by running:
echo   - schtasks /run /tn "DPlayer_Restart_Admin"
echo   - schtasks /run /tn "DPlayer_Restart_Main"
echo   - schtasks /run /tn "DPlayer_Restart_Thumbnail"
echo   - schtasks /run /tn "DPlayer_Restart_All"
echo.
pause
