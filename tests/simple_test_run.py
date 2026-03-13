#!/usr/bin/env python3
import sys
sys.path.insert(0, 'tests')

from test_framework import get_test_framework, reset_test_framework

# 重置
reset_test_framework()

# 导入所有测试模块
import test_port
import test_config
import test_database
import test_api_main
import test_api_admin
import test_thumbnail
import test_recommendation
import test_logging
import test_video_processing
import test_system_monitor
import test_error_handling
import test_performance
import test_integration
import test_security
import test_compatibility
import test_framework_tests
import test_routes_tests
import test_functions_tests

# 获取框架
fw = get_test_framework()

# 统计
total = len(fw.test_cases)
framework_count = len(fw.categories.get('FRAMEWORK', []))
routes_count = len(fw.categories.get('ROUTES', []))
functions_count = len(fw.categories.get('FUNCTIONS', []))

print(f"Total tests: {total}")
print(f"FRAMEWORK: {framework_count}")
print(f"ROUTES: {routes_count}")
print(f"FUNCTIONS: {functions_count}")
print()
print("Categories:", len(fw.categories))
