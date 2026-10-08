# Notion TodoList V4

Notion TodoList V4 是一个 Windows 桌面任务管理应用，使用 Python、PySide6 与 Qt Quick/QML 构建，并通过 Notion API 读写任务和目标数据。

## 主要功能

- 任务的创建、编辑、完成、删除与顺延；按日期、分类、目标和关键词查看。
- 目标的创建、编辑、删除、关联任务和进度计算。
- 25 分钟专注与 5 分钟休息计时，可选择当前专注任务。
- 任务完成率、分类分布、完成趋势与目标进度统计。
- 可配置启动页、默认视图、专注时长、自动同步和界面显示选项。

## 技术栈

- Python 3、PySide6、Qt Quick / QML
- `python-dotenv`、`requests`（Notion 配置与 HTTP 请求）
- PyInstaller（Windows onedir 发布包）

## 项目结构

```text
├── main.py                    # 应用入口
├── app/                       # 应用状态
├── controllers/               # 任务、目标和统计控制器
├── models/                    # 任务、目标数据模型
├── services/                  # Notion API 服务
├── qt_app/                    # Qt Bridge、列表模型和后台任务
├── qml/                       # 页面、组件和对话框
├── design/、assets/           # 设计资源和应用图标
├── tests/                     # 自动化测试
├── requirements.txt           # Python 依赖
├── NotionTodoListV4.spec      # PyInstaller 配置
└── build_v4_release.ps1       # Windows 发布包构建脚本
```

## 安装与运行

```powershell
git clone https://github.com/brooke-cloud/Notion-TodoList.git
cd Notion-TodoList
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

## Notion API 配置

将 `.env.example` 复制为项目根目录的 `.env` 后填写自己的值：

```env
NOTION_TOKEN=secret_your_notion_integration_token
NOTION_DATABASE_ID=your-task-database-id-or-url
GOAL_DATABASE_ID=your-goal-database-id-or-url
GOAL_DATA_SOURCE_ID=your-goal-data-source-id
```

- `NOTION_TOKEN` 是首选配置名；程序也兼容 `NOTION_API_KEY`。
- `NOTION_DATABASE_ID` 用于任务数据库，可填写 ID 或完整 Notion 数据库链接。
- `GOAL_DATABASE_ID` 用于目标数据库；未填写 `GOAL_DATA_SOURCE_ID` 时，程序会依据目标数据库尝试发现数据源。
- 请在 Notion 中把相应数据库共享给你的 Integration，否则应用无法读取或写入数据。

## Windows EXE 打包

在已激活的虚拟环境中执行：

```powershell
.\build_v4_release.ps1
```

脚本调用 PyInstaller，并生成 `dist\Notion TodoList V4` 的 onedir 发布目录。请分发整个目录，而不是只复制其中的 EXE；脚本会检查发布目录中是否意外出现 `.env` 或常见凭据文件。

## 安全说明

- `.env`、本地 `settings.json`、日志、缓存、构建产物和 EXE 均在 `.gitignore` 中排除；仅提交 `.env.example` 模板。
- 不要提交或通过 Issue、日志、截图发送 Notion Token、数据库链接、个人任务数据或其他凭据。
- 新增 `.gitignore` 无法移除已经提交的敏感信息；推送前也应检查待推送历史。

## 许可证

当前仓库未声明开源许可证；使用、修改和再分发权限以仓库所有者后续发布的许可证为准。
