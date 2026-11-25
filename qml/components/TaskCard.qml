import QtQuick
import QtQuick.Controls
import ".."

GlassPanel {
    id: root
    shadowEnabled: false
    property string taskTitle: ""
    property string category: ""
    property string priority: "P1"
    property string taskDate: ""
    property string goal: ""
    property bool completed: false
    property bool inGoalDetail: false
    signal toggled
    signal editRequested
    signal postponeRequested
    signal focusRequested
    signal deleteRequested
    signal removeGoalRequested
    height: 76
    panelRadius: Theme.radiusCard
    surfaceColor: hover.hovered ? Theme.cardHover : Theme.card
    strokeColor: hover.hovered ? Theme.borderActive : Theme.borderSoft
    HoverHandler { id: hover }
    Row {
        anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 18; spacing: 10
        Rectangle {
            width: 28; height: 28; radius: 14; anchors.verticalCenter: parent.verticalCenter
            color: root.completed ? Theme.success : "transparent"; border.width: 2; border.color: root.completed ? Theme.success : Theme.dim
            Behavior on color { ColorAnimation { duration: 110 } }
            Behavior on border.color { ColorAnimation { duration: 110 } }
            Text { anchors.centerIn: parent; text: "\u2713"; opacity: root.completed ? 1 : 0; scale: root.completed ? 1 : 0.65; color: "white"; font.pixelSize: 16; font.bold: true
                Behavior on opacity { NumberAnimation { duration: 100 } }
                Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutBack } }
            }
            TapHandler { onTapped: root.toggled() }
        }
        Column {
            width: Math.max(116, parent.width - 272); anchors.verticalCenter: parent.verticalCenter; spacing: 7
            Text { text: root.taskTitle; color: root.completed ? Theme.dim : Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontCard; font.bold: true; font.strikeout: root.completed; elide: Text.ElideRight; width: parent.width }
            Row {
                spacing: 7
                Repeater { model: [{text:root.category,kind:"category"},{text:root.priority,kind:"priority"},{text:root.taskDate,kind:"date"},{text:root.goal,kind:"goal"}]
                    Rectangle { required property var modelData; visible: modelData.text.length > 0; height: 22; width: badgeText.implicitWidth + 18; radius: Theme.radiusSmall; color: modelData.kind === "category" ? Theme.categoryBackground(modelData.text) : modelData.text === "P0" ? Theme.priorityHigh : Theme.tag; border.width: 1; border.color: modelData.kind === "category" ? Theme.categoryBorder(modelData.text) : Theme.tagBorder
                        Text { id: badgeText; anchors.centerIn: parent; text: modelData.text; color: modelData.kind === "category" ? Theme.categoryColor(modelData.text) : Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta }
                    }
                }
            }
        }
        GlassButton { width: 72; height: 36; text: "\u987a\u5ef6"; fontPixelSize: Theme.fontBody; anchors.verticalCenter: parent.verticalCenter; onClicked: root.postponeRequested() }
        GlassButton { width: 68; height: 36; text: "\u4e13\u6ce8"; fontPixelSize: Theme.fontBody; anchors.verticalCenter: parent.verticalCenter; onClicked: root.focusRequested() }
        GlassButton { width: 64; height: 36; text: "\u5220\u9664"; fontPixelSize: Theme.fontBody; anchors.verticalCenter: parent.verticalCenter; border.color: Theme.danger; onClicked: confirmDelete.open() }
    }
    TapHandler { acceptedButtons: Qt.LeftButton; gesturePolicy: TapHandler.DragThreshold; onDoubleTapped: root.editRequested() }
    Popup {
        id: confirmDelete
        objectName: "taskDeleteConfirm"
        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay
        width: Math.min(400, Overlay.overlay.width - 32)
        height: 176
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: GlassPanel { surfaceColor: Theme.panelStrong }
        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            Text { text: "删除任务？"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
            Text { width: parent.width; text: root.taskTitle; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody; elide: Text.ElideRight }
            Text { text: "确认后将从 Notion 删除该任务。"; color: Theme.dim; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta }
            Row {
                anchors.right: parent.right
                spacing: 10
                GlassButton { width: 100; height: 36; text: "取消"; onClicked: confirmDelete.close() }
                GlassButton { width: 100; height: 36; text: "确认删除"; border.color: Theme.danger; onClicked: { confirmDelete.close(); root.deleteRequested() } }
            }
        }
    }
}
