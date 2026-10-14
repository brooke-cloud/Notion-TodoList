from __future__ import annotations

import json
import os
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from models.task import Task


SHANGHAI = ZoneInfo("Asia/Shanghai")


def shanghai_now() -> datetime:
    return datetime.now(SHANGHAI)


class DailyReportStore:
    """Atomic AppData-backed report and workflow journal storage."""

    def __init__(self, root: Path | None = None):
        if root is None:
            override = os.environ.get("NOTION_TODOLIST_REPORT_DIR")
            if override:
                root = Path(override)
        if root is None:
            local = os.environ.get("LOCALAPPDATA")
            base = Path(local) if local else Path.home() / "AppData" / "Local"
            root = base / "NotionTodoListV4" / "daily_reports"
        self.root = Path(root)
        self.reports = self.root / "reports"
        self.state_path = self.root / "workflow_state.json"

    @staticmethod
    def _read(path: Path, default):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default

    @staticmethod
    def _write(path: Path, payload) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)

    def load_state(self) -> dict:
        return self._read(self.state_path, {"days": {}, "last_seen_date": "", "shown": {}})

    def save_state(self, state: dict) -> None:
        self._write(self.state_path, state)

    def report_path(self, target: date) -> Path:
        return self.reports / f"{target.isoformat()}.json"

    def save_report(self, target: date, report: dict) -> None:
        self._write(self.report_path(target), report)

    def load_report(self, target: date) -> dict | None:
        path = self.report_path(target)
        return self._read(path, None) if path.exists() else None

    def history(self) -> list[dict]:
        if not self.reports.exists():
            return []
        result = []
        for path in sorted(self.reports.glob("*.json"), reverse=True):
            report = self._read(path, None)
            if report:
                result.append(report)
        return result


class DailyWorkflow:
    """Report-before-rollover coordinator with per-task retry journal."""

    def __init__(self, store: DailyReportStore, clock: Callable[[], datetime] = shanghai_now):
        self.store = store
        self.clock = clock

    @staticmethod
    def build_report(target: date, tasks: list[Task], *, accuracy: str) -> dict:
        completed = [task for task in tasks if task.is_done]
        pending = [task for task in tasks if not task.is_done]
        categories = {}
        for category in sorted({task.project or "未分类" for task in tasks}):
            group = [task for task in tasks if (task.project or "未分类") == category]
            categories[category] = {
                "total": len(group),
                "completed": sum(task.is_done for task in group),
            }
        priorities = Counter(task.priority or "未设置" for task in tasks)
        return {
            "date": target.isoformat(),
            "generated_at": shanghai_now().isoformat(),
            "timezone": "Asia/Shanghai",
            "accuracy": accuracy,
            "total": len(tasks),
            "completed": len(completed),
            "completion_rate": round(len(completed) * 100 / len(tasks), 1) if tasks else 0,
            "pending": len(pending),
            "auto_postponed": 0,
            "categories": categories,
            "priorities": dict(sorted(priorities.items())),
            "main_pending": [
                {"id": task.id, "title": task.title, "category": task.project, "priority": task.priority}
                for task in pending[:10]
            ],
        }

    def _dates_to_process(self, today: date, state: dict) -> list[date]:
        last_seen = state.get("last_seen_date")
        if last_seen:
            try:
                start = date.fromisoformat(last_seen)
            except ValueError:
                start = today - timedelta(days=1)
        else:
            start = today - timedelta(days=1)
        if start >= today:
            return []
        return [start + timedelta(days=offset) for offset in range((today - start).days)]

    def run(self, service, *, auto_postpone: bool = True) -> dict:
        now = self.clock().astimezone(SHANGHAI)
        today = now.date()
        state = self.store.load_state()
        processed = []
        for target in self._dates_to_process(today, state):
            day_key = target.isoformat()
            day_state = state.setdefault("days", {}).setdefault(day_key, {
                "report_saved": False, "completed_task_ids": [], "pending_task_ids": [], "complete": False,
            })
            if day_state.get("complete"):
                continue

            if not day_state.get("report_saved"):
                snapshot = service.fetch_tasks_for_date(target)
                accuracy = "captured_at_rollover" if target == today - timedelta(days=1) else "partial_historical_snapshot"
                report = self.build_report(target, snapshot, accuracy=accuracy)
                self.store.save_report(target, report)
                day_state["report_saved"] = True
                self.store.save_state(state)

            overdue = service.fetch_overdue_tasks(today) if auto_postpone else []
            completed_ids = set(day_state.get("completed_task_ids", []))
            candidates = []
            for task in overdue:
                if task.id in completed_ids:
                    continue
                if task.repeat_type == "每天":
                    candidates.append((task, "daily_reset"))
                elif not task.is_done:
                    candidates.append((task, "postpone"))

            day_state["pending_task_ids"] = [task.id for task, _ in candidates]
            self.store.save_state(state)
            moved = 0
            try:
                for task, operation in candidates:
                    if operation == "daily_reset":
                        service.reset_daily_task_to_date(task.id, today)
                    else:
                        service.move_task_to_date(task.id, today)
                    completed_ids.add(task.id)
                    moved += 1
                    day_state["completed_task_ids"] = sorted(completed_ids)
                    day_state["pending_task_ids"] = [item for item in day_state["pending_task_ids"] if item != task.id]
                    self.store.save_state(state)
            except Exception:
                self.store.save_state(state)
                raise

            report = self.store.load_report(target) or {}
            report["auto_postponed"] = len(completed_ids)
            today_tasks = service.fetch_tasks_for_date(today)
            report["today_tasks"] = [
                {"id": task.id, "title": task.title, "category": task.project, "priority": task.priority}
                for task in today_tasks if not task.is_done
            ][:15]
            self.store.save_report(target, report)
            day_state["complete"] = not day_state["pending_task_ids"]
            self.store.save_state(state)
            processed.append({"date": day_key, "moved": moved, "report": report})

        state["last_seen_date"] = today.isoformat()
        self.store.save_state(state)
        return {"today": today.isoformat(), "processed": processed}

    def report_for_auto_show(self) -> dict | None:
        today = self.clock().astimezone(SHANGHAI).date()
        target = today - timedelta(days=1)
        state = self.store.load_state()
        shown = state.setdefault("shown", {})
        report = self.store.load_report(target)
        if not report or shown.get(target.isoformat()) == today.isoformat():
            return None
        shown[target.isoformat()] = today.isoformat()
        self.store.save_state(state)
        return report
