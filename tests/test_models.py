"""
Basic tests for Vesper models.
"""

from vesper.models.document import Document, DocumentSection
from vesper.models.task import Task, TaskPriority, TaskStatus


def test_document_creation():
    """Test creating a document."""
    doc = Document(title="Test Document")
    assert doc.title == "Test Document"
    assert doc.root_section is not None
    assert doc.root_section.title == "Test Document"


def test_document_section_hierarchy():
    """Test document section hierarchy."""
    root = DocumentSection(title="Root", level=0)
    child1 = DocumentSection(title="Child 1")
    child2 = DocumentSection(title="Child 2")

    root.add_child(child1)
    root.add_child(child2)

    assert len(root.children) == 2
    assert child1.parent == root
    assert child1.level == 1
    assert child2.parent == root
    assert child2.level == 1


def test_task_creation():
    """Test creating a task."""
    task = Task(
        title="Test Task",
        description="A test task",
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
    )

    assert task.title == "Test Task"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.TODO
    assert task.status_emoji == "🔲"


def test_task_completion():
    """Test task completion."""
    task = Task(title="Test Task")
    assert task.status == TaskStatus.TODO

    task.mark_completed()
    assert task.status == TaskStatus.DONE
    assert task.completed_at is not None
    assert task.status_emoji == "✅"


def test_sample_fixtures(sample_document, sample_task):
    """Test that fixtures work correctly."""
    assert sample_document.title == "Test Document"
    assert len(sample_document.get_all_sections()) >= 1

    assert sample_task.title == "Test Task"
    assert sample_task.priority == TaskPriority.HIGH
