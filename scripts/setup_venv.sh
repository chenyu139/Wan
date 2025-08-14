#!/bin/bash

# GCZM TI to Video API venv环境设置脚本

set -e

echo "=== GCZM TI to Video API venv环境设置 ==="
echo

# 检查python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python 3.11+"
    exit 1
fi

# 检查python版本
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python版本: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "❌ Python版本过低，需要Python 3.10+"
    exit 1
fi

echo "✅ Python版本符合要求"

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "项目目录: $PROJECT_DIR"

# 检查requirements.txt是否存在
if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "❌ requirements.txt文件不存在"
    exit 1
fi

# 创建虚拟环境
VENV_DIR="$PROJECT_DIR/venv"
echo "创建虚拟环境: $VENV_DIR"

# 如果虚拟环境已存在，询问是否重新创建
if [ -d "$VENV_DIR" ]; then
    echo "虚拟环境已存在，删除旧环境..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
echo "✅ 虚拟环境创建完成"
echo

# 激活虚拟环境
echo "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
echo "升级pip..."
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 安装依赖
echo "安装项目依赖..."
pip install -r "$PROJECT_DIR/requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 安装项目（开发模式）
echo "安装项目（开发模式）..."
cd "$PROJECT_DIR"
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple/

echo "✅ 项目安装完成"
echo

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs outputs

echo "✅ 目录创建完成"
echo

# 复制环境变量文件
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo "✅ 环境变量文件已创建: .env"
    else
        echo "⚠️  .env.example文件不存在，请手动创建.env文件"
    fi
else
    echo "✅ .env文件已存在"
fi

echo
echo "🎉 环境设置完成！"
echo
echo "使用方法:"
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 启动服务: python scripts/start_server.py"
echo "3. 测试API: python scripts/test_api.py"
echo "4. 退出虚拟环境: deactivate"
echo
echo "注意: 每次使用前都需要先激活虚拟环境！"