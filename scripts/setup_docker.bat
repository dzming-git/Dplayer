@echo off
REM Docker部署快速设置脚本 (Windows版本)
REM 用于创建必要的目录结构和配置文件

setlocal enabledelayedexpansion

echo =========================================
echo Dplayer Docker 部署快速设置
echo =========================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

cd /d "%PROJECT_ROOT%"

echo [1/5] 创建基础目录结构...
mkdir data\config 2>nul
mkdir content 2>nul
mkdir logs 2>nul
mkdir videos 2>nul

mkdir content\videos 2>nul
mkdir content\thumbnails 2>nul
mkdir content\uploads 2>nul
mkdir content\static 2>nul
mkdir content\cache 2>nul

echo [OK] 基础目录结构创建完成
echo.

REM 询问是否创建多实例
set /p create_multi="是否需要创建多实例部署？(y/n): "
if /i "%create_multi%"=="y" (
    set /p num_instances="请输入实例数量 (1-10): "

    REM 验证输入
    if "!num_instances!" lss "1" set num_instances=1
    if "!num_instances!" gtr "10" set num_instances=10

    echo [2/5] 创建 !num_instances! 个实例的目录结构...
    for /l %%i in (1,1,!num_instances!) do (
        set instance_name=instance-%%i
        mkdir data\config\!instance_name! 2>nul
        mkdir content\!instance_name!\videos 2>nul
        mkdir content\!instance_name!\thumbnails 2>nul
        mkdir content\!instance_name!\uploads 2>nul
        mkdir content\!instance_name!\static 2>nul
        mkdir content\!instance_name!\cache 2>nul
        mkdir logs\!instance_name! 2>nul
        echo   [OK] 实例 %%i: !instance_name!
    )
)

echo.
echo [3/5] 生成挂载配置文件...

if /i "%create_multi%"=="y" (
    REM 生成多实例配置
    for /l %%i in (1,1,!num_instances!) do (
        set instance_name=instance-%%i
        python scripts\mount_setup.py create-instance !instance_name! -o .
    )
) else (
    REM 生成单实例配置
    python scripts\mount_setup.py create-default
)

echo [OK] 挂载配置文件生成完成
echo.

echo [4/5] 创建环境变量文件...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [OK] .env 文件已创建（从 .env.example 复制）
    ) else (
        (
            echo # Dplayer Docker 配置
            echo.
            echo # 应用配置
            echo DPLAYER_HOST=0.0.0.0
            echo DPLAYER_PORT=80
            echo DPLAYER_DEBUG=False
            echo DPLAYER_SECRET_KEY=your-secret-key-here-change-in-production
            echo.
            echo # 缩略图服务配置
            echo DPLAYER_THUMBNAIL_SERVICE_ENABLED=true
            echo DPLAYER_THUMBNAIL_SERVICE_URL=http://thumbnail-service:5001
            echo DPLAYER_THUMBNAIL_FALLBACK_ENABLED=true
            echo.
            echo # Git配置
            echo DPLAYER_GIT_ENABLED=true
            echo GIT_USER_NAME=Docker User
            echo GIT_USER_EMAIL=docker@example.com
            echo.
            echo # 日志配置
            echo DPLAYER_LOG_LEVEL=INFO
            echo.
            echo # 挂载配置
            echo DPLAYER_MOUNT_CONFIG=/config/mounts.json
        ) > .env
        echo [OK] .env 文件已创建（默认配置）
    )
) else (
    echo [!] .env 文件已存在，跳过创建
)
echo.

echo [5/5] 创建部署指导文件...
(
echo # Dplayer Docker 部署快速开始 ^(Windows^)
echo.
echo ## 目录结构
echo.
echo ```
echo Dplayer/
echo ├── data/
echo │   └── config/          # 配置文件目录
echo ├── content/             # 统一内容目录（所有挂载点）
echo │   ├── videos/          # 视频文件
echo │   ├── thumbnails/      # 缩略图
echo │   ├── uploads/         # 上传文件
echo │   ├── static/          # 静态资源
echo │   └── cache/           # 缓存
echo ├── logs/                # 日志目录
echo └── videos/              # 外部视频目录（可选）
echo ```
echo.
echo ## 快速启动
echo.
echo ### 单实例部署
echo.
echo ```cmd
echo # 启动服务
echo docker-compose up -d
echo.
echo # 查看日志
echo docker-compose logs -f
echo.
echo # 停止服务
echo docker-compose down
echo ```
echo.
echo 访问: http://localhost:8080
echo.
echo ### 多实例部署
echo.
echo ```cmd
echo # 启动多个实例
echo docker-compose -f docker-compose.flexible.yml up -d
echo.
echo # 查看状态
echo docker-compose -f docker-compose.flexible.yml ps
echo.
echo # 停止服务
echo docker-compose -f docker-compose.flexible.yml down
echo ```
echo.
echo 访问:
echo - 实例1: http://localhost:8081
echo - 实例2: http://localhost:8082
echo - 实例3: http://localhost:8083
echo.
echo ## 添加视频
echo.
echo 将视频文件复制到 `content\videos\` 目录：
echo.
echo ```cmd
echo copy /path/to/your/videos/* content\videos\
echo ```
echo.
echo ## 查看日志
echo.
echo ```cmd
echo # 所有日志
echo docker-compose logs -f dplayer
echo.
echo # 实时日志
echo docker-compose logs -f --tail=100 dplayer
echo.
echo # 特定实例
echo docker-compose -f docker-compose.flexible.yml logs -f dplayer-1
echo ```
echo.
echo ## 管理挂载
echo.
echo ### 查看当前挂载配置
echo.
echo ```cmd
echo python scripts\mount_setup.py summary mounts_config.json
echo ```
echo.
echo ### 生成自定义docker-compose
echo.
echo ```cmd
echo python scripts\mount_setup.py generate-compose mounts_config.json -o docker-compose.custom.yml
echo docker-compose -f docker-compose.custom.yml up -d
echo ```
echo.
echo ## 故障排查
echo.
echo ### 检查容器状态
echo.
echo ```cmd
echo docker-compose ps
echo ```
echo.
echo ### 查看容器日志
echo.
echo ```cmd
echo docker-compose logs dplayer
echo ```
echo.
echo ### 进入容器
echo.
echo ```cmd
echo docker-compose exec dplayer bash
echo ```
echo.
echo ### 重新构建镜像
echo.
echo ```cmd
echo docker-compose build --no-cache
echo docker-compose up -d
echo ```
echo.
echo ## 更多信息
echo.
echo 详细文档请参考: DOCKER_DEPLOYMENT_GUIDE.md
) > DOCKER_DEPLOYMENT_QUICK_START.md
echo [OK] 部署指导文件已创建
echo.

echo =========================================
echo [OK] Docker部署设置完成！
echo =========================================
echo.
echo 下一步：
echo   1. 编辑 .env 文件配置应用参数
echo   2. 将视频文件复制到 content\videos\ 目录
echo   3. 运行 docker-compose up -d 启动服务
echo.
echo 详细文档请查看: DOCKER_DEPLOYMENT_QUICK_START.md
echo.

pause
