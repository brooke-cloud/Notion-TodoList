import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Popup {
    id: root
    property var allTaskModel
    property int mode: 0
    property var selectedIds: []
    modal: true
    focus: true
    width: 620
    height: 610
    anchors.centerIn: Overlay.overlay
    background: GlassPanel { surfaceColor: Theme.panelStrong }

    onOpened: { mode = 0; selectedIds = [] }
    onClosed: appBridge.searchAllTasks("")
    function selected(taskId) { return selectedIds.indexOf(taskId) >= 0 }
    function toggle(taskId) {
        let values = selectedIds.slice()
        let index = values.indexOf(taskId)
        if (index >= 0) values.splice(index, 1); else values.push(taskId)
        selectedIds = values
    }

    Column {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 14
        Row {
            width: parent.width
            Text {
                text: root.mode === 0 ? "添加小目标" : root.mode === 1 ? "新建小目标" : "从现有任务添加"
                color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true
            }
            Item { width: parent.width - 180; height: 1 }
            GlassButton { width: 42; height: 34; text: "×"; onClicked: root.close() }
        }
        Row {
            visible: root.mode === 0; width: parent.width; spacing: 14
            GlassButton { width: (parent.width - 14) / 2; height: 90; text: "＋ 新建小目标"; primary: true; onClicked: root.mode = 1 }
            GlassButton { width: (parent.width - 14) / 2; height: 90; text: "☷ 从现有任务添加"; onClicked: root.mode = 2 }
        }
        Column {
            visible: root.mode === 1; width: parent.width; spacing: 10
            Text { text: "任务标题"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassInput { id: newTitle; width: parent.width }
            Text { text: "分类"; color: Theme.muted; font.family: Theme.fontFamily }
            ComboBox { id: newCategory; width: parent.width; height: 42; model: ["未分类", "学习", "工作", "副业", "生活"] }
            Text { text: "优先级"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassSegmentedControl { id: newPriority; width: parent.width; model: ["P0", "P1", "P2"]; currentIndex: 1 }
            Text { text: "日期"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassInput { id: newDate; width: parent.width; text: Qt.formatDate(new Date(), "yyyy-MM-dd") }
            Row {
                anchors.right: parent.right; spacing: 10
                GlassButton { text: "取消"; onClicked: root.close() }
                GlassButton {
                    width: 210; text: "创建任务并加入当前目标"; primary: true
                    onClicked: {
                        if (newTitle.text.trim())
                            appBridge.createTaskForCurrentGoal(newTitle.text, newCategory.currentText,
                                                               newPriority.model[newPriority.currentIndex], newDate.text)
                    }
                }
            }
        }
        Column {
            visible: root.mode === 2; width: parent.width; height: parent.height - 70; spacing: 10
            GlassInput { id: search; width: parent.width; placeholderText: "搜索任务…"; leadingIcon: "⌕"; onTextChanged: appBridge.searchAllTasks(text) }
            ListView {
                id: availableList; width: parent.width; height: parent.height - 110
                model: root.allTaskModel; spacing: 6; clip: true
                delegate: Rectangle {
                    required property var model
                    property string taskId: model.id
                    property bool already: model.goalId === appBridge.selectedGoalId
                    width: availableList.width - 8; height: 58; radius: Theme.radiusControl
                    color: Theme.card; border.color: root.selected(taskId) ? Theme.borderActive : Theme.borderSoft
                    opacity: already ? 0.55 : 1
                    Row {
                        anchors.fill: parent; anchors.margins: 12; spacing: 12
                        Rectangle {
                            width: 22; height: 22; radius: 6
                            color: root.selected(taskId) ? Theme.accent : "transparent"; border.color: Theme.dim
                            Text { anchors.centerIn: parent; text: root.selected(taskId) ? "✓" : ""; color: "white" }
                        }
                        Column {
                            width: parent.width - 150
                            Text { text: model.title; color: Theme.text; font.family: Theme.fontFamily; font.bold: true; elide: Text.ElideRight; width: parent.width }
                            Text {
                                text: model.category + " · " + model.priority + " · " + model.date
                                      + (already ? " · 已关联" : model.goalTitle ? " · 当前属于：" + model.goalTitle : "")
                                color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta
                            }
                        }
                    }
                    TapHandler { enabled: !parent.already; onTapped: root.toggle(parent.taskId) }
                }
            }
            Row {
                anchors.right: parent.right; spacing: 10
                GlassButton { text: "取消"; onClicked: root.close() }
                GlassButton { text: "确认关联 (" + root.selectedIds.length + ")"; primary: true; onClicked: appBridge.addTasksToCurrentGoal(root.selectedIds) }
            }
        }
    }
    Connections {
        target: appBridge
        function onSmallTaskCreated() { root.close() }
        function onRelationBatchFinished(ok, failed) { if (failed === 0) root.close() }
    }
}
