# 视频预览图和时长生成说明

## 功能概述

本系统支持自动为本地视频生成**多帧GIF动图预览**和获取时长信息，采用**静态缓存**策略，提升性能并避免重复计算。

## 技术方案

### 1. 静态缓存策略
- **首次生成**：视频添加到数据库时自动生成GIF预览图和获取时长
- **缓存存储**：
  - GIF 动图：`static/thumbnails/{video_hash}.gif`
  - 静态缩略图：`static/thumbnails/{video_hash}.jpg`（GIF生成失败时）
- **复用机制**：已存在的预览图不会被重复生成
- **性能优化**：避免每次访问时的重复计算

### 2. 多帧GIF预览

#### 生成特点
- **帧数**：默认6帧，均匀分布在视频中
- **尺寸**：320x180 像素（16:9 比例）
- **格式**：GIF 动图，循环播放
- **每帧时长**：500毫秒（可调整）
- **循环**：无限循环（loop=0）

#### 帧分布算法
```python
# 将视频分为6个等分段，从每段截取一帧
frame_interval = total_frames / 6
frame_positions = [0, frame_interval, 2*frame_interval, ...]
```

### 3. 生成时机

#### 自动生成
- 扫描本地视频时（`/api/scan`）
- 上传视频时（`/api/video/upload`）

#### 手动生成
- 单个视频重新生成（`/api/video/{hash}/regenerate`）
- 批量重新生成（`/api/thumbnails/regenerate`）

### 4. 生成参数

#### GIF预览图生成
- **截取帧数**：6帧（均匀分布）
- **图片尺寸**：320x180 像素
- **每帧时长**：500ms
- **格式**：GIF（循环播放）
- **文件名**：`{video_hash}.gif`

#### 静态缩略图（备用）
- **截取时间点**：视频第5秒
- **图片尺寸**：320x180 像素
- **格式**：JPG
- **文件名**：`{video_hash}.jpg`

#### 时长获取
- **单位**：秒
- **精度**：整数秒
- **方法**：通过 OpenCV 读取视频帧数和帧率计算

## 依赖库

```txt
opencv-python>=4.0.0
Pillow>=10.0.0
imageio>=2.31.0
imageio-ffmpeg>=0.4.9
```

## 使用方法

### 1. 安装依赖

#### Windows
```bash
# 双击运行安装脚本
install_dependencies.bat

# 或手动安装
pip install -r requirements.txt
```

#### Linux/Mac
```bash
# 给脚本执行权限
chmod +x install_dependencies.sh

# 运行安装脚本
./install_dependencies.sh

# 或手动安装
pip install -r requirements.txt
```

#### 使用国内镜像源（推荐）
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 添加视频时自动生成

扫描本地视频或上传视频时，系统会自动：
- 获取视频时长
- 生成GIF动图预览（优先）
- 如果GIF生成失败，则生成静态缩略图
- 保存到数据库和文件系统

### 3. 手动重新生成

#### 单个视频
```bash
POST /api/video/{video_hash}/regenerate
```

#### 批量生成
通过管理页面点击"重新生成缩略图"按钮，或调用：
```bash
POST /api/thumbnails/regenerate
```

### 4. 清理缓存

删除 `static/thumbnails/` 目录下的图片和GIF文件即可。

## 缓存验证

系统通过 `video_hash` 判断缓存是否已存在：
- GIF文件：`{video_hash}.gif`
- JPG文件：`{video_hash}.jpg`
- 数据库字段：`video.thumbnail`
- 缓存命中：直接使用已存在的预览图
- 缓存未命中：生成新的预览图

## 预览图显示

### HTML中使用
```html
<!-- GIF动图预览 -->
<img src="{{ video.thumbnail }}" alt="{{ video.title }}" class="video-thumbnail">

<!-- 鼠标悬停播放，默认显示第一帧 -->
<img src="{{ video.thumbnail }}" alt="{{ video.title }}"
     class="video-thumbnail"
     style="transition: transform 0.3s;">
```

### CSS样式建议
```css
.video-thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 4px;
}

.video-thumbnail:hover {
    transform: scale(1.05);
    cursor: pointer;
}
```

## 性能优化建议

1. **首次生成**：建议在低峰期批量生成
2. **批量处理**：使用 `/api/thumbnails/regenerate` 批量更新
3. **异步任务**：大量视频可考虑使用后台任务队列（Celery）
4. **缓存有效期**：视频文件不变更时无需重新生成
5. **GIF优化**：已启用Pillow的optimize参数

## 文件大小估算

| 格式 | 单个文件大小 | 说明 |
|------|------------|------|
| GIF (6帧) | 50-200KB | 取决于视频内容复杂度 |
| JPG (1帧) | 10-30KB | 静态缩略图 |
| 100个视频 | 5-20MB | 全部使用GIF |

## 故障排查

### GIF未生成
1. 检查 `static/thumbnails/` 目录权限
2. 确认视频文件格式支持（mp4, avi, mkv, mov, wmv, flv, webm, m4v）
3. 检查 OpenCV 是否正确安装：`python -c "import cv2; print(cv2.__version__)"`
4. 查看 Python 控制台错误日志

### 时长显示错误
1. 确认视频文件完整
2. 检查视频编码格式
3. 尝试重新生成缩略图

### 内存占用高
1. 批量生成时分批处理（每次处理10-20个视频）
2. 降低 GIF 帧数（修改 `num_frames` 参数）
3. 增加系统内存

### OpenCV安装失败
```bash
# 方案1：使用预编译版本
pip install opencv-python

# 方案2：使用无界面版本（Linux服务器）
pip install opencv-python-headless

# 方案3：使用国内镜像
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 自定义配置

如需修改生成参数，编辑 `app.py` 中的函数调用：

```python
# 修改 GIF 帧数（默认6帧）
generate_video_gif(video_path, output_path, num_frames=10)

# 修改每帧时长（默认500ms）
generate_video_gif(video_path, output_path, duration=300)

# 修改图片尺寸（默认320x180）
generate_video_gif(video_path, output_path, size=(640, 360))
```

## 注意事项

1. GIF 文件比 JPG 大约 3-5 倍，但提供更好的预览效果
2. 生成速度取决于视频大小和系统性能（通常每个视频 2-10秒）
3. 建议定期清理无效的预览图文件
4. 视频文件路径变更时需要重新生成
5. 首次批量生成建议分批进行，避免系统负载过高

## 技术优势

✅ **动态预览**：多帧GIF循环播放，展示视频内容
✅ **均匀采样**：从视频不同位置截取帧，全面展示
✅ **缓存优化**：避免重复生成，提升性能
✅ **降级方案**：GIF失败时自动使用静态缩略图
✅ **易于管理**：支持单个和批量重新生成

