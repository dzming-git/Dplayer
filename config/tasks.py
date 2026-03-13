#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步缩略图生成任务
使用Celery实现异步处理
"""

import os
import cv2
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
from celery import shared_task, chain, group

from config.celery_config import app, RESOURCE_LIMITS
from services.resource_monitor import ResourceLimiter, ResourceLimit, ResourceType
from utils.config_manager import get_config

logger = logging.getLogger(__name__)

# 获取配置
config = get_config()
THUMBNAIL_DIR = os.path.join(config.static_dir or 'static', 'thumbnails')
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


@shared_task(
    name='tasks.generate_thumbnail',
    bind=True,
    max_retries=3,
    soft_time_limit=240,
    time_limit=300,
)
def generate_thumbnail(
    self,
    video_path: str,
    video_hash: str = None,
    output_format: str = 'webp',
    width: int = 320,
    height: int = None,
    quality: int = 85,
    timestamp: float = 5.0  # 截取第5秒的帧
):
    """
    异步生成缩略图

    Args:
        self: Celery任务实例
        video_path: 视频文件路径
        video_hash: 视频hash（可选，自动计算）
        output_format: 输出格式（webp, jpg, png）
        width: 缩略图宽度
        height: 缩略图高度（可选，按比例计算）
        quality: 质量（1-100）
        timestamp: 截取时间点（秒）

    Returns:
        缩略图信息字典
    """
    # 初始化资源限制器
    limits = ResourceLimit(
        max_memory_mb=RESOURCE_LIMITS['max_memory_mb'],
        max_cpu_percent=RESOURCE_LIMITS['max_cpu_percent'],
        check_interval=RESOURCE_LIMITS['check_interval']
    )
    limiter = ResourceLimiter(limits)

    try:
        limiter.start()
        logger.info(f"[任务 {self.request.id}] 开始生成缩略图: {video_path}")

        # 等待资源释放
        limiter.wait_if_paused()

        # 验证视频文件
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 计算视频hash
        if not video_hash:
            video_hash = _calculate_video_hash(video_path)
            logger.info(f"[任务 {self.request.id}] 视频hash: {video_hash}")

        # 检查缩略图是否已存在
        thumbnail_path = _get_thumbnail_path(video_hash, output_format)
        if os.path.exists(thumbnail_path):
            logger.info(f"[任务 {self.request.id}] 缩略图已存在: {thumbnail_path}")
            return {
                'success': True,
                'video_hash': video_hash,
                'thumbnail_path': thumbnail_path,
                'message': '缩略图已存在',
                'file_size': os.path.getsize(thumbnail_path)
            }

        # 等待资源释放
        limiter.wait_if_paused()

        # 提取帧并生成缩略图
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频: {video_path}")

        try:
            # 跳转到指定时间点
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)

            # 读取帧
            ret, frame = cap.read()
            if not ret:
                raise RuntimeError("无法读取视频帧")

            # 等待资源释放
            limiter.wait_if_paused()

            # 调整大小
            if height is None:
                # 按比例计算高度
                h, w = frame.shape[:2]
                ratio = width / w
                height = int(h * ratio)

            resized_frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LANCZOS4)

            # 确保输出目录存在
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

            # 根据格式保存缩略图
            if output_format.lower() == 'webp':
                params = [cv2.IMWRITE_WEBP_QUALITY, quality]
            elif output_format.lower() in ['jpg', 'jpeg']:
                params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            elif output_format.lower() == 'png':
                params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            else:
                params = []

            # 保存缩略图
            cv2.imwrite(thumbnail_path, resized_frame, params)

            # 获取文件大小
            file_size = os.path.getsize(thumbnail_path)

            logger.info(
                f"[任务 {self.request.id}] 缩略图生成成功: {thumbnail_path}, "
                f"大小={file_size}字节"
            )

            return {
                'success': True,
                'video_hash': video_hash,
                'thumbnail_path': thumbnail_path,
                'width': width,
                'height': height,
                'format': output_format,
                'file_size': file_size,
                'quality': quality
            }

        finally:
            cap.release()

    except Exception as e:
        logger.error(f"[任务 {self.request.id}] 缩略图生成失败: {e}", exc_info=True)
        # 重试任务
        raise self.retry(exc=e, countdown=60)

    finally:
        limiter.stop()


@shared_task(
    name='tasks.batch_generate_thumbnails',
    bind=True,
)
def batch_generate_thumbnails(
    self,
    video_paths: List[str],
    output_format: str = 'webp',
    width: int = 320,
    height: int = None,
    quality: int = 85,
    concurrent: int = 3
):
    """
    批量生成缩略图

    Args:
        self: Celery任务实例
        video_paths: 视频文件路径列表
        output_format: 输出格式
        width: 缩略图宽度
        height: 缩略图高度
        quality: 质量
        concurrent: 并发数

    Returns:
        批量生成结果
    """
    logger.info(f"[任务 {self.request.id}] 开始批量生成缩略图，共{len(video_paths)}个视频")

    # 创建任务组
    tasks = []
    for video_path in video_paths:
        task = generate_thumbnail.s(
            video_path=video_path,
            output_format=output_format,
            width=width,
            height=height,
            quality=quality
        )
        tasks.append(task)

    # 并发执行任务
    job = group(tasks)
    result = job.apply_async()

    # 等待所有任务完成
    results = result.get(timeout=3600)  # 1小时超时

    success_count = sum(1 for r in results if r.get('success'))
    failed_count = len(results) - success_count

    logger.info(
        f"[任务 {self.request.id}] 批量生成完成: "
        f"成功={success_count}, 失败={failed_count}"
    )

    return {
        'total': len(video_paths),
        'success': success_count,
        'failed': failed_count,
        'results': results
    }


@shared_task(
    name='tasks.regenerate_thumbnail',
    bind=True,
)
def regenerate_thumbnail(
    self,
    video_path: str,
    video_hash: str = None,
    delete_existing: bool = True,
    **kwargs
):
    """
    重新生成缩略图

    Args:
        self: Celery任务实例
        video_path: 视频文件路径
        video_hash: 视频hash
        delete_existing: 是否删除已存在的缩略图
        **kwargs: 传递给generate_thumbnail的参数

    Returns:
        生成结果
    """
    logger.info(f"[任务 {self.request.id}] 重新生成缩略图: {video_path}")

    # 计算视频hash
    if not video_hash:
        video_hash = _calculate_video_hash(video_path)

    # 删除已存在的缩略图
    if delete_existing:
        thumbnail_path = _get_thumbnail_path(video_hash, kwargs.get('output_format', 'webp'))
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            logger.info(f"[任务 {self.request.id}] 已删除旧缩略图: {thumbnail_path}")

    # 生成新缩略图
    result = generate_thumbnail(
        video_path=video_path,
        video_hash=video_hash,
        **kwargs
    )

    return result


@shared_task(
    name='tasks.check_thumbnail_status',
    bind=True,
)
def check_thumbnail_status(self, video_hash: str, output_format: str = 'webp'):
    """
    检查缩略图状态

    Args:
        self: Celery任务实例
        video_hash: 视频hash
        output_format: 输出格式

    Returns:
        状态信息
    """
    thumbnail_path = _get_thumbnail_path(video_hash, output_format)

    if os.path.exists(thumbnail_path):
        return {
            'exists': True,
            'path': thumbnail_path,
            'size': os.path.getsize(thumbnail_path),
            'modified': datetime.fromtimestamp(os.path.getmtime(thumbnail_path)).isoformat()
        }
    else:
        return {
            'exists': False,
            'path': thumbnail_path
        }


@shared_task(
    name='tasks.cleanup_old_thumbnails',
    bind=True,
)
def cleanup_old_thumbnails(self, days: int = 30):
    """
    清理旧缩略图

    Args:
        self: Celery任务实例
        days: 清理多少天前的缩略图

    Returns:
        清理结果
    """
    logger.info(f"[任务 {self.request.id}] 清理{days}天前的缩略图")

    now = datetime.now()
    deleted_count = 0
    deleted_size = 0

    for root, dirs, files in os.walk(THUMBNAIL_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            age_days = (now - file_time).days

            if age_days > days:
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_size += size
                    logger.info(f"删除缩略图: {file_path}")
                except Exception as e:
                    logger.error(f"删除缩略图失败: {file_path}, 错误: {e}")

    logger.info(
        f"[任务 {self.request.id}] 清理完成: "
        f"删除{deleted_count}个文件，释放{deleted_size / 1024 / 1024:.2f}MB"
    )

    return {
        'deleted_count': deleted_count,
        'deleted_size_mb': deleted_size / 1024 / 1024,
        'days': days
    }


# ========== 辅助函数 ==========

def _calculate_video_hash(video_path: str) -> str:
    """计算视频文件hash"""
    # 使用文件大小和修改时间快速生成hash
    stat = os.stat(video_path)
    hash_str = f"{os.path.basename(video_path)}-{stat.st_size}-{stat.st_mtime}"
    return hashlib.md5(hash_str.encode()).hexdigest()


def _get_thumbnail_path(video_hash: str, output_format: str) -> str:
    """获取缩略图路径"""
    # 使用hash的前两位创建子目录，避免单个目录文件过多
    subdir = video_hash[:2]
    filename = f"{video_hash}.{output_format}"
    return os.path.join(THUMBNAIL_DIR, subdir, filename)


if __name__ == '__main__':
    # 测试代码
    from celery_config import app

    # 启动Celery worker
    app.worker_main(['worker', '--loglevel=info', '--concurrency=2'])
