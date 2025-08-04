"""Wan model management."""

import torch
from pathlib import Path
from typing import Optional
from PIL import Image
import cv2
import numpy as np

from diffusers import WanImageToVideoPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

from ..core.config import get_settings
from ..core.logging import app_logger as logger


class ImageProcessor:
    """Custom image processor to replace ModularPipeline."""
    
    def __init__(self):
        self.logger = logger
    
    def __call__(self, image, max_area: int = 901120, output: str = "processed_image"):
        """Process image with resizing and cropping."""
        if isinstance(image, str):
            # If image is a URL or path, load it
            if image.startswith(('http://', 'https://')):
                import requests
                from io import BytesIO
                response = requests.get(image)
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(image)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get original dimensions
        original_width, original_height = image.size
        original_area = original_width * original_height
        
        # Calculate new dimensions if area exceeds max_area
        if original_area > max_area:
            scale_factor = (max_area / original_area) ** 0.5
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Ensure dimensions are divisible by 8 (common requirement for video models)
            new_width = (new_width // 8) * 8
            new_height = (new_height // 8) * 8
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logger.info(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
        else:
            # Still ensure dimensions are divisible by 8
            new_width = (original_width // 8) * 8
            new_height = (original_height // 8) * 8
            if new_width != original_width or new_height != original_height:
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.logger.info(f"Adjusted image dimensions to {new_width}x{new_height} (divisible by 8)")
        
        return image


class WanVideoModel:
    """Wan video generation model wrapper."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logger
        self.pipe: Optional[WanImageToVideoPipeline] = None
        self.image_processor: Optional[ImageProcessor] = None
        self.device = self.settings.device if torch.cuda.is_available() else "cpu"
        
        # Set dtype
        if self.settings.dtype == "bfloat16":
            self.dtype = torch.bfloat16
        elif self.settings.dtype == "float16":
            self.dtype = torch.float16
        else:
            self.dtype = torch.float32
    
    async def load_model(self):
        """Load the Wan model."""
        try:
            self.logger.info("Loading Wan2.2 model...")
            
            model_path = Path(self.settings.model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"Model path does not exist: {model_path}")
            
            # Load VAE
            self.logger.info("Loading VAE...")
            vae = AutoencoderKLWan.from_pretrained(
                str(model_path),
                subfolder="vae",
                torch_dtype=torch.float32
            )
            
            # Load pipeline
            self.logger.info("Loading pipeline...")
            self.pipe = WanImageToVideoPipeline.from_pretrained(
                str(model_path),
                vae=vae,
                torch_dtype=self.dtype
            )
            
            # Enable sequential CPU offload for memory efficiency while keeping inference on GPU
            if torch.cuda.is_available() and self.device != "cpu":
                self.pipe.enable_sequential_cpu_offload()
                self.logger.info(f"Enabled sequential CPU offload for GPU inference on device: {self.device}")
            else:
                self.logger.info("Using CPU for inference")
            
            # Initialize image processor
            self.image_processor = ImageProcessor()
            
            self.logger.info("Model loaded successfully!")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise e
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.pipe is not None and self.image_processor is not None
    
    async def generate_video(
        self,
        image: Image.Image,
        prompt: str,
        negative_prompt: str = "",
        num_frames: int = 121,
        num_inference_steps: int = 50,
        guidance_scale: float = 5.0,
        max_area: int = 901120
    ) -> np.ndarray:
        """Generate video from image and prompt."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")
        
        try:
            # Process image
            self.logger.info("Processing input image...")
            processed_image = self.image_processor(
                image=image,
                max_area=max_area,
                output="processed_image"
            )
            
            height, width = processed_image.height, processed_image.width
            self.logger.info(f"Processed image size - height: {height}, width: {width}")
            
            # Generate video
            self.logger.info("Starting video generation...")
            self.logger.info(f"Parameters: frames={num_frames}, steps={num_inference_steps}, guidance={guidance_scale}")
            
            output = self.pipe(
                image=processed_image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                height=height,
                width=width,
                num_frames=num_frames,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
            ).frames[0]
            
            self.logger.info("Video generation completed successfully!")
            return output
            
        except Exception as e:
            self.logger.error(f"Error generating video: {e}")
            raise e
    
    def export_video(self, frames: np.ndarray, output_path: str, fps: int = 24):
        """Export video frames to file."""
        try:
            export_to_video(frames, output_path, fps=fps)
            self.logger.info(f"Video exported to: {output_path}")
        except Exception as e:
            self.logger.error(f"Error exporting video: {e}")
            raise e


# Global model instance
wan_model = WanVideoModel()


def get_model() -> WanVideoModel:
    """Get the global model instance."""
    return wan_model