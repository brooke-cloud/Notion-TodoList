from dataclasses import dataclass


@dataclass
class Goal:
    id: str
    title: str
    status: str = "Not Started"
    notes: str = ""
    last_updated: str = ""


@dataclass(frozen=True)
class GoalProgress:
    goal: Goal
    total_tasks: int = 0
    completed_tasks: int = 0

    @property
    def percent(self) -> int:
        if self.goal.status == "Completed":
            return 100
        return round(self.completed_tasks / self.total_tasks * 100) if self.total_tasks else 0
