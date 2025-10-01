"""
Task model for task management.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class TaskStatus(Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task:
    """A task item."""

    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.modified_at = datetime.now()

    def mark_in_progress(self) -> None:
        """Mark the task as in progress."""
        self.status = TaskStatus.IN_PROGRESS
        self.modified_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the task."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.modified_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the task."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        return self.due_date < date.today()

    @property
    def status_emoji(self) -> str:
        """Get emoji representation of task status."""
        return {
            TaskStatus.TODO: "🔲",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.DONE: "✅",
            TaskStatus.CANCELLED: "❌",
        }[self.status]


@dataclass
class TaskList:
    """A collection of tasks."""

    name: str
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: Task) -> None:
        """Add a task to the list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the list."""
        if task in self.tasks:
            self.tasks.remove(task)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks filtered by status."""
        return [task for task in self.tasks if task.status == status]

    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks."""
        return [task for task in self.tasks if task.is_overdue]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get tasks filtered by priority."""
        return [task for task in self.tasks if task.priority == priority]
