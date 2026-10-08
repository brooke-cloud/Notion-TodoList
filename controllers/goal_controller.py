from app.state import AppState
from models.goal import Goal, GoalProgress
from models.task import Task
from services.notion_service import NotionService


class GoalController:
    STATUS_LABELS = {
        "Not Started": "未开始",
        "In Progress": "进行中",
        "Completed": "已完成",
    }

    def __init__(self, app_state: AppState, notion_service: NotionService | None):
        self.app_state = app_state
        self.notion_service = notion_service

    def load_goals(self) -> list[Goal]:
        goals = self.notion_service.fetch_goals()
        self.app_state.goals = goals
        self.app_state.goals_available = True
        return goals

    def select_goal(self, goal_id: str | None) -> None:
        self.app_state.current_goal_id = goal_id
        goal = next((item for item in self.app_state.goals if item.id == goal_id), None)
        self.app_state.current_goal_title = goal.title if goal else None

    def filter_goals(self, value: str) -> list[Goal]:
        self.app_state.goal_filter = value
        mapping = {"进行中": "In Progress", "未开始": "Not Started", "已完成": "Completed"}
        status = mapping.get(value)
        return [goal for goal in self.app_state.goals if not status or goal.status == status]

    def progress_for(self, goal: Goal, tasks: list[Task]) -> GoalProgress:
        return self.calculate_goal_progress(goal, tasks)

    @staticmethod
    def calculate_goal_progress(goal: Goal, tasks: list[Task]) -> GoalProgress:
        """Shared progress source for the goal list, detail, banner and analytics."""
        related = [task for task in tasks if task.goal_id == goal.id]
        return GoalProgress(goal, len(related), sum(task.is_done for task in related))

    def progress_list(self, tasks: list[Task], goals: list[Goal] | None = None) -> list[GoalProgress]:
        return [self.progress_for(goal, tasks) for goal in (goals or self.app_state.goals)]

    def tasks_for_goal(self, goal_id: str, tasks: list[Task]) -> list[Task]:
        return [task for task in tasks if task.goal_id == goal_id]

    def create_goal(self, title: str, status: str = "Not Started", notes: str = "") -> Goal:
        goal = self.notion_service.create_goal(title, status, notes)
        self.app_state.goals.append(goal)
        return goal

    def update_goal(self, goal: Goal, title: str, status: str, notes: str) -> Goal:
        self.notion_service.update_goal(goal.id, title, status, notes)
        goal.title, goal.status, goal.notes = title, status, notes
        if self.app_state.current_goal_id == goal.id:
            self.app_state.current_goal_title = title
        return goal

    def delete_goal(self, goal: Goal) -> None:
        self.notion_service.delete_goal(goal.id)
        self.app_state.goals = [item for item in self.app_state.goals if item.id != goal.id]
