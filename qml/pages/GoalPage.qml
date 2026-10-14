import QtQuick
import QtQuick.Controls
import ".."
import "../components"

GlassPanel {
    id: root
    property var goalModel
    signal createRequested
    surfaceColor: "#B20A2037"

    Column {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 14

        Row {
            id: headerRow
            width: parent.width
            height: 55
            Text { text: "\u5927\u76ee\u6807"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontPage; font.bold: true }
            Text { text: "  " + appBridge.syncText; color: Theme.success; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta; anchors.verticalCenter: parent.verticalCenter }
            Item { width: Math.max(Theme.space24, parent.width - 354); height: 1 }
            GlassButton { width: 150; text: "+ \u65b0\u5efa\u5927\u76ee\u6807"; primary: true; onClicked: root.createRequested() }
            Item { width: Theme.space24; height: 1 }
        }

        GlassSegmentedControl {
            id: statusFilter
            width: parent.width
            model: ["\u672a\u5f00\u59cb", "\u8fdb\u884c\u4e2d", "\u5df2\u5b8c\u6210", "\u5168\u90e8"]
            currentIndex: 3
            onSelected: (index, value) => appBridge.filterGoals(value)
        }

        Row {
            id: searchRow
            width: parent.width
            height: 44
            spacing: 10
            GlassInput { width: parent.width - 170; placeholderText: "\u641c\u7d22\u5927\u76ee\u6807\u3001\u63cf\u8ff0\u6216\u6807\u7b7e\u2026"; leadingIcon: "\u2315"; onTextChanged: appBridge.searchGoals(text) }
            GlassButton { width: 160; text: "\u6240\u6709\u5206\u7c7b" }
        }

        ListView {
            id: goalList
            width: parent.width
            height: Math.max(0, parent.height - headerRow.height - statusFilter.height - searchRow.height - parent.spacing * 3)
            model: root.goalModel
            spacing: 10
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            contentWidth: width
            footer: Item { width: goalList.width; height: 16 }
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            delegate: GoalCard { width: goalList.width - 8; goalId: model.id; goalTitle: model.title; statusLabel: model.statusLabel; progress: model.progress; totalTasks: model.totalTasks; completedTasks: model.completedTasks; updated: model.lastUpdated; onOpened: appBridge.openGoal(goalId) }
        }
    }
}
