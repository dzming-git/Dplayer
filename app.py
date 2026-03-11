from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, abort
from werkzeug.utils import secure_filename
from models import db, Video, Tag, VideoTag, UserInteraction, UserPreference
from datetime import datetime
import random
import os
import hashlib
import json
import glob
from urllib.parse import quote
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dplayer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB 最大上传

# 配置文件路径
CONFIG_FILE = 'config.json'

# 全局进度字典
progress_store = {}

# 初始化数据库
db.init_app(app)

# 注册模板过滤器
@app.template_filter('format_number')
def format_number(num):
    """格式化数字显示"""
    if num >= 10000:
        return f"{num / 10000:.1f}万"
    return str(num)

@app.template_filter('format_duration')
def format_duration(seconds):
    """格式化视频时长显示"""
    if not seconds or seconds <= 0:
        return "00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

# 添加本地视频文件路由
@app.route('/local_video/<path:video_path>')
def serve_local_video(video_path):
    """提供本地视频文件"""
    # 解码路径
    try:
        video_path = video_path.encode('utf-8').decode('utf-8')
        # 规范化路径
        video_path = os.path.normpath(video_path).replace('\\', '/')

        # 检查路径是否允许访问
        scan_dirs = config.get('scan_directories', [])
        allowed = False
        for dir_config in scan_dirs:
            scan_path = dir_config.get('path', '').replace('\\', '/').replace('//', '/')
            if video_path.startswith(scan_path.replace('\\', '/')):
                allowed = True
                break

        if not allowed:
            abort(403, "路径不允许访问")

        # 检查文件是否存在
        if not os.path.exists(video_path):
            abort(404, "文件不存在")

        # 检查是否是文件
        if not os.path.isfile(video_path):
            abort(400, "不是有效的文件")

        # 发送文件
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=False
        )
    except Exception as e:
        print(f'视频服务错误: {e}')
        abort(500, str(e))

# 懒加载缩略图路由
@app.route('/thumbnail/<video_hash>')
def serve_lazy_thumbnail(video_hash):
    """懒加载缩略图：如果不存在则生成"""
    try:
        # 查询视频
        video = Video.query.filter_by(hash=video_hash).first_or_404()

        # 缩略图文件路径（使用视频hash作为文件名）
        thumbnail_dir = os.path.join('static', 'thumbnails')
        gif_path = os.path.join(thumbnail_dir, f'{video_hash}.gif')
        jpg_path = os.path.join(thumbnail_dir, f'{video_hash}.jpg')

        # 检查是否已存在缩略图
        if os.path.exists(gif_path):
            return send_file(gif_path, mimetype='image/gif')
        elif os.path.exists(jpg_path):
            return send_file(jpg_path, mimetype='image/jpeg')

        # 不存在则生成
        if video.local_path and os.path.exists(video.local_path):
            # 确保目录存在
            os.makedirs(thumbnail_dir, exist_ok=True)

            # 尝试生成GIF预览图
            gif_success = generate_video_gif(video.local_path, gif_path, num_frames=6, duration=500)

            if gif_success:
                return send_file(gif_path, mimetype='image/gif')

            # 如果GIF生成失败，生成静态缩略图
            jpg_success = generate_video_thumbnail(video.local_path, jpg_path)

            if jpg_success:
                return send_file(jpg_path, mimetype='image/jpeg')

        # 如果生成失败，返回默认缩略图
        default_thumbnail = os.path.join('static', 'thumbnails', 'default.png')
        if os.path.exists(default_thumbnail):
            return send_file(default_thumbnail, mimetype='image/png')

        # 如果连默认缩略图都没有，返回404
        abort(404, "缩略图不可用")

    except Exception as e:
        print(f'缩略图服务错误: {e}')
        abort(500, str(e))

# 视频上传目录
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 缩略图上传目录
THUMBNAIL_FOLDER = 'static/thumbnails'
if not os.path.exists(THUMBNAIL_FOLDER):
    os.makedirs(THUMBNAIL_FOLDER)
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER

# 允许的文件扩展名
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 配置加载和保存函数
def load_config():
    """加载配置文件"""
    default_config = {
        "scan_directories": [
            {
                "path": "M:/bang",
                "recursive": True,
                "enabled": True
            }
        ],
        "auto_scan_on_startup": True,
        "scan_interval_minutes": 60,
        "supported_formats": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
        "default_tags": ["本地视频"],
        "default_priority": 0
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except Exception as e:
            print(f'加载配置文件失败: {e}，使用默认配置')
    return default_config


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f'保存配置文件失败: {e}')
        return False


# 加载配置
config = load_config()


def scan_directory(directory_path, recursive=True, supported_formats=None):
    """
    扫描目录查找视频文件

    Args:
        directory_path: 目录路径
        recursive: 是否递归扫描子目录
        supported_formats: 支持的视频格式列表

    Returns:
        视频文件路径列表
    """
    if supported_formats is None:
        supported_formats = config.get('supported_formats', ['.mp4', '.avi', '.mkv'])

    video_files = []

    # 检查目录是否存在
    if not os.path.exists(directory_path):
        print(f'目录不存在: {directory_path}')
        return video_files

    if not os.path.isdir(directory_path):
        print(f'路径不是目录: {directory_path}')
        return video_files

    # 扫描目录
    if recursive:
        # 递归扫描
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in supported_formats):
                    video_files.append(os.path.join(root, file))
    else:
        # 只扫描当前目录
        for file in os.listdir(directory_path):
            file_lower = file.lower()
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and any(file_lower.endswith(ext) for ext in supported_formats):
                video_files.append(file_path)

    return video_files


def get_video_duration(video_path):
    """
    获取视频时长（秒）

    Args:
        video_path: 视频文件路径

    Returns:
        视频时长（秒），失败返回None
    """
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            if fps > 0:
                return int(frame_count / fps)
    except Exception as e:
        print(f'获取视频时长失败 {video_path}: {str(e)}')
    return None


def generate_video_frames(video_path, num_frames=6, size=(320, 180)):
    """
    从视频中平均截取多个关键帧

    Args:
        video_path: 视频文件路径
        num_frames: 截取帧数，默认6帧
        size: 图片尺寸，默认320x180

    Returns:
        帧列表，失败返回None
    """
    try:
        import cv2
        import numpy as np

        print(f'[DEBUG] 开始处理视频: {video_path}')
        print(f'[DEBUG] 文件是否存在: {os.path.exists(video_path)}')

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f'[ERROR] 无法打开视频文件: {video_path}')
            return None

        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        print(f'[DEBUG] 总帧数: {total_frames}, FPS: {fps}')

        if total_frames == 0:
            print(f'[ERROR] 视频帧数为0: {video_path}')
            cap.release()
            return None

        # 计算要截取的帧位置（均匀分布）
        frame_interval = max(1, total_frames // num_frames)
        frame_positions = [min(i * frame_interval, total_frames - 1) for i in range(num_frames)]

        print(f'[DEBUG] 帧间隔: {frame_interval}, 帧位置: {frame_positions}')

        frames = []
        for i, frame_pos in enumerate(frame_positions):
            # 跳转到指定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

            # 读取帧
            ret, frame = cap.read()
            if ret:
                # 调整大小
                frame = cv2.resize(frame, size)
                frames.append(frame)
                print(f'[DEBUG] 成功读取第 {i+1} 帧 (位置: {frame_pos})')
            else:
                print(f'[WARNING] 读取第 {i+1} 帧失败 (位置: {frame_pos})')

        cap.release()
        print(f'[DEBUG] 成功提取 {len(frames)} 帧')
        return frames if frames else None
    except ImportError as e:
        print(f'[ERROR] OpenCV 未安装: {str(e)}')
        print('[HINT] 请运行: pip install opencv-python')
        return None
    except Exception as e:
        print(f'[ERROR] 生成视频帧失败 {video_path}: {str(e)}')
        import traceback
        traceback.print_exc()
        return None


def generate_video_gif(video_path, output_path, num_frames=6, size=(320, 180), duration=500):
    """
    生成视频预览GIF动图

    Args:
        video_path: 视频文件路径
        output_path: 输出GIF路径
        num_frames: 截取帧数，默认6帧
        size: 图片尺寸，默认320x180
        duration: 每帧持续时间（毫秒），默认500ms

    Returns:
        是否成功
    """
    try:
        from PIL import Image

        print(f'[DEBUG] 开始生成GIF: {output_path}')

        # 生成帧
        frames = generate_video_frames(video_path, num_frames, size)
        if not frames or len(frames) == 0:
            print(f'[ERROR] 无法提取视频帧')
            return False

        # 将OpenCV BGR格式转换为PIL RGB格式
        pil_frames = []
        import cv2
        for i, frame in enumerate(frames):
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            pil_frames.append(pil_image)
            print(f'[DEBUG] 转换第 {i+1} 帧为RGB格式')

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 保存为GIF
        print(f'[DEBUG] 保存GIF到: {output_path}')
        pil_frames[0].save(
            output_path,
            format='GIF',
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        print(f'[DEBUG] GIF生成成功: {output_path}')
        return True
    except ImportError as e:
        print(f'[ERROR] Pillow 未安装: {str(e)}')
        print('[HINT] 请运行: pip install Pillow')
        return False
    except Exception as e:
        print(f'[ERROR] 生成GIF失败 {video_path}: {str(e)}')
        import traceback
        traceback.print_exc()
        return False


def generate_video_thumbnail(video_path, output_path, time_offset=5, size=(320, 180)):
    """
    生成视频缩略图（单帧静态图）

    Args:
        video_path: 视频文件路径
        output_path: 输出图片路径
        time_offset: 截取时间点（秒），默认5秒
        size: 图片尺寸，默认320x180

    Returns:
        是否成功
    """
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False

        # 获取视频总时长
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 计算截取的帧数
        if fps > 0:
            frame_num = min(int(time_offset * fps), total_frames - 1)
        else:
            frame_num = min(10, total_frames - 1)

        # 跳转到指定帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

        # 读取帧
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return False

        # 调整大小
        frame = cv2.resize(frame, size)

        # 保存图片
        cv2.imwrite(output_path, frame)
        return True
    except Exception as e:
        print(f'生成缩略图失败 {video_path}: {str(e)}')
        return False


def add_local_videos(video_files, default_tags=None, default_priority=0):
    """
    将本地视频文件添加到数据库

    Args:
        video_files: 视频文件路径列表
        default_tags: 默认标签列表
        default_priority: 默认优先级

    Returns:
        添加的视频数量
    """
    if default_tags is None:
        default_tags = config.get('default_tags', ['本地视频'])

    added_count = 0

    try:
        for video_file in video_files:
            try:
                # 获取文件名作为标题（不带扩展名）
                file_name = os.path.basename(video_file)
                title = os.path.splitext(file_name)[0]

                # 生成视频hash（使用文件路径）
                video_hash = Video.generate_hash(video_file)

                # 检查是否已存在
                existing_video = Video.query.filter_by(hash=video_hash).first()
                if existing_video:
                    # 更新本地路径
                    if not existing_video.is_downloaded:
                        existing_video.is_downloaded = True
                        existing_video.local_path = video_file
                        existing_video.url = f'/local_video/{video_file.replace(chr(92), "/")}'  # 更新为本地服务URL
                        db.session.commit()
                    continue

                # 生成本地视频的URL（用于播放）
                # 将反斜杠转换为正斜杠，并URL编码
                normalized_path = video_file.replace(chr(92), "/")
                video_url = f'/local_video/{normalized_path}'

                # 获取视频时长
                video_duration = get_video_duration(video_file)

                # 懒加载缩略图：使用视频hash作为缩略图路径，但不立即生成
                # 缩略图会在首次访问时按需生成
                thumbnail_path = f'/thumbnail/{video_hash}'

                # 创建视频记录
                video = Video(
                    hash=video_hash,
                    title=title,
                    description=f'本地视频: {file_name}',
                    url=video_url,  # 使用本地服务URL
                    thumbnail=thumbnail_path,  # 使用懒加载路径
                    duration=video_duration,
                    priority=default_priority,
                    is_downloaded=True,
                    local_path=video_file
                )

                db.session.add(video)
                db.session.flush()  # 获取video.id

                # 添加标签
                for tag_name in default_tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        category = '类型'
                        tag = Tag(name=tag_name, category=category)
                        db.session.add(tag)
                        db.session.flush()

                    # 创建视频-标签关联
                    video_tag = VideoTag(video_id=video.id, tag_id=tag.id)
                    db.session.add(video_tag)

                added_count += 1
            except Exception as e:
                print(f'添加视频 {video_file} 时出错: {str(e)}')
                continue

        db.session.commit()
    except Exception as e:
        print(f'批量添加视频时出错: {str(e)}')
        db.session.rollback()
    return added_count


def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        # 更新所有NULL的priority值
        videos = Video.query.filter(Video.priority.is_(None)).all()
        for video in videos:
            video.priority = 0
        if videos:
            db.session.commit()
            print(f'已更新 {len(videos)} 个视频的priority值')

        # 清理无效的视频标签关联
        orphan_video_tags = VideoTag.query.filter(
            ~VideoTag.video_id.in_(db.session.query(Video.id))
        ).all()
        for vt in orphan_video_tags:
            db.session.delete(vt)
        if orphan_video_tags:
            db.session.commit()
            print(f'已清理 {len(orphan_video_tags)} 个无效的视频标签关联')

        # 清理无效的用户交互记录
        orphan_interactions = UserInteraction.query.filter(
            ~UserInteraction.video_id.in_(db.session.query(Video.id))
        ).all()
        for ui in orphan_interactions:
            db.session.delete(ui)
        if orphan_interactions:
            db.session.commit()
            print(f'已清理 {len(orphan_interactions)} 个无效的用户交互记录')

        print('数据库初始化完成！')


def get_user_session():
    """获取或创建用户会话ID"""
    if 'user_session' not in session:
        session['user_session'] = str(random.randint(100000, 999999))
    return session['user_session']


@app.route('/')
def index():
    """首页 - 显示推荐视频"""
    user_session = get_user_session()
    recommended_videos = get_recommended_videos(user_session, limit=12)
    popular_tags = get_popular_tags(limit=10)
    return render_template('index.html',
                         videos=recommended_videos,
                         tags=popular_tags,
                         current_tag=None)


@app.route('/tag/<int:tag_id>')
def tag_page(tag_id):
    """标签页面 - 显示特定标签的视频"""
    tag = Tag.query.get_or_404(tag_id)
    videos = [vt.video for vt in tag.videos if vt.video is not None]
    # 按优先级和播放量排序（处理None值）
    videos = sorted(videos, key=lambda v: (v.priority or 0, v.view_count or 0), reverse=True)
    popular_tags = get_popular_tags(limit=10)
    return render_template('index.html',
                         videos=videos,
                         tags=popular_tags,
                         current_tag=tag)


@app.route('/video/<video_hash>')
def video_page(video_hash):
    """视频播放页面"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()

    # 记录播放
    user_session = get_user_session()
    record_interaction(video.id, user_session, 'view', score=1.0)

    # 增加播放计数
    video.view_count += 1
    db.session.commit()

    # 获取相关推荐
    recommended_videos = get_recommended_videos(user_session, limit=6, exclude_video_id=video.id)

    return render_template('video.html',
                         video=video,
                         recommended_videos=recommended_videos)


@app.route('/search')
def search():
    """搜索功能"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'videos': []})

    # 搜索标题和描述
    videos = Video.query.filter(
        (Video.title.contains(query)) |
        (Video.description.contains(query))
    ).all()

    # 搜索标签
    tag = Tag.query.filter(Tag.name.contains(query)).first()
    if tag:
        tag_videos = [vt.video for vt in tag.videos if vt.video is not None]
        # 合并结果去重
        video_ids = {v.id for v in videos}
        for v in tag_videos:
            if v.id not in video_ids:
                videos.append(v)

    return jsonify({
        'videos': [v.to_dict() for v in videos[:20]]
    })


@app.route('/api/videos', methods=['GET'])
def api_get_videos():
    """获取视频列表API"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    tag_id = request.args.get('tag_id', type=int)

    if tag_id:
        tag = Tag.query.get(tag_id)
        if tag:
            videos = [vt.video for vt in tag.videos if vt.video is not None]
            videos = sorted(videos, key=lambda v: (v.priority or 0, v.view_count or 0), reverse=True)
        else:
            videos = []
    else:
        videos = Video.query.all()
        videos = sorted(videos, key=lambda v: (v.priority or 0, v.view_count or 0), reverse=True)

    videos = videos[offset:offset + limit]

    return jsonify({
        'videos': [v.to_dict() for v in videos],
        'total': len(videos)
    })


@app.route('/api/videos/recommend', methods=['GET'])
def api_get_recommended_videos():
    """获取推荐视频列表API"""
    limit = request.args.get('limit', 12, type=int)
    user_session = get_user_session()

    recommended_videos = get_recommended_videos(user_session, limit=limit)

    return jsonify({
        'videos': [v.to_dict() for v in recommended_videos],
        'total': len(recommended_videos)
    })


@app.route('/api/video/<video_hash>', methods=['GET'])
def api_get_video(video_hash):
    """获取单个视频详情API"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()
    return jsonify(video.to_dict())


@app.route('/api/video/<video_hash>/like', methods=['POST'])
def like_video(video_hash):
    """点赞视频"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()
    user_session = get_user_session()

    video.like_count += 1
    record_interaction(video.id, user_session, 'like', score=2.0)
    db.session.commit()

    return jsonify({
        'success': True,
        'like_count': video.like_count
    })


@app.route('/api/video/<video_hash>/download', methods=['POST', 'GET'])
def download_video(video_hash):
    """下载视频（模拟）"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()
    user_session = get_user_session()

    video.download_count += 1
    record_interaction(video.id, user_session, 'download', score=3.0)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '下载已开始',
        'download_url': video.url,
        'download_count': video.download_count
    })


@app.route('/api/video/<video_hash>/priority', methods=['POST'])
def update_priority(video_hash):
    """更新视频优先级"""
    data = request.get_json()
    priority = data.get('priority', 0)

    video = Video.query.filter_by(hash=video_hash).first_or_404()
    video.priority = priority
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '优先级已更新'
    })


@app.route('/api/video/<video_hash>/regenerate', methods=['POST'])
def regenerate_thumbnail(video_hash):
    """重新生成视频缩略图和更新时长"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()

    if not video.local_path or not os.path.exists(video.local_path):
        return jsonify({
            'success': False,
            'message': '本地视频文件不存在'
        }), 400

    try:
        # 删除旧的缩略图文件
        for ext in ['.jpg', '.gif']:
            old_path = os.path.join('static', 'thumbnails', f'{video_hash}{ext}')
            if os.path.exists(old_path):
                os.remove(old_path)

        # 生成GIF预览图（循环播放的多帧）
        gif_path = os.path.join('static', 'thumbnails', f'{video_hash}.gif')
        gif_success = generate_video_gif(video.local_path, gif_path, num_frames=6, duration=500)

        # 如果GIF生成失败，生成静态缩略图
        thumbnail_path = os.path.join('static', 'thumbnails', f'{video_hash}.jpg')
        thumbnail_success = False

        if not gif_success:
            thumbnail_success = generate_video_thumbnail(video.local_path, thumbnail_path)

        # 懒加载机制：数据库中始终使用懒加载路径，不更新为静态路径
        # video.thumbnail 保持为 f'/thumbnail/{video_hash}'

        # 更新时长
        video_duration = get_video_duration(video.local_path)
        if video_duration:
            video.duration = video_duration

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '缩略图和时长已更新',
            'thumbnail': f'/thumbnail/{video_hash}',  # 返回懒加载路径
            'duration': video.duration,
            'is_gif': gif_success
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@app.route('/api/tags', methods=['GET'])
def api_get_tags():
    """获取所有标签"""
    tags = Tag.query.order_by(Tag.name).all()
    return jsonify({
        'tags': [tag.to_dict() for tag in tags]
    })


@app.route('/api/video/<video_hash>/tags', methods=['GET', 'PUT'])
def manage_video_tags(video_hash):
    """获取或更新视频标签"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()

    if request.method == 'GET':
        # 获取视频标签
        return jsonify({
            'tags': [vt.tag.to_dict() for vt in video.tags if vt.tag is not None],
            'tag_names': [vt.tag.name for vt in video.tags if vt.tag is not None]
        })
    else:
        # 更新视频标签
        data = request.get_json()
        tag_names = data.get('tags', [])

        # 删除现有标签关联
        VideoTag.query.filter_by(video_id=video.id).delete()

        # 添加新标签
        for tag_name in tag_names:
            if not tag_name.strip():
                continue

            tag = Tag.query.filter_by(name=tag_name.strip()).first()
            if not tag:
                # 创建新标签
                category = '类型'
                tag = Tag(name=tag_name.strip(), category=category)
                db.session.add(tag)
                db.session.flush()

            # 创建关联
            video_tag = VideoTag(video_id=video.id, tag_id=tag.id)
            db.session.add(video_tag)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '标签已更新',
            'tags': [vt.tag.to_dict() for vt in video.tags if vt.tag is not None]
        })


@app.route('/api/video/<video_hash>/favorite', methods=['POST'])
def toggle_favorite(video_hash):
    """切换视频收藏状态"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()
    user_session = get_user_session()

    # 查找是否已收藏
    interaction = UserInteraction.query.filter_by(
        video_id=video.id,
        user_session=user_session,
        interaction_type='favorite'
    ).first()

    if interaction:
        # 已收藏，取消收藏
        db.session.delete(interaction)
        favorited = False
    else:
        # 未收藏，添加收藏
        interaction = UserInteraction(
            video_id=video.id,
            user_session=user_session,
            interaction_type='favorite',
            interaction_score=5.0
        )
        db.session.add(interaction)
        favorited = True

    db.session.commit()

    return jsonify({
        'success': True,
        'favorited': favorited,
        'message': '已收藏' if favorited else '已取消收藏'
    })


@app.route('/api/video/<video_hash>/is-favorite', methods=['GET'])
def is_favorite(video_hash):
    """检查视频是否已收藏"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()
    user_session = get_user_session()

    interaction = UserInteraction.query.filter_by(
        video_id=video.id,
        user_session=user_session,
        interaction_type='favorite'
    ).first()

    return jsonify({
        'is_favorite': interaction is not None
    })


@app.route('/favorites')
def favorites_page():
    """收藏页面"""
    user_session = get_user_session()

    # 获取用户收藏的视频
    favorite_interactions = UserInteraction.query.filter_by(
        user_session=user_session,
        interaction_type='favorite'
    ).order_by(UserInteraction.created_at.desc()).all()

    favorite_videos = []
    for interaction in favorite_interactions:
        if interaction.video:
            favorite_videos.append(interaction.video)

    popular_tags = get_popular_tags(limit=10)
    return render_template('index.html',
                         videos=favorite_videos,
                         tags=popular_tags,
                         current_tag=None,
                         is_favorites_page=True)


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    return jsonify({
        'success': True,
        'config': config
    })


@app.route('/api/config', methods=['PUT'])
def update_config():
    """更新配置"""
    data = request.get_json()

    # 更新配置
    for key, value in data.items():
        config[key] = value

    # 保存到文件
    if save_config(config):
        return jsonify({
            'success': True,
            'message': '配置已更新',
            'config': config
        })
    else:
        return jsonify({
            'success': False,
            'message': '保存配置失败'
        }), 500


@app.route('/api/videos/clear', methods=['POST'])
def clear_videos():
    """清空所有视频数据"""
    data = request.get_json() or {}
    confirm_text = data.get('confirm_text', '')

    if confirm_text != 'CLEAR_ALL_VIDEOS':
        return jsonify({
            'success': False,
            'message': '请输入确认文本: CLEAR_ALL_VIDEOS'
        }), 400

    try:
        # 删除所有视频记录（包括关联的标签关系）
        Video.query.delete()
        # 删除视频标签关联表
        VideoTag.query.delete()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '所有视频数据已清空'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'清空失败: {str(e)}'
        }), 500


@app.route('/manage')
def manage_page():
    """视频管理页面"""
    videos = Video.query.order_by(Video.created_at.desc()).all()
    return render_template('manage.html', videos=videos)


@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    """上传视频"""
    if 'video' not in request.files:
        return jsonify({'success': False, 'message': '没有选择视频文件'}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'success': False, 'message': '没有选择视频文件'}), 400

    if not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({'success': False, 'message': '不支持的文件格式'}), 400

    # 保存视频文件
    video_filename = secure_filename(video_file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    video_filename = f"{timestamp}_{video_filename}"
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    video_file.save(video_path)

    # 处理缩略图
    thumbnail_url = None
    if 'thumbnail' in request.files:
        thumbnail_file = request.files['thumbnail']
        if thumbnail_file and allowed_file(thumbnail_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            thumb_filename = secure_filename(thumbnail_file.filename)
            thumb_filename = f"{timestamp}_{thumb_filename}"
            thumb_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumb_filename)
            thumbnail_file.save(thumb_path)
            thumbnail_url = f"/static/thumbnails/{thumb_filename}"

    # 获取其他表单数据
    title = request.form.get('title', video_filename)
    description = request.form.get('description', '')
    tags_str = request.form.get('tags', '')
    priority = int(request.form.get('priority', 0))

    # 生成视频hash
    video_url = f"/static/uploads/{video_filename}"
    video_hash = hashlib.sha256(video_url.encode('utf-8')).hexdigest()

    # 创建视频记录
    video = Video(
        hash=video_hash,
        title=title,
        description=description,
        url=video_url,
        thumbnail=thumbnail_url or '/static/thumbnails/default.png',
        priority=priority,
        is_downloaded=True,
        local_path=video_path
    )

    # 处理标签
    if tags_str:
        tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                category = '类型'
                tag = Tag(name=tag_name, category=category)
                db.session.add(tag)
                db.session.flush()

            video.tags.append(tag)

    db.session.add(video)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '视频上传成功',
        'video': video.to_dict()
    })


@app.route('/api/video/<video_hash>', methods=['DELETE'])
def delete_video(video_hash):
    """删除视频"""
    video = Video.query.filter_by(hash=video_hash).first_or_404()

    # 删除本地文件
    if video.local_path and os.path.exists(video.local_path):
        os.remove(video.local_path)

    db.session.delete(video)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '视频已删除'
    })


@app.route('/api/scan', methods=['POST'])
def scan_videos():
    """扫描配置的目录并添加视频"""
    data = request.get_json() or {}
    scan_directories = data.get('scan_directories', None)
    force_rescan = data.get('force_rescan', False)

    # 使用传入的目录或配置文件中的目录
    if scan_directories is None:
        scan_directories = config.get('scan_directories', [])

    total_added = 0
    results = []

    for dir_config in scan_directories:
        if not dir_config.get('enabled', True):
            continue

        dir_path = dir_config.get('path', '')
        recursive = dir_config.get('recursive', True)

        print(f'正在扫描目录: {dir_path} (递归: {recursive})')

        try:
            # 扫描目录
            video_files = scan_directory(dir_path, recursive, config.get('supported_formats'))

            if force_rescan:
                # 强制重新扫描：删除所有此目录的视频并重新添加
                dir_prefix = dir_path.replace('\\', '/').rstrip('/')
                existing_videos = Video.query.filter(Video.url.like(f'{dir_prefix}%')).all()
                for video in existing_videos:
                    db.session.delete(video)
                db.session.commit()

            # 添加到数据库
            added = add_local_videos(
                video_files,
                default_tags=config.get('default_tags', ['本地视频']),
                default_priority=config.get('default_priority', 0)
            )

            total_added += added
            results.append({
                'directory': dir_path,
                'found': len(video_files),
                'added': added,
                'error': None
            })

            print(f'目录 {dir_path}: 找到 {len(video_files)} 个视频，添加 {added} 个')
        except Exception as e:
            print(f'扫描目录 {dir_path} 时出错: {str(e)}')
            results.append({
                'directory': dir_path,
                'found': 0,
                'added': 0,
                'error': str(e)
            })

    return jsonify({
        'success': True,
        'message': f'扫描完成，共添加 {total_added} 个视频',
        'total_added': total_added,
        'results': results
    })


@app.route('/api/thumbnails/regenerate', methods=['POST'])
def regenerate_all_thumbnails():
    """批量重新生成所有视频的缩略图和时长"""
    print("\n" + "="*60)
    print('[INFO] 开始批量重新生成缩略图...')
    print("="*60)

    videos = Video.query.filter(Video.local_path.isnot(None)).all()
    total = len(videos)

    print(f'[INFO] 找到 {total} 个有本地路径的视频')

    if total == 0:
        return jsonify({'success': False, 'message': '没有本地视频需要处理'})

    # 生成唯一的任务ID
    task_id = f'thumb_{datetime.now().strftime("%Y%m%d%H%M%S")}'

    print(f'[INFO] 创建任务ID: {task_id}')

    # 初始化进度
    progress_store[task_id] = {
        'current': 0,
        'total': total,
        'status': 'running',
        'message': '准备开始...'
    }

    print(f'[INFO] 初始化进度: {progress_store[task_id]}')

    # 在后台线程中执行缩略图生成
    def generate_in_background():
        print(f"\n[线程] 后台任务线程开始: {task_id}")

        success_count = 0
        gif_count = 0
        no_path_count = 0
        not_exist_count = 0
        errors = []

        try:
            for i, video in enumerate(videos, 1):
                try:
                    # 更新进度
                    progress_store[task_id]['current'] = i
                    progress_store[task_id]['message'] = f'正在处理: {video.title}'
                    print(f"\n[进度 {i}/{total}] {video.title}")

                    if not video.local_path:
                        no_path_count += 1
                        print(f"  [跳过] 没有本地路径")
                        continue

                    if not os.path.exists(video.local_path):
                        not_exist_count += 1
                        print(f"  [跳过] 文件不存在")
                        continue

                    print(f"  [路径] {video.local_path}")

                    # 删除旧的缩略图文件
                    for ext in ['.jpg', '.gif']:
                        old_path = os.path.join('static', 'thumbnails', f'{video.hash}{ext}')
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            print(f"  [删除] {old_path}")

                    # 生成GIF预览图
                    gif_path = os.path.join('static', 'thumbnails', f'{video.hash}.gif')
                    print(f"  [开始] 生成GIF预览...")
                    gif_success = generate_video_gif(video.local_path, gif_path, num_frames=6, duration=500)

                    # 如果GIF生成失败，生成静态缩略图
                    thumbnail_path = os.path.join('static', 'thumbnails', f'{video.hash}.jpg')
                    thumbnail_success = False

                    if not gif_success:
                        print(f"  [降级] GIF失败,生成静态图...")
                        thumbnail_success = generate_video_thumbnail(video.local_path, thumbnail_path)

                    if gif_success:
                        # 懒加载机制：不更新数据库中的 thumbnail 字段
                        gif_count += 1
                        print(f"  [成功] GIF生成成功")
                    elif thumbnail_success:
                        # 懒加载机制：不更新数据库中的 thumbnail 字段
                        print(f"  [成功] JPG生成成功")
                    else:
                        print(f"  [失败] 预览图生成失败")
                        errors.append(f'{video.title}: 预览图生成失败')

                    # 更新时长
                    video_duration = get_video_duration(video.local_path)
                    if video_duration:
                        video.duration = video.duration

                    success_count += 1

                    # 更新进度信息
                    progress = (i / total) * 100
                    progress_store[task_id]['progress'] = progress
                    print(f"  [进度条] {progress:.1f}%")

                except Exception as e:
                    error_msg = f'{video.title}: {str(e)}'
                    errors.append(error_msg)
                    print(f"\n[错误] 处理视频失败:")
                    print(f"  异常: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue

            db.session.commit()

            # 完成
            progress_store[task_id]['status'] = 'completed'
            progress_store[task_id]['message'] = f'完成! 成功生成 {success_count}/{total} 个缩略图 ({gif_count} 个GIF)'
            progress_store[task_id]['success_count'] = success_count

            print(f"\n[完成] 任务完成: {success_count}/{total} 个缩略图, {gif_count} 个GIF")
            print(f"[统计] 成功={success_count}, GIF={gif_count}, 无路径={no_path_count}, 文件不存在={not_exist_count}")
            print("="*60 + "\n")

        except Exception as e:
            progress_store[task_id]['status'] = 'error'
            progress_store[task_id]['message'] = f'出错: {str(e)}'
            print(f"\n[严重错误] {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*60 + "\n")

    # 启动后台线程
    thread = threading.Thread(target=generate_in_background, daemon=False)
    thread.start()
    print(f"[线程] 后台线程已启动\n")

    # 立即返回,不等待线程完成
    return jsonify({
        'success': True,
        'task_id': task_id,
        'total': total,
        'message': f'开始处理 {total} 个视频...'
    })


@app.route('/api/thumbnails/progress/<task_id>')
def get_thumbnail_progress(task_id):
    """获取缩略图生成进度"""
    print(f"[进度查询] task_id={task_id}")

    if task_id in progress_store:
        progress = progress_store[task_id]
        print(f"[进度数据] {progress}")
        return jsonify({
            'success': True,
            'data': progress
        })

    print(f"[警告] 任务 {task_id} 不存在于进度存储中")
    return jsonify({
        'success': False,
        'message': '任务不存在'
    })


@app.route('/api/video/add', methods=['POST'])
def add_video_url():
    """通过URL添加视频"""
    data = request.get_json()
    video_url = data.get('url', '').strip()

    if not video_url:
        return jsonify({'success': False, 'message': '请输入视频URL'}), 400

    if not video_url.startswith('http://') and not video_url.startswith('https://'):
        return jsonify({'success': False, 'message': '请输入有效的URL'}), 400

    # 检查是否已存在
    video_hash = Video.generate_hash(video_url)
    existing_video = Video.query.filter_by(hash=video_hash).first()
    if existing_video:
        return jsonify({'success': False, 'message': '该视频已存在'}), 400

    # 创建视频记录
    title = data.get('title', '未命名视频')
    description = data.get('description', '')
    thumbnail = data.get('thumbnail', '/static/thumbnails/default.png')
    duration = data.get('duration', 0)
    tags_str = data.get('tags', '')
    priority = int(data.get('priority', 0))

    video = Video(
        hash=video_hash,
        title=title,
        description=description,
        url=video_url,
        thumbnail=thumbnail,
        duration=duration,
        priority=priority
    )

    # 处理标签
    if tags_str:
        tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
        for tag_name in tag_names:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                category = '类型'
                tag = Tag(name=tag_name, category=category)
                db.session.add(tag)
                db.session.flush()

            video.tags.append(tag)

    db.session.add(video)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '视频添加成功',
        'video': video.to_dict()
    })


def get_recommended_videos(user_session, limit=10, exclude_video_id=None):
    """获取推荐视频"""
    # 获取用户偏好的标签
    user_preferences = UserPreference.query.filter_by(user_session=user_session).order_by(
        UserPreference.preference_score.desc()
    ).limit(5).all()

    # 获取所有视频
    videos = Video.query.all()

    # 推荐算法：计算每个视频的推荐分数
    video_scores = []
    for video in videos:
        if exclude_video_id and video.id == exclude_video_id:
            continue

        score = (video.priority or 0) * 0.3 + (video.view_count or 0) * 0.0001

        # 根据用户偏好加分
        if user_preferences:
            for pref in user_preferences:
                if any(tag.tag_id == pref.tag_id for tag in video.tags):
                    score += pref.preference_score * 5

        video_scores.append((video, score))

    # 排序并取前N个
    video_scores.sort(key=lambda x: x[1], reverse=True)
    recommended = [v for v, s in video_scores[:limit]]

    # 如果推荐不够，随机补充
    if len(recommended) < limit:
        remaining_videos = [v for v in videos if v not in recommended]
        random.shuffle(remaining_videos)
        recommended.extend(remaining_videos[:limit - len(recommended)])

    return recommended


def record_interaction(video_id, user_session, interaction_type, score=1.0):
    """记录用户交互并更新用户偏好"""
    # 记录交互
    interaction = UserInteraction(
        video_id=video_id,
        user_session=user_session,
        interaction_type=interaction_type,
        interaction_score=score
    )
    db.session.add(interaction)

    # 更新用户偏好
    video_tags = VideoTag.query.filter_by(video_id=video_id).all()
    for vt in video_tags:
        preference = UserPreference.query.filter_by(
            user_session=user_session,
            tag_id=vt.tag_id
        ).first()

        if preference:
            preference.preference_score += score * 0.1
            preference.interaction_count += 1
            preference.updated_at = datetime.utcnow()
        else:
            preference = UserPreference(
                user_session=user_session,
                tag_id=vt.tag_id,
                preference_score=1.0 + score * 0.1,
                interaction_count=1
            )
            db.session.add(preference)

    db.session.commit()


def get_popular_tags(limit=10):
    """获取热门标签"""
    tags = Tag.query.all()
    tags.sort(key=lambda t: len(t.videos), reverse=True)
    return tags[:limit]


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy'
    })


@app.route('/api/dependencies/check', methods=['GET'])
def check_dependencies():
    """检查依赖是否正确安装"""
    dependencies = {
        'opencv': {'name': 'opencv-python', 'installed': False, 'version': None},
        'pillow': {'name': 'Pillow', 'installed': False, 'version': None},
        'flask': {'name': 'Flask', 'installed': False, 'version': None},
    }

    # 检查 OpenCV
    try:
        import cv2
        dependencies['opencv']['installed'] = True
        dependencies['opencv']['version'] = cv2.__version__
    except ImportError:
        pass

    # 检查 Pillow
    try:
        from PIL import Image
        dependencies['pillow']['installed'] = True
        dependencies['pillow']['version'] = Image.__version__
    except ImportError:
        pass

    # 检查 Flask
    try:
        import flask
        dependencies['flask']['installed'] = True
        dependencies['flask']['version'] = flask.__version__
    except ImportError:
        pass

    all_installed = all(dep['installed'] for dep in dependencies.values())

    return jsonify({
        'success': all_installed,
        'dependencies': dependencies,
        'message': '所有依赖已安装' if all_installed else '部分依赖未安装'
    })


if __name__ == '__main__':
    PORT = 80
    print(f'Starting Flask server on 0.0.0.0:{PORT}')
    init_db()  # 初始化数据库
    app.run(host='0.0.0.0', port=PORT, debug=True)
