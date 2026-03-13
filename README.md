# DPlayer 视频站

一个类似 B 站的视频播放器系统，支持视频播放、推荐算法、搜索、标签等功能。

## 功能特性

### 1. B 站风格首页布局
- 网格化视频卡片展示
- 响应式设计，支持移动端
- 标签分类导航

### 2. 智能推荐算法
- 基于用户行为（观看、点赞、下载）的个性化推荐
- 支持按标签和优先级排序
- 随机推荐功能

### 3. 视频管理
- 通过 URL 添加视频
- 上传本地视频文件
- 视频缩略图预览
- 视频信息编辑（标题、描述、标签等）

### 4. 优先级设置
- 设置视频优先级（0-100）
- 优先级影响推荐排序

### 5. 视频标签
- 灵活的标签分类系统
- 标签关联管理
- 按标签筛选视频

### 6. 搜索功能
- 支持视频标题和描述搜索
- 支持标签搜索
- 实时搜索结果展示

### 7. 视频下载
- 一键下载视频
- 下载统计

### 8. 视频唯一标识
- 使用 SHA256 hash 作为视频唯一标识
- 避免重复添加相同视频

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

#### 方法一：直接运行（开发环境）

```bash
python app.py
```

#### 方法二：使用 Windows 原生服务（生产环境推荐）

**安装服务（需要管理员权限）：**

```batch
# 方法1：使用安装脚本（会自动请求管理员权限）
scripts\install_services.bat

# 方法2：手动以管理员身份运行
# 右键点击 install_services.bat，选择"以管理员身份运行"
```

**管理服务：**

```batch
# 启动所有服务
scripts\start_all_services.bat

# 停止所有服务
scripts\stop_all_services.bat

# 检查服务状态
scripts\check_services.bat

# 单独管理某个服务
scripts\service_control.bat start admin_service
scripts\service_control.bat stop admin_service
scripts\service_control.bat restart admin_service

# 卸载服务（需要管理员权限）
scripts\service_control.bat remove admin_service
```

**服务说明：**
- `DPlayer-Admin` - 管理后台（端口 8080）
- `DPlayer-Main` - 主应用（端口 5000）
- `DPlayer-Thumbnail` - 缩略图服务

**Linux/Mac 用户：**

```bash
# 使用进程管理器
python process_manager.py start all
python process_manager.py status
python process_manager.py stop all
```

#### 方法三：使用快捷脚本

```batch
# Windows - 启动所有服务
scripts\start_all_services.bat

# Windows - 停止所有服务
scripts\stop_all_services.bat
```

### 3. 访问页面

- 首页: `http://localhost/`
- 视频播放: `http://localhost/video/{video_hash}`
- 视频管理: `http://localhost/manage`
- 管理后台: `http://localhost:8080`（需要先启动 admin_app.py）
- 缩略图服务: `http://localhost:5001`（需要先启动 thumbnail_service.py）

## 项目结构

```
Dplayer/
├── app.py                 # Flask 主应用
├── admin_app.py            # 管理后台
├── process_manager.py      # 跨平台进程管理器
├── models.py              # 数据库模型
├── requirements.txt       # Python 依赖
├── templates/             # HTML 模板
│   ├── index.html        # 首页
│   ├── video.html        # 视频播放页面
│   └── manage.html       # 视频管理页面
├── static/                # 静态资源
│   ├── css/
│   │   ├── style.css     # 首页样式
│   │   ├── video.css     # 视频页面样式
│   │   └── manage.css    # 管理页面样式
│   ├── uploads/          # 上传的视频文件
│   └── thumbnails/       # 视频缩略图
├── scripts/               # 启动和管理脚本
│   ├── service_manager.ps1      # PowerShell 服务管理器（Windows 推荐）
│   ├── service_manager.bat      # 服务管理器启动器
│   ├── install_services.bat     # 一键安装脚本
│   ├── uninstall_services.bat   # 一键卸载脚本
│   ├── migrate_to_services.bat # 迁移工具
│   ├── start_all_services.bat   # 启动所有服务
│   ├── stop_all_services.bat    # 停止所有服务
│   └── ...                     # 其他辅助脚本
├── services/              # 微服务
│   └── thumbnail_service.py     # 缩略图生成服务
└── dplayer.db            # SQLite 数据库（自动生成）
```

## 服务管理

### Windows 用户（推荐）

使用 PowerShell 服务管理器，基于 Windows 原生服务 API：

- ✅ 原生 Windows 服务支持
- ✅ 自动启动配置
- ✅ 系统级监控和恢复
- ✅ 详细的进程状态监控
- ✅ 事件日志集成

**快速开始：**
```batch
# 安装服务（需要管理员权限）
scripts\install_services.bat

# 管理服务
scripts\service_manager.bat status
scripts\service_manager.bat start All
scripts\service_manager.bat stop All
scripts\service_manager.bat restart All
```

详细文档请查看：[docs/POWERSHELL_SERVICE_MANAGER.md](docs/POWERSHELL_SERVICE_MANAGER.md)

### Linux/Mac 用户

使用 Python 进程管理器：

```bash
# 启动所有服务
python process_manager.py start all

# 查看状态
python process_manager.py status

# 停止所有服务
python process_manager.py stop all

# 重启服务
python process_manager.py restart all

# 注册为系统服务（systemd）
python process_manager.py enable all
```

## API 接口

### 获取视频列表
```
GET /api/videos?limit=20&offset=0&tag_id=1
```

### 获取视频详情
```
GET /api/video/{video_hash}
```

### 点赞视频
```
POST /api/video/{video_hash}/like
```

### 下载视频
```
POST /api/video/{video_hash}/download
```

### 更新优先级
```
POST /api/video/{video_hash}/priority
Body: { "priority": 50 }
```

### 搜索视频
```
GET /search?q=关键词
```

### 上传视频
```
POST /api/video/upload
Content-Type: multipart/form-data
```

### 通过 URL 添加视频
```
POST /api/video/add
Content-Type: application/json
Body: {
  "title": "视频标题",
  "url": "视频URL",
  "description": "描述",
  "tags": "标签1,标签2",
  "priority": 10
}
```

### 删除视频
```
DELETE /api/video/{video_hash}
```

## 数据库模型

### Video（视频）
- hash: 视频唯一标识（SHA256）
- title: 标题
- description: 描述
- url: 视频URL
- thumbnail: 缩略图URL
- duration: 时长
- view_count: 播放次数
- like_count: 点赞数
- download_count: 下载次数
- priority: 优先级
- is_downloaded: 是否已下载
- local_path: 本地路径

### Tag（标签）
- name: 标签名称
- category: 分类

### UserInteraction（用户交互）
- video_id: 视频ID
- user_session: 用户会话
- interaction_type: 交互类型（view/like/download）
- interaction_score: 交互评分

### UserPreference（用户偏好）
- user_session: 用户会话
- tag_id: 标签ID
- preference_score: 偏好评分
- interaction_count: 交互次数

## 技术栈

- **后端**: Flask, Flask-SQLAlchemy, SQLAlchemy
- **前端**: HTML, CSS, JavaScript, DPlayer
- **数据库**: SQLite
- **视频播放**: DPlayer

## 注意事项

- 首次运行会自动创建数据库并插入示例视频
- 上传视频文件大小限制为 500MB
- 支持的视频格式: MP4, WebM, MOV, AVI
- 支持的图片格式: PNG, JPG, JPEG, GIF

## 开发计划

- [ ] 用户登录系统
- [ ] 视频收藏功能
- [ ] 弹幕系统
- [ ] 视频评论功能
- [ ] 视频排行版
- [ ] 播放历史记录
- [ ] 视频分享功能
