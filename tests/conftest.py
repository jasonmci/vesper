"""
Test configuration for Vesper.
"""

import pytest

from vesper.models.document import Document, DocumentSection
from vesper.models.task import Task, TaskPriority, TaskStatus


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    doc = Document(title="Test Document")
    section1 = DocumentSection(title="Introduction", content="This is the intro")
    section2 = DocumentSection(title="Conclusion", content="This is the end")

    if doc.root_section:
        doc.root_section.add_child(section1)
        doc.root_section.add_child(section2)

    return doc


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        title="Test Task",
        description="A task for testing",
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
    )
