# Dplayer 测试用例列表

## 测试用例分类

### 1. 端口管理测试 (PORT)
- PORT-001: 检查端口是否被占用
- PORT-002: 查找占用端口的进程
- PORT-003: 终止占用端口的进程
- PORT-004: 批量终止占用端口的进程
- PORT-005: 确保端口可用（自动释放）
- PORT-006: 配置文件端口读取
- PORT-007: 端口验证脚本

### 2. 配置管理测试 (CONFIG)
- CONFIG-001: 读取配置文件
- CONFIG-002: 更新配置文件
- CONFIG-003: 配置热加载
- CONFIG-004: 默认配置回退
- CONFIG-005: 配置文件不存在处理
- CONFIG-006: 配置文件格式错误处理

### 3. 数据库测试 (DATABASE)
- DATABASE-001: 数据库连接测试
- DATABASE-002: 数据库表结构验证
- DATABASE-003: 视频模型CRUD操作
- DATABASE-004: 标签模型CRUD操作
- DATABASE-005: 视频标签关联
- DATABASE-006: 用户交互记录
- DATABASE-007: 用户偏好更新
- DATABASE-008: 数据库统计信息
- DATABASE-009: 数据库清理（dry-run）
- DATABASE-010: 数据库清理（实际执行）

### 4. 主应用API测试 (API_MAIN)

#### 4.1 视频管理API
- API_MAIN-001: 获取视频列表（无筛选）
- API_MAIN-002: 获取视频列表（分页）
- API_MAIN-003: 获取视频列表（标签筛选）
- API_MAIN-004: 获取视频列表（排序）
- API_MAIN-005: 获取推荐视频列表
- API_MAIN-006: 获取视频详情
- API_MAIN-007: 添加视频
- API_MAIN-008: 删除视频
- API_MAIN-009: 更新视频优先级
- API_MAIN-010: 重新生成视频缩略图
- API_MAIN-011: 清空所有视频数据

#### 4.2 标签管理API
- API_MAIN-012: 获取所有标签
- API_MAIN-013: 添加标签
- API_MAIN-014: 获取标签详情
- API_MAIN-015: 更新标签
- API_MAIN-016: 删除标签
- API_MAIN-017: 获取标签关联的视频
- API_MAIN-018: 获取视频的标签
- API_MAIN-019: 更新视频的标签

#### 4.3 用户交互API
- API_MAIN-020: 点赞视频
- API_MAIN-021: 收藏视频
- API_MAIN-022: 取消收藏视频
- API_MAIN-023: 检查视频收藏状态
- API_MAIN-024: 下载视频
- API_MAIN-025: 获取收藏列表
- API_MAIN-026: 获取排行榜（播放次数）
- API_MAIN-027: 获取排行榜（点赞次数）
- API_MAIN-028: 获取排行榜（下载次数）

#### 4.4 缩略图API
- API_MAIN-029: 检查缩略图状态
- API_MAIN-030: 获取缩略图（已存在）
- API_MAIN-031: 获取缩略图（不存在，触发生成）
- API_MAIN-032: 批量生成缩略图

#### 4.5 系统配置API
- API_MAIN-033: 获取系统配置
- API_MAIN-034: 更新系统配置

#### 4.6 页面路由
- API_MAIN-035: 访问首页
- API_MAIN-036: 访问标签页面
- API_MAIN-037: 访问视频播放页面
- API_MAIN-038: 访问搜索页面
- API_MAIN-039: 访问排行榜页面
- API_MAIN-040: 访问标签管理页面
- API_MAIN-041: 访问收藏页面
- API_MAIN-042: 播放本地视频文件

### 5. 管理后台API测试 (API_ADMIN)

#### 5.1 应用管理API
- API_ADMIN-001: 获取系统状态
- API_ADMIN-002: 启动主应用
- API_ADMIN-003: 停止主应用
- API_ADMIN-004: 重启主应用
- API_ADMIN-005: 检查主应用运行状态

#### 5.2 数据库管理API
- API_ADMIN-006: 获取数据库统计信息
- API_ADMIN-007: 清理数据库（dry-run）
- API_ADMIN-008: 清理数据库（实际执行）

#### 5.3 视频管理API
- API_ADMIN-009: 获取视频列表
- API_ADMIN-010: 添加视频
- API_ADMIN-011: 删除视频
- API_ADMIN-012: 获取视频详情
- API_ADMIN-013: 获取视频标签
- API_ADMIN-014: 更新视频标签
- API_ADMIN-015: 清空所有视频

#### 5.4 标签管理API
- API_ADMIN-016: 获取标签列表
- API_ADMIN-017: 添加标签
- API_ADMIN-018: 删除标签

#### 5.5 日志管理API
- API_ADMIN-019: 获取日志（所有类型）
- API_ADMIN-020: 获取日志（指定类型）
- API_ADMIN-021: 获取日志（指定行数）
- API_ADMIN-022: 获取日志文件列表
- API_ADMIN-023: 下载日志文件
- API_ADMIN-024: 清空日志（所有类型）
- API_ADMIN-025: 清空日志（指定类型）
- API_ADMIN-026: 获取日志目录大小

#### 5.6 缩略图管理API
- API_ADMIN-027: 批量重新生成缩略图

#### 5.7 代理API
- API_ADMIN-028: 获取配置（代理）
- API_ADMIN-029: 更新配置（代理）
- API_ADMIN-030: 扫描目录（代理）
- API_ADMIN-031: 检查依赖（代理）
- API_ADMIN-032: 获取收藏列表（代理）
- API_ADMIN-033: 获取排行榜（代理）

#### 5.8 管理页面路由
- API_ADMIN-034: 访问管理后台首页

### 6. 缩略图生成测试 (THUMBNAIL)

- THUMBNAIL-001: 生成GIF格式缩略图
- THUMBNAIL-002: 生成JPG格式缩略图
- THUMBNAIL-003: 获取视频时长
- THUMBNAIL-004: 提取视频帧
- THUMBNAIL-005: 缩略图懒加载
- THUMBNAIL-006: 缩略图生成状态管理
- THUMBNAIL-007: 并发缩略图生成控制
- THUMBNAIL-008: 缩略图生成失败处理
- THUMBNAIL-009: 批量生成缺失缩略图
- THUMBNAIL-010: 重新生成缩略图

### 7. 推荐系统测试 (RECOMMENDATION)

- RECOMMENDATION-001: 获取推荐视频（无历史）
- RECOMMENDATION-002: 获取推荐视频（有历史）
- RECOMMENDATION-003: 推荐视频排除已显示
- RECOMMENDATION-004: 标签偏好分析
- RECOMMENDATION-005: 推荐结果多样性

### 8. 日志系统测试 (LOGGING)

- LOGGING-001: 写入维护日志
- LOGGING-002: 写入运行日志
- LOGGING-003: 写入操作日志
- LOGGING-004: 写入调试日志
- LOGGING-005: 日志文件轮转
- LOGGING-006: 读取日志内容
- LOGGING-007: 解析日志行
- LOGGING-008: 自定义日志级别
- LOGGING-009: 获取日志列表
- LOGGING-010: 清空日志

### 9. 视频处理测试 (VIDEO_PROCESSING)

- VIDEO_PROCESSING-001: 检测视频时长
- VIDEO_PROCESSING-002: 获取视频信息
- VIDEO_PROCESSING-003: 提取视频帧
- VIDEO_PROCESSING-004: 视频文件不存在处理
- VIDEO_PROCESSING-005: 不支持的格式处理
- VIDEO_PROCESSING-006: 视频流式播放

### 10. 系统监控测试 (SYSTEM_MONITOR)

- SYSTEM_MONITOR-001: 获取CPU使用率
- SYSTEM_MONITOR-002: 获取内存使用情况
- SYSTEM_MONITOR-003: 获取磁盘空间
- SYSTEM_MONITOR-004: 监控进程资源
- SYSTEM_MONITOR-005: 系统状态聚合

### 11. 错误处理测试 (ERROR_HANDLING)

- ERROR_HANDLING-001: 404错误处理
- ERROR_HANDLING-002: 500错误处理
- ERROR_HANDLING-003: 参数验证错误
- ERROR_HANDLING-004: 权限错误处理
- ERROR_HANDLING-005: 数据库连接错误
- ERROR_HANDLING-006: 文件读写错误
- ERROR_HANDLING-007: 网络请求超时
- ERROR_HANDLING-008: JSON解析错误

### 12. 性能测试 (PERFORMANCE)

- PERFORMANCE-001: 视频列表查询性能
- PERFORMANCE-002: 缩略图生成性能
- PERFORMANCE-003: 批量操作性能
- PERFORMANCE-004: 并发请求处理
- PERFORMANCE-005: 大数据量处理
- PERFORMANCE-006: 日志文件大小控制

### 13. 集成测试 (INTEGRATION)

- INTEGRATION-001: 完整视频添加流程
- INTEGRATION-002: 完整视频播放流程
- INTEGRATION-003: 完整推荐流程
- INTEGRATION-004: 完整标签管理流程
- INTEGRATION-005: 完整收藏流程
- INTEGRATION-006: 完整应用重启流程
- INTEGRATION-007: 完整数据库清理流程
- INTEGRATION-008: 完整日志管理流程

### 14. 安全性测试 (SECURITY)

- SECURITY-001: SQL注入防护
- SECURITY-002: XSS防护
- SECURITY-003: CSRF防护
- SECURITY-004: 文件上传安全
- SECURITY-005: 路径遍历防护
- SECURITY-006: 认证和授权

### 15. 兼容性测试 (COMPATIBILITY)

- COMPATIBILITY-001: Windows系统兼容性
- COMPATIBILITY-002: Linux系统兼容性
- COMPATIBILITY-003: Mac系统兼容性
- COMPATIBILITY-004: 不同浏览器兼容性
- COMPATIBILITY-005: 移动端兼容性

### 16. 异步缩略图生成测试 (ASYNC_THUMBNAIL) ⭐ 新增

- ASYNC_THUMBNAIL-001: 提交单个异步缩略图生成任务
- ASYNC_THUMBNAIL-002: 查询任务状态（PENDING）
- ASYNC_THUMBNAIL-003: 查询任务状态（SUCCESS）
- ASYNC_THUMBNAIL-004: 查询任务状态（FAILURE）
- ASYNC_THUMBNAIL-005: 任务重试机制
- ASYNC_THUMBNAIL-006: 批量异步生成缩略图
- ASYNC_THUMBNAIL-007: 取消异步任务
- ASYNC_THUMBNAIL-008: 任务超时处理
- ASYNC_THUMBNAIL-009: Celery Worker状态检查
- ASYNC_THUMBNAIL-010: 并发任务处理
- ASYNC_THUMBNAIL-011: Redis消息代理连接测试
- ASYNC_THUMBNAIL-012: 任务结果获取

### 17. 播放列表功能测试 (PLAYLIST) ⭐ 新增

- PLAYLIST-001: 创建播放列表（无视频）
- PLAYLIST-002: 创建播放列表（包含视频）
- PLAYLIST-003: 获取所有播放列表
- PLAYLIST-004: 获取指定播放列表详情
- PLAYLIST-005: 更新播放列表信息
- PLAYLIST-006: 删除播放列表
- PLAYLIST-007: 添加视频到播放列表
- PLAYLIST-008: 从播放列表移除视频
- PLAYLIST-009: 重新排序播放列表项
- PLAYLIST-010: 播放播放列表
- PLAYLIST-011: 获取下一个视频（顺序播放）
- PLAYLIST-012: 获取上一个视频
- PLAYLIST-013: 随机播放
- PLAYLIST-014: 单曲循环模式
- PLAYLIST-015: 列表循环模式
- PLAYLIST-016: 播放列表为空处理
- PLAYLIST-017: 用户会话隔离
- PLAYLIST-018: 播放次数统计
- PLAYLIST-019: 当前播放位置记忆

### 18. 资源监控和限制测试 (RESOURCE_MONITOR) ⭐ 新增

- RESOURCE_MONITOR-001: CPU使用率监控
- RESOURCE_MONITOR-002: 内存使用率监控
- RESOURCE_MONITOR-003: 资源限制配置读取
- RESOURCE_MONITOR-004: 资源限制配置更新
- RESOURCE_MONITOR-005: 内存超限暂停处理
- RESOURCE_MONITOR-006: CPU超限暂停处理
- RESOURCE_MONITOR-007: 自动恢复机制
- RESOURCE_MONITOR-008: 资源阈值触发测试
- RESOURCE_MONITOR-009: 监控线程启动/停止
- RESOURCE_MONITOR-010: 资源违规统计
- RESOURCE_MONITOR-011: 上下文管理器模式
- RESOURCE_MONITOR-012: 资源限制禁用测试

### 19. Docker多文件夹挂载测试 (DOCKER_MOUNT) ⭐ 新增

- DOCKER_MOUNT-001: 挂载配置文件加载
- DOCKER_MOUNT-002: 单文件夹挂载
- DOCKER_MOUNT-003: 多文件夹挂载
- DOCKER_MOUNT-004: 读写权限配置
- DOCKER_MOUNT-005: 软链接创建验证
- DOCKER_MOUNT-006: Docker Compose卷配置生成
- DOCKER_MOUNT-007: 统一内容目录路径
- DOCKER_MOUNT-008: 向后兼容性验证
- DOCKER_MOUNT-009: 配置文件格式错误处理
- DOCKER_MOUNT-010: 环境变量配置测试

---

## 测试用例优先级

### P0 - 关键功能（必须通过）
- 所有API端点的基本功能测试
- 数据库CRUD操作
- 端口管理和配置管理
- 异步缩略图生成 ⭐ 新增
- 播放列表功能 ⭐ 新增

### P1 - 重要功能（应该通过）
- 缩略图生成
- 推荐系统
- 应用管理
- 日志系统
- 资源监控和限制 ⭐ 新增

### P2 - 一般功能（可以暂缓）
- 性能测试
- 兼容性测试
- 部分错误处理
- Docker多文件夹挂载 ⭐ 新增

### P3 - 可选功能（不强制）
- 安全性测试
- 高级功能测试

---

## 测试数据准备

### 1. 测试视频文件
- `test_video_1.mp4` - 标准MP4视频
- `test_video_2.avi` - AVI格式视频
- `test_video_3.mkv` - MKV格式视频
- `test_video_corrupted.mp4` - 损坏的视频文件

### 2. 测试数据库
- `test.db` - 测试数据库
- 初始测试数据（5个视频，3个标签）

### 3. 测试配置
- `test_config.json` - 测试配置文件
- `empty_config.json` - 空配置文件
- `invalid_config.json` - 无效配置文件

### 4. Docker配置 ⭐ 新增
- `mounts_config.example.json` - Docker挂载配置示例
- `docker-compose.yml` - Docker Compose配置
- `docker-compose.multi.yml` - 多文件夹挂载配置

### 5. Celery配置 ⭐ 新增
- `celery_config.py` - Celery任务配置
- Redis服务配置
- Worker启动脚本

---

## 测试环境要求

### 1. 基础环境
- Python 3.7+
- SQLite 3
- 端口 80 和 8080 可用
- Redis 服务器（用于Celery）⭐ 新增

### 2. 依赖包
- Flask
- SQLAlchemy
- psutil
- OpenCV (cv2)
- Pillow (PIL)
- requests
- Celery ⭐ 新增
- redis ⭐ 新增

### 3. 系统要求
- FFmpeg（用于视频处理）
- 至少1GB可用磁盘空间
- Docker（可选，用于Docker测试）⭐ 新增

### 4. 服务要求 ⭐ 新增
- Redis服务运行中（端口6379）
- Celery Worker进程运行中
- Docker守护进程（可选）

---

## 测试执行策略

### 1. 单元测试
- 测试单个函数和类
- 使用Mock对象隔离依赖
- 快速执行

### 2. 集成测试
- 测试模块间交互
- 使用真实数据库
- 中等执行时间

### 3. 端到端测试
- 测试完整用户流程
- 使用真实环境
- 较长执行时间

### 4. 性能测试
- 测试系统性能指标
- 负载测试
- 长时间执行

### 5. 异步任务测试 ⭐ 新增
- 测试Celery任务提交和执行
- 任务状态跟踪
- 错误处理和重试
- 并发任务处理

---

## 测试覆盖目标

| 测试类型 | 覆盖率目标 |
|---------|-----------|
| 代码覆盖率 | ≥ 80% |
| API覆盖率 | 100% |
| 功能覆盖率 | 100% |
| 分支覆盖率 | ≥ 75% |

---

## 测试报告

### 1. 测试摘要
- 测试用例总数
- 通过数量
- 失败数量
- 跳过数量
- 通过率

### 2. 详细结果
- 每个测试用例的执行结果
- 执行时间
- 错误信息
- 截图/日志

### 3. 趋势分析
- 历史测试结果对比
- 趋势图
- 回归分析

### 4. 新功能测试报告 ⭐ 新增
- 异步缩略图生成测试结果
- 播放列表功能测试结果
- 资源监控和限制测试结果
- Docker多文件夹挂载测试结果

---

## 自动化测试

### 1. 持续集成
- 代码提交自动运行测试
- 测试失败阻止合并
- 定时运行测试

### 2. 测试调度
- 每日自动运行
- 每周完整测试
- 发布前全面测试

### 3. 通知机制
- 测试失败通知
- 报告生成
- 问题跟踪

### 4. 异步任务监控 ⭐ 新增
- Celery任务状态监控
- Redis队列监控
- Worker健康检查

---

## 测试用例总数统计

- PORT: 7个
- CONFIG: 6个
- DATABASE: 10个
- API_MAIN: 42个
- API_ADMIN: 34个
- THUMBNAIL: 10个
- RECOMMENDATION: 5个
- LOGGING: 10个
- VIDEO_PROCESSING: 6个
- SYSTEM_MONITOR: 5个
- ERROR_HANDLING: 8个
- PERFORMANCE: 6个
- INTEGRATION: 8个
- SECURITY: 6个
- COMPATIBILITY: 5个
- ASYNC_THUMBNAIL: 12个 ⭐ 新增
- PLAYLIST: 19个 ⭐ 新增
- RESOURCE_MONITOR: 12个 ⭐ 新增
- DOCKER_MOUNT: 10个 ⭐ 新增

**总计：233个测试用例**（原168个 + 新增65个）
