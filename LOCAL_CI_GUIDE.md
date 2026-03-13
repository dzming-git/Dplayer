# 本地CI检查设置指南

本目录包含本地CI模拟脚本，帮助您在提交代码前运行所有CI检查，确保代码质量。

## 快速开始

### 1. 运行本地CI检查

```bash
# 快速检查（代码质量 + 单元测试）
python local_ci_check.py --quick

# 完整检查（所有测试 + 代码质量 + 安全检查）
python local_ci_check.py

# 运行指定类别的测试
python local_ci_check.py --category PORT CONFIG DATABASE

# 跳过性能测试
python local_ci_check.py --skip-performance

# 跳过安全检查
python local_ci_check.py --skip-security
```

### 2. 设置Pre-commit Hook（可选）

如果您想在每次`git commit`前自动运行快速CI检查：

**Windows：**
```bash
copy .git\hooks\pre-commit .git\hooks\pre-commit.bat
```

**Linux/Mac：**
```bash
chmod +x .git/hooks/pre-commit
```

设置后，每次提交时会自动运行快速CI检查。如果检查失败，提交将被拒绝。

**绕过pre-commit hook：**
```bash
git commit --no-verify
```

## CI检查内容

### 快速检查模式 (`--quick`)
- Flake8代码复杂度检查
- Pylint主应用检查
- Pylint模块检查
- 单元测试（test_thumbnail_simple.py）

### 完整检查模式（默认）
包含快速检查的所有内容，加上：
- API集成测试（API_MAIN, API_ADMIN）
- 完整测试套件（run_all_tests.py）
- 性能测试（PERFORMANCE类别）
- 安全测试（Bandit + Safety）

### 指定类别测试
可以运行任意测试类别的组合：
- PORT：端口管理测试
- CONFIG：配置管理测试
- DATABASE：数据库测试
- API_MAIN：主应用API测试
- API_ADMIN：管理后台API测试
- THUMBNAIL：缩略图生成测试
- RECOMMENDATION：推荐系统测试
- LOGGING：日志系统测试
- VIDEO_PROCESSING：视频处理测试
- SYSTEM_MONITOR：系统监控测试
- ERROR_HANDLING：错误处理测试
- PERFORMANCE：性能测试
- INTEGRATION：集成测试
- SECURITY：安全性测试
- COMPATIBILITY：兼容性测试

## 输出说明

- `[OK]` 或 `✓`：检查通过
- `[FAIL]` 或 `✗`：检查失败
- `[WARN]` 或 `⚠`：警告信息
- `[INFO]` 或 `ℹ`：普通信息

## 提交前检查清单

在提交代码到GitHub之前，建议执行以下步骤：

1. **运行快速检查**（约30秒）
   ```bash
   python local_ci_check.py --quick
   ```

2. **如果快速检查通过，运行完整检查**（约2-3分钟）
   ```bash
   python local_ci_check.py
   ```

3. **修复所有失败的检查项**

4. **提交代码**
   ```bash
   git add .
   git commit -m "您的提交信息"
   ```

5. **推送到GitHub**
   ```bash
   git push origin master
   ```

## 注意事项

1. **Flake8严重错误检查**目前设置为警告模式，不会阻止提交。请检查输出中的错误并修复。

2. **数据库相关测试**可能需要预先创建测试数据库。

3. **某些API测试**可能需要Flask应用正在运行。

4. **性能测试**和**安全测试**可能较慢，可以使用`--skip-performance`和`--skip-security`跳过。

5. **CI和本地环境的差异**：
   - CI环境使用Python 3.9
   - CI运行在Linux上
   - CI使用固定的工作目录

## 故障排除

### pre-commit hook不工作

如果您设置了pre-commit hook但git commit没有触发检查：

1. **检查文件权限**：
   ```bash
   # Linux/Mac
   chmod +x .git/hooks/pre-commit
   ```

2. **检查文件位置**：
   确保pre-commit文件在`.git/hooks/`目录下

3. **查看hook输出**：
   手动运行hook脚本查看是否有错误：
   ```bash
   # Windows
   .git\hooks\pre-commit.bat

   # Linux/Mac
   .git/hooks/pre-commit
   ```

### 检查超时

某些测试可能较慢，特别是：
- 完整测试套件（run_all_tests.py）
- 性能测试
- 安全测试

如果超时，可以分别运行各个测试：
```bash
python tests/run_tests.py API_MAIN
python tests/run_tests.py API_ADMIN
python tests/run_all_tests.py
```

### 依赖问题

如果遇到缺少依赖的错误：
```bash
pip install -r requirements.txt
pip install flake8 pylint bandit safety
```

## 与GitHub CI的对应关系

| 本地CI检查 | GitHub CI检查 | 说明 |
|-----------|--------------|------|
| Flake8/Pylint检查 | Code Quality Check | 代码质量检查 |
| 单元测试 | Unit Tests | test_thumbnail_simple.py |
| API集成测试 | API Integration Tests | API_MAIN和API_ADMIN |
| 完整测试套件 | Full Test Suite | run_all_tests.py |
| 性能测试 | Performance Tests | PERFORMANCE类别 |
| 安全测试 | Security Tests | Bandit + Safety |

## 维护者说明

作为项目维护者，请确保：

1. **每次提交前运行本地CI检查**
2. **不要使用`--no-verify`绕过检查**，除非有特殊原因
3. **及时修复CI检查失败的问题**
4. **定期更新本地CI脚本**，保持与GitHub CI配置同步

## 联系方式

如有问题，请查看：
- GitHub Issues: https://github.com/dzming-git/Dplayer/issues
- CI配置文件: `.github/workflows/ci-cd.yml`
