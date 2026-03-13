"""
迁移脚本: 将动态路由改为静态文件路由
将所有视频的thumbnail字段从 /thumbnail/xxx 改为 /static/thumbnails/xxx.jpg
"""
import os
import sys
sys.path.insert(0, '.')
from app import app, db, Video

def migrate_thumbnails():
    """迁移缩略图URL到静态文件格式"""
    with app.app_context():
        print("=" * 80)
        print("迁移缩略图URL到静态文件格式")
        print("=" * 80)

        # 获取所有视频
        videos = Video.query.all()
        print(f"\n总视频数: {len(videos)}")

        # 统计
        updated_count = 0
        default_count = 0
        error_count = 0

        thumbnail_dir = os.path.join('static', 'thumbnails')

        for i, video in enumerate(videos, 1):
            # 检查缩略图文件
            jpg_path = os.path.join(thumbnail_dir, f'{video.hash}.jpg')
            gif_path = os.path.join(thumbnail_dir, f'{video.hash}.gif')

            old_thumbnail = video.thumbnail

            try:
                if os.path.exists(jpg_path):
                    # 优先使用JPG
                    new_thumbnail = f'/static/thumbnails/{video.hash}.jpg'
                    video.thumbnail = new_thumbnail
                    updated_count += 1
                elif os.path.exists(gif_path):
                    # 使用GIF
                    new_thumbnail = f'/static/thumbnails/{video.hash}.gif'
                    video.thumbnail = new_thumbnail
                    updated_count += 1
                else:
                    # 没有缩略图,使用默认图
                    new_thumbnail = '/static/thumbnails/default.png'
                    video.thumbnail = new_thumbnail
                    default_count += 1

                # 显示变更(仅显示前10个)
                if i <= 10:
                    print(f"\n[{i}/{len(videos)}] {video.title[:50]}...")
                    print(f"  旧URL: {old_thumbnail}")
                    print(f"  新URL: {new_thumbnail}")
                elif i == 11:
                    print("\n... (省略其余视频)")

            except Exception as e:
                error_count += 1
                print(f"\n[ERROR] 视频 ID={video.id} 处理失败: {e}")

        # 提交更改
        print("\n" + "=" * 80)
        print("提交更改到数据库...")
        print("=" * 80)

        try:
            db.session.commit()
            print("✓ 更新成功!")
        except Exception as e:
            db.session.rollback()
            print(f"✗ 更新失败: {e}")
            return False

        # 统计结果
        print("\n" + "=" * 80)
        print("迁移结果统计")
        print("=" * 80)
        print(f"总视频数: {len(videos)}")
        print(f"已更新(有缩略图): {updated_count}")
        print(f"使用默认缩略图: {default_count}")
        print(f"处理失败: {error_count}")

        # 验证
        print("\n" + "=" * 80)
        print("验证迁移结果")
        print("=" * 80)

        # 随机抽样验证
        import random
        sample_videos = random.sample(videos, min(10, len(videos)))

        for video in sample_videos:
            print(f"\n{video.title[:50]}...")
            print(f"  Hash: {video.hash[:16]}...")
            print(f"  Thumbnail: {video.thumbnail}")

            # 检查文件是否存在
            if video.thumbnail.startswith('/static/thumbnails/'):
                filename = video.thumbnail.split('/')[-1]
                filepath = os.path.join(thumbnail_dir, filename)
                exists = os.path.exists(filepath)
                print(f"  文件存在: {exists}")

                if not exists and 'default' not in video.thumbnail:
                    print(f"  [WARNING] 缩略图文件不存在!")

        print("\n" + "=" * 80)
        print("迁移完成!")
        print("=" * 80)
        print("\n下一步:")
        print("1. 重启Flask应用")
        print("2. 清除浏览器缓存")
        print("3. 测试缩略图加载")

        return True

if __name__ == '__main__':
    print("警告: 此操作将修改所有视频的缩略图URL")
    response = input("是否继续? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        success = migrate_thumbnails()
        if success:
            print("\n迁移成功!")
        else:
            print("\n迁移失败!")
    else:
        print("操作已取消")
