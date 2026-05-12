import argparse
import datetime
import os
import re
import sys


# 强制 UTF-8 输出，防止 Windows (GBK) 环境下表情符号报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROGRESS_FILE = "progress.txt"
# 历史进度归档已收拢至 CHANGELOG.md。注意：自动化脚本写入可能破坏其结构，建议手动维护。
ARCHIVE_FILE = "CHANGELOG.md"


def read_file(path: str) -> list[str]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return f.readlines()


def write_file(path: str, lines: list[str]):
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def get_sections(lines: list[str]) -> dict:
    sections = {"header": [], "focus": [], "tasks": [], "completed": [], "footer": []}
    current_section = "header"

    for line in lines:
        if line.startswith("## 🎯 当前重点"):
            current_section = "focus"
            sections[current_section].append(line)
        elif line.startswith("## 🛠️ 任务清单"):
            current_section = "tasks"
            sections[current_section].append(line)
        elif line.startswith("## 📋 最近完成"):
            current_section = "completed"
            sections[current_section].append(line)
        elif line.startswith("---"):
            current_section = "footer"
            sections[current_section].append(line)
        else:
            sections[current_section].append(line)

    return sections


def add_task(content: str):
    lines = read_file(PROGRESS_FILE)
    sections = get_sections(lines)

    # 找到最后一个任务编号
    last_num = 0
    for line in sections["tasks"]:
        match = re.match(r"(\d+)\.", line.strip())
        if match:
            last_num = int(match.group(1))

    new_task = f"{last_num + 1}. {content} ⏳ 待实现\n"
    sections["tasks"].append(new_task)

    new_lines = sections["header"] + sections["focus"] + sections["tasks"] + sections["completed"] + sections["footer"]
    write_file(PROGRESS_FILE, new_lines)
    print(f"Added task: {new_task.strip()}")


def mark_done(task_id: int):
    lines = read_file(PROGRESS_FILE)
    sections = get_sections(lines)

    target_idx = -1
    target_line = ""

    for i, line in enumerate(sections["tasks"]):
        if line.strip().startswith(f"{task_id}."):
            target_idx = i
            target_line = line
            break

    if target_idx == -1:
        print(f"Task {task_id} not found.")
        return

    # 移除原任务并重排剩余任务
    sections["tasks"].pop(target_idx)
    renumbered_tasks = []
    current_num = 1
    for line in sections["tasks"]:
        if re.match(r"\d+\.", line.strip()):
            new_line = re.sub(r"^\d+\.", f"{current_num}.", line)
            renumbered_tasks.append(new_line)
            current_num += 1
        else:
            renumbered_tasks.append(line)
    sections["tasks"] = renumbered_tasks

    # 转换任务格式
    clean_task = re.sub(r"⏳ 待实现", "", target_line)
    clean_task = re.sub(r"^\d+\.\s*", "", clean_task).strip()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    completed_line = f"1. {clean_task} ({timestamp})\n"

    # 插入到最近完成的顶部并重排最近完成
    old_completed_lines = []
    for line in sections["completed"]:
        if re.match(r"\d+\.", line.strip()) or line.startswith("##"):
            continue
        old_completed_lines.append(line)

    # 获取现有所有条目内容
    current_items = [completed_line]
    for line in sections["completed"]:
        match = re.match(r"\d+\.\s*(.*)", line.strip())
        if match:
            current_items.append(match.group(1) + "\n")

    # 重新生成带编号的条目
    new_completed = ["## 📋 最近完成 (Recently Completed)\n"]
    for i, content in enumerate(current_items):
        new_completed.append(f"{i + 1}. {content}")

    sections["completed"] = new_completed + old_completed_lines

    new_lines = sections["header"] + sections["focus"] + sections["tasks"] + sections["completed"] + sections["footer"]
    write_file(PROGRESS_FILE, new_lines)
    print(f"Marked task {task_id} as done: {clean_task}")


def archive():
    lines = read_file(PROGRESS_FILE)
    sections = get_sections(lines)

    completed_items = []
    other_completed = []
    for line in sections["completed"]:
        if re.match(r"\d+\.", line.strip()):
            completed_items.append(line)
        elif not line.startswith("##"):
            other_completed.append(line)

    if len(completed_items) <= 5:
        print("No archiving needed (<= 5 items).")
        return

    to_keep = completed_items[:5]
    to_archive = completed_items[5:]

    # 写入存档
    archive_lines = read_file(ARCHIVE_FILE)
    if not archive_lines:
        archive_lines = ["# DevOps Progress Archive\n\n"]

    # 插入到存档顶部
    new_archive = [archive_lines[0], "\n"] + to_archive + archive_lines[1:]
    write_file(ARCHIVE_FILE, new_archive)

    to_keep_lines = []
    for i, line in enumerate(to_keep):
        content = re.sub(r"^\d+\.\s*", "", line).strip()
        to_keep_lines.append(f"{i + 1}. {content}\n")

    # 更新当前文件
    sections["completed"] = ["## 📋 最近完成 (Recently Completed)\n"] + to_keep_lines + other_completed
    new_lines = sections["header"] + sections["focus"] + sections["tasks"] + sections["completed"] + sections["footer"]
    write_file(PROGRESS_FILE, new_lines)
    print(f"Archived {len(to_archive)} items to {ARCHIVE_FILE}")


def update_focus(content: str):
    lines = read_file(PROGRESS_FILE)
    sections = get_sections(lines)

    # 保持标题，替换内容
    new_focus = ["## 🎯 当前重点 (Current Focus)\n", f"- **核心重点**: {content}\n"]

    # 尝试寻找原本的状态行，如果没有则默认
    status_line = "- **状态**: 🟡 正在进行中\n"
    for line in sections["focus"]:
        if line.startswith("- **状态**"):
            status_line = line
            break
    new_focus.append(status_line)
    new_focus.append("\n")

    sections["focus"] = new_focus

    new_lines = sections["header"] + sections["focus"] + sections["tasks"] + sections["completed"] + sections["footer"]
    write_file(PROGRESS_FILE, new_lines)
    print(f"Updated focus: {content}")


def mirror_tasks(tasks_str: str):
    tasks = tasks_str.split(";")
    for task in tasks:
        if task.strip():
            add_task(task.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--add", help="Add a new task")
    parser.add_argument("--done", type=int, help="Mark a task index as done")
    parser.add_argument("--archive", action="store_true", help="Archive old tasks")
    parser.add_argument("--update-focus", help="Update the Current Focus section")
    parser.add_argument("--mirror-tasks", help="Mirror multiple deferred tasks (split by ';')")
    args = parser.parse_args()

    if args.add:
        add_task(args.add)
    elif args.done:
        mark_done(args.done)
    elif args.archive:
        archive()
    elif args.update_focus:
        update_focus(args.update_focus)
    elif args.mirror_tasks:
        mirror_tasks(args.mirror_tasks)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
