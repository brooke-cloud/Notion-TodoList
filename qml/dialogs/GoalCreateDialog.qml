import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Popup{id:root;modal:true;focus:true;width:560;height:430;anchors.centerIn:Overlay.overlay;background:GlassPanel{surfaceColor:Theme.panelStrong}
    property bool saving:false
    Column{anchors.fill:parent;anchors.margins:24;spacing:14
        Text{text:"新建大目标";color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontSection;font.bold:true}
        Text{text:"目标名称";color:Theme.muted;font.family:Theme.fontFamily} GlassInput{id:titleField;width:parent.width}
        Text{text:"初始状态：未开始";color:Theme.muted;font.family:Theme.fontFamily}
        Text{text:"Notes";color:Theme.muted;font.family:Theme.fontFamily}
        TextArea{id:notesField;width:parent.width;height:140;color:Theme.text;background:Rectangle{color:Theme.control;radius:Theme.radiusControl;border.color:Theme.borderSoft}}
        Row{anchors.right:parent.right;spacing:10;GlassButton{text:"取消";onClicked:root.close()} GlassButton{text:root.saving?"创建中…":"创建";primary:true;enabled:!root.saving;onClicked:{if(!titleField.text.trim())return;root.saving=true;appBridge.createGoal(titleField.text,"Not Started",notesField.text)}}}
    }
    Connections{target:appBridge;function onGoalCreateSucceeded(){root.saving=false;root.close()}function onGoalCreateFailed(message){root.saving=false}}
}
