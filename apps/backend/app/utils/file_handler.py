"""
File handling utilities for uploading, validating, and managing files.
"""
import os
import uuid
import aiofiles
import magic
from pathlib import Path
from typing import Optional, Tuple, List
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class FileHandler:
    """Handle file upload, validation, storage and deletion."""
    
    # Extended allowed types
    ALLOWED_VIDEO_TYPES = [
        "video/mp4", "video/webm", "video/quicktime", 
        "video/x-msvideo", "video/x-matroska"
    ]
    ALLOWED_DOCUMENT_TYPES = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "application/zip",
        "application/x-rar-compressed",
    ]
    ALLOWED_IMAGE_TYPES = [
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"
    ]
    
    def __init__(self):
        self.storage_path = Path(settings.STORAGE_PATH)
        self.max_video_size = settings.MAX_VIDEO_SIZE_MB * 1024 * 1024  # Convert to bytes
        self.max_document_size = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
        self.max_image_size = 10 * 1024 * 1024  # 10MB for images
        
        # Ensure storage directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist."""
        directories = [
            self.storage_path,
            self.storage_path / "videos",
            self.storage_path / "documents",
            self.storage_path / "images",
            self.storage_path / "submissions",
            self.storage_path / "thumbnails",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_mime_type(self, file_content: bytes) -> str:
        """Detect MIME type from file content."""
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception:
            return "application/octet-stream"
    
    def _get_file_extension(self, filename: str, mime_type: str) -> str:
        """Get file extension from filename or MIME type."""
        # Try to get from filename first
        if filename and "." in filename:
            return filename.rsplit(".", 1)[-1].lower()
        
        # Fallback to MIME type mapping
        mime_to_ext = {
            "video/mp4": "mp4",
            "video/webm": "webm",
            "video/quicktime": "mov",
            "application/pdf": "pdf",
            "application/msword": "doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/gif": "gif",
            "image/webp": "webp",
            "text/plain": "txt",
            "text/csv": "csv",
        }
        return mime_to_ext.get(mime_type, "bin")
    
    def _generate_unique_filename(self, original_filename: str, mime_type: str) -> str:
        """Generate a unique filename preserving extension."""
        ext = self._get_file_extension(original_filename, mime_type)
        unique_id = uuid.uuid4().hex[:16]
        return f"{unique_id}.{ext}"
    
    def _get_file_category(self, mime_type: str) -> str:
        """Determine file category from MIME type."""
        if mime_type in self.ALLOWED_VIDEO_TYPES:
            return "videos"
        elif mime_type in self.ALLOWED_IMAGE_TYPES:
            return "images"
        elif mime_type in self.ALLOWED_DOCUMENT_TYPES:
            return "documents"
        else:
            return "documents"  # Default to documents
    
    def validate_file(
        self, 
        content: bytes, 
        filename: str,
        allowed_types: Optional[List[str]] = None,
        max_size: Optional[int] = None
    ) -> Tuple[str, int]:
        """
        Validate file content and return (mime_type, size).
        Raises HTTPException if validation fails.
        """
        # Check file size
        file_size = len(content)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        # Detect MIME type
        mime_type = self._get_mime_type(content)
        
        # Determine allowed types if not specified
        if allowed_types is None:
            allowed_types = (
                self.ALLOWED_VIDEO_TYPES + 
                self.ALLOWED_DOCUMENT_TYPES + 
                self.ALLOWED_IMAGE_TYPES
            )
        
        # Check MIME type
        if mime_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{mime_type}' not allowed. Allowed types: {allowed_types}"
            )
        
        # Determine max size based on file type if not specified
        if max_size is None:
            if mime_type in self.ALLOWED_VIDEO_TYPES:
                max_size = self.max_video_size
            elif mime_type in self.ALLOWED_IMAGE_TYPES:
                max_size = self.max_image_size
            else:
                max_size = self.max_document_size
        
        # Check size
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size / (1024*1024):.2f}MB) exceeds maximum allowed ({max_mb:.0f}MB)"
            )
        
        return mime_type, file_size
    
    async def save_file(
        self,
        file: UploadFile,
        subdirectory: Optional[str] = None,
        allowed_types: Optional[List[str]] = None,
        max_size: Optional[int] = None
    ) -> dict:
        """
        Save uploaded file to storage.
        Returns dict with file_url, file_name, file_size, mime_type.
        """
        # Read file content
        content = await file.read()
        
        # Validate file
        mime_type, file_size = self.validate_file(
            content, 
            file.filename, 
            allowed_types, 
            max_size
        )
        
        # Generate unique filename
        unique_filename = self._generate_unique_filename(file.filename, mime_type)
        
        # Determine storage subdirectory
        if subdirectory:
            save_dir = self.storage_path / subdirectory
        else:
            category = self._get_file_category(mime_type)
            save_dir = self.storage_path / category
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Full path for saving
        file_path = save_dir / unique_filename
        
        # Save file asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Generate relative URL for storage
        relative_path = file_path.relative_to(self.storage_path)
        file_url = f"/storage/{relative_path}"
        
        return {
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "storage_path": str(file_path),
        }
    
    async def save_material_file(self, file: UploadFile, lesson_id: str) -> dict:
        """Save a material file (video/document/image) for a lesson."""
        return await self.save_file(
            file,
            subdirectory=f"materials/{lesson_id}",
            allowed_types=self.ALLOWED_VIDEO_TYPES + self.ALLOWED_DOCUMENT_TYPES + self.ALLOWED_IMAGE_TYPES
        )
    
    async def save_submission_file(self, file: UploadFile, assignment_id: str, user_id: str) -> dict:
        """Save a submission file for an assignment."""
        return await self.save_file(
            file,
            subdirectory=f"submissions/{assignment_id}/{user_id}",
            allowed_types=self.ALLOWED_DOCUMENT_TYPES + self.ALLOWED_IMAGE_TYPES,
            max_size=self.max_document_size
        )
    
    async def save_thumbnail(self, file: UploadFile, entity_type: str, entity_id: str) -> dict:
        """Save a thumbnail image."""
        return await self.save_file(
            file,
            subdirectory=f"thumbnails/{entity_type}/{entity_id}",
            allowed_types=self.ALLOWED_IMAGE_TYPES,
            max_size=self.max_image_size
        )
    
    def delete_file(self, file_url: str) -> bool:
        """Delete a file by its URL. Returns True if deleted."""
        if not file_url:
            return False
        
        # Convert URL to path
        # file_url format: /storage/path/to/file.ext
        try:
            relative_path = file_url.replace("/storage/", "")
            file_path = self.storage_path / relative_path
            
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
        except Exception:
            pass
        
        return False
    
    def get_file_path(self, file_url: str) -> Optional[Path]:
        """Get the actual file path from URL."""
        if not file_url:
            return None
        
        try:
            relative_path = file_url.replace("/storage/", "")
            file_path = self.storage_path / relative_path
            if file_path.exists():
                return file_path
        except Exception:
            pass
        
        return None


# Singleton instance
file_handler = FileHandler()
