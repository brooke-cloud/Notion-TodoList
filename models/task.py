from dataclasses import dataclass


@dataclass
class Task:
    id: str
    title: str
    priority: str = "中"
    project: str = "未分类"
    notes: str = ""
    date: str = ""
    repeat_type: str = "单次"
    is_done: bool = False
    goal_id: str | None = None
    goal_title: str | None = None
