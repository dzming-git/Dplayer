# 依赖安装指南

## Windows 系统

### 方法1：使用安装脚本（推荐）

1. 双击运行 `install_dependencies.bat`
2. 等待安装完成
3. 按照提示启动服务器

### 方法2：手动安装

#### 步骤1：升级 pip
```bash
python -m pip install --upgrade pip
```

#### 步骤2：使用国内镜像安装（推荐）
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤3：验证安装
```bash
python -c "import flask, cv2, PIL; print('安装成功')"
```

### 常见问题

#### 问题1：OpenCV 安装失败

**解决方案**：
```bash
# 尝试不同版本
pip install opencv-python==4.8.1.78
# 或
pip install opencv-python==4.9.0.80
```

#### 问题2：网络连接超时

**解决方案**：使用国内镜像源
```bash
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 问题3：权限不足

**解决方案**：以管理员身份运行命令提示符

---

## Linux 系统

### 方法1：使用安装脚本

```bash
# 添加执行权限
chmod +x install_dependencies.sh

# 运行脚本
./install_dependencies.sh
```

### 方法2：手动安装

#### 步骤1：安装系统依赖
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-dev libgl1-mesa-glx libglib2.0-0

# CentOS/RHEL
sudo yum install python3-pip python3-devel mesa-libGL glib2
```

#### 步骤2：升级 pip
```bash
python3 -m pip install --upgrade pip
```

#### 步骤3：安装 Python 依赖
```bash
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤4：验证安装
```bash
python3 -c "import flask, cv2, PIL; print('安装成功')"
```

### 常见问题

#### 问题1：缺少系统库

**解决方案**：
```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-glx

# CentOS/RHEL
sudo yum install mesa-libGL
```

#### 问题2：OpenCV 编译错误

**解决方案**：使用预编译版本
```bash
pip3 install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## macOS 系统

### 方法1：使用安装脚本

```bash
# 添加执行权限
chmod +x install_dependencies.sh

# 运行脚本
./install_dependencies.sh
```

### 方法2：手动安装

#### 步骤1：安装 Homebrew（如果未安装）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 步骤2：安装系统依赖
```bash
brew install python3
brew install libav
```

#### 步骤3：升级 pip
```bash
python3 -m pip install --upgrade pip
```

#### 步骤4：安装 Python 依赖
```bash
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 步骤5：验证安装
```bash
python3 -c "import flask, cv2, PIL; print('安装成功')"
```

---

## 国内镜像源

### 清华源
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 阿里源
```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 中科大源
```bash
pip install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple/
```

### 豆瓣源
```bash
pip install -r requirements.txt -i https://pypi.douban.com/simple/
```

---

## 配置永久镜像源

### Windows
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Linux/Mac
```bash
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 验证安装

运行以下命令验证所有依赖是否正确安装：

```bash
python -c "
import flask
import flask_sqlalchemy
import PIL
import cv2
import imageio
print('所有依赖安装成功！')
print(f'Flask: {flask.__version__}')
print(f'Pillow: {PIL.__version__}')
print(f'OpenCV: {cv2.__version__}')
print(f'ImageIO: {imageio.__version__}')
"
```

---

## 依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| Flask | 3.0.0 | Web 框架 |
| Flask-SQLAlchemy | 3.1.1 | 数据库 ORM |
| SQLAlchemy | 2.0.23 | 数据库引擎 |
| Pillow | 10.1.0 | 图像处理（GIF 生成） |
| requests | 2.31.0 | HTTP 请求 |
| opencv-python | 最新 | 视频处理（提取帧） |
| imageio | >=2.31.0 | 图像 I/O |
| imageio-ffmpeg | >=0.4.9 | 视频解码 |

---

## 故障排查

### 1. 检查 Python 版本
```bash
python --version
```
需要 Python 3.7 或更高版本

### 2. 检查 pip 版本
```bash
pip --version
```
建议使用最新版本的 pip

### 3. 重新安装特定包
```bash
pip uninstall opencv-python
pip install opencv-python -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4. 使用虚拟环境（推荐）
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 获取帮助

如果遇到安装问题：

1. 查看错误日志
2. 尝试使用不同的镜像源
3. 检查网络连接
4. 确认 Python 版本符合要求
5. 搜索错误信息寻找解决方案

---

**提示**：推荐使用虚拟环境进行开发，避免与系统包冲突。
