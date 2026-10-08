import QtQuick
import QtQuick.Controls
import ".."

ComboBox {
    id: root
    implicitWidth: 180; implicitHeight: 38
    contentItem: Text { leftPadding: 12; rightPadding: 26; text: root.displayText; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody; verticalAlignment: Text.AlignVCenter; elide: Text.ElideRight }
    indicator: Text { x: root.width - width - 12; anchors.verticalCenter: parent.verticalCenter; text: "\u25be"; color: Theme.muted; font.pixelSize: 15 }
    background: Rectangle { radius: Theme.radiusControl; color: Theme.control; border.width: 1; border.color: root.hovered || root.popup.visible ? Theme.borderActive : Theme.borderSoft }
    delegate: ItemDelegate {
        required property var modelData
        width: root.width; height: 34
        contentItem: Text { text: modelData; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { radius: 7; color: highlighted ? Theme.cardHover : "transparent" }
    }
    popup: Popup {
        y: root.height + 4; width: root.width; implicitHeight: contentItem.implicitHeight; padding: 5
        contentItem: ListView { clip: true; implicitHeight: contentHeight; model: root.popup.visible ? root.delegateModel : null; currentIndex: root.highlightedIndex; ScrollIndicator.vertical: ScrollIndicator {} }
        background: Rectangle { radius: Theme.radiusControl; color: Theme.panelStrong; border.width: 1; border.color: Theme.borderSoft }
    }
}
