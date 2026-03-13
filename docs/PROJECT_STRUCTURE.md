# 项目目录结构说明

## 根目录

根目录仅包含应用入口文件和项目文档，极简化。

```
Dplayer/
├── app.py                      # 主Flask应用入口
├── admin_app.py                # 管理后台Flask应用入口
├── README.md                   # 项目说明文档
├── requirements.txt            # Python依赖列表
└── .gitignore                  # Git忽略规则
```

## 代码模块结构

### core/ - 核心模块
存放核心数据库模型和基础组件。

```
core/
├── __init__.py                 # Python包初始化
└── models.py                   # 数据库模型定义
    ├── Video                   # 视频模型
    ├── Tag                     # 标签模型
    ├── Playlist                # 播放列表模型
    └── ... (其他模型)
```

### api/ - API接口模块
存放所有API接口端点。

```
api/
├── __init__.py                 # Python包初始化
├── async_thumbnail_api.py      # 异步缩略图API
└── playlist_api.py            # 播放列表API
```

### services/ - 服务模块
存放业务逻辑和服务模块。

```
services/
├── __init__.py                 # Python包初始化
├── thumbnail_service.py        # 缩略图服务
├── thumbnail_service_client.py # 缩略图客户端
├── playlist_manager.py         # 播放列表管理器
└── resource_monitor.py         # 资源监控
```

### utils/ - 工具类模块
存放工具类和辅助函数。

```
utils/
├── __init__.py                 # Python包初始化
├── config_manager.py           # 配置管理器
├── port_manager.py             # 端口管理器
└── mount_config.py             # 挂载配置
```

## 子目录结构

### config/ - 配置模块目录
存放配置相关文件和模块。

```
config/
├── config.json                  # 用户配置（.gitignore忽略）
├── mounts_config.example.json   # Docker挂载配置示例
├── test_monitor_config.example.json  # 监控配置示例
├── celery_config.py            # Celery配置
└── tasks.py                    # Celery异步任务
```

### docker/ - Docker配置目录
存放Docker相关配置文件。

```
docker/
├── docker-compose.yml           # 标准Docker Compose配置
├── docker-compose.flexible.yml  # 灵活部署配置
└── docker-compose.multi.yml     # 多文件夹挂载配置
```

### docs/ - 文档目录
存放项目文档、报告和说明。

```
docs/
├── DIRECTORY_OPTIMIZATION_REPORT.md  # 目录优化报告
├── FEATURES.md                         # 功能说明
├── TEST_CASES.md                      # 测试用例文档
└── ... (其他文档)
```

### instance/ - 运行时数据目录
存放Flask应用的运行时数据，包括数据库文件。

```
instance/
├── dplayer.db                  # 主数据库
├── videos.db                   # 视频数据库
└── main_app.pid                # 主应用进程ID文件
```

**注意**：instance目录已在.gitignore中，不会被提交到Git。

### scripts/ - 启动脚本目录
存放应用的启动、停止、重启等运维脚本。

```
scripts/
├── start.bat                    # Windows启动脚本
├── start.sh                     # Linux/Mac启动脚本
├── start_admin.bat              # 管理后台启动脚本
├── stop_all_services.bat        # 停止所有服务
├── run_tests.bat               # 运行测试
└── ... (其他脚本)
```

### tests/ - 测试脚本目录
存放所有测试脚本和测试文档。

```
tests/
├── test_db.py                   # 数据库测试
├── test_admin_apis.py          # 管理API测试
├── test_priority_features.py   # 优先功能测试
├── check_test_coverage.py      # 测试覆盖率检查
└── ... (其他测试)
```

### static/ - 静态资源目录
存放静态文件，包括缩略图、CSS、JS等。

```
static/
├── thumbnails/                  # 缩略图（941个GIF文件）
│   └── *.gif
├── css/                         # 样式文件
│   ├── style.css
│   └── ...
├── js/                          # JavaScript文件
│   └── ...
└── html/                        # 静态HTML文件
    └── ...
```

### templates/ - 模板目录
存放Flask模板文件（HTML模板）。

```
templates/
├── index.html                  # 主页模板
├── playlist.html               # 播放列表模板
└── ... (其他模板)
```

### archive/ - 归档目录
存放临时文件、过时文档、测试结果等，不会提交到Git。

```
archive/
├── *.txt                       # 测试结果、临时文件
├── *.py                        # 过时的测试脚本
├── *.log                       # 日志文件
└── ... (其他归档文件)
```

### logs/ - 日志目录
存放应用运行日志。

```
logs/
├── app.log                     # 应用日志
├── admin.log                   # 管理后台日志
└── ... (其他日志)
```

### diagnostics/ - 诊断脚本目录
存放诊断和调试脚本。

```
diagnostics/
├── diagnose_port.py            # 端口诊断
├── diagnose_db.py              # 数据库诊断
└── ... (其他诊断脚本)
```

## 项目特点

### 1. 根目录极简化
- 只包含4个文件（2个应用入口 + 2个项目文档）
- 没有任何零散的代码文件
- 清晰的项目入口点

### 2. 代码模块化
- core/ - 核心数据模型
- api/ - API接口层
- services/ - 业务逻辑层
- utils/ - 工具类层
- config/ - 配置模块

### 3. 分类清晰
- 配置文件独立在config/
- Docker文件独立在docker/
- 文档统一在docs/
- 脚本统一在scripts/
- 测试统一在tests/

### 4. 符合最佳实践
- Flask instance目录用于运行时数据
- 符合Python包结构规范
- 清晰的分层架构
- 易于团队协作和部署

### 4. Git管理规范
- 运行时数据（instance/）不提交
- 用户配置（config/config.json）不提交
- 归档文件（archive/）不提交
- 只提交核心代码和必要文档

## 使用说明

### 启动应用
```bash
# Windows
python app.py

# 或使用脚本
scripts/start.bat
```

### 运行测试
```bash
# Windows
scripts/run_tests.bat

# 或直接运行
python tests/test_db.py
```

### Docker部署
```bash
# 使用Docker Compose
cd docker
docker-compose up -d
```

### 配置应用
```bash
# 编辑配置文件
# Windows: notepad config\config.json
# Linux/Mac: nano config/config.json
```

## 注意事项

1. **配置文件**：config.json是用户配置，不会被Git跟踪
2. **数据库文件**：instance目录下的数据库文件不会提交
3. **日志文件**：logs目录下的日志文件不会提交
4. **归档文件**：archive目录用于临时存储，不会提交

## 维护建议

1. 新增功能时，将核心代码放在根目录
2. 测试脚本放在tests/目录
3. 文档放在docs/目录
4. 启动脚本放在scripts/目录
5. 定期清理archive/目录中的临时文件
