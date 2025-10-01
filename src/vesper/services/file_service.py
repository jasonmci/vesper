"""
File management service for loading and saving documents.
"""

import json
from pathlib import Path
from typing import Optional

from vesper.models.document import Document


class FileService:
    """Service for file operations."""

    @staticmethod
    def load_document(file_path: str) -> Optional[Document]:
        """Load a document from file."""
        path = Path(file_path)

        if not path.exists():
            return None

        try:
            if path.suffix.lower() in [".md", ".markdown"]:
                return FileService._load_markdown(path)
            elif path.suffix.lower() == ".txt":
                return FileService._load_text(path)
            elif path.suffix.lower() == ".json":
                return FileService._load_json(path)
            else:
                # Default to text loading
                return FileService._load_text(path)
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return None

    @staticmethod
    def save_document(document: Document, file_path: str) -> bool:
        """Save a document to file."""
        path = Path(file_path)

        try:
            if path.suffix.lower() in [".md", ".markdown"]:
                return FileService._save_markdown(document, path)
            elif path.suffix.lower() == ".txt":
                return FileService._save_text(document, path)
            elif path.suffix.lower() == ".json":
                return FileService._save_json(document, path)
            else:
                # Default to text saving
                return FileService._save_text(document, path)
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")
            return False

    @staticmethod
    def _load_text(path: Path) -> Document:
        """Load a plain text file."""
        content = path.read_text(encoding="utf-8")
        document = Document(title=path.stem, file_path=str(path))
        if document.root_section:
            document.root_section.content = content
        return document

    @staticmethod
    def _load_markdown(path: Path) -> Document:
        """Load a markdown file."""
        content = path.read_text(encoding="utf-8")
        document = Document(title=path.stem, file_path=str(path))
        if document.root_section:
            document.root_section.content = content
        return document

    @staticmethod
    def _load_json(path: Path) -> Document:
        """Load a JSON document structure."""
        data = json.loads(path.read_text(encoding="utf-8"))
        # TODO: Implement JSON document structure loading
        document = Document(title=data.get("title", path.stem), file_path=str(path))
        return document

    @staticmethod
    def _save_text(document: Document, path: Path) -> bool:
        """Save as plain text file."""
        if document.root_section:
            path.write_text(document.root_section.content, encoding="utf-8")
        return True

    @staticmethod
    def _save_markdown(document: Document, path: Path) -> bool:
        """Save as markdown file."""
        if document.root_section:
            path.write_text(document.root_section.content, encoding="utf-8")
        return True

    @staticmethod
    def _save_json(document: Document, path: Path) -> bool:
        """Save as JSON document structure."""
        data = {
            "title": document.title,
            "created_at": document.created_at.isoformat(),
            "modified_at": document.modified_at.isoformat(),
            # TODO: Implement full document structure serialization
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
