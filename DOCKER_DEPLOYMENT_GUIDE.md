# Dplayer Docker部署指南

## 概述

本文档介绍如何使用Docker部署Dplayer项目，包括单实例部署、多实例部署、灵活挂载配置等内容。

## 核心特性

- ✅ 统一内容目录挂载（/content）
- ✅ 灵活的多文件夹挂载配置
- ✅ 支持单实例和多实例部署
- ✅ 自动跨平台支持（Windows/Linux/macOS）
- ✅ 完全外部挂载配置、数据、日志
- ✅ 支持Git配置集成

## 快速开始

### 方式1: 自动设置（推荐）

#### Linux/macOS

```bash
# 运行自动设置脚本
bash scripts/setup_docker.sh

# 按照提示选择：
# - 是否创建多实例部署
# - 如果是多实例，输入实例数量

# 启动服务
docker-compose up -d
```

#### Windows

```cmd
# 运行自动设置脚本
scripts\setup_docker.bat

# 按照提示选择：
# - 是否创建多实例部署
# - 如果是多实例，输入实例数量

# 启动服务
docker-compose up -d
```

### 方式2: 手动设置

```bash
# 1. 创建基础目录
mkdir -p data/config content/{videos,thumbnails,uploads,static,cache} logs

# 2. 生成挂载配置
python scripts/mount_setup.py create-default

# 3. 复制环境变量文件
cp .env.example .env
# 编辑 .env 文件

# 4. 启动服务
docker-compose up -d
```

## 统一内容目录挂载

### 架构设计

Docker内部使用 `/content` 目录作为统一的内容挂载点，所有数据目录都挂载在这个目录下：

```
Docker内部:
/content/              # 统一内容根目录
├── videos/           # 视频文件
├── thumbnails/       # 缩略图
├── uploads/          # 上传文件
├── static/           # 静态资源
└── cache/            # 缓存
```

同时，为了兼容旧代码，创建了软链接：

```
/data/videos      -> /content/videos
/data/thumbnails  -> /content/thumbnails
/data/uploads     -> /content/uploads
/data/cache       -> /content/cache
```

### 挂载配置文件

通过 `mounts_config.json` 文件管理所有挂载点：

```json
{
  "mounts": {
    "videos": {
      "source": "/content/videos",
      "target": "/app/videos",
      "description": "视频文件目录",
      "read_only": true
    },
    "thumbnails": {
      "source": "/content/thumbnails",
      "target": "/app/thumbnails",
      "description": "缩略图目录",
      "read_only": false
    },
    "uploads": {
      "source": "/content/uploads",
      "target": "/app/uploads",
      "description": "上传文件目录",
      "read_only": false
    },
    "static": {
      "source": "/content/static",
      "target": "/app/static",
      "description": "静态资源目录",
      "read_only": true
    },
    "cache": {
      "source": "/content/cache",
      "target": "/app/cache",
      "description": "缓存目录",
      "read_only": false
    }
  }
}
```

## 目录结构

### 宿主机目录结构（推荐）

```
Dplayer/
├── data/
│   └── config/              # 配置文件目录
│       └── mounts.json      # 挂载配置
├── content/                 # 统一内容目录（外部挂载）
│   ├── videos/             # 视频文件
│   ├── thumbnails/         # 缩略图
│   ├── uploads/            # 上传文件
│   ├── static/             # 静态资源
│   └── cache/              # 缓存
├── logs/                    # 日志目录
│   ├── dplayer.log        # 主应用日志
│   └── thumbnail.log      # 缩略图服务日志
└── videos/                  # 外部视频目录（可选）
```

### 多实例目录结构

```
Dplayer/
├── data/
│   └── config/
│       ├── instance-1/
│       │   └── mounts_instance_1.json
│       ├── instance-2/
│       │   └── mounts_instance_2.json
│       └── instance-3/
│           └── mounts_instance_3.json
├── content/
│   ├── instance-1/
│   │   ├── videos/
│   │   ├── thumbnails/
│   │   ├── uploads/
│   │   ├── static/
│   │   └── cache/
│   ├── instance-2/
│   │   └── ...
│   └── instance-3/
│       └── ...
└── logs/
    ├── instance-1/
    ├── instance-2/
    └── instance-3/
```

## 部署方式

### 1. 单实例部署

使用默认配置：

```bash
docker-compose up -d
```

#### docker-compose.yml 配置

```yaml
volumes:
  # 配置文件挂载
  - ./data/config:/config
  # 统一内容目录挂载
  - ./content:/content
  # 日志目录挂载
  - ./logs:/logs
  # 挂载配置文件（可选）
  - ./mounts_config.json:/config/mounts.json:ro
```

#### 访问地址

- 主应用: http://localhost:8080
- 缩略图服务: http://localhost:5001

### 2. 多实例部署（标准）

使用预设的多实例配置：

```bash
docker-compose -f docker-compose.multi.yml up -d
```

#### 访问地址

| 实例 | 主应用端口 | 缩略图端口 | 访问地址 |
|------|-----------|-----------|---------|
| 实例1 | 8081 | 5001 | http://localhost:8081 |
| 实例2 | 8082 | 5002 | http://localhost:8082 |
| 实例3 | 8083 | 5003 | http://localhost:8083 |

### 3. 多实例部署（灵活）

使用灵活配置，支持自定义挂载：

```bash
docker-compose -f docker-compose.flexible.yml up -d
```

特性：
- 每个实例有独立的挂载配置文件
- 支持自定义实例数量
- 支持自定义端口映射

## 端口映射

### 单实例

| 服务 | 容器端口 | 主机端口 |
|------|---------|---------|
| 主应用 | 80 | 8080 |
| 缩略图服务 | 5001 | 5001 |

### 多实例

| 实例 | 主应用端口 | 缩略图端口 |
|------|-----------|-----------|
| 实例1 | 8081 | 5001 |
| 实例2 | 8082 | 5002 |
| 实例3 | 8083 | 5003 |

## 挂载配置管理

### 挂载配置工具

使用 `scripts/mount_setup.py` 工具管理挂载配置：

#### 查看帮助

```bash
python scripts/mount_setup.py --help
```

#### 创建默认配置

```bash
python scripts/mount_setup.py create-default
```

#### 创建实例配置

```bash
python scripts/mount_setup.py create-instance instance-1 -o .
```

#### 创建多个实例配置

```bash
python scripts/mount_setup.py create-multi 3 -o .
```

#### 从挂载配置生成docker-compose

```bash
python scripts/mount_setup.py generate-compose mounts_config.json -o docker-compose.custom.yml
docker-compose -f docker-compose.custom.yml up -d
```

#### 查看挂载配置摘要

```bash
python scripts/mount_setup.py summary mounts_config.json
```

#### 创建目录结构

```bash
python scripts/mount_setup.py create-dirs ./my-docker-instance
python scripts/mount_setup.py create-dirs ./my-docker-instance -i instance-1
```

### 自定义挂载

#### 方式1: 编辑挂载配置文件

编辑 `mounts_config.json`：

```json
{
  "mounts": {
    "videos": {
      "source": "/content/videos",
      "target": "/app/videos",
      "description": "视频文件目录",
      "read_only": true
    },
    "my_custom_dir": {
      "source": "/content/my_custom",
      "target": "/app/my_custom",
      "description": "自定义目录",
      "read_only": false
    }
  }
}
```

#### 方式2: 使用Python API

```python
from mount_config import MountConfig

config = MountConfig('mounts_config.json')

# 添加自定义挂载
config.add_mount(
    name='my_movies',
    source='/content/movies',
    target='/app/movies',
    description='我的电影目录',
    read_only=True
)

# 保存配置
config.save()
```

## 环境变量配置

### 基本配置

在 `.env` 文件中配置：

```env
# 应用配置
DPLAYER_HOST=0.0.0.0
DPLAYER_PORT=80
DPLAYER_DEBUG=False
DPLAYER_SECRET_KEY=your-secret-key-here

# 缩略图服务
DPLAYER_THUMBNAIL_SERVICE_ENABLED=true
DPLAYER_THUMBNAIL_SERVICE_URL=http://thumbnail-service:5001
DPLAYER_THUMBNAIL_FALLBACK_ENABLED=true

# Git配置
DPLAYER_GIT_ENABLED=true
GIT_USER_NAME=Docker User
GIT_USER_EMAIL=docker@example.com

# 日志
DPLAYER_LOG_LEVEL=INFO

# 挂载配置
DPLAYER_MOUNT_CONFIG=/config/mounts.json
```

### 从环境读取Git配置

```bash
docker run -e DPLAYER_GIT_ENABLED=true \
  -e DPLAYER_GIT_USER_NAME="$(git config user.name)" \
  -e DPLAYER_GIT_USER_EMAIL="$(git config user.email)" \
  dplayer:latest
```

## 常用命令

### 容器管理

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f dplayer

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec dplayer bash
```

### 镜像管理

```bash
# 构建镜像
docker-compose build

# 重新构建（无缓存）
docker-compose build --no-cache

# 查看镜像
docker images | grep dplayer
```

### 数据管理

```bash
# 查看挂载目录
docker-compose exec dplayer ls -la /content

# 查看配置
docker-compose exec dplayer cat /config/mounts.json

# 备份数据
docker-compose exec dplayer tar czf /backup/data.tar.gz /content
docker cp dplayer:/backup/data.tar.gz ./backup/
```

## 添加视频

### 方式1: 复制到content目录

```bash
# 复制视频文件
cp /path/to/your/videos/* content/videos/

# 重启容器以应用更改
docker-compose restart
```

### 方式2: 挂载外部视频目录

编辑 `docker-compose.yml`：

```yaml
volumes:
  - ./content:/content
  - /path/to/external/videos:/content/videos:ro  # 挂载外部视频目录
```

### 方式3: 使用自定义挂载配置

编辑 `mounts_config.json`：

```json
{
  "mounts": {
    "external_videos": {
      "source": "/external/videos",
      "target": "/app/videos",
      "description": "外部视频目录",
      "read_only": true
    }
  }
}
```

编辑 `docker-compose.yml`：

```yaml
volumes:
  - /path/to/external/videos:/external/videos:ro
```

## 跨平台支持

### 自动平台识别

应用会自动识别运行平台（Windows/Linux/macOS），无需手动配置：

```python
from config_manager import get_config

config = get_config()
if config.is_platform_windows():
    # Windows 特定逻辑
elif config.is_platform_linux():
    # Linux 特定逻辑
elif config.is_platform_macos():
    # macOS 特定逻辑
```

### Docker环境检测

应用会自动检测是否运行在Docker容器中：

```python
if config.is_docker:
    # Docker 特定逻辑
```

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs dplayer

# 检查配置
docker-compose config

# 验证挂载
docker-compose exec dplayer ls -la /content
```

### 权限问题

```bash
# Linux/macOS: 设置正确的权限
sudo chown -R $USER:$USER content logs data

# Docker: 使用正确的用户
docker-compose run --user $(id -u):$(id -g) dplayer bash
```

### 端口冲突

```bash
# 检查端口占用
lsof -i :8080  # Linux/macOS
netstat -ano | findstr :8080  # Windows

# 修改端口映射（编辑docker-compose.yml）
ports:
  - "8090:80"  # 改用8090端口
```

### 挂载失败

```bash
# 检查目录是否存在
ls -la content/

# 验证挂载配置
python scripts/mount_setup.py summary mounts_config.json

# 查看容器挂载
docker inspect dplayer-app | grep -A 10 Mounts
```

## 性能优化

### 资源限制

编辑 `docker-compose.yml`：

```yaml
services:
  dplayer:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 日志管理

```yaml
services:
  dplayer:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 生产环境部署

### 安全建议

1. 修改默认的 `DPLAYER_SECRET_KEY`
2. 启用HTTPS（使用反向代理如Nginx）
3. 配置防火墙规则
4. 定期备份数据
5. 使用只读挂载（如不需要写入）

### 备份策略

```bash
# 备份脚本
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份数据
docker-compose exec dplayer tar czf /backup/data.tar.gz /content
docker cp dplayer:/backup/data.tar.gz $BACKUP_DIR/

# 备份配置
cp -r data/config $BACKUP_DIR/
cp .env $BACKUP_DIR/
```

### 监控

```bash
# 查看容器状态
docker stats

# 查看资源使用
docker stats --no-stream
```

## 更多资源

- [Docker官方文档](https://docs.docker.com/)
- [Docker Compose文档](https://docs.docker.com/compose/)
- 项目GitHub仓库
- 示例配置文件: `.env.example`, `mounts_config.example.json`
