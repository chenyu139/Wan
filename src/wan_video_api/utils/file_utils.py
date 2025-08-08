"""File utilities for Wan Video API."""

import os
from pathlib import Path
from typing import List

from fastapi import UploadFile
from PIL import Image
import io

from ..core.config import Settings
from ..core.logging import app_logger as logger


def validate_image_file(file: UploadFile, settings: Settings) -> None:
    """Validate uploaded image file."""
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > settings.max_file_size:
        raise ValueError(f"File size {file.size} exceeds maximum allowed size {settings.max_file_size}")
    
    # Check file extension
    if file.filename:
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        allowed_exts = settings.get_allowed_extensions_list()
        if file_ext not in allowed_exts:
            raise ValueError(f"File extension '{file_ext}' not allowed. Allowed extensions: {allowed_exts}")
    
    logger.info(f"File validation passed for: {file.filename}")


def cleanup_file(file_path: str) -> None:
    """Clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {e}")


def ensure_directory(directory: str) -> Path:
    """Ensure directory exists and return Path object."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    return os.path.getsize(file_path)


def is_valid_image(file_data: bytes) -> bool:
    """Check if file data represents a valid image."""
    try:
        image = Image.open(io.BytesIO(file_data))
        image.verify()
        return True
    except Exception:
        return False


def get_image_info(file_data: bytes) -> dict:
    """Get image information from file data."""
    try:
        image = Image.open(io.BytesIO(file_data))
        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height
        }
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return {}


def list_output_files(output_dir: str) -> List[dict]:
    """List files in output directory."""
    files = []
    output_path = Path(output_dir)
    
    if output_path.exists():
        for file_path in output_path.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created": file_path.stat().st_ctime,
                    "modified": file_path.stat().st_mtime
                })
    
    return sorted(files, key=lambda x: x["created"], reverse=True)