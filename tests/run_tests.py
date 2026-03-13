#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dplayer 测试运行器

使用方法：
    python run_tests.py --all                    # 运行所有测试
    python run_tests.py -k                        # 运行所有测试，出错不跳过
    python run_tests.py PORT CONFIG DATABASE      # 运行指定类别的测试
    python run_tests.py --all -k                  # 运行所有测试，出错不跳过
    python run_tests.py --help                    # 显示帮助信息
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_framework import (
    get_test_framework,
    reset_test_framework,
    TestFramework
)


def discover_test_files(test_dir: str = "tests") -> list:
    """发现测试文件"""
    test_files = []
    if not os.path.exists(test_dir):
        return test_files

    for filename in os.listdir(test_dir):
        if filename.startswith("test_") and filename.endswith(".py"):
            if filename != "test_framework.py" and filename != "run_tests.py":
                test_files.append(os.path.join(test_dir, filename))

    return sorted(test_files)


def import_test_modules(test_files: list):
    """导入测试模块"""
    for test_file in test_files:
        module_name = os.path.basename(test_file)[:-3]  # 移除 .py
        full_module_name = f"tests.{module_name}"

        try:
            # 使用 importlib 导入
            import importlib
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_module_name] = module

            # 在导入前保存标准输出和错误
            original_stdout = sys.stdout
            original_stderr = sys.stderr

            try:
                spec.loader.exec_module(module)
            finally:
                # 确保标准输出和错误被恢复
                sys.stdout = original_stdout
                sys.stderr = original_stderr

            print(f"[导入] {module_name}")
        except Exception as e:
            print(f"[错误] 导入 {module_name} 失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description="Dplayer 自动化测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py --all                    运行所有测试
  python run_tests.py -k                        运行所有测试，出错不跳过
  python run_tests.py PORT CONFIG DATABASE      运行指定类别的测试
  python run_tests.py --all -k                  运行所有测试，出错不跳过

测试类别:
  PORT              端口管理测试
  CONFIG            配置管理测试
  DATABASE          数据库测试
  API_MAIN          主应用API测试
  API_ADMIN         管理后台API测试
  THUMBNAIL         缩略图生成测试
  RECOMMENDATION    推荐系统测试
  LOGGING           日志系统测试
  VIDEO_PROCESSING  视频处理测试
  SYSTEM_MONITOR    系统监控测试
  ERROR_HANDLING    错误处理测试
  PERFORMANCE       性能测试
  INTEGRATION       集成测试
  SECURITY          安全性测试
  COMPATIBILITY     兼容性测试
        """
    )

    parser.add_argument(
        'categories',
        nargs='*',
        help='测试类别（可选，如果不指定则必须使用 --all）'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='运行所有测试'
    )

    parser.add_argument(
        '-k',
        '--keep-going',
        action='store_true',
        help='出错不跳过，继续运行所有测试'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='测试报告输出文件（默认：test_report.txt）'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='导出JSON格式的测试报告'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='详细输出'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有测试用例'
    )

    # 解析参数
    args = parser.parse_args()

    # 验证参数
    if not args.all and not args.categories and not args.list:
        parser.print_help()
        sys.exit(1)

    if args.all and args.categories:
        print("错误: 不能同时使用 --all 和指定类别")
        sys.exit(1)

    # 获取测试框架
    framework = get_test_framework()

    # 列出测试用例
    if args.list:
        print("\n所有测试用例:")
        print("=" * 80)
        for test_id, test_case in sorted(framework.test_cases.items()):
            print(f"{test_id:20} | {test_case.category:20} | {test_case.name}")
            if args.verbose:
                print(f"{'':20} | 描述: {test_case.description}")
                print(f"{'':20} | 优先级: {test_case.priority}")
                print(f"{'':20} | 超时: {test_case.timeout}秒")
        print("=" * 80)
        print(f"\n总计: {len(framework.test_cases)} 个测试用例\n")
        sys.exit(0)

    # 发现并导入测试模块
    test_files = discover_test_files()
    if test_files:
        print("\n发现测试文件:")
        for test_file in test_files:
            print(f"  - {test_file}")
        print()

        import_test_modules(test_files)
    else:
        print("警告: 未发现测试文件")

    # 验证测试类别
    if args.categories:
        for category in args.categories:
            if category not in framework.categories:
                print(f"错误: 未知的测试类别 '{category}'")
                print(f"可用的测试类别: {', '.join(framework.categories.keys())}")
                sys.exit(1)

    # 设置测试框架参数
    framework.stop_on_error = not args.keep_going

    # 打印测试信息
    print("\n" + "=" * 80)
    print("Dplayer 自动化测试")
    print("=" * 80)

    if args.all:
        print("模式: 运行所有测试")
    else:
        print("模式: 运行指定类别的测试")
        print(f"类别: {', '.join(args.categories)}")

    print(f"出错继续: {'是' if args.keep_going else '否'}")
    print(f"详细输出: {'是' if args.verbose else '否'}")
    print("=" * 80)

    # 运行测试
    try:
        results = framework.run_tests(
            categories=args.categories if not args.all else None,
            all_tests=args.all
        )

        # 生成报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = args.output or f"test_report_{timestamp}.txt"
        framework.generate_report(results, report_file)

        # 导出JSON报告
        if args.json:
            json_file = report_file.replace(".txt", ".json")
            framework.export_json_report(json_file)

        # 退出码
        failed_count = sum(1 for r in results if r.status.value in ["failed", "error"])
        if failed_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
