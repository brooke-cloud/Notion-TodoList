from dataclasses import dataclass
from datetime import date


@dataclass
class DailyReportData:
    target_date: date
    completed_tasks: list[str]
    pending_tasks: list[str]
    completed_count: int
    pending_count: int
