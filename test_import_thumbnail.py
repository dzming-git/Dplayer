#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试缩略图服务模块是否能正常导入
"""

import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("测试缩略图服务模块导入")
print("=" * 60)
print()

# 测试1: 导入缩略图服务
try:
    import thumbnail_service
    print("[OK] thumbnail_service imported successfully")
except Exception as e:
    print(f"[ERROR] thumbnail_service import failed: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试2: 导入客户端
try:
    import thumbnail_service_client
    print("[OK] thumbnail_service_client imported successfully")
except Exception as e:
    print(f"[ERROR] thumbnail_service_client import failed: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试3: 测试Task类
try:
    task = thumbnail_service.Task("test_id", "/path/to/video.mp4", "hash123", {'format': 'jpg'})
    print("[OK] Task class created successfully")
    print(f"    Task ID: {task.task_id}")
    print(f"    Status: {task.status}")
except Exception as e:
    print(f"[ERROR] Task class creation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试4: 测试TaskManager类
try:
    manager = thumbnail_service.TaskManager(max_concurrent=2, queue_size=10)
    print("[OK] TaskManager class created successfully")
    print(f"    Max Concurrent: {manager.max_concurrent}")
    print(f"    Queue Size: {manager.queue_size}")
except Exception as e:
    print(f"[ERROR] TaskManager class creation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# 测试5: 测试客户端
try:
    client = thumbnail_service_client.ThumbnailServiceClient(service_url='http://localhost:5001')
    print("[OK] ThumbnailServiceClient created successfully")
    print(f"    Service URL: {client.service_url}")
except Exception as e:
    print(f"[ERROR] ThumbnailServiceClient creation failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
