import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from qt_app.app_bridge import AppBridge
from models.goal import Goal, GoalProgress
from models.task import Task


def main():
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    root = ROOT
    report_temp = tempfile.TemporaryDirectory(dir=root)
    os.environ["NOTION_TODOLIST_REPORT_DIR"] = report_temp.name
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    # QML lifetime/stability is deterministic and must not depend on network.
    original_initialize = AppBridge.initialize
    AppBridge.initialize = lambda self: None
    bridge = AppBridge(root)
    AppBridge.initialize = original_initialize
    goal = Goal("qml-goal", "QML stability goal", "In Progress")
    task = Task("qml-task", "QML stability task", "中", "工作", date="2026-10-06", goal_id=goal.id)
    task.goal_title = goal.title
    bridge.state.goal_tasks = [task]
    bridge.task_model.set_tasks([task]); bridge.all_task_model.set_tasks([task])
    bridge.goal_model.set_goals([goal], [GoalProgress(goal, 1, 0)])
    app._engine, app._bridge = engine, bridge
    warnings = []
    engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
    context = engine.rootContext()
    context.setContextProperty("appBridge", bridge)
    context.setContextProperty("taskListModel", bridge.task_model)
    context.setContextProperty("allTaskListModel", bridge.all_task_model)
    context.setContextProperty("goalListModel", bridge.goal_model)
    context.setContextProperty("backgroundUrl", QUrl.fromLocalFile(str(root / "design" / "bg.jpg")))
    engine.addImportPath(str(root / "qml")); engine.load(QUrl.fromLocalFile(str(root / "qml" / "Main.qml")))
    if not engine.rootObjects():
        raise RuntimeError("QML root failed:\n" + "\n".join(warnings))
    state = {"count": 0, "started": False}
    window = engine.rootObjects()[0]
    capture_dir = Path(os.environ["V4_SCREENSHOT_DIR"]) if os.environ.get("V4_SCREENSHOT_DIR") else None
    if capture_dir:
        capture_dir.mkdir(parents=True, exist_ok=True)

    def open_editor_after_report():
        if capture_dir:
            app.primaryScreen().grabWindow(int(window.winId())).save(str(capture_dir / "daily-report.png"))
        bridge.openGoal(bridge.goal_model._all[0]["id"])
        app.processEvents()
        if capture_dir:
            app.primaryScreen().grabWindow(int(window.winId())).save(str(capture_dir / "goal-detail.png"))
        if bridge.task_model._items:
            bridge.editTask(bridge.task_model._items[0]["id"])
        QTimer.singleShot(180, capture_editor)

    def capture_editor():
        if capture_dir:
            app.primaryScreen().grabWindow(int(window.winId())).save(str(capture_dir / "task-editor.png"))
        QTimer.singleShot(120, finish)

    def cycle():
        if not bridge.goal_model._all:
            QTimer.singleShot(100, cycle); return
        state["started"] = True
        if state["count"] >= 20:
            for width, height in ((1440, 900), (1280, 800), (1100, 700)):
                window.setWidth(width); window.setHeight(height); app.processEvents()
            bridge.selectSection("tasks"); app.processEvents()
            if capture_dir:
                app.primaryScreen().grabWindow(int(window.winId())).save(str(capture_dir / "task-home.png"))
            for section in ("goals", "analytics", "settings", "goals"):
                bridge.selectSection(section); app.processEvents()
            bridge.dailyReportRequested.emit({"date":"2026-10-05","total":3,"completed":2,"pending":1,"completion_rate":66.7,"auto_postponed":1,"main_pending":[{"title":"Mock pending","category":"工作","priority":"高"}],"today_tasks":[{"title":"Mock today","category":"学习","priority":"中"}]})
            app.processEvents()
            QTimer.singleShot(180, open_editor_after_report); return
        bridge.openGoal(bridge.goal_model._all[0]["id"])
        bridge.closeGoal(); state["count"] += 1
        QTimer.singleShot(35, cycle)

    def finish():
        bad = [line for line in warnings if any(token in line for token in ("TypeError", "ReferenceError", "deleted", "Binding loop"))]
        print("GOAL_DETAIL_CYCLES", state["count"])
        print("QML_RESIZE_CASES", 3)
        print("QML_NAVIGATION_SEQUENCE_OK")
        print("QML_BAD_WARNINGS", len(bad))
        for line in bad: print(line)
        app.exit(0 if state["count"] == 20 and not bad else 2)

    QTimer.singleShot(100, cycle); QTimer.singleShot(30000, lambda: app.exit(3))
    result = app.exec()
    report_temp.cleanup()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
