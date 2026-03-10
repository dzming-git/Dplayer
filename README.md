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

```bash
python app.py
```

默认运行在 `http://localhost`

### 3. 访问页面

- 首页: `http://localhost/`
- 视频播放: `http://localhost/video/{video_hash}`
- 视频管理: `http://localhost/manage`

## 项目结构

```
Dplayer/
├── app.py                 # Flask 主应用
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
└── dplayer.db            # SQLite 数据库（自动生成）
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
