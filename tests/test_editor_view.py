"""Tests for EditorView logic (offline / without full Textual run loop)."""

import types

from vesper.screens.editor import EditorView


def test_editor_new_file_resets_state():
    view = EditorView()
    # Patch methods that rely on Textual runtime
    view._update_app_title = lambda: None  # type: ignore
    # Simulate mount by injecting a fake TextArea query result.
    # We'll monkeypatch query_one to return a simple object with 'text' attribute.

    textarea_holder = types.SimpleNamespace(text="Some initial text")

    class Status:
        def update(self, *_):
            pass

    status_holder = Status()

    def dispatch(*args, **kwargs):  # type: ignore
        if args:
            sel = args[0]
            if getattr(sel, "__name__", None) == "TextArea":
                return textarea_holder
            if sel == "#editor-status":
                return status_holder
        return textarea_holder

    view.query_one = dispatch  # type: ignore

    view.new_file()
    assert textarea_holder.text == ""
    assert view.current_path is None
    assert view.dirty is False


def test_editor_counts_update():
    view = EditorView()
    view._update_app_title = lambda: None  # type: ignore

    sample = "Hello world\nThis is\ntext"  # 3 lines, 5 words
    textarea_holder = types.SimpleNamespace(text=sample)
    updated_texts: list[str] = []

    class StatusHolder:
        def update(self, msg: str) -> None:  # mimic Static.update
            updated_texts.append(msg)

    status_holder = StatusHolder()

    # Dispatcher that recognizes:
    #   query_one(TextArea)
    #   query_one("#editor-status", Static)
    def dispatch(*args, **kwargs):  # type: ignore[override]
        if args:
            selector = args[0]
            # If passed a type (TextArea) return textarea
            if getattr(selector, "__name__", None) == "TextArea":
                return textarea_holder
            # If passed a string id selector
            if selector == "#editor-status":
                return status_holder
        return textarea_holder

    view.query_one = dispatch  # type: ignore
    # Execute the count update path
    view._update_counts()  # type: ignore

    # Validate manual calculations
    chars = len(sample)
    lines = sample.count("\n") + (0 if (chars == 0 or sample.endswith("\n")) else 1)
    words = len([w for w in sample.split() if w.strip()])
    assert lines == 3
    assert words == 5
    assert updated_texts, "Expected status_holder.update to be invoked"
    assert "Words: 5" in updated_texts[-1]
    assert "Lines: 3" in updated_texts[-1]
    assert f"Chars: {chars}" in updated_texts[-1]
