# DPlayer 服务控制脚本 - Python版本优化说明

## 概述

基于参考代码的 win32service API 优化,创建了更强大的 Python 版本服务控制脚本。

## 主要改进

### 1. 直接使用 win32service API

**之前的方法**:
- 依赖 `subprocess` 调用 `sc.exe` 命令
- 受限于命令行工具的输出格式
- 错误处理不够精确

**现在的优化**:
- 使用 `win32service.OpenSCManager()` 和 `win32service.OpenService()` 直接操作服务
- 更精确的状态查询和控制
- 更好的错误处理和返回值

### 2. 核心功能实现

#### 服务状态查询 (`get_service_status`)
```python
def get_service_status(service_name):
    """使用 win32service API 直接查询服务状态"""
    scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_READ)
    service_handle = win32service.OpenService(scm_handle, service_name, win32con.GENERIC_READ)
    status = win32service.QueryServiceStatus(service_handle)
    # 返回标准化的状态字符串
```

#### 服务启动 (`start_service`)
```python
def start_service(service_key):
    """使用 win32service API 启动服务"""
    scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_EXECUTE)
    service_handle = win32service.OpenService(scm_handle, svc['name'], win32con.SERVICE_START)
    win32service.StartService(service_handle, None)
```

#### 服务停止 (`stop_service`)
```python
def stop_service(service_key):
    """使用 win32service API 停止服务"""
    scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_EXECUTE)
    service_handle = win32service.OpenService(scm_handle, svc['name'], win32service.SERVICE_STOP)
    win32service.ControlService(service_handle, win32service.SERVICE_CONTROL_STOP)
```

#### 服务卸载 (`uninstall_service`)
```python
def uninstall_service(service_key):
    """使用 win32service API 卸载服务"""
    scm_handle = win32service.OpenSCManager(None, None, win32con.GENERIC_WRITE)
    service_handle = win32service.OpenService(scm_handle, svc['name'], win32con.DELETE)
    win32service.DeleteService(service_handle)
```

### 3. 增强功能

#### a) PID 跟踪
```python
def get_service_pid(service_name):
    """获取服务进程 ID"""
    # 使用 sc queryex 获取 PID
    # 用于验证服务重启是否成功
```

#### b) 端口监听检查
```python
def check_port_listening(port):
    """检查端口是否在监听"""
    # 使用 socket 连接测试
    # 验证服务是否真正可用
```

#### c) 状态等待机制
```python
def wait_for_service_state(service_name, desired_state, timeout=30):
    """等待服务达到指定状态"""
    # 轮询服务状态直到达到目标或超时
    # 确保操作完成后再继续
```

#### d) 彩色控制台输出
```python
class Colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    # ... 提供更好的可视化效果
```

### 4. 参考代码的应用

#### 参考1: win32serviceutil.ServiceFramework
- 用于理解 Windows 服务的基本结构
- 服务脚本的安装/启动/停止机制
- 用于服务管理脚本的 `HandleCommandLine` 模式

#### 参考2: win32service 直接 API
- `OpenSCManager` / `CloseServiceHandle` - 服务控制管理器操作
- `OpenService` / `DeleteService` - 服务操作
- `QueryServiceStatus` - 状态查询
- `StartService` - 启动服务
- `ControlService` - 控制服务(停止等)
- `CreateService` - 创建新服务(用于手动注册模式)

### 5. 与 PowerShell/Batch 版本的对比

| 特性 | Python 版本 | PowerShell 版本 | Batch 版本 |
|------|-------------|-----------------|------------|
| API 使用 | win32service 原生 API | PowerShell cmdlets | sc.exe 命令 |
| 错误处理 | 精确的异常处理 | try-catch | 错误代码判断 |
| 状态查询 | 直接 API 调用 | Get-Service | sc query |
| PID 跟踪 | ✓ | ✓ | ✗ |
| 端口检查 | ✓ | ✓ | ✓ |
| 彩色输出 | ✓ | ✓ | ✗ |
| 跨平台 | ✓ | Windows only | Windows only |
| 权限检查 | ✓ | ✓ | ✓ |

## 使用方法

### 基本命令

```bash
# 查看帮助
python scripts\service_controller.py help

# 查询所有服务状态
python scripts\service_controller.py status

# 查询单个服务状态
python scripts\service_controller.py status admin

# 启动所有服务
python scripts\service_controller.py start

# 启动单个服务
python scripts\service_controller.py start admin

# 停止服务
python scripts\service_controller.py stop main

# 重启服务
python scripts\service_controller.py restart thumbnail

# 安装所有服务
python scripts\service_controller.py install

# 卸载服务
python scripts\service_controller.py uninstall

# 安装单个服务
python scripts\service_controller.py install-one admin

# 卸载单个服务
python scripts\service_controller.py uninstall-one main
```

### 测试验证

```bash
# 测试状态查询
python scripts\service_controller.py status

# 预期输出:
# - 显示所有三个服务的状态
# - PID 信息
# - 端口监听状态
# - 启动类型
# - 统计摘要
```

## 优势

1. **更精确的控制**: 直接使用 win32service API,避免命令行工具的限制
2. **更好的错误处理**: 精确捕获和处理异常
3. **更快的执行**: 不需要创建子进程
4. **更易维护**: 纯 Python 实现,无需依赖外部命令
5. **更丰富的功能**: PID 跟踪、端口检查、状态等待等
6. **更好的输出**: 彩色控制台输出,易于识别

## 注意事项

1. **管理员权限**: 所有操作(除 status 外)都需要管理员权限
2. **依赖包**: 需要 pywin32 包
   ```bash
   pip install pywin32
   ```
3. **服务脚本**: 依赖现有的服务包装器脚本(admin_service.py, main_service.py, thumbnail_service_win.py)
4. **安装模式**: 仍然使用服务脚本自带的 install 模式,但卸载使用 win32service API

## 完整示例

### 重启管理服务并验证

```bash
# 查看当前状态
python scripts\service_controller.py status admin

# 重启服务
python scripts\service_controller.py restart admin

# 验证 PID 变化和端口监听
python scripts\service_controller.py status admin
```

### 批量操作

```bash
# 安装所有服务
python scripts\service_controller.py install

# 启动所有服务
python scripts\service_controller.py start

# 验证所有服务状态
python scripts\service_controller.py status
```

## 未来改进建议

1. **日志记录**: 添加详细的日志记录功能
2. **配置文件**: 从配置文件读取服务列表
3. **依赖管理**: 支持服务依赖关系
4. **健康检查**: 更深入的服务健康检查
5. **自动恢复**: 服务崩溃时自动重启
6. **性能监控**: 资源使用情况监控

## 总结

新的 Python 版本通过直接使用 win32service API,提供了:
- 更精确的服务控制
- 更好的错误处理
- 更丰富的功能特性
- 更优秀的用户体验

这个优化版本充分利用了参考代码中的两种模式:
1. win32serviceutil.ServiceFramework - 用于服务脚本
2. win32service 原生 API - 用于服务控制

为 DPlayer 项目提供了强大而灵活的服务管理能力。
