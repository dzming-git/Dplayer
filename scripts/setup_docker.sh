#!/bin/bash
# Docker部署快速设置脚本
# 用于创建必要的目录结构和配置文件

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Dplayer Docker 部署快速设置"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建基础目录结构
echo -e "${YELLOW}[1/5] 创建基础目录结构...${NC}"
mkdir -p data/config
mkdir -p content
mkdir -p logs
mkdir -p videos

# 创建默认内容目录
mkdir -p content/videos
mkdir -p content/thumbnails
mkdir -p content/uploads
mkdir -p content/static
mkdir -p content/cache

echo -e "${GREEN}✓ 基础目录结构创建完成${NC}"
echo ""

# 创建多实例目录结构（可选）
read -p "是否需要创建多实例部署？(y/n): " create_multi
if [ "$create_multi" = "y" ] || [ "$create_multi" = "Y" ]; then
    read -p "请输入实例数量 (1-10): " num_instances
    
    if [[ ! $num_instances =~ ^[0-9]+$ ]] || [ $num_instances -lt 1 ] || [ $num_instances -gt 10 ]; then
        echo "无效的实例数量，使用默认值 3"
        num_instances=3
    fi
    
    echo -e "${YELLOW}[2/5] 创建 $num_instances 个实例的目录结构...${NC}"
    for i in $(seq 1 $num_instances); do
        instance_name="instance-$i"
        mkdir -p "data/config/$instance_name"
        mkdir -p "content/$instance_name"/{videos,thumbnails,uploads,static,cache}
        mkdir -p "logs/$instance_name"
        echo -e "${GREEN}  ✓ 实例 $i: $instance_name${NC}"
    done
fi
echo ""

# 生成挂载配置文件
echo -e "${YELLOW}[3/5] 生成挂载配置文件...${NC}"

if [ "$create_multi" = "y" ] || [ "$create_multi" = "Y" ]; then
    # 生成多实例配置
    python scripts/mount_setup.py create-multi $num_instances -o .
else:
    # 生成单实例配置
    python scripts/mount_setup.py create-default
fi
echo -e "${GREEN}✓ 挂载配置文件生成完成${NC}"
echo ""

# 创建.env文件
echo -e "${YELLOW}[4/5] 创建环境变量文件...${NC}"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env 文件已创建（从 .env.example 复制）${NC}"
    else
        cat > .env << 'EOF'
# Dplayer Docker 配置

# 应用配置
DPLAYER_HOST=0.0.0.0
DPLAYER_PORT=80
DPLAYER_DEBUG=False
DPLAYER_SECRET_KEY=your-secret-key-here-change-in-production

# 缩略图服务配置
DPLAYER_THUMBNAIL_SERVICE_ENABLED=true
DPLAYER_THUMBNAIL_SERVICE_URL=http://thumbnail-service:5001
DPLAYER_THUMBNAIL_FALLBACK_ENABLED=true

# Git配置
DPLAYER_GIT_ENABLED=true
GIT_USER_NAME=Docker User
GIT_USER_EMAIL=docker@example.com

# 日志配置
DPLAYER_LOG_LEVEL=INFO

# 挂载配置
DPLAYER_MOUNT_CONFIG=/config/mounts.json
EOF
        echo -e "${GREEN}✓ .env 文件已创建（默认配置）${NC}"
    fi
else
    echo -e "${YELLOW}  ! .env 文件已存在，跳过创建${NC}"
fi
echo ""

# 创建README指导文件
echo -e "${YELLOW}[5/5] 创建部署指导文件...${NC}"
cat > DOCKER_DEPLOYMENT_QUICK_START.md << 'EOF'
# Dplayer Docker 部署快速开始

## 目录结构

```
Dplayer/
├── data/
│   └── config/          # 配置文件目录
├── content/             # 统一内容目录（所有挂载点）
│   ├── videos/          # 视频文件
│   ├── thumbnails/      # 缩略图
│   ├── uploads/         # 上传文件
│   ├── static/          # 静态资源
│   └── cache/           # 缓存
├── logs/                # 日志目录
└── videos/              # 外部视频目录（可选）
```

## 快速启动

### 单实例部署

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问: http://localhost:8080

### 多实例部署

```bash
# 启动多个实例
docker-compose -f docker-compose.flexible.yml up -d

# 查看状态
docker-compose -f docker-compose.flexible.yml ps

# 停止服务
docker-compose -f docker-compose.flexible.yml down
```

访问:
- 实例1: http://localhost:8081
- 实例2: http://localhost:8082
- 实例3: http://localhost:8083

## 添加视频

将视频文件复制到 `content/videos/` 目录：

```bash
cp /path/to/your/videos/* content/videos/
```

## 查看日志

```bash
# 所有日志
docker-compose logs -f dplayer

# 实时日志
docker-compose logs -f --tail=100 dplayer

# 特定实例
docker-compose -f docker-compose.flexible.yml logs -f dplayer-1
```

## 管理挂载

### 查看当前挂载配置

```bash
python scripts/mount_setup.py summary mounts_config.json
```

### 生成自定义docker-compose

```bash
python scripts/mount_setup.py generate-compose mounts_config.json -o docker-compose.custom.yml
docker-compose -f docker-compose.custom.yml up -d
```

## 故障排查

### 检查容器状态

```bash
docker-compose ps
```

### 查看容器日志

```bash
docker-compose logs dplayer
```

### 进入容器

```bash
docker-compose exec dplayer bash
```

### 重新构建镜像

```bash
docker-compose build --no-cache
docker-compose up -d
```

## 更多信息

详细文档请参考: DOCKER_DEPLOYMENT_GUIDE.md
EOF
echo -e "${GREEN}✓ 部署指导文件已创建${NC}"
echo ""

# 完成提示
echo "========================================="
echo -e "${GREEN}✓ Docker部署设置完成！${NC}"
echo "========================================="
echo ""
echo "下一步："
echo "  1. 编辑 .env 文件配置应用参数"
echo "  2. 将视频文件复制到 content/videos/ 目录"
echo "  3. 运行 docker-compose up -d 启动服务"
echo ""
echo "详细文档请查看: DOCKER_DEPLOYMENT_QUICK_START.md"
echo ""
