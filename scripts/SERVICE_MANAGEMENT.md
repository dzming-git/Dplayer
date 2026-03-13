# DPlayer 服务管理使用说明

## 统一服务控制器

所有服务管理功能现在统一使用 `service_controller.py`。

### 基本用法

```bash
# 查看帮助信息
python scripts\service_controller.py

# 操作所有服务（默认）
python scripts\service_controller.py <操作>

# 操作单个服务
python scripts\service_controller.py <操作> <服务>
```

### 可用操作

| 操作 | 说明 | 示例 |
|------|------|------|
| `install` | 注册所有DPlayer服务 | `python scripts\service_controller.py install` |
| `uninstall` | 卸载所有DPlayer服务 | `python scripts\service_controller.py uninstall` |
| `install-one` | 注册单个服务 | `python scripts\service_controller.py install-one admin` |
| `uninstall-one` | 卸载单个服务 | `python scripts\service_controller.py uninstall-one admin` |
| `start` | 启动服务 | `python scripts\service_controller.py start all` |
| `stop` | 停止服务 | `python scripts\service_controller.py stop main` |
| `restart` | 重启服务 | `python scripts\service_controller.py restart thumbnail` |
| `status` | 查询服务状态 | `python scripts\service_controller.py status` |
| `autostart-enable` | 启用开机自启动 | `python scripts\service_controller.py autostart-enable` |
| `autostart-disable` | 禁用开机自启动 | `python scripts\service_controller.py autostart-disable main` |
| `autostart-status` | 查看开机自启动状态 | `python scripts\service_controller.py autostart-status` |

### 服务列表

| 服务标识 | 服务名称 | 端口 | 说明 |
|---------|---------|------|------|
| `admin` | DPlayer-Admin | 8080 | 管理面板服务 |
| `main` | DPlayer-Main | 80 | 主应用服务 |
| `thumbnail` | DPlayer-Thumbnail | 5001 | 缩略图服务 |
| `all` | 所有服务 | - | 操作所有服务（默认） |

### 常用场景

#### 1. 首次安装服务

```bash
# 以管理员身份运行
python scripts\service_controller.py install
```

#### 2. 启动所有服务

```bash
python scripts\service_controller.py start all
```

#### 3. 查看服务状态

```bash
python scripts\service_controller.py status
```

#### 4. 重启单个服务

```bash
python scripts\service_controller.py restart admin
```

#### 5. 启用开机自启动

```bash
# 启用所有服务的开机自启动
python scripts\service_controller.py autostart-enable

# 仅启用主应用服务的开机自启动
python scripts\service_controller.py autostart-enable main
```

#### 6. 查看开机自启动状态

```bash
python scripts\service_controller.py autostart-status
```

#### 7. 停止所有服务

```bash
python scripts\service_controller.py stop all
```

#### 8. 完全卸载服务

```bash
python scripts\service_controller.py uninstall
```

### 其他实用脚本

| 脚本 | 用途 |
|------|------|
| `start_all_services.bat` | 启动所有服务 |
| `stop_all_services.bat` | 停止所有服务 |
| `clean_all_dplayer.bat` | 清理所有DPlayer服务 |
| `clean_all_dplayer.ps1` | PowerShell版清理脚本 |
| `kill_ports.py` | 清理被占用的端口 |
| `migrate_db.py` | 数据库迁移 |

### 注意事项

1. **需要管理员权限**：安装、卸载、启动、停止、重启服务都需要管理员权限
2. **服务依赖**：缩略图服务依赖于主应用服务，建议先启动主应用
3. **端口占用**：启动前确保端口没有被其他程序占用
4. **开机自启动**：生产环境建议启用，开发环境建议禁用手动控制

### 管理后台访问

服务启动后，可以通过管理后台进行可视化管理：

- **管理后台**: http://localhost:8080/admin
- **主应用**: http://localhost

在管理后台的"服务管理"页面可以：
- 查看所有服务的运行状态
- 启动、停止、重启服务
- 查看服务详细信息（PID、端口等）
