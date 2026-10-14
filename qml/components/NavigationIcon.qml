import QtQuick
import ".."

Item {
    id: root
    required property string kind
    property color iconColor: Theme.muted
    width: 20
    height: 20

    Canvas {
        id: canvas
        anchors.centerIn: parent
        width: 20
        height: 20
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            ctx.strokeStyle = root.iconColor
            ctx.lineWidth = 1.8
            ctx.lineCap = "round"
            ctx.lineJoin = "round"
            if (root.kind === "tasks") {
                ctx.strokeRect(3.5, 3.5, 13, 13)
                ctx.beginPath(); ctx.moveTo(6.5, 10); ctx.lineTo(9, 12.5); ctx.lineTo(14, 7.5); ctx.stroke()
            } else if (root.kind === "goals") {
                ctx.beginPath(); ctx.arc(10, 10, 6.5, 0, Math.PI * 2); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(10, 6.5); ctx.lineTo(10, 10); ctx.lineTo(13.5, 10); ctx.stroke()
            } else if (root.kind === "analytics") {
                ctx.strokeRect(3.5, 11, 2.5, 5.5); ctx.strokeRect(8.75, 7.5, 2.5, 9); ctx.strokeRect(14, 4, 2.5, 12.5)
            } else {
                ctx.beginPath(); ctx.arc(10, 10, 3.2, 0, Math.PI * 2); ctx.stroke()
                for (let i = 0; i < 8; ++i) {
                    const angle = i * Math.PI / 4
                    const x1 = 10 + Math.cos(angle) * 5
                    const y1 = 10 + Math.sin(angle) * 5
                    const x2 = 10 + Math.cos(angle) * 7
                    const y2 = 10 + Math.sin(angle) * 7
                    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke()
                }
            }
        }
        Connections { target: root; function onIconColorChanged() { canvas.requestPaint() } }
    }
}
