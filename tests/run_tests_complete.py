#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试运行器 - 运行所有测试用例 (修复版)
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试框架
from tests.test_framework import get_test_framework, reset_test_framework

# 重置框架,确保使用最新的配置
reset_test_framework()

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

print(f"\n================================================================================")
print(f"总计: {len(framework.test_cases)} 个测试用例")
print(f"================================================================================\n")

# 运行所有测试
all_tests = framework.get_all_tests()
print(f"运行所有 {len(framework.categories)} 个类别的测试...\n")
print(f"准备运行 {len(all_tests)} 个测试用例...\n")

# 运行测试
results = framework.run_tests(all_tests=True)

# 统计结果
passed = sum(1 for r in results if r.status.name == 'PASSED')
failed = sum(1 for r in results if r.status.name == 'FAILED')
error = sum(1 for r in results if r.status.name == 'ERROR')
skipped = sum(1 for r in results if r.status.name == 'SKIPPED')

print("\n" + "=" * 80)
print("测试摘要:")
print(f"  总计: {len(results)}")
print(f"  通过: {passed} ({passed/len(results)*100:.1f}%)" if results else "  通过: 0")
print(f"  失败: {failed}")
print(f"  错误: {error}")
print(f"  跳过: {skipped}")
print("=" * 80)
print("\n测试完成!")
print("=" * 80)
