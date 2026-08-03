import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO
from pathlib import Path
from dataclasses import dataclass, asdict
import logging

try:
    import PyPDF2
    from PyPDF2 import PdfReader
    HAS_PYPDF2 = True
except ImportError:
    PyPDF2 = None
    PdfReader = None
    HAS_PYPDF2 = False

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    success: bool
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    word_count: int = 0
    char_count: int = 0
    page_count: int = 0
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DocumentProcessor:
    """Document processor for extracting text and metadata from various file types."""

    SUPPORTED_TYPES = {
        "text/plain": "_process_text",
        "application/pdf": "_process_pdf",
        "text/markdown": "_process_text",
        "application/json": "_process_text",
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_file(self, file_path: str, mime_type: Optional[str] = None) -> ProcessingResult:
        """Process a file and extract content and metadata."""
        path = Path(file_path)
        if not path.exists():
            return ProcessingResult(success=False, error=f"File not found: {file_path}")

        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "text/plain"

        try:
            checksum = self._compute_checksum(file_path)
            method_name = self.SUPPORTED_TYPES.get(mime_type, "_process_text")
            method = getattr(self, method_name)
            result = method(file_path)
            result.checksum = checksum
            return result
        except Exception as exc:
            self.logger.error("Error processing file %s: %s", file_path, exc)
            return ProcessingResult(success=False, error=str(exc))

    def process_bytes(self, data: bytes, filename: str, mime_type: Optional[str] = None) -> ProcessingResult:
        """Process raw bytes content."""
        if mime_type is None:
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type is None:
                mime_type = "text/plain"

        try:
            checksum = hashlib.sha256(data).hexdigest()
            if mime_type == "application/pdf" and HAS_PYPDF2:
                import io
                reader = PdfReader(io.BytesIO(data))
                content = ""
                for page in reader.pages:
                    content += page.extract_text() or ""
                result = ProcessingResult(
                    success=True,
                    content=content,
                    metadata={"page_count": len(reader.pages), "filename": filename},
                    word_count=len(content.split()),
                    char_count=len(content),
                    page_count=len(reader.pages),
                )
            else:
                try:
                    content = data.decode("utf-8")
                except UnicodeDecodeError:
                    content = data.decode("latin-1", errors="replace")
                result = ProcessingResult(
                    success=True,
                    content=content,
                    metadata={"filename": filename},
                    word_count=len(content.split()),
                    char_count=len(content),
                )
            result.checksum = checksum
            return result
        except Exception as exc:
            self.logger.error("Error processing bytes for %s: %s", filename, exc)
            return ProcessingResult(success=False, error=str(exc))

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a file without full processing."""
        path = Path(file_path)
        if not path.exists():
            return {}

        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(file_path)
        return {
            "filename": path.name,
            "file_size": stat.st_size,
            "mime_type": mime_type or "application/octet-stream",
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": path.suffix.lower(),
        }

    def _process_text(self, file_path: str) -> ProcessingResult:
        """Process plain text files."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return ProcessingResult(
            success=True,
            content=content,
            metadata=self.extract_metadata(file_path),
            word_count=len(content.split()),
            char_count=len(content),
        )

    def _process_pdf(self, file_path: str) -> ProcessingResult:
        """Process PDF files."""
        if not HAS_PYPDF2:
            self.logger.warning("PyPDF2 not available; falling back to text processing")
            return self._process_text(file_path)
        try:
            reader = PdfReader(file_path)
            content = ""
            for page in reader.pages:
                content += page.extract_text() or ""
            metadata = self.extract_metadata(file_path)
            metadata["page_count"] = len(reader.pages)
            return ProcessingResult(
                success=True,
                content=content,
                metadata=metadata,
                word_count=len(content.split()),
                char_count=len(content),
                page_count=len(reader.pages),
            )
        except Exception as exc:
            return ProcessingResult(success=False, error=f"PDF processing error: {exc}")

    def _compute_checksum(self, file_path: str) -> str:
        """Compute SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
