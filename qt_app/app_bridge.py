from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from PySide6.QtCore import Property, QObject, QThreadPool, QTimer, Signal, Slot
from app.state import AppState
from controllers.analytics_controller import AnalyticsController
from controllers.goal_controller import GoalController
from controllers.todo_controller import TodoController
from services.notion_service import NotionService
from .goal_list_model import GoalListModel
from .task_list_model import TaskListModel
from .workers import Worker


class AppBridge(QObject):
    sectionChanged=Signal(); syncChanged=Signal(); summaryChanged=Signal(); focusChanged=Signal()
    dateViewChanged=Signal(); taskLoadingChanged=Signal(); taskLoadStateChanged=Signal()
    selectedGoalChanged=Signal(); analyticsChanged=Signal(); settingsChanged=Signal()
    toastRequested=Signal(str,str); taskEditRequested=Signal(dict); goalCreateRequested=Signal()
    taskSaveSucceeded=Signal(str); taskSaveFailed=Signal(str,str); goalCreateSucceeded=Signal(); goalCreateFailed=Signal(str)
    smallTaskCreated=Signal(); smallTaskFailed=Signal(str); relationBatchFinished=Signal(int,int)

    def __init__(self,base_dir:Path,parent=None):
        super().__init__(parent); self.base_dir=Path(base_dir); self.state=AppState(settings=self._load_settings())
        extra_defaults={"auto_sync_enabled":False,"sync_on_startup":True,"completed_tasks_to_bottom":True,"default_focus_minutes":25,"default_break_minutes":5,"show_background_image":True,"background_opacity":72,"ui_scale":100,"notifications_enabled":True}
        for key,value in extra_defaults.items():self.state.settings.setdefault(key,value)
        self.service=None; self.todo=TodoController(self.state,None); self.goals=GoalController(self.state,None)
        self.analytics=AnalyticsController(self.state,self.goals); self.task_model=TaskListModel(self); self.all_task_model=TaskListModel(self); self.goal_model=GoalListModel(self)
        self.pool=QThreadPool.globalInstance(); self._workers=set(); self._section="tasks"; self._sync_text="正在同步"; self._selected_goal_id=""; self._analytics_data={}
        self.task_cache={}; self.task_request_generation=0; self._task_cache_generation={}; self._task_loading=False; self._task_requests=set()
        self._task_load_state="idle";self._task_load_error=""
        self._timer=QTimer(self); self._timer.setInterval(1000); self._timer.timeout.connect(self._tick_focus)
        self._auto_sync_timer=QTimer(self); self._auto_sync_timer.timeout.connect(self.loadAll)
        self._apply_startup_settings(); QTimer.singleShot(0,self.initialize)

    def _load_settings(self):
        defaults={"appearance_mode":"Dark","auto_sync_seconds":1800,"startup_page":"任务","default_date_view":"今天"}
        try:return {**defaults,**json.loads((self.base_dir/"settings.json").read_text(encoding="utf-8"))}
        except (OSError,ValueError):return defaults
    def _save_settings(self):
        try:(self.base_dir/"settings.json").write_text(json.dumps(self.state.settings,ensure_ascii=False,indent=2),encoding="utf-8")
        except OSError as exc:self.toastRequested.emit(str(exc),"error")
    def _apply_settings_runtime(self):
        if self.state.settings.get("auto_sync_enabled",False):
            self._auto_sync_timer.start(max(60,int(self.state.settings.get("auto_sync_seconds",1800)))*1000)
        else:self._auto_sync_timer.stop()
    def _apply_startup_settings(self):
        self._section={"大目标":"goals","统计分析":"analytics"}.get(self.state.settings.get("startup_page"),"tasks")
        view=self.state.settings.get("default_date_view","今天")
        if view in ("今天","明天","全部"):self.todo.set_view(view)
        self.todo.set_timer_mode(int(self.state.settings.get("default_focus_minutes",25)))
        sort_completed=bool(self.state.settings.get("completed_tasks_to_bottom",True))
        self.task_model.completed_to_bottom=sort_completed;self.all_task_model.completed_to_bottom=sort_completed
        self._apply_settings_runtime()
    def _run(self,function,success=None,failure=None):
        worker=Worker(function); self._workers.add(worker)
        if success:worker.signals.succeeded.connect(success)
        worker.signals.failed.connect(failure or (lambda message:self.toastRequested.emit(message,"error")))
        worker.signals.finished.connect(lambda:self._workers.discard(worker)); self.pool.start(worker)

    @Slot()
    def initialize(self):
        self._sync_text="正在同步"; self.syncChanged.emit()
        def ready(service):self.service=service; self.todo.notion_service=service; self.goals.notion_service=service; self.state.goal_relation_available=service.goal_relation_available; self.loadAll()
        self._run(NotionService,ready,lambda message:self._sync_failed(message))
    def _sync_failed(self,message):self._sync_text="同步失败"; self.syncChanged.emit(); self.toastRequested.emit(message,"error")

    @Property(str,notify=sectionChanged)
    def section(self):return self._section
    @Property(str,notify=syncChanged)
    def syncText(self):return self._sync_text
    @Property(str,notify=dateViewChanged)
    def dateView(self):return self.state.current_view
    @Property(str,notify=dateViewChanged)
    def taskViewTitle(self):return "全部任务" if self.state.current_view=="全部" else self.state.current_view
    @Property(bool,notify=taskLoadingChanged)
    def taskLoading(self):return self._task_loading
    @Property(str,notify=taskLoadStateChanged)
    def taskLoadState(self):return self._task_load_state
    @Property(str,notify=taskLoadStateChanged)
    def taskLoadError(self):return self._task_load_error
    @Property(int,notify=summaryChanged)
    def pendingCount(self):return sum(not item["isDone"] for item in self.task_model._all)
    @Property(int,notify=summaryChanged)
    def completedCount(self):return sum(item["isDone"] for item in self.task_model._all)
    @Property('QVariantList',notify=summaryChanged)
    def categorySummary(self):
        counts={}
        for item in self.all_task_model._all or self.task_model._all:
            name=item.get("category") or "未分类"; counts[name]=counts.get(name,0)+1
        preferred=["工作","学习","副业","生活"]
        names=preferred+[name for name in sorted(counts) if name not in preferred]
        return [{"name":name,"count":counts.get(name,0)} for name in names[:6]]
    @Property(str,notify=focusChanged)
    def focusTime(self):
        seconds=self.state.current_time_left; return f"{seconds//60:02d}:{seconds%60:02d}"
    @Property(bool,notify=focusChanged)
    def focusRunning(self):return self.state.timer_running
    @Property(int,notify=focusChanged)
    def focusMode(self):return self.state.timer_minutes
    @Property(str,notify=focusChanged)
    def focusTaskTitle(self):return self.state.current_focus_task
    @Property(str,notify=selectedGoalChanged)
    def selectedGoalId(self):return self._selected_goal_id
    @Property('QVariantMap',notify=selectedGoalChanged)
    def selectedGoal(self):return {k:v for k,v in (self.goal_model.item(self._selected_goal_id) or {}).items() if not k.startswith("_")}
    @Property('QVariantMap',notify=analyticsChanged)
    def analyticsData(self):return self._analytics_data
    @Property('QVariantMap',notify=settingsChanged)
    def settings(self):return self.state.settings

    @Slot(str)
    def selectSection(self,value):self._section=value; self.sectionChanged.emit(); self.refreshAnalytics() if value=="analytics" else None
    @Slot()
    def loadAll(self):
        if not self.service:return
        self._request_current_tasks()
        self._refresh_reference_data()

    def _cache_key(self,view,target):
        return "all" if view=="全部" else target.isoformat()

    @staticmethod
    def _task_signature(tasks):
        return [(task.id,task.title,task.project,task.priority,task.date,task.repeat_type,bool(task.is_done),task.goal_id,task.goal_title) for task in tasks]

    def _set_task_loading(self,value):
        value=bool(value)
        if self._task_loading!=value:self._task_loading=value;self.taskLoadingChanged.emit()

    def _set_task_load_state(self,state,error=""):
        if self._task_load_state!=state or self._task_load_error!=error:
            self._task_load_state=state;self._task_load_error=error;self.taskLoadStateChanged.emit()

    def _show_tasks(self,tasks):
        self.state.cached_tasks=list(tasks);self.state.displayed_tasks=list(tasks)
        self.task_model.sync_tasks(tasks);self.summaryChanged.emit()

    def _request_current_tasks(self):
        self.task_request_generation+=1
        generation=self.task_request_generation;view=self.state.current_view;target=self.state.current_date
        key=self._cache_key(view,target);cached=self.task_cache.get(key)
        started=perf_counter()
        if cached is not None:
            self._show_tasks(cached);self._set_task_loading(False);self._set_task_load_state("refreshing")
            print(f"[V4 perf] date selected/rendered from cache in {(perf_counter()-started)*1000:.2f} ms key={key}")
        else:
            self._show_tasks([]);self._set_task_loading(True);self._set_task_load_state("loading");self._sync_text="正在后台加载…";self.syncChanged.emit()
            print(f"[V4 perf] date selected in {(perf_counter()-started)*1000:.2f} ms; background load key={key}")
        self._fetch_task_view(view,target,key,generation,foreground=True)

    def _fetch_task_view(self,view,target,key,generation,foreground=False):
        request_token=(key,generation if foreground else "prefetch")
        if request_token in self._task_requests:return
        self._task_requests.add(request_token)
        def accept(tasks):
            self._task_requests.discard(request_token)
            old=self.task_cache.get(key)
            if generation>=self._task_cache_generation.get(key,-1):
                self.task_cache[key]=list(tasks);self._task_cache_generation[key]=generation
            if foreground and generation==self.task_request_generation and view==self.state.current_view and (view=="全部" or target==self.state.current_date):
                if old is None or self._task_signature(old)!=self._task_signature(tasks):self._show_tasks(tasks)
                self._set_task_loading(False);self._set_task_load_state("idle");self._sync_text=f"已同步 {len(tasks)} 项 · 刚刚更新";self.syncChanged.emit()
                if view=="今天":self._preload_adjacent_dates()
        def failed(message):
            self._task_requests.discard(request_token)
            if foreground and generation==self.task_request_generation:
                self._set_task_loading(False);self._set_task_load_state("error",message);self._sync_failed(message)
        self._run(lambda:self.todo.load_tasks(view,target),accept,failed)

    def _preload_adjacent_dates(self):
        for target in (date.today()-timedelta(days=1),date.today()+timedelta(days=1)):
            key=self._cache_key("日期",target)
            self._fetch_task_view("日期",target,key,self.task_request_generation,foreground=False)

    def _refresh_reference_data(self):
        def fetch():return self.goals.load_goals(),self.service.fetch_all_tasks()
        def accept(payload):
            goals,all_tasks=payload;titles={g.id:g.title for g in goals}
            for task in all_tasks:task.goal_title=titles.get(task.goal_id)
            for tasks in self.task_cache.values():
                for task in tasks:task.goal_title=titles.get(task.goal_id)
            self.state.goal_tasks=all_tasks;self.all_task_model.sync_tasks(all_tasks)
            self.goal_model.set_goals(goals,self.goals.progress_list(all_tasks,goals));self.refreshAnalytics()
            current=self.task_cache.get(self._cache_key(self.state.current_view,self.state.current_date))
            if current is not None:self._show_tasks(current)
        self._run(fetch,accept,lambda message:self.toastRequested.emit(message,"error"))
    @Slot(str)
    def setDateView(self,value):
        started=perf_counter();self.todo.set_view(value);self.dateViewChanged.emit();self._request_current_tasks()
        print(f"[V4 perf] date click callback returned in {(perf_counter()-started)*1000:.2f} ms view={value}")
    @Slot()
    def retryCurrentTasks(self):self._request_current_tasks()
    @Slot(str)
    def searchTasks(self,text):self.task_model.set_filters(query=text)
    @Slot(str)
    def searchAllTasks(self,text):self.all_task_model.set_filters(query=text)
    @Slot(str)
    def filterCategory(self,value):self.task_model.set_filters(category=value)
    @Slot(str)
    def filterTaskGoal(self,goal_id):self.task_model.set_filters(goal_id=goal_id)
    @Slot(str)
    def createTask(self,title):
        if title.strip():self._run(lambda:self.todo.create_task(title.strip()),lambda _:self._request_current_tasks())
    def _task(self,task_id):return self.task_model.task_object(task_id)
    def _sync_task_cache(self,task_id,**changes):
        attributes={"title":"title","category":"project","priority":"priority","date":"date","isDone":"is_done","goalId":"goal_id","goalTitle":"goal_title"}
        for tasks in self.task_cache.values():
            for cached in tasks:
                if cached.id==task_id:
                    for key,value in changes.items():setattr(cached,attributes.get(key,key),value)

    def _remove_task_from_caches(self,task_id):
        for key,tasks in list(self.task_cache.items()):self.task_cache[key]=[task for task in tasks if task.id!=task_id]

    def _move_task_date_cache(self,task,old_date,new_date):
        old_key=(old_date or "")[:10];new_key=(new_date or "")[:10]
        if old_key in self.task_cache:self.task_cache[old_key]=[cached for cached in self.task_cache[old_key] if cached.id!=task.id]
        if new_key in self.task_cache and not any(cached.id==task.id for cached in self.task_cache[new_key]):self.task_cache[new_key].append(task)

    @Slot(str)
    def toggleTaskDone(self,task_id):
        task=self._task(task_id)
        if not task:return
        old=task.is_done; self.task_model.update(task_id,isDone=not old); self.summaryChanged.emit()
        def saved(_):self._sync_task_cache(task_id,isDone=task.is_done);self.summaryChanged.emit()
        self._run(lambda:self.todo.toggle_task(task),saved,lambda msg:self._rollback_task(task_id,{"isDone":old},msg))
    @Slot(str)
    def postponeTask(self,task_id):
        task=self._task(task_id)
        if not task:return
        old=task.date; tomorrow=(date.today()+timedelta(days=1)).isoformat()
        self.task_model.update(task_id,date=tomorrow);self._sync_task_cache(task_id,date=tomorrow);self._move_task_date_cache(task,old,tomorrow)
        def saved(_):
            current_key=self._cache_key(self.state.current_view,self.state.current_date)
            if current_key!=(tomorrow[:10]) and self.state.current_view!="全部":self.task_model.remove(task_id);self.summaryChanged.emit()
        def failed(msg):
            self._sync_task_cache(task_id,date=old);self._move_task_date_cache(task,tomorrow,old)
            self._rollback_task(task_id,{"date":old},msg)
        self._run(lambda:self.todo.postpone_task(task),saved,failed)
    @Slot(str)
    def deleteTask(self,task_id):
        task=self._task(task_id)
        if task:self._run(lambda:self.todo.delete_task(task),lambda _:(self._remove_task_from_caches(task_id),self.task_model.remove(task_id),self.summaryChanged.emit()))
    @Slot(str)
    def editTask(self,task_id):
        item=self.task_model.item(task_id)
        if item:self.taskEditRequested.emit({key:item.get(key,"") for key in TaskListModel.FIELDS})
    @Slot(str,str,str,str,str,str)
    def updateTask(self,task_id,title,category,priority,task_date,goal_id):
        task=self._task(task_id)
        if not task:return
        notion_priority={"P0":"高","P1":"中","P2":"低"}.get(priority,priority); goal=self.goal_model.item(goal_id)
        snapshot={"title":task.title,"category":task.project,"priority":{"高":"P0","中":"P1","低":"P2"}.get(task.priority,task.priority),"date":task.date[:10],"goalId":task.goal_id or "","goalTitle":task.goal_title or ""}
        changes={"title":title,"category":category,"priority":priority,"date":task_date,"goalId":goal_id,"goalTitle":goal["title"] if goal else ""}; self.task_model.update(task_id,**changes)
        old_goal=task.goal_id or ""
        def save():
            self.todo.update_task_fields(task,title,category,notion_priority,task_date)
            if old_goal!=goal_id:
                try:
                    self.service.update_task_goal_relation(task.id,goal_id or None)
                except Exception as relation_error:
                    old_priority={"P0":"高","P1":"中","P2":"低"}.get(snapshot["priority"],snapshot["priority"])
                    try:
                        self.todo.update_task_fields(task,snapshot["title"],snapshot["category"],old_priority,snapshot["date"])
                    except Exception as compensation_error:
                        raise RuntimeError(
                            "部分数据已写入 Notion，请重新同步确认。"
                            f" Relation: {relation_error}; rollback: {compensation_error}"
                        ) from compensation_error
                    raise RuntimeError(f"大目标关联保存失败，普通字段已回滚：{relation_error}") from relation_error
        def saved(_):
            self._sync_task_cache(task_id,title=title,category=category,priority=notion_priority,date=task_date,goalId=goal_id,goalTitle=changes["goalTitle"])
            if snapshot["date"]!=task_date:self._move_task_date_cache(task,snapshot["date"],task_date)
            current=self.task_cache.get(self._cache_key(self.state.current_view,self.state.current_date))
            if current is not None:self._show_tasks(current)
            self.taskSaveSucceeded.emit(task_id);self._refresh_reference_data()
        def failed(msg):self._rollback_task(task_id,snapshot,msg);self.taskSaveFailed.emit(task_id,msg)
        self._run(save,saved,failed)
    def _rollback_task(self,task_id,snapshot,message):self.task_model.update(task_id,**snapshot); self.summaryChanged.emit(); self.toastRequested.emit(message,"error")
    @Slot(str)
    def focusTask(self,task_id):
        task=self._task(task_id)
        if task:self.todo.select_focus_task(task.title); self.focusChanged.emit()

    @Slot(str)
    def searchGoals(self,text):self.goal_model.set_filters(query=text)
    @Slot(str)
    def filterGoals(self,status):self.goal_model.set_filters(status=status)
    @Slot(str,str,str)
    def createGoal(self,title,status,notes):
        def saved(_):self.goalCreateSucceeded.emit();self.loadAll()
        def failed(msg):self.goalCreateFailed.emit(msg);self.toastRequested.emit(msg,"error")
        self._run(lambda:self.goals.create_goal(title,status,notes),saved,failed)
    @Slot(str)
    def openGoal(self,goal_id):self._selected_goal_id=goal_id; self.task_model.set_filters(goal_id=goal_id); self.selectedGoalChanged.emit(); self._section="goalDetail"; self.sectionChanged.emit()
    @Slot()
    def closeGoal(self):self.task_model.set_filters(goal_id=""); self._section="goals"; self.sectionChanged.emit()
    @Slot(str,str)
    def renameGoal(self,goal_id,title):self._update_goal(goal_id,title=title)
    @Slot(str,str)
    def setGoalStatus(self,goal_id,status):self._update_goal(goal_id,status=status)
    @Slot(str,str)
    def updateGoalNotes(self,goal_id,notes):self._update_goal(goal_id,notes=notes)
    def _update_goal(self,goal_id,**changes):
        goal=self.goal_model.goal_object(goal_id); item=self.goal_model.item(goal_id)
        if not goal or not item:return
        snapshot={"title":goal.title,"status":goal.status,"notes":goal.notes}; target={**snapshot,**changes}; self.goal_model.update(goal_id,**changes)
        self._run(lambda:self.goals.update_goal(goal,target["title"],target["status"],target["notes"]),lambda _:self.loadAll(),lambda msg:self._rollback_goal(goal_id,snapshot,msg))
    def _rollback_goal(self,goal_id,snapshot,message):self.goal_model.update(goal_id,**snapshot); self.toastRequested.emit(message,"error")
    @Slot(str)
    def deleteGoal(self,goal_id):
        goal=self.goal_model.goal_object(goal_id)
        if goal:self._run(lambda:self.goals.delete_goal(goal),lambda _:self.goal_model.remove(goal_id))
    @Slot(str,str)
    def addTaskToGoal(self,task_id,goal_id):self._set_relation(task_id,goal_id)
    @Slot(str)
    def removeTaskFromGoal(self,task_id):self._set_relation(task_id,"")
    def _set_relation(self,task_id,goal_id):
        task=self._task(task_id) or next((t for t in self.state.goal_tasks if t.id==task_id),None)
        if not task:return
        old_id,old_title=task.goal_id or "",task.goal_title or ""; goal=self.goal_model.item(goal_id); self.task_model.update(task_id,goalId=goal_id,goalTitle=goal["title"] if goal else "")
        def save():self.service.update_task_goal_relation(task_id,goal_id or None); task.goal_id=goal_id or None; task.goal_title=goal["title"] if goal else None
        self._run(save,lambda _:self.loadAll(),lambda msg:self._rollback_task(task_id,{"goalId":old_id,"goalTitle":old_title},msg))

    @Slot(str,str,str,str)
    def createTaskForCurrentGoal(self,title,category,priority,task_date):
        goal_id=self._selected_goal_id; title=title.strip()
        if not goal_id or not title:return
        notion_priority={"P0":"高","P1":"中","P2":"低"}.get(priority,priority)
        def create():
            target=date.fromisoformat(task_date)
            before_ids={task.id for task in self.service.fetch_all_tasks()}
            self.service.create_task(title,target,"单次",notion_priority,category)
            candidates=[task for task in self.service.fetch_all_tasks() if task.id not in before_ids and task.title==title and not task.goal_id]
            if not candidates:raise RuntimeError("任务已创建，但未能定位新 Task Page ID。")
            task=candidates[-1]
            try:self.service.update_task_goal_relation(task.id,goal_id)
            except Exception:
                if title.startswith("[V4 TEST]"):self.service.delete_task(task.id)
                raise RuntimeError("任务已创建，但关联大目标失败。")
            task.goal_id=goal_id; task.goal_title=(self.goal_model.item(goal_id) or {}).get("title","")
            return task
        def success(task):
            self.all_task_model.insert_task(task); self.task_model.insert_task(task)
            self.smallTaskCreated.emit();self.toastRequested.emit("已创建并关联小目标","success");self.loadAll()
        def failure(message):self.smallTaskFailed.emit(message);self.toastRequested.emit(message,"error");self.loadAll()
        self._run(create,success,failure)

    @Slot('QVariantList')
    def addTasksToCurrentGoal(self,task_ids):
        goal_id=self._selected_goal_id
        if not goal_id:return
        pending=list(task_ids); result={"ok":0,"failed":0}
        if not pending:self.relationBatchFinished.emit(0,0);return
        def next_item():
            if not pending:
                self.relationBatchFinished.emit(result["ok"],result["failed"]);self.toastRequested.emit(f"已成功关联 {result['ok']} 个任务；{result['failed']} 个失败","success" if not result["failed"] else "error");self.loadAll();return
            task_id=pending.pop(0); task=self.all_task_model.task_object(task_id); old_id=task.goal_id if task else None
            def save():self.service.update_task_goal_relation(task_id,goal_id)
            def ok(_):result["ok"]+=1;next_item()
            def fail(_message):
                result["failed"]+=1
                if task:task.goal_id=old_id
                next_item()
            self._run(save,ok,fail)
        next_item()

    @Slot()
    def startFocus(self):self.todo.set_timer_running(True); self._timer.start(); self.focusChanged.emit()
    @Slot()
    def pauseFocus(self):self.todo.set_timer_running(False); self._timer.stop(); self.focusChanged.emit()
    @Slot()
    def resetFocus(self):self.todo.set_timer_mode(self.state.timer_minutes); self._timer.stop(); self.focusChanged.emit()
    @Slot(int)
    def setFocusMode(self,minutes):self.todo.set_timer_mode(minutes); self._timer.stop(); self.focusChanged.emit()
    def _tick_focus(self):self.todo.tick_timer(); self.focusChanged.emit(); self._timer.stop() if not self.state.timer_running else None
    @Slot()
    def refreshAnalytics(self):
        data=self.analytics.build(self.state.analytics_period); data["categories"]=[{"name":n,"count":c} for n,c in data["categories"]]; data["weekly"]=[{"day":d,"count":c} for d,c in data["weekly"]]; data["goals"]=[{"title":p.goal.title,"progress":p.percent} for p in data["goals"]]; self._analytics_data=data; self.analyticsChanged.emit()
    @Slot(str,'QVariant')
    def updateSetting(self,key,value):
        self.state.settings[key]=value; self.todo.update_settings(dict(self.state.settings))
        if key=="default_focus_minutes":self.todo.set_timer_mode(int(value));self.focusChanged.emit()
        if key=="completed_tasks_to_bottom":
            self.task_model.completed_to_bottom=bool(value);self.all_task_model.completed_to_bottom=bool(value)
            self.task_model.set_filters();self.all_task_model.set_filters()
        self._apply_settings_runtime(); self._save_settings(); self.settingsChanged.emit()
