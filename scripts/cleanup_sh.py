import os

# scripts目录下的.sh文件
script_files = [
    'setup_docker.sh',
    'setup_firewall.sh',
    'service/install_linux_services.sh'
]

# 删除scripts目录的文件
for file in script_files:
    file_path = f'c:/Users/71555/WorkBuddy/Dplayer/scripts/{file}'
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f'Deleted: scripts/{file}')
    else:
        print(f'Not found: scripts/{file}')

# 尝试删除service目录
service_dir = 'c:/Users/71555/WorkBuddy/Dplayer/scripts/service'
if os.path.exists(service_dir):
    try:
        os.rmdir(service_dir)
        print(f'Deleted directory: scripts/service')
    except OSError as e:
        print(f'Cannot remove directory scripts/service: {e}')

print('\nAll .sh files deleted successfully!')
