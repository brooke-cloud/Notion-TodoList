import QtQuick
import ".."

GlassPanel {
    id: root
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
            Text { anchors.centerIn: parent; text: root.completed ? "\u2713" : ""; color: "white"; font.pixelSize: 16; font.bold: true }
            TapHandler { onTapped: root.toggled() }
        }
        Column {
            width: Math.max(116, parent.width - 198); anchors.verticalCenter: parent.verticalCenter; spacing: 7
            Text { text: root.taskTitle; color: root.completed ? Theme.dim : Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontCard; font.bold: true; font.strikeout: root.completed; elide: Text.ElideRight; width: parent.width }
            Row {
                spacing: 7
                Repeater { model: [root.category, root.priority, root.taskDate, root.goal]
                    Rectangle { required property string modelData; visible: modelData.length > 0; height: 22; width: badgeText.implicitWidth + 18; radius: Theme.radiusSmall; color: modelData === "P0" ? "#90492A48" : Theme.tag; border.width: 1; border.color: "#264F7290"
                        Text { id: badgeText; anchors.centerIn: parent; text: modelData; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta }
                    }
                }
            }
        }
        GlassButton { width: 72; height: 36; text: "\u987a\u5ef6"; fontPixelSize: Theme.fontBody; anchors.verticalCenter: parent.verticalCenter; onClicked: root.postponeRequested() }
        GlassButton { width: 68; height: 36; text: "\u4e13\u6ce8"; fontPixelSize: Theme.fontBody; anchors.verticalCenter: parent.verticalCenter; onClicked: root.focusRequested() }
    }
    TapHandler { acceptedButtons: Qt.LeftButton; gesturePolicy: TapHandler.DragThreshold; onDoubleTapped: root.editRequested() }
}
