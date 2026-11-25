# Notion TodoList V4

基于 Python、PySide6 和 Qt Quick/QML 的 Windows 桌面任务管理应用。任务与大目标通过 Notion API 同步；界面采用 Deep Navy Glass 风格。

## 功能

- 创建、编辑、完成、删除和顺延任务；按今天、昨天、明天或全部日期查看。
- 管理大目标、关联小目标任务，并查看完成进度与状态。
- 设置专注和休息时长，使用专注计时器。
- 查看任务完成情况、分类分布、目标进度和历史工作日报。
- 按北京时间生成日报并处理逾期未完成任务；可在设置中关闭每日自动顺延和日报自动弹出。
- 使用本地缓存、后台 Worker 和 Qt Bridge 更新界面与 Notion 数据。

## 项目结构

| 路径 | 用途 |
| --- | --- |
| `main.py` | 桌面应用入口与 QML 加载 |
| `qml/` | 页面、组件、弹窗和主题 |
| `qt_app/` | Qt Bridge、列表模型及后台 Worker |
| `models/`、`controllers/`、`services/`、`app/` | 数据模型、业务控制、Notion 服务和应用状态 |
| `design/`、`assets/` | 运行时背景和应用图标 |
| `tests/` | 自动测试与 QML 稳定性检查 |
| `NotionTodoListV4.spec`、`build_v4_release.ps1` | Windows onedir 打包配置与脚本 |

## 安装与运行

建议使用 Python 3.13 和 PowerShell。在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

在 `.env` 中填写自己的 `NOTION_TOKEN`、`NOTION_DATABASE_ID` 和 `GOAL_DATABASE_ID`；必要时填写 `GOAL_DATA_SOURCE_ID`。程序也兼容 `NOTION_API_KEY`。请在 Notion 中将任务和目标数据库共享给对应的 Integration，并保持数据库属性与当前应用的映射一致。模板中的值只是占位符。

## Windows EXE 打包

在已安装依赖和 PyInstaller 的 Python 环境中执行：

```powershell
python -m pip install pyinstaller
.\build_v4_release.ps1
```

脚本使用 `NotionTodoListV4.spec` 构建 onedir 版本，输出到 `dist\Notion TodoList V4\`。运行其中的 `Notion TodoList.exe`；移动或分发时须保留整个目录及 `_internal` 子目录。脚本会检查关键 QML、背景、图标和证书资源，并在替换旧发布目录时保留原有发布目录旁的本地 `.env`。首次使用时应为发布目录单独配置 `.env`。

## 数据与安全

源码运行时的 `.env` 和 `settings.json` 位于项目根目录；EXE 运行时从 EXE 所在目录读取配置。日报与启动日志保存在用户的 `%LOCALAPPDATA%\NotionTodoListV4\` 下。打包脚本当前会将项目根目录的 `settings.json` 复制到发布目录，分发前请检查并移除个人配置；也不要分发包含真实 `.env` 的发布目录。

`.gitignore` 排除 `.env`、本地设置、日志、缓存、`build/`、`dist/` 和 EXE。不要将 Token、数据库链接或个人任务数据提交到仓库；已经进入 Git 历史的敏感信息不会因 `.gitignore` 而消失。
