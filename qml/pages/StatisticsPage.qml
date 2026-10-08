import QtQuick
import QtQuick.Controls
import ".."
import "../components"

GlassPanel {
    id: root
    surfaceColor: "#B20A2037"
    property var data: appBridge.analyticsData || ({})
    property int gap: 14
    Flickable {
        anchors.fill: parent; anchors.margins: 24; contentWidth: width; contentHeight: dashboard.height; clip: true
        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
        Column {
            id: dashboard; width: parent.width; height: childrenRect.height; spacing: 16
            Text { text: "\u7edf\u8ba1\u5206\u6790"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontPage; font.bold: true }
            Grid {
                width: parent.width; columns: 4; spacing: root.gap
                Repeater {
                    model: [{label:"\u4efb\u52a1\u603b\u6570",value:root.data.total||0},{label:"\u5df2\u5b8c\u6210",value:root.data.completed||0},{label:"\u5f85\u5b8c\u6210",value:root.data.pending||0},{label:"\u5b8c\u6210\u7387",value:(root.data.rate||0)+"%"}]
                    GlassPanel { required property var modelData; width:(dashboard.width-root.gap*3)/4; height:104
                        Column { anchors.centerIn:parent; spacing:6
                            Text { anchors.horizontalCenter:parent.horizontalCenter; text:modelData.value; color:Theme.accent; font.family:Theme.fontFamily; font.pixelSize:27; font.bold:true }
                            Text { anchors.horizontalCenter:parent.horizontalCenter; text:modelData.label; color:Theme.muted; font.family:Theme.fontFamily; font.pixelSize:Theme.fontBody }
                        }
                    }
                }
            }
            Grid {
                width: parent.width; columns: width >= 920 ? 2 : 1; spacing: root.gap
                property real cardWidth: columns === 2 ? (width-root.gap)/2 : width
                GlassPanel { width:parent.cardWidth; height:250
                    Column { anchors.fill:parent; anchors.margins:18; spacing:8
                        Text { text:"\u6700\u8fd17\u5929\u5b8c\u6210\u8d8b\u52bf"; color:Theme.text; font.family:Theme.fontFamily; font.pixelSize:Theme.fontSection; font.bold:true }
                        Item { width:parent.width; height:190
                            Text { anchors.centerIn:parent; visible:!(root.data.weekly&&root.data.weekly.length); text:"\u6682\u65e0\u8d8b\u52bf\u6570\u636e"; color:Theme.dim }
                            Canvas { id:lineChart; anchors.fill:parent; visible:root.data.weekly&&root.data.weekly.length
                                onPaint: { var c=getContext("2d"),a=root.data.weekly||[];c.reset();if(!a.length)return;var max=1;for(var i=0;i<a.length;i++)max=Math.max(max,a[i].count);var left=22,top=18,w=width-42,h=height-46;c.strokeStyle="#345778";c.lineWidth=1;for(i=0;i<4;i++){var y=top+h*i/3;c.beginPath();c.moveTo(left,y);c.lineTo(left+w,y);c.stroke()}c.strokeStyle=Theme.accent;c.lineWidth=3;c.beginPath();for(i=0;i<a.length;i++){var x=left+w*i/Math.max(1,a.length-1),py=top+h-(a[i].count/max)*h;if(i===0)c.moveTo(x,py);else c.lineTo(x,py)}c.stroke();for(i=0;i<a.length;i++){x=left+w*i/Math.max(1,a.length-1);py=top+h-(a[i].count/max)*h;c.fillStyle="#42E2B3";c.beginPath();c.arc(x,py,4,0,Math.PI*2);c.fill();c.fillStyle="#B5CAE0";c.font="11px Microsoft YaHei UI";c.fillText(a[i].day,x-5,height-8)} }
                                Connections { target:appBridge; function onAnalyticsChanged(){lineChart.requestPaint()} }
                                MouseArea { anchors.fill:parent; hoverEnabled:true; onPositionChanged:(mouse)=>{var a=root.data.weekly||[];if(!a.length)return;var i=Math.max(0,Math.min(a.length-1,Math.round((mouse.x-22)/Math.max(1,width-42)*(a.length-1))));trendTip.text=a[i].day+"  "+a[i].count;trendTip.x=Math.min(width-trendTip.width,Math.max(0,mouse.x+8));trendTip.y=Math.max(0,mouse.y-32);trendTip.visible=true}; onExited:trendTip.visible=false }
                                Rectangle { id:trendTip; visible:false; z:4; width:tipText.implicitWidth+18; height:28; radius:8; color:Theme.panelStrong; border.color:Theme.borderActive; property alias text:tipText.text; Text{id:tipText;anchors.centerIn:parent;color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta} }
                            }
                        }
                    }
                }
                GlassPanel { width:parent.cardWidth; height:250
                    Column { anchors.fill:parent; anchors.margins:18; spacing:10
                        Text { text:"\u4efb\u52a1\u5206\u7c7b\u5206\u5e03"; color:Theme.text; font.family:Theme.fontFamily; font.pixelSize:Theme.fontSection; font.bold:true }
                        Text { visible:!(root.data.categories&&root.data.categories.length); text:"\u6682\u65e0\u5206\u7c7b\u6570\u636e"; color:Theme.dim }
                        Repeater { model:root.data.categories||[]
                            Column { required property var modelData; width:parent.width; spacing:3
                                Row { width:parent.width
                                    Text{width:parent.width-45;text:modelData.name;color:Theme.muted;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}
                                    Text{text:modelData.count;color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}
                                }
                                Rectangle { width:parent.width; height:8; radius:4; color:Theme.control; Rectangle{width:parent.width*Math.max(.02,modelData.count/Math.max(1,root.data.total||1));height:parent.height;radius:4;color:Theme.accent} }
                            }
                        }
                    }
                }
                GlassPanel { width:parent.cardWidth; height:230
                    Column { anchors.fill:parent; anchors.margins:18; spacing:10
                        Text { text:"\u5927\u76ee\u6807\u5b8c\u6210\u8fdb\u5ea6"; color:Theme.text; font.family:Theme.fontFamily; font.pixelSize:Theme.fontSection; font.bold:true }
                        Text { visible:!(root.data.goals&&root.data.goals.length); text:"\u6682\u65e0\u8fdb\u884c\u4e2d\u7684\u5927\u76ee\u6807"; color:Theme.dim }
                        Repeater { model:root.data.goals||[]
                            Column { required property var modelData; width:parent.width; spacing:4
                                Row { width:parent.width
                                    Text{width:parent.width-50;text:modelData.title;color:Theme.muted;elide:Text.ElideRight;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}
                                    Text{text:modelData.progress+"%";color:Theme.text;font.pixelSize:Theme.fontMeta}
                                }
                                Rectangle { width:parent.width;height:7;radius:4;color:Theme.control;Rectangle{width:parent.width*modelData.progress/100;height:parent.height;radius:4;color:Theme.success} }
                            }
                        }
                    }
                }
                GlassPanel { width:parent.cardWidth; height:230
                    Row { anchors.fill:parent; anchors.margins:18; spacing:22
                        Canvas { id:ratioChart; width:150; height:150; anchors.verticalCenter:parent.verticalCenter
                            onPaint:{var c=getContext("2d");c.reset();var rate=(root.data.rate||0)/100;c.lineWidth=18;c.strokeStyle="#243E58";c.beginPath();c.arc(width/2,height/2,52,0,Math.PI*2);c.stroke();c.strokeStyle="#42E2B3";c.beginPath();c.arc(width/2,height/2,52,-Math.PI/2,-Math.PI/2+Math.PI*2*rate);c.stroke()}
                            Connections{target:appBridge;function onAnalyticsChanged(){ratioChart.requestPaint()}}
                            Text{anchors.centerIn:parent;text:(root.data.rate||0)+"%";color:Theme.text;font.pixelSize:24;font.bold:true}
                        }
                        Column { anchors.verticalCenter:parent.verticalCenter; spacing:14
                            Text{text:"\u5df2\u5b8c\u6210 / \u5f85\u5b8c\u6210";color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontSection;font.bold:true}
                            Text{text:"\u5df2\u5b8c\u6210  "+(root.data.completed||0);color:Theme.success;font.family:Theme.fontFamily}
                            Text{text:"\u5f85\u5b8c\u6210  "+(root.data.pending||0);color:Theme.muted;font.family:Theme.fontFamily}
                            Text{text:"\u672c\u5468\u5171\u8bb0\u5f55 "+(root.data.total||0)+" \u9879\u4efb\u52a1";color:Theme.dim;font.family:Theme.fontFamily;font.pixelSize:Theme.fontMeta}
                        }
                    }
                }
            }
            Item { width:1; height:10 }
        }
    }
}
