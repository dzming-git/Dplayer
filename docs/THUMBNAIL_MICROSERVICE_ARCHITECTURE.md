# 缩略图微服务架构设计文档

## 1. 架构概述

### 1.1 设计目标

将缩略图生成功能从主应用（Dplayer）中完全解耦，使用微服务架构实现，提供以下优势：

- **完全解耦**：缩略图生成失败不影响主应用运行
- **独立部署**：可以单独部署、扩展、重启缩略图服务
- **技术独立**：可以使用不同的技术栈优化缩略图生成
- **可观测性**：独立监控和日志记录
- **弹性伸缩**：可以根据负载独立扩展缩略图服务实例

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        主应用 (app.py)                           │
│                   Port: 80 (0.0.0.0)                            │
├─────────────────────────────────────────────────────────────────┤
│  • 用户界面和视频管理                                             │
│  • 通过HTTP API调用缩略图服务                                      │
│  • 处理缩略图请求和状态查询                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP API
                            │ 请求缩略图生成
                            │ 查询生成状态
                            │ 获取缩略图文件
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  缩略图微服务 (thumbnail_service.py)            │
│                   Port: 5001 (0.0.0.0)                         │
├─────────────────────────────────────────────────────────────────┤
│  API端点:                                                       │
│  • POST   /api/thumbnail/generate      - 请求生成缩略图          │
│  • GET    /api/thumbnail/status/<id>   - 查询生成状态            │
│  • GET    /api/thumbnail/file/<hash>   - 获取缩略图文件          │
│  • GET    /health                     - 健康检查                 │
│  • GET    /metrics                    - 服务指标                 │
├─────────────────────────────────────────────────────────────────┤
│  核心功能:                                                       │
│  • 视频帧提取和缩略图生成 (使用OpenCV)                             │
│  • 异步任务队列                                                  │
│  • 任务状态管理                                                  │
│  • 结果缓存                                                      │
│  • 健康监控和日志                                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   本地文件系统  │
                    │ /thumbnails/  │
                    └───────────────┘
```

## 2. 服务设计

### 2.1 缩略图微服务 (thumbnail_service.py)

**端口配置**：
- 默认端口：`5001`
- 可配置端口：通过环境变量 `THUMBNAIL_SERVICE_PORT`

**核心API**：

#### 2.1.1 生成缩略图
```http
POST /api/thumbnail/generate
Content-Type: application/json

{
  "video_path": "/path/to/video.mp4",
  "video_hash": "abc123...",
  "output_format": "gif",  // 可选: "gif" 或 "jpg"
  "time_offset": 5,         // 可选: 截取时间点(秒)
  "size": [320, 180]        // 可选: 缩略图尺寸
}

Response:
{
  "success": true,
  "task_id": "thumb_task_20250313_123456",
  "status": "pending",
  "estimated_time": 3
}
```

#### 2.1.2 查询生成状态
```http
GET /api/thumbnail/status/<task_id>

Response:
{
  "success": true,
  "status": "completed",  // pending, processing, completed, failed
  "progress": 100,
  "thumbnail_path": "/thumbnails/abc123...gif",
  "format": "gif",
  "file_size": 25600,
  "error": null
}
```

#### 2.1.3 获取缩略图文件
```http
GET /api/thumbnail/file/<video_hash>

Response:
- 返回缩略图文件(GIF或JPG)
- Cache-Control: max-age=3600
```

#### 2.1.4 健康检查
```http
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "active_tasks": 3,
  "total_processed": 150,
  "success_rate": 98.5
}
```

#### 2.1.5 服务指标
```http
GET /metrics

Response:
{
  "tasks_total": 150,
  "tasks_completed": 148,
  "tasks_failed": 2,
  "avg_processing_time": 2.5,
  "queue_size": 5,
  "memory_usage": "256MB",
  "cpu_usage": "15%"
}
```

### 2.2 主应用集成 (app.py)

**修改点**：

1. **配置缩略图服务URL**：
   ```python
   THUMBNAIL_SERVICE_URL = os.getenv(
       'THUMBNAIL_SERVICE_URL', 
       'http://localhost:5001'
   )
   ```

2. **修改缩略图路由**：
   - `/thumbnail/<video_hash>` - 代理到微服务
   - `/api/thumbnail/<video_hash>/status` - 查询微服务状态

3. **异步生成流程**：
   - 主应用收到缩略图请求
   - 检查本地缓存
   - 如果不存在，调用微服务API生成
   - 轮询查询生成状态
   - 生成完成后缓存并返回

### 2.3 错误处理和降级策略

**微服务不可用时**：
- 主应用降级到本地生成模式
- 记录错误日志
- 显示默认缩略图
- 监控微服务健康状态

**微服务恢复后**：
- 自动恢复正常使用
- 清理降级标记

## 3. 数据流

### 3.1 缩略图生成流程

```
用户请求缩略图
    ↓
主应用检查本地缓存
    ↓ 未命中
请求微服务生成
    ↓
微服务创建任务并返回task_id
    ↓
微服务异步处理（后台线程）
    ↓
主应用轮询查询状态
    ↓
任务完成，返回缩略图
    ↓
主应用缓存并返回给用户
```

### 3.2 缩略图获取流程

```
用户请求缩略图
    ↓
主应用检查本地缓存
    ↓ 命中
直接返回缓存
    ↓ 未命中
代理到微服务 /api/thumbnail/file/<hash>
    ↓
微服务返回文件
    ↓
主应用缓存并返回
```

## 4. 技术实现细节

### 4.1 微服务技术栈

- **框架**：Flask
- **异步处理**：Python threading
- **任务队列**：内存队列（可扩展到Redis/RabbitMQ）
- **视频处理**：OpenCV (cv2)
- **日志**：Python logging + RotatingFileHandler
- **健康检查**：HTTP endpoint
- **指标监控**：内部指标统计

### 4.2 任务管理

```python
class Task:
    def __init__(self, task_id, video_path, video_hash, config):
        self.task_id = task_id
        self.video_path = video_path
        self.video_hash = video_hash
        self.status = 'pending'  # pending, processing, completed, failed
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.thumbnail_path = None
        self.format = None
        self.file_size = None
```

### 4.3 缓存策略

**两级缓存**：
1. **微服务本地缓存**：存储已生成的缩略图文件
2. **主应用缓存**：通过HTTP缓存头和本地存储

**缓存失效**：
- 基于时间：1小时
- 基于版本：视频hash变化时失效

### 4.4 并发控制

- **最大并发数**：可配置（默认5）
- **队列大小**：可配置（默认100）
- **超时控制**：单个任务最多30秒

## 5. 部署配置

### 5.1 环境变量

**缩略图微服务**：
```bash
THUMBNAIL_SERVICE_PORT=5001
THUMBNAIL_SERVICE_HOST=0.0.0.0
MAX_CONCURRENT_TASKS=5
QUEUE_SIZE=100
TASK_TIMEOUT=30
LOG_LEVEL=INFO
```

**主应用**：
```bash
THUMBNAIL_SERVICE_URL=http://localhost:5001
THUMBNAIL_FALLBACK_ENABLED=true
```

### 5.2 启动脚本

**启动所有服务**：
```bash
# Windows
start_all_services.bat

# Linux/Mac
./start_all.sh
```

**仅启动缩略图服务**：
```bash
# Windows
start_thumbnail_service.bat

# Linux/Mac
./start_thumbnail_service.sh
```

### 5.3 Docker部署（可选）

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY thumbnail_service.py .
CMD ["python", "thumbnail_service.py"]
```

```yaml
# docker-compose.yml
version: '3'
services:
  main_app:
    build: .
    ports:
      - "80:80"
    environment:
      - THUMBNAIL_SERVICE_URL=http://thumbnail_service:5001
    depends_on:
      - thumbnail_service

  thumbnail_service:
    build: .
    ports:
      - "5001:5001"
    environment:
      - THUMBNAIL_SERVICE_PORT=5001
```

## 6. 监控和日志

### 6.1 日志记录

**微服务日志**：
- `logs/thumbnail_service.log` - 主日志
- `logs/thumbnail_service_error.log` - 错误日志
- `logs/thumbnail_service_access.log` - 访问日志

**日志级别**：
- DEBUG: 详细的调试信息
- INFO: 正常运行信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 6.2 健康检查

```bash
curl http://localhost:5001/health
```

### 6.3 监控指标

- 任务总数
- 成功率
- 平均处理时间
- 队列大小
- 内存使用
- CPU使用率

## 7. 安全考虑

### 7.1 访问控制

- 仅允许来自主应用的请求（可配置IP白名单）
- API密钥认证（可选）

### 7.2 输入验证

- 验证视频路径合法性
- 限制文件大小
- 检测恶意文件

### 7.3 资源限制

- 限制并发任务数
- 限制单个任务CPU/内存使用
- 定期清理临时文件

## 8. 扩展性

### 8.1 水平扩展

可以启动多个缩略图服务实例，通过负载均衡器分发请求。

### 8.2 技术栈升级

未来可以：
- 使用Celery + Redis实现分布式任务队列
- 使用消息队列（RabbitMQ, Kafka）实现异步处理
- 使用FFmpeg替代OpenCV以获得更好的性能

### 8.3 功能扩展

- 支持多种缩略图格式（WebP, AVIF）
- 支持智能缩略图（基于视频内容）
- 支持缩略图压缩和优化
- 支持批量生成

## 9. 迁移计划

### 9.1 阶段1：微服务开发
- 创建thumbnail_service.py
- 实现核心API
- 编写单元测试

### 9.2 阶段2：主应用集成
- 修改app.py集成微服务调用
- 实现降级策略
- 端到端测试

### 9.3 阶段3：部署和监控
- 配置启动脚本
- 设置日志和监控
- 性能测试和优化

### 9.4 阶段4：数据迁移（可选）
- 迁移现有缩略图
- 清理旧代码

## 10. 总结

通过微服务架构，缩略图生成功能实现了完全解耦，提供了更好的：

- **可靠性**：独立的服务不会影响主应用
- **可扩展性**：可以根据负载独立扩展
- **可维护性**：代码更清晰，职责更明确
- **可观测性**：独立监控和日志
- **灵活性**：技术栈可以独立优化

这个架构为未来的功能扩展和性能优化打下了良好的基础。
