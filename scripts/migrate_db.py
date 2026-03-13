#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
添加用户系统和视频权限相关的字段和表
"""

import sqlite3
import os
import sys

# 获取项目根目录
BASEDIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASEDIR, 'instance', 'dplayer.db')


def migrate_database():
    """执行数据库迁移"""
    
    print(f"[*] 数据库路径: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"[!] 数据库文件不存在: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取现有表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"[*] 现有表: {existing_tables}")
    
    changes_made = []
    
    # 1. 检查 videos 表是否有 min_role 字段
    cursor.execute("PRAGMA table_info(videos)")
    video_columns = [row[1] for row in cursor.fetchall()]
    
    if 'min_role' not in video_columns:
        print("[*] 添加 videos.min_role 字段...")
        cursor.execute("ALTER TABLE videos ADD COLUMN min_role INTEGER DEFAULT 0 NOT NULL")
        changes_made.append("添加 videos.min_role 字段")
    else:
        print("[*] videos.min_role 字段已存在")
    
    # 2. 创建 users 表
    if 'users' not in existing_tables:
        print("[*] 创建 users 表...")
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                password_hash VARCHAR(256) NOT NULL,
                role INTEGER DEFAULT 1 NOT NULL,
                email VARCHAR(120) UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        cursor.execute("CREATE INDEX ix_users_username ON users (username)")
        changes_made.append("创建 users 表")
    else:
        print("[*] users 表已存在")
    
    # 3. 创建 user_sessions 表
    if 'user_sessions' not in existing_tables:
        print("[*] 创建 user_sessions 表...")
        cursor.execute('''
            CREATE TABLE user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_token VARCHAR(128) NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute("CREATE INDEX ix_user_sessions_token ON user_sessions (session_token)")
        changes_made.append("创建 user_sessions 表")
    else:
        print("[*] user_sessions 表已存在")
    
    # 4. 检查是否有 root 用户
    cursor.execute("SELECT id FROM users WHERE role = 3")
    if not cursor.fetchone():
        print("[*] 创建默认 root 用户...")
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('root123456')
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, 3, 1)
        ''', ('root', password_hash))
        changes_made.append("创建默认 root 用户 (密码: root123456)")
    else:
        print("[*] root 用户已存在")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    if changes_made:
        print("\n[OK] 数据库迁移完成，更改如下:")
        for change in changes_made:
            print(f"    - {change}")
    else:
        print("\n[OK] 数据库已是最新状态，无需迁移")
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Dplayer 数据库迁移脚本")
    print("=" * 60)
    print()
    
    try:
        migrate_database()
    except Exception as e:
        print(f"[!] 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("[*] 完成")
