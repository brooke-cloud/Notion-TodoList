import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Popup {
    id: root
    property var report: ({})
    modal: true
    focus: true
    width: 680
    height: Math.min(610, reportPanel.height + 240)
    anchors.centerIn: Overlay.overlay
    background: GlassPanel { surfaceColor: Theme.panelStrong }
    function showReport(value) { report = value || ({}); open() }
    function categoryText() {
        var data = report.categories || ({}), parts = []
        Object.keys(data).sort().forEach(function(name) {
            var item = data[name] || ({})
            parts.push(name + " " + (item.completed || 0) + "/" + (item.total || 0))
        })
        return parts.length ? parts.join("  ·  ") : "无分类数据"
    }
    function priorityText() {
        var data = report.priorities || ({}), parts = []
        Object.keys(data).sort().forEach(function(name) { parts.push(name + " " + data[name]) })
        return parts.length ? parts.join("  ·  ") : "无优先级数据"
    }
    Column {
        anchors.fill: parent; anchors.margins: 24; spacing: 14
        Text { text: "每日工作日报 · " + (root.report.date || ""); color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontPage; font.bold: true }
        Text { text: "任务 " + (root.report.total || 0) + " · 完成 " + (root.report.completed || 0) + " · 未完成 " + (root.report.pending || 0) + " · 完成率 " + (root.report.completion_rate || 0) + "%"; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody }
        Text { text: "自动顺延 " + (root.report.auto_postponed || 0) + " 项"; color: Theme.accent; font.family: Theme.fontFamily }
        Text { visible: root.report.accuracy === "partial_historical_snapshot"; text: "历史数据无法完全还原，本日报已标记为部分快照。"; color: Theme.warning; font.family: Theme.fontFamily }
        GlassPanel { id: reportPanel; width: parent.width; height: Math.min(350, Math.max(190, reportContent.implicitHeight + 32))
            ScrollView { id: reportScroll; anchors.fill: parent; anchors.margins: 16; clip: true
                Column { id: reportContent; width: reportScroll.availableWidth; spacing: 9
                    Text { text: "主要未完成任务"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    Text { visible: !(root.report.main_pending && root.report.main_pending.length); text: "无未完成任务"; color: Theme.success; font.family: Theme.fontFamily }
                    Repeater { model: root.report.main_pending || []
                        RowLayout { required property var modelData; width: reportScroll.availableWidth; spacing: 12
                            Text { Layout.fillWidth: true; text: "• " + modelData.title; color: Theme.muted; font.family: Theme.fontFamily; wrapMode: Text.Wrap; maximumLineCount: 2 }
                            Text { Layout.alignment: Qt.AlignTop; text: "[" + (modelData.category || "未分类") + "]  " + (modelData.priority || "未设置"); color: Theme.dim; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta }
                        }
                    }
                    Text { text: "分类完成情况"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    Text { width: reportScroll.availableWidth; text: root.categoryText(); color: Theme.muted; font.family: Theme.fontFamily; wrapMode: Text.Wrap }
                    Text { text: "优先级分布"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    Text { width: reportScroll.availableWidth; text: root.priorityText(); color: Theme.muted; font.family: Theme.fontFamily; wrapMode: Text.Wrap }
                    Text { text: "今日待办"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    Text { visible: !(root.report.today_tasks && root.report.today_tasks.length); text: "今日暂无待办"; color: Theme.dim; font.family: Theme.fontFamily }
                    Repeater { model: root.report.today_tasks || []
                        RowLayout { required property var modelData; width: reportScroll.availableWidth; spacing: 12
                            Text { Layout.fillWidth: true; text: "• " + modelData.title; color: Theme.muted; font.family: Theme.fontFamily; wrapMode: Text.Wrap; maximumLineCount: 2 }
                            Text { Layout.alignment: Qt.AlignTop; text: "[" + (modelData.category || "未分类") + "]"; color: Theme.dim; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta }
                        }
                    }
                }
            }
        }
        Item { width: 1; height: 1 }
        Row { anchors.right: parent.right; spacing: 10
            GlassButton { text: "关闭"; onClicked: root.close() }
            GlassButton { text: "查看详细日报"; primary: true; onClicked: { appBridge.selectSection("analytics"); root.close() } }
        }
    }
}
