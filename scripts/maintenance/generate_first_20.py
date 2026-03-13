"""
生成前20个没有缩略图的视频的缩略图
"""
import sys
import io
import time

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import app, Video, db
from app import generate_video_thumbnail
import os

print("=" * 80)
print("生成前20个缩略图")
print("=" * 80)
print()

with app.app_context():
    # 获取最新的视频
    videos = Video.query.order_by(Video.id.desc()).limit(20).all()

    print(f"最新的20个视频:")
    print()

    success_count = 0
    fail_count = 0

    for i, video in enumerate(videos, 1):
        print(f"[{i}/20] {video.title[:40]}")

        # 检查是否已有缩略图
        thumbnail_dir = 'static/thumbnails'
        gif_path = os.path.join(thumbnail_dir, f'{video.hash}.gif')
        jpg_path = os.path.join(thumbnail_dir, f'{video.hash}.jpg')

        if os.path.exists(gif_path) or os.path.exists(jpg_path):
            print(f"    跳过: 已有缩略图")
            print()
            continue

        # 检查本地路径
        if not video.local_path or not os.path.exists(video.local_path):
            print(f"    跳过: 文件不存在")
            fail_count += 1
            print()
            continue

        # 生成缩略图
        print(f"    生成中...")
        jpg_success = generate_video_thumbnail(video.local_path, jpg_path)

        if jpg_success:
            print(f"    ✓ 成功")
            success_count += 1
        else:
            print(f"    ✗ 失败")
            fail_count += 1

        print()

    print("=" * 80)
    print("生成完成")
    print("=" * 80)
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
