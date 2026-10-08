from datetime import date, timedelta

from app.state import AppState
from controllers.report_data import DailyReportData
from models.task import Task
from services.notion_service import NotionService


class TodoController:
    def __init__(self, app_state: AppState, notion_service: NotionService):
        self.app_state = app_state
        self.notion_service = notion_service

    def set_view(self, selected: str):
        self.app_state.current_view = selected
        if selected == "今天":
            self.app_state.current_date = date.today()
        elif selected == "昨天":
            self.app_state.current_date = date.today() - timedelta(days=1)
        elif selected == "明天":
            self.app_state.current_date = date.today() + timedelta(days=1)

    def go_to_today(self):
        self.set_view("今天")

    def select_date(self, picked_date: date):
        self.app_state.current_date = picked_date
        if picked_date == date.today():
            self.app_state.current_view = "今天"
        elif picked_date == date.today() - timedelta(days=1):
            self.app_state.current_view = "昨天"
        elif picked_date == date.today() + timedelta(days=1):
            self.app_state.current_view = "明天"
        else:
            self.app_state.current_view = "日期"

    def set_search_text(self, text: str) -> list[Task]:
        self.app_state.search_text = text.strip().lower()
        return self.apply_filters()

    def set_project_filter(self, value: str) -> list[Task]:
        self.app_state.project_filter_value = value
        return self.apply_filters()

    def apply_filters(self) -> list[Task]:
        tasks = []
        for task in self.app_state.cached_tasks:
            searchable = f"{task.title} {task.notes} {task.project}".lower()
            if self.app_state.search_text and self.app_state.search_text not in searchable:
                continue
            if self.app_state.project_filter_value != "全部分类" and task.project != self.app_state.project_filter_value:
                continue
            if self.app_state.current_goal_id == "__unbound__" and task.goal_id is not None:
                continue
            if self.app_state.current_goal_id not in (None, "__unbound__") and task.goal_id != self.app_state.current_goal_id:
                continue
            tasks.append(task)
        self.app_state.displayed_tasks = tasks
        return tasks

    def load_tasks(self, view: str, target_date: date) -> list[Task]:
        if view == "全部":
            return self.notion_service.fetch_all_open_tasks()
        return self.notion_service.fetch_tasks_for_date(target_date)

    def accept_loaded_tasks(
        self,
        view: str,
        target_date: date,
        tasks: list[Task],
        goal_id: str | None = None,
    ) -> list[Task] | None:
        # 请求返回时仅接受仍与当前页面匹配的数据。
        if view != self.app_state.current_view:
            return None
        if view != "全部" and target_date != self.app_state.current_date:
            return None
        if goal_id != self.app_state.current_goal_id:
            return None
        self.app_state.cached_tasks = tasks
        return self.apply_filters()

    def create_task(self, title: str) -> None:
        repeat_type = "单次"
        priority = "中"
        project = self.app_state.project_filter_value
        if project == "全部分类":
            project = "未分类"
        self.notion_service.create_task(
            title, self.app_state.current_date, repeat_type, priority, project,
            goal_id=self.app_state.current_goal_id,
        )

    def set_goal_filter(self, goal_id: str | None) -> list[Task]:
        self.app_state.current_goal_id = goal_id
        return self.apply_filters()

    def rename_task(self, task: Task, new_title: str) -> None:
        old_title = task.title
        self.notion_service.update_task_title(task.id, new_title)
        task.title = new_title
        for collection in (self.app_state.cached_tasks, self.app_state.displayed_tasks, self.app_state.goal_tasks):
            for cached in collection:
                if cached.id == task.id:
                    cached.title = new_title
        if self.app_state.current_focus_task == old_title:
            self.app_state.current_focus_task = new_title

    def toggle_task(self, task: Task) -> bool:
        old_state = task.is_done
        new_state = not old_state
        task.is_done = new_state
        target_date = self.app_state.current_date if task.repeat_type == "每天" else None
        try:
            self.notion_service.update_task_status(task.id, new_state, target_date)
        except Exception:
            task.is_done = old_state
            self._sync_task_done(task.id, old_state)
            raise
        self._sync_task_done(task.id, new_state)
        return new_state

    def postpone_task(self, task: Task) -> date:
        tomorrow = date.today() + timedelta(days=1)
        self.notion_service.move_task_to_date(task.id, tomorrow)
        task.date = tomorrow.isoformat()
        self._sync_task_date(task.id, tomorrow.isoformat())
        return tomorrow

    def update_task_metadata(self, task: Task, *, project=None, priority=None, task_date=None) -> None:
        """Persist an inline metadata edit and keep every cached task instance aligned."""
        old_project, old_priority, old_date = task.project, task.priority, task.date
        if project is not None:
            task.project = project
        if priority is not None:
            task.priority = priority
        if task_date is not None:
            task.date = task_date
        try:
            target_date = date.fromisoformat(task.date[:10]) if task.date else None
            self.notion_service.update_task_detail(
                task.id, task.title, target_date, task.repeat_type, task.priority, task.project, task.notes
            )
        except Exception:
            task.project, task.priority, task.date = old_project, old_priority, old_date
            self._sync_task_metadata(task.id, old_project, old_priority, old_date)
            raise
        self._sync_task_metadata(task.id, task.project, task.priority, task.date)

    def update_task_fields(self, task: Task, title: str, project: str, priority: str, task_date: str) -> None:
        """Persist the complete task editor with one Notion page update."""
        related = []
        seen = set()
        for collection in (self.app_state.cached_tasks, self.app_state.displayed_tasks, self.app_state.goal_tasks):
            for item in collection:
                if item.id == task.id and id(item) not in seen:
                    seen.add(id(item)); related.append(item)
        if id(task) not in seen:
            related.append(task)
        snapshots = [(item, item.title, item.project, item.priority, item.date) for item in related]
        old_focus_title = self.app_state.current_focus_task
        for item in related:
            item.title, item.project, item.priority, item.date = title, project, priority, task_date
        try:
            target_date = date.fromisoformat(task_date[:10]) if task_date else None
            self.notion_service.update_task_detail(
                task.id, title, target_date, task.repeat_type, priority, project, task.notes
            )
        except Exception:
            for item, old_title, old_project, old_priority, old_date in snapshots:
                item.title, item.project, item.priority, item.date = old_title, old_project, old_priority, old_date
            self.app_state.current_focus_task = old_focus_title
            raise
        if old_focus_title == snapshots[0][1]:
            self.app_state.current_focus_task = title

    def get_postponable_tasks(self) -> list[Task]:
        return [
            task for task in self.app_state.cached_tasks
            if not task.is_done and task.repeat_type != "每天" and task.date
        ]

    def postpone_tasks(self, tasks: list[Task]) -> int:
        tomorrow = date.today() + timedelta(days=1)
        completed = 0
        for task in tasks:
            self.notion_service.move_task_to_date(task.id, tomorrow)
            task.date = tomorrow.isoformat()
            self._sync_task_date(task.id, tomorrow.isoformat())
            completed += 1
        return completed

    def delete_task(self, task: Task) -> None:
        self.notion_service.delete_task(task.id)
        self.app_state.cached_tasks = [cached for cached in self.app_state.cached_tasks if cached.id != task.id]
        self.app_state.goal_tasks = [cached for cached in self.app_state.goal_tasks if cached.id != task.id]
        self.apply_filters()

    def build_daily_report(self, target_date: date) -> DailyReportData:
        tasks = self.notion_service.fetch_tasks_for_date(target_date)
        completed = []
        pending = []
        for task in tasks:
            tags = []
            if self.notion_service.priority_supported:
                tags.append(task.priority)
            if self.notion_service.project_supported:
                tags.append(task.project)
            if task.repeat_type == "每天":
                tags.append("日常")
            prefix = "".join(f"[{tag}] " for tag in tags)
            text = prefix + task.title
            if task.is_done:
                completed.append(text)
            else:
                pending.append(text)
        return DailyReportData(
            target_date=target_date,
            completed_tasks=completed,
            pending_tasks=pending,
            completed_count=len(completed),
            pending_count=len(pending),
        )

    def set_timer_mode(self, minutes: int) -> int:
        self.app_state.timer_running = False
        self.app_state.timer_minutes = minutes
        self.app_state.current_time_left = minutes * 60
        return self.app_state.current_time_left

    def set_timer_running(self, running: bool) -> bool:
        self.app_state.timer_running = running
        return self.app_state.timer_running

    def reset_timer(self) -> int:
        self.app_state.timer_running = False
        self.app_state.timer_minutes = 25
        self.app_state.current_time_left = 25 * 60
        return self.app_state.current_time_left

    def tick_timer(self) -> int:
        if self.app_state.timer_running and self.app_state.current_time_left > 0:
            self.app_state.current_time_left -= 1
        if self.app_state.current_time_left <= 0:
            self.app_state.timer_running = False
        return self.app_state.current_time_left

    def select_focus_task(self, task_title: str) -> str:
        self.app_state.current_focus_task = task_title
        return self.app_state.current_focus_task

    def update_settings(self, new_settings: dict) -> None:
        self.app_state.settings = new_settings

    def _sync_task_done(self, task_id: str, is_done: bool) -> None:
        for collection in (self.app_state.cached_tasks, self.app_state.displayed_tasks, self.app_state.goal_tasks):
            for cached in collection:
                if cached.id == task_id:
                    cached.is_done = is_done

    def _sync_task_date(self, task_id: str, task_date: str) -> None:
        for collection in (self.app_state.cached_tasks, self.app_state.displayed_tasks, self.app_state.goal_tasks):
            for cached in collection:
                if cached.id == task_id:
                    cached.date = task_date

    def _sync_task_metadata(self, task_id: str, project: str, priority: str, task_date: str) -> None:
        for collection in (self.app_state.cached_tasks, self.app_state.displayed_tasks, self.app_state.goal_tasks):
            for cached in collection:
                if cached.id == task_id:
                    cached.project, cached.priority, cached.date = project, priority, task_date
