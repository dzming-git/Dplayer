import os
import sys
import subprocess
import time

print("=" * 60)
print("重启管理应用 - 强制加载最新代码")
print("=" * 60)

# 1. 停止所有Python进程
print("\n[1/4] 停止所有Python进程...")
os.system('taskkill /F /IM python.exe >nul 2>&1')
time.sleep(2)
print("    [OK] 进程已停止")

# 2. 清理Python缓存
print("\n[2/4] 清理Python缓存...")
import shutil
cache_dir = '__pycache__'
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)
    print("    [OK] __pycache__ 已删除")
else:
    print("    [INFO] __pycache__ 不存在")

# 3. 重新启动管理应用
print("\n[3/4] 启动管理应用...")
proc = subprocess.Popen(
    [sys.executable, 'admin_app.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
print(f"    [OK] 进程已启动, PID: {proc.pid}")

# 4. 验证端口配置
print("\n[4/4] 验证端口配置...")
time.sleep(3)

log_file = 'logs/admin_stdout.log'
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        # 查找启动信息
        for i, line in enumerate(lines):
            if 'Main app port:' in line:
                port = line.split(':')[-1].strip()
                if port == '8081':
                    print(f"    [OK] 主应用端口: {port}")
                else:
                    print(f"    [FAIL] 主应用端口: {port} (期望: 8081)")
                break

print("\n" + "=" * 60)
print("完成！请检查管理后台是否正常运行")
print("访问地址: http://localhost:8080")
print("=" * 60)
