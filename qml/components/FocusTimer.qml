import QtQuick
import ".."

GlassPanel {
    id: root
    property string timeText: "25:00"
    property bool running: false
    property int mode: 25
    property string taskTitle: "\u6682\u672a\u9009\u62e9\u4e13\u6ce8\u4efb\u52a1"
    signal startRequested
    signal pauseRequested
    signal resetRequested
    signal modeRequested(int minutes)
    height: 394
    Column {
        anchors.fill: parent; anchors.margins: 18; spacing: 12
        Text { text: "\u4e13\u6ce8\u8ba1\u65f6"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
        Text { text: root.taskTitle; color: Theme.dim; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta; elide: Text.ElideRight; width: parent.width }
        ProgressRing { width: 204; height: 204; anchors.horizontalCenter: parent.horizontalCenter; value: 1.0; centerText: root.timeText }
        GlassSegmentedControl { width: parent.width; height: 40; model: ["25 \u5206\u949f", "5 \u5206\u949f"]; currentIndex: root.mode===25?0:1; onSelected: (index,value)=>root.modeRequested(index===0?25:5) }
        Row { width: parent.width; spacing: 10
            GlassButton { width: (parent.width - 10) * .58; text: root.running ? "\u6682\u505c" : "\u5f00\u59cb"; primary: true; onClicked: root.running?root.pauseRequested():root.startRequested() }
            GlassButton { width: (parent.width - 10) * .42; text: "\u91cd\u7f6e"; onClicked: root.resetRequested() }
        }
    }
}
