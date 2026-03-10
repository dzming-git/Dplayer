# DPlayer 视频站快速入门

## 一、环境要求

- Python 3.7+
- pip 包管理器
- 磁盘空间：至少 1GB（用于视频和预览图）

## 二、安装步骤

### 1. 安装依赖

#### Windows 用户
```bash
# 双击运行安装脚本
install_dependencies.bat

# 或使用命令行
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Linux/Mac 用户
```bash
# 运行安装脚本
chmod +x install_dependencies.sh
./install_dependencies.sh

# 或使用命令行
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置扫描目录

编辑 `config.json`，修改 `scan_directories` 中的路径：

```json
{
  "scan_directories": [
    {
      "path": "M:/bang",
      "recursive": true,
      "enabled": true
    }
  ]
}
```

### 3. 启动服务器

#### Windows
```bash
# 双击运行
start_server.bat

# 或使用命令行
python app.py
```

#### Linux/Mac
```bash
python3 app.py
```

服务器将在 `http://localhost:80` 启动

## 三、添加视频

### 方法1：扫描本地视频（推荐）

1. 访问 `http://localhost:80/manage`
2. 点击"扫描本地视频"按钮
3. 系统会自动：
   - 扫描配置的目录
   - 生成 GIF 预览图
   - 获取视频时长
   - 添加到数据库

### 方法2：上传视频

1. 访问 `http://localhost:80/manage`
2. 切换到"上传本地文件"标签
3. 填写视频信息并上传

### 方法3：添加 URL 视频

1. 访问 `http://localhost:80/manage`
2. 填写视频 URL 和信息
3. 点击"添加视频"

## 四、预览图生成

### 自动生成

扫描或上传视频时，系统会自动生成：
- **GIF 动图**：6 帧循环播放，展示视频内容
- **视频时长**：精确到秒

### 手动重新生成

1. **单个视频**：在管理页面点击视频的"播放"按钮旁边的选项
2. **批量生成**：点击管理页面的"重新生成缩略图"按钮

## 五、常见问题

### 1. 依赖安装失败

**问题**：OpenCV 安装失败

**解决方案**：
```bash
# 使用国内镜像
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用预编译版本
pip install opencv-python-headless
```

### 2. 视频无法播放

**检查项**：
- 视频文件是否存在
- 文件格式是否支持（mp4, avi, mkv, mov, wmv, flv, webm, m4v）
- 浏览器是否支持该格式

### 3. 预览图未生成

**检查项**：
- OpenCV 是否正确安装
- 视频文件是否完整
- `static/thumbnails/` 目录权限

### 4. 端口被占用

**问题**：80 端口已被其他程序占用

**解决方案**：

修改 `app.py` 最后一行：
```python
app.run(host='0.0.0.0', port=8080, debug=True)  # 改为 8080
```

## 六、功能特性

✅ **智能推荐**：基于用户行为和标签的推荐算法
✅ **GIF 预览**：多帧循环播放，动态展示视频内容
✅ **标签系统**：支持多标签分类和搜索
✅ **优先级排序**：自定义视频优先级
✅ **本地扫描**：自动扫描本地视频目录
✅ **下载管理**：支持视频下载到本地
✅ **数据统计**：播放量、点赞数、下载数统计

## 七、目录结构

```
Dplayer/
├── app.py                 # 主程序
├── models.py              # 数据库模型
├── config.json            # 配置文件
├── requirements.txt       # 依赖列表
├── instance/
│   └── dplayer.db        # SQLite 数据库
├── static/
│   ├── css/              # 样式文件
│   ├── thumbnails/       # 视频预览图
│   └── uploads/          # 上传的视频
└── templates/
    ├── index.html        # 首页
    ├── video.html        # 播放页
    └── manage.html       # 管理页
```

## 八、API 接口

### 视频管理
- `POST /api/scan` - 扫描本地视频
- `GET /api/videos` - 获取视频列表
- `POST /api/video/add` - 添加视频
- `DELETE /api/video/{hash}` - 删除视频
- `POST /api/video/{hash}/like` - 点赞视频
- `POST /api/video/{hash}/download` - 下载视频

### 预览图管理
- `POST /api/video/{hash}/regenerate` - 重新生成单个视频预览图
- `POST /api/thumbnails/regenerate` - 批量重新生成预览图

### 数据管理
- `POST /api/videos/clear` - 清空所有视频数据
- `GET /api/config` - 获取配置
- `PUT /api/config` - 更新配置

## 九、性能优化

1. **首次生成**：建议在低峰期批量生成预览图
2. **批量处理**：使用批量接口一次性处理多个视频
3. **缓存策略**：预览图采用静态缓存，避免重复生成
4. **数据库优化**：定期清理无效的关联记录

## 十、技术支持

- 详细文档：查看 `THUMBNAIL_GUIDE.md`
- 问题反馈：检查 Python 控制台错误日志
- 依赖问题：参考 `requirements.txt`

## 十一、下一步

1. 修改 `config.json` 配置你的视频目录
2. 运行 `install_dependencies.bat` 安装依赖
3. 启动服务器并访问 `http://localhost:80`
4. 扫描本地视频开始使用

---

**提示**：首次扫描大量视频时，预览图生成可能需要较长时间，请耐心等待。
