"""
Tasks screen for task management and tracking.
"""

from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static


class TasksView(Container):
    """Tasks screen component."""

    def compose(self):
        """Compose the tasks layout."""
        with Vertical():
            yield Static("✅ Task Tracker", classes="screen-title")

            with Horizontal(classes="task-input"):
                yield Input(placeholder="Add a new task...", id="task-input")
                yield Button("Add", id="add-task", variant="primary")

            table = DataTable()
            table.add_columns("Status", "Task", "Priority", "Due Date")

            # Add some sample tasks
            table.add_rows(
                [
                    ["🔲", "Set up project structure", "High", "Today"],
                    ["✅", "Install dependencies", "High", "Done"],
                    ["🔲", "Create main app layout", "Medium", "Tomorrow"],
                    ["🔲", "Implement editor functionality", "High", "This week"],
                ]
            )

            yield table

    def on_mount(self) -> None:
        """Handle tasks mount."""
        input_widget = self.query_one("#task-input", Input)
        input_widget.focus()

    def on_button_pressed(self, event) -> None:
        """Handle button press events."""
        if event.button.id == "add-task":
            input_widget = self.query_one("#task-input", Input)
            task_text = input_widget.value.strip()

            if task_text:
                table = self.query_one(DataTable)
                table.add_row("🔲", task_text, "Medium", "TBD")
                input_widget.value = ""
