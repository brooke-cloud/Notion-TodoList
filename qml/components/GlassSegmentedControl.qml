import QtQuick
import ".."

Rectangle {
    id: root
    property var model: []
    property int currentIndex: 0
    signal selected(int index, string value)
    implicitHeight: 46
    radius: Theme.radiusControl
    color: Theme.panel
    border.width: 1
    border.color: Theme.borderSoft
    Row {
        anchors.fill: parent
        anchors.margins: 4
        Repeater {
            model: root.model
            GlassButton {
                required property int index
                required property var modelData
                width: (root.width - 8) / root.model.length
                height: parent.height
                text: modelData
                checked: index === root.currentIndex
                border.width: checked ? 1 : 0
                onClicked: { root.currentIndex = index; root.selected(index, modelData) }
            }
        }
    }
}
