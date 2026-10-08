from dataclasses import dataclass, field
from datetime import date
from typing import Any

from models.task import Task
from models.goal import Goal


@dataclass
class AppState:
    settings: dict[str, Any]
    current_date: date = field(default_factory=date.today)
    current_view: str = "今天"
    cached_tasks: list[Task] = field(default_factory=list)
    displayed_tasks: list[Task] = field(default_factory=list)
    search_text: str = ""
    project_filter_value: str = "全部分类"
    is_loading: bool = False
    is_inline_editing: bool = False
    current_focus_task: str = "暂未选择专注任务"
    timer_running: bool = False
    current_time_left: int = 25 * 60
    timer_minutes: int = 25
    current_section: str = "tasks"
    current_goal_id: str | None = None
    current_goal_title: str | None = None
    goals: list[Goal] = field(default_factory=list)
    goal_tasks: list[Task] = field(default_factory=list)
    goal_filter: str = "全部"
    goals_available: bool = False
    goal_relation_available: bool = False
    is_goals_loading: bool = False
    goal_error: str = ""
    analytics_period: str = "本周"
