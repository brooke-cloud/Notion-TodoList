import QtQuick
import QtQuick.Controls
import ".."
import "../components"

Popup{id:root;property var taskData:({});property var goalModel;modal:true;focus:true;width:560;height:560;anchors.centerIn:Overlay.overlay;background:GlassPanel{surfaceColor:Theme.panelStrong}
    property bool saving:false
    property bool goalCleared:false
    onOpened:{saving=false;goalCleared=false;titleField.text=taskData.title||"";categoryBox.currentIndex=Math.max(0,["未分类","学习","工作","副业","生活"].indexOf(taskData.category));priority.currentIndex=Math.max(0,["P0","P1","P2"].indexOf(taskData.priority));dateField.text=taskData.date||"";goalBox.currentIndex=goalModel.indexOfId(taskData.goalId||"")}
    Column{anchors.fill:parent;anchors.margins:24;spacing:11
        Text{text:"编辑任务";color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontSection;font.bold:true}
        Text{text:"任务标题";color:Theme.muted;font.family:Theme.fontFamily} GlassInput{id:titleField;width:parent.width}
        Text{text:"分类";color:Theme.muted;font.family:Theme.fontFamily} ComboBox{id:categoryBox;width:parent.width;height:42;model:["未分类","学习","工作","副业","生活"]}
        Text{text:"优先级";color:Theme.muted;font.family:Theme.fontFamily} GlassSegmentedControl{id:priority;width:parent.width;model:["P0","P1","P2"]}
        Text{text:"日期";color:Theme.muted;font.family:Theme.fontFamily}
        Row{width:parent.width;spacing:8;GlassInput{id:dateField;width:parent.width-170;placeholderText:"YYYY-MM-DD"} GlassButton{width:76;text:"今天";onClicked:dateField.text=Qt.formatDate(new Date(),"yyyy-MM-dd")} GlassButton{width:78;text:"明天";onClicked:{let d=new Date();d.setDate(d.getDate()+1);dateField.text=Qt.formatDate(d,"yyyy-MM-dd")}}}
        Text{text:"大目标";color:Theme.muted;font.family:Theme.fontFamily}
        Row{width:parent.width;spacing:8
            ComboBox{id:goalBox;width:parent.width-108;height:42;model:root.goalModel;textRole:"title";valueRole:"id";onActivated:root.goalCleared=false}
            GlassButton{width:100;height:42;text:root.goalCleared?"不关联 ✓":"不关联";onClicked:{root.goalCleared=true;goalBox.currentIndex=-1}}
        }
        Item{width:1;height:6}
        Row{anchors.right:parent.right;spacing:10
            GlassButton{text:"取消";onClicked:root.close()}
            GlassButton{text:root.saving?"保存中…":"保存修改";primary:true;enabled:!root.saving;onClicked:{if(!titleField.text.trim())return;let selectedGoal=root.goalCleared?"":(goalBox.currentIndex>=0?goalBox.currentValue:"");root.saving=true;appBridge.updateTask(taskData.id,titleField.text,categoryBox.currentText,priority.model[priority.currentIndex],dateField.text,selectedGoal)}}
        }
    }
    Connections{target:appBridge;function onTaskSaveSucceeded(taskId){if(taskId===root.taskData.id){root.saving=false;root.close()}}function onTaskSaveFailed(taskId,message){if(taskId===root.taskData.id)root.saving=false}}
}
