import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "."
import "components"
import "pages"
import "dialogs"

ApplicationWindow {
    id: window
    width: 1440
    height: 900
    minimumWidth: 1100
    minimumHeight: 700
    visible: true
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint
    title: "Notion TodoList V4"

    Rectangle {
        id: shell
        anchors.fill: parent
        radius: window.visibility === Window.Maximized ? 0 : 18
        clip: true
        color: Theme.background
        border.width: 1
        border.color: Theme.borderSoft

        Image {
            anchors.fill: parent
            source: backgroundUrl
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            cache: true
            visible: appBridge.settings.show_background_image === undefined || appBridge.settings.show_background_image
            opacity: (appBridge.settings.background_opacity === undefined ? 72 : appBridge.settings.background_opacity) / 100
        }
        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0; color: Theme.overlayTop }
                GradientStop { position: .48; color: "#D0061830" }
                GradientStop { position: 1; color: Theme.overlayBottom }
            }
        }

        Rectangle {
            id: titleBar
            anchors { left: parent.left; right: parent.right; top: parent.top }
            height: 44
            color: "#D007192C"
            border.width: 1
            border.color: Theme.borderSoft
            Row {
                anchors.left: parent.left; anchors.leftMargin: 18; anchors.verticalCenter: parent.verticalCenter; spacing: 10
                Rectangle { width: 28; height: 28; radius: 8; color: Theme.accent; Text { anchors.centerIn: parent; text: "◉"; color: "white"; font.pixelSize: 14 } }
                Text { text: "Notion TodoList"; color: Theme.text; font.family: Theme.fontFamily; font.pixelSize: Theme.fontBody; anchors.verticalCenter: parent.verticalCenter }
                Text { text: "V4 Preview"; color: Theme.dim; font.family: Theme.fontFamily; font.pixelSize: Theme.fontMeta; anchors.verticalCenter: parent.verticalCenter }
            }
            Row {
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                Repeater {
                    model: ["—", "□", "×"]
                    Rectangle {
                        required property int index
                        required property string modelData
                        width: 46; height: 42; color: titleHover.hovered ? (index === 2 ? "#A9E34F68" : "#55284967") : "transparent"
                        Text { anchors.centerIn: parent; text: modelData; color: Theme.muted; font.pixelSize: index === 2 ? 19 : 14 }
                        HoverHandler { id: titleHover }
                        TapHandler {
                            onTapped: {
                                if (index === 0) window.showMinimized()
                                else if (index === 1) window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized()
                                else window.close()
                            }
                        }
                    }
                }
            }
            DragHandler {
                target: null
                onActiveChanged: if (active) window.startSystemMove()
            }
            TapHandler {
                acceptedButtons: Qt.LeftButton
                gesturePolicy: TapHandler.DragThreshold
                onDoubleTapped: window.visibility === Window.Maximized ? window.showNormal() : window.showMaximized()
            }
        }

        Row {
            anchors { left: parent.left; right: parent.right; top: titleBar.bottom; bottom: parent.bottom }
            Sidebar {
                width: 188; height: parent.height
                currentSection: appBridge.section
                onSectionSelected: appBridge.selectSection(section)
            }
            Item {
                width: parent.width - 188; height: parent.height
                Loader {
                    property real interfaceScale: (appBridge.settings.ui_scale === undefined ? 100 : appBridge.settings.ui_scale) / 100
                    anchors.left: parent.left
                    anchors.top: parent.top
                    width: (parent.width - 28) / interfaceScale
                    height: (parent.height - 28) / interfaceScale
                    scale: interfaceScale
                    transformOrigin: Item.TopLeft
                    anchors.margins: 14
                    sourceComponent: appBridge.section === "tasks" ? taskComponent : appBridge.section === "goals" ? goalComponent : appBridge.section === "goalDetail" ? detailComponent : appBridge.section === "analytics" ? analyticsComponent : settingsComponent
                }
            }
        }
    }

    Component { id: taskComponent; TaskPage { taskModel: taskListModel } }
    Component{id:goalComponent;GoalPage{goalModel:goalListModel;onCreateRequested:goalCreate.open()}}
    Component{id:detailComponent;GoalDetailPage{taskModel:taskListModel}}
    Component{id:analyticsComponent;StatisticsPage{}}
    Component{id:settingsComponent;SettingsPage{}}
    TaskEditDialog{id:taskEdit;goalModel:goalListModel}
    GoalCreateDialog{id:goalCreate}
    Rectangle{id:toast;width:Math.min(520,toastText.implicitWidth+40);height:46;radius:12;color:"#E51B3048";border.color:toast.kind==="error"?Theme.danger:Theme.borderActive;visible:false;anchors.horizontalCenter:parent.horizontalCenter;anchors.bottom:parent.bottom;anchors.bottomMargin:24;property string kind:"info"
        Text{id:toastText;anchors.centerIn:parent;color:Theme.text;font.family:Theme.fontFamily}
        Timer{id:toastTimer;interval:3600;onTriggered:toast.visible=false}
    }
    Connections{target:appBridge
        function onTaskEditRequested(data){taskEdit.taskData=data;taskEdit.open()}
        function onToastRequested(message,kind){toastText.text=message;toast.kind=kind;toast.visible=true;toastTimer.restart()}
    }
}
