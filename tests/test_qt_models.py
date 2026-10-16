import unittest
from types import SimpleNamespace
from PySide6.QtCore import QCoreApplication, QEventLoop, QThreadPool, QTimer

from models.goal import Goal, GoalProgress
from models.task import Task
from controllers.goal_controller import GoalController
from qt_app.goal_list_model import GoalListModel
from qt_app.task_list_model import TaskListModel
from qt_app.workers import Worker


class TaskListModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QCoreApplication.instance() or QCoreApplication([])
    def setUp(self):
        self.pending = Task("1", "pending", "中", "工作", date="2026-10-06")
        self.done = Task("2", "done", "低", "学习", date="2026-10-06", is_done=True)
        self.model = TaskListModel(); self.model.set_tasks([self.done, self.pending])

    def test_pending_tasks_sort_before_completed_and_move_back(self):
        self.assertEqual(self.model.idAt(0), "1")
        self.model.update("1", isDone=True)
        self.model.update("2", isDone=False)
        self.assertEqual(self.model.idAt(0), "2")

    def test_roles_and_filters_are_stable(self):
        self.assertIn(b"goalId", self.model.roleNames().values())
        self.assertIn(b"createdDate", self.model.roleNames().values())
        self.model.set_filters(category="工作")
        self.assertEqual(self.model.rowCount(), 1)
        self.assertEqual(self.model.idAt(0), "1")

    def test_card_date_uses_creation_date_without_changing_due_date(self):
        task=Task("created","created",date="2026-10-16",created_date="2026-09-28")
        model=TaskListModel();model.set_tasks([task]);item=model.item(task.id)
        self.assertEqual(item["date"],"2026-10-16")
        self.assertEqual(item["createdDate"],"2026-09-28")

    def test_insert_and_remove_use_incremental_model_updates(self):
        inserted = Task("3", "inserted", "高", "副业", date="2026-10-06")
        about_to_insert=[]; about_to_remove=[]
        self.model.rowsAboutToBeInserted.connect(lambda *_:about_to_insert.append(True))
        self.model.rowsAboutToBeRemoved.connect(lambda *_:about_to_remove.append(True))
        self.assertTrue(self.model.insert_task(inserted))
        self.assertEqual(len(about_to_insert),1)
        self.model.remove("3")
        self.assertEqual(len(about_to_remove),1)

    def test_relation_filter_removal_is_incremental(self):
        self.pending.goal_id="g"; self.model.set_tasks([self.pending]); self.model.set_filters(goal_id="g")
        removed=[]; self.model.rowsAboutToBeRemoved.connect(lambda *_:removed.append(True))
        self.model.update("1",goalId="")
        self.assertEqual(self.model.rowCount(),0); self.assertEqual(len(removed),1)

    def test_completion_paints_before_deferred_bottom_sort(self):
        self.model.update_completion("1",True,"完成",80)
        self.assertEqual(self.model.idAt(0),"1")
        role=next(role for role,name in self.model.ROLES.items() if name=="isDone")
        self.assertTrue(self.model.data(self.model.index(0),role))
        loop=QEventLoop();QTimer.singleShot(130,loop.quit);loop.exec()
        self.assertEqual(self.model.idAt(self.model.rowCount()-1),"1")


class GoalListModelTests(unittest.TestCase):
    def test_automatic_goal_status_rules(self):
        self.assertEqual(GoalController.automatic_status(0,0),"Not Started")
        self.assertEqual(GoalController.automatic_status(3,2),"In Progress")
        self.assertEqual(GoalController.automatic_status(3,3),"Completed")
    def test_goal_progress_comes_from_related_task_counts(self):
        goal = Goal("g", "goal", "Completed")
        model = GoalListModel(); model.set_goals([goal], [GoalProgress(goal, 3, 1)])
        role = next(role for role, name in model.ROLES.items() if name == "progress")
        self.assertEqual(model.data(model.index(0), role), 33)

    def test_insert_goal_is_incremental(self):
        model=GoalListModel(); model.set_goals([],[]); events=[]
        model.rowsAboutToBeInserted.connect(lambda *_:events.append(True))
        goal=Goal("g2","new","In Progress")
        self.assertTrue(model.insert_goal(goal,GoalProgress(goal,0,0)))
        self.assertEqual(model.rowCount(),1); self.assertEqual(len(events),1)

    def test_status_filters_use_real_goal_status_immediately(self):
        goals=[Goal("todo","todo","Not Started"),Goal("doing","doing","In Progress"),Goal("done","done","Completed")]
        model=GoalListModel();model.set_goals(goals,[GoalProgress(goal,0,0) for goal in goals])
        for label,expected in (("未开始","todo"),("进行中","doing"),("已完成","done")):
            model.set_filters(status=label)
            self.assertEqual(model.rowCount(),1);self.assertEqual(model.idAt(0),expected)
        model.set_filters(status="全部");self.assertEqual(model.rowCount(),3)

    def test_completed_status_moves_between_goal_filters_and_keeps_progress(self):
        goal=Goal("g","goal","In Progress");model=GoalListModel();model.set_goals([goal],[GoalProgress(goal,2,2)])
        model.set_filters(status="进行中");self.assertEqual(model.rowCount(),1)
        model.update(goal.id,status="Completed",progress=100)
        self.assertEqual(model.rowCount(),0)
        model.set_filters(status="已完成");self.assertEqual(model.rowCount(),1)
        item=model.item(goal.id);self.assertEqual(item["statusLabel"],"已完成");self.assertEqual(item["progress"],100)


class WorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QCoreApplication.instance() or QCoreApplication([])

    def _run_worker(self, function):
        result={}; worker=Worker(function)
        worker.signals.succeeded.connect(lambda value:result.update(value=value))
        worker.signals.failed.connect(lambda message:result.update(error=message))
        worker.signals.finished.connect(self.app.quit)
        QThreadPool.globalInstance().start(worker); self.app.exec()
        return result

    def test_network_exception_reaches_main_thread_signal(self):
        result=self._run_worker(lambda:(_ for _ in ()).throw(RuntimeError("network down")))
        self.assertEqual(result.get("error"),"network down")

    def test_worker_success_reaches_main_thread_signal(self):
        self.assertEqual(self._run_worker(lambda:42).get("value"),42)


if __name__ == "__main__":
    unittest.main()
