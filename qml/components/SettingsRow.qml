import QtQuick
import ".."

Item {
    id: root
    property string label: ""
    default property alias controlData: holder.data
    implicitHeight: 40
    Text { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; width: Math.min(230, parent.width * .44); text: root.label; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody; elide: Text.ElideRight }
    Item { id: holder; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; width: Math.min(210, parent.width * .48); height: 38 }
}
