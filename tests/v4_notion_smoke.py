"""Safe, staged Notion smoke test for V4."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.notion_service import NotionService

PREFIX = "[V4 TEST]"
CONFIRMATION = "I UNDERSTAND V4 TEST WRITES"
STATE_PATH = Path(__file__).with_name(".v4_smoke_state.json")


def dry_run():
    print("DRY RUN - NO NOTION WRITES")
    print("PLAN Task: create, re-read, edit title/category/priority/date, complete, uncomplete, postpone, delete")
    print("PLAN Goal: create, re-read, rename, cycle Not Started/In Progress/Completed, delete")
    print("PLAN Relation: create one Goal and one Task, link by page ID, verify, retain IDs for restart checks")
    print(f"PLAN Cleanup: only IDs recorded in {STATE_PATH.name}, after exact [V4 TEST] title verification")


def require_confirmation():
    value = input(f'Type exactly "{CONFIRMATION}" to allow test writes: ')
    if value != CONFIRMATION:
        raise SystemExit("WRITE_REFUSED: confirmation did not match")


def load_state():
    if not STATE_PATH.exists():
        raise RuntimeError(f"State file not found: {STATE_PATH}")
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    allowed = {"goal_page_id", "goal_title", "task_page_id", "task_title", "stage"}
    if set(data) - allowed:
        raise RuntimeError("Unsafe or unexpected fields in smoke state")
    return data


def save_state(data):
    STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_task(service, task_id):
    return next((task for task in service.fetch_all_tasks() if task.id == task_id), None)


def find_task_by_exact_title(service, title):
    matches = [task for task in service.fetch_all_tasks() if task.title == title]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one freshly-created test task, found {len(matches)}")
    return matches[0]


def guard_task(service, task_id):
    task = find_task(service, task_id)
    if task is None or not task.title.startswith(PREFIX):
        raise RuntimeError(f"REFUSED task mutation: page {task_id} is missing or is not test-owned")
    return task


def guard_goal(service, goal_id):
    goal = service.fetch_goal(goal_id)
    if not goal.title.startswith(PREFIX):
        raise RuntimeError(f"REFUSED goal mutation: page {goal_id} is not test-owned")
    return goal


def task_crud(service, suffix):
    title = f"{PREFIX} Task CRUD {suffix}"; task_id = ""
    try:
        service.create_task(title, date.today(), "单次", "中", "工作")
        task = find_task_by_exact_title(service, title); task_id = task.id
        guard_task(service, task_id)
        edited = f"{PREFIX} Task CRUD Renamed {suffix}"
        service.update_task_detail(task_id, edited, date.today(), task.repeat_type, "高", "学习", task.notes)
        task = guard_task(service, task_id)
        assert task.title == edited and task.date[:10] == date.today().isoformat()
        if service.priority_supported: assert task.priority == "高"
        if service.project_supported: assert task.project == "学习"
        service.update_task_status(task_id, True); assert guard_task(service, task_id).is_done is True
        service.update_task_status(task_id, False); assert guard_task(service, task_id).is_done is False
        tomorrow = date.today() + timedelta(days=1)
        service.move_task_to_date(task_id, tomorrow); assert guard_task(service, task_id).date[:10] == tomorrow.isoformat()
        print("TASK_CRUD_PASS")
    finally:
        if task_id:
            guard_task(service, task_id); service.delete_task(task_id)


def goal_crud(service, suffix):
    goal = service.create_goal(f"{PREFIX} Goal CRUD {suffix}", "Not Started", "V4 smoke")
    try:
        goal = guard_goal(service, goal.id); renamed = f"{PREFIX} Goal CRUD Renamed {suffix}"
        for status in ("Not Started", "In Progress", "Completed"):
            guard_goal(service, goal.id); service.update_goal(goal.id, renamed, status, "V4 smoke")
            current = guard_goal(service, goal.id)
            assert current.title == renamed and current.status == status
        assert current.status == "Completed"
        print("GOAL_CRUD_PASS")
    finally:
        guard_goal(service, goal.id); service.delete_goal(goal.id)


def create_relation_fixture(service, suffix):
    if STATE_PATH.exists():
        raise RuntimeError("Existing relation fixture found; verify or cleanup it before --write")
    goal = service.create_goal(f"{PREFIX} Goal Relation {suffix}", "In Progress", "V4 relation smoke")
    task_id = ""
    try:
        title = f"{PREFIX} Task Relation {suffix}"
        service.create_task(title, date.today(), "单次", "中", "未分类")
        task = find_task_by_exact_title(service, title); task_id = task.id
        guard_task(service, task_id); guard_goal(service, goal.id)
        service.update_task_goal_relation(task_id, goal.id)
        assert guard_task(service, task_id).goal_id == goal.id
        save_state({"goal_page_id": goal.id, "goal_title": goal.title,
                    "task_page_id": task_id, "task_title": title, "stage": "linked"})
        print("RELATION_CREATE_PASS")
    except Exception:
        if task_id:
            try: guard_task(service, task_id); service.delete_task(task_id)
            except Exception: pass
        try: guard_goal(service, goal.id); service.delete_goal(goal.id)
        except Exception: pass
        raise


def verify_relation(service, expected):
    state = load_state(); task = guard_task(service, state["task_page_id"]); guard_goal(service, state["goal_page_id"])
    if expected:
        assert task.goal_id == state["goal_page_id"]; print("RELATION_PERSISTENCE_PASS")
    else:
        assert not task.goal_id; print("RELATION_EMPTY_PERSISTENCE_PASS")


def remove_relation(service):
    state = load_state(); task = guard_task(service, state["task_page_id"]); guard_goal(service, state["goal_page_id"])
    service.update_task_goal_relation(task.id, None)
    assert not guard_task(service, task.id).goal_id
    state["stage"] = "unlinked"; save_state(state); print("RELATION_REMOVE_PASS")


def cleanup(service):
    state = load_state(); failures = []
    for kind, page_id in (("task", state["task_page_id"]), ("goal", state["goal_page_id"])):
        try:
            if kind == "task": guard_task(service, page_id); service.delete_task(page_id)
            else: guard_goal(service, page_id); service.delete_goal(page_id)
            print(f"CLEANUP_DELETED {kind} {page_id}")
        except Exception as exc:
            failures.append((kind, page_id, str(exc)))
    if failures:
        print("CLEANUP_FAILED")
        for kind, page_id, reason in failures: print(f"{kind} {page_id} {reason}")
        raise SystemExit(1)
    STATE_PATH.unlink(missing_ok=True); print("CLEANUP_PASS")


def parse_args():
    parser = argparse.ArgumentParser(); modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify-relation", action="store_true")
    modes.add_argument("--remove-relation", action="store_true")
    modes.add_argument("--verify-no-relation", action="store_true")
    modes.add_argument("--cleanup", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if not any(vars(args).values()): dry_run(); return
    if args.write or args.remove_relation or args.cleanup: require_confirmation()
    service = NotionService()
    if args.write:
        suffix = uuid4().hex[:8]; task_crud(service, suffix); goal_crud(service, suffix); create_relation_fixture(service, suffix)
    elif args.verify_relation: verify_relation(service, True)
    elif args.remove_relation: remove_relation(service)
    elif args.verify_no_relation: verify_relation(service, False)
    elif args.cleanup: cleanup(service)


if __name__ == "__main__": main()
