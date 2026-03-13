#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试脚本

功能：
- 运行性能基准测试
- 记录性能指标
- 生成性能趋势报告
- 比较不同版本的性能

使用方法：
python scripts/benchmark.py
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BenchmarkRunner:
    """性能基准测试运行器"""

    def __init__(self):
        """初始化基准测试运行器"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(self.project_root, 'benchmark_results')
        self.ensure_results_dir()
        self.benchmarks = {}

    def ensure_results_dir(self):
        """确保结果目录存在"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def run_benchmark(self, name, func, iterations=10):
        """运行单个基准测试"""
        print(f"运行基准测试: {name}...")

        times = []
        for i in range(iterations):
            start = time.time()
            result = func()
            end = time.time()
            elapsed = (end - start) * 1000  # 转换为毫秒
            times.append(elapsed)
            print(f"  迭代 {i+1}/{iterations}: {elapsed:.2f}ms")

        # 计算统计数据
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = (sum((t - avg_time) ** 2 for t in times) / len(times)) ** 0.5

        benchmark_result = {
            'name': name,
            'iterations': iterations,
            'avg_time_ms': round(avg_time, 2),
            'min_time_ms': round(min_time, 2),
            'max_time_ms': round(max_time, 2),
            'std_dev_ms': round(std_dev, 2),
            'total_time_s': round(sum(times) / 1000, 2),
            'timestamp': datetime.now().isoformat()
        }

        self.benchmarks[name] = benchmark_result
        print(f"  平均时间: {avg_time:.2f}ms")
        print(f"  最小时间: {min_time:.2f}ms")
        print(f"  最大时间: {max_time:.2f}ms")
        print(f"  标准差: {std_dev:.2f}ms")

        return benchmark_result

    def save_results(self):
        """保存基准测试结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(self.results_dir, f'benchmark_{timestamp}.json')

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.benchmarks, f, indent=2, ensure_ascii=False)

        print(f"基准测试结果已保存: {result_file}")
        return result_file

    def generate_report(self):
        """生成基准测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.results_dir, f'benchmark_report_{timestamp}.html')

        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Dplayer 性能基准测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .good { color: green; }
        .warning { color: orange; }
        .bad { color: red; }
    </style>
</head>
<body>
    <h1>Dplayer 性能基准测试报告</h1>
    <p>生成时间: {timestamp}</p>

    <table>
        <tr>
            <th>测试名称</th>
            <th>平均时间 (ms)</th>
            <th>最小时间 (ms)</th>
            <th>最大时间 (ms)</th>
            <th>标准差 (ms)</th>
            <th>迭代次数</th>
            <th>状态</th>
        </tr>
        {rows}
    </table>
</body>
</html>
        """

        rows = ''
        for name, result in self.benchmarks.items():
            avg = result['avg_time_ms']
            status_class = 'good' if avg < 100 else 'warning' if avg < 500 else 'bad'
            status = '优秀' if avg < 100 else '良好' if avg < 500 else '需要优化'

            rows += f"""
            <tr>
                <td>{name}</td>
                <td>{avg}</td>
                <td>{result['min_time_ms']}</td>
                <td>{result['max_time_ms']}</td>
                <td>{result['std_dev_ms']}</td>
                <td>{result['iterations']}</td>
                <td class="{status_class}">{status}</td>
            </tr>
            """

        html = html_content.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            rows=rows
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"基准测试报告已生成: {report_file}")


def run_all_benchmarks():
    """运行所有基准测试"""
    runner = BenchmarkRunner()

    # 示例基准测试 - 导入测试
    def import_app():
        import app
        return True

    runner.run_benchmark('导入app.py', import_app, iterations=5)

    # 示例基准测试 - 导入models
    def import_models():
        import models
        return True

    runner.run_benchmark('导入models.py', import_models, iterations=5)

    # 示例基准测试 - 导入thumbnail_service
    def import_thumbnail_service():
        import thumbnail_service
        return True

    runner.run_benchmark('导入thumbnail_service.py', import_thumbnail_service, iterations=5)

    # 示例基准测试 - 导入thumbnail_service_client
    def import_thumbnail_service_client():
        import thumbnail_service_client
        return True

    runner.run_benchmark('导入thumbnail_service_client.py', import_thumbnail_service_client, iterations=5)

    # 保存结果
    runner.save_results()

    # 生成报告
    runner.generate_report()

    return runner.benchmarks


if __name__ == '__main__':
    print("=" * 60)
    print("Dplayer 性能基准测试")
    print("=" * 60)

    benchmarks = run_all_benchmarks()

    print("\n" + "=" * 60)
    print("基准测试完成")
    print("=" * 60)
