# Dplayer 功能文档

## 目录

1. [概述](#概述)
2. [主应用功能 (app.py)](#主应用功能-apppy)
3. [管理后台功能 (admin_app.py)](#管理后台功能-admin_apppy)
4. [数据库模型 (models.py)](#数据库模型-modelspy)
5. [核心功能模块](#核心功能模块)
6. [辅助工具](#辅助工具)

---

## 概述

Dplayer 是一个功能完整的本地视频管理和播放平台，采用双应用架构：
- **主应用 (app.py)**：视频播放、推荐、用户交互等功能
- **管理后台 (admin_app.py)**：系统管理、数据库维护、日志监控等功能

---

## 主应用功能 (app.py)

### 1. 页面路由

| 路由 | 方法 | 功能描述 |
|------|------|----------|
| `/` | GET | 首页 - 显示推荐视频列表 |
| `/tag/<int:tag_id>` | GET | 标签页面 - 显示特定标签下的所有视频 |
| `/video/<video_hash>` | GET | 视频播放页面 - 播放指定视频 |
| `/search` | GET | 搜索功能页面 |
| `/ranking` | GET | 排行榜页面 - 按播放/点赞/下载次数排序 |
| `/tags` | GET | 标签管理页面 - 管理所有标签 |
| `/favorites` | GET | 收藏页面 - 显示用户收藏的视频列表 |
| `/local_video/<path:video_path>` | GET | 提供本地视频文件流式播放服务 |

### 2. API 端点 - 视频管理

#### 2.1 视频列表与详情

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/videos` | GET | 获取视频列表（支持分页和标签筛选） | `page`, `per_page`, `tag_id`, `sort_by` |
| `/api/videos/recommend` | GET | 获取推荐视频列表（支持排除已显示） | `exclude`, `limit` |
| `/api/video/<video_hash>` | GET | 获取单个视频详情 | 无 |
| `/api/video/<video_hash>/like` | POST | 点赞视频 | 无 |
| `/api/video/<video_hash>/download` | POST/GET | 下载视频（模拟） | 无 |
| `/api/video/<video_hash>/priority` | POST | 更新视频优先级 | `priority` |
| `/api/video/<video_hash>/regenerate` | POST | 重新生成视频缩略图和更新时长 | 无 |

#### 2.2 缩略图管理

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/thumbnail/<video_hash>/status` | GET | 检查缩略图是否已生成 | 无 |
| `/thumbnail/<video_hash>` | GET | 懒加载缩略图（不存在则异步生成） | 无 |

#### 2.3 标签管理

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/tags` | GET | 获取所有标签（按关联视频数降序） | 无 |
| `/api/tags/add` | POST | 添加新标签 | `name`, `category` |
| `/api/tags/<int:tag_id>` | GET | 获取标签详情 | 无 |
| `/api/tags/<int:tag_id>` | PUT | 更新标签 | `name`, `category` |
| `/api/tags/<int:tag_id>` | DELETE | 删除标签 | 无 |
| `/api/tags/<int:tag_id>/videos` | GET | 获取标签关联的所有视频 | 无 |
| `/api/video/<video_hash>/tags` | GET | 获取视频的标签列表 | 无 |
| `/api/video/<video_hash>/tags` | PUT | 更新视频的标签 | `tag_ids` |

#### 2.4 用户交互

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/video/<video_hash>/favorite` | POST | 切换视频收藏状态 | 无 |
| `/api/video/<video_hash>/is-favorite` | GET | 检查视频是否已收藏 | 无 |
| `/api/favorites` | GET | 获取收藏列表 | 无 |
| `/api/ranking` | GET | 获取排行榜数据 | `type`, `limit` |

#### 2.5 系统配置

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/config` | GET | 获取系统配置 | 无 |
| `/api/config` | PUT | 更新系统配置 | 配置JSON |
| `/api/videos/clear` | POST | 清空所有视频数据 | `confirmation` |

### 3. 核心功能模块

#### 3.1 缩略图生成系统

**功能特性**：
- **懒加载机制**：首次请求返回202状态码并后台生成
- **并发控制**：限制同时生成2个缩略图
- **双格式支持**：GIF动态图和JPG静态图
- **状态管理**：记录生成状态（pending/generating/ready/failed）
- **自动时长检测**：使用FFmpeg检测视频时长
- **智能采样**：自动选择最佳帧生成缩略图

**关键函数**：
- `generate_thumbnail(video_path, output_path_gif, output_path_jpg)`
- `get_video_duration(video_path)`
- `generate_missing_thumbnails_async()`

#### 3.2 推荐系统

**功能特性**：
- 基于用户交互历史（浏览、点赞、收藏、下载）
- 考虑标签偏好和权重
- 支持换一批功能
- 个性化推荐算法

**关键函数**：
- `get_recommended_videos(exclude_hashes=None, limit=12)`

#### 3.3 视频处理功能

**功能特性**：
- 视频时长自动检测（使用FFmpeg）
- 缩略图生成（使用OpenCV + PIL）
- 视频帧提取
- 批量缩略图生成

**关键函数**：
- `extract_video_frames(video_path, output_dir, num_frames=10)`
- `get_video_info(video_path)`

#### 3.4 日志系统

**功能特性**：
- 多类型日志：维护日志、运行日志、操作日志、调试日志
- 自动轮转：每个日志文件最大10MB，保留5个备份
- 结构化日志解析
- 自定义日志级别（CRITICAL/ERROR/INFO/NOTICE/DEBUG）

**日志类型**：
- `maintenance.log` - 维护日志
- `runtime.log` - 运行日志
- `operation.log` - 操作日志
- `debug.log` - 调试日志

**关键函数**：
- `get_log_content(log_type, lines=100)`
- `parse_log_line(line)`

#### 3.5 端口管理

**功能特性**：
- 端口占用检查
- 强制释放端口进程
- 进程管理功能

**关键函数**：
- `is_port_in_use(port)`
- `find_process_using_port(port)`
- `kill_process(process)`
- `kill_all_processes_using_port(port)`
- `ensure_port_available(port)`

#### 3.6 配置管理

**功能特性**：
- JSON格式配置文件
- 配置热加载
- 配置持久化

**配置项**：
- 端口配置（主应用、管理应用）
- 扫描目录配置
- 支持的视频格式
- 默认标签
- 自动扫描设置

**关键函数**：
- `load_config()`
- `save_config(config)`

---

## 管理后台功能 (admin_app.py)

### 1. 管理页面

| 路由 | 方法 | 功能描述 |
|------|------|----------|
| `/` | GET | 管理后台首页 - 显示系统状态 |

### 2. 应用管理 API

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/status` | GET | 获取状态信息（主应用状态、系统统计、数据库统计） | 无 |
| `/api/app/start` | POST | 启动主应用 | 无 |
| `/api/app/stop` | POST | 停止主应用 | 无 |
| `/api/app/restart` | POST | 重启主应用 | 无 |

### 3. 数据库管理 API

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/db/stats` | GET | 获取数据库统计（视频数、标签数、浏览量等） | 无 |
| `/api/db/clear` | POST | 清理数据库（支持dry-run） | `dry_run` |

### 4. 视频管理 API

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/videos` | GET | 获取视频列表（分页） | `page`, `per_page`, `search` |
| `/api/video/add` | POST | 添加视频 | `url`, `title`, `description`, `tags` |
| `/api/video/<video_hash>` | DELETE | 删除视频 | 无 |
| `/api/video/<video_hash>` | GET | 获取视频详情 | 无 |
| `/api/video/<video_hash>/tags` | GET | 获取视频的标签 | 无 |
| `/api/video/<video_hash>/tags` | PUT | 更新视频的标签 | `tag_ids` |
| `/api/videos/clear` | POST | 清空所有视频 | 无 |

### 5. 标签管理 API

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/tags` | GET | 获取标签列表（含视频计数） | 无 |
| `/api/tags/add` | POST | 添加标签 | `name`, `category` |
| `/api/tags/<int:tag_id>` | DELETE | 删除标签 | 无 |

### 6. 日志管理 API

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/logs` | GET | 获取日志（支持类型筛选和行数限制） | `type`, `lines` |
| `/api/logs/list` | GET | 获取日志文件列表 | 无 |
| `/api/logs/download/<filename>` | GET | 下载日志文件 | 无 |
| `/api/logs/clear` | POST | 清空日志 | `types` |
| `/api/logs/size` | GET | 获取日志目录总大小 | 无 |

### 7. 缩略图管理 API

| API | 方法 | 功能描述 | 参数 |
|-----|------|----------|------|
| `/api/thumbnails/regenerate` | POST | 批量重新生成缩略图 | `limit` |

### 8. 代理 API（转发到主应用）

| API | 方法 | 功能描述 |
|-----|------|----------|
| `/api/config` | GET/PUT | 配置管理（通过主应用） |
| `/api/scan` | POST | 扫描配置目录（通过主应用） |
| `/api/dependencies/check` | GET | 检查依赖（通过主应用） |
| `/api/favorites` | GET | 获取收藏列表（通过主应用） |
| `/api/ranking` | GET | 获取排行榜（通过主应用） |

### 9. 核心管理功能

#### 9.1 应用管理

- 启动/停止/重启主应用
- 进程状态监控（CPU、内存）
- PID文件管理
- 主应用状态检查

**关键函数**：
- `start_main_app()`
- `stop_main_app()`
- `restart_main_app()`
- `get_main_app_status()`

#### 9.2 系统监控

- CPU使用率监控
- 内存使用情况监控
- 磁盘空间监控
- 进程资源监控

**关键函数**：
- `get_system_stats()`

#### 9.3 数据库管理

- 统计信息查询
- 数据清理（用户交互、标签、缩略图等）
- 批量操作支持

**关键函数**：
- `get_db_stats()`
- `clear_database_data(dry_run=False)`

#### 9.4 日志管理

- 日志文件浏览
- 日志下载
- 日志清理
- 大小监控

**关键函数**：
- `get_logs(log_type=None, lines=100)`
- `clear_logs(types=None)`

---

## 数据库模型 (models.py)

### 1. Video（视频模型）

**表名**: `videos`

**字段**：
- `id` - 主键
- `hash` - 视频唯一标识（MD5）
- `title` - 视频标题
- `description` - 视频描述
- `url` - 视频URL
- `thumbnail` - 缩略图路径
- `duration` - 视频时长（秒）
- `file_size` - 文件大小（字节）
- `view_count` - 浏览次数
- `like_count` - 点赞次数
- `download_count` - 下载次数
- `priority` - 优先级
- `is_downloaded` - 是否已下载
- `local_path` - 本地路径
- `created_at` - 创建时间
- `updated_at` - 更新时间

**关联关系**：
- 与 `Tag` 多对多关系（通过 `VideoTag`）
- 与 `UserInteraction` 一对多关系

### 2. Tag（标签模型）

**表名**: `tags`

**字段**：
- `id` - 主键
- `name` - 标签名（唯一）
- `category` - 标签分类
- `created_at` - 创建时间

**关联关系**：
- 与 `Video` 多对多关系（通过 `VideoTag`）

### 3. VideoTag（视频-标签关联表）

**表名**: `video_tags`

**字段**：
- `id` - 主键
- `video_id` - 视频ID（外键）
- `tag_id` - 标签ID（外键）
- `created_at` - 创建时间

**约束**：
- 唯一约束：`(video_id, tag_id)` 防止重复关联

### 4. UserInteraction（用户交互记录）

**表名**: `user_interactions`

**字段**：
- `id` - 主键
- `video_id` - 视频ID（外键）
- `user_session` - 用户会话ID
- `interaction_type` - 交互类型（view/like/download/share/favorite）
- `interaction_score` - 交互分数
- `created_at` - 创建时间

### 5. UserPreference（用户偏好模型）

**表名**: `user_preferences`

**字段**：
- `id` - 主键
- `user_session` - 用户会话ID
- `tag_id` - 标签ID（外键）
- `preference_score` - 偏好分数
- `interaction_count` - 交互次数
- `updated_at` - 更新时间

---

## 核心功能模块

### 1. 缩略图生成系统

**功能特性**：
- 懒加载机制：首次请求时触发异步生成
- 并发控制：限制同时生成2个缩略图
- 双格式支持：GIF动态图和JPG静态图
- 状态管理：pending/generating/ready/failed
- 自动时长检测：使用FFmpeg获取视频时长
- 智能采样：自动选择最佳帧

**关键函数**：
- `generate_thumbnail(video_path, output_path_gif, output_path_jpg)`
- `get_video_duration(video_path)`
- `extract_video_frames(video_path, output_dir, num_frames=10)`
- `generate_missing_thumbnails_async()`

### 2. 推荐系统

**功能特性**：
- 基于用户交互历史
- 标签偏好分析
- 个性化推荐
- 支持换一批功能

**关键函数**：
- `get_recommended_videos(exclude_hashes=None, limit=12)`

### 3. 视频处理

**功能特性**：
- 视频时长检测
- 缩略图生成
- 帧提取
- 视频信息获取

**关键函数**：
- `get_video_info(video_path)`
- `extract_video_frames(video_path, output_dir, num_frames=10)`

### 4. 日志系统

**功能特性**：
- 多类型日志
- 自动轮转
- 结构化解析
- 自定义级别

**日志类型**：
- maintenance.log - 维护日志
- runtime.log - 运行日志
- operation.log - 操作日志
- debug.log - 调试日志

**关键函数**：
- `get_log_content(log_type, lines=100)`
- `parse_log_line(line)`

### 5. 端口管理

**功能特性**：
- 端口占用检查
- 进程查找
- 进程终止
- 端口释放

**关键函数**：
- `is_port_in_use(port)`
- `find_process_using_port(port)`
- `kill_process(process)`
- `kill_all_processes_using_port(port)`
- `ensure_port_available(port)`

### 6. 配置管理

**功能特性**：
- JSON配置
- 热加载
- 持久化

**关键函数**：
- `load_config()`
- `save_config(config)`

---

## 辅助工具

### 1. 端口管理工具

**文件**：`port_manager.py`（已整合到主文件）

**功能**：
- 端口占用检查
- 进程查找和终止
- 端口释放

### 2. 启动脚本

**文件**：
- `clean_and_start.py` - 清理并重新启动所有服务
- `restart_services.py` - 重启服务脚本
- `verify_ports.py` - 端口验证工具

### 3. 数据库工具

**文件**：
- `check_db_tables.py` - 检查数据库表结构
- `test_db.py` - 数据库连接测试

### 4. 配置工具

**文件**：
- `check_config.py` - 配置检查工具
- `final_verification.py` - 最终验证工具

### 5. 诊断工具

**目录**：`diagnostics/`

**工具**：
- 缩略图诊断：`diagnose_thumbnail_issue.py`, `check_thumbnail_files.py`
- 路径检查：`check_paths.py`, `check_video.py`
- 日志收集：`collect_logs.py`
- 路由调试：`debug_route_404.py`
- 推荐算法调试：`debug_recommendation.py`

### 6. 维护脚本

**目录**：`scripts/`

**脚本**：
- 批量缩略图生成：`batch_generate_thumbnails.py`, `batch_generate_all.py`
- 维护脚本：`update_old_thumbnails.py`, `force_update_thumbnails.py`
- 服务器控制：`restart_flask.py`, `kill_flask.py`
- 数据迁移：`migrate_to_static_thumbnails.py`
- 目录重组：`reorganize_directory.py`
- 路径修复：`fix_paths_after_move.py`

---

## 技术架构

### 1. 双应用架构

- **主应用**：用户界面、视频播放、推荐系统
- **管理后台**：系统管理、数据库维护、日志监控

### 2. 数据库设计

- SQLite数据库
- SQLAlchemy ORM + 原生SQL混合使用
- 完整的关系映射

### 3. 异步处理

- 后台线程池处理缩略图生成
- 异步任务队列

### 4. 缓存机制

- 懒加载缩略图
- 缓存控制

### 5. 监控系统

- 系统资源监控
- 应用状态监控
- 日志监控

### 6. 推荐算法

- 基于用户行为的简单推荐系统
- 标签偏好分析
- 个性化推荐

### 7. 日志系统

- 多类型分级日志管理
- 自动轮转
- 结构化日志

---

## 主要功能分类

### 视频管理
- ✅ 视频扫描与导入
- ✅ 缩略图自动生成
- ✅ 标签管理
- ✅ 优先级设置
- ✅ 搜索功能
- ✅ 视频详情查看
- ✅ 视频删除

### 用户功能
- ✅ 视频播放记录
- ✅ 点赞/收藏功能
- ✅ 个人收藏管理
- ✅ 个性化推荐
- ✅ 排行榜

### 系统管理
- ✅ 应用启停控制
- ✅ 数据库维护
- ✅ 日志管理
- ✅ 配置管理
- ✅ 端口管理
- ✅ 系统监控

### 维护功能
- ✅ 批量缩略图生成
- ✅ 数据清理
- ✅ 诊断工具
- ✅ 测试工具
- ✅ 日志下载

---

## 总结

Dplayer 是一个功能相当完整的视频管理平台，具有：

- **完整的视频管理功能**：扫描、导入、缩略图、标签、搜索
- **丰富的用户交互**：播放记录、点赞、收藏、推荐
- **强大的后台管理**：应用控制、数据库管理、日志管理
- **完善的维护工具**：诊断工具、批量操作、测试工具
- **清晰的架构设计**：双应用架构、模块化设计

前后端分离的架构设计，支持本地视频管理和在线播放，包含完整的用户交互系统和后台管理功能。
