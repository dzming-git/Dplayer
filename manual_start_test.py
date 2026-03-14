import subprocess
import sys
import os
import time

# 测试启动app.py，完全模拟admin_app.py的方式
BASEDIR = r'C:\Users\71555\WorkBuddy\Dplayer'
LOG_DIR = os.path.join(BASEDIR, 'logs')
script = os.path.join(BASEDIR, 'app.py')

# 打开日志文件
stdout_file = open(os.path.join(LOG_DIR, 'test_stdout.log'), 'w', encoding='utf-8')
stderr_file = open(os.path.join(LOG_DIR, 'test_stderr.log'), 'w', encoding='utf-8')

print(f"启动命令: {[sys.executable, script]}")
print(f"工作目录: {BASEDIR}")

proc = subprocess.Popen(
    [sys.executable, script],
    cwd=BASEDIR,
    stdout=stdout_file,
    stderr=stderr_file,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
)

print(f"进程已启动, PID: {proc.pid}")

# 立即关闭文件句柄
stdout_file.close()
stderr_file.close()

# 等待3秒检查进程状态
time.sleep(3)

import psutil
if psutil.pid_exists(proc.pid):
    print(f"进程仍在运行")
    proc.terminate()
else:
    print(f"进程已退出")
    # 读取错误日志
    try:
        with open(os.path.join(LOG_DIR, 'test_stderr.log'), 'r', encoding='utf-8') as f:
            error_content = f.read()
        if error_content:
            print(f"错误日志:\n{error_content}")
        else:
            print("错误日志为空")
    except Exception as e:
        print(f"读取错误日志失败: {e}")
