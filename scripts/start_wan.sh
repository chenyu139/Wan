#!/bin/bash

# GCZM TI to Video API 一键启动脚本
# 基于 FLUX.1-Kontext API 启动脚本模板

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 默认配置
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8002}
DEVICE=${DEVICE:-"cuda"}
VENV_DIR="$PROJECT_ROOT/venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
ENV_FILE="$PROJECT_ROOT/.env"
LOGS_DIR="$PROJECT_ROOT/logs"
OUTPUTS_DIR="$PROJECT_ROOT/outputs"

# 解析命令行参数
RUN_ONLY=false
NO_VENV=false
NO_INSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --run-only)
            RUN_ONLY=true
            shift
            ;;
        --no-venv)
            NO_VENV=true
            shift
            ;;
        --no-install)
            NO_INSTALL=true
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --device)
            DEVICE="$2"
            shift 2
            ;;
        -h|--help)
            echo "GCZM TI to Video API 启动脚本"
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --run-only      跳过环境检查和依赖安装，直接启动服务"
            echo "  --no-venv       不使用虚拟环境"
            echo "  --no-install    跳过依赖安装"
            echo "  --host HOST     指定服务器主机地址 (默认: 0.0.0.0)"
            echo "  --port PORT     指定服务器端口 (默认: 8002)"
            echo "  --device DEVICE 指定设备 (默认: cuda)"
            echo "  -h, --help      显示此帮助信息"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# 检查Python版本
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_info "检测到 Python 版本: $PYTHON_VERSION"
    
    # 检查Python版本是否满足要求 (>= 3.8)
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python 版本满足要求"
    else
        log_error "Python 版本过低，需要 >= 3.8"
        exit 1
    fi
}

# 检查NVIDIA GPU
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        log_info "检测到 NVIDIA GPU:"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | while read line; do
            log_info "  $line MB"
        done
        log_success "GPU 检查通过"
    else
        log_warning "未检测到 NVIDIA GPU 或 nvidia-smi 命令"
        if [[ "$DEVICE" == "cuda" ]]; then
            log_warning "将使用 CPU 模式"
            DEVICE="cpu"
        fi
    fi
}

# 创建并激活虚拟环境
setup_venv() {
    if [[ "$NO_VENV" == "true" ]]; then
        log_info "跳过虚拟环境设置"
        return
    fi
    
    if [[ ! -d "$VENV_DIR" ]]; then
        log_info "创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        log_success "虚拟环境创建完成"
    fi
    
    log_info "激活虚拟环境..."
    source "$VENV_DIR/bin/activate"
    
    # 配置清华PyPI镜像源
    log_info "配置 PyPI 镜像源..."
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn
    
    # 升级pip
    log_info "升级 pip..."
    pip install --upgrade pip
    
    log_success "虚拟环境设置完成"
}

# 安装依赖
install_dependencies() {
    if [[ "$NO_INSTALL" == "true" ]]; then
        log_info "跳过依赖安装"
        return
    fi
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_error "requirements.txt 文件不存在: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    log_info "安装项目依赖..."
    pip install -r "$REQUIREMENTS_FILE"
    
    # 检查并安装可能缺失的包
    log_info "检查额外依赖..."
    
    # 检查 ftfy
    if ! python3 -c "import ftfy" 2>/dev/null; then
        log_info "安装 ftfy..."
        pip install ftfy
    fi
    
    log_success "依赖安装完成"
}

# 创建必要目录
setup_directories() {
    log_info "创建必要目录..."
    
    mkdir -p "$LOGS_DIR"
    mkdir -p "$OUTPUTS_DIR"
    
    log_success "目录创建完成"
}

# 检查环境配置
check_env_config() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning ".env 文件不存在，请确保已正确配置环境变量"
        if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
            log_info "可以参考 .env.example 文件创建 .env 配置"
        fi
        return
    fi
    
    log_info "检查环境配置..."
    
    # 检查模型路径
    if grep -q "MODEL_PATH" "$ENV_FILE"; then
        MODEL_PATH=$(grep "MODEL_PATH" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
        if [[ -n "$MODEL_PATH" && -d "$MODEL_PATH" ]]; then
            log_success "模型路径验证通过: $MODEL_PATH"
        else
            log_warning "模型路径可能不存在: $MODEL_PATH"
        fi
    else
        log_warning "未在 .env 中找到 MODEL_PATH 配置"
    fi
}

# 启动服务器
start_server() {
    log_info "启动 GCZM TI to Video API 服务器..."
    log_info "配置信息:"
    log_info "  主机: $HOST"
    log_info "  端口: $PORT"
    log_info "  设备: $DEVICE"
    log_info "  项目根目录: $PROJECT_ROOT"
    
    cd "$PROJECT_ROOT"
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    export DEVICE="$DEVICE"
    
    # 启动服务器
    log_success "服务器启动中..."
    echo -e "${GREEN}访问地址: http://$HOST:$PORT${NC}"
    echo -e "${GREEN}API文档: http://$HOST:$PORT/docs${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
    echo ""
    
    if [[ "$NO_VENV" != "true" && -f "$VENV_DIR/bin/activate" ]]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # 使用 uvicorn 启动
    uvicorn gczm_ti_to_video.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --app-dir "$PROJECT_ROOT/src"
}

# 主函数
main() {
    echo -e "${BLUE}=== GCZM TI to Video API 启动脚本 ===${NC}"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    if [[ "$RUN_ONLY" != "true" ]]; then
        log_info "开始环境检查和设置..."
        check_python
        check_gpu
        setup_venv
        install_dependencies
        setup_directories
        check_env_config
        echo ""
    else
        log_info "快速启动模式，跳过环境检查..."
        if [[ "$NO_VENV" != "true" && -f "$VENV_DIR/bin/activate" ]]; then
            source "$VENV_DIR/bin/activate"
        fi
    fi
    
    start_server
}

# 错误处理
trap 'log_error "脚本执行被中断"; exit 1' INT TERM

# 执行主函数
main "$@"