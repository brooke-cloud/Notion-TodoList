import QtQuick
import QtQuick.Controls
import ".."
import "../components"
import "../dialogs"

GlassPanel {
    id:root;property var taskModel;property int tabIndex:0;surfaceColor:"#B20A2037"
    Column{anchors.fill:parent;anchors.margins:20;spacing:12
        GlassButton{width:88;height:38;text:"‹ 返回";onClicked:appBridge.closeGoal()}
        Row{width:parent.width;height:70
            Column{width:parent.width-190;spacing:8
                Text{id:titleText;text:appBridge.selectedGoal.title||"";color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontPage;font.bold:true
                    MouseArea{anchors.fill:parent;acceptedButtons:Qt.LeftButton;onDoubleClicked:{renameField.text=titleText.text;renameField.visible=true;renameField.forceActiveFocus();renameField.selectAll()}}}
                GlassInput{
                    id:renameField
                    visible:false
                    width:520
                    text:""
                    onAccepted:{if(text.trim()){appBridge.renameGoal(appBridge.selectedGoalId,text.trim())} visible=false}
                    Keys.onEscapePressed:visible=false
                }
                Row{spacing:12
                    GlassButton{width:105;height:32;text:(appBridge.selectedGoal.statusLabel||"未开始")+"  ▾";onClicked:statusPopup.open()}
                    Text{text:(appBridge.selectedGoal.progress||0)+"%";color:Theme.accent;font.family:Theme.fontFamily;font.pixelSize:Theme.fontBody;font.bold:true;anchors.verticalCenter:parent.verticalCenter}
                    Text{text:(appBridge.selectedGoal.completedTasks||0)+" / "+(appBridge.selectedGoal.totalTasks||0)+" 个小目标";color:Theme.muted;font.family:Theme.fontFamily;font.pixelSize:Theme.fontBody;anchors.verticalCenter:parent.verticalCenter}
                }
            }
            GlassButton{width:170;text:"＋ 添加小目标";primary:true;onClicked:addSheet.open()}
        }
        GlassSegmentedControl{width:parent.width;model:["小目标任务","统计分析","详细信息"];onSelected:(index,value)=>root.tabIndex=index}
        ListView{visible:root.tabIndex===0;width:parent.width;height:parent.height-190;model:root.taskModel;spacing:9;clip:true
            delegate:TaskCard{property string taskId:model.id;width:ListView.view.width-8;taskTitle:model.title;category:model.category;priority:model.priority;taskDate:model.date;goal:model.goalTitle;completed:model.isDone;inGoalDetail:true;onToggled:appBridge.toggleTaskDone(taskId);onEditRequested:appBridge.editTask(taskId);onPostponeRequested:appBridge.postponeTask(taskId);onFocusRequested:appBridge.focusTask(taskId);onDeleteRequested:appBridge.deleteTask(taskId);onRemoveGoalRequested:appBridge.removeTaskFromGoal(taskId)}}
        Column{visible:root.tabIndex===1;spacing:14
            Text{text:"总小目标  "+(appBridge.selectedGoal.totalTasks||0)+"    已完成  "+(appBridge.selectedGoal.completedTasks||0)+"    完成率  "+(appBridge.selectedGoal.progress||0)+"%";color:Theme.text;font.family:Theme.fontFamily;font.pixelSize:Theme.fontSection}
            Text{text:(appBridge.selectedGoal.totalTasks||0)>0?"数据来自当前 Goal 的真实关联任务":"暂无真实数据";color:Theme.muted;font.family:Theme.fontFamily}
        }
        Column{visible:root.tabIndex===2;spacing:12
            Text{text:"名称："+(appBridge.selectedGoal.title||"");color:Theme.text;font.family:Theme.fontFamily}
            Text{text:"状态："+(appBridge.selectedGoal.statusLabel||"");color:Theme.text;font.family:Theme.fontFamily}
            Text{text:"Notes："+(appBridge.selectedGoal.notes||"暂无");color:Theme.muted;font.family:Theme.fontFamily;wrapMode:Text.Wrap;width:parent.width}
            Text{text:"最后更新："+(appBridge.selectedGoal.lastUpdated||"");color:Theme.dim;font.family:Theme.fontFamily}
        }
    }
    Popup{id:statusPopup;width:150;height:126;modal:false;focus:true;x:20;y:145;background:GlassPanel{surfaceColor:Theme.panelStrong}
        Column{anchors.fill:parent;anchors.margins:6;Repeater{model:[{label:"未开始",value:"Not Started"},{label:"进行中",value:"In Progress"},{label:"已完成",value:"Completed"}]
            GlassButton{required property var modelData;width:parent.width;height:36;text:modelData.label;onClicked:{appBridge.setGoalStatus(appBridge.selectedGoalId,modelData.value);statusPopup.close()}}}}
    }
    AddSmallGoalSheet{id:addSheet;allTaskModel:allTaskListModel}
}
