import QtQuick
import QtQuick.Effects
import ".."

Item {
    id: root
    property color surfaceColor: Theme.panel
    property color strokeColor: Theme.borderSoft
    property real panelRadius: Theme.radiusPanel
    property real shadowOpacity: 0.42
    property bool shadowEnabled: true
    default property alias content: contentItem.data

    MultiEffect {
        visible: root.shadowEnabled
        anchors.fill: surface
        // Use the real rounded glass surface as the source.  A dark source
        // rectangle is composited by MultiEffect as well as its shadow and
        // therefore becomes a visible square/black backplate around cards.
        source: surface
        shadowEnabled: root.shadowEnabled
        shadowColor: Theme.shadow
        shadowOpacity: root.shadowOpacity
        shadowBlur: 0.62
        shadowVerticalOffset: 3
        blurMax: 20
    }
    Rectangle {
        id: surface
        anchors.fill: parent
        radius: root.panelRadius
        color: root.surfaceColor
        border.width: 1
        border.color: root.strokeColor
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.lighter(root.surfaceColor, 1.10) }
            GradientStop { position: 0.12; color: root.surfaceColor }
            GradientStop { position: 1.0; color: Qt.darker(root.surfaceColor, 1.10) }
        }
        Rectangle {
            anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: root.panelRadius; rightMargin: root.panelRadius }
            height: 1
            color: Theme.highlight
            opacity: 0.45
        }
    }
    Item { id: contentItem; anchors.fill: parent }
}
