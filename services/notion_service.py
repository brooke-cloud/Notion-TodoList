import os
import re
import sys
import threading
from urllib.parse import unquote, urlparse

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from models.task import Task
from models.goal import Goal


def get_base_dir():
    # 打包成 exe 后使用 exe 所在目录
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # Python 运行时使用项目根目录
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = get_base_dir()
load_dotenv(os.path.join(BASE_DIR, ".env"))
NOTION_API_KEY = os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")


def normalize_database_id(value):
    """同时接受 Notion 数据库 ID 和浏览器中的完整数据库链接。"""
    raw_value = (value or "").strip()
    if not raw_value:
        return ""
    if raw_value.startswith(("https://", "http://")):
        path = unquote(urlparse(raw_value).path)
        matches = re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])", path)
        return matches[-1] if matches else ""
    compact_value = raw_value.replace("-", "")
    return compact_value if re.fullmatch(r"[0-9a-fA-F]{32}", compact_value) else ""


DATABASE_ID = normalize_database_id(os.getenv("NOTION_DATABASE_ID"))
BIG_GOAL_DATABASE_ID = normalize_database_id(
    os.getenv("GOAL_DATABASE_ID") or os.getenv("BIG_GOAL_DATABASE_ID")
)
GOAL_DATA_SOURCE_ID = normalize_database_id(os.getenv("GOAL_DATA_SOURCE_ID"))
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
GOAL_NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2025-09-03",
    "Content-Type": "application/json",
}


def response_diagnostic(response):
    status = response.status_code
    try:
        payload = response.json()
    except ValueError:
        return "JSON_ERROR", "响应不是有效 JSON"
    code = payload.get("code", "")
    message = payload.get("message", "")
    if status == 401:
        return "UNAUTHORIZED", message
    if status == 403:
        return "ACCESS_DENIED", message
    if status == 404:
        return "ACCESS_DENIED" if "shared with your integration" in message else "INVALID_ID", message
    if status == 429 or code == "rate_limited":
        return "RATE_LIMITED", message
    return f"HTTP_{status}", message


def log_goal_response(response, endpoint, *, database_id, data_source_id):
    """Log only safe request diagnostics; authentication is never included."""
    try:
        code = response.json().get("code", "OK")
    except ValueError:
        code = "invalid_json"
    print(
        f"[Notion] Goal request: HTTP {response.status_code}; code={code}; "
        f"endpoint={endpoint}; database_id={database_id}; "
        f"data_source_id={data_source_id}"
    )


class NotionService:
    def __init__(self):
        # 检查必要环境变量
        if not NOTION_API_KEY:
            raise RuntimeError("没有找到 NOTION_API_KEY，请检查 .env 文件")
        if not DATABASE_ID:
            raise RuntimeError("NOTION_DATABASE_ID 无效，请填写数据库 ID 或完整 Notion 数据库链接")
        # 创建带重试能力的 Session
        self.session = requests.Session()
        self.api_lock = threading.Lock()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "POST", "PATCH"]),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.timeout = 12
        # 可选字段支持状态
        self.priority_supported = False
        self.project_supported = False
        self.notes_supported = False
        self.goal_relation_available = False
        self.goals_available = False
        self.goal_schema_error = ""
        self.goal_diagnostic = "NOT_CONFIGURED"
        self.goal_data_source_id = GOAL_DATA_SOURCE_ID
        self.goal_status_type = "status"
        self.goal_notes_supported = False
        self.project_options = []
        self.category_property = ""
        self.detect_database_schema()
        self.detect_goal_schema()

    def request(self, method, url, **kwargs):
        # 所有 Notion 请求统一增加 headers、timeout 和线程锁
        kwargs.setdefault("headers", NOTION_HEADERS)
        kwargs.setdefault("timeout", self.timeout)
        with self.api_lock:
            return self.session.request(method, url, **kwargs)

    def detect_database_schema(self):
        # 读取数据库字段结构并自动识别可选功能
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
        try:
            resp = self.request("GET", url)
        except requests.RequestException as exc:
            print("[Notion] Todo database: NETWORK_ERROR")
            print(f"[Notion][debug] Todo database: {exc}")
            raise RuntimeError("Notion 网络连接失败") from exc
        if resp.status_code != 200:
            diagnostic, detail = response_diagnostic(resp)
            print(f"[Notion] Todo database: {diagnostic}")
            print(f"[Notion][debug] Todo database HTTP {resp.status_code}: {detail}")
            raise RuntimeError(f"Todo 数据库连接失败：{diagnostic}")
        try:
            properties = resp.json().get("properties", {})
        except ValueError as exc:
            print("[Notion] Todo database: JSON_ERROR")
            raise RuntimeError("Todo 数据库响应解析失败") from exc
        print("[Notion] Todo database: OK")
        priority_prop = properties.get("优先级")
        self.priority_supported = bool(priority_prop and priority_prop.get("type") == "select")
        # 正式字段为“分类”；仅对旧数据库的“项目”字段保留兼容读取。
        self.category_property = "分类" if "分类" in properties else "项目" if "项目" in properties else ""
        project_prop = properties.get(self.category_property) if self.category_property else None
        self.project_supported = bool(project_prop and project_prop.get("type") == "select")
        if self.project_supported:
            options = project_prop.get("select", {}).get("options", [])
            self.project_options = [item.get("name", "") for item in options if item.get("name")]
        notes_prop = properties.get("备注")
        self.notes_supported = bool(notes_prop and notes_prop.get("type") == "rich_text")
        relation_prop = properties.get("大目标")
        relation_data = (relation_prop or {}).get("relation") or {}
        relation_target = relation_data.get("database_id", "")
        relation_data_source = relation_data.get("data_source_id", "")
        target_matches = (
            (BIG_GOAL_DATABASE_ID and normalize_database_id(relation_target) == BIG_GOAL_DATABASE_ID)
            or (self.goal_data_source_id and normalize_database_id(relation_data_source) == self.goal_data_source_id)
            or (not BIG_GOAL_DATABASE_ID and not self.goal_data_source_id)
        )
        self.goal_relation_available = bool(
            relation_prop and relation_prop.get("type") == "relation"
            and target_matches
        )

    def detect_goal_schema(self):
        if not self.goal_data_source_id:
            if not BIG_GOAL_DATABASE_ID:
                self.goal_schema_error = "未配置 GOAL_DATABASE_ID"
                self.goal_diagnostic = "INVALID_ID"
                print("[Notion] Goal database: INVALID_ID")
                return
            try:
                database_resp = self.request(
                    "GET", f"https://api.notion.com/v1/databases/{BIG_GOAL_DATABASE_ID}",
                    headers=GOAL_NOTION_HEADERS,
                )
            except requests.RequestException as exc:
                self.goal_diagnostic = "NETWORK_ERROR"
                self.goal_schema_error = "大目标数据库网络连接失败"
                print("[Notion] Goal database: NETWORK_ERROR")
                print(f"[Notion][debug] Goal database discovery: {exc}")
                return
            if database_resp.status_code != 200:
                diagnostic, detail = response_diagnostic(database_resp)
                self.goal_diagnostic = diagnostic
                self.goal_schema_error = (
                    "无法访问大目标数据库\n当前 Notion Integration 尚未获得该数据库访问权限。"
                    if diagnostic == "ACCESS_DENIED" else f"大目标数据库不可用（{diagnostic}）"
                )
                print(f"[Notion] Goal database: {diagnostic}")
                print(
                    f"[Notion][debug] Goal database discovery HTTP {database_resp.status_code}; "
                    f"database_id={BIG_GOAL_DATABASE_ID}; {detail}"
                )
                return
            try:
                data_sources = database_resp.json().get("data_sources", [])
            except ValueError:
                self.goal_diagnostic = "JSON_ERROR"
                self.goal_schema_error = "大目标数据库响应解析失败"
                print("[Notion] Goal database: JSON_ERROR")
                return
            if not data_sources:
                self.goal_diagnostic = "INVALID_ID"
                self.goal_schema_error = "大目标数据库没有可用的 Data Source"
                print("[Notion] Goal database: INVALID_ID")
                return
            self.goal_data_source_id = normalize_database_id(data_sources[0].get("id"))
        endpoint = f"https://api.notion.com/v1/data_sources/{self.goal_data_source_id}"
        try:
            resp = self.request(
                "GET", endpoint,
                headers=GOAL_NOTION_HEADERS,
            )
        except requests.RequestException as exc:
            self.goal_diagnostic = "NETWORK_ERROR"
            self.goal_schema_error = "大目标数据库网络连接失败"
            print("[Notion] Goal database: NETWORK_ERROR")
            print(f"[Notion][debug] Goal endpoint={endpoint}; data_source_id={self.goal_data_source_id}; {exc}")
            return
        try:
            response_payload = resp.json()
        except ValueError:
            response_payload = None
        log_goal_response(
            resp, endpoint, database_id=BIG_GOAL_DATABASE_ID,
            data_source_id=self.goal_data_source_id,
        )
        if resp.status_code != 200:
            diagnostic, detail = response_diagnostic(resp)
            self.goal_diagnostic = diagnostic
            self.goal_schema_error = (
                "无法访问大目标数据库\n当前 Notion Integration 尚未获得该数据库访问权限。"
                if diagnostic == "ACCESS_DENIED" else f"大目标数据库不可用（{diagnostic}）"
            )
            print(f"[Notion] Goal database: {diagnostic}")
            print(
                f"[Notion][debug] Goal database HTTP {resp.status_code}; "
                f"database_id={BIG_GOAL_DATABASE_ID}; data_source_id={self.goal_data_source_id}; {detail}"
            )
            return
        if response_payload is None:
            self.goal_diagnostic = "JSON_ERROR"
            self.goal_schema_error = "大目标数据库响应解析失败"
            print("[Notion] Goal database: JSON_ERROR")
            return
        properties = response_payload.get("properties", {})
        required = ("Task", "Status")
        missing = [name for name in required if name not in properties]
        if missing:
            self.goal_schema_error = "大目标数据库缺少字段：" + "、".join(missing)
            self.goal_diagnostic = "INVALID_SCHEMA"
            print("[Notion] Goal database: INVALID_SCHEMA")
            return
        self.goal_status_type = properties["Status"].get("type", "status")
        self.goal_notes_supported = (properties.get("Notes") or {}).get("type") == "rich_text"
        self.goals_available = True
        self.goal_diagnostic = "OK"
        print("[Notion] Goal database: OK")

    def parse_task(self, item, target_date=None):
        # 将 Notion 页面转换成 Task 数据模型
        props = item.get("properties", {})
        title_list = props.get("Task", {}).get("title", [])
        title = "".join(part.get("plain_text", "") for part in title_list).strip() or "未命名任务"
        repeat_type = (props.get("重复", {}).get("select") or {}).get("name", "单次")
        status_name = (props.get("状态", {}).get("status") or {}).get("name", "未开始")
        date_data = props.get("日期", {}).get("date")
        task_date = date_data.get("start", "") if date_data else ""
        priority = "中"
        if self.priority_supported:
            priority = (props.get("优先级", {}).get("select") or {}).get("name", "中")
        project = "未分类"
        if self.project_supported:
            project = (props.get(self.category_property, {}).get("select") or {}).get("name", "未分类")
        notes = ""
        if self.notes_supported:
            notes_list = props.get("备注", {}).get("rich_text", [])
            notes = "".join(part.get("plain_text", "") for part in notes_list)
        relations = props.get("大目标", {}).get("relation", []) if self.goal_relation_available else []
        goal_id = relations[0].get("id") if relations else None
        # 每日任务在日期视图中按“状态+日期”判断当天是否完成
        if repeat_type == "每天" and target_date is not None:
            is_done = status_name == "完成" and task_date == target_date.isoformat()
        else:
            is_done = status_name == "完成"
        return Task(
            id=item["id"],
            title=title,
            priority=priority,
            project=project,
            notes=notes,
            date=task_date,
            repeat_type=repeat_type,
            is_done=is_done,
            goal_id=goal_id,
        )

    def sort_tasks(self, tasks):
        # 未完成任务优先，再按优先级、项目和标题排序
        priority_order = {"高": 0, "中": 1, "低": 2}
        tasks.sort(
            key=lambda task: (
                task.is_done,
                priority_order.get(task.priority, 1),
                task.project,
                task.title,
            )
        )
        return tasks

    def query_all_pages(self, payload):
        # 自动处理 Notion 查询分页
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        all_results = []
        next_cursor = None
        while True:
            body = dict(payload)
            if next_cursor:
                body["start_cursor"] = next_cursor
            resp = self.request("POST", url, json=body)
            if resp.status_code != 200:
                raise Exception(f"查询任务失败：{resp.text}")
            data = resp.json()
            all_results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            next_cursor = data.get("next_cursor")
            if not next_cursor:
                break
        return all_results

    def fetch_tasks_for_date(self, target_date):
        # 查询指定日期任务以及每日习惯
        target_iso = target_date.isoformat()
        payload = {
            "filter": {
                "or": [
                    {"property": "日期", "date": {"equals": target_iso}},
                    {"property": "重复", "select": {"equals": "每天"}},
                ]
            }
        }
        results = self.query_all_pages(payload)
        return self.sort_tasks([self.parse_task(item, target_date) for item in results])

    def fetch_inbox_tasks(self):
        # 收件箱定义为“日期为空且不是每日习惯”
        payload = {
            "filter": {
                "and": [
                    {"property": "日期", "date": {"is_empty": True}},
                    {"property": "重复", "select": {"does_not_equal": "每天"}},
                ]
            }
        }
        results = self.query_all_pages(payload)
        return self.sort_tasks([self.parse_task(item) for item in results])

    def fetch_all_open_tasks(self):
        # 全部视图读取所有未完成任务
        payload = {
            "filter": {
                "property": "状态",
                "status": {"does_not_equal": "完成"},
            }
        }
        results = self.query_all_pages(payload)
        return self.sort_tasks([self.parse_task(item) for item in results])

    def fetch_all_tasks(self):
        results = self.query_all_pages({})
        return self.sort_tasks([self.parse_task(item) for item in results])

    def create_task(self, title, target_date, repeat_type, priority, project, goal_id=None):
        # 创建新任务
        url = "https://api.notion.com/v1/pages"
        properties = {
            "Task": {"title": [{"text": {"content": title}}]},
            "状态": {"status": {"name": "未开始"}},
            "重复": {"select": {"name": repeat_type}},
            "日期": {"date": {"start": target_date.isoformat()}} if target_date else {"date": None},
        }
        if self.priority_supported:
            properties["优先级"] = {"select": {"name": priority}}
        if self.project_supported and project and project != "未分类":
            properties[self.category_property] = {"select": {"name": project}}
        if goal_id:
            if not self.goal_relation_available:
                raise RuntimeError("任务数据库缺少“大目标”Relation，无法关联任务")
            properties["大目标"] = {"relation": [{"id": goal_id}]}
        payload = {"parent": {"database_id": DATABASE_ID}, "properties": properties}
        resp = self.request("POST", url, json=payload)
        if resp.status_code not in (200, 201):
            raise Exception(f"创建任务失败：{resp.text}")

    def query_database_pages(self, database_id, payload=None):
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        all_results, next_cursor = [], None
        while True:
            body = dict(payload or {})
            if next_cursor:
                body["start_cursor"] = next_cursor
            resp = self.request("POST", url, json=body)
            if resp.status_code != 200:
                raise Exception(f"查询 Notion 数据库失败：{resp.text}")
            data = resp.json()
            all_results.extend(data.get("results", []))
            if not data.get("has_more"):
                return all_results
            next_cursor = data.get("next_cursor")

    def query_goal_pages(self, payload=None):
        url = f"https://api.notion.com/v1/data_sources/{self.goal_data_source_id}/query"
        all_results, next_cursor = [], None
        while True:
            body = dict(payload or {})
            if next_cursor:
                body["start_cursor"] = next_cursor
            resp = self.request("POST", url, json=body, headers=GOAL_NOTION_HEADERS)
            log_goal_response(
                resp, url, database_id=BIG_GOAL_DATABASE_ID,
                data_source_id=self.goal_data_source_id,
            )
            if resp.status_code != 200:
                diagnostic, detail = response_diagnostic(resp)
                print(f"[Notion] Goal database: {diagnostic}")
                print(
                    f"[Notion][debug] Goal query HTTP {resp.status_code}; "
                    f"endpoint={url}; database_id={BIG_GOAL_DATABASE_ID}; "
                    f"data_source_id={self.goal_data_source_id}; {detail}"
                )
                raise RuntimeError(f"大目标数据库查询失败（{diagnostic}）")
            try:
                data = resp.json()
            except ValueError as exc:
                print("[Notion] Goal database: JSON_ERROR")
                raise RuntimeError("大目标数据库响应解析失败") from exc
            all_results.extend(data.get("results", []))
            if not data.get("has_more"):
                return all_results
            next_cursor = data.get("next_cursor")

    @staticmethod
    def _plain_text(prop):
        values = prop.get(prop.get("type", "rich_text"), []) if prop else []
        return "".join(item.get("plain_text", "") for item in values).strip()

    def parse_goal(self, item):
        props = item.get("properties", {})
        title = self._plain_text(props.get("Task", {})) or "未命名大目标"
        status_prop = props.get("Status", {})
        status_data = status_prop.get("status") or status_prop.get("select") or {}
        notes = self._plain_text(props.get("Notes", {}))
        updated_prop = props.get("Last Updated", {})
        updated = updated_prop.get("last_edited_time") or (updated_prop.get("date") or {}).get("start", "")
        return Goal(item["id"], title, status_data.get("name", "Not Started"), notes, updated)

    def fetch_goals(self):
        if not self.goals_available:
            raise RuntimeError(self.goal_schema_error or "大目标数据库不可用")
        return [self.parse_goal(item) for item in self.query_goal_pages()]

    def fetch_goal(self, goal_id):
        resp = self.request("GET", f"https://api.notion.com/v1/pages/{goal_id}", headers=GOAL_NOTION_HEADERS)
        if resp.status_code != 200:
            raise Exception(f"读取大目标失败：{resp.text}")
        return self.parse_goal(resp.json())

    def fetch_tasks_by_goal(self, goal_id):
        if not self.goal_relation_available:
            return []
        payload = {"filter": {"property": "大目标", "relation": {"contains": goal_id}}}
        return self.sort_tasks([self.parse_task(item) for item in self.query_all_pages(payload)])

    def create_goal(self, title, status="Not Started", notes=""):
        if not self.goals_available:
            raise RuntimeError(self.goal_schema_error or "大目标数据库不可用")
        properties = {"Task": {"title": [{"text": {"content": title}}]}}
        properties["Status"] = {self.goal_status_type: {"name": status}}
        if notes and self.goal_notes_supported:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]}
        resp = self.request("POST", "https://api.notion.com/v1/pages", headers=GOAL_NOTION_HEADERS, json={
            "parent": {"type": "data_source_id", "data_source_id": self.goal_data_source_id},
            "properties": properties,
        })
        if resp.status_code not in (200, 201):
            raise Exception(f"创建大目标失败：{resp.text}")
        return self.parse_goal(resp.json())

    def update_goal(self, goal_id, title, status, notes):
        properties = {"Task": {"title": [{"text": {"content": title}}]}}
        properties["Status"] = {self.goal_status_type: {"name": status}}
        if self.goal_notes_supported:
            properties["Notes"] = {"rich_text": [{"text": {"content": notes}}]} if notes else {"rich_text": []}
        resp = self.request("PATCH", f"https://api.notion.com/v1/pages/{goal_id}",
                            headers=GOAL_NOTION_HEADERS, json={"properties": properties})
        if resp.status_code != 200:
            raise Exception(f"更新大目标失败：{resp.text}")

    def delete_goal(self, goal_id):
        resp = self.request("PATCH", f"https://api.notion.com/v1/pages/{goal_id}", headers=GOAL_NOTION_HEADERS, json={"archived": True})
        if resp.status_code != 200:
            raise Exception(f"删除大目标失败：{resp.text}")

    def update_task_title(self, page_id, new_title):
        # 更新任务标题
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {"properties": {"Task": {"title": [{"text": {"content": new_title}}]}}}
        resp = self.request("PATCH", url, json=payload)
        if resp.status_code != 200:
            raise Exception(f"修改任务标题失败：{resp.text}")

    def update_task_goal_relation(self, page_id, goal_id=None):
        """Update only the existing Goal relation using Notion page IDs."""
        if not self.goal_relation_available:
            raise RuntimeError("任务数据库缺少“大目标”Relation")
        relation = [{"id": goal_id}] if goal_id else []
        resp = self.request(
            "PATCH",
            f"https://api.notion.com/v1/pages/{page_id}",
            json={"properties": {"大目标": {"relation": relation}}},
        )
        if resp.status_code != 200:
            raise Exception(f"更新任务大目标 Relation 失败：{resp.text}")

    def update_task_status(self, page_id, is_done, target_date=None):
        # 更新任务完成状态
        url = f"https://api.notion.com/v1/pages/{page_id}"
        properties = {"状态": {"status": {"name": "完成" if is_done else "未开始"}}}
        if is_done and target_date is not None:
            properties["日期"] = {"date": {"start": target_date.isoformat()}}
        resp = self.request("PATCH", url, json={"properties": properties})
        if resp.status_code != 200:
            raise Exception(f"修改任务状态失败：{resp.text}")

    def update_task_detail(self, page_id, title, target_date, repeat_type, priority, project, notes):
        # 一次性保存标题、日期、重复、优先级、项目和备注
        url = f"https://api.notion.com/v1/pages/{page_id}"
        properties = {
            "Task": {"title": [{"text": {"content": title}}]},
            "重复": {"select": {"name": repeat_type}},
            "日期": {"date": {"start": target_date.isoformat()}} if target_date else {"date": None},
        }
        if self.priority_supported:
            properties["优先级"] = {"select": {"name": priority}}
        if self.project_supported:
            properties[self.category_property] = {"select": {"name": project}} if project and project != "未分类" else {"select": None}
        if self.notes_supported:
            properties["备注"] = {"rich_text": [{"text": {"content": notes}}]} if notes else {"rich_text": []}
        resp = self.request("PATCH", url, json={"properties": properties})
        if resp.status_code != 200:
            raise Exception(f"保存任务详情失败：{resp.text}")

    def move_task_to_date(self, page_id, new_date):
        # 将任务顺延到指定日期
        url = f"https://api.notion.com/v1/pages/{page_id}"
        payload = {
            "properties": {
                "日期": {"date": {"start": new_date.isoformat()}},
                "状态": {"status": {"name": "未开始"}},
            }
        }
        resp = self.request("PATCH", url, json=payload)
        if resp.status_code != 200:
            raise Exception(f"顺延任务失败：{resp.text}")

    def delete_task(self, page_id):
        # Notion 删除页面实际使用 archived=True
        url = f"https://api.notion.com/v1/pages/{page_id}"
        resp = self.request("PATCH", url, json={"archived": True})
        if resp.status_code != 200:
            raise Exception(f"删除任务失败：{resp.text}")
