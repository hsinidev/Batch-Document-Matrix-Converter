"""
Document model & Universal Document Transcoding Matrix Data Structures.
Handles document item state, metadata attachment, target format assignments,
and output path resolution.
"""
import os
import uuid
import time
from typing import Dict, Any, Optional, List
from src.config import SUPPORTED_FORMATS, VALID_EXTENSIONS

class ConversionStatus:
    QUEUED = "Queued"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

class DocumentItem:
    """
    Represents an individual document in the transcoding batch matrix.
    """
    def __init__(self, file_path: str, target_format: str = "epub"):
        self.id = str(uuid.uuid4())[:8]
        self.file_path = os.path.abspath(file_path)
        self.filename = os.path.basename(file_path)
        self.file_size = self._get_size()
        
        # Format detection
        _, ext = os.path.splitext(file_path)
        self.input_ext = ext.lower().strip()
        self.input_format = self._detect_format(self.input_ext)
        
        self.target_format = target_format if target_format in SUPPORTED_FORMATS else "epub"
        self.status = ConversionStatus.QUEUED
        self.progress = 0  # 0 to 100
        
        # Per-document custom styling & metadata overrides
        self.metadata: Dict[str, Any] = {
            "title": os.path.splitext(self.filename)[0].replace("_", " ").replace("-", " ").title(),
            "author": "Anonymous Author",
            "publisher": "Batch Matrix Converter",
            "language": "en-US",
            "subject": "General Document",
            "rights": "All Rights Reserved",
            "cover_image": ""
        }
        
        self.custom_css_path: Optional[str] = None
        self.custom_flags: List[str] = []
        self.output_path: Optional[str] = None
        self.error_message: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    def _get_size(self) -> int:
        try:
            return os.path.getsize(self.file_path)
        except Exception:
            return 0

    def _detect_format(self, ext: str) -> str:
        clean_ext = ext.lstrip(".")
        if clean_ext in SUPPORTED_FORMATS:
            return clean_ext
        if clean_ext in ("markdown", "mdown", "mkd"):
            return "md"
        if clean_ext in ("htm", "xhtml"):
            return "html"
        if clean_ext in ("text", "log"):
            return "txt"
        return "txt"

    def formatted_size(self) -> str:
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def resolve_output_path(self, output_dir: Optional[str] = None) -> str:
        target_info = SUPPORTED_FORMATS.get(self.target_format, SUPPORTED_FORMATS["epub"])
        target_ext = target_info["ext"]
        base_name, _ = os.path.splitext(self.filename)
        
        target_folder = output_dir if output_dir and os.path.isdir(output_dir) else os.path.dirname(self.file_path)
        candidate = os.path.join(target_folder, f"{base_name}_converted{target_ext}")
        
        # Prevent overwriting input directly
        if os.path.abspath(candidate) == os.path.abspath(self.file_path):
            candidate = os.path.join(target_folder, f"{base_name}_out{target_ext}")
            
        self.output_path = candidate
        return candidate

    def update_status(self, status: str, progress: int = 0, error: Optional[str] = None):
        self.status = status
        self.progress = progress
        if error:
            self.error_message = error
        if status == ConversionStatus.PROCESSING and not self.started_at:
            self.started_at = time.time()
        elif status in (ConversionStatus.COMPLETED, ConversionStatus.FAILED, ConversionStatus.CANCELLED):
            self.completed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "input_format": self.input_format,
            "target_format": self.target_format,
            "status": self.status,
            "progress": self.progress,
            "metadata": self.metadata,
            "output_path": self.output_path,
            "error": self.error_message
        }
