"""Additional tests for Document and DocumentSection edge cases."""

from vesper.models.document import Document, DocumentSection


def test_document_root_auto_creation():
    doc = Document(title="Auto Root")
    assert doc.root_section is not None
    assert doc.root_section.level == 0


def test_document_find_section_by_title():
    doc = Document(title="Doc")
    sec_a = DocumentSection(title="A")
    sec_b = DocumentSection(title="B")
    assert doc.root_section is not None
    doc.root_section.add_child(sec_a)
    doc.root_section.add_child(sec_b)
    assert doc.find_section_by_title("B") is sec_b
    assert doc.find_section_by_title("Missing") is None


def test_section_remove_child():
    parent = DocumentSection(title="Parent", level=0)
    child = DocumentSection(title="Child")
    parent.add_child(child)
    assert child in parent.children
    parent.remove_child(child)
    assert child not in parent.children
    assert child.parent is None


def test_get_all_descendants_nested():
    root = DocumentSection(title="Root", level=0)
    c1 = DocumentSection(title="C1")
    c2 = DocumentSection(title="C2")
    c11 = DocumentSection(title="C1.1")
    root.add_child(c1)
    root.add_child(c2)
    c1.add_child(c11)
    descendants = root.get_all_descendants()
    assert set(d.title for d in descendants) == {"C1", "C2", "C1.1"}


def test_mark_modified_updates_flags_and_timestamp(monkeypatch):
    doc = Document(title="Doc")
    original_modified = doc.modified_at

    class DummyDateTime:
        @staticmethod
        def now():
            from datetime import datetime as _dt

            return _dt(2030, 1, 1, 12, 0, 0)

    from vesper.models import document as document_module

    monkeypatch.setattr(document_module, "datetime", DummyDateTime)
    doc.mark_modified()
    assert doc.is_modified is True
    assert doc.modified_at != original_modified
