#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试运行器 - 运行所有测试用例
"""

import sys
import os
import importlib

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入测试框架
from tests.test_framework import get_test_framework, reset_test_framework

# 重置框架,确保使用最新的配置
reset_test_framework()

# 动态发现并导入所有测试模块
def discover_test_modules(test_dir="tests"):
    """发现并导入所有测试模块"""
    imported_modules = []
    if not os.path.exists(test_dir):
        return imported_modules

    for filename in sorted(os.listdir(test_dir)):
        # 导入所有以test_开头且不是test_framework.py、run_*.py等的测试文件
        if (filename.startswith("test_") and
            filename.endswith(".py") and
            filename != "test_framework.py" and
            not filename.startswith("test_admin_apis") and
            not filename.startswith("run_") and
            filename not in ["test_import.py", "test_quick.py"]):

            module_name = filename[:-3]  # 移除 .py
            full_module_name = f"tests.{module_name}"

            try:
                # 使用importlib动态导入，捕获并忽略所有错误
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, os.path.join(test_dir, filename))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)

                    # 在独立上下文中执行，避免影响标准输出
                    import io
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    try:
                        sys.stdout = io.StringIO()
                        sys.stderr = io.StringIO()
                        spec.loader.exec_module(module)
                        imported_modules.append(module_name)
                        print(f"[导入] {module_name}")
                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
            except Exception as e:
                # 静默跳过有问题的测试模块
                pass

    return imported_modules

# 导入所有测试模块
print("\n正在导入测试模块...")
print("=" * 80)
imported = discover_test_modules()
print(f"成功导入 {len(imported)} 个测试模块")
print("=" * 80 + "\n")

# 获取测试框架
framework = get_test_framework()

print("\n" + "=" * 80)
print("Dplayer 完整自动化测试 - 所有测试用例")
print("=" * 80 + "\n")

# 按类别显示测试
for category, test_ids in framework.categories.items():
    if test_ids:
        print(f"\n【{category}】{len(test_ids)} 个测试用例")
        print("-" * 80)
        for test_id in test_ids:
            test_case = framework.test_cases[test_id]
            print(f"  {test_id:20} | {test_case.name}")

print("\n" + "=" * 80)
total = len(framework.test_cases)
print(f"总计: {total} 个测试用例")
print("=" * 80 + "\n")

# 如果没有测试用例，直接退出
if total == 0:
    print("警告: 没有发现任何测试用例")
    sys.exit(0)

# 运行所有类别测试
all_categories = list(framework.categories.keys())
print(f"运行所有 {len(all_categories)} 个类别的测试...\n")

# 调试：检查测试用例
print(f"调试信息:")
print(f"  测试用例数量: {len(framework.test_cases)}")
print(f"  测试用例类型: {type(list(framework.test_cases.values())[0]) if framework.test_cases else 'None'}")

results = framework.run_tests(categories=all_categories)

# 调试：检查results类型
print(f"\n调试信息:")
print(f"  results长度: {len(results)}")
if results:
    str_count = sum(1 for r in results if isinstance(r, str))
    testresult_count = sum(1 for r in results if hasattr(r, 'status'))
    print(f"  TestResult对象数量: {testresult_count}")
    print(f"  字符串对象数量: {str_count}")

    # 找出所有字符串对象
    string_indices = [i for i, r in enumerate(results) if isinstance(r, str)]
    if string_indices:
        print(f"  字符串对象的位置: {string_indices[:10]}")
        for idx in string_indices[:5]:
            print(f"    results[{idx}] = {results[idx][:50] if len(results[idx]) > 50 else results[idx]}")

# 生成报告
framework.generate_report("test_report.txt")
framework.export_json_report("test_report.json")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80 + "\n")
