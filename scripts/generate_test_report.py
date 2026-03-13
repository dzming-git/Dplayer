#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试报告生成脚本
为CI/CD流水线生成测试报告
"""

import os
import sys
from datetime import datetime

def generate_test_report():
    """生成测试报告"""
    print("开始生成测试报告...")

    # 检查是否有测试结果目录
    test_results_dir = "test_results"
    if not os.path.exists(test_results_dir):
        os.makedirs(test_results_dir)
        print(f"创建测试结果目录: {test_results_dir}")

    # 生成简单的HTML报告
    report_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dplayer 测试报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .info {{
            background-color: #e3f2fd;
            padding: 15px;
            border-left: 4px solid #2196F3;
            margin: 20px 0;
        }}
        .note {{
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }}
        footer {{
            margin-top: 40px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Dplayer 测试报告</h1>

        <div class="info">
            <h2>报告信息</h2>
            <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>测试类型:</strong> 自动化测试</p>
            <p><strong>运行环境:</strong> CI/CD 流水线</p>
        </div>

        <div class="note">
            <h2>测试说明</h2>
            <p>此报告由 CI/CD 流水线自动生成。</p>
            <p>详细的测试结果和日志请查看 GitHub Actions 的运行日志。</p>
        </div>

        <div class="info">
            <h2>测试类别</h2>
            <ul>
                <li>单元测试 (Unit Tests)</li>
                <li>API 集成测试 (API Integration Tests)</li>
                <li>性能测试 (Performance Tests)</li>
                <li>安全测试 (Security Tests)</li>
            </ul>
        </div>

        <div class="note">
            <h2>注意事项</h2>
            <p>由于项目已进行目录结构优化，部分测试文件路径已更新。</p>
            <p>新的目录结构：</p>
            <ul>
                <li><code>core/</code> - 核心模型</li>
                <li><code>api/</code> - API 接口</li>
                <li><code>services/</code> - 业务逻辑</li>
                <li><code>utils/</code> - 工具类</li>
                <li><code>config/</code> - 配置文件</li>
            </ul>
        </div>

        <footer>
            <p>Dplayer Flask 视频播放器项目 - 自动化测试报告</p>
            <p>生成于 {datetime.now().strftime('%Y年%m月%d日')}</p>
        </footer>
    </div>
</body>
</html>
"""

    # 保存报告
    report_file = "test_report.html"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_html)

    print(f"测试报告已生成: {report_file}")
    return report_file

if __name__ == "__main__":
    try:
        generate_test_report()
        print("测试报告生成成功")
        sys.exit(0)
    except Exception as e:
        print(f"生成测试报告失败: {e}")
        sys.exit(1)
