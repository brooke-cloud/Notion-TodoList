import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from models.task import Task
from qt_app.task_list_model import TaskListModel
from services.daily_workflow import DailyReportStore, DailyWorkflow


TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]


class MockNotionService:
    def __init__(self, tasks, fail_once_id=None):
        self.tasks = tasks
        self.fail_once_id = fail_once_id
        self.failed = False
        self.moves = []
        self.daily_resets = []

    def fetch_tasks_for_date(self, target):
        return [task for task in self.tasks if task.date[:10] == target.isoformat() or task.repeat_type == "每天"]

    def fetch_overdue_tasks(self, before):
        return [task for task in self.tasks if task.date and task.date[:10] < before.isoformat()]

    def _move(self, task_id, target, daily):
        if task_id == self.fail_once_id and not self.failed:
            self.failed = True
            raise RuntimeError("simulated network failure")
        task = next(task for task in self.tasks if task.id == task_id)
        task.date = target.isoformat()
        task.status = "未开始"
        task.is_done = False
        (self.daily_resets if daily else self.moves).append(task_id)

    def move_task_to_date(self, task_id, target):
        self._move(task_id, target, False)

    def reset_daily_task_to_date(self, task_id, target):
        self._move(task_id, target, True)


class DailyWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.store = DailyReportStore(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def workflow(self, iso_datetime):
        current = datetime.fromisoformat(iso_datetime).replace(tzinfo=TZ)
        return DailyWorkflow(self.store, clock=lambda: current)

    def test_2359_to_0001_generates_report_before_postponing(self):
        task = Task("late", "late", date="2026-10-08", status="进行中")
        service = MockNotionService([task])
        self.store.save_state({"days": {}, "last_seen_date": "2026-10-08", "shown": {}})
        self.workflow("2026-10-08T23:59:00").run(service)
        self.assertFalse(service.moves)
        result = self.workflow("2026-10-09T00:01:00").run(service)
        self.assertEqual(service.moves, ["late"])
        report = self.store.load_report(date(2026, 10, 8))
        self.assertEqual(report["pending"], 1)
        self.assertEqual(report["auto_postponed"], 1)
        self.assertEqual(result["today"], "2026-10-09")

    def test_first_start_and_double_start_are_idempotent(self):
        task = Task("one", "one", date="2026-10-07")
        service = MockNotionService([task])
        workflow = self.workflow("2026-10-08T09:00:00")
        workflow.run(service)
        workflow.run(service)
        self.assertEqual(service.moves, ["one"])
        self.assertEqual(len(self.store.history()), 1)

    def test_multiple_missed_days_are_archived_and_marked_partial(self):
        service = MockNotionService([Task("old", "old", date="2026-10-05")])
        self.store.save_state({"days": {}, "last_seen_date": "2026-10-05", "shown": {}})
        self.workflow("2026-10-08T08:00:00").run(service)
        history = self.store.history()
        self.assertEqual([item["date"] for item in history], ["2026-10-07", "2026-10-06", "2026-10-05"])
        self.assertTrue(all(item["accuracy"] == "partial_historical_snapshot" for item in history[1:]))

    def test_network_failure_keeps_retry_state_without_duplicate_move(self):
        first = Task("first", "first", date="2026-10-07")
        second = Task("second", "second", date="2026-10-07")
        service = MockNotionService([first, second], fail_once_id="second")
        workflow = self.workflow("2026-10-08T08:00:00")
        with self.assertRaisesRegex(RuntimeError, "network"):
            workflow.run(service)
        self.assertEqual(service.moves, ["first"])
        workflow.run(service)
        self.assertEqual(service.moves, ["first", "second"])
        state = self.store.load_state()["days"]["2026-10-07"]
        self.assertTrue(state["complete"])

    def test_completed_one_off_never_moves_and_daily_uses_reset_path(self):
        completed = Task("done", "done", date="2026-10-07", status="完成", is_done=True)
        daily = Task("daily", "daily", date="2026-10-07", repeat_type="每天", status="完成", is_done=True)
        service = MockNotionService([completed, daily])
        self.workflow("2026-10-08T08:00:00").run(service)
        self.assertNotIn("done", service.moves)
        self.assertEqual(service.daily_resets, ["daily"])

    def test_report_auto_show_only_once_per_day(self):
        service = MockNotionService([Task("one", "one", date="2026-10-07")])
        workflow = self.workflow("2026-10-08T08:00:00")
        workflow.run(service)
        self.assertIsNotNone(workflow.report_for_auto_show())
        self.assertIsNone(workflow.report_for_auto_show())


class StatusFilterTests(unittest.TestCase):
    def test_status_filter_uses_real_status_and_updates_immediately(self):
        model = TaskListModel()
        tasks = [
            Task("todo", "todo", status="未开始"),
            Task("doing", "doing", status="进行中"),
            Task("done", "done", status="完成", is_done=True),
        ]
        model.set_tasks(tasks)
        model.set_filters(status="进行中")
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.idAt(0), "doing")
        model.update("doing", status="完成", isDone=True)
        self.assertEqual(model.rowCount(), 0)
        model.set_filters(status="已完成")
        self.assertEqual({model.idAt(row) for row in range(model.rowCount())}, {"doing", "done"})


if __name__ == "__main__":
    unittest.main()
