#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dplayer 挂载配置工具脚本
用于生成和管理挂载配置文件
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mount_config import MountConfig


def create_default_config(output_path: str = "mounts_config.json"):
    """
    创建默认的挂载配置文件
    
    Args:
        output_path: 输出文件路径
    """
    print(f"创建默认挂载配置: {output_path}")
    
    config = MountConfig()
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存配置
    config.save(output_path)
    
    print(f"✓ 配置文件已创建: {output_path}")
    print("\n默认挂载配置:")
    config.print_mounts()


def create_instance_config(instance_name: str, output_dir: str = "."):
    """
    创建实例特定的挂载配置文件
    
    Args:
        instance_name: 实例名称
        output_dir: 输出目录
    """
    config_file = os.path.join(output_dir, f"mounts_config_{instance_name}.json")
    print(f"创建实例挂载配置: {config_file}")
    
    config = MountConfig()
    
    # 为每个实例创建独立的内容目录
    default_mounts = config.get_default_mounts()
    
    # 更新源路径以使用实例特定的目录
    for name, mount in default_mounts.items():
        # 将 /content 改为 /content/instance-name
        if mount['source'].startswith('/content/'):
            mount['source'] = f"/content/{instance_name}/{mount['source'].replace('/content/', '')}"
        elif mount['source'] == '/content':
            mount['source'] = f"/content/{instance_name}"
    
    config.mounts = default_mounts
    config.save(config_file)
    
    print(f"✓ 实例配置文件已创建: {config_file}")
    print(f"\n实例 [{instance_name}] 挂载配置:")
    config.print_mounts()


def create_multi_instance_config(num_instances: int, output_dir: str = "."):
    """
    创建多个实例的挂载配置文件
    
    Args:
        num_instances: 实例数量
        output_dir: 输出目录
    """
    print(f"创建 {num_instances} 个实例的挂载配置...")
    
    for i in range(1, num_instances + 1):
        instance_name = f"instance-{i}"
        create_instance_config(instance_name, output_dir)
    
    print(f"\n✓ 已创建 {num_instances} 个实例的配置文件")


def create_docker_compose_from_mounts(mount_config_path: str, output_path: str = "docker-compose.generated.yml"):
    """
    从挂载配置生成docker-compose文件
    
    Args:
        mount_config_path: 挂载配置文件路径
        output_path: 输出的docker-compose文件路径
    """
    print(f"从挂载配置生成docker-compose文件...")
    print(f"挂载配置: {mount_config_path}")
    print(f"输出文件: {output_path}")
    
    # 加载挂载配置
    config = MountConfig(mount_config_path)
    
    # 生成卷配置
    volumes = config.generate_docker_compose_volumes()
    
    # 生成docker-compose内容
    compose_content = f'''version: '3.8'

services:
  dplayer:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: dplayer-generated
    restart: unless-stopped
    ports:
      - "8080:80"
    environment:
      - DPLAYER_HOST=0.0.0.0
      - DPLAYER_PORT=80
      - DPLAYER_DEBUG=False
      - DPLAYER_MOUNT_CONFIG=/config/mounts.json
    volumes:
      # 从挂载配置自动生成
'''
    
    for vol in volumes:
        compose_content += f'      - {vol}\n'
    
    compose_content += '''    networks:
      - dplayer-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:80/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

networks:
  dplayer-network:
    driver: bridge
'''
    
    # 保存文件
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(compose_content)
    
    print(f"✓ docker-compose文件已生成: {output_path}")


def create_directory_structure(base_dir: str, instance_name: str = None):
    """
    创建推荐的项目目录结构
    
    Args:
        base_dir: 基础目录
        instance_name: 实例名称（可选）
    """
    print(f"创建项目目录结构...")
    print(f"基础目录: {base_dir}")
    if instance_name:
        print(f"实例名称: {instance_name}")
    
    # 创建基础目录结构
    dirs = [
        os.path.join(base_dir, "data", "config"),
        os.path.join(base_dir, "content"),
        os.path.join(base_dir, "logs"),
        os.path.join(base_dir, "videos")
    ]
    
    if instance_name:
        # 为特定实例创建目录
        dirs.extend([
            os.path.join(base_dir, "data", "config", instance_name),
            os.path.join(base_dir, "content", instance_name, "videos"),
            os.path.join(base_dir, "content", instance_name, "thumbnails"),
            os.path.join(base_dir, "content", instance_name, "uploads"),
            os.path.join(base_dir, "content", instance_name, "static"),
            os.path.join(base_dir, "content", instance_name, "cache"),
            os.path.join(base_dir, "logs", instance_name)
        ])
    else:
        # 单实例目录结构
        dirs.extend([
            os.path.join(base_dir, "content", "videos"),
            os.path.join(base_dir, "content", "thumbnails"),
            os.path.join(base_dir, "content", "uploads"),
            os.path.join(base_dir, "content", "static"),
            os.path.join(base_dir, "content", "cache")
        ])
    
    # 创建所有目录
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"  ✓ {d}")
    
    print(f"\n✓ 目录结构创建完成")


def print_mount_summary(mount_config_path: str):
    """
    打印挂载配置摘要
    
    Args:
        mount_config_path: 挂载配置文件路径
    """
    print(f"挂载配置摘要: {mount_config_path}")
    print("=" * 60)
    
    config = MountConfig(mount_config_path)
    
    # 打印挂载配置
    config.print_mounts()
    
    # 打印Docker Compose格式
    print("Docker Compose 卷配置:")
    print("-" * 60)
    volumes = config.generate_docker_compose_volumes()
    for vol in volumes:
        print(f"  - {vol}")
    
    # 打印docker run格式
    print("\ndocker run 命令参数:")
    print("-" * 60)
    args = config.generate_docker_run_args()
    print(" ".join(args))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Dplayer 挂载配置工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建默认配置
    subparsers.add_parser('create-default', help='创建默认挂载配置')
    
    # 创建实例配置
    parser_instance = subparsers.add_parser('create-instance', help='创建实例特定配置')
    parser_instance.add_argument('instance_name', help='实例名称')
    parser_instance.add_argument('-o', '--output-dir', default='.', help='输出目录')
    
    # 创建多实例配置
    parser_multi = subparsers.add_parser('create-multi', help='创建多个实例配置')
    parser_multi.add_argument('num', type=int, help='实例数量')
    parser_multi.add_argument('-o', '--output-dir', default='.', help='输出目录')
    
    # 从挂载配置生成docker-compose
    parser_compose = subparsers.add_parser('generate-compose', help='生成docker-compose文件')
    parser_compose.add_argument('mount_config', help='挂载配置文件路径')
    parser_compose.add_argument('-o', '--output', default='docker-compose.generated.yml', help='输出文件路径')
    
    # 创建目录结构
    parser_dirs = subparsers.add_parser('create-dirs', help='创建项目目录结构')
    parser_dirs.add_argument('base_dir', help='基础目录')
    parser_dirs.add_argument('-i', '--instance', help='实例名称（可选）')
    
    # 打印配置摘要
    parser_summary = subparsers.add_parser('summary', help='打印挂载配置摘要')
    parser_summary.add_argument('mount_config', help='挂载配置文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'create-default':
        create_default_config()
    
    elif args.command == 'create-instance':
        create_instance_config(args.instance_name, args.output_dir)
    
    elif args.command == 'create-multi':
        create_multi_instance_config(args.num, args.output_dir)
    
    elif args.command == 'generate-compose':
        create_docker_compose_from_mounts(args.mount_config, args.output)
    
    elif args.command == 'create-dirs':
        create_directory_structure(args.base_dir, args.instance)
    
    elif args.command == 'summary':
        print_mount_summary(args.mount_config)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
