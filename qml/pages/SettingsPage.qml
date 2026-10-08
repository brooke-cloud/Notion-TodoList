import QtQuick
import QtQuick.Controls
import ".."
import "../components"

GlassPanel {
    id: root
    surfaceColor: "#B20A2037"
    function value(key, fallback) { return appBridge.settings[key] === undefined ? fallback : appBridge.settings[key] }
    ScrollView {
        anchors.fill: parent; anchors.margins: 24; clip: true
        Column {
            width: root.width - 48; spacing: 14
            Text { text: "\u8bbe\u7f6e"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontPage; font.bold: true }
            Text { text: "\u4fee\u6539\u540e\u7acb\u5373\u4fdd\u5b58\uff0c\u5e76\u5728\u4e0b\u6b21\u542f\u52a8\u65f6\u6062\u590d"; color: Theme.muted; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody }
            GlassPanel { width: parent.width; height: 146
                Column { anchors.fill: parent; anchors.margins: 18; spacing: 8
                    Text { text: "\u901a\u7528\u8bbe\u7f6e"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    SettingsRow { width: parent.width; label: "\u9ed8\u8ba4\u542f\u52a8\u9875\u9762"; GlassComboBox { anchors.fill: parent; model: ["\u4efb\u52a1","\u5927\u76ee\u6807","\u7edf\u8ba1\u5206\u6790"]; currentIndex: Math.max(0,model.indexOf(root.value("startup_page","\u4efb\u52a1"))); onActivated: appBridge.updateSetting("startup_page",currentText) } }
                    SettingsRow { width: parent.width; label: "\u9ed8\u8ba4\u4efb\u52a1\u89c6\u56fe"; GlassComboBox { anchors.fill: parent; model: ["\u4eca\u5929","\u660e\u5929","\u5168\u90e8"]; currentIndex: Math.max(0,model.indexOf(root.value("default_date_view","\u4eca\u5929"))); onActivated: appBridge.updateSetting("default_date_view",currentText) } }
                }
            }
            GlassPanel { width: parent.width; height: 104
                Column { anchors.fill: parent; anchors.margins: 18; spacing: 8
                    Text { text: "\u4efb\u52a1\u8bbe\u7f6e"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    SettingsRow { width: parent.width; label: "\u5b8c\u6210\u4efb\u52a1\u81ea\u52a8\u6c89\u5e95"; GlassSwitch { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; checked: root.value("completed_tasks_to_bottom",true); onToggled: appBridge.updateSetting("completed_tasks_to_bottom",checked) } }
                }
            }
            GlassPanel { width: parent.width; height: 146
                Column { anchors.fill: parent; anchors.margins: 18; spacing: 8
                    Text { text: "\u4e13\u6ce8\u8bbe\u7f6e"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    SettingsRow { width: parent.width; label: "\u9ed8\u8ba4\u4e13\u6ce8\u65f6\u957f"; GlassComboBox { anchors.fill: parent; model: [15,25,45,60]; currentIndex: model.indexOf(root.value("default_focus_minutes",25)); onActivated: appBridge.updateSetting("default_focus_minutes",currentValue) } }
                    SettingsRow { width: parent.width; label: "\u9ed8\u8ba4\u4f11\u606f\u65f6\u957f"; GlassComboBox { anchors.fill: parent; model: [5,10,15]; currentIndex: model.indexOf(root.value("default_break_minutes",5)); onActivated: appBridge.updateSetting("default_break_minutes",currentValue) } }
                }
            }
            GlassPanel { width: parent.width; height: 188
                Column { anchors.fill: parent; anchors.margins: 18; spacing: 8
                    Text { text: "\u540c\u6b65\u8bbe\u7f6e"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    SettingsRow { width: parent.width; label: "\u81ea\u52a8\u540c\u6b65"; GlassSwitch { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; checked: root.value("auto_sync_enabled",false); onToggled: appBridge.updateSetting("auto_sync_enabled",checked) } }
                    SettingsRow { width: parent.width; label: "\u540c\u6b65\u95f4\u9694\uff08\u5206\u949f\uff09"; GlassComboBox { anchors.fill: parent; model: [5,15,30,60]; currentIndex: model.indexOf(root.value("auto_sync_seconds",1800)/60); onActivated: appBridge.updateSetting("auto_sync_seconds",currentValue*60) } }
                    SettingsRow { width: parent.width; label: "\u542f\u52a8\u65f6\u540c\u6b65"; GlassSwitch { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; checked: root.value("sync_on_startup",true); onToggled: appBridge.updateSetting("sync_on_startup",checked) } }
                }
            }
            GlassPanel { width: parent.width; height: 230
                Column { anchors.fill: parent; anchors.margins: 18; spacing: 8
                    Text { text: "\u5916\u89c2\u8bbe\u7f6e"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontSection; font.bold: true }
                    SettingsRow { width: parent.width; label: "\u663e\u793a\u80cc\u666f\u56fe\u7247"; GlassSwitch { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; checked: root.value("show_background_image",true); onToggled: appBridge.updateSetting("show_background_image",checked) } }
                    SettingsRow { width: parent.width; label: "\u80cc\u666f\u4eae\u5ea6 / \u906e\u7f69"
                        Slider { id: bgSlider; anchors.fill: parent; from: 20; to: 100; value: root.value("background_opacity",72); onMoved: appBridge.updateSetting("background_opacity",Math.round(value))
                            background: Rectangle { x:bgSlider.leftPadding; y:bgSlider.topPadding+bgSlider.availableHeight/2-3; width:bgSlider.availableWidth; height:6; radius:3; color:Theme.control }
                            handle: Rectangle { x:bgSlider.leftPadding+bgSlider.visualPosition*(bgSlider.availableWidth-width); y:bgSlider.topPadding+bgSlider.availableHeight/2-height/2; width:16; height:16; radius:8; color:Theme.accent }
                        }
                    }
                    SettingsRow { width: parent.width; label: "\u754c\u9762\u7f29\u653e\uff08%\uff09"; GlassComboBox { anchors.fill: parent; model: [90,100,110,125]; currentIndex: model.indexOf(root.value("ui_scale",100)); onActivated: appBridge.updateSetting("ui_scale",currentValue) } }
                    SettingsRow { width: parent.width; label: "\u901a\u77e5"; GlassSwitch { anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter; checked: root.value("notifications_enabled",true); onToggled: appBridge.updateSetting("notifications_enabled",checked) } }
                }
            }
            Item { width: 1; height: 10 }
        }
    }
}
