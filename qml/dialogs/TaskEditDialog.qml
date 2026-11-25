import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Popup {
    id: root
    objectName: "taskDialog"
    property var taskData: ({})
    property var goalModel
    property var goalOptions: []
    property bool saving: false
    property bool goalCleared: false
    readonly property bool creating: !!taskData.creating
    modal: true
    focus: true
    width: Math.min(560, Overlay.overlay.width - 32)
    height: Math.min(620, Overlay.overlay.height - 32)
    anchors.centerIn: Overlay.overlay
    padding: 0
    background: GlassPanel { surfaceColor: Theme.panelStrong }

    function goalIndex(goalId) {
        for (let i = 0; i < goalOptions.length; i++)
            if (goalOptions[i].id === goalId) return i
        return -1
    }
    onOpened: {
        saving = false
        goalCleared = false
        goalOptions = taskData.goalOptions || []
        titleField.text = taskData.title || ""
        categoryBox.currentIndex = Math.max(0, ["未分类", "学习", "工作", "副业", "生活"].indexOf(taskData.category))
        priority.currentIndex = Math.max(0, ["P0", "P1", "P2"].indexOf(taskData.priority))
        repeatType.currentIndex = Math.max(0, ["单次", "每天"].indexOf(taskData.repeatType || "单次"))
        dateField.text = taskData.date || ""
        goalBox.currentIndex = goalIndex(taskData.goalId || "")
        formScroll.contentY = 0
    }

    Flickable {
        id: formScroll
        anchors { left: parent.left; right: parent.right; top: parent.top; bottom: footer.top; leftMargin: 24; rightMargin: 24; topMargin: 24; bottomMargin: 12 }
        contentWidth: width
        contentHeight: form.height
        clip: true
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        Column {
            id: form
            width: formScroll.width
            spacing: 11
            Text { text: root.creating ? "添加任务" : "编辑任务"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
            Text { text: "任务标题"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassInput { id: titleField; width: parent.width }
            Text { text: "分类"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassComboBox { id: categoryBox; width: parent.width; height: 42; colorizeCategories: true; model: ["未分类", "学习", "工作", "副业", "生活"] }
            Text { text: "优先级"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassSegmentedControl { id: priority; width: parent.width; model: ["P0", "P1", "P2"] }
            Text { text: "重复类型"; color: Theme.muted; font.family: Theme.fontFamily }
            GlassSegmentedControl { id: repeatType; width: parent.width; model: ["单次", "每天"] }
            Text { text: "日期"; color: Theme.muted; font.family: Theme.fontFamily }
            Row {
                width: parent.width; spacing: 8
                GlassInput { id: dateField; width: parent.width - 170; placeholderText: "YYYY-MM-DD" }
                GlassButton { width: 76; text: "今天"; onClicked: dateField.text = Qt.formatDate(new Date(), "yyyy-MM-dd") }
                GlassButton { width: 78; text: "明天"; onClicked: { let d = new Date(); d.setDate(d.getDate() + 1); dateField.text = Qt.formatDate(d, "yyyy-MM-dd") } }
            }
            Text { text: "大目标"; color: Theme.muted; font.family: Theme.fontFamily }
            Row {
                width: parent.width; spacing: 8
                GlassComboBox { id: goalBox; width: parent.width - 108; height: 42; model: root.goalOptions.map(function(item) { return item.title }); onActivated: root.goalCleared = false }
                GlassButton { width: 100; height: 42; text: root.goalCleared ? "不关联 ✓" : "不关联"; onClicked: { root.goalCleared = true; goalBox.currentIndex = -1 } }
            }
        }
    }
    Row {
        id: footer
        objectName: "taskDialogFooter"
        anchors { right: parent.right; bottom: parent.bottom; rightMargin: 24; bottomMargin: 24 }
        height: 42
        spacing: 10
        GlassButton { width: 110; height: parent.height; text: "取消"; onClicked: root.close() }
        GlassButton {
            width: 110; height: parent.height
            text: root.saving ? "保存中…" : root.creating ? "添加任务" : "保存修改"
            primary: true
            enabled: !root.saving
            onClicked: {
                if (!titleField.text.trim()) return
                let selectedGoal = root.goalCleared ? "" : (goalBox.currentIndex >= 0 && goalBox.currentIndex < root.goalOptions.length ? root.goalOptions[goalBox.currentIndex].id : taskData.goalId || "")
                root.saving = true
                if (root.creating)
                    appBridge.createTaskDetailed(titleField.text, categoryBox.currentText, priority.model[priority.currentIndex], repeatType.model[repeatType.currentIndex], dateField.text, selectedGoal)
                else
                    appBridge.updateTask(taskData.id, titleField.text, categoryBox.currentText, priority.model[priority.currentIndex], repeatType.model[repeatType.currentIndex], dateField.text, selectedGoal)
            }
        }
    }
    Connections {
        target: appBridge
        function onTaskCreateSucceeded() { if (root.creating) { root.saving = false; root.close() } }
        function onTaskCreateFailed(message) { if (root.creating) root.saving = false }
        function onTaskSaveSucceeded(taskId) { if (!root.creating && taskId === root.taskData.id) { root.saving = false; root.close() } }
        function onTaskSaveFailed(taskId, message) { if (!root.creating && taskId === root.taskData.id) root.saving = false }
    }
}
