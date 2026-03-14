import sqlite3
import os
import cv2

DB_FILE = 'instance/dplayer.db'

def migrate():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 检查字段是否存在
    cursor.execute("PRAGMA table_info(videos)")
    columns = [row[1] for row in cursor.fetchall()]

    # 添加 width 和 height 字段
    if 'width' not in columns:
        cursor.execute("ALTER TABLE videos ADD COLUMN width INTEGER DEFAULT 0")
        print("添加 width 字段")

    if 'height' not in columns:
        cursor.execute("ALTER TABLE videos ADD COLUMN height INTEGER DEFAULT 0")
        print("添加 height 字段")

    conn.commit()

    # 为没有分辨率的视频获取分辨率
    cursor.execute("SELECT id, local_path FROM videos WHERE (width IS NULL OR width = 0) AND local_path IS NOT NULL")
    rows = cursor.fetchall()

    print(f"需要更新分辨率的视频数量: {len(rows)}")

    for video_id, local_path in rows:
        if not local_path or not os.path.exists(local_path):
            continue

        try:
            cap = cv2.VideoCapture(local_path)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()

                cursor.execute("UPDATE videos SET width = ?, height = ? WHERE id = ?", (width, height, video_id))
                print(f"更新视频 {video_id}: {width}x{height}")
            else:
                cap.release()
        except Exception as e:
            print(f"处理视频 {video_id} 失败: {e}")

    conn.commit()
    conn.close()
    print("迁移完成")

if __name__ == '__main__':
    migrate()
