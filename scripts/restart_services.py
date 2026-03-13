#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重启 DPlayer 服务的脚本"""
import sys
import subprocess
import time

def get_service_pid(service_name):
    """获取服务的进程ID"""
    try:
        result = subprocess.run(['sc', 'queryex', service_name], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'PID' in line:
                pid = line.split(':')[1].strip()
                return int(pid)
    except Exception as e:
        print(f"获取 {service_name} PID 时出错: {e}")
    return None

def restart_service(service_name):
    """重启指定的 Windows 服务"""
    print(f"\n{'='*60}")
    print(f"正在重启服务: {service_name}")
    print(f"{'='*60}")
    
    # 获取重启前的PID
    old_pid = get_service_pid(service_name)
    print(f"重启前 PID: {old_pid}")
    
    # 停止服务
    print("正在停止服务...")
    try:
        result = subprocess.run(['sc', 'stop', service_name], capture_output=True, text=True, check=False)
        print(f"停止结果: {result.stdout.strip()}")
        if result.returncode != 0:
            print(f"停止失败，错误代码: {result.returncode}")
            print(f"错误详情: {result.stderr.strip()}")
            return
    except Exception as e:
        print(f"停止 {service_name} 时出错: {e}")
        return
    
    # 等待服务停止
    print("等待服务停止...")
    for i in range(10):
        time.sleep(1)
        current_pid = get_service_pid(service_name)
        if current_pid is None or current_pid != old_pid:
            print(f"服务已停止（第 {i+1} 秒）")
            break
    
    # 启动服务
    print("正在启动服务...")
    try:
        result = subprocess.run(['sc', 'start', service_name], capture_output=True, text=True, check=False)
        print(f"启动结果: {result.stdout.strip()}")
        if result.returncode != 0:
            print(f"启动失败，错误代码: {result.returncode}")
            print(f"错误详情: {result.stderr.strip()}")
            return
    except Exception as e:
        print(f"启动 {service_name} 时出错: {e}")
        return
    
    # 等待服务启动
    time.sleep(3)
    
    # 获取重启后的PID
    new_pid = get_service_pid(service_name)
    print(f"重启后 PID: {new_pid}")
    
    # 验证PID是否变化
    if old_pid is not None and new_pid is not None:
        if old_pid != new_pid:
            print(f"[OK] PID 已变更 ({old_pid} -> {new_pid})，服务重启成功！")
        else:
            print(f"[WARNING] PID 未变化 ({old_pid} = {new_pid})，可能服务未正确重启")
    else:
        print("[WARNING] 无法验证PID变化")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python restart_services.py [admin|main|thumbnail|all]")
        sys.exit(1)
    
    service = sys.argv[1].lower()
    
    if service == 'admin':
        restart_service('DPlayer-Admin')
    elif service == 'main':
        restart_service('DPlayer-Main')
    elif service == 'thumbnail':
        restart_service('DPlayer-Thumbnail')
    elif service == 'all':
        restart_service('DPlayer-Admin')
        restart_service('DPlayer-Main')
        restart_service('DPlayer-Thumbnail')
    else:
        print(f"未知的服务类型: {service}")
        sys.exit(1)
