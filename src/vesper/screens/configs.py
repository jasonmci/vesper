"""
Stats screen for dashboard and analytics.
"""

from textual.containers import Container, Grid, Horizontal, Vertical
from textual.widgets import ProgressBar, Sparkline, Static


class ConfigView(Container):
    """Stats dashboard screen component."""

    def compose(self):
        """Compose the stats layout."""
        with Vertical():
            yield Static("📊 Dashboard", classes="screen-title")

            # Top row - summary cards
            with Horizontal(classes="stats-cards"):
                with Vertical(classes="stat-card"):
                    yield Static("Documents", classes="card-title")
                    yield Static("12", classes="card-value")
                    yield Static("↑ 3 this week", classes="card-trend")

                with Vertical(classes="stat-card"):
                    yield Static("Words Written", classes="card-title")
                    yield Static("8,547", classes="card-value")
                    yield Static("↑ 1,234 today", classes="card-trend")

                with Vertical(classes="stat-card"):
                    yield Static("Tasks Completed", classes="card-title")
                    yield Static("24", classes="card-value")
                    yield Static("↑ 5 this week", classes="card-trend")

                with Vertical(classes="stat-card"):
                    yield Static("Writing Streak", classes="card-title")
                    yield Static("7 days", classes="card-value")
                    yield Static("🔥 Keep it up!", classes="card-trend")

            # Middle row - progress and activity
            with Grid(classes="stats-grid"):
                with Vertical(classes="progress-section"):
                    yield Static("📝 Writing Goals", classes="section-title")

                    yield Static("Daily Word Count (500/1000)")
                    progress_daily = ProgressBar(total=1000, show_eta=False)
                    progress_daily.advance(500)
                    yield progress_daily

                    yield Static("Weekly Pages (12/20)")
                    progress_weekly = ProgressBar(total=20, show_eta=False)
                    progress_weekly.advance(23)
                    yield progress_weekly

                    yield Static("Monthly Projects (2/5)")
                    progress_monthly = ProgressBar(total=5, show_eta=False)
                    progress_monthly.advance(2)
                    yield progress_monthly

                with Vertical(classes="activity-section"):
                    yield Static("📈 Activity Trends", classes="section-title")

                    yield Static("Word Count (Last 30 days)")
                    # Sample data for sparkline
                    word_data = [
                        45,
                        67,
                        123,
                        89,
                        156,
                        200,
                        178,
                        145,
                        267,
                        189,
                        234,
                        178,
                        145,
                        267,
                        189,
                        123,
                        156,
                        200,
                        178,
                        267,
                        189,
                        234,
                        178,
                        145,
                        267,
                        189,
                        123,
                        156,
                        200,
                        267,
                    ]
                    yield Sparkline(word_data, summary_function=max)

                    yield Static("Task Completion Rate")
                    task_data = [
                        8,
                        6,
                        9,
                        7,
                        8,
                        5,
                        9,
                        8,
                        7,
                        6,
                        9,
                        8,
                        7,
                        6,
                        8,
                        9,
                        7,
                        8,
                        6,
                        9,
                        8,
                        7,
                        6,
                        9,
                        8,
                        7,
                        6,
                        8,
                        9,
                        7,
                    ]
                    yield Sparkline(task_data, summary_function=max)

            # Bottom row - recent activity
            with Vertical(classes="recent-activity"):
                yield Static("🕐 Recent Activity", classes="section-title")

                with Vertical(classes="activity-list"):
                    yield Static("• Completed task: 'Review Chapter 3' (2 hours ago)")
                    yield Static("• Added 347 words to 'Project Notes' (3 hours ago)")
                    yield Static(
                        "• Created new document: 'Meeting Minutes' " "(5 hours ago)"
                    )
                    yield Static("• Edited outline for 'Research Paper' (1 day ago)")
                    yield Static(
                        "• Completed task: 'Send follow-up emails' (1 day ago)"
                    )

    def on_mount(self) -> None:
        """Handle stats screen mount."""
        # Focus on the first element
        pass
