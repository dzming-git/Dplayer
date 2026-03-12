# Git 操作指南

## 1. 安装 Git

### Windows 系统
下载并安装 Git: https://git-scm.com/download/win

安装后重启终端或命令行窗口，然后验证安装：
```bash
git --version
```

## 2. 项目已完成的配置

### .gitignore 文件已创建
已经创建了 `.gitignore` 文件，排除了：
- Python 缓存文件 (`__pycache__/`, `*.pyc`)
- 数据库文件 (`*.db`, `*.sqlite`)
- 用户配置文件 (`config.json`) ⚠️
- IDE 配置 (`.vscode/`, `.idea/`)
- 虚拟环境 (`venv/`, `env/`)
- 系统文件 (`.DS_Store`, `Thumbs.db`)
- 日志文件 (`*.log`)

### 配置文件生成逻辑
`app.py` 中的 `load_config()` 函数已经包含默认配置逻辑：
- 如果 `config.json` 不存在，会生成默认配置
- 如果 `config.json` 存在但缺少某些配置项，会合并默认配置

## 3. Git 操作命令

### 初始化仓库（如果还没初始化）
```bash
cd C:/Users/71555/Desktop/Dplayer
git init
```

### 添加文件到暂存区
```bash
git add .
```

### 查看暂存状态
```bash
git status
```

### 提交更改
```bash
git commit -m "Initial commit: Add DPlayer video player application"
```

### 配置远程仓库（如果还没配置）
```bash
git remote add origin <你的远程仓库URL>
```

### 推送到远程仓库
```bash
git branch -M main
git push -u origin main
```

### 后续更新和推送
```bash
git add .
git commit -m "Your commit message"
git push
```

## 4. 配置文件说明

### 第一次启动时
如果没有 `config.json` 文件，系统会自动生成包含以下默认值的配置：
- 扫描目录: `M:/bang`（递归扫描）
- 自动扫描启动: 开启
- 支持的视频格式: `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`
- 默认标签: 本地视频
- 默认优先级: 0

### 用户配置不上传
`config.json` 已经被添加到 `.gitignore` 中，确保：
1. 每个用户第一次启动时都会生成适合自己的默认配置
2. 用户的个人配置不会被提交到 Git 仓库
3. 保护用户隐私（扫描目录等敏感信息）
