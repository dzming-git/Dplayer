import subprocess
import time
import os
import sys

def run_command(cmd, description):
    """执行命令并打印结果"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"异常: {e}")
        return False

def main():
    print("=" * 80)
    print("清理并重新启动服务")
    print("=" * 80)
    
    # 1. 停止所有Python进程
    print("\n1. 停止所有Python进程...")
    run_command("wmic process where \"name='python.exe'\" delete", "停止Python进程")
    time.sleep(3)
    
    # 2. 删除临时文件
    print("\n2. 删除临时文件...")
    temp_files = ['main_app.pid', 'test_results.txt']
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  已删除: {file}")
            except:
                print(f"  无法删除: {file}")
    
    # 3. 切换到项目目录
    project_dir = r'c:\Users\71555\WorkBuddy\Dplayer'
    os.chdir(project_dir)
    print(f"\n3. 当前目录: {os.getcwd()}")
    
    # 4. 启动主应用
    print("\n4. 启动主应用...")
    try:
        # 使用CREATE_NO_WINDOW避免弹出窗口
        subprocess.Popen(
            ['python', 'app.py'],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("  主应用启动命令已发送")
    except Exception as e:
        print(f"  启动失败: {e}")
        return 1
    
    time.sleep(3)
    
    # 5. 启动管理后台
    print("\n5. 启动管理后台...")
    try:
        subprocess.Popen(
            ['python', 'admin_app.py'],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("  管理后台启动命令已发送")
    except Exception as e:
        print(f"  启动失败: {e}")
        return 1
    
    time.sleep(3)
    
    # 6. 检查进程
    print("\n6. 检查进程状态...")
    result = run_command("tasklist | findstr python", "检查Python进程")
    
    # 7. 检查端口
    print("\n7. 检查端口状态...")
    run_command("netstat -ano | findstr :80", "检查80端口")
    run_command("netstat -ano | findstr :8080", "检查8080端口")
    
    print("\n" + "=" * 80)
    print("启动完成!")
    print("主应用: http://127.0.0.1:80")
    print("管理后台: http://127.0.0.1:8080")
    print("=" * 80)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
