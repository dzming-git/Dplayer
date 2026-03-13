# DPlayer 管理后台功能对比文档

## 一、已实现功能（admin_app.py）

### 1. 系统管理
- ✅ `/api/status` - 获取系统状态（主应用状态、系统资源、数据库统计）
- ✅ `/api/app/start` - 启动主应用
- ✅ `/api/app/stop` - 停止主应用
- ✅ `/api/app/restart` - 重启主应用
- ✅ `/api/db/stats` - 获取数据库统计
- ✅ `/api/db/clear` - 清理数据库（支持按类型清理）

### 2. 视频管理
- ✅ `/api/videos` - 获取视频列表（分页）
- ✅ `/api/video/add` - 添加视频
- ✅ `/api/video/<video_hash>` - 删除视频
- ✅ `/api/videos/clear` - 清空所有视频

### 3. 标签管理
- ✅ `/api/tags` - 获取标签列表
- ✅ `/api/tags/add` - 添加标签
- ✅ `/api/tags/<int:tag_id>` - 删除标签

### 4. 日志管理
- ✅ `/api/logs` - 获取日志内容

## 二、主应用已实现功能（app.py）

### 1. 视频管理
- ✅ `/api/videos` - 获取视频列表（支持分页、标签筛选）
- ✅ `/api/videos/recommend` - 获取推荐视频列表
- ✅ `/api/video/<video_hash>` - 获取单个视频详情
- ✅ `/api/video/<video_hash>` - 删除视频
- ✅ `/api/video/<video_hash>/like` - 点赞视频
- ✅ `/api/video/<video_hash>/download` - 下载视频
- ✅ `/api/video/<video_hash>/priority` - 更新视频优先级
- ✅ `/api/video/<video_hash>/regenerate` - 重新生成缩略图和更新时长
- ✅ `/api/video/<video_hash>/tags` - 获取/更新视频标签
- ✅ `/api/video/<video_hash>/favorite` - 切换收藏状态
- ✅ `/api/video/<video_hash>/is-favorite` - 检查是否已收藏
- ✅ `/api/video/upload` - 上传视频文件
- ✅ `/api/video/add` - 通过URL添加视频
- ✅ `/api/videos/clear` - 清空所有视频

### 2. 标签管理
- ✅ `/api/tags` - 获取所有标签
- ✅ `/api/tags/add` - 添加新标签
- ✅ `/api/tags/<int:tag_id>` - 获取单个标签详情
- ✅ `/api/tags/<int:tag_id>` - 更新标签信息
- ✅ `/api/tags/<int:tag_id>` - 删除标签
- ✅ `/api/tags/<int:tag_id>/videos` - 获取标签关联的视频

### 3. 缩略图管理
- ✅ `/api/thumbnail/<video_hash>/status` - 检查缩略图生成状态
- ✅ `/api/thumbnails/regenerate` - 批量重新生成缩略图
- ✅ `/api/thumbnails/progress/<task_id>` - 获取缩略图生成进度

### 4. 日志管理
- ✅ `/api/logs` - 获取日志文件列表
- ✅ `/api/logs/<path:filepath>` - 获取日志文件内容（支持搜索、级别过滤）
- ✅ `/api/logs/download/<path:filepath>` - 下载日志文件
- ✅ `/api/logs/clear` - 清空所有日志文件
- ✅ `/api/logs/clear/<log_type>` - 清空指定类型的日志
- ✅ `/api/logs/size` - 获取日志目录总大小

### 5. 系统配置
- ✅ `/api/config` - 获取系统配置
- ✅ `/api/config` - 更新系统配置
- ✅ `/api/scan` - 扫描配置目录并添加视频
- ✅ `/api/check-file` - 检查文件是否存在
- ✅ `/api/dependencies/check` - 检查依赖安装状态
- ✅ `/api/status` - 获取应用状态
- ✅ `/api/favorites` - 获取收藏列表
- ✅ `/api/ranking` - 获取排行榜数据

## 三、需要移植到管理后台的功能

### 高优先级（核心管理功能）
1. **视频详情查看** - `/api/video/<video_hash>` (GET)
2. **视频标签管理** - `/api/video/<video_hash>/tags` (GET/PUT)
3. **视频收藏管理** - `/api/video/<video_hash>/favorite` (POST/GET)
4. **视频点赞管理** - `/api/video/<video_hash>/like` (POST)
5. **缩略图管理** - `/api/thumbnails/regenerate` (POST)
6. **日志文件列表** - `/api/logs` (GET - 返回文件列表而非内容)
7. **日志文件下载** - `/api/logs/download/<path:filepath>` (GET)
8. **日志文件内容** - `/api/logs/<path:filepath>` (GET)
9. **日志清空** - `/api/logs/clear` 和 `/api/logs/clear/<log_type>` (POST)
10. **日志大小查询** - `/api/logs/size` (GET)

### 中优先级（增强功能）
1. **系统配置管理** - `/api/config` (GET/PUT)
2. **目录扫描** - `/api/scan` (POST)
3. **依赖检查** - `/api/dependencies/check` (GET)
4. **视频上传** - `/api/video/upload` (POST)
5. **推荐视频** - `/api/videos/recommend` (GET)
6. **收藏列表** - `/api/favorites` (GET)
7. **排行榜** - `/api/ranking` (GET)

### 低优先级（用户交互功能）
1. **视频下载** - `/api/video/<video_hash>/download` (GET/POST)
2. **视频优先级更新** - `/api/video/<video_hash>/priority` (POST)
3. **单个缩略图重新生成** - `/api/video/<video_hash>/regenerate` (POST)
4. **标签更新** - `/api/tags/<int:tag_id>` (PUT)
5. **标签详情** - `/api/tags/<int:tag_id>` (GET)
6. **标签关联视频** - `/api/tags/<int:tag_id>/videos` (GET)
7. **文件检查** - `/api/check-file` (POST)

## 四、实施计划

### 阶段1：核心管理功能（当前阶段）
- 添加视频详情查看API
- 添加视频标签管理API
- 添加缩略图批量生成API
- 完善日志管理API（文件列表、下载、清空）

### 阶段2：系统配置
- 添加系统配置API
- 添加目录扫描API
- 添加依赖检查API

### 阶段3：用户体验增强
- 添加收藏管理API
- 添加排行榜API
- 添加视频上传API

## 五、实现原则

1. **复用现有逻辑** - 尽量复用app.py中的业务逻辑，避免重复代码
2. **使用原生SQL** - 管理后台继续使用原生SQL查询，避免SQLAlchemy冲突
3. **统一接口规范** - 确保所有API返回格式一致
4. **错误处理** - 所有API都应有完善的错误处理和日志记录
5. **测试覆盖** - 每个新增API都应编写测试用例
