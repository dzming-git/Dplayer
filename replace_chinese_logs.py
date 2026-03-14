#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to replace Chinese logger messages in app.py with English
"""

import re

# Read the file
with open('C:/Users/71555/WorkBuddy/Dplayer/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacements for Chinese logger messages
replacements = {
    # Thumbnail related
    'logger.info(f"缩略图微服务已连接: {THUMBNAIL_SERVICE_URL}")': 'logger.info(f"Thumbnail microservice connected: {THUMBNAIL_SERVICE_URL}")',
    'logger.warning(f"缩略图微服务不可用，将使用降级模式: {THUMBNAIL_SERVICE_URL}")': 'logger.warning(f"Thumbnail microservice unavailable, will use fallback mode: {THUMBNAIL_SERVICE_URL}")',
    'logger.info("降级模式已启用")': 'logger.info("Fallback mode enabled")',
    'logger.error("降级模式未启用，缩略图功能将不可用")': 'logger.error("Fallback mode not enabled, thumbnail feature will be unavailable")',
    'logger.error(f"初始化缩略图服务失败: {str(e)}")': 'logger.error(f"Failed to initialize thumbnail service: {str(e)}")',
    'logger.info("将使用降级模式（本地生成）")': 'logger.info("Will use fallback mode (local generation)")',
    'logger.info("缩略图微服务未启用，使用本地生成模式")': 'logger.info("Thumbnail microservice not enabled, using local generation mode")',
    
    # Runtime log messages
    'runtime_log.warning(f"[缩略图生成失败] 视频不存在: video_hash={video_hash}")': 'runtime_log.warning(f"[Thumbnail generation failed] Video does not exist: video_hash={video_hash}")',
    'runtime_log.info(f"[缩略图生成开始] video_title={video.title}, video_hash={video_hash}, local_path={video.local_path}")': 'runtime_log.info(f"[Thumbnail generation started] video_title={video.title}, video_hash={video_hash}, local_path={video.local_path}")',
    'runtime_log.info(f"[缩略图生成成功] 格式=JPG, video_title={video.title}, video_hash={video_hash}, 总耗时={total_time:.3f}s, 路径={jpg_path}")': 'runtime_log.info(f"[Thumbnail generation successful] Format=JPG, video_title={video.title}, video_hash={video_hash}, total_time={total_time:.3f}s, path={jpg_path}")',
    'runtime_log.info(f"[缩略图生成成功] 格式=GIF, video_title={video.title}, video_hash={video_hash}, 总耗时={total_time:.3f}s, 路径={gif_path}")': 'runtime_log.info(f"[Thumbnail generation successful] Format=GIF, video_title={video.title}, video_hash={video_hash}, total_time={total_time:.3f}s, path={gif_path}")',
    'runtime_log.error(f"[缩略图生成失败] video_title={video.title}, video_hash={video_hash}, local_path={video.local_path}, 耗时={total_time:.3f}s")': 'runtime_log.error(f"[Thumbnail generation failed] video_title={video.title}, video_hash={video_hash}, local_path={video.local_path}, time_spent={total_time:.3f}s")',
    'runtime_log.error(f"[缩略图生成异常] video_hash={video_hash}, error={str(e)}, 耗时={total_time:.3f}s")': 'runtime_log.error(f"[Thumbnail generation exception] video_hash={video_hash}, error={str(e)}, time_spent={total_time:.3f}s")',
    'runtime_log.error(f"[缩略图异常] {video_hash}: {str(e)}")': 'runtime_log.error(f"[Thumbnail exception] {video_hash}: {str(e)}")',
    
    # Debug log messages
    'debug_log.debug(f"[GIF生成] 开始生成: video_path={video_path}, output={output_path}, num_frames={num_frames}, size={size}, duration={duration}ms")': 'debug_log.debug(f"[GIF generation] Start generating: video_path={video_path}, output={output_path}, num_frames={num_frames}, size={size}, duration={duration}ms")',
    'debug_log.warning(f"[时长更新] 更新失败: {video.title}, error={e}")': 'debug_log.warning(f"[Duration update] Update failed: {video.title}, error={e}")',
    'debug_log.error(f"[缩略图状态] 查询异常: video_hash={video_hash}, error={str(e)}")': 'debug_log.error(f"[Thumbnail status] Query exception: video_hash={video_hash}, error={str(e)}")',
}

# Apply replacements
for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        print(f"Replaced: {old[:50]}...")
    else:
        print(f"Not found: {old[:50]}...")

# Write back
with open('C:/Users/71555/WorkBuddy/Dplayer/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nReplacements completed!")
