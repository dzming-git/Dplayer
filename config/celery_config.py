#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Celery配置文件
用于异步缩略图生成任务
"""

import os
from celery import Celery
from config_manager import get_config

# 获取配置
config = get_config()

# Celery应用配置
app = Celery('dplayer')

# 配置Celery
app.conf.update(
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,

    # 任务结果后端
    result_backend='db+sqlite:///celery_results.db',

    # 消息代理（使用Redis）
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'db+sqlite:///celery_results.db'),

    # 任务路由
    task_routes={
        'tasks.generate_thumbnail': {'queue': 'thumbnails'},
        'tasks.batch_generate_thumbnails': {'queue': 'thumbnails'},
    },

    # 任务限制
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # 重试配置
    task_default_retry_delay=60,
    task_max_retries=3,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软限制

    # 并发配置
    worker_concurrency=int(os.getenv('CELERY_WORKER_CONCURRENCY', '2')),

    # 资源限制
    worker_max_tasks_per_child=50,  # 每个worker处理50个任务后重启
    worker_disable_rate_limits=False,

    # 日志
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

# 自动发现任务
app.autodiscover_tasks(['tasks'])

# 资源限制配置
RESOURCE_LIMITS = {
    'max_memory_mb': int(os.getenv('MAX_MEMORY_MB', '512')),  # 最大内存512MB
    'max_cpu_percent': float(os.getenv('MAX_CPU_PERCENT', '80.0')),  # 最大CPU使用率80%
    'check_interval': int(os.getenv('RESOURCE_CHECK_INTERVAL', '5')),  # 资源检查间隔5秒
}

# 任务队列配置
QUEUE_CONFIG = {
    'thumbnails': {
        'max_concurrent': int(os.getenv('THUMBNAIL_MAX_CONCURRENT', '3')),
        'priority': 10,
    },
    'high_priority': {
        'max_concurrent': int(os.getenv('HIGH_PRIORITY_MAX_CONCURRENT', '1')),
        'priority': 20,
    },
}

if __name__ == '__main__':
    app.start()
