import os
import shutil

# 根目录的.bat文件
root_files = [
    'restart_admin.bat',
    'restart_all.bat'
]

# scripts目录下的.bat文件
script_files = [
    'clean_all_dplayer.bat',
    'diagnose_network.bat',
    'fix_network_issues.bat',
    'run_tests.bat',
    'setup_docker.bat',
    'setup_firewall.bat',
    'setup_restart_perms.bat',
    'start_all_services.bat',
    'stop_all_services.bat'
]

# 删除根目录的文件
for file in root_files:
    file_path = f'c:/Users/71555/WorkBuddy/Dplayer/{file}'
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f'Deleted: {file}')
    else:
        print(f'Not found: {file}')

# 删除scripts目录的文件
for file in script_files:
    file_path = f'c:/Users/71555/WorkBuddy/Dplayer/scripts/{file}'
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f'Deleted: scripts/{file}')
    else:
        print(f'Not found: scripts/{file}')

print('\nAll .bat files deleted successfully!')
