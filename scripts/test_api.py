#!/usr/bin/env python3
"""
测试Wan Image to Video API的脚本
"""

import requests
import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw


def test_health_check(base_url: str = "http://localhost:8000") -> bool:
    """测试健康检查接口"""
    print("Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data}")
            return data.get('model_loaded', False)
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False


def test_model_info(base_url: str = "http://localhost:8000") -> bool:
    """测试模型信息接口"""
    print("Testing model info...")
    try:
        response = requests.get(f"{base_url}/api/v1/model/info")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Model info: {data}")
            return True
        else:
            print(f"✗ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Model info error: {e}")
        return False


def create_test_image(filename: str = "test_image.jpg") -> str:
    """创建一个测试图片"""
    print(f"Creating test image: {filename}")
    
    # 创建一个简单的测试图片
    img = Image.new('RGB', (512, 512), color='lightblue')
    
    # 添加一些简单的图形
    draw = ImageDraw.Draw(img)
    
    # 画一个圆
    draw.ellipse([100, 100, 400, 400], fill='yellow', outline='orange', width=5)
    
    # 画眼睛
    draw.ellipse([180, 200, 220, 240], fill='black')
    draw.ellipse([290, 200, 330, 240], fill='black')
    
    # 画嘴巴
    draw.arc([200, 280, 310, 350], start=0, end=180, fill='black', width=5)
    
    img.save(filename)
    print(f"✓ Test image created: {filename}")
    return filename


def test_generate_video(
    image_path: str, 
    base_url: str = "http://localhost:8000",
    quick_test: bool = False
) -> bool:
    """测试视频生成接口"""
    print(f"Testing video generation with image: {image_path}")
    
    if not os.path.exists(image_path):
        print(f"✗ Image file not found: {image_path}")
        return False
    
    url = f"{base_url}/api/v1/generate_video"
    
    # 准备请求数据
    with open(image_path, "rb") as f:
        files = {"image": ("test.jpg", f, "image/jpeg")}
        
        if quick_test:
            # 快速测试参数
            data = {
                "prompt": "A happy smiling face animation, smooth movement, cheerful expression",
                "negative_prompt": "blurry, static, low quality, distorted",
                "num_frames": 25,  # 减少帧数
                "num_inference_steps": 20,  # 减少推理步数
                "guidance_scale": 5.0
            }
        else:
            # 完整测试参数
            data = {
                "prompt": "A happy smiling face animation, smooth movement, cheerful expression, high quality",
                "negative_prompt": "blurry, static, low quality, distorted, ugly, deformed",
                "num_frames": 121,
                "num_inference_steps": 50,
                "guidance_scale": 5.0
            }
        
        try:
            print("Sending request to generate video...")
            print("This may take several minutes, please wait...")
            
            timeout = 300 if quick_test else 1200  # 5分钟或20分钟超时
            response = requests.post(url, files=files, data=data, timeout=timeout)
            
            if response.status_code == 200:
                output_filename = "test_generated_video.mp4"
                with open(output_filename, "wb") as video_file:
                    video_file.write(response.content)
                print(f"✓ Video generated successfully: {output_filename}")
                print(f"  File size: {len(response.content)} bytes")
                return True
            else:
                print(f"✗ Video generation failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"✗ Request timeout ({timeout} seconds)")
            return False
        except Exception as e:
            print(f"✗ Video generation error: {e}")
            return False


def main():
    """主测试函数"""
    parser = argparse.ArgumentParser(description="测试Wan Image to Video API")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务器地址")
    parser.add_argument("--image", help="测试图片路径")
    parser.add_argument("--quick", action="store_true", help="快速测试（减少帧数和推理步数）")
    parser.add_argument("--skip-generation", action="store_true", help="跳过视频生成测试")
    
    args = parser.parse_args()
    
    print("=== Wan Image to Video API Test ===")
    print(f"Testing API at: {args.url}")
    print()
    
    # 1. 测试健康检查
    model_loaded = test_health_check(args.url)
    print()
    
    # 2. 测试模型信息
    test_model_info(args.url)
    print()
    
    if not model_loaded:
        print("Model not loaded, cannot proceed with video generation test.")
        return
    
    if args.skip_generation:
        print("Skipping video generation test as requested.")
        return
    
    # 3. 准备测试图片
    if args.image and os.path.exists(args.image):
        test_image = args.image
        print(f"Using provided test image: {test_image}")
    else:
        test_image = "test_image.jpg"
        if not os.path.exists(test_image):
            create_test_image(test_image)
        else:
            print(f"Using existing test image: {test_image}")
    
    print()
    
    # 4. 测试视频生成
    success = test_generate_video(test_image, args.url, args.quick)
    
    print()
    if success:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed.")


if __name__ == "__main__":
    main()