"""The sole desktop entry point for the PySide6/QML V4 application."""

import faulthandler
import logging
import os
import re
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from qt_app.app_bridge import AppBridge


APP_NAME = "Notion TodoList V4"
_SENSITIVE_VALUE = re.compile(
    r"(?i)(notion[_ -]?token|api[_ -]?key|secret|authorization)(\s*[:=]\s*)([^\s,;]+)"
)


class _LogStream:
    """File-backed replacement only for missing windowed standard streams."""

    encoding = "utf-8"

    def __init__(self, logger: logging.Logger, level: int) -> None:
        self._logger = logger
        self._level = level

    def write(self, message: str) -> int:
        text = message.strip()
        if text:
            self._logger.log(self._level, _redact(text))
        return len(message)

    def flush(self) -> None:
        for handler in self._logger.handlers:
            handler.flush()

    def isatty(self) -> bool:
        return False


def _redact(message: str) -> str:
    """Keep diagnostic logging useful without writing credentials to disk."""
    return _SENSITIVE_VALUE.sub(r"\1<redacted>", message)


def _log_path() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return root / "NotionTodoListV4" / "logs" / "startup.log"


def configure_startup_logging() -> logging.Logger:
    """Configure GUI-safe diagnostics without depending on a console stream."""
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("notion_todolist_v4")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    if sys.stdout is None:
        sys.stdout = _LogStream(logger, logging.INFO)
    if sys.stderr is None:
        sys.stderr = _LogStream(logger, logging.ERROR)

    def log_unhandled_exception(exc_type, exc_value, exc_traceback) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("Unhandled exception:\n%s", _redact("".join(traceback.format_exception(exc_type, exc_value, exc_traceback))))

    sys.excepthook = log_unhandled_exception
    return logger


def resource_path(relative: str) -> Path:
    """Return a bundled resource path in frozen builds and a source path otherwise."""
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative


def config_path() -> Path:
    """Return the writable configuration root for source and frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main() -> int:
    logger = configure_startup_logging()
    logger.info("Application startup (frozen=%s)", bool(getattr(sys, "frozen", False)))
    # ``faulthandler.enable()`` defaults to sys.stderr, which is None in a
    # PyInstaller windowed build.  Write faults to the same GUI-safe log instead.
    fault_log = open(_log_path(), "a", encoding="utf-8")
    faulthandler.enable(file=fault_log)
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    QGuiApplication.setApplicationName(APP_NAME)
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    qInstallMessageHandler(lambda _type, _context, message: logger.warning("Qt: %s", _redact(message)))
    engine.warnings.connect(lambda warnings: [logger.warning("QML: %s", _redact(warning.toString())) for warning in warnings])
    bridge = AppBridge(config_path())
    # Keep QObjects exposed to QML alive for the whole event loop.
    app._v4_engine = engine
    app._v4_bridge = bridge
    engine.rootContext().setContextProperty("appBridge", bridge)
    engine.rootContext().setContextProperty("taskListModel", bridge.task_model)
    engine.rootContext().setContextProperty("allTaskListModel", bridge.all_task_model)
    engine.rootContext().setContextProperty("goalListModel", bridge.goal_model)
    engine.rootContext().setContextProperty(
        "backgroundUrl", QUrl.fromLocalFile(str(resource_path("design/bg.jpg")))
    )
    qml_root = resource_path("qml")
    engine.addImportPath(str(qml_root))
    engine.load(QUrl.fromLocalFile(str(qml_root / "Main.qml")))
    if not engine.rootObjects():
        logger.error("QML root object failed to load")
        return 1
    try:
        return app.exec()
    finally:
        faulthandler.disable()
        fault_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
