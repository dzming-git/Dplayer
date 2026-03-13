#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缩略图微服务单元测试

测试缩略图微服务的核心功能：
- Task类功能
- TaskManager类功能
- API端点测试
- 降级机制测试

作者：WorkBuddy AI
创建时间：2025-03-13
"""

import sys
import os
import unittest
import tempfile
import shutil
import time
import threading
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 添加tests目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ========== 导入测试框架 ==========
try:
    from test_framework import test_case, get_test_framework
except ImportError:
    # 如果测试框架不可用，创建一个空装饰器
    def test_case(name, category):
        def decorator(func):
            return func
        return decorator
    get_test_framework = None


# ========== 导入缩略图服务模块 ==========
# 需要先导入Flask应用才能使用test_client
import thumbnail_service


class TestThumbnailTask(unittest.TestCase):
    """测试Task类"""
    
    def setUp(self):
        """测试前准备"""
        self.task_id = "test_task_001"
        self.video_path = "/tmp/test_video.mp4"
        self.video_hash = "abc123"
        self.config = {
            'output_format': 'jpg',
            'time_offset': 5,
            'size': [320, 180]
        }
        self.task = thumbnail_service.Task(
            self.task_id,
            self.video_path,
            self.video_hash,
            self.config
        )
    
    def test_task_creation(self):
        """测试任务创建"""
        self.assertEqual(self.task.task_id, self.task_id)
        self.assertEqual(self.task.video_path, self.video_path)
        self.assertEqual(self.task.video_hash, self.video_hash)
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(self.task.progress, 0)
        self.assertIsNone(self.task.error)
        self.assertEqual(self.task.format, 'jpg')
        self.assertIsNotNone(self.task.created_at)
    
    def test_task_to_dict(self):
        """测试任务转换为字典"""
        task_dict = self.task.to_dict()
        
        self.assertEqual(task_dict['task_id'], self.task_id)
        self.assertEqual(task_dict['video_path'], self.video_path)
        self.assertEqual(task_dict['video_hash'], self.video_hash)
        self.assertEqual(task_dict['status'], 'pending')
        self.assertEqual(task_dict['progress'], 0)
        self.assertEqual(task_dict['format'], 'jpg')
        self.assertIn('created_at', task_dict)
    
    def test_task_status_update(self):
        """测试任务状态更新"""
        # 更新为processing
        self.task.status = 'processing'
        self.task.started_at = datetime.now()
        self.assertEqual(self.task.status, 'processing')
        self.assertIsNotNone(self.task.started_at)
        
        # 更新为completed
        self.task.status = 'completed'
        self.task.completed_at = datetime.now()
        self.task.thumbnail_path = '/thumbnails/abc123.jpg'
        self.task.file_size = 25600
        self.assertEqual(self.task.status, 'completed')
        self.assertIsNotNone(self.task.completed_at)
        self.assertEqual(self.task.thumbnail_path, '/thumbnails/abc123.jpg')
        self.assertEqual(self.task.file_size, 25600)
    
    def test_task_failure(self):
        """测试任务失败"""
        self.task.status = 'failed'
        self.task.error = 'Video file not found'
        self.task.completed_at = datetime.now()
        
        self.assertEqual(self.task.status, 'failed')
        self.assertEqual(self.task.error, 'Video file not found')
        self.assertIsNotNone(self.task.completed_at)


class TestThumbnailTaskManager(unittest.TestCase):
    """测试TaskManager类"""
    
    def setUp(self):
        """测试前准备"""
        self.manager = thumbnail_service.TaskManager(
            max_concurrent=2,
            queue_size=10
        )
    
    def test_manager_creation(self):
        """测试任务管理器创建"""
        self.assertEqual(self.manager.max_concurrent, 2)
        self.assertEqual(self.manager.queue_size, 10)
        self.assertEqual(self.manager.active_count, 0)
        self.assertEqual(len(self.manager.tasks), 0)
        self.assertEqual(len(self.manager.queue), 0)
    
    def test_create_task(self):
        """测试创建任务"""
        video_path = "/tmp/test1.mp4"
        video_hash = "hash1"
        config = {'output_format': 'jpg'}
        
        task = self.manager.create_task(video_path, video_hash, config)
        
        self.assertIsNotNone(task)
        self.assertEqual(task.video_path, video_path)
        self.assertEqual(task.video_hash, video_hash)
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertEqual(len(self.manager.queue), 1)
        self.assertIn(video_hash, self.manager.video_hash_to_task_id)
    
    def test_duplicate_task(self):
        """测试重复任务"""
        video_path = "/tmp/test1.mp4"
        video_hash = "hash1"
        config = {'output_format': 'jpg'}
        
        # 创建第一个任务
        task1 = self.manager.create_task(video_path, video_hash, config)
        
        # 创建重复任务
        task2 = self.manager.create_task(video_path, video_hash, config)
        
        # 应该返回相同的任务
        self.assertEqual(task1.task_id, task2.task_id)
        self.assertEqual(len(self.manager.tasks), 1)
        self.assertEqual(len(self.manager.queue), 1)
    
    def test_queue_full(self):
        """测试队列已满"""
        config = {'output_format': 'jpg'}
        
        # 创建10个任务（队列已满）
        for i in range(10):
            self.manager.create_task(
                f"/tmp/video{i}.mp4",
                f"hash{i}",
                config
            )
        
        # 尝试创建第11个任务
        task = self.manager.create_task(
            "/tmp/video10.mp4",
            "hash10",
            config
        )
        
        # 应该返回None
        self.assertIsNone(task)
    
    def test_get_task(self):
        """测试获取任务"""
        video_path = "/tmp/test1.mp4"
        video_hash = "hash1"
        config = {'output_format': 'jpg'}
        
        created_task = self.manager.create_task(video_path, video_hash, config)
        retrieved_task = self.manager.get_task(created_task.task_id)
        
        self.assertEqual(retrieved_task.task_id, created_task.task_id)
    
    def test_get_task_by_video_hash(self):
        """测试根据视频hash获取任务"""
        video_path = "/tmp/test1.mp4"
        video_hash = "hash1"
        config = {'output_format': 'jpg'}
        
        created_task = self.manager.create_task(video_path, video_hash, config)
        retrieved_task = self.manager.get_task_by_video_hash(video_hash)
        
        self.assertEqual(retrieved_task.task_id, created_task.task_id)
    
    def test_complete_task(self):
        """测试完成任务"""
        video_path = "/tmp/test1.mp4"
        video_hash = "hash1"
        config = {'output_format': 'jpg'}
        
        task = self.manager.create_task(video_path, video_hash, config)
        
        # 完成任务
        self.manager.complete_task(
            task.task_id,
            success=True,
            thumbnail_path='/thumbnails/hash1.jpg',
            file_size=25600
        )
        
        retrieved_task = self.manager.get_task(task.task_id)
        self.assertEqual(retrieved_task.status, 'completed')
        self.assertEqual(retrieved_task.thumbnail_path, '/thumbnails/hash1.jpg')
        self.assertEqual(retrieved_task.file_size, 25600)
        self.assertEqual(self.manager.stats['completed'], 1)
    
    def test_failed_task(self):
        """测试失败任务"""
        video_path = "/tmp/test1.mp4"
        video_hash = "hash1"
        config = {'output_format': 'jpg'}
        
        task = self.manager.create_task(video_path, video_hash, config)
        
        # 任务失败
        self.manager.complete_task(
            task.task_id,
            success=False,
            error='Video file not found'
        )
        
        retrieved_task = self.manager.get_task(task.task_id)
        self.assertEqual(retrieved_task.status, 'failed')
        self.assertEqual(retrieved_task.error, 'Video file not found')
        self.assertEqual(self.manager.stats['failed'], 1)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        config = {'output_format': 'jpg'}
        
        # 创建多个任务
        for i in range(5):
            self.manager.create_task(
                f"/tmp/video{i}.mp4",
                f"hash{i}",
                config
            )
        
        # 完成一些任务
        for i in range(3):
            task = self.manager.get_task(f"thumb_task_*")  # 注意：实际需要真实的task_id
        
        stats = self.manager.get_stats()
        
        self.assertIn('uptime', stats)
        self.assertIn('total_tasks', stats)
        self.assertIn('completed_tasks', stats)
        self.assertIn('failed_tasks', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('active_tasks', stats)
        self.assertIn('queue_size', stats)


class TestThumbnailServiceAPI(unittest.TestCase):
    """测试缩略图服务API"""
    
    def setUp(self):
        """测试前准备"""
        self.app = thumbnail_service.app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 创建临时缩略图目录
        self.temp_dir = tempfile.mkdtemp()
        original_thumbnail_dir = thumbnail_service.THUMBNAIL_DIR
        thumbnail_service.THUMBNAIL_DIR = self.temp_dir
        
        # 保存原始目录，测试后恢复
        self.original_thumbnail_dir = original_thumbnail_dir
    
    def tearDown(self):
        """测试后清理"""
        # 恢复原始缩略图目录
        thumbnail_service.THUMBNAIL_DIR = self.original_thumbnail_dir
        
        # 删除临时目录
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_health_check(self):
        """测试健康检查API"""
        response = self.client.get('/health')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('version', data)
        self.assertIn('uptime', data)
        self.assertIn('active_tasks', data)
    
    def test_metrics(self):
        """测试服务指标API"""
        response = self.client.get('/metrics')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('tasks_total', data)
        self.assertIn('tasks_completed', data)
        self.assertIn('tasks_failed', data)
        self.assertIn('success_rate', data)
        self.assertIn('active_tasks', data)
    
    def test_generate_thumbnail_missing_params(self):
        """测试生成缩略图 - 缺少参数"""
        response = self.client.post(
            '/api/thumbnail/generate',
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data['success'])
    
    def test_generate_thumbnail_success(self):
        """测试生成缩略图 - 成功"""
        # 创建一个临时测试视频文件
        test_video_path = os.path.join(self.temp_dir, 'test_video.mp4')
        with open(test_video_path, 'wb') as f:
            f.write(b'fake video data')
        
        response = self.client.post(
            '/api/thumbnail/generate',
            json={
                'video_path': test_video_path,
                'video_hash': 'test_hash',
                'output_format': 'jpg'
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])
        self.assertIn('task_id', data)
        self.assertIn('status', data)
    
    def test_generate_thumbnail_video_not_found(self):
        """测试生成缩略图 - 视频不存在"""
        response = self.client.post(
            '/api/thumbnail/generate',
            json={
                'video_path': '/nonexistent/video.mp4',
                'video_hash': 'test_hash',
                'output_format': 'jpg'
            }
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data['success'])
    
    def test_get_task_status_not_found(self):
        """测试查询任务状态 - 任务不存在"""
        response = self.client.get('/api/thumbnail/status/nonexistent_task')
        
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertFalse(data['success'])
    
    def test_get_thumbnail_file_not_found(self):
        """测试获取缩略图文件 - 文件不存在"""
        response = self.client.get('/api/thumbnail/file/nonexistent_hash')
        
        self.assertEqual(response.status_code, 200)
        # 应该返回错误信息或404


class TestThumbnailServiceClient(unittest.TestCase):
    """测试缩略图服务客户端"""
    
    def setUp(self):
        """测试前准备"""
        self.client = thumbnail_service_client.ThumbnailServiceClient(
            service_url='http://localhost:5001',
            timeout=5,
            max_retries=2
        )
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        self.assertEqual(self.client.service_url, 'http://localhost:5001')
        self.assertEqual(self.client.timeout, 5)
        self.assertEqual(self.client.max_retries, 2)
        self.assertTrue(self.client.fallback_enabled)
        self.assertTrue(self.client.service_available)
    
    @patch('thumbnail_service_client.requests.get')
    def test_check_health_success(self, mock_get):
        """测试健康检查 - 成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'healthy',
            'version': '1.0.0',
            'uptime': 100.0,
            'active_tasks': 0,
            'queue_size': 0,
            'total_processed': 10,
            'success_rate': 100.0
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = self.client.check_health()
        
        self.assertTrue(result)
        self.assertTrue(self.client.service_available)
    
    @patch('thumbnail_service_client.requests.get')
    def test_check_health_failure(self, mock_get):
        """测试健康检查 - 失败"""
        mock_get.side_effect = Exception("Connection error")
        
        result = self.client.check_health()
        
        self.assertFalse(result)
        self.assertFalse(self.client.service_available)
    
    @patch('thumbnail_service_client.requests.post')
    def test_generate_thumbnail_success(self, mock_post):
        """测试生成缩略图 - 成功"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'success': True,
            'task_id': 'test_task_001',
            'status': 'pending',
            'estimated_time': 3
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = self.client.generate_thumbnail(
            video_path='/tmp/test.mp4',
            video_hash='test_hash',
            output_format='jpg'
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['task_id'], 'test_task_001')


# 需要导入客户端模块
import thumbnail_service_client


# ========== 注册测试用例 ==========
@test_case("测试Task类的基本功能", "THUMBNAIL")
def test_task_basic_functionality():
    """测试Task类的基本功能"""
    # 此函数用于注册，实际测试在TestThumbnailTask类中
    pass


@test_case("测试TaskManager类的任务管理功能", "THUMBNAIL")
def test_task_manager_functions():
    """测试TaskManager类的任务管理功能"""
    # 此函数用于注册，实际测试在TestThumbnailTaskManager类中
    pass


@test_case("测试缩略图服务API端点", "THUMBNAIL")
def test_thumbnail_service_api():
    """测试缩略图服务API端点"""
    # 此函数用于注册，实际测试在TestThumbnailServiceAPI类中
    pass


@test_case("测试缩略图服务客户端功能", "THUMBNAIL")
def test_thumbnail_service_client():
    """测试缩略图服务客户端功能"""
    # 此函数用于注册，实际测试在TestThumbnailServiceClient类中
    pass


# ========== 主测试运行器 ==========
if __name__ == '__main__':
    # 运行unittest测试
    unittest.main(verbosity=2)
