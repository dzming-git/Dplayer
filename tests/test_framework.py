"""
Dplayer 自动化测试框架

功能：
1. 全自动测试执行
2. 支持选择性测试（通过参数指定）
3. 支持全部测试（--all 参数）
4. 支持错误时不跳过（-k 参数）
5. 测试报告生成
6. 并行测试支持
7. 测试数据管理
8. 测试日志记录

使用方法：
    python run_tests.py --all                    # 运行所有测试
    python run_tests.py -k                        # 运行所有测试，出错不跳过
    python run_tests.py PORT CONFIG DATABASE      # 运行指定类别的测试
    python run_tests.py --all -k                  # 运行所有测试，出错不跳过
"""

import sys
import os
import time
import json
import traceback
from datetime import datetime
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import concurrent.futures
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """测试用例类"""
    id: str
    name: str
    category: str
    description: str
    priority: str = "P1"
    test_func: Optional[Callable] = None
    timeout: int = 300  # 默认超时时间5分钟
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """测试结果类"""
    test_case: TestCase
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error_message: str = ""
    stack_trace: str = ""
    output: str = ""


class TestFramework:
    """测试框架核心类"""

    def __init__(self):
        self.test_cases: Dict[str, TestCase] = {}
        self.test_results: List[TestResult] = []
        self.stop_on_error = False
        self.parallel = False
        self.max_workers = 4
        self.categories: Dict[str, List[str]] = {
            "PORT": [],
            "CONFIG": [],
            "DATABASE": [],
            "API_MAIN": [],
            "API_ADMIN": [],
            "THUMBNAIL": [],
            "RECOMMENDATION": [],
            "LOGGING": [],
            "VIDEO_PROCESSING": [],
            "SYSTEM_MONITOR": [],
            "ERROR_HANDLING": [],
            "PERFORMANCE": [],
            "INTEGRATION": [],
            "SECURITY": [],
            "COMPATIBILITY": [],
            "FRAMEWORK": [],
            "ROUTES": [],
            "FUNCTIONS": []
        }

    def register_test(self, test_case: TestCase):
        """注册测试用例"""
        self.test_cases[test_case.id] = test_case
        if test_case.category in self.categories:
            self.categories[test_case.category].append(test_case.id)

    def get_tests_by_category(self, category: str) -> List[TestCase]:
        """获取指定类别的测试用例"""
        test_ids = self.categories.get(category, [])
        return [self.test_cases[tid] for tid in test_ids]

    def get_all_tests(self) -> List[TestCase]:
        """获取所有测试用例"""
        return list(self.test_cases.values())

    def run_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        result = TestResult(test_case=test_case)
        result.status = TestStatus.RUNNING
        result.start_time = datetime.now()

        try:
            # 执行测试函数
            if test_case.test_func:
                print(f"[测试] {test_case.id}: {test_case.name}")
                print(f"[描述] {test_case.description}")

                # 执行测试
                test_case.test_func()

                result.status = TestStatus.PASSED
                print(f"[通过] {test_case.id}")
            else:
                result.status = TestStatus.SKIPPED
                result.error_message = "测试函数未定义"
                print(f"[跳过] {test_case.id}: 未实现")

        except AssertionError as e:
            result.status = TestStatus.FAILED
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
            print(f"[失败] {test_case.id}: {e}")

        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.stack_trace = traceback.format_exc()
            print(f"[错误] {test_case.id}: {e}")

        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()

        return result

    def run_tests(self, categories: List[str] = None, all_tests: bool = False) -> List[TestResult]:
        """运行测试用例"""
        results = []

        # 确定要运行的测试用例
        tests_to_run = []
        if all_tests:
            tests_to_run = self.get_all_tests()
        elif categories:
            for category in categories:
                tests_to_run.extend(self.get_tests_by_category(category))
        else:
            print("错误: 必须指定 --all 或指定测试类别")
            return []

        # 调试：打印tests_to_run的类型
        if tests_to_run:
            print(f"[调试] tests_to_run[0]类型: {type(tests_to_run[0])}")
            print(f"[调试] tests_to_run[0]是否为TestCase: {isinstance(tests_to_run[0], TestCase)}")

        # 按优先级排序
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        tests_to_run.sort(key=lambda tc: priority_order.get(tc.priority, 4))

        print(f"\n准备运行 {len(tests_to_run)} 个测试用例...\n")
        print("=" * 80)

        # 运行测试
        for i, test_case in enumerate(tests_to_run, 1):
            print(f"\n[{i}/{len(tests_to_run)}] 运行测试: {test_case.id}")
            print("-" * 80)

            result = self.run_test(test_case)
            results.append(result)
            self.test_results.append(result)

            # 如果设置了 stop_on_error 且测试失败，停止运行
            if self.stop_on_error and result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                print(f"\n[停止] 由于错误停止测试执行")
                break

        # 调试：打印results的类型
        if results:
            print(f"\n[调试] results[0]类型: {type(results[0])}")
            print(f"[调试] results[0]是否为TestResult: {isinstance(results[0], TestResult)}")

        return results

    def generate_report(self, results: List[TestResult], output_file: str = None) -> str:
        """生成测试报告"""
        # 过滤掉非TestResult对象
        valid_results = [r for r in results if isinstance(r, TestResult)]

        # 调试：检查results
        if len(valid_results) != len(results):
            print(f"[警告] results包含{len(results) - len(valid_results)}个无效对象，已过滤")

        total = len(valid_results)
        passed = sum(1 for r in valid_results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in valid_results if r.status == TestStatus.FAILED)
        error = sum(1 for r in valid_results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in valid_results if r.status == TestStatus.SKIPPED)
        total_duration = sum(r.duration for r in valid_results)

        report_lines = [
            "\n" + "=" * 80,
            "Dplayer 测试报告",
            "=" * 80,
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\n测试摘要:",
            f"  总计: {total}",
            f"  通过: {passed} ({passed/total*100:.1f}%)" if total > 0 else "  通过: 0",
            f"  失败: {failed} ({failed/total*100:.1f}%)" if total > 0 else "  失败: 0",
            f"  错误: {error} ({error/total*100:.1f}%)" if total > 0 else "  错误: 0",
            f"  跳过: {skipped} ({skipped/total*100:.1f}%)" if total > 0 else "  跳过: 0",
            f"  总耗时: {total_duration:.2f}秒",
            "\n" + "=" * 80,
        ]

        # 失败和错误的测试详情
        failed_tests = [r for r in valid_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
        if failed_tests:
            report_lines.append("\n失败/错误详情:")
            report_lines.append("-" * 80)
            for result in failed_tests:
                report_lines.append(f"\n{result.test_case.id}: {result.test_case.name}")
                report_lines.append(f"  状态: {result.status.value}")
                report_lines.append(f"  错误: {result.error_message}")
                if result.stack_trace:
                    report_lines.append(f"  堆栈:\n{result.stack_trace}")

        report_lines.append("\n" + "=" * 80)
        report = "\n".join(report_lines)

        # 输出报告
        print(report)

        # 保存到文件
        if output_file:
            self.save_report(report, output_file)
            print(f"\n测试报告已保存到: {output_file}")

        return report

    def save_report(self, report: str, output_file: str):
        """保存测试报告到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    def export_json_report(self, output_file: str = "test_report.json"):
        """导出JSON格式的测试报告"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r.status == TestStatus.PASSED),
                "failed": sum(1 for r in self.test_results if r.status == TestStatus.FAILED),
                "error": sum(1 for r in self.test_results if r.status == TestStatus.ERROR),
                "skipped": sum(1 for r in self.test_results if r.status == TestStatus.SKIPPED),
                "total_duration": sum(r.duration for r in self.test_results)
            },
            "results": []
        }

        for result in self.test_results:
            report_data["results"].append({
                "id": result.test_case.id,
                "name": result.test_case.name,
                "category": result.test_case.category,
                "priority": result.test_case.priority,
                "status": result.status.value,
                "duration": result.duration,
                "error_message": result.error_message,
                "stack_trace": result.stack_trace
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"JSON报告已保存到: {output_file}")


# 测试装饰器
def test_case(id: str, name: str, category: str, description: str, priority: str = "P1", timeout: int = 300):
    """测试用例装饰器"""
    def decorator(func):
        # 获取测试框架实例
        framework = get_test_framework()

        # 创建测试用例
        tc = TestCase(
            id=id,
            name=name,
            category=category,
            description=description,
            priority=priority,
            test_func=func,
            timeout=timeout
        )

        # 注册测试用例
        framework.register_test(tc)

        return func

    return decorator


# 全局测试框架实例
_test_framework = None


def get_test_framework() -> TestFramework:
    """获取测试框架实例"""
    global _test_framework
    if _test_framework is None:
        _test_framework = TestFramework()
    return _test_framework


def reset_test_framework():
    """重置测试框架"""
    global _test_framework
    _test_framework = None


# 断言函数
def assert_equal(actual, expected, message: str = ""):
    """断言相等"""
    if actual != expected:
        raise AssertionError(f"{message}\n预期: {expected}\n实际: {actual}")


def assert_not_equal(actual, expected, message: str = ""):
    """断言不相等"""
    if actual == expected:
        raise AssertionError(f"{message}\n值不应该等于: {expected}")


def assert_true(condition, message: str = ""):
    """断言为真"""
    if not condition:
        raise AssertionError(f"{message}\n条件应该为真")


def assert_false(condition, message: str = ""):
    """断言为假"""
    if condition:
        raise AssertionError(f"{message}\n条件应该为假")


def assert_in(item, container, message: str = ""):
    """断言包含"""
    if item not in container:
        raise AssertionError(f"{message}\n{item} 不在 {container} 中")


def assert_not_in(item, container, message: str = ""):
    """断言不包含"""
    if item in container:
        raise AssertionError(f"{message}\n{item} 不应该在 {container} 中")


def assert_greater(a, b, message: str = ""):
    """断言大于"""
    if not a > b:
        raise AssertionError(f"{message}\n{a} 应该大于 {b}")


def assert_less(a, b, message: str = ""):
    """断言小于"""
    if not a < b:
        raise AssertionError(f"{message}\n{a} 应该小于 {b}")


def assert_raises(exception_type, func, *args, **kwargs):
    """断言抛出异常"""
    try:
        func(*args, **kwargs)
        raise AssertionError(f"预期抛出 {exception_type.__name__} 异常，但没有抛出")
    except exception_type:
        pass
    except Exception as e:
        raise AssertionError(f"预期抛出 {exception_type.__name__} 异常，但抛出了 {type(e).__name__}: {e}")
