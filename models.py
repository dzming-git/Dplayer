from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

class Video(db.Model):
    """视频模型"""
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64), unique=True, nullable=False, index=True)  # 视频唯一标识符
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(500), nullable=False)  # 视频URL
    thumbnail = db.Column(db.String(500))  # 视频缩略图URL
    duration = db.Column(db.Integer)  # 视频时长(秒)
    file_size = db.Column(db.BigInteger)  # 文件大小(字节)
    view_count = db.Column(db.Integer, default=0)  # 播放次数
    like_count = db.Column(db.Integer, default=0)  # 点赞数
    download_count = db.Column(db.Integer, default=0)  # 下载次数
    priority = db.Column(db.Integer, default=0)  # 优先级，数值越大优先级越高
    is_downloaded = db.Column(db.Boolean, default=False)  # 是否已下载到本地
    local_path = db.Column(db.String(500))  # 本地存储路径
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    tags = db.relationship('VideoTag', back_populates='video', cascade='all, delete-orphan')
    user_interactions = db.relationship('UserInteraction', back_populates='video', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Video {self.title}>'

    @staticmethod
    def generate_hash(video_url):
        """生成视频唯一hash"""
        return hashlib.sha256(video_url.encode('utf-8')).hexdigest()

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'hash': self.hash,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'thumbnail': self.thumbnail,
            'duration': self.duration,
            'file_size': self.file_size,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'download_count': self.download_count,
            'priority': self.priority,
            'is_downloaded': self.is_downloaded,
            'local_path': self.local_path,
            'tags': [vt.tag.to_dict() for vt in self.tags if vt.tag is not None],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))  # 标签分类：如 "类型", "作者", "地区" 等
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    videos = db.relationship('VideoTag', back_populates='tag', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Tag {self.name}>'

    def video_count(self):
        """获取实际存在的视频数量（过滤掉已删除的视频）"""
        return len([vt for vt in self.videos if vt.video is not None])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'video_count': self.video_count()
        }


class VideoTag(db.Model):
    """视频-标签关联表"""
    __tablename__ = 'video_tags'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    video = db.relationship('Video', back_populates='tags')
    tag = db.relationship('Tag', back_populates='videos')

    # 唯一约束，防止重复关联
    __table_args__ = (db.UniqueConstraint('video_id', 'tag_id', name='_video_tag_uc'),)


class UserInteraction(db.Model):
    """用户交互记录模型"""
    __tablename__ = 'user_interactions'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    user_session = db.Column(db.String(100), nullable=False)  # 用户会话ID（简单模拟用户）
    interaction_type = db.Column(db.String(20), nullable=False)  # 交互类型: view, like, download, share, favorite
    interaction_score = db.Column(db.Float, default=0.0)  # 交互评分（用于推荐算法）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    video = db.relationship('Video', back_populates='user_interactions')

    def __repr__(self):
        return f'<UserInteraction {self.user_session} - {self.interaction_type}>'


class UserPreference(db.Model):
    """用户偏好模型"""
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_session = db.Column(db.String(100), nullable=False, index=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    preference_score = db.Column(db.Float, default=1.0)  # 偏好评分，越高表示越喜欢
    interaction_count = db.Column(db.Integer, default=0)  # 交互次数
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserPreference {self.user_session} - {self.preference_score}>'
