import QtQuick
import ".."

GlassPanel {
    id: root
    property string currentSection: "tasks"
    signal sectionSelected(string section)
    panelRadius: 0
    surfaceColor: "#C70B2239"
    strokeColor: "transparent"
    shadowOpacity: 0.2

    Column {
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14; topMargin: 24 }
        spacing: 8
        Repeater {
            model: [
                { key: "tasks", label: "任务" },
                { key: "goals", label: "大目标" },
                { key: "analytics", label: "统计分析" },
                { key: "settings", label: "设置" }
            ]
            Item {
                required property var modelData
                width: parent.width; height: 50
                Rectangle {
                    anchors.fill: parent; radius: Theme.radiusControl
                    color: modelData.key === root.currentSection ? "#9B1C4E7E" : (navHover.hovered ? "#65183956" : "transparent")
                    border.width: modelData.key === root.currentSection ? 1 : 0
                    border.color: Theme.borderSoft
                }
                Rectangle {
                    width: 3; height: 28; radius: 2; anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                    color: modelData.key === root.currentSection ? Theme.accent : "transparent"
                }
                Row {
                    anchors.verticalCenter: parent.verticalCenter; anchors.left: parent.left; anchors.leftMargin: 20; spacing: 12
                    NavigationIcon { kind: modelData.key; iconColor: modelData.key === root.currentSection ? Theme.text : Theme.muted }
                    Text { text: modelData.label; color: modelData.key === root.currentSection ? Theme.text : Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody }
                }
                HoverHandler { id: navHover }
                TapHandler { onTapped: root.sectionSelected(modelData.key) }
            }
        }
    }
}
