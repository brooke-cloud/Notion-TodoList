import QtQuick
import ".."

GlassPanel {
    // Match Task cards: no dark outer backplate in dense scrolling lists.
    shadowEnabled: false
    id: root
    property string goalId:""; property string goalTitle:""; property string statusLabel:""; property int progress:0
    property int totalTasks:0; property int completedTasks:0; property string updated:""
    signal opened
    height:94; panelRadius:Theme.radiusCard; surfaceColor:hover.hovered?Theme.cardHover:Theme.card
    HoverHandler{id:hover}
    Row { anchors.fill:parent; anchors.margins:16; spacing:18
        ProgressRing { width:62;height:62;value:root.progress/100;centerText:root.progress+"%";caption:"";centerFontSize:13 }
        Column { width:parent.width-250;anchors.verticalCenter:parent.verticalCenter;spacing:8
            Text{text:root.goalTitle;color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontCard;font.bold:true;elide:Text.ElideRight;width:parent.width}
            Text{text:root.totalTasks+" 个小目标  ·  "+root.completedTasks+" 已完成";color:Theme.muted;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}
        }
        Column { width:130;anchors.verticalCenter:parent.verticalCenter;spacing:7
            Rectangle{width:88;height:26;radius:9;color:root.statusLabel==="已完成"?"#6842E2B3":Theme.accentSoft
                Text{anchors.centerIn:parent;text:root.statusLabel;color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}}
            Text{text:root.updated?"更新 "+root.updated.slice(0,10):"";color:Theme.dim;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}
        }
    }
    TapHandler{onTapped:root.opened()}
}
