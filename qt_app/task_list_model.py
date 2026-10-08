from __future__ import annotations

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot


class TaskListModel(QAbstractListModel):
    FIELDS = ("id", "title", "category", "priority", "date", "repeatType", "isDone", "goalId", "goalTitle")
    ROLES = {Qt.UserRole + index + 1: name for index, name in enumerate(FIELDS)}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all = []
        self._items = []
        self._query = ""
        self._category = "全部分类"
        self._goal_id = ""
        self.completed_to_bottom = True

    def roleNames(self):
        return {role: name.encode() for role, name in self.ROLES.items()}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        return self._items[index.row()].get(self.ROLES.get(role, ""))

    @staticmethod
    def from_task(task):
        return {"id": task.id, "title": task.title, "category": task.project or "未分类",
                "priority": {"高": "P0", "中": "P1", "低": "P2"}.get(task.priority, task.priority),
                "date": (task.date or "")[:10], "repeatType": task.repeat_type,
                "isDone": bool(task.is_done), "goalId": task.goal_id or "", "goalTitle": task.goal_title or "",
                "_object": task}

    def set_tasks(self, tasks):
        self.beginResetModel()
        self._all = [self.from_task(task) for task in tasks]
        self._items = self._filtered()
        self.endResetModel()

    def sync_tasks(self, tasks):
        """Reconcile a refreshed task list without resetting the QML model."""
        incoming = [self.from_task(task) for task in tasks]
        previous = {item["id"]: item for item in self._all}
        merged = []
        changed_by_id = {}
        for fresh in incoming:
            current = previous.get(fresh["id"])
            if current is None:
                merged.append(fresh)
                continue
            changed = [name for name in self.FIELDS if current.get(name) != fresh.get(name)]
            current.update(fresh)
            changed_by_id[current["id"]] = changed
            merged.append(current)
        self._all = merged
        desired = self._filtered()

        desired_ids = {item["id"] for item in desired}
        for row in range(len(self._items) - 1, -1, -1):
            if self._items[row]["id"] not in desired_ids:
                self.beginRemoveRows(QModelIndex(), row, row)
                self._items.pop(row)
                self.endRemoveRows()

        for target_row, item in enumerate(desired):
            current_row = next((i for i, value in enumerate(self._items) if value["id"] == item["id"]), -1)
            if current_row < 0:
                self.beginInsertRows(QModelIndex(), target_row, target_row)
                self._items.insert(target_row, item)
                self.endInsertRows()
            elif current_row != target_row:
                destination = target_row if target_row < current_row else target_row + 1
                self.beginMoveRows(QModelIndex(), current_row, current_row, QModelIndex(), destination)
                moved = self._items.pop(current_row)
                self._items.insert(target_row, moved)
                self.endMoveRows()

            changed = changed_by_id.get(item["id"], [])
            if changed:
                roles = [role for role, name in self.ROLES.items() if name in changed]
                self.dataChanged.emit(self.index(target_row), self.index(target_row), roles)

    def insert_task(self, task):
        """Insert one task without resetting the model."""
        item = self.from_task(task)
        if self.item(item["id"]):
            return False
        self._all.append(item)
        visible = self._filtered()
        if item in visible:
            row = visible.index(item)
            self.beginInsertRows(QModelIndex(), row, row)
            self._items.insert(row, item)
            self.endInsertRows()
        return True

    def _filtered(self):
        result = []
        for item in self._all:
            haystack = f"{item['title']} {item['category']} {item['goalTitle']}".lower()
            if self._query and self._query not in haystack:
                continue
            if self._category != "全部分类" and item["category"] != self._category:
                continue
            if self._goal_id == "__unbound__" and item["goalId"]:
                continue
            if self._goal_id not in ("", "__unbound__") and item["goalId"] != self._goal_id:
                continue
            result.append(item)
        if not self.completed_to_bottom:
            return result
        ordered = sorted(enumerate(result), key=lambda pair: (pair[1]["isDone"], pair[0]))
        return [pair[1] for pair in ordered]

    def set_filters(self, query=None, category=None, goal_id=None):
        if query is not None: self._query = query.strip().lower()
        if category is not None: self._category = category
        if goal_id is not None: self._goal_id = goal_id
        self.beginResetModel(); self._items = self._filtered(); self.endResetModel()

    def item(self, task_id):
        return next((item for item in self._all if item["id"] == task_id), None)

    def task_object(self, task_id):
        item = self.item(task_id)
        return item.get("_object") if item else None

    def update(self, task_id, **changes):
        item = self.item(task_id)
        if not item: return False
        old_row = self._items.index(item) if item in self._items else -1
        item.update(changes)
        new_items = self._filtered()
        new_row = new_items.index(item) if item in new_items else -1
        if old_row >= 0 and new_row >= 0 and old_row != new_row:
            destination = new_row + (1 if new_row > old_row else 0)
            self.beginMoveRows(QModelIndex(), old_row, old_row, QModelIndex(), destination)
            self._items.pop(old_row); self._items.insert(new_row, item); self.endMoveRows()
        elif old_row >= 0 and new_row >= 0:
            roles = [role for role, name in self.ROLES.items() if name in changes]
            self.dataChanged.emit(self.index(old_row), self.index(old_row), roles)
        elif old_row >= 0 and new_row < 0:
            self.beginRemoveRows(QModelIndex(), old_row, old_row)
            self._items.pop(old_row)
            self.endRemoveRows()
        elif old_row < 0 and new_row >= 0:
            self.beginInsertRows(QModelIndex(), new_row, new_row)
            self._items.insert(new_row, item)
            self.endInsertRows()
        return True

    def remove(self, task_id):
        item = self.item(task_id)
        if not item: return
        if item in self._items:
            row = self._items.index(item); self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row); self.endRemoveRows()
        self._all.remove(item)

    @Slot(int, result=str)
    def idAt(self, row):
        return self._items[row]["id"] if 0 <= row < len(self._items) else ""
