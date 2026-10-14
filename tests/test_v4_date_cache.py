import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from models.task import Task
from models.goal import Goal, GoalProgress
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
    def update_goal(self, goal_id, title, status, notes):
        return None


class DetailService:
    def __init__(self): self.saved_status="unset";self.saved_repeat_type=None
    def update_task_detail(self, task_id, title, target_date, repeat_type, priority, project, notes, status_name=None):
        self.saved_status=status_name;self.saved_repeat_type=repeat_type


class FailingDetailService(DetailService):
    def update_task_detail(self, *args, **kwargs):
        super().update_task_detail(*args, **kwargs)
        raise RuntimeError("simulated detail failure")


class SlowMutationService:
    def __init__(self, delay=1.2):
        self.delay=delay;self.status_calls=[];self.relation_calls=[];self.goal_calls=[];self.fail_status=False;self.fail_relation=False
    def update_task_status(self, task_id, is_done, target_date=None, status_name=None):
        time.sleep(self.delay);self.status_calls.append(is_done)
        if self.fail_status:raise RuntimeError("simulated status failure")
    def update_task_goal_relation(self, task_id, goal_id=None):
        time.sleep(self.delay);self.relation_calls.append((task_id,goal_id))
        if self.fail_relation:raise RuntimeError("simulated relation failure")
    def update_goal(self, goal_id, title, status, notes):
        self.goal_calls.append((goal_id,status))


class GoalTaskCreationService(SlowMutationService):
    def __init__(self, created):
        super().__init__(0);self.created=created;self.created_visible=False
    def fetch_all_tasks(self):
        return [self.created] if self.created_visible else []
    def create_task(self, title, target, repeat_type, priority, category):
        self.created_visible=True


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

    def test_task_section_clears_goal_filter_without_reloading(self):
        goal_task=Task("goal-task","Goal task","中","工作",date=date.today().isoformat(),goal_id="goal")
        free_task=Task("free-task","Free task","中","学习",date=date.today().isoformat())
        self.bridge.task_model.set_tasks([goal_task,free_task])
        self.bridge.openGoal("goal")
        self.assertEqual(self.bridge.task_model.rowCount(),1)
        self.bridge.selectSection("tasks")
        self.assertEqual(self.bridge.task_model.rowCount(),2)

    def test_custom_focus_and_break_durations_apply_immediately(self):
        self.bridge._save_settings=lambda:None
        self.bridge.setFocusDurations(45,10)
        self.assertEqual(self.bridge.settings["default_focus_minutes"],45)
        self.assertEqual(self.bridge.settings["default_break_minutes"],10)
        self.assertEqual(self.bridge.focusMode,45)
        self.assertEqual(self.bridge.focusTime,"45:00")
        self.bridge.setFocusMode(self.bridge.settings["default_break_minutes"])
        self.assertEqual(self.bridge.focusTime,"10:00")

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

    def test_editor_preserves_status_and_keeps_current_completed_goal(self):
        active=Goal("active","Active","In Progress");completed=Goal("completed","Completed","Completed")
        self.bridge.goal_model.set_goals([active,completed],[GoalProgress(active),GoalProgress(completed)])
        task=Task("edit","Edit me","中","工作",date=date.today().isoformat(),status="进行中",goal_id="completed",goal_title="Completed")
        self.bridge._show_tasks([task]);captured=[];saved=[]
        self.bridge.taskEditRequested.connect(captured.append);self.bridge.taskSaveSucceeded.connect(saved.append)
        self.bridge.editTask(task.id)
        self.assertEqual({item["id"] for item in captured[0]["goalOptions"]},{"active","completed"})
        detail=DetailService();self.bridge.service=detail;self.bridge.todo.notion_service=detail
        self.bridge.updateTask(task.id,"Edited","学习","P1","每天",task.date,"completed")
        self.wait_until(lambda:bool(saved))
        self.assertEqual(task.status,"进行中");self.assertFalse(task.is_done);self.assertIsNone(detail.saved_status)
        self.assertEqual(task.goal_id,"completed");self.assertEqual(detail.saved_repeat_type,"每天")
        self.assertEqual(task.repeat_type,"每天")
        self.bridge.editTask(task.id)
        self.assertEqual(captured[-1]["repeatType"],"每天")

    def test_editor_repeat_type_rolls_back_when_notion_save_fails(self):
        task=Task("repeat-failure","Keep once","中","工作",date=date.today().isoformat(),repeat_type="单次")
        self.bridge._show_tasks([task]);failed=[];self.bridge.taskSaveFailed.connect(lambda *_:failed.append(True))
        detail=FailingDetailService();self.bridge.service=detail;self.bridge.todo.notion_service=detail
        self.bridge.updateTask(task.id,"Keep once","工作","P1","每天",task.date,"")
        self.wait_until(lambda:bool(failed))
        self.assertEqual(task.repeat_type,"单次")
        self.assertEqual(self.bridge.task_model.item(task.id)["repeatType"],"单次")

    def _prepare_goal_detail(self):
        goal=Goal("goal","Goal","In Progress");other=Goal("other","Other","In Progress")
        bound=Task("bound","Bound","中","工作",date=date.today().isoformat(),goal_id="other",goal_title="Other")
        free=Task("free","Free","中","学习",date=date.today().isoformat())
        self.bridge.goal_model.set_goals([goal,other],[GoalProgress(goal),GoalProgress(other,1,0)])
        self.bridge.state.goal_tasks=[bound,free];self.bridge.all_task_model.set_tasks([bound,free]);self.bridge.task_model.set_tasks([bound,free])
        self.bridge.openGoal("goal")
        return goal,bound,free

    def test_goal_detail_toggle_is_under_100ms_and_serializes_rapid_changes(self):
        goal,_,free=self._prepare_goal_detail();self.bridge._apply_relation_local(free.id,goal.id,goal.title)
        service=SlowMutationService();self.bridge.service=service
        started=time.perf_counter();self.bridge.toggleTaskDone(free.id);elapsed=(time.perf_counter()-started)*1000
        print(f"[V4 perf] optimistic goal toggle returned in {elapsed:.2f} ms")
        self.assertLess(elapsed,100);self.assertTrue(free.is_done);self.assertEqual(self.bridge.selectedGoal["progress"],100)
        self.bridge.toggleTaskDone(free.id);self.assertFalse(free.is_done);self.assertEqual(self.bridge.selectedGoal["progress"],0)
        self.wait_until(lambda:free.id not in self.bridge._toggle_sync,3500)
        self.assertEqual(service.status_calls,[True,False]);self.assertFalse(free.is_done)

    def test_goal_detail_toggle_failure_rolls_back_progress(self):
        goal,_,free=self._prepare_goal_detail();self.bridge._apply_relation_local(free.id,goal.id,goal.title)
        service=SlowMutationService(.15);service.fail_status=True;self.bridge.service=service
        self.bridge.toggleTaskDone(free.id);self.assertTrue(free.is_done);self.assertEqual(self.bridge.selectedGoal["completedTasks"],1)
        self.wait_until(lambda:free.id not in self.bridge._toggle_sync)
        self.assertFalse(free.is_done);self.assertEqual(self.bridge.selectedGoal["completedTasks"],0)

    def test_relation_filters_bound_tasks_and_rolls_back_failure(self):
        goal,bound,free=self._prepare_goal_detail();self.bridge.searchAllTasks("")
        self.assertEqual(self.bridge.all_task_model.rowCount(),1);self.assertEqual(self.bridge.all_task_model.idAt(0),free.id)
        service=SlowMutationService(.15);self.bridge.service=service
        started=time.perf_counter();self.bridge.addTaskToGoal(free.id,goal.id);elapsed=(time.perf_counter()-started)*1000
        print(f"[V4 perf] optimistic relation returned in {elapsed:.2f} ms")
        self.assertLess(elapsed,100);self.assertEqual(self.bridge.all_task_model.rowCount(),0);self.assertEqual(self.bridge.task_model.rowCount(),1)
        self.assertEqual(self.bridge.selectedGoal["totalTasks"],1)
        self.wait_until(lambda:free.id not in self.bridge._relation_pending)
        service.fail_relation=True;self.bridge.removeTaskFromGoal(free.id)
        self.assertEqual(self.bridge.task_model.rowCount(),0);self.assertEqual(self.bridge.selectedGoal["totalTasks"],0)
        self.wait_until(lambda:free.id not in self.bridge._relation_pending)
        self.assertEqual(free.goal_id,goal.id);self.assertEqual(self.bridge.task_model.rowCount(),1);self.assertEqual(self.bridge.selectedGoal["totalTasks"],1)

    def test_today_goal_task_is_cached_immediately_and_replaced_after_create(self):
        goal=Goal("goal","Goal","Not Started");self.bridge.goal_model.set_goals([goal],[GoalProgress(goal)])
        self.bridge.state.goal_tasks=[];self.bridge.all_task_model.set_tasks([]);self.bridge.task_model.set_tasks([]);self.bridge.openGoal(goal.id)
        today=date.today().isoformat();self.bridge.task_cache[today]=[]
        created=Task("real-task","Today child","中","工作",date=today)
        service=GoalTaskCreationService(created);self.bridge.service=service;self.bridge.todo.notion_service=service;self.bridge.goals.notion_service=service
        saved=[];self.bridge.smallTaskCreated.connect(lambda:saved.append(True))
        self.bridge.createTaskForCurrentGoal("Today child","工作","P1",today)
        self.assertEqual(len(self.bridge.task_cache[today]),1);self.assertTrue(self.bridge.task_cache[today][0].id.startswith("pending:"))
        self.assertEqual(self.bridge.task_model.rowCount(),1);self.assertEqual(self.bridge.selectedGoal["status"],"In Progress")
        self.wait_until(lambda:bool(saved));self.assertEqual(self.bridge.task_cache[today][0].id,"real-task")
        self.assertEqual(self.bridge.task_model.idAt(0),"real-task")

    def test_goal_auto_completes_then_reopens_when_unfinished_task_added(self):
        goal=Goal("goal","Goal","Not Started");task=Task("task","Task","中","工作",date=date.today().isoformat(),goal_id=goal.id,goal_title=goal.title)
        self.bridge.goal_model.set_goals([goal],[GoalProgress(goal,1,0)]);self.bridge.state.goal_tasks=[task]
        self.bridge.all_task_model.set_tasks([task]);self.bridge.task_model.set_tasks([task]);self.bridge.openGoal(goal.id)
        service=SlowMutationService(0);self.bridge.service=service
        self.bridge._reconcile_goal_status(goal.id);self.assertEqual(self.bridge.selectedGoal["status"],"In Progress")
        self.bridge.toggleTaskDone(task.id);self.assertEqual(self.bridge.selectedGoal["status"],"Completed");self.assertEqual(self.bridge.selectedGoal["progress"],100)
        self.wait_until(lambda:goal.id not in self.bridge._goal_status_sync)
        self.assertIn((goal.id,"Completed"),service.goal_calls)
        new_task=Task("new","New","中","学习",date=date.today().isoformat())
        self.bridge.state.goal_tasks.append(new_task);self.bridge.all_task_model.insert_task(new_task)
        self.bridge._apply_relation_local(new_task.id,goal.id,goal.title)
        self.assertEqual(self.bridge.selectedGoal["status"],"In Progress")
        self.wait_until(lambda:goal.id not in self.bridge._goal_status_sync)
        self.assertEqual(service.goal_calls[-1],(goal.id,"In Progress"))

    def test_manual_goal_status_updates_immediately_and_syncs_without_reload(self):
        goal=Goal("manual","Manual","Not Started")
        self.bridge.goal_model.set_goals([goal],[GoalProgress(goal)])
        self.bridge.openGoal(goal.id)
        service=SlowMutationService(0);self.bridge.service=service
        self.bridge.setGoalStatus(goal.id,"Completed")
        self.assertEqual(self.bridge.selectedGoal["status"],"Completed")
        self.assertEqual(self.bridge.selectedGoal["statusLabel"],"已完成")
        self.bridge._reconcile_all_goal_statuses()
        self.assertEqual(self.bridge.selectedGoal["status"],"Completed")
        self.wait_until(lambda:goal.id not in self.bridge._goal_status_sync)
        self.assertEqual(service.goal_calls,[(goal.id,"Completed")])
        self.bridge._goal_progress_delta(goal.id,total_delta=1)
        self.assertEqual(self.bridge.selectedGoal["status"],"In Progress")
        self.wait_until(lambda:goal.id not in self.bridge._goal_status_sync)
        self.assertEqual(service.goal_calls[-1],(goal.id,"In Progress"))


if __name__ == "__main__":
    unittest.main()
