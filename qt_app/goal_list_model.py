from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Slot


class GoalListModel(QAbstractListModel):
    FIELDS = ("id", "title", "status", "statusLabel", "notes", "lastUpdated", "progress", "totalTasks", "completedTasks")
    ROLES = {Qt.UserRole + index + 1: name for index, name in enumerate(FIELDS)}
    LABELS = {"Not Started": "未开始", "In Progress": "进行中", "Completed": "已完成"}

    def __init__(self, parent=None):
        super().__init__(parent); self._all=[]; self._items=[]; self._query=""; self._status="全部"

    def roleNames(self): return {role:name.encode() for role,name in self.ROLES.items()}
    def rowCount(self,parent=QModelIndex()): return 0 if parent.isValid() else len(self._items)
    def data(self,index,role=Qt.DisplayRole):
        return self._items[index.row()].get(self.ROLES.get(role,"")) if index.isValid() and 0<=index.row()<len(self._items) else None

    def set_goals(self, goals, progresses):
        self.beginResetModel(); self._all=[]
        for goal, progress in zip(goals, progresses):
            self._all.append({"id":goal.id,"title":goal.title,"status":goal.status,"statusLabel":self.LABELS.get(goal.status,goal.status),
                "notes":goal.notes,"lastUpdated":goal.last_updated,"progress":progress.percent,"totalTasks":progress.total_tasks,
                "completedTasks":progress.completed_tasks,"_object":goal})
        self._items=self._filtered(); self.endResetModel()

    def insert_goal(self, goal, progress):
        if self.item(goal.id):return False
        item={"id":goal.id,"title":goal.title,"status":goal.status,"statusLabel":self.LABELS.get(goal.status,goal.status),
              "notes":goal.notes,"lastUpdated":goal.last_updated,"progress":progress.percent,"totalTasks":progress.total_tasks,
              "completedTasks":progress.completed_tasks,"_object":goal}
        self._all.append(item); visible=self._filtered()
        if item in visible:
            row=visible.index(item); self.beginInsertRows(QModelIndex(),row,row); self._items.insert(row,item); self.endInsertRows()
        return True

    def _filtered(self):
        mapping={"进行中":"In Progress","未开始":"Not Started","已完成":"Completed"}; target=mapping.get(self._status)
        return [g for g in self._all if (not target or g["status"]==target) and (not self._query or self._query in (g["title"]+" "+g["notes"]).lower())]
    def set_filters(self, query=None, status=None):
        if query is not None:self._query=query.strip().lower()
        if status is not None:self._status=status
        self.beginResetModel(); self._items=self._filtered(); self.endResetModel()
    def item(self,goal_id): return next((g for g in self._all if g["id"]==goal_id),None)
    def goal_object(self,goal_id):
        item=self.item(goal_id); return item.get("_object") if item else None
    def update(self,goal_id,**changes):
        item=self.item(goal_id)
        if not item:return False
        item.update(changes)
        if "status" in changes:item["statusLabel"]=self.LABELS.get(item["status"],item["status"])
        if item in self._items:
            row=self._items.index(item); roles=[r for r,n in self.ROLES.items() if n in changes or n=="statusLabel"]
            self.dataChanged.emit(self.index(row),self.index(row),roles)
        else:self.set_filters()
        return True
    def remove(self,goal_id):
        item=self.item(goal_id)
        if not item:return
        if item in self._items:
            row=self._items.index(item); self.beginRemoveRows(QModelIndex(),row,row); self._items.pop(row); self.endRemoveRows()
        self._all.remove(item)
    @Slot(int,result=str)
    def idAt(self,row): return self._items[row]["id"] if 0<=row<len(self._items) else ""
    @Slot(str,result=int)
    def indexOfId(self,goal_id):
        return next((index for index,item in enumerate(self._items) if item["id"]==goal_id),-1)
