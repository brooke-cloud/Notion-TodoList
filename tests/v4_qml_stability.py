import os
import sys
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

    def cycle():
        if not bridge.goal_model._all:
            QTimer.singleShot(100, cycle); return
        state["started"] = True
        if state["count"] >= 20:
            for width, height in ((1440, 900), (1280, 800), (1100, 700)):
                window.setWidth(width); window.setHeight(height); app.processEvents()
            for section in ("tasks", "goals", "analytics", "settings", "goals"):
                bridge.selectSection(section); app.processEvents()
            bridge.openGoal(bridge.goal_model._all[0]["id"])
            if bridge.task_model._items:
                bridge.editTask(bridge.task_model._items[0]["id"])
            QTimer.singleShot(300, finish); return
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
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
