"""API routes for Wan Video API."""

import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from PIL import Image
import io
from typing import Optional

from ..core.config import get_settings
from ..core.logging import app_logger as logger
from ..models.wan_model import get_model, WanVideoModel
from ..utils.file_utils import validate_image_file, cleanup_file


router = APIRouter()
security = HTTPBearer()


async def verify_api_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """验证API token"""
    settings = get_settings()
    
    # 如果不需要认证，直接返回默认用户
    if not settings.require_auth:
        return "anonymous"
    
    # 需要认证但没有提供token
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 验证token
    if not settings.api_token:
        raise HTTPException(
            status_code=500,
            detail="API token not configured on server"
        )
    
    if credentials.credentials != settings.api_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return "authenticated_user"


@router.get("/health")
async def health_check(user: str = Depends(verify_api_token)):
    """Health check endpoint."""
    model = get_model()
    settings = get_settings()
    
    return {
        "status": "healthy",
        "message": "GCZMTIToVedio API is running",
        "version": "1.0.0",
        "user": user,
        "model_loaded": model.is_loaded(),
        "device": model.device,
        "model_path": settings.model_path,
        "endpoints": {
            "generate_video": "/api/v1/generate_video",
            "generate_video_from_text": "/api/v1/generate_video_from_text",
            "model_info": "/api/v1/model/info",
            "model_reload": "/api/v1/model/reload",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@router.post("/generate_video")
async def generate_video(
    image: UploadFile = File(..., description="Input image file"),
    prompt: str = Form(..., description="Text prompt for video generation"),
    negative_prompt: Optional[str] = Form(
        default="色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        description="Negative prompt"
    ),
    num_frames: Optional[int] = Form(default=None, description="Number of frames to generate"),
    num_inference_steps: Optional[int] = Form(default=None, description="Number of inference steps"),
    guidance_scale: Optional[float] = Form(default=None, description="Guidance scale"),
    max_area: Optional[int] = Form(default=None, description="Maximum area for image processing"),
    user: str = Depends(verify_api_token),
    model: WanVideoModel = Depends(get_model),
    settings = Depends(get_settings)
):
    """Generate video from image and prompt."""
    
    if not model.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Validate image file
    try:
        validate_image_file(image, settings)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Use default values if not provided
    num_frames = num_frames or settings.default_num_frames
    num_inference_steps = num_inference_steps or settings.default_num_inference_steps
    guidance_scale = guidance_scale or settings.default_guidance_scale
    max_area = max_area or settings.default_max_area
    
    try:
        # Read and process the uploaded image
        logger.info(f"Processing uploaded image: {image.filename}")
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data))
        
        # Generate video
        logger.info("Starting video generation...")
        output_frames = await model.generate_video(
            image=pil_image,
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            max_area=max_area
        )
        
        # Create output file
        output_filename = f"generated_video_{uuid.uuid4().hex}.mp4"
        
        # Use configured output directory
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        
        # Export video
        model.export_video(output_frames, str(output_path), fps=24)
        
        logger.info(f"Video generated successfully: {output_path}")
        
        # Return the video file
        return FileResponse(
            path=str(output_path),
            media_type="video/mp4",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating video: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating video: {str(e)}")


@router.post("/generate_video_from_text")
async def generate_video_from_text(
    prompt: str = Form(..., description="Text prompt for video generation"),
    negative_prompt: Optional[str] = Form(
        default="色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        description="Negative prompt"
    ),
    num_frames: Optional[int] = Form(default=None, description="Number of frames to generate"),
    num_inference_steps: Optional[int] = Form(default=None, description="Number of inference steps"),
    guidance_scale: Optional[float] = Form(default=None, description="Guidance scale"),
    height: Optional[int] = Form(default=720, description="Video height"),
    width: Optional[int] = Form(default=1280, description="Video width"),
    user: str = Depends(verify_api_token),
    model: WanVideoModel = Depends(get_model),
    settings = Depends(get_settings)
):
    """Generate video from text prompt only."""
    
    if not model.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Use default values if not provided
    num_frames = num_frames or settings.default_num_frames
    num_inference_steps = num_inference_steps or settings.default_num_inference_steps
    guidance_scale = guidance_scale or settings.default_guidance_scale
    
    try:
        # Generate video from text only
        logger.info("Starting text-to-video generation...")
        output_frames = await model.generate_video_from_text(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_frames=num_frames,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            height=height,
            width=width
        )
        
        # Create output file
        output_filename = f"generated_video_text_{uuid.uuid4().hex}.mp4"
        
        # Use configured output directory
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        
        # Export video
        model.export_video(output_frames, str(output_path), fps=24)
        
        logger.info(f"Video generated successfully: {output_path}")
        
        # Return the video file
        return FileResponse(
            path=str(output_path),
            media_type="video/mp4",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating video from text: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating video from text: {str(e)}")


@router.get("/model/info")
async def model_info(user: str = Depends(verify_api_token), model: WanVideoModel = Depends(get_model)):
    """Get model information."""
    settings = get_settings()
    
    return {
        "model_path": settings.model_path,
        "device": model.device,
        "dtype": str(model.dtype),
        "is_loaded": model.is_loaded(),
        "user": user,
        "default_settings": {
            "num_frames": settings.default_num_frames,
            "num_inference_steps": settings.default_num_inference_steps,
            "guidance_scale": settings.default_guidance_scale,
            "max_area": settings.default_max_area
        }
    }


@router.post("/model/reload")
async def reload_model(user: str = Depends(verify_api_token), model: WanVideoModel = Depends(get_model)):
    """Reload the model."""
    try:
        logger.info("Reloading model...")
        await model.load_model()
        return {"status": "success", "message": "Model reloaded successfully", "user": user}
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        raise HTTPException(status_code=500, detail=f"Error reloading model: {str(e)}")