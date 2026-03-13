#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定期测试监控脚本

功能：
- 定期运行测试
- 记录测试结果
- 发送测试通知
- 生成测试趋势报告

使用方法：
python scripts/test_monitor.py
"""

import os
import sys
import json
import time
import subprocess
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMonitor:
    """测试监控类"""

    def __init__(self, config_file='test_monitor_config.json'):
        """初始化测试监控"""
        self.config = self.load_config(config_file)
        self.results_dir = 'test_monitor_results'
        self.ensure_results_dir()

    def load_config(self, config_file):
        """加载配置文件"""
        default_config = {
            'test_interval': 3600,  # 测试间隔（秒），默认1小时
            'test_command': 'python tests/run_all_tests.py',
            'notification_enabled': False,
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender': '',
                'password': '',
                'recipients': []
            },
            'slack': {
                'enabled': False,
                'webhook_url': ''
            }
        }

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                default_config.update(config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                print("使用默认配置")

        return default_config

    def ensure_results_dir(self):
        """确保结果目录存在"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def run_tests(self):
        """运行测试"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(self.results_dir, f'test_{timestamp}.log')
        result_file = os.path.join(self.results_dir, f'test_{timestamp}.json')

        print(f"[{datetime.now()}] 开始运行测试...")

        try:
            # 运行测试命令
            result = subprocess.run(
                self.config['test_command'],
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            # 解析测试结果
            test_result = self.parse_test_result(result.stdout, result.stderr)

            # 保存结果
            self.save_result(result_file, test_result, log_file, result.stdout, result.stderr)

            # 发送通知
            if self.config['notification_enabled']:
                self.send_notification(test_result)

            print(f"[{datetime.now()}] 测试完成: 通过={test_result['passed']}, 失败={test_result['failed']}")

            return test_result

        except Exception as e:
            print(f"[{datetime.now()}] 测试运行失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def parse_test_result(self, stdout, stderr):
        """解析测试结果"""
        # 这里需要根据实际的测试输出格式来解析
        # 简化版本，假设测试输出包含 "Tests run: X, Successes: Y"

        result = {
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'duration': 0
        }

        # 尝试从输出中解析测试结果
        for line in stdout.split('\n'):
            if 'Tests run:' in line:
                try:
                    parts = line.split(',')
                    for part in parts:
                        part = part.strip()
                        if 'Tests run:' in part:
                            result['total'] = int(part.split(':')[1].strip())
                        elif 'Successes:' in part:
                            result['passed'] = int(part.split(':')[1].strip())
                        elif 'Failures:' in part:
                            result['failed'] = int(part.split(':')[1].strip())
                        elif 'Errors:' in part:
                            result['errors'] = int(part.split(':')[1].strip())
                except Exception:
                    pass

        # 确定测试状态
        if result['failed'] > 0 or result['errors'] > 0:
            result['status'] = 'failed'
        elif result['passed'] > 0:
            result['status'] = 'passed'
        else:
            result['status'] = 'unknown'

        return result

    def save_result(self, result_file, test_result, log_file, stdout, stderr):
        """保存测试结果"""
        # 保存JSON结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)

        # 保存日志
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=== STDOUT ===\n")
            f.write(stdout)
            f.write("\n\n=== STDERR ===\n")
            f.write(stderr)

    def send_notification(self, test_result):
        """发送测试通知"""
        # 发送邮件通知
        if self.config['email']['enabled']:
            self.send_email_notification(test_result)

        # 发送Slack通知
        if self.config['slack']['enabled']:
            self.send_slack_notification(test_result)

    def send_email_notification(self, test_result):
        """发送邮件通知"""
        try:
            email_config = self.config['email']

            msg = MIMEMultipart()
            msg['From'] = email_config['sender']
            msg['To'] = ', '.join(email_config['recipients'])

            # 根据测试结果设置主题
            if test_result['status'] == 'passed':
                msg['Subject'] = f"[PASS] Dplayer 测试通过 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elif test_result['status'] == 'failed':
                msg['Subject'] = f"[FAIL] Dplayer 测试失败 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                msg['Subject'] = f"[UNKNOWN] Dplayer 测试结果未知 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # 邮件正文
            body = f"""
测试时间: {test_result['timestamp']}
测试状态: {test_result['status']}

测试结果:
- 总测试数: {test_result['total']}
- 通过: {test_result['passed']}
- 失败: {test_result['failed']}
- 错误: {test_result['errors']}

详细日志请查看附件或测试服务器。
            """
            msg.attach(MIMEText(body, 'plain'))

            # 发送邮件
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender'], email_config['password'])
                server.send_message(msg)

            print(f"[{datetime.now()}] 邮件通知已发送")

        except Exception as e:
            print(f"[{datetime.now()}] 发送邮件通知失败: {e}")

    def send_slack_notification(self, test_result):
        """发送Slack通知"""
        try:
            import requests

            slack_config = self.config['slack']

            # 根据测试结果设置颜色
            if test_result['status'] == 'passed':
                color = '#36a64f'  # 绿色
                emoji = ':white_check_mark:'
            elif test_result['status'] == 'failed':
                color = '#ff0000'  # 红色
                emoji = ':x:'
            else:
                color = '#ffcc00'  # 黄色
                emoji = ':warning:'

            # 构建Slack消息
            message = {
                'attachments': [
                    {
                        'color': color,
                        'title': f'{emoji} Dplayer 测试结果',
                        'fields': [
                            {
                                'title': '状态',
                                'value': test_result['status'],
                                'short': True
                            },
                            {
                                'title': '时间',
                                'value': test_result['timestamp'],
                                'short': True
                            },
                            {
                                'title': '总测试数',
                                'value': test_result['total'],
                                'short': True
                            },
                            {
                                'title': '通过',
                                'value': test_result['passed'],
                                'short': True
                            },
                            {
                                'title': '失败',
                                'value': test_result['failed'],
                                'short': True
                            },
                            {
                                'title': '错误',
                                'value': test_result['errors'],
                                'short': True
                            }
                        ]
                    }
                ]
            }

            # 发送到Slack
            requests.post(slack_config['webhook_url'], json=message)

            print(f"[{datetime.now()}] Slack通知已发送")

        except Exception as e:
            print(f"[{datetime.now()}] 发送Slack通知失败: {e}")

    def generate_trend_report(self):
        """生成测试趋势报告"""
        print(f"[{datetime.now()}] 生成测试趋势报告...")

        # 收集所有测试结果
        results = []
        for filename in os.listdir(self.results_dir):
            if filename.startswith('test_') and filename.endswith('.json'):
                filepath = os.path.join(self.results_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        results.append(json.load(f))
                except Exception as e:
                    print(f"读取结果文件失败 {filename}: {e}")

        # 按时间排序
        results.sort(key=lambda x: x['timestamp'])

        # 生成报告
        report_file = os.path.join(self.results_dir, 'trend_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # 生成HTML报告
        self.generate_html_trend_report(results)

        print(f"[{datetime.now()}] 趋势报告已生成: {report_file}")

    def generate_html_trend_report(self, results):
        """生成HTML趋势报告"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dplayer 测试趋势报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .passed { color: green; }
        .failed { color: red; }
        .summary { margin-top: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Dplayer 测试趋势报告</h1>

    <div class="summary">
        <h2>摘要</h2>
        <p>总测试次数: <strong>{total_runs}</strong></p>
        <p>通过次数: <strong class="passed">{passed_runs}</strong></p>
        <p>失败次数: <strong class="failed">{failed_runs}</strong></p>
        <p>通过率: <strong>{pass_rate:.1f}%</strong></p>
    </div>

    <h2>详细测试记录</h2>
    <table>
        <tr>
            <th>时间</th>
            <th>状态</th>
            <th>总测试数</th>
            <th>通过</th>
            <th>失败</th>
            <th>错误</th>
        </tr>
        {rows}
    </table>
</body>
</html>
        """

        # 计算统计数据
        total_runs = len(results)
        passed_runs = sum(1 for r in results if r['status'] == 'passed')
        failed_runs = sum(1 for r in results if r['status'] == 'failed')
        pass_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0

        # 生成表格行
        rows = ''
        for result in results[-50:]:  # 只显示最近50次测试
            status_class = result['status']
            rows += f"""
            <tr>
                <td>{result['timestamp']}</td>
                <td class="{status_class}">{result['status']}</td>
                <td>{result['total']}</td>
                <td>{result['passed']}</td>
                <td>{result['failed']}</td>
                <td>{result['errors']}</td>
            </tr>
            """

        html = html_content.format(
            total_runs=total_runs,
            passed_runs=passed_runs,
            failed_runs=failed_runs,
            pass_rate=pass_rate,
            rows=rows
        )

        report_file = os.path.join(self.results_dir, 'trend_report.html')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)

    def run_continuous(self):
        """持续运行测试监控"""
        print(f"[{datetime.now()}] 启动测试监控，测试间隔: {self.config['test_interval']}秒")
        print(f"[{datetime.now()}] 按 Ctrl+C 停止监控")

        try:
            while True:
                self.run_tests()
                print(f"[{datetime.now()}] 等待 {self.config['test_interval']} 秒...")
                time.sleep(self.config['test_interval'])
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] 测试监控已停止")
            self.generate_trend_report()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Dplayer 测试监控脚本')
    parser.add_argument('--once', action='store_true', help='只运行一次测试')
    parser.add_argument('--report', action='store_true', help='生成趋势报告')
    parser.add_argument('--config', default='test_monitor_config.json', help='配置文件路径')

    args = parser.parse_args()

    monitor = TestMonitor(args.config)

    if args.report:
        monitor.generate_trend_report()
    elif args.once:
        monitor.run_tests()
    else:
        monitor.run_continuous()


if __name__ == '__main__':
    main()
