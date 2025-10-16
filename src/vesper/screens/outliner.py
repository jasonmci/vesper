from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Static, Tree
from textual.widgets.tree import TreeNode

from . import MilestonePrompt, PathPrompt  # reuse your small input modal

SETTINGS_FILE = Path.home() / ".vesper" / "settings.json"
GRID_COL_WIDTHS = (36, 36, 36, 36)  # Plot, Subplot, Character, Theme


def _last_project_from_settings() -> Optional[Path]:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        p = Path(data.get("last_project", "")).expanduser()
        return p if p.is_dir() else None
    except Exception:
        return None


def _preview(text: str, max_chars: int) -> str:
    if not text:
        return ""
    t = text.replace("\n", " ").strip()
    return t if len(t) <= max_chars else t[: max(0, max_chars - 1)] + "…"


# ---- Data model ------------------------------------------------------------


@dataclass
class OutlineItem:
    id: str
    title: str
    kind: str  # "beat" | "chapter" | "milestone"
    children: List["OutlineItem"]
    # Milestone meta (ignored for beats/chapters)
    plot: str = ""
    subplot: str = ""
    character: str = ""
    theme: str = ""

    @staticmethod
    def new(title: str, kind: str, **meta: str) -> "OutlineItem":
        return OutlineItem(
            id=str(uuid.uuid4()),
            title=title,
            kind=kind,
            children=[],
            plot=meta.get("plot", ""),
            subplot=meta.get("subplot", ""),
            character=meta.get("character", ""),
            theme=meta.get("theme", ""),
        )


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
        Binding("b", "collapse_all", "Collapse All"),
        Binding("shift+e", "collapse_all", "Collapse All"),
        Binding("r", "rename", "Rename"),  # easier access than Enter
        Binding("m", "edit_milestone", "Edit Milestone"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="outliner-split"):
            with Vertical(id="outliner-wrapper"):
                yield Static("Outliner", classes="screen-title")
                tree: Tree[OutlineItem] = Tree("ROOT", id="outline-tree")
                tree.show_root = False
                self._tree = tree
                yield tree
                yield Static(
                    (
                        "A: Sibling  C: Child  Enter: Rename  ⌫: Delete  "
                        "Tab/Shift+Tab: Indent/Outdent  J/K: Move  E: Expand"
                    ),
                    id="outliner-help",
                )

            with Vertical(id="grid-wrapper"):
                yield Static("", id="grid-spacer-top")

                self._grid = DataTable(id="outline-grid")
                # Add columns ONCE; no widths here (avoids API differences)
                self._grid.add_columns("Plot", "Subplot", "Character", "Theme")
                self._grid.cursor_type = "row"
                yield self._grid

                yield Static("", id="grid-spacer-bottom")

    # ---- Lifecycle ---------------------------------------------------------
    def action_edit_milestone(self) -> None:
        self.app.run_worker(self._edit_milestone_worker())

    async def _edit_milestone_worker(self) -> None:
        pair = self._selected_node_and_item()
        if pair is None:
            return
        node, data = pair
        if data.kind != "milestone":
            self.app.notify("Select a milestone to edit", severity="warning")
            return

        fields = await self.app.push_screen_wait(
            MilestonePrompt(
                "Edit milestone",
                default_title=data.title,
                default_plot=data.plot,
                default_subplot=data.subplot,
                default_character=data.character,
                default_theme=data.theme,
            )
        )
        if not fields:
            return

        # Update model + tree label
        data.title = fields["title"] or data.title
        data.plot = fields["plot"]
        data.subplot = fields["subplot"]
        data.character = fields["character"]
        data.theme = fields["theme"]
        node.set_label(self._node_label(data))

        self._save_outline()
        self._rebuild_grid()
        self._reselect_by_id(data.id)

    def on_mount(self) -> None:
        items = self._load_outline() or self._seed_bme()
        self._populate_tree(items)
        self._rebuild_grid()
        self._expand_all()
        self._tree.focus()

    def reload_outline_from_disk(self) -> None:
        items = self._load_outline() or self._seed_bme()
        self._populate_tree(items)
        self._rebuild_grid()
        self._expand_all()

    # ---- Actions (keys) ----------------------------------------------------

    def action_expand_all(self) -> None:
        self._expand_all()

    def action_collapse_all(self) -> None:
        self._collapse_all()

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
            self._rebuild_grid()

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
        self._rebuild_grid()

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
        self._rebuild_grid()

    def action_move_up(self) -> None:
        node = self._selected_node()
        if node is None or node.parent is None:
            return
        parent = node.parent
        sibs = list(parent.children)
        idx = sibs.index(node)
        item_id = node.data.id if node.data else None

        if idx > 0:
            order = [self._clone_subtree(ch) for ch in sibs]
            order[idx - 1], order[idx] = order[idx], order[idx - 1]
            self._rebuild_children(parent, order)
            if item_id:
                self._reselect_by_id(item_id)
            self._save_outline()
            self._rebuild_grid()
            return

        grand = parent.parent
        if grand is None:
            return
        prev_parent = self._previous_sibling(parent)
        if prev_parent is None:
            return

        moving_item = self._clone_subtree(node)
        node.remove()
        prev_items = [self._clone_subtree(ch) for ch in prev_parent.children]
        prev_items.append(moving_item)
        self._rebuild_children(prev_parent, prev_items)
        self._reselect_by_id(moving_item.id)
        self._save_outline()
        self._rebuild_grid()

    def action_move_down(self) -> None:
        node = self._selected_node()
        if node is None or node.parent is None:
            return
        parent = node.parent
        sibs = list(parent.children)
        idx = sibs.index(node)
        item_id = node.data.id if node.data else None

        if idx < len(sibs) - 1:
            order = [self._clone_subtree(ch) for ch in sibs]
            order[idx], order[idx + 1] = order[idx + 1], order[idx]
            self._rebuild_children(parent, order)
            if item_id:
                self._reselect_by_id(item_id)
            self._save_outline()
            self._rebuild_grid()
            return

        grand = parent.parent
        if grand is None:
            return
        next_parent = self._next_sibling(parent)
        if next_parent is None:
            return

        moving_item = self._clone_subtree(node)
        node.remove()
        next_items = [self._clone_subtree(ch) for ch in next_parent.children]
        next_items.insert(0, moving_item)
        self._rebuild_children(next_parent, next_items)
        self._reselect_by_id(moving_item.id)
        self._save_outline()
        self._rebuild_grid()

    # ---- Workers (async) ---------------------------------------------------

    def _add_item(self, parent: TreeNode, item: OutlineItem) -> TreeNode:
        node = parent.add(self._node_label(item), data=item)
        return node

    async def _add_sibling_worker(self) -> None:
        parent = self._parent_node_of_selection()
        if not parent:
            return
        level = self._level_of(parent) + 1
        kind = self._kind_for_level(level)
        if not kind:
            return

        if kind == "milestone":
            data = await self.app.push_screen_wait(MilestonePrompt("New milestone"))
            if not data or not data.get("title"):
                return
            item = OutlineItem.new(
                data["title"],
                "milestone",
                plot=data.get("plot", ""),
                subplot=data.get("subplot", ""),
                character=data.get("character", ""),
                theme=data.get("theme", ""),
            )
        else:
            title = await self._ask("New item title…", f"New {kind.title()}")
            if not title:
                return
            item = OutlineItem.new(title, kind)

        self._add_item(parent, item)
        self._save_outline()
        self._rebuild_grid()

    async def _add_child_worker(self) -> None:
        node = self._selected_node()
        if not node:
            return
        level = self._level_of(node) + 1
        if level > 3:
            self.app.notify("Max depth is 3", severity="warning")
            return
        kind = self._kind_for_level(level)
        if not kind:
            return  # Safety: unexpected level outside 1..3

        if kind == "milestone":
            data = await self.app.push_screen_wait(MilestonePrompt("New milestone"))
            if not data or not data.get("title"):
                return
            item = OutlineItem.new(
                data["title"],
                "milestone",
                plot=data.get("plot", ""),
                subplot=data.get("subplot", ""),
                character=data.get("character", ""),
                theme=data.get("theme", ""),
            )
        else:
            title = await self._ask("New child title…", f"New {kind.title()}")
            if not title:
                return
            item = OutlineItem.new(title, kind)

        self._add_item(node, item)
        node.expand()
        self._save_outline()
        self._rebuild_grid()

    async def _rename_worker(self) -> None:
        node = self._selected_node()
        if not node or not node.data:
            return
        current = node.data.title
        title = await self._ask("Rename item…", current)
        if not title:
            return
        node.data.title = title
        node.set_label(self._node_label(node.data))
        self._save_outline()
        self._rebuild_grid()

    # ---- Helpers: tree <-> data -------------------------------------------

    def _expand_all(self) -> None:
        """Expand all nodes in the tree."""

        def walk(node):
            node.expand()
            for ch in node.children:
                walk(ch)

        walk(self._tree.root)

    def _collapse_all(self) -> None:
        def walk(node):
            node.collapse()
            for ch in node.children:
                walk(ch)

        walk(self._tree.root)

    def _expand_to(self, node) -> None:
        """Expand ancestors so `node` is visible."""
        p = node.parent
        while p is not None:
            p.expand()
            p = p.parent

    def _rebuild_children(
        self, parent: TreeNode[OutlineItem], items: List[OutlineItem]
    ) -> None:
        for ch in list(parent.children):
            ch.remove()
        for it in items:
            self._attach_subtree(parent, it)
        self._expand_all()

    # ---- Tree / grid helpers ----------------------------------------------

    def _seed_bme(self) -> List[OutlineItem]:
        return [
            OutlineItem.new("Beginning", "beat"),
            OutlineItem.new("Middle", "beat"),
            OutlineItem.new("End", "beat"),
        ]

    def _populate_tree(self, items: List[OutlineItem]) -> None:
        root = self._tree.root
        for ch in list(root.children):
            ch.remove()
        for item in items:
            self._attach_subtree(root, item)

    def _attach_subtree(
        self, parent: TreeNode[OutlineItem], item: OutlineItem
    ) -> TreeNode[OutlineItem]:
        node = parent.add(self._node_label(item), data=item)
        for child in item.children:
            self._attach_subtree(node, child)
        return node

    def _clone_subtree(self, node: TreeNode[OutlineItem]) -> OutlineItem:
        assert node.data is not None
        d = node.data
        return OutlineItem(
            id=d.id,
            title=d.title,
            kind=d.kind,
            plot=d.plot,
            subplot=d.subplot,
            character=d.character,
            theme=d.theme,
            children=[self._clone_subtree(ch) for ch in node.children],
        )

    def _node_label(self, item: OutlineItem) -> str:
        prefix = {"beat": "📗 ", "chapter": "📓 ", "milestone": "• "}.get(item.kind, "")
        return f"{prefix}{item.title}" if prefix else item.title

    def _selected_node(self) -> Optional[TreeNode[OutlineItem]]:
        return self._tree.cursor_node

    def _parent_node_of_selection(self) -> Optional[TreeNode[OutlineItem]]:
        node = self._selected_node()
        return node.parent if node else None

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

    def _previous_sibling(
        self, node: TreeNode[OutlineItem]
    ) -> Optional[TreeNode[OutlineItem]]:
        if node.parent is None:
            return None
        sibs = node.parent.children
        i = sibs.index(node)
        return sibs[i - 1] if i > 0 else None

    def _next_sibling(
        self, node: TreeNode[OutlineItem]
    ) -> Optional[TreeNode[OutlineItem]]:
        if node.parent is None:
            return None
        sibs = node.parent.children
        i = sibs.index(node)
        return sibs[i + 1] if i + 1 < len(sibs) else None

    def _level_of(self, node: TreeNode[OutlineItem]) -> int:
        level = -1
        n: Optional[TreeNode[OutlineItem]] = node
        while n is not None:
            level += 1
            n = n.parent
        return level  # 1=beat, 2=chapter, 3=milestone

    def _kind_for_level(self, level: int) -> Optional[str]:
        return {1: "beat", 2: "chapter", 3: "milestone"}.get(level)

    async def _ask(self, title: str, default: str = "") -> Optional[str]:
        # Reuse your PathPrompt as a generic input
        val = await self.app.push_screen_wait(PathPrompt(title, default=default))
        return val.strip() if val else None

    # ---- Persistence -------------------------------------------------------

    def _outline_path(self) -> Path:
        # Prefer the app’s current project; else last_project from settings; else CWD
        root = getattr(self.app, "project_root", None)
        if not root:
            root = _last_project_from_settings()
        base = Path(root) if root else Path(".")
        return (base / "outline.json").expanduser()

    def _save_outline(self) -> None:
        def node_to_item(node: TreeNode[OutlineItem]) -> OutlineItem:
            assert node.data is not None, "Expected node to have OutlineItem data"
            d: OutlineItem = node.data
            return OutlineItem(
                id=d.id,
                title=d.title,
                kind=d.kind,
                plot=d.plot,
                subplot=d.subplot,
                character=d.character,
                theme=d.theme,
                children=[node_to_item(ch) for ch in node.children],
            )

        items = [node_to_item(n) for n in self._tree.root.children]
        payload = [asdict(item) for item in items]
        path = self._outline_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_outline(self) -> Optional[List[OutlineItem]]:
        path = self._outline_path()
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [self._hydrate(item) for item in data]
        except Exception:
            return None

    def _hydrate(self, data: Dict[str, Any]) -> OutlineItem:
        return OutlineItem(
            id=data.get("id") or str(uuid.uuid4()),
            title=data.get("title", "Untitled"),
            kind=data.get("kind", "beat"),
            plot=data.get("plot", ""),
            subplot=data.get("subplot", ""),
            character=data.get("character", ""),
            theme=data.get("theme", ""),
            children=[self._hydrate(c) for c in data.get("children", [])],
        )

    # Reselect helper after structural edits
    def _reselect_by_id(self, node_id: str) -> None:
        def find(n: TreeNode[OutlineItem]) -> Optional[TreeNode[OutlineItem]]:
            if n.data and getattr(n.data, "id", None) == node_id:
                return n
            for ch in n.children:
                r = find(ch)
                if r:
                    return r
            return None

        for top in self._tree.root.children:
            target = find(top)
            if target:
                self._expand_to(target)
                # select_node is the cross-version safe way
                self._tree.select_node(target)
                self._tree.focus()
                scroll_to_node = getattr(self._tree, "scroll_to_node", None)
                if callable(scroll_to_node):
                    scroll_to_node(target)
                break

    # ---- Grid building / selection ----------------------------------------

    def _flatten(self) -> List[OutlineItem]:
        items: List[OutlineItem] = []

        def walk(n: TreeNode[OutlineItem]) -> None:
            if n is not self._tree.root and n.data:
                items.append(n.data)
            for ch in n.children:
                walk(ch)

        for top in self._tree.root.children:
            walk(top)
        return items

    def _rebuild_grid(self) -> None:
        # Clear rows only; keep headers
        try:
            self._grid.clear(columns=False)
        except TypeError:
            self._grid.clear()
            if not getattr(self._grid, "columns", None):
                self._grid.add_columns("Plot", "Subplot", "Character", "Theme")

        self._grid_index: List[str] = []

        # simple preview lengths (tweak if you want)
        w_plot, w_subplot, w_char, w_theme = (
            GRID_COL_WIDTHS if "GRID_COL_WIDTHS" in globals() else (36, 36, 36, 36)
        )

        for item in self._flatten():
            self._grid_index.append(item.id)
            if item.kind == "milestone":
                self._grid.add_row(
                    _preview(item.plot, w_plot),
                    _preview(item.subplot, w_subplot),
                    _preview(item.character, w_char),
                    _preview(item.theme, w_theme),
                )
            else:
                self._grid.add_row("", "", "", "")

        # keep grid near the selected node
        node = self._selected_node()
        if node and node.data:
            self._grid_select_by_id(node.data.id)

    def _grid_select_by_id(self, node_id: str) -> None:
        try:
            idx = self._grid_index.index(node_id)
        except ValueError:
            return
        scroll_to_row = getattr(self._grid, "scroll_to_row", None)
        if callable(scroll_to_row):
            scroll_to_row(idx)
        try:
            from textual.coordinate import Coordinate

            self._grid.cursor_coordinate = Coordinate(idx, 0)
        except Exception:
            pass

    # Tree -> Grid
    def on_tree_node_selected(self, event) -> None:
        node = getattr(event, "node", None)
        if node and node.data:
            self._grid_select_by_id(node.data.id)

    # Grid -> Tree
    def on_data_table_row_highlighted(self, event) -> None:
        idx = getattr(event, "row_index", getattr(event, "row", None))
        if idx is None:
            return
        if 0 <= idx < len(getattr(self, "_grid_index", [])):
            self._reselect_by_id(self._grid_index[idx])
