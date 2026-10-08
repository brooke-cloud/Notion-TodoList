import QtQuick
import QtQuick.Controls
import ".."

Rectangle {
    id: root
    property alias text: input.text
    property alias placeholderText: input.placeholderText
    property string leadingIcon: ""
    signal accepted
    implicitHeight: 44
    radius: Theme.radiusControl
    color: Theme.control
    border.width: 1
    border.color: input.activeFocus ? Theme.borderActive : Theme.borderSoft
    Row {
        anchors.fill: parent
        anchors.leftMargin: 15
        anchors.rightMargin: 12
        spacing: 10
        Text { visible: root.leadingIcon.length > 0; text: root.leadingIcon; color: Theme.dim; font.pixelSize: 17; anchors.verticalCenter: parent.verticalCenter }
        TextField {
            id: input
            width: parent.width - (root.leadingIcon.length > 0 ? 28 : 0)
            height: parent.height
            color: Theme.text
            placeholderTextColor: Theme.dim
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fontBody
            background: null
            verticalAlignment: TextInput.AlignVCenter
            onAccepted: root.accepted()
        }
    }
    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        height: 1
        color: Theme.highlight
        opacity: input.activeFocus ? .6 : .25
    }
}
