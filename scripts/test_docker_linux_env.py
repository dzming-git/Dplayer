#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker Linux环境测试脚本
在本地Windows环境中模拟Docker Linux环境进行测试
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path

# Windows控制台编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import get_config
from mount_config import MountConfig


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_platform_detection():
    """测试平台检测功能"""
    print_section("1. 平台检测测试")

    config = get_config()

    print(f"当前平台: {platform.system()}")
    print(f"平台类型: {config.platform}")
    print(f"是否Windows: {config.is_platform_windows()}")
    print(f"是否Linux: {config.is_platform_linux()}")
    print(f"是否macOS: {config.is_platform_macos()}")
    print(f"是否Docker环境: {config.is_docker}")

    # 模拟Docker环境测试
    print("\n[模拟Docker环境]")
    original_env = os.environ.get('DPLAYER_IS_DOCKER')
    os.environ['DPLAYER_IS_DOCKER'] = 'true'

    # 重新加载配置
    import importlib
    import config_manager
    importlib.reload(config_manager)
    from config_manager import get_config as get_config_new
    config_docker = get_config_new()

    print(f"模拟Docker环境检测结果: {config_docker.is_docker}")

    # 恢复环境变量
    if original_env:
        os.environ['DPLAYER_IS_DOCKER'] = original_env
    else:
        os.environ.pop('DPLAYER_IS_DOCKER', None)

    print("✓ 平台检测测试完成")
    return True


def test_path_handling():
    """测试路径处理"""
    print_section("2. 路径处理测试")

    config = get_config()

    print(f"配置目录: {config.config_dir}")
    print(f"数据目录: {config.data_dir}")
    print(f"日志目录: {config.log_dir}")
    print(f"视频目录: {config.video_dir}")
    print(f"缩略图目录: {config.thumbnail_dir}")

    # 测试路径规范化
    test_paths = [
        "/content/videos",
        "content/videos",
        "./content/videos",
        "C:/content/videos"
    ]

    print("\n路径规范化测试:")
    for path in test_paths:
        normalized = str(Path(path).as_posix())
        print(f"  原始: {path:25s} -> 规范化: {normalized}")

    print("✓ 路径处理测试完成")
    return True


def test_mount_config():
    """测试挂载配置"""
    print_section("3. 挂载配置测试")

    # 使用示例配置
    config_path = "mounts_config.example.json"
    if os.path.exists(config_path):
        mount_config = MountConfig(config_path)
    else:
        print(f"配置文件不存在，使用默认配置")
        mount_config = MountConfig()

    # 打印挂载配置
    mount_config.print_mounts()

    # 测试获取挂载路径
    print("\n挂载路径获取测试:")
    test_mounts = ['videos', 'thumbnails', 'uploads', 'static', 'cache']
    for mount_name in test_mounts:
        mount_path = mount_config.get_mount_path(mount_name)
        source_path = mount_config.get_source_path(mount_name)
        read_only = mount_config.is_read_only(mount_name)
        print(f"  {mount_name:15s} -> {mount_path} (源: {source_path}, 只读: {read_only})")

    # 测试生成Docker Compose配置
    print("\nDocker Compose卷配置:")
    volumes = mount_config.generate_docker_compose_volumes()
    for vol in volumes:
        print(f"  - {vol}")

    # 测试生成docker run参数
    print("\ndocker run参数:")
    args = mount_config.generate_docker_run_args()
    print("  " + " ".join(args))

    # 测试添加自定义挂载
    print("\n添加自定义挂载:")
    mount_config.add_mount(
        name='test_custom',
        source='/content/test',
        target='/app/test',
        description='测试挂载',
        read_only=False
    )
    print("  ✓ 已添加 test_custom 挂载")

    # 测试保存配置
    test_config_path = os.path.join(os.getcwd(), "test_mounts_config.json")
    mount_config.save(test_config_path)
    if os.path.exists(test_config_path):
        print(f"  ✓ 配置已保存到: {test_config_path}")
        os.remove(test_config_path)
        print(f"  ✓ 测试配置文件已清理")

    print("✓ 挂载配置测试完成")
    return True


def test_config_file_loading():
    """测试配置文件加载"""
    print_section("4. 配置文件加载测试")

    config = get_config()

    print(f"项目根目录: {config.project_root}")
    print(f"配置目录: {config.config_dir}")
    print(f"数据目录: {config.data_dir}")
    print(f"日志目录: {config.log_dir}")
    print(f"视频目录: {config.video_dir}")
    print(f"数据库路径: {config.get_db_path()}")

    # 测试环境变量覆盖
    print("\n环境变量覆盖测试:")

    # 测试DPLAYER_CONFIG_DIR
    original_config_dir = os.environ.get('DPLAYER_CONFIG_DIR')
    os.environ['DPLAYER_CONFIG_DIR'] = '/test/config'

    import importlib
    import config_manager
    importlib.reload(config_manager)
    from config_manager import get_config as get_config_env
    config_env = get_config_env()

    print(f"  环境变量 DPLAYER_CONFIG_DIR=/test/config")
    print(f"  配置目录: {config_env.config_dir}")

    # 恢复环境变量
    if original_config_dir:
        os.environ['DPLAYER_CONFIG_DIR'] = original_config_dir
    else:
        os.environ.pop('DPLAYER_CONFIG_DIR', None)

    print("✓ 配置文件加载测试完成")
    return True


def test_directory_structure():
    """测试目录结构"""
    print_section("5. 目录结构测试")

    config = get_config()

    # 检查关键目录
    key_dirs = [
        ('配置目录', config.config_dir),
        ('数据目录', config.data_dir),
        ('日志目录', config.log_dir),
        ('视频目录', config.video_dir),
        ('缩略图目录', config.thumbnail_dir)
    ]

    print("\n目录存在性检查:")
    all_exist = True
    for name, path in key_dirs:
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {path}")
        if not exists:
            all_exist = False

    # 测试目录创建
    print("\n测试目录创建:")
    test_dir = "test_docker_dir"
    test_path = os.path.join(config.data_dir, test_dir)

    os.makedirs(test_path, exist_ok=True)
    print(f"  ✓ 创建测试目录: {test_path}")

    if os.path.exists(test_path):
        print(f"  ✓ 目录创建成功")
        os.rmdir(test_path)
        print(f"  ✓ 目录已清理")

    print("✓ 目录结构测试完成")
    return all_exist


def test_cross_platform_compatibility():
    """测试跨平台兼容性"""
    print_section("6. 跨平台兼容性测试")

    config = get_config()

    # 测试路径分隔符处理
    print("\n路径分隔符测试:")
    test_paths = [
        "/content/videos/test.mp4",
        "content/videos/test.mp4"
    ]

    for path in test_paths:
        path_obj = Path(path)
        normalized = path_obj.as_posix()  # 使用 / 作为分隔符
        print(f"  {path:35s} -> {normalized}")

    # 测试文件操作
    print("\n文件操作测试:")
    test_file = os.path.join(config.data_dir, "test_file.txt")

    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试文件内容\n")
        print(f"  ✓ 写入文件: {test_file}")

        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"  ✓ 读取文件: {content.strip()}")

        os.remove(test_file)
        print(f"  ✓ 删除文件")

    except Exception as e:
        print(f"  ✗ 文件操作失败: {e}")
        return False

    print("✓ 跨平台兼容性测试完成")
    return True


def test_docker_specific_features():
    """测试Docker特定功能"""
    print_section("7. Docker特定功能测试")

    config = get_config()

    print(f"Docker环境检测: {config.is_docker}")
    print(f"平台: {config.platform}")

    # 测试软链接（Windows可能不支持）
    print("\n软链接支持测试:")
    if platform.system() == 'Windows':
        print("  ℹ Windows环境，跳过软链接测试")
    else:
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                source = os.path.join(tmpdir, "source")
                target = os.path.join(tmpdir, "target")

                os.makedirs(source)
                os.symlink(source, target)

                if os.path.islink(target):
                    print("  ✓ 系统支持软链接")
                else:
                    print("  ✗ 系统不支持软链接")
        except Exception as e:
            print(f"  ✗ 软链接测试失败: {e}")

    # 测试环境变量
    print("\nDocker环境变量检查:")
    docker_env_vars = [
        'DPLAYER_IS_DOCKER',
        'DPLAYER_CONFIG_DIR',
        'DPLAYER_DATA_DIR',
        'DPLAYER_LOG_DIR',
        'DPLAYER_MOUNT_CONFIG'
    ]

    for var in docker_env_vars:
        value = os.environ.get(var, '未设置')
        print(f"  {var:30s} = {value}")

    print("✓ Docker特定功能测试完成")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Docker Linux环境功能测试" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")

    test_results = []

    # 运行所有测试
    tests = [
        ("平台检测", test_platform_detection),
        ("路径处理", test_path_handling),
        ("挂载配置", test_mount_config),
        ("配置文件加载", test_config_file_loading),
        ("目录结构", test_directory_structure),
        ("跨平台兼容性", test_cross_platform_compatibility),
        ("Docker特定功能", test_docker_specific_features)
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result, "PASS"))
        except Exception as e:
            print(f"\n✗ {test_name}测试失败: {e}")
            test_results.append((test_name, False, "FAIL"))

    # 打印测试总结
    print_section("测试结果总结")

    total = len(test_results)
    passed = sum(1 for _, result, _ in test_results if result)
    failed = total - passed

    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")

    print("\n详细结果:")
    for test_name, result, status in test_results:
        status_icon = "✓" if result else "✗"
        print(f"  {status_icon} {test_name:20s} [{status}]")

    # 生成JSON报告
    report = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed/total*100:.1f}%",
        "results": [
            {
                "name": name,
                "passed": result,
                "status": status
            }
            for name, result, status in test_results
        ]
    }

    report_file = "docker_linux_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✓ 测试报告已保存: {report_file}")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
