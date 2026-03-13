# Dplayer Docker部署指南

## 概述

本文档介绍如何使用Docker部署Dplayer项目，包括单实例部署、多实例部署、跨平台支持等内容。

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件
```

### 2. 启动服务

```bash
# 单实例
docker-compose up -d

# 多实例
docker-compose -f docker-compose.multi.yml up -d
```

### 3. 访问服务

- 单实例: http://localhost:8080
- 多实例: http://localhost:8081, 8082, 8083

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

## 目录挂载

```yaml
volumes:
  - ./data/config:/config        # 配置文件
  - ./data:/data                 # 数据（数据库、缩略图）
  - ./logs:/logs                 # 日志
  - ./videos:/data/videos:ro     # 视频（只读）
```

## Git配置

在 `.env` 中配置：

```bash
DPLAYER_GIT_ENABLED=true
DPLAYER_GIT_USER_NAME="Your Name"
DPLAYER_GIT_USER_EMAIL="your.email@example.com"
```

## 跨平台支持

自动识别Windows/Linux/macOS，无需手动配置。

详细内容请参考完整文档。

---

**文档版本**: 1.0
**最后更新**: 2026-03-13
