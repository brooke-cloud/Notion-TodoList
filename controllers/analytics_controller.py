from collections import Counter
from datetime import date, timedelta

from app.state import AppState
from controllers.goal_controller import GoalController


class AnalyticsController:
    """Pure application statistics; no Tk or Notion access."""

    def __init__(self, app_state: AppState, goal_controller: GoalController):
        self.app_state = app_state
        self.goal_controller = goal_controller

    def build(self, period="本周"):
        source = self.app_state.goal_tasks or self.app_state.cached_tasks
        tasks = self._tasks_in_period(source, period)
        total = len(tasks)
        completed = sum(task.is_done for task in tasks)
        categories = Counter(task.project or "未分类" for task in tasks)
        week_start = date.today() - timedelta(days=6)
        weekly = []
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            count = sum(task.is_done and task.date[:10] == day.isoformat() for task in source if task.date)
            weekly.append(("一二三四五六日"[offset], count))
        goals = [
            progress for progress in self.goal_controller.progress_list(source)
            if progress.goal.status == "In Progress"
        ][:5]
        return {
            "period": period,
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "rate": round(completed / total * 100) if total else 0,
            "weekly": weekly,
            "categories": categories.most_common(),
            "goals": goals,
        }

    @staticmethod
    def _tasks_in_period(tasks, period):
        if period == "全部":
            return list(tasks)
        today = date.today()
        if period == "本月":
            prefix = today.strftime("%Y-%m")
            return [task for task in tasks if task.date[:7] == prefix]
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        result = []
        for task in tasks:
            try:
                task_date = date.fromisoformat(task.date[:10])
            except (TypeError, ValueError):
                continue
            if start <= task_date <= end:
                result.append(task)
        return result
