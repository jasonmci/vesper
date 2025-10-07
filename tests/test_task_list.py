"""Tests for TaskList filtering and tagging behavior."""

from datetime import date, timedelta

from vesper.models.task import Task, TaskList, TaskPriority, TaskStatus


def build_task(title: str, **kwargs) -> Task:
    return Task(title=title, **kwargs)


def test_add_and_remove_task():
    lst = TaskList(name="Inbox")
    t = build_task("Task 1")
    lst.add_task(t)
    assert t in lst.tasks
    lst.remove_task(t)
    assert t not in lst.tasks


def test_get_tasks_by_status():
    lst = TaskList(name="Work")
    t1 = build_task("T1", status=TaskStatus.TODO)
    t2 = build_task("T2", status=TaskStatus.IN_PROGRESS)
    t3 = build_task("T3", status=TaskStatus.DONE)
    for t in (t1, t2, t3):
        lst.add_task(t)
    assert {t.title for t in lst.get_tasks_by_status(TaskStatus.DONE)} == {"T3"}


def test_get_tasks_by_priority():
    lst = TaskList(name="P")
    t1 = build_task("A", priority=TaskPriority.HIGH)
    t2 = build_task("B", priority=TaskPriority.LOW)
    t3 = build_task("C", priority=TaskPriority.HIGH)
    for t in (t1, t2, t3):
        lst.add_task(t)
    highs = lst.get_tasks_by_priority(TaskPriority.HIGH)
    assert {t.title for t in highs} == {"A", "C"}


def test_overdue_detection():
    lst = TaskList(name="Deadlines")
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)
    overdue = build_task("Late", due_date=yesterday)
    future = build_task("Future", due_date=tomorrow)
    done = build_task("Done", due_date=yesterday, status=TaskStatus.DONE)
    for t in (overdue, future, done):
        lst.add_task(t)
    overdue_titles = {t.title for t in lst.get_overdue_tasks()}
    assert overdue_titles == {"Late"}


def test_tag_add_remove_and_no_duplicates():
    task = build_task("Tagged")
    task.add_tag("x")
    task.add_tag("x")  # duplicate ignored
    task.add_tag("y")
    assert task.tags == ["x", "y"]
    task.remove_tag("x")
    assert task.tags == ["y"]
