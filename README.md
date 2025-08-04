# Wan Image to Video API

基于Wan2.2-TI2V-5B模型的图片到视频生成API服务，使用FastAPI构建的完整工程项目。

## 项目结构

```
Wan/
├── src/
│   └── wan_video_api/
│       ├── __init__.py
│       ├── main.py              # 主应用程序
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py        # API路由
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py        # 配置管理
│       │   └── logging.py       # 日志配置
│       ├── models/
│       │   ├── __init__.py
│       │   └── wan_model.py     # 模型管理
│       └── utils/
│           ├── __init__.py
│           └── file_utils.py    # 文件工具
├── scripts/
│   ├── setup_env.sh            # 环境设置脚本
│   ├── start_server.py         # 服务启动脚本
│   └── test_api.py             # API测试脚本
├── tests/                      # 测试目录
├── docs/                       # 文档目录
├── logs/                       # 日志目录
├── outputs/                    # 输出目录
├── requirements.txt           # Python依赖配置
├── pyproject.toml             # 项目配置
├── .env.example               # 环境变量示例
└── README.md                  # 项目说明
```

## 功能特性

- 🎬 支持上传图片并根据文本提示生成视频
- 🚀 基于FastAPI构建的高性能RESTful API
- ⚙️ 支持自定义生成参数（帧数、推理步数、引导比例等）
- 🔧 完整的配置管理和日志系统
- 🐍 使用venv虚拟环境管理依赖
- 📊 自动GPU加速（如果可用）
- 🧪 包含完整的测试脚本
- 📚 自动生成API文档

## 快速开始

### 1. 环境设置

使用提供的脚本自动设置环境：

```bash
# 给脚本执行权限
chmod +x scripts/setup_venv.sh

# 运行环境设置脚本
./scripts/setup_venv.sh
```

或者手动设置：

```bash
# 创建venv虚拟环境
python3 -m venv venv

# 激活环境
source venv/bin/activate

# 安装依赖（使用清华源）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 安装项目（使用清华源）
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 创建必要目录
mkdir -p logs outputs

# 复制环境变量文件
cp .env.example .env
```

### 2. 配置环境变量

编辑 `.env` 文件，确保模型路径正确：

```bash
MODEL_PATH=/home/chenyu/.cache/modelscope/hub/models/Wan-AI/Wan2___2-TI2V-5B-Diffusers
```

### 3. 启动服务

```bash
# 激活环境
source venv/bin/activate

# 启动服务
python scripts/start_server.py
```

服务将在 `http://localhost:8000` 启动。

### 4. 测试API

```bash
# 快速测试
python scripts/test_api.py --quick

# 完整测试
python scripts/test_api.py
```

## API 接口

### 健康检查

```
GET /api/v1/health
```

返回服务状态和模型加载情况。

### 模型信息

```
GET /api/v1/model/info
```

返回模型配置信息。

### 生成视频

```
POST /api/v1/generate_video
```

**参数：**

- `image` (文件): 输入图片文件
- `prompt` (字符串): 视频生成的文本提示
- `negative_prompt` (字符串, 可选): 负面提示词
- `num_frames` (整数, 可选): 生成帧数，默认121
- `num_inference_steps` (整数, 可选): 推理步数，默认50
- `guidance_scale` (浮点数, 可选): 引导比例，默认5.0
- `max_area` (整数, 可选): 图片处理最大面积，默认901120

**返回：**

生成的MP4视频文件。

### 重新加载模型

```
POST /api/v1/model/reload
```

重新加载模型（用于模型更新后）。

## 使用示例

### 使用curl

```bash
curl -X POST "http://localhost:8000/api/v1/generate_video" \
  -F "image=@your_image.jpg" \
  -F "prompt=Summer beach vacation style, a white cat wearing sunglasses sits on a surfboard" \
  -F "num_frames=121" \
  -F "guidance_scale=5.0" \
  -o generated_video.mp4
```

### 使用Python requests

```python
import requests

url = "http://localhost:8000/api/v1/generate_video"

with open("your_image.jpg", "rb") as f:
    files = {"image": f}
    data = {
        "prompt": "Summer beach vacation style, a white cat wearing sunglasses sits on a surfboard",
        "num_frames": 121,
        "guidance_scale": 5.0
    }
    
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        with open("generated_video.mp4", "wb") as video_file:
            video_file.write(response.content)
        print("视频生成成功！")
    else:
        print(f"错误: {response.status_code} - {response.text}")
```

## 配置说明

### 环境变量

主要配置项（在 `.env` 文件中）：

```bash
# 模型配置
MODEL_PATH=/path/to/model
DEVICE=cuda
DTYPE=bfloat16

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 生成默认参数
DEFAULT_NUM_FRAMES=121
DEFAULT_NUM_INFERENCE_STEPS=50
DEFAULT_GUIDANCE_SCALE=5.0

# 文件上传限制
MAX_FILE_SIZE=50000000
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp,bmp
```

### 日志配置

日志文件位置：`logs/wan_video_api.log`

支持的日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL

## 开发指南

### 项目安装（开发模式）

```bash
source venv/bin/activate
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 代码格式化

```bash
# 安装开发依赖（使用清华源）
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 格式化代码
black src/
isort src/

# 代码检查
flake8 src/
```

### 运行测试

```bash
pytest tests/
```

## 注意事项

1. **模型路径**：确保模型文件位于正确路径：`/home/chenyu/.cache/modelscope/hub/models/Wan-AI/Wan2___2-TI2V-5B-Diffusers`
2. **GPU内存**：视频生成需要大量GPU内存，建议使用至少12GB显存的GPU
3. **生成时间**：视频生成可能需要较长时间，请耐心等待
4. **文件格式**：支持的图片格式：JPG, JPEG, PNG, WEBP, BMP
5. **虚拟环境**：务必使用venv虚拟环境，避免依赖冲突
6. **Diffusers版本**：项目使用最新的diffusers代码（从GitHub直接安装），确保兼容性和最新功能

## API文档

启动服务后，可以访问以下地址查看自动生成的API文档：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型路径是否正确
   - 确保有足够的磁盘空间和内存
   - 检查CUDA版本兼容性

2. **GPU内存不足**
   - 减少 `num_frames` 参数
   - 降低图片分辨率
   - 使用CPU模式（设置 `DEVICE=cpu`）

3. **依赖安装问题**
   - 确保使用正确的venv虚拟环境
   - 重新创建环境：`rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

4. **端口占用**
   - 更改端口：`python scripts/start_server.py --port 8001`
   - 或在 `.env` 文件中修改 `PORT` 配置

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！