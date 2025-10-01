"""
Document model for text editing and outlining.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class DocumentSection:
    """A section within a document."""

    title: str
    content: str = ""
    level: int = 1
    children: List["DocumentSection"] = field(default_factory=list)
    parent: Optional["DocumentSection"] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def add_child(self, section: "DocumentSection") -> None:
        """Add a child section."""
        section.parent = self
        section.level = self.level + 1
        self.children.append(section)

    def remove_child(self, section: "DocumentSection") -> None:
        """Remove a child section."""
        if section in self.children:
            section.parent = None
            self.children.remove(section)

    def get_all_descendants(self) -> List["DocumentSection"]:
        """Get all descendant sections."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


@dataclass
class Document:
    """A document containing sections and content."""

    title: str
    file_path: Optional[str] = None
    root_section: Optional[DocumentSection] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_modified: bool = False

    def __post_init__(self):
        """Initialize the document with a root section if none provided."""
        if self.root_section is None:
            self.root_section = DocumentSection(title=self.title, level=0)

    def mark_modified(self) -> None:
        """Mark the document as modified."""
        self.is_modified = True
        self.modified_at = datetime.now()

    def get_all_sections(self) -> List[DocumentSection]:
        """Get all sections in the document."""
        if self.root_section is None:
            return []
        return [self.root_section] + self.root_section.get_all_descendants()

    def find_section_by_title(self, title: str) -> Optional[DocumentSection]:
        """Find a section by its title."""
        for section in self.get_all_sections():
            if section.title == title:
                return section
        return None
