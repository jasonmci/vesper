from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Static, Tree
from textual.widgets.tree import TreeNode

from . import PathPrompt  # reuse your small input modal

SETTINGS_FILE = Path.home() / ".vesper" / "settings.json"


def _last_project_from_settings() -> Optional[Path]:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        p = Path(data.get("last_project", "")).expanduser()
        return p if p.is_dir() else None
    except Exception:
        return None


# ---- Data model ------------------------------------------------------------


@dataclass
class OutlineItem:
    id: str
    title: str
    kind: str  # "beat" | "chapter" | "milestone"
    children: List["OutlineItem"]

    @staticmethod
    def new(title: str, kind: str) -> "OutlineItem":
        return OutlineItem(id=str(uuid.uuid4()), title=title, kind=kind, children=[])


# ---- View ------------------------------------------------------------------


class OutlinerView(Container):
    """3-level outline: Beats -> Chapters -> Milestones."""

    BINDINGS = [
        Binding("a", "add_sibling", "Add Sibling"),
        Binding("c", "add_child", "Add Child"),
        Binding("enter", "rename", "Rename"),
        Binding("backspace", "delete", "Delete"),
        Binding("tab", "indent", "Indent"),
        Binding("shift+tab", "outdent", "Outdent"),
        Binding("ctrl+shift+up", "move_up", "Move Up"),
        Binding("ctrl+k", "move_up", "Move Up"),  # fallback
        Binding("ctrl+shift+down", "move_down", "Move Down"),
        Binding("ctrl+j", "move_down", "Move Down"),  # fallback
        Binding("e", "expand_all", "Expand All"),
        Binding("shift+e", "collapse_all", "Collapse All"),
        Binding("r", "rename", "Rename"),  # easier access than Enter
    ]

    def compose(self) -> ComposeResult:
        # Single wrapper containing title, tree, and help
        with Vertical(id="outliner-wrapper"):
            yield Static("📋 Outliner", classes="screen-title")

            tree: Tree[OutlineItem] = Tree("ROOT", id="outline-tree")
            tree.show_root = False
            self._tree = tree  # store reference for later operations
            yield tree

            yield Static(
                "A: Sibling  C: Child  Enter: Rename  ⌫: Delete\n"
                "Tab/Shift+Tab: Indent/Outdent",
                id="outliner-help",
            )

    # ---- Lifecycle ---------------------------------------------------------

    def reload_outline_from_disk(self) -> None:
        items = self._load_outline() or self._seed_bme()
        self._populate_tree(items)

    def on_mount(self) -> None:
        items = self._load_outline() or self._seed_bme()
        self._populate_tree(items)
        self._expand_all()
        self._tree.focus()

    # ---- Actions (keys) ----------------------------------------------------

    def action_expand_all(self) -> None:
        self._expand_all()

    # def action_collapse_all(self) -> None:
    #     self._tree.collapse_all()

    def action_add_sibling(self) -> None:
        self.app.run_worker(self._add_sibling_worker())

    def action_add_child(self) -> None:
        self.app.run_worker(self._add_child_worker())

    def action_rename(self) -> None:
        self.app.run_worker(self._rename_worker())

    def action_delete(self) -> None:
        node = self._selected_node()
        if node and node.parent:
            node.remove()
            self._save_outline()

    def action_indent(self) -> None:
        node = self._selected_node()
        if node is None or node.parent is None:
            return
        prev = self._previous_sibling(node)
        if prev is None:
            return
        if self._level_of(prev) + 1 > 3:
            self.app.notify("Max depth is 3", severity="warning")
            return
        cloned = self._clone_subtree(node)
        node.remove()
        self._attach_subtree(prev, cloned)
        prev.expand()
        self._reselect_by_id(cloned.id)
        self._save_outline()

    def action_outdent(self) -> None:
        node = self._selected_node()
        if node is None:
            return
        parent = node.parent
        if parent is None:
            return
        grand = parent.parent
        if grand is None:
            return
        cloned = self._clone_subtree(node)
        node.remove()
        self._attach_subtree(grand, cloned)
        self._reselect_by_id(cloned.id)
        self._save_outline()

    def action_move_up(self) -> None:
        node = self._selected_node()
        if node is None or node.parent is None:
            return
        parent = node.parent
        sibs = cast(list[TreeNode[OutlineItem]], parent.children)
        idx = sibs.index(node)
        item_id = node.data.id if node.data else None

        if idx > 0:
            # Swap with previous within the same parent
            order = [self._clone_subtree(ch) for ch in sibs]
            order[idx - 1], order[idx] = order[idx], order[idx - 1]
            self._rebuild_children(parent, order)
            if item_id:
                self._reselect_by_id(item_id)
            self._save_outline()
            return

        # At first position -> try to move into previous parent (if any)
        grand = parent.parent
        if grand is None:
            return  # top-level parent is root; nothing above to hop into
        prev_parent = self._previous_sibling(parent)
        if prev_parent is None:
            return

        moving_item = self._clone_subtree(node)
        node.remove()
        # append at end of previous parent
        prev_items = [self._clone_subtree(ch) for ch in prev_parent.children]
        prev_items.append(moving_item)
        self._rebuild_children(prev_parent, prev_items)

        self._reselect_by_id(moving_item.id)
        self._save_outline()

    def action_move_down(self) -> None:
        node = self._selected_node()
        if node is None or node.parent is None:
            return
        parent = node.parent
        # type: ignore[attr-defined]
        sibs: list[TreeNode[OutlineItem]] = parent.children  # type: ignore
        idx = sibs.index(node)
        item_id = node.data.id if node.data else None

        if idx < len(sibs) - 1:
            # Swap with next within the same parent
            order = [self._clone_subtree(ch) for ch in sibs]
            order[idx], order[idx + 1] = order[idx + 1], order[idx]
            self._rebuild_children(parent, order)
            if item_id:
                self._reselect_by_id(item_id)
            self._save_outline()
            return

        # At last position -> try to move into next parent (if any)
        grand = parent.parent
        if grand is None:
            return  # top-level parent is root; nothing below to hop into
        next_parent = self._next_sibling(parent)
        if next_parent is None:
            return

        moving_item = self._clone_subtree(node)
        node.remove()
        # insert at beginning of next parent
        next_items = [self._clone_subtree(ch) for ch in next_parent.children]
        next_items.insert(0, moving_item)
        self._rebuild_children(next_parent, next_items)

        self._reselect_by_id(moving_item.id)
        self._save_outline()

    async def _add_sibling_worker(self) -> None:
        parent = self._parent_node_of_selection()
        if parent is None:
            return
        level = self._level_of(parent) + 1
        kind = self._kind_for_level(level)
        if not kind:
            return
        title = await self._ask("New item title…", f"New {kind.title()}")
        if not title:
            return
        self._add_item(parent, OutlineItem.new(title, kind))
        self._save_outline()

    def _add_item(self, parent: TreeNode, item: OutlineItem) -> TreeNode:
        node = parent.add(self._node_label(item), data=item)
        return node

    async def _add_child_worker(self) -> None:
        node = self._selected_node()
        if node is None:
            return
        level = self._level_of(node) + 1
        if level > 3:
            self.app.notify("Max depth is 3", severity="warning")
            return
        kind = self._kind_for_level(level)
        if not kind:
            return
        title = await self._ask("New child title…", f"New {kind.title()}")
        if not title:
            return
        self._add_item(node, OutlineItem.new(title, kind))
        node.expand()
        self._save_outline()

    async def _rename_worker(self) -> None:
        pair = self._selected_node_and_item()
        if pair is None:
            return
        node, data = pair
        title = await self._ask("Rename item…", data.title)
        if not title:
            return
        data.title = title
        node.set_label(self._node_label(data))
        self._save_outline()

    # ---- Helpers: tree <-> data -------------------------------------------

    def _expand_all(self) -> None:
        """Expand all nodes in the tree."""

        def walk(node):
            node.expand()
            for ch in node.children:
                walk(ch)

        walk(self._tree.root)

    def _expand_to(self, node) -> None:
        """Expand ancestors so `node` is visible."""
        p = node.parent
        while p is not None:
            p.expand()
            p = p.parent

    def _rebuild_children(self, parent, items):
        for ch in list(parent.children):
            ch.remove()
        for it in items:
            self._attach_subtree(parent, it)
        # keep everything expanded after structural changes
        self._expand_all()

    def _next_sibling(
        self, node: TreeNode[OutlineItem]
    ) -> Optional[TreeNode[OutlineItem]]:
        if node.parent is None:
            return None
        sibs = cast(list[TreeNode[OutlineItem]], node.parent.children)
        i = sibs.index(node)
        return sibs[i + 1] if i + 1 < len(sibs) else None

    def _seed_bme(self) -> List[OutlineItem]:
        return [
            OutlineItem.new("Beginning", "beat"),
            OutlineItem.new("Middle", "beat"),
            OutlineItem.new("End", "beat"),
        ]

    def _populate_tree(self, items: list[OutlineItem]) -> None:
        root = self._tree.root
        # Clear existing children (works across Textual versions)
        for child in list(root.children):
            child.remove()

        for item in items:
            self._attach_subtree(root, item)

    def _attach_subtree(
        self,
        parent: TreeNode[OutlineItem],
        item: OutlineItem,
    ) -> TreeNode[OutlineItem]:
        node = parent.add(self._node_label(item), data=item)
        for child in item.children:
            self._attach_subtree(node, child)
        return node

    def _clone_subtree(self, node: TreeNode[OutlineItem]) -> OutlineItem:
        assert node.data is not None  # by construction, all non-root nodes carry data
        data: OutlineItem = node.data
        return OutlineItem(
            id=data.id,
            title=data.title,
            kind=data.kind,
            children=[self._clone_subtree(child) for child in node.children],
        )

    def _node_label(self, item: OutlineItem) -> str:
        # Prefix by type for easy scanning
        prefix = {
            "beat": "Beat",
            "chapter": "Chapter",
            "milestone": "•",
        }.get(item.kind, "")
        return f"{prefix} — {item.title}" if prefix else item.title

    def _selected_node(self) -> Optional[TreeNode[OutlineItem]]:
        return self._tree.cursor_node

    def _selected_node_and_item(
        self,
    ) -> Optional[Tuple[TreeNode[OutlineItem], OutlineItem]]:
        node = self._selected_node()
        if node is None:
            return None
        data = node.data
        if data is None:  # root or uninitialized node
            return None
        return node, data

    def _parent_node_of_selection(self) -> Optional[TreeNode[OutlineItem]]:
        node = self._selected_node()
        return node.parent if node else None

    def _previous_sibling(
        self, node: TreeNode[OutlineItem]
    ) -> Optional[TreeNode[OutlineItem]]:
        if node.parent is None:
            return None
        siblings = node.parent.children  # type: ignore[attr-defined]
        i = siblings.index(node)
        return siblings[i - 1] if i > 0 else None

    def _level_of(self, node: TreeNode[OutlineItem]) -> int:
        level = -1
        n: Optional[TreeNode[OutlineItem]] = node
        while n is not None:
            level += 1
            n = n.parent
        return level

    def _kind_for_level(self, level: int) -> Optional[str]:
        return {1: "beat", 2: "chapter", 3: "milestone"}.get(level)

    async def _ask(self, title: str, default: str = "") -> Optional[str]:
        # Reuse your PathPrompt as a generic input
        val = await self.app.push_screen_wait(PathPrompt(title, default=default))
        return val.strip() if val else None

    # ---- Persistence -------------------------------------------------------

    def _outline_path(self) -> Path:
        # Prefer app.project_root;
        # otherwise fall back to settings' last_project; else CWD
        root = getattr(self.app, "project_root", None)
        if not root:
            root = _last_project_from_settings()
        base = Path(root) if root else Path(".")
        return (base / "outline.json").expanduser()

    def _save_outline(self) -> None:
        def node_to_item(node: TreeNode) -> OutlineItem:
            # All non-root nodes should have data; assert for type checking and safety.
            assert node.data is not None, "Tree node missing OutlineItem data"
            data = cast(OutlineItem, node.data)
            return OutlineItem(
                id=data.id,
                title=data.title,
                kind=data.kind,
                children=[node_to_item(child) for child in node.children],
            )

        items = [node_to_item(n) for n in self._tree.root.children]
        payload = [asdict(item) for item in items]
        path = self._outline_path()
        path.parent.mkdir(parents=True, exist_ok=True)  # <- ensure folder
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_outline(self) -> Optional[List[OutlineItem]]:
        path = self._outline_path()
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [self._hydrate(item) for item in data]
        except Exception:
            # corrupt or incompatible; fall back to seed
            return None

    def _hydrate(self, data: Dict[str, Any]) -> OutlineItem:
        return OutlineItem(
            id=data.get("id") or str(uuid.uuid4()),
            title=data.get("title", "Untitled"),
            kind=data.get("kind", "beat"),
            children=[self._hydrate(c) for c in data.get("children", [])],
        )

    # Reselect helper after structural edits
    def _reselect_by_id(self, node_id: str) -> None:
        def find(node):
            if node.data and getattr(node.data, "id", None) == node_id:
                return node
            for ch in node.children:
                f = find(ch)
                if f:
                    return f
            return None

        for top in self._tree.root.children:
            target = find(top)
            if target:
                self._expand_to(target)  # expand ancestors so it's visible
                # <-- instead of: self._tree.cursor_node = target
                self._tree.select_node(target)
                self._tree.focus()
                # scroll (handle API differences across Textual versions)
                scroll_to_node = getattr(self._tree, "scroll_to_node", None)
                if callable(scroll_to_node):
                    scroll_to_node(target)
                else:
                    # fallback if needed
                    line = getattr(target, "line", None)
                    if isinstance(line, int):
                        self._tree.scroll_to_line(line)
                break
