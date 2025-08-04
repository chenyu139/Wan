#!/usr/bin/env python3
"""
启动Wan Image to Video API服务的脚本
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from wan_video_api.core.config import get_settings
from wan_video_api.core.logging import app_logger as logger


def check_model_path(model_path: str) -> bool:
    """检查模型路径是否存在"""
    if not os.path.exists(model_path):
        print(f"❌ 模型路径不存在: {model_path}")
        print("请确保模型已正确下载到指定位置")
        return False
    
    # 检查关键文件
    required_files = ['model_index.json']
    for file in required_files:
        file_path = os.path.join(model_path, file)
        if not os.path.exists(file_path):
            print(f"❌ 缺少必要文件: {file_path}")
            return False
    
    # 检查配置文件（可能是config.json或configuration.json）
    config_files = ['config.json', 'configuration.json']
    config_found = False
    for config_file in config_files:
        if os.path.exists(os.path.join(model_path, config_file)):
            config_found = True
            break
    
    if not config_found:
        print(f"❌ 缺少配置文件: {config_files}")
        return False
    
    print(f"✅ 模型路径验证通过: {model_path}")
    return True


def check_dependencies() -> bool:
    """检查依赖是否安装"""
    print("检查依赖包...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'torch',
        'diffusers',
        'transformers',
        'PIL',
        'loguru',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少以下依赖包: {', '.join(missing_packages)}")
        print("请运行: ./scripts/setup_venv.sh 创建虚拟环境")
        print("或激活虚拟环境后安装: pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/")
        print("手动安装单个包: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ <package_name>")
        return False
    
    print("✅ 所有依赖包已安装")
    return True


def check_gpu() -> bool:
    """检查GPU可用性"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ GPU可用: {gpu_name} (共{gpu_count}个GPU)")
            
            # 检查显存
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"   显存: {gpu_memory:.1f} GB")
            
            if gpu_memory < 10:
                print("⚠️  警告: 显存可能不足，建议至少12GB显存")
            
            return True
        else:
            print("⚠️  GPU不可用，将使用CPU（速度会很慢）")
            return False
    except Exception as e:
        print(f"❌ GPU检查失败: {e}")
        return False


def start_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 1, reload: bool = True):
    """启动服务器"""
    print(f"\n🚀 启动服务器...")
    print(f"   地址: http://{host}:{port}")
    print(f"   工作进程: {workers}")
    print(f"   API文档: http://{host}:{port}/docs")
    print("\n按 Ctrl+C 停止服务器\n")
    
    try:
        # 设置环境变量
        os.environ["HOST"] = host
        os.environ["PORT"] = str(port)
        os.environ["WORKERS"] = str(workers)
        os.environ["RELOAD"] = str(reload).lower()
        
        # 使用uvicorn启动
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "wan_video_api.main:app",
            "--host", host,
            "--port", str(port),
        ]
        
        if reload:
            cmd.append("--reload")
        else:
            cmd.extend(["--workers", str(workers)])
        
        subprocess.run(cmd, cwd=src_path)
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="启动Wan Image to Video API服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="端口号 (默认: 8000)")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数 (默认: 1)")
    parser.add_argument("--no-reload", action="store_true", help="禁用自动重载")
    parser.add_argument("--skip-checks", action="store_true", help="跳过预检查")
    
    args = parser.parse_args()
    
    print("=== Wan Image to Video API 启动器 ===")
    print()
    
    if not args.skip_checks:
        # 检查依赖
        if not check_dependencies():
            sys.exit(1)
        
        print()
        
        # 检查模型路径
        settings = get_settings()
        if not check_model_path(settings.model_path):
            sys.exit(1)
        
        print()
        
        # 检查GPU
        check_gpu()
        
        print()
    
    # 启动服务器
    start_server(
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=not args.no_reload
    )


if __name__ == "__main__":
    main()