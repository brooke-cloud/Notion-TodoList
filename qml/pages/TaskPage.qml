import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Item {
    id: root; property var taskModel
    Row { anchors.fill: parent; spacing: 14
        GlassPanel { width: parent.width - 314; height: parent.height; surfaceColor: "#B20A2037"
            Column { anchors.fill: parent; anchors.margins: 20; spacing: 12
                Row { width: parent.width; height: 58
                    Column { spacing: 3
                        Text { text: appBridge.taskViewTitle; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontPage; font.bold: true }
                        Text { text: appBridge.pendingCount + " \u4e2a\u5f85\u5b8c\u6210\u4efb\u52a1 \u00b7 \u5df2\u5b8c\u6210 " + appBridge.completedCount + " \u4e2a"; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody }
                    }
                    Item { width: parent.width - 300; height: 1 }
                    Text { text: appBridge.taskLoadState === "refreshing" ? "\u540c\u6b65\u4e2d\u2026" : appBridge.taskLoadState === "loading" ? "\u52a0\u8f7d\u4e2d\u2026" : appBridge.taskLoadState === "error" ? "\u52a0\u8f7d\u5931\u8d25" : "\u5df2\u540c\u6b65"; color: appBridge.taskLoadState === "error" ? Theme.danger : appBridge.taskLoadState === "idle" ? Theme.success : Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta; anchors.verticalCenter: parent.verticalCenter }
                }
                GlassSegmentedControl { width: parent.width; model: ["\u4eca\u5929", "\u6628\u5929", "\u660e\u5929", "\u5168\u90e8"]; currentIndex: Math.max(0, model.indexOf(appBridge.dateView)); onSelected: (index, value) => appBridge.setDateView(value) }
                Row { width: parent.width; height: 46; spacing: 10
                    GlassInput { id: quickAdd; width: parent.width - 104; height: parent.height; leadingIcon: "+"; placeholderText: "\u6dfb\u52a0\u4e00\u4e2a\u4efb\u52a1\u2026"; onAccepted: { appBridge.createTask(text); text = "" } }
                    GlassButton { width: 94; height: parent.height; text: "\u6dfb\u52a0"; primary: true; onClicked: { appBridge.createTask(quickAdd.text); quickAdd.text = "" } }
                }
                Row { width: parent.width; height: 44; spacing: 10
                    GlassInput { width: parent.width - 378; height: parent.height; leadingIcon: "\u2315"; placeholderText: "\u641c\u7d22\u4efb\u52a1\u2026"; onTextChanged: appBridge.searchTasks(text) }
                    GlassButton { width: 150; height: parent.height; text: "\u5168\u90e8\u5206\u7c7b" }
                    GlassButton { width: 174; height: parent.height; text: "\u5168\u90e8\u5927\u76ee\u6807" }
                    GlassButton { width: 44; height: parent.height; text: "\u21bb" }
                }
                Item { width: parent.width; height: parent.height - 226
                    ListView { id: taskList; anchors.fill: parent; visible: appBridge.taskLoadState === "idle" || appBridge.taskLoadState === "refreshing"; model: root.taskModel; spacing: 9; clip: true; boundsBehavior: Flickable.StopAtBounds; ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
                        delegate: TaskCard { width: taskList.width - 8; property string taskId: model.id; taskTitle: model.title; category: model.category; priority: model.priority; taskDate: model.date; goal: model.goalTitle; completed: model.isDone; onToggled: appBridge.toggleTaskDone(taskId); onEditRequested: appBridge.editTask(taskId); onPostponeRequested: appBridge.postponeTask(taskId); onFocusRequested: appBridge.focusTask(taskId) }
                    }
                    Text { anchors.centerIn: parent; visible: appBridge.taskLoadState === "idle" && taskList.count === 0; text: appBridge.taskViewTitle + "\u8fd8\u6ca1\u6709\u4efb\u52a1"; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection }
                }
            }
        }
        Column { width: 300; height: parent.height; spacing: 12
            FocusTimer { width: parent.width; timeText: appBridge.focusTime; running: appBridge.focusRunning; mode: appBridge.focusMode; taskTitle: appBridge.focusTaskTitle; onStartRequested: appBridge.startFocus(); onPauseRequested: appBridge.pauseFocus(); onResetRequested: appBridge.resetFocus(); onModeRequested: (minutes) => appBridge.setFocusMode(minutes) }
            GlassPanel { width: parent.width; height: 146
                Column { anchors.fill: parent; anchors.margins: 18; spacing: 14
                    Text { text: "\u4eca\u65e5\u7edf\u8ba1"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    Row { width: parent.width
                        Repeater { model: [{value: appBridge.pendingCount, label: "\u5f85\u5b8c\u6210", color: Theme.text}, {value: appBridge.completedCount, label: "\u5df2\u5b8c\u6210", color: Theme.success}]
                            Column { required property var modelData; width: parent.width / 2
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.value; color: modelData.color; font.pixelSize: 25; font.bold: true }
                                Text { anchors.horizontalCenter: parent.horizontalCenter; text: modelData.label; color: Theme.muted; font.pixelSize: Theme.fontMeta }
                            }
                        }
                    }
                }
            }
            GlassPanel {
                width: parent.width
                height: Math.max(150, parent.height - 564)
                Column {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 12
                    Text { text: "\u6700\u8fd1\u5206\u7c7b"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    Repeater {
                        model: appBridge.categorySummary
                        Row {
                            required property var modelData
                            required property int index
                            width: parent.width
                            height: 22
                            spacing: 10
                            Rectangle { width: 7; height: 7; radius: 4; color: [Theme.accent,"#8A6CFF",Theme.warning,Theme.success][index % 4]; anchors.verticalCenter: parent.verticalCenter }
                            Text { width: parent.width - 44; text: modelData.name; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody; elide: Text.ElideRight }
                            Text { text: modelData.count; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta }
                        }
                    }
                }
            }
        }
    }
}
