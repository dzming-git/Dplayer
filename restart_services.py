import subprocess
import time
import os

def kill_python_processes():
    """停止所有Python进程"""
    print("正在停止所有Python进程...")
    
    try:
        # 使用wmic停止所有Python进程
        result = subprocess.run(
            ['wmic', 'process', 'where', "name='python.exe'", 'delete'],
            capture_output=True,
            text=True,
            timeout=30
        )
        print(f"wmic返回: {result.stdout}")
        
        # 等待进程完全停止
        time.sleep(2)
        
        print("Python进程已停止")
        return True
    except Exception as e:
        print(f"停止进程时出错: {e}")
        # 尝试使用taskkill
        try:
            result = subprocess.run(
                ['taskkill', '/F', '/IM', 'python.exe', '/T'],
                capture_output=True,
                text=True,
                timeout=30
            )
            print(f"taskkill返回: {result.stdout}")
            time.sleep(2)
            return True
        except Exception as e2:
            print(f"taskkill也失败了: {e2}")
            return False

def start_services():
    """启动主应用和管理后台"""
    print("\n正在启动服务...")
    
    # 切换到项目目录
    project_dir = r'c:\Users\71555\WorkBuddy\Dplayer'
    os.chdir(project_dir)
    
    # 启动主应用
    print("启动主应用 (端口 80)...")
    subprocess.Popen(
        ['python', 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)
    
    # 启动管理后台
    print("启动管理后台 (端口 8080)...")
    subprocess.Popen(
        ['python', 'admin_app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    time.sleep(2)
    
    print("\n服务启动完成!")
    print("- 主应用: http://127.0.0.1:80")
    print("- 管理后台: http://127.0.0.1:8080")

if __name__ == '__main__':
    kill_python_processes()
    start_services()
