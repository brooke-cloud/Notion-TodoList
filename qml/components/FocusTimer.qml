import QtQuick
import ".."

GlassPanel {
    id: root
    property string timeText: "25:00"
    property bool running: false
    property int mode: 25
    property int focusMinutes: 25
    property int breakMinutes: 5
    property string taskTitle: "\u6682\u672a\u9009\u62e9\u4e13\u6ce8\u4efb\u52a1"
    signal startRequested
    signal pauseRequested
    signal resetRequested
    signal modeRequested(int minutes)
    signal durationsRequested(int focusMinutes, int breakMinutes)
    height: 394
    Column {
        anchors.fill: parent; anchors.margins: 18; spacing: 8
        Text { text: "\u4e13\u6ce8\u8ba1\u65f6"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
        Text { text: root.taskTitle; color: Theme.dim; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta; elide: Text.ElideRight; width: parent.width }
        ProgressRing { width: 150; height: 150; anchors.horizontalCenter: parent.horizontalCenter; value: 1.0; centerText: root.timeText }
        GlassSegmentedControl { width: parent.width; height: 38; model: [root.focusMinutes+" \u5206\u949f\u4e13\u6ce8", root.breakMinutes+" \u5206\u949f\u4f11\u606f"]; currentIndex: root.mode===root.breakMinutes?1:0; onSelected: (index,value)=>root.modeRequested(index===0?root.focusMinutes:root.breakMinutes) }
        Row {
            width:parent.width;height:38;spacing:6
            GlassInput{id:focusInput;width:74;height:38;text:String(root.focusMinutes);placeholderText:"\u4e13\u6ce8"}
            Text{text:"/";color:Theme.dim;anchors.verticalCenter:parent.verticalCenter}
            GlassInput{id:breakInput;width:64;height:38;text:String(root.breakMinutes);placeholderText:"\u4f11\u606f"}
            GlassButton{width:parent.width-166;height:38;text:"\u5e94\u7528";onClicked:{
                var focusValue=parseInt(focusInput.text)
                var breakValue=parseInt(breakInput.text)
                if(isNaN(focusValue))focusValue=root.focusMinutes
                if(isNaN(breakValue))breakValue=root.breakMinutes
                root.durationsRequested(focusValue,breakValue)
            }}
        }
        Row { width: parent.width; spacing: 10
            GlassButton { width: (parent.width - 10) * .58; text: root.running ? "\u6682\u505c" : "\u5f00\u59cb"; primary: true; onClicked: root.running?root.pauseRequested():root.startRequested() }
            GlassButton { width: (parent.width - 10) * .42; text: "\u91cd\u7f6e"; onClicked: root.resetRequested() }
        }
    }
}
