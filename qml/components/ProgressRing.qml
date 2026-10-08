import QtQuick
import ".."

Item {
    id: root
    property real value: 1.0
    property string centerText: "25:00"
    property string caption: "专注时间"
    property int centerFontSize: Theme.fontTimer
    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            const cx = width / 2, cy = height / 2, radius = Math.min(width, height) / 2 - 13
            ctx.lineCap = "round"
            ctx.lineWidth = 7
            ctx.strokeStyle = "#274967"
            ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke()
            ctx.shadowColor = Theme.glow; ctx.shadowBlur = 15
            const gradient = ctx.createLinearGradient(0, 0, width, height)
            gradient.addColorStop(0, Theme.accentTop); gradient.addColorStop(1, Theme.accent)
            ctx.strokeStyle = gradient
            ctx.beginPath(); ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * root.value); ctx.stroke()
        }
        Connections { target: root; function onValueChanged() { canvas.requestPaint() } }
    }
    Column {
        anchors.centerIn: parent
        spacing: 2
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: root.centerText; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: root.centerFontSize; font.bold: true }
        Text { visible:root.caption.length>0; anchors.horizontalCenter: parent.horizontalCenter; text: root.caption; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody }
    }
}
