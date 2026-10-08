import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from models.task import Task
from qt_app.app_bridge import AppBridge


class DelayedTaskService:
    def __init__(self):
        self.calls = []
        self.delays = {}
        self.versions = {}
        self.fail_dates = set()
        self.empty_dates = set()

    def fetch_tasks_for_date(self, target):
        call = len(self.calls) + 1
        self.calls.append(target)
        time.sleep(self.delays.get((target, call), self.delays.get(target, 0.02)))
        if target in self.fail_dates:
            raise RuntimeError("simulated network failure")
        if target in self.empty_dates:
            return []
        version = self.versions.get((target, call), call)
        return [Task(f"{target}-{version}", f"task-{target}-{version}", "中", "工作", date=target.isoformat())]

    def fetch_all_open_tasks(self):
        time.sleep(0.02)
        return []


class BridgeWithoutStartup(AppBridge):
    def initialize(self):
        pass


class DateCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.bridge = BridgeWithoutStartup(Path.cwd())
        self.service = DelayedTaskService()
        self.bridge.service = self.service
        self.bridge.todo.notion_service = self.service

    def wait_until(self, predicate, timeout=2500):
        loop = QEventLoop(); poll = QTimer(); poll.setInterval(10)
        poll.timeout.connect(lambda: loop.quit() if predicate() else None)
        QTimer.singleShot(timeout, loop.quit); poll.start(); loop.exec(); poll.stop()
        self.assertTrue(predicate())

    def test_cached_date_switch_renders_under_50ms(self):
        tomorrow = date.today() + timedelta(days=1)
        cached = [Task("cached", "cached tomorrow", "中", "工作", date=tomorrow.isoformat())]
        self.bridge.task_cache[tomorrow.isoformat()] = cached
        started = time.perf_counter(); self.bridge.setDateView("明天"); elapsed = (time.perf_counter() - started) * 1000
        self.assertLess(elapsed, 50)
        self.assertEqual(self.bridge.task_model.idAt(0), "cached")
        self.assertEqual(self.bridge.taskLoadState, "refreshing")

    def test_uncached_switch_returns_under_50ms_during_two_second_network_delay(self):
        tomorrow = date.today() + timedelta(days=1); self.service.delays[tomorrow] = 1.2
        started = time.perf_counter(); self.bridge.setDateView("明天"); elapsed = (time.perf_counter() - started) * 1000
        self.assertLess(elapsed, 50); self.assertEqual(self.bridge.dateView, "明天"); self.assertTrue(self.bridge.taskLoading)
        self.assertEqual(self.bridge.taskLoadState, "loading")
        self.wait_until(lambda: not self.bridge.taskLoading, 2200)
        self.assertEqual(self.bridge.taskLoadState, "idle")

    def test_old_request_never_overwrites_last_selected_date(self):
        today = date.today(); tomorrow = today + timedelta(days=1)
        self.service.delays[(today, 1)] = .35
        self.service.delays[(tomorrow, 2)] = .25
        self.service.delays[(today, 3)] = .05
        self.bridge.setDateView("今天"); self.bridge.setDateView("明天"); self.bridge.setDateView("今天")
        self.wait_until(lambda: not self.bridge.taskLoading)
        expected = f"{today}-3"
        self.assertEqual(self.bridge.dateView, "今天")
        self.assertEqual(self.bridge.task_model.idAt(0), expected)
        self.wait_until(lambda: len(self.service.calls) >= 3)
        time.sleep(.4); self.app.processEvents()
        self.assertEqual(self.bridge.task_model.idAt(0), expected)
        self.assertEqual(self.bridge.task_cache[today.isoformat()][0].id, expected)

    def test_completion_edit_delete_and_postpone_keep_date_caches_consistent(self):
        today=date.today(); tomorrow=today+timedelta(days=1)
        task=Task("cache-task","original","中","工作",date=today.isoformat())
        self.bridge.task_cache[today.isoformat()]=[task]
        self.bridge.task_cache[tomorrow.isoformat()]=[]
        self.bridge._show_tasks([task])

        self.bridge._sync_task_cache(task.id,isDone=True,title="edited",category="学习",priority="高")
        self.assertTrue(task.is_done);self.assertEqual((task.title,task.project,task.priority),("edited","学习","高"))

        task.date=tomorrow.isoformat();self.bridge._move_task_date_cache(task,today.isoformat(),tomorrow.isoformat())
        self.assertFalse(self.bridge.task_cache[today.isoformat()])
        self.assertEqual(self.bridge.task_cache[tomorrow.isoformat()][0].id,task.id)

        self.bridge._remove_task_from_caches(task.id)
        self.assertFalse(self.bridge.task_cache[tomorrow.isoformat()])

    def test_empty_and_failure_leave_terminal_feedback_states(self):
        yesterday=date.today()-timedelta(days=1);self.service.empty_dates.add(yesterday)
        self.bridge.setDateView("昨天");self.wait_until(lambda:not self.bridge.taskLoading)
        self.assertEqual(self.bridge.taskLoadState,"idle");self.assertEqual(self.bridge.task_model.rowCount(),0)

        tomorrow=date.today()+timedelta(days=1);self.service.fail_dates.add(tomorrow)
        self.bridge.setDateView("明天");self.wait_until(lambda:self.bridge.taskLoadState=="error")
        self.assertIn("simulated network failure",self.bridge.taskLoadError)


if __name__ == "__main__":
    unittest.main()
