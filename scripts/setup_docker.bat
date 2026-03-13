@echo off
REM Docker deployment quick setup script (Windows)
REM Creates required directory structure and configuration files

setlocal enabledelayedexpansion

echo =========================================
echo Dplayer Docker Deployment Quick Setup
echo =========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

cd /d "%PROJECT_ROOT%"

echo [1/5] Creating base directory structure...
mkdir data\config 2>nul
mkdir content 2>nul
mkdir logs 2>nul
mkdir videos 2>nul

mkdir content\videos 2>nul
mkdir content\thumbnails 2>nul
mkdir content\uploads 2>nul
mkdir content\static 2>nul
mkdir content\cache 2>nul

echo [OK] Base directory structure created
echo.

REM Ask about multi-instance setup
set /p create_multi="Create multi-instance deployment? (y/n): "
if /i "%create_multi%"=="y" (
    set /p num_instances="Number of instances (1-10): "

    REM Validate input
    if "!num_instances!" lss "1" set num_instances=1
    if "!num_instances!" gtr "10" set num_instances=10

    echo [2/5] Creating !num_instances! instance directory structure...
    for /l %%i in (1,1,!num_instances!) do (
        set instance_name=instance-%%i
        mkdir data\config\!instance_name! 2>nul
        mkdir content\!instance_name!\videos 2>nul
        mkdir content\!instance_name!\thumbnails 2>nul
        mkdir content\!instance_name!\uploads 2>nul
        mkdir content\!instance_name!\static 2>nul
        mkdir content\!instance_name!\cache 2>nul
        mkdir logs\!instance_name! 2>nul
        echo   [OK] Instance %%i: !instance_name!
    )
)

echo.
echo [3/5] Generating mount config file...

if /i "%create_multi%"=="y" (
    REM Generate multi-instance config
    for /l %%i in (1,1,!num_instances!) do (
        set instance_name=instance-%%i
        python scripts\mount_setup.py create-instance !instance_name! -o .
    )
) else (
    REM Generate single-instance config
    python scripts\mount_setup.py create-default
)

echo [OK] Mount config generated
echo.

echo [4/5] Creating environment file...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [OK] .env created (copied from .env.example)
    ) else (
        (
            echo # Dplayer Docker Configuration
            echo.
            echo # App settings
            echo DPLAYER_HOST=0.0.0.0
            echo DPLAYER_PORT=80
            echo DPLAYER_DEBUG=False
            echo DPLAYER_SECRET_KEY=your-secret-key-here-change-in-production
            echo.
            echo # Thumbnail service
            echo DPLAYER_THUMBNAIL_SERVICE_ENABLED=true
            echo DPLAYER_THUMBNAIL_SERVICE_URL=http://thumbnail-service:5001
            echo DPLAYER_THUMBNAIL_FALLBACK_ENABLED=true
            echo.
            echo # Git config
            echo DPLAYER_GIT_ENABLED=true
            echo GIT_USER_NAME=Docker User
            echo GIT_USER_EMAIL=docker@example.com
            echo.
            echo # Logging
            echo DPLAYER_LOG_LEVEL=INFO
            echo.
            echo # Mount config
            echo DPLAYER_MOUNT_CONFIG=/config/mounts.json
        ) > .env
        echo [OK] .env created (default config)
    )
) else (
    echo [!] .env already exists, skipping
)
echo.

echo [5/5] Creating deployment guide...
(
echo # Dplayer Docker Quick Start ^(Windows^)
echo.
echo ## Directory Structure
echo.
echo ```
echo Dplayer/
echo ^|-- data/
echo ^|   ^`-- config/          # Config files
echo ^|-- content/             # Unified content directory
echo ^|   ^|-- videos/          # Video files
echo ^|   ^|-- thumbnails/      # Thumbnails
echo ^|   ^|-- uploads/         # Uploaded files
echo ^|   ^|-- static/          # Static assets
echo ^|   ^`-- cache/           # Cache
echo ^|-- logs/                # Log files
echo ^`-- videos/              # External video dir (optional)
echo ```
echo.
echo ## Quick Start
echo.
echo ### Single Instance
echo.
echo ```cmd
echo docker-compose up -d
echo docker-compose logs -f
echo docker-compose down
echo ```
echo.
echo Access: http://localhost:8080
echo.
echo ### Multi-Instance
echo.
echo ```cmd
echo docker-compose -f docker-compose.flexible.yml up -d
echo docker-compose -f docker-compose.flexible.yml ps
echo docker-compose -f docker-compose.flexible.yml down
echo ```
echo.
echo Access:
echo - Instance 1: http://localhost:8081
echo - Instance 2: http://localhost:8082
echo - Instance 3: http://localhost:8083
echo.
echo ## Add Videos
echo.
echo Copy video files to content\videos\:
echo.
echo ```cmd
echo copy /path/to/your/videos/* content\videos\
echo ```
echo.
echo ## View Logs
echo.
echo ```cmd
echo docker-compose logs -f dplayer
echo docker-compose logs -f --tail=100 dplayer
echo docker-compose -f docker-compose.flexible.yml logs -f dplayer-1
echo ```
echo.
echo ## More Info
echo.
echo See: DOCKER_DEPLOYMENT_GUIDE.md
) > DOCKER_DEPLOYMENT_QUICK_START.md
echo [OK] Deployment guide created
echo.

echo =========================================
echo [OK] Docker setup complete!
echo =========================================
echo.
echo Next steps:
echo   1. Edit .env to configure app parameters
echo   2. Copy video files to content\videos\
echo   3. Run docker-compose up -d to start services
echo.
echo See: DOCKER_DEPLOYMENT_QUICK_START.md
echo.

pause
