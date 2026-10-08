import QtQuick
import QtQuick.Controls
import ".."

Switch {
    id: root
    implicitWidth: 50
    implicitHeight: 28
    indicator: Rectangle {
        implicitWidth: 48; implicitHeight: 26; radius: 13
        color: root.checked ? Theme.accent : Theme.control
        border.width: 1; border.color: root.hovered ? Theme.borderActive : Theme.borderSoft
        Rectangle {
            x: root.checked ? 25 : 3; y: 3; width: 20; height: 20; radius: 10; color: Theme.text
            Behavior on x { NumberAnimation { duration: 130 } }
        }
    }
    contentItem: Item {}
}
