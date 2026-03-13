# Dplayer 自动化测试框架

## 概述

Dplayer 自动化测试框架是一个完整的测试解决方案，支持：

1. 全自动测试执行
2. 选择性测试（通过参数指定类别）
3. 全部测试（--all 参数）
4. 错误时不跳过（-k 参数）
5. 测试报告生成（文本和JSON格式）
6. 并行测试支持
7. 测试数据管理
8. 测试日志记录

## 目录结构

```
tests/
├── __init__.py              # 测试包初始化
├── test_framework.py        # 测试框架核心代码
├── run_tests.py            # 测试运行器
├── test_port.py            # 端口管理测试
├── test_config.py          # 配置管理测试
├── test_database.py        # 数据库测试
├── test_api_main.py        # 主应用API测试（待实现）
├── test_api_admin.py       # 管理后台API测试（待实现）
├── test_thumbnail.py       # 缩略图生成测试（待实现）
├── test_recommendation.py  # 推荐系统测试（待实现）
├── test_logging.py         # 日志系统测试（待实现）
├── test_video_processing.py # 视频处理测试（待实现）
├── test_integration.py     # 集成测试（待实现）
└── test_performance.py     # 性能测试（待实现）
```

## 快速开始

### 1. 运行所有测试

```bash
python tests/run_tests.py --all
```

### 2. 运行指定类别的测试

```bash
# 运行端口管理测试
python tests/run_tests.py PORT

# 运行多个类别的测试
python tests/run_tests.py PORT CONFIG DATABASE

# 运行所有配置的测试类别
python tests/run_tests.py PORT CONFIG DATABASE API_MAIN API_ADMIN THUMBNAIL RECOMMENDATION LOGGING VIDEO_PROCESSING SYSTEM_MONITOR ERROR_HANDLING PERFORMANCE INTEGRATION SECURITY COMPATIBILITY
```

### 3. 出错不跳过，继续运行所有测试

```bash
# 运行所有测试，出错不跳过
python tests/run_tests.py --all -k

# 运行指定类别的测试，出错不跳过
python tests/run_tests.py PORT CONFIG -k
```

### 4. 查看帮助信息

```bash
python tests/run_tests.py --help
```

### 5. 列出所有测试用例

```bash
python tests/run_tests.py --list
```

### 6. 详细输出

```bash
python tests/run_tests.py --all -v
```

## 测试类别

| 类别 | 描述 | 测试数量 | 状态 |
|------|------|---------|------|
| PORT | 端口管理测试 | 7 | ✓ 已实现 |
| CONFIG | 配置管理测试 | 6 | ✓ 已实现 |
| DATABASE | 数据库测试 | 8 | ✓ 已实现 |
| API_MAIN | 主应用API测试 | 42 | 待实现 |
| API_ADMIN | 管理后台API测试 | 34 | 待实现 |
| THUMBNAIL | 缩略图生成测试 | 10 | 待实现 |
| RECOMMENDATION | 推荐系统测试 | 5 | 待实现 |
| LOGGING | 日志系统测试 | 10 | 待实现 |
| VIDEO_PROCESSING | 视频处理测试 | 6 | 待实现 |
| SYSTEM_MONITOR | 系统监控测试 | 5 | 待实现 |
| ERROR_HANDLING | 错误处理测试 | 8 | 待实现 |
| PERFORMANCE | 性能测试 | 6 | 待实现 |
| INTEGRATION | 集成测试 | 8 | 待实现 |
| SECURITY | 安全性测试 | 6 | 待实现 |
| COMPATIBILITY | 兼容性测试 | 5 | 待实现 |

**总计：168个测试用例**

## 命令行参数

```
python run_tests.py [options] [categories...]

位置参数:
  categories              测试类别（可选，如果不指定则必须使用 --all）

可选参数:
  --all                   运行所有测试
  -k, --keep-going        出错不跳过，继续运行所有测试
  -o OUTPUT, --output OUTPUT
                          测试报告输出文件（默认：test_report_<timestamp>.txt）
  --json                  导出JSON格式的测试报告
  -v, --verbose           详细输出
  --list                  列出所有测试用例
  -h, --help              显示帮助信息
```

## 测试报告

### 文本报告

测试完成后会生成文本格式的测试报告，包含：

- 测试摘要（总计、通过、失败、错误、跳过）
- 失败/错误的测试详情
- 执行时间统计

示例：
```
================================================================================
Dplayer 测试报告
================================================================================

生成时间: 2026-03-13 10:30:00

测试摘要:
  总计: 21
  通过: 18 (85.7%)
  失败: 2 (9.5%)
  错误: 0 (0.0%)
  跳过: 1 (4.8%)
  总耗时: 12.34秒

================================================================================
```

### JSON报告

使用 `--json` 参数可以生成JSON格式的测试报告，便于：

- 自动化集成
- 结果分析
- 历史对比
- CI/CD 集成

JSON报告包含：

- 测试摘要
- 每个测试用例的详细结果
- 错误堆栈信息
- 执行时间

## 编写测试用例

### 基本结构

```python
from tests.test_framework import test_case, assert_true, assert_equal

@test_case(
    id="CATEGORY-XXX",
    name="测试用例名称",
    category="CATEGORY",
    description="测试用例描述",
    priority="P1"
)
def test_example():
    """测试用例实现"""
    # 测试代码
    assert_true(condition, "断言失败消息")
    assert_equal(actual, expected, "值不相等")
```

### 使用测试框架断言

```python
from tests.test_framework import (
    assert_equal,           # 断言相等
    assert_not_equal,       # 断言不相等
    assert_true,            # 断言为真
    assert_false,           # 断言为假
    assert_in,              # 断言包含
    assert_not_in,          # 断言不包含
    assert_greater,         # 断言大于
    assert_less,            # 断言小于
    assert_raises           # 断言抛出异常
)
```

### 测试用例元数据

| 字段 | 说明 | 必填 | 示例 |
|------|------|------|------|
| id | 测试用例ID（格式：类别-编号） | 是 | "PORT-001" |
| name | 测试用例名称 | 是 | "检查端口是否被占用" |
| category | 测试类别 | 是 | "PORT" |
| description | 测试用例描述 | 是 | "测试端口占用检查功能" |
| priority | 优先级（P0/P1/P2/P3） | 否 | "P0" |
| timeout | 超时时间（秒） | 否 | 300 |

## 测试优先级

- **P0** - 关键功能（必须通过）
  - 所有API端点的基本功能测试
  - 数据库CRUD操作
  - 端口管理和配置管理

- **P1** - 重要功能（应该通过）
  - 缩略图生成
  - 推荐系统
  - 应用管理
  - 日志系统

- **P2** - 一般功能（可以暂缓）
  - 性能测试
  - 兼容性测试
  - 部分错误处理

- **P3** - 可选功能（不强制）
  - 安全性测试
  - 高级功能测试

## 迁移现有测试

如果项目中已有测试代码，可以按照以下步骤迁移到测试框架：

1. **识别测试类别**
   - 根据测试功能确定类别（PORT/CONFIG/DATABASE等）

2. **添加测试装饰器**
   ```python
   @test_case(
       id="CATEGORY-XXX",
       name="测试名称",
       category="CATEGORY",
       description="测试描述",
       priority="P1"
   )
   ```

3. **使用测试框架断言**
   - 将 `assert` 替换为 `assert_true`、`assert_equal` 等
   - 或者继续使用 `assert`（框架会捕获 AssertionError）

4. **创建测试文件**
   - 在 `tests/` 目录下创建 `test_<category>.py`
   - 按照约定命名测试函数（以 `test_` 开头）

5. **验证测试**
   - 运行 `python tests/run_tests.py --list` 确认测试已注册
   - 运行 `python tests/run_tests.py CATEGORY` 测试单个类别

## 持续集成

### GitHub Actions 示例

```yaml
name: Dplayer Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8

    - name: Install dependencies
      run: |
        pip install flask sqlalchemy psutil opencv-python pillow requests

    - name: Run all tests
      run: |
        python tests/run_tests.py --all --json

    - name: Upload test report
      uses: actions/upload-artifact@v2
      with:
        name: test-report
        path: test_report_*.json
```

### Jenkins Pipeline 示例

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests') {
            steps {
                sh 'python tests/run_tests.py --all --json'
            }
        }

        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'test_report_*.json', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            junit 'test_report_*.json'
        }
    }
}
```

## 故障排除

### 问题1：无法导入测试模块

**症状**：运行测试时提示模块导入错误

**解决方案**：
```bash
# 确保在项目根目录运行
cd /path/to/Dplayer
python tests/run_tests.py --all
```

### 问题2：数据库连接失败

**症状**：测试数据库时提示连接失败

**解决方案**：
```bash
# 检查数据库文件是否存在
ls -la dplayer.db

# 如果不存在，先启动应用创建数据库
python app.py
```

### 问题3：端口被占用

**症状**：端口测试失败，提示端口被占用

**解决方案**：
```bash
# 停止占用端口的进程
python tests/run_tests.py PORT -k

# 或者修改配置文件中的端口
```

## 最佳实践

1. **编写独立的测试**
   - 每个测试应该独立运行
   - 不依赖其他测试的执行顺序
   - 使用 setup 和 teardown 清理测试数据

2. **使用描述性的测试名称**
   - 测试名称应该清楚说明测试的内容
   - 例如：`test_create_video_with_valid_data`

3. **提供清晰的错误消息**
   - 断言失败时提供有用的错误信息
   - 例如：`assert_equal(actual, expected, f"视频标题应该是 {expected}，实际是 {actual}")`

4. **保持测试简洁**
   - 每个测试只测试一个功能点
   - 避免在一个测试中测试多个功能

5. **使用适当的优先级**
   - P0: 关键功能，必须通过
   - P1: 重要功能，应该通过
   - P2: 一般功能，可以暂缓
   - P3: 可选功能，不强制

## 贡献指南

### 添加新的测试用例

1. 确定测试类别
2. 分配测试ID（格式：类别-编号）
3. 编写测试代码
4. 更新测试用例文档（TEST_CASES.md）
5. 运行测试验证

### 实现待开发的测试

1. 查看待实现的测试列表
2. 选择一个测试类别
3. 参考 `test_port.py`、`test_config.py` 等已实现的测试
4. 按照相同的模式实现新的测试文件

## 联系方式

如有问题或建议，请联系项目维护者。

## 许可证

本测试框架遵循 Dplayer 项目的许可证。
