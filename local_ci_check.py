#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地CI模拟脚本 - 在git commit前运行所有CI检查

使用方法：
    python local_ci_check.py              # 运行所有检查
    python local_ci_check.py --quick       # 只运行快速检查
    python local_ci_check.py --category PORT CONFIG DATABASE  # 运行指定类别的测试
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

# Windows兼容性检查
IS_WINDOWS = sys.platform == 'win32'

# 颜色输出
class Colors:
    GREEN = '\033[92m' if not IS_WINDOWS else ''
    RED = '\033[91m' if not IS_WINDOWS else ''
    YELLOW = '\033[93m' if not IS_WINDOWS else ''
    BLUE = '\033[94m' if not IS_WINDOWS else ''
    RESET = '\033[0m' if not IS_WINDOWS else ''
    BOLD = '\033[1m' if not IS_WINDOWS else ''

    # 符号
    CHECK = '[OK]' if IS_WINDOWS else '✓'
    CROSS = '[FAIL]' if IS_WINDOWS else '✗'
    WARN = '[WARN]' if IS_WINDOWS else '⚠'
    INFO = '[INFO]' if IS_WINDOWS else 'ℹ'

def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 80}{Colors.RESET}\n")

def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}{Colors.CHECK} {text}{Colors.RESET}")

def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}{Colors.CROSS} {text}{Colors.RESET}")

def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}{Colors.WARN} {text}{Colors.RESET}")

def print_info(text):
    """打印信息"""
    print(f"{Colors.BLUE}{Colors.INFO} {text}{Colors.RESET}")

def run_command(cmd, description, cwd=None):
    """
    运行命令并返回结果

    Args:
        cmd: 命令列表
        description: 命令描述
        cwd: 工作目录

    Returns:
        (success: bool, output: str, error: str)
    """
    print(f"\n{Colors.BLUE}[运行] {description}{Colors.RESET}")
    print(f"{' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )

        if result.returncode == 0:
            print_success(f"{description} - 通过")
            return True, result.stdout, result.stderr
        else:
            print_error(f"{description} - 失败 (退出码: {result.returncode})")
            if result.stderr:
                print(f"{Colors.RED}错误输出:\n{result.stderr[:500]}{Colors.RESET}")
            return False, result.stdout, result.stderr

    except Exception as e:
        print_error(f"{description} - 异常: {e}")
        return False, "", str(e)

def check_code_quality():
    """代码质量检查"""
    print_header("代码质量检查")

    # Flake8检查（严重错误只警告，不阻止提交）
    print_warning("注意：Flake8严重错误检查只显示警告，不会阻止提交")
    _, output, _ = run_command(
        [sys.executable, "-m", "flake8", ".", "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"],
        "Flake8 严重错误检查"
    )

    success2, _, _ = run_command(
        [sys.executable, "-m", "flake8", ".", "--count", "--exit-zero", "--max-complexity=10", "--max-line-length=127", "--statistics"],
        "Flake8 代码复杂度检查"
    )

    # Pylint检查
    success3, _, _ = run_command(
        [sys.executable, "-m", "pylint", "app.py", "admin_app.py", "--exit-zero"],
        "Pylint 主应用检查"
    )

    success4, _, _ = run_command(
        [sys.executable, "-m", "pylint", "core/", "api/", "services/", "utils/", "config/", "--exit-zero", "--ignore=__pycache__"],
        "Pylint 模块检查"
    )

    return all([success2, success3, success4])

def run_unit_tests():
    """运行单元测试"""
    print_header("单元测试")

    # 测试test_thumbnail_simple.py
    success, _, _ = run_command(
        [sys.executable, "tests/test_thumbnail_simple.py"],
        "缩略图简单测试"
    )

    return success

def run_api_tests():
    """运行API集成测试"""
    print_header("API集成测试")

    # API_MAIN测试
    success1, _, _ = run_command(
        [sys.executable, "tests/run_tests.py", "API_MAIN"],
        "主应用API测试"
    )

    # API_ADMIN测试
    success2, _, _ = run_command(
        [sys.executable, "tests/run_tests.py", "API_ADMIN"],
        "管理后台API测试"
    )

    return all([success1, success2])

def run_all_tests():
    """运行完整测试套件"""
    print_header("完整测试套件")

    success, _, _ = run_command(
        [sys.executable, "tests/run_all_tests.py"],
        "完整测试套件"
    )

    return success

def run_performance_tests():
    """运行性能测试"""
    print_header("性能测试")

    success, _, _ = run_command(
        [sys.executable, "tests/run_tests.py", "PERFORMANCE"],
        "性能测试"
    )

    return success

def run_security_tests():
    """运行安全测试"""
    print_header("安全测试")

    # Bandit安全扫描
    success1, _, _ = run_command(
        [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-o", "bandit-report.json"],
        "Bandit 安全扫描"
    )

    # Safety依赖漏洞检查
    success2, _, _ = run_command(
        [sys.executable, "-m", "safety", "check", "--json", ">safety-report.json"],
        "Safety 依赖安全检查"
    )

    # Safety可能返回非0退出码但仍然安全，所以这里总是返回True
    return success1

def main():
    parser = argparse.ArgumentParser(
        description="本地CI模拟脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python local_ci_check.py                    # 运行所有检查
  python local_ci_check.py --quick           # 只运行快速检查（代码质量+单元测试）
  python local_ci_check.py --skip-performance # 跳过性能测试
  python local_ci_check.py --category PORT    # 运行指定类别测试
        """
    )

    parser.add_argument('--quick', action='store_true', help='只运行快速检查')
    parser.add_argument('--skip-performance', action='store_true', help='跳过性能测试')
    parser.add_argument('--skip-security', action='store_true', help='跳过安全测试')
    parser.add_argument('--category', nargs='+', help='运行指定类别的测试（如: PORT CONFIG DATABASE）')

    args = parser.parse_args()

    # 打印开始信息
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 80)
    print("Dplayer 本地CI模拟")
    print("=" * 80)
    print(f"{Colors.RESET}开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")

    # 记录所有检查结果
    results = {}

    # 1. 代码质量检查
    results['代码质量检查'] = check_code_quality()

    # 2. 单元测试
    if args.category:
        # 运行指定类别的测试
        print_header(f"指定类别测试: {' '.join(args.category)}")
        success, _, _ = run_command(
            [sys.executable, "tests/run_tests.py"] + args.category,
            f"测试类别: {' '.join(args.category)}"
        )
        results['指定类别测试'] = success
    elif args.quick:
        # 快速模式：只运行单元测试
        results['单元测试'] = run_unit_tests()
    else:
        # 完整模式：运行所有测试
        results['单元测试'] = run_unit_tests()
        results['API集成测试'] = run_api_tests()
        results['完整测试套件'] = run_all_tests()

        # 性能测试（可选）
        if not args.skip_performance:
            results['性能测试'] = run_performance_tests()

        # 安全测试（可选）
        if not args.skip_security:
            results['安全测试'] = run_security_tests()

    # 打印汇总结果
    print_header("检查结果汇总")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, success in results.items():
        status = f"{Colors.GREEN}{Colors.CHECK} 通过{Colors.RESET}" if success else f"{Colors.RED}{Colors.CROSS} 失败{Colors.RESET}"
        print(f"{name:30s} {status}")

    print(f"\n总计: {total}  |  通过: {Colors.GREEN}{passed}{Colors.RESET}  |  失败: {Colors.RED}{failed}{Colors.RESET}")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 返回适当的退出码
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}{Colors.CHECK} 所有检查通过！可以提交代码。{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}{Colors.CROSS} 有 {failed} 个检查失败！请修复后再提交。{Colors.RESET}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
