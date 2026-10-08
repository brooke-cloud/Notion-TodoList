import QtQuick
import ".."

Rectangle {
    id: root
    property string text: ""
    property string iconText: ""
    property bool primary: false
    property bool checked: false
    property alias fontPixelSize: label.font.pixelSize
    signal clicked
    implicitHeight: 42
    implicitWidth: 110
    radius: Theme.radiusControl
    border.width: 1
    border.color: checked || hover.hovered ? Theme.borderActive : Theme.borderSoft
    gradient: Gradient {
        GradientStop { position: 0; color: root.primary ? Theme.accentTop : (root.checked ? "#C52A639D" : Theme.control) }
        GradientStop { position: 1; color: root.primary ? Theme.accentBottom : (root.checked ? "#C51A4777" : Qt.darker(Theme.control, 1.08)) }
    }
    opacity: tap.pressed ? 0.86 : 1

    Row {
        anchors.centerIn: parent
        spacing: 8
        Text { text: root.iconText; color: root.primary ? "white" : Theme.muted; font.pixelSize: 16 }
        Text { id: label; text: root.text; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody }
    }
    HoverHandler { id: hover }
    TapHandler { id: tap; onTapped: root.clicked() }
}
