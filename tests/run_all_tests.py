#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试运行器 - 运行所有测试用例
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试框架和测试模块
from tests.test_framework import get_test_framework

# 导入所有测试模块
import tests.test_port
import tests.test_config
import tests.test_database
import tests.test_api_main
import tests.test_api_admin
import tests.test_thumbnail
import tests.test_recommendation
import tests.test_logging
import tests.test_video_processing
import tests.test_system_monitor
import tests.test_error_handling
import tests.test_performance
import tests.test_integration
import tests.test_security
import tests.test_compatibility
import tests.test_framework_tests
import tests.test_routes_tests
import tests.test_functions_tests

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

# 运行所有类别测试
all_categories = list(framework.categories.keys())
print(f"运行所有 {len(all_categories)} 个类别的测试...\n")

results = framework.run_tests(categories=all_categories)

# 生成报告
framework.generate_report(results, "test_report.txt")
framework.export_json_report("test_report.json")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80 + "\n")
