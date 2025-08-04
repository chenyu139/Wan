"""Configuration management for Wan Video API."""

import os
from pathlib import Path
from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Model Configuration
    model_path: str = Field(
        default="/home/chenyu/.cache/modelscope/hub/models/Wan-AI/Wan2___2-TI2V-5B-Diffusers",
        description="Path to the Wan model"
    )
    device: str = Field(default="cuda", description="Device to run the model on")
    dtype: str = Field(default="bfloat16", description="Data type for model")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    reload: bool = Field(default=True, description="Enable auto-reload")
    
    # Generation Defaults
    default_num_frames: int = Field(default=121, description="Default number of frames")
    default_num_inference_steps: int = Field(default=50, description="Default inference steps")
    default_guidance_scale: float = Field(default=5.0, description="Default guidance scale")
    default_max_area: int = Field(default=901120, description="Default max area for image processing")
    
    # File Upload
    max_file_size: int = Field(default=50_000_000, description="Maximum file size in bytes")
    allowed_extensions: List[str] = Field(
        default=["jpg", "jpeg", "png", "webp", "bmp"],
        description="Allowed file extensions"
    )
    
    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default="logs/wan_video_api.log", description="Log file path")
    
    # Output
    output_dir: str = Field(default="outputs", description="Output directory")
    temp_dir: str = Field(default="/tmp", description="Temporary directory")
    cleanup_temp_files: bool = Field(default=True, description="Cleanup temporary files")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def ensure_directories():
    """Ensure required directories exist."""
    directories = [
        settings.output_dir,
        Path(settings.log_file).parent if settings.log_file else None,
    ]
    
    for directory in directories:
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)