"""
强制更新所有视频的缩略图URL为懒加载格式
"""
import sys
import io

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import app, Video, db

print("=" * 80)
print("强制更新缩略图URL")
print("=" * 80)
print()

with app.app_context():
    # 获取所有视频
    videos = Video.query.all()
    print(f"找到 {len(videos)} 个视频")
    print()

    updated_count = 0
    wrong_count = 0

    for video in videos:
        expected_url = f'/thumbnail/{video.hash}'

        if video.thumbnail != expected_url:
            print(f"更新: {video.title[:40]}")
            print(f"  旧URL: {video.thumbnail}")
            print(f"  新URL: {expected_url}")
            video.thumbnail = expected_url
            updated_count += 1
        else:
            wrong_count += 1

    if updated_count > 0:
        db.session.commit()
        print()
        print(f"✓ 已更新 {updated_count} 个视频的缩略图URL")
    else:
        print()
        print(f"✓ 所有 {wrong_count} 个视频的缩略图URL已是正确的格式")

    print()
    print("=" * 80)
    print("更新完成")
    print("=" * 80)
