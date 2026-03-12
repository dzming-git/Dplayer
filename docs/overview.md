# DPlayer 视频播放器系统概览

## 系统简介

DPlayer 是一个基于 Flask 的本地视频播放和管理系统,支持视频扫描、播放、收藏、标签管理等功能。

## 核心功能

### 1. 视频管理
- 本地视频扫描和导入
- 视频播放和在线预览
- 视频信息管理(标题、描述、时长等)
- 缩略图自动生成(支持GIF和JPG两种格式)
- 优先级设置和管理

### 2. 标签系统
- 标签管理界面(增删改查)
- 标签分类(类型/作者/地区/年份/其他)
- 视频标签关联
- 热门标签统计

### 3. 用户交互
- 视频收藏功能
- 播放记录
- 点赞功能
- 下载计数
- 智能推荐系统(基于用户偏好)

### 4. 排行榜
- 播放排行(按播放量)
- 点赞排行(按点赞数)
- 下载排行(按下载量)
- 时长排行(按视频时长)

### 5. 搜索功能
- 视频标题搜索
- 标签搜索
- 实时搜索提示

### 6. 日志系统
- 分类日志(维护/运行/操作/调试)
- 日志轮转(自动备份)
- 日志在线查看
- 日志搜索和过滤
- 日志下载

## 技术架构

### 后端技术栈
- **框架**: Flask
- **数据库**: SQLite + SQLAlchemy ORM
- **视频处理**: OpenCV (cv2)
- **图像处理**: Pillow (PIL)
- **日志系统**: Python logging with RotatingFileHandler

### 前端技术栈
- **HTML5**: 语义化标签
- **CSS3**: 响应式设计
- **JavaScript**: 原生JS + Fetch API
- **DPlayer**: 视频播放器组件

### 项目结构

```
Dplayer/
├── app.py                 # Flask应用主文件
├── models.py              # 数据库模型定义
├── requirements.txt       # Python依赖
├── config.json           # 系统配置
├── dplayer.db            # SQLite数据库
├── static/               # 静态资源
│   ├── css/             # 样式文件
│   ├── uploads/         # 上传的视频
│   └── thumbnails/      # 视频缩略图
├── templates/            # HTML模板
│   ├── index.html       # 首页/收藏/排行榜
│   ├── video.html       # 视频播放页
│   ├── manage.html      # 视频管理页
│   ├── tags.html        # 标签管理页
│   └── logs.html        # 日志管理页
├── logs/                 # 日志目录
│   ├── runtime.log      # 运行日志
│   ├── maintenance.log  # 维护日志
│   ├── operation.log    # 操作日志
│   └── debug.log        # 调试日志
└── docs/                 # 文档目录
    ├── TAG_MANAGEMENT.md      # 标签管理文档
    ├── RANKING_FAVORITES_FIX.md  # 排行榜和收藏修复文档
    └── ID_ANALYSIS.md      # ID编号分析文档
```

## 数据库模型

### Video (视频表)
- `id`: 主键
- `hash`: 视频唯一标识(SHA256)
- `title`: 视频标题
- `description`: 视频描述
- `url`: 视频URL或本地路径
- `thumbnail`: 缩略图路径
- `duration`: 视频时长(秒)
- `view_count`: 播放量
- `like_count`: 点赞数
- `download_count`: 下载量
- `priority`: 优先级
- `is_downloaded`: 是否已下载
- `local_path`: 本地文件路径
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Tag (标签表)
- `id`: 主键
- `name`: 标签名称
- `category`: 标签分类
- `created_at`: 创建时间

### VideoTag (视频-标签关联表)
- `id`: 主键
- `video_id`: 视频ID
- `tag_id`: 标签ID

### UserInteraction (用户交互表)
- `id`: 主键
- `video_id`: 视频ID
- `user_session`: 用户会话ID
- `interaction_type`: 交互类型(view/like/download/favorite)
- `interaction_score`: 交互得分
- `created_at`: 创建时间

### UserPreference (用户偏好表)
- `id`: 主键
- `user_session`: 用户会话ID
- `tag_id`: 标签ID
- `preference_score`: 偏好得分
- `interaction_count`: 交互次数
- `created_at`: 创建时间
- `updated_at`: 更新时间

## API接口

### 视频相关
- `GET /api/videos` - 获取视频列表
- `GET /api/videos/recommend` - 获取推荐视频
- `GET /api/video/<hash>` - 获取视频详情
- `POST /api/video/<hash>/like` - 点赞视频
- `POST /api/video/<hash>/download` - 下载视频
- `POST /api/video/<hash>/favorite` - 收藏/取消收藏
- `GET /api/video/<hash>/is-favorite` - 检查是否收藏
- `DELETE /api/video/<hash>` - 删除视频
- `POST /api/video/<hash>/regenerate` - 重新生成缩略图
- `POST /api/video/<hash>/priority` - 更新优先级

### 标签相关
- `GET /api/tags` - 获取所有标签
- `POST /api/tags/add` - 添加标签
- `GET /api/tags/<id>` - 获取标签详情
- `PUT /api/tags/<id>` - 更新标签
- `DELETE /api/tags/<id>` - 删除标签
- `GET /api/tags/<id>/videos` - 获取标签关联的视频
- `GET /api/video/<hash>/tags` - 获取/更新视频标签

### 排行榜
- `GET /api/ranking?type={type}&limit={limit}` - 获取排行榜

### 收藏
- `GET /api/favorites` - 获取收藏列表

### 配置
- `GET /api/config` - 获取配置
- `PUT /api/config` - 更新配置

### 扫描
- `POST /api/scan` - 扫描本地视频
- `POST /api/thumbnails/regenerate` - 批量重新生成缩略图
- `GET /api/thumbnails/progress/<task_id>` - 获取缩略图生成进度

### 日志
- `GET /api/logs` - 获取日志文件列表
- `GET /api/logs/<filepath>` - 获取日志内容
- `GET /api/logs/download/<filepath>` - 下载日志文件
- `POST /api/logs/clear` - 清空所有日志
- `POST /api/logs/clear/<type>` - 清空指定类型日志
- `GET /api/logs/size` - 获取日志大小

## 配置说明

### config.json
```json
{
  "scan_directories": [
    {
      "path": "M:/bang",
      "recursive": true,
      "enabled": true
    }
  ],
  "auto_scan_on_startup": true,
  "scan_interval_minutes": 60,
  "supported_formats": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
  "default_tags": ["本地视频"],
  "default_priority": 0
}
```

## 部署说明

### 环境要求
- Python 3.7+
- 依赖包见 `requirements.txt`

### 安装步骤
1. 安装依赖: `pip install -r requirements.txt`
2. 修改配置: 编辑 `config.json`
3. 启动服务: `python app.py`
4. 访问系统: http://127.0.0.1

### 默认端口
- Web服务: 80
- 数据库: SQLite (本地文件)

## 已知问题

1. **视频ID和标签ID**: 当前使用自增ID,未来删除记录可能导致ID不连续,但不影响功能(使用hash作为对外标识)
2. **缩略图生成**: 大视频文件生成缩略图可能较慢,已优化为异步生成
3. **并发限制**: 缩略图生成限制为2个并发,避免资源占用过高

## 最近更新

### 2025-03-13
- ✅ 修复排行榜功能缺失问题
- ✅ 修复我的收藏加载失败问题
- ✅ 实现排行榜API(播放/点赞/下载/时长)
- ✅ 实现收藏列表API

### 标签管理功能
- ✅ 标签管理界面(增删改查)
- ✅ 标签分类功能
- ✅ 视频标签关联管理

## 开发者信息

- **项目名称**: DPlayer
- **开发语言**: Python (Flask)
- **数据库**: SQLite
- **许可证**: 未指定

## 相关文档

- [标签管理功能说明](./TAG_MANAGEMENT.md)
- [排行榜和收藏修复文档](./RANKING_FAVORITES_FIX.md)
- [ID编号分析文档](./ID_ANALYSIS.md)
