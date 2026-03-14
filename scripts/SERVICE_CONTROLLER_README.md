# DPlayer 服务控制脚本使用文档

## 概述

本项目提供了统一的服务控制脚本，可以方便地管理所有DPlayer Windows服务。

## 脚本文件

1. **service_controller.bat** - 批处理版本（推荐，兼容性最好）
2. **service_controller.ps1** - PowerShell版本（功能更强大，彩色输出）
3. **verify_controller.py** - 验证脚本（测试脚本和服务的状态）

## 功能

所有脚本支持以下操作：

| 操作 | 说明 | 支持的服务 |
|------|------|------------|
| `install` | 注册所有DPlayer服务到Windows | all（所有） |
| `uninstall` | 从Windows卸载所有DPlayer服务 | all（所有） |
| `start` | 启动服务 | admin, main, thumbnail, all |
| `stop` | 停止服务 | admin, main, thumbnail, all |
| `restart` | 重启服务 | admin, main, thumbnail, all |
| `status` | 查询服务状态 | admin, main, thumbnail, all |

## 服务列表

- **admin** / **DPlayer-Admin** - 管理服务（端口8080）
- **main** / **DPlayer-Main** - 主应用服务（端口80）
- **thumbnail** / **DPlayer-Thumbnail** - 缩略图服务（端口5001）

## 使用方法

### 批处理版本（推荐）

```batch
# 以管理员身份运行
scripts\service_controller.bat [操作] [服务]
```

**示例：**

```batch
# 查询所有服务状态
scripts\service_controller.bat status

# 启动所有服务
scripts\service_controller.bat start all

# 停止主应用服务
scripts\service_controller.bat stop main

# 重启管理服务
scripts\service_controller.bat restart admin

# 注册所有服务
scripts\service_controller.bat install

# 卸载所有服务
scripts\service_controller.bat uninstall
```

### PowerShell版本

```powershell
# 以管理员身份运行
.\scripts\service_controller.ps1 [操作] [服务]
```

**示例：**

```powershell
# 查询所有服务状态
.\scripts\service_controller.ps1 status

# 启动所有服务
.\scripts\service_controller.ps1 start all

# 停止主应用服务
.\scripts\service_controller.ps1 stop main

# 重启管理服务
.\scripts\service_controller.ps1 restart admin

# 注册所有服务
.\scripts\service_controller.ps1 install

# 卸载所有服务
.\scripts\service_controller.ps1 uninstall
```

## 验证脚本

运行验证脚本可以检查：
- 服务包装器脚本是否存在
- 当前服务状态
- 端口监听状态

```batch
scripts\verify_controller.py
```

验证输出示例：

```
╔══════════════════════════════╗
║                    服务控制脚本验证                   ║
╚══════════════════════════════╝

============================================================
测试服务包装器脚本
============================================================

[OK] services\admin_service.py
[OK] services\main_service.py
[OK] services\thumbnail_service_win.py

============================================================
测试当前服务状态
============================================================

[OK] DPlayer-Admin 已注册
      状态: 运行中
[OK] DPlayer-Main 已注册
      状态: 运行中
[OK] DPlayer-Thumbnail 已注册
      状态: 运行中

============================================================
测试端口监听
============================================================

[OK] 管理服务 (Admin) - 端口 8080 正在监听
[OK] 主应用服务 (Main) - 端口 80 正在监听
[OK] 缩略图服务 (Thumbnail) - 端口 5001 正在监听
```

## 管理界面集成

服务控制脚本与管理后台页面集成：

- **服务管理页面** (`http://localhost:8080/services`)
- **API端点**:
  - `GET /api/services/status` - 获取所有服务状态
  - `POST /api/services/{key}/start` - 启动指定服务
  - `POST /api/services/{key}/stop` - 停止指定服务
  - `POST /api/services/{key}/restart` - 重启指定服务

**注意**：管理后台服务自身不能被停止或重启。

## 注意事项

1. **管理员权限**：所有服务控制操作都需要管理员权限
2. **服务状态**：脚本会自动等待服务状态变更（最多30秒超时）
3. **端口验证**：启动/重启操作后会验证端口是否正确监听
4. **PID验证**：重启操作会验证PID是否变更，确保服务真正重启

## 故障排查

### 服务无法启动

1. 运行验证脚本检查服务状态：
   ```batch
   scripts\verify_controller.py
   ```

2. 检查Windows事件查看器：
   - 按 `Win+R` 输入 `eventvwr.msc`
   - 查看"Windows 日志" → "应用程序"

3. 查看服务日志：
   - `logs/admin.log` - 管理服务日志
   - `logs/app.log` - 主应用服务日志
   - `logs/thumbnail.log` - 缩略图服务日志

### 端口被占用

```batch
# 查看端口占用
netstat -ano | findstr "8080"
netstat -ano | findstr ":80"
netstat -ano | findstr ":5001"
```

如果端口被占用，运行：
```batch
scripts\service_controller.bat stop all
```

### 服务未注册

运行安装命令：
```batch
scripts\service_controller.bat install
```

## 相关脚本

- `restart_services.py` - 简单的服务重启脚本
- `install_services.bat` - 服务安装脚本
- `start_all_services.bat` - 批量启动脚本
- `stop_all_services.bat` - 批量停止脚本

## 版本信息

- **创建日期**：2026-03-14
- **最新更新**：2026-03-14（添加 Python 版本）
- **版本**：2.0
- **兼容性**：Windows 10/11 Server

## 相关文档

- **SERVICE_CONTROLLER_PYTHON.md** - Python 版本详细说明
- **SERVICE_CONTROLLER_COMPARISON.md** - 版本对比分析报告
