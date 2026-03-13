# -*- coding: utf-8 -*-
"""
管理后台最终验证脚本
"""

import requests
import json
import time

ADMIN_URL = "http://127.0.0.1:8080"
MAIN_URL = "http://127.0.0.1:80"

print("=" * 80)
print("Dplayer 管理后台最终验证")
print("=" * 80)
print(f"管理后台: {ADMIN_URL}")
print(f"主应用: {MAIN_URL}")
print("=" * 80)
print()

results = []

def test(name, url, method='GET', data=None, check_keys=None):
    """测试API"""
    try:
        if method == 'GET':
            r = requests.get(url, timeout=10)
        elif method == 'POST':
            r = requests.post(url, json=data, timeout=10)
        elif method == 'PUT':
            r = requests.put(url, json=data, timeout=10)
        elif method == 'DELETE':
            r = requests.delete(url, timeout=10)
        else:
            return False, "不支持的HTTP方法"

        print(f"[{r.status_code}] {name}")

        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"

        # 解析JSON
        try:
            resp = r.json()
        except:
            return False, "无法解析JSON"

        # 检查必需字段
        if check_keys:
            for key in check_keys:
                if key not in resp:
                    return False, f"缺少字段: {key}"

        return True, resp.get('message', 'OK')

    except requests.exceptions.Timeout:
        print(f"[TIMEOUT] {name}")
        return False, "请求超时"
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] {name}")
        return False, f"连接错误: {str(e)[:50]}"
    except Exception as e:
        print(f"[ERROR] {name}")
        return False, str(e)[:50]

print("1. 应用控制功能")
print("-" * 80)

ok, msg = test("获取状态", f"{ADMIN_URL}/api/status", check_keys=['success', 'main_app'])
results.append(("获取状态", ok, msg))

ok, msg = test("启动主应用", f"{ADMIN_URL}/api/app/start", method='POST')
results.append(("启动主应用", ok, msg))

time.sleep(2)  # 等待启动

ok, msg = test("验证运行状态", f"{ADMIN_URL}/api/status", check_keys=['success'])
results.append(("验证运行状态", ok, msg))

print()
print("2. 系统监控功能")
print("-" * 80)

ok, msg = test("数据库统计", f"{ADMIN_URL}/api/db/stats", check_keys=['success'])
results.append(("数据库统计", ok, msg))

print()
print("3. 视频管理功能")
print("-" * 80)

ok, msg = test("获取视频列表", f"{ADMIN_URL}/api/videos", check_keys=['success'])
results.append(("获取视频列表", ok, msg))

ok, msg = test("获取标签列表", f"{ADMIN_URL}/api/tags", check_keys=['success'])
results.append(("获取标签列表", ok, msg))

print()
print("4. 日志管理功能")
print("-" * 80)

ok, msg = test("日志文件列表", f"{ADMIN_URL}/api/logs/list", check_keys=['success'])
results.append(("日志文件列表", ok, msg))

ok, msg = test("日志目录大小", f"{ADMIN_URL}/api/logs/size", check_keys=['success'])
results.append(("日志目录大小", ok, msg))

print()
print("5. 系统配置功能 (需要主应用运行)")
print("-" * 80)

ok, msg = test("获取配置", f"{ADMIN_URL}/api/config", check_keys=['success'])
results.append(("获取配置", ok, msg))

ok, msg = test("依赖检查", f"{ADMIN_URL}/api/dependencies/check", check_keys=['success'])
results.append(("依赖检查", ok, msg))

print()
print("6. 用户功能 (需要主应用运行)")
print("-" * 80)

ok, msg = test("收藏列表", f"{ADMIN_URL}/api/favorites", check_keys=['success'])
results.append(("收藏列表", ok, msg))

ok, msg = test("排行榜", f"{ADMIN_URL}/api/ranking", check_keys=['success'])
results.append(("排行榜", ok, msg))

print()
print("=" * 80)
print("测试总结")
print("=" * 80)

passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)

for name, ok, msg in results:
    status = "[PASS]" if ok else "[FAIL]"
    print(f"{status} {name:<20} - {msg}")

print()
print(f"总计: {len(results)} 个测试")
print(f"通过: {passed} 个")
print(f"失败: {failed} 个")
print(f"通过率: {(passed/len(results)*100):.1f}%")
print("=" * 80)

# 分类统计
app_control = sum(1 for name, ok, _ in results if ok and any(k in name for k in ['状态', '启动', '停止', '验证']))
sys_monitor = sum(1 for name, ok, _ in results if ok and any(k in name for k in ['数据库', '统计']))
video_mgr = sum(1 for name, ok, _ in results if ok and any(k in name for k in ['视频', '标签']))
log_mgr = sum(1 for name, ok, _ in results if ok and any(k in name for k in ['日志']))
sys_config = sum(1 for name, ok, _ in results if ok and any(k in name for k in ['配置', '依赖', '扫描']))
user_func = sum(1 for name, ok, _ in results if ok and any(k in name for k in ['收藏', '排行']))

print()
print("分类统计:")
print(f"  应用控制: {app_control}/3")
print(f"  系统监控: {sys_monitor}/1")
print(f"  视频管理: {video_mgr}/2")
print(f"  日志管理: {log_mgr}/2")
print(f"  系统配置: {sys_config}/2")
print(f"  用户功能: {user_func}/2")
print("=" * 80)
