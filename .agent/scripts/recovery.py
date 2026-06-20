#!/usr/bin/env python3
"""Session Checkpoint and Recovery Tool.

Supports manual saving of current workspace changes (uncommitted git changes,
progress.txt, and conversation-specific task.md) and restoring them after
reboots or session losses.
"""

import os
import sys
import json
import glob
import subprocess
import shutil
from datetime import datetime

WORKSPACE_DIR = "/home/netxs/devops"
SCRATCH_DIR = os.path.join(WORKSPACE_DIR, ".agent/scratch")
CHECKPOINT_FILE = os.path.join(SCRATCH_DIR, "session_checkpoint.json")
UNSTAGED_PATCH = os.path.join(SCRATCH_DIR, "unstaged_changes.patch")
STAGED_PATCH = os.path.join(SCRATCH_DIR, "staged_changes.patch")
PROGRESS_BACKUP = os.path.join(SCRATCH_DIR, "progress_backup.txt")
TASK_BACKUP = os.path.join(SCRATCH_DIR, "task_backup.md")


def find_active_task_md():
    brain_dir = "/home/netxs/.gemini/antigravity-ide/brain"
    if not os.path.exists(brain_dir):
        return None
    paths = glob.glob(os.path.join(brain_dir, "*/task.md"))
    if not paths:
        return None
    # Sort by modification time, most recent first
    paths.sort(key=os.path.getmtime, reverse=True)
    return paths[0]


def run_command(args, cwd=WORKSPACE_DIR):
    try:
        result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(args)}: {e.stderr}", file=sys.stderr)
        return None


def save_checkpoint():
    print(">>> Creating manual checkpoint...")
    os.makedirs(SCRATCH_DIR, exist_ok=True)

    # 1. Save uncommitted changes as patches
    unstaged_diff = run_command(["git", "diff"])
    if unstaged_diff:
        with open(UNSTAGED_PATCH, "w", encoding="utf-8") as f:
            f.write(unstaged_diff)
        print("  - Saved unstaged changes patch.")
    elif os.path.exists(UNSTAGED_PATCH):
        os.remove(UNSTAGED_PATCH)

    staged_diff = run_command(["git", "diff", "--cached"])
    if staged_diff:
        with open(STAGED_PATCH, "w", encoding="utf-8") as f:
            f.write(staged_diff)
        print("  - Saved staged changes patch.")
    elif os.path.exists(STAGED_PATCH):
        os.remove(STAGED_PATCH)

    # 2. Backup progress.txt
    progress_path = os.path.join(WORKSPACE_DIR, "progress.txt")
    if os.path.exists(progress_path):
        shutil.copy2(progress_path, PROGRESS_BACKUP)
        print("  - Backed up progress.txt.")

    # 3. Backup active task.md
    task_md_path = find_active_task_md()
    if task_md_path and os.path.exists(task_md_path):
        shutil.copy2(task_md_path, TASK_BACKUP)
        print(f"  - Backed up active task.md from: {os.path.basename(os.path.dirname(task_md_path))}")
        task_ref = task_md_path
    else:
        task_ref = None

    # 4. Write metadata
    current_commit = run_command(["git", "rev-parse", "HEAD"])
    current_branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "branch": current_branch,
        "commit": current_commit,
        "has_unstaged_patch": bool(unstaged_diff),
        "has_staged_patch": bool(staged_diff),
        "task_md_path": task_ref,
    }

    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(">>> Checkpoint saved successfully!")


def restore_checkpoint():
    print(">>> Restoring from checkpoint...")
    if not os.path.exists(CHECKPOINT_FILE):
        print("Error: No checkpoint found at .agent/scratch/session_checkpoint.json", file=sys.stderr)
        sys.exit(1)

    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # 1. Verify branch/commit alignment
    current_branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    current_commit = run_command(["git", "rev-parse", "HEAD"])

    if current_branch != metadata["branch"]:
        print(f"Warning: Current branch '{current_branch}' differs from checkpoint branch '{metadata['branch']}'. Switching branch...")
        run_command(["git", "checkout", metadata["branch"]])

    if current_commit != metadata.get("commit"):
        if "--force" not in sys.argv:
            print(
                f"❌ 防呆拦截 (Safety Guard): 当前 Commit ({current_commit[:7]}) 与检查点 Commit ({metadata.get('commit', '')[:7]}) 不匹配！", file=sys.stderr
            )
            print("直接恢复可能导致较新的代码被旧的补丁和进度文件覆盖。", file=sys.stderr)
            print("若您确认要强行时光倒流，请执行: python recovery.py restore --force 或 just recover --force", file=sys.stderr)
            sys.exit(1)
        else:
            print("⚠️ 警告：检测到 --force 参数，正在强制应用跨版本的旧检查点！")

    # 2. Restore progress.txt
    if os.path.exists(PROGRESS_BACKUP):
        shutil.copy2(PROGRESS_BACKUP, os.path.join(WORKSPACE_DIR, "progress.txt"))
        print("  - Restored progress.txt.")

    # 3. Restore task.md
    target_task_md = metadata.get("task_md_path") or find_active_task_md()
    if os.path.exists(TASK_BACKUP):
        if target_task_md:
            os.makedirs(os.path.dirname(target_task_md), exist_ok=True)
            shutil.copy2(TASK_BACKUP, target_task_md)
            print(f"  - Restored task.md to: {target_task_md}")
        else:
            print("  - Task backup exists, but target task.md path could not be resolved.")

    # 4. Apply patches
    if metadata.get("has_staged_patch") and os.path.exists(STAGED_PATCH):
        print("  - Applying staged changes patch...")
        run_command(["git", "apply", STAGED_PATCH])
        # Re-stage the changes
        run_command(["git", "add", "."])  # Simple way to re-stage, or apply specific files

    if metadata.get("has_unstaged_patch") and os.path.exists(UNSTAGED_PATCH):
        print("  - Applying unstaged changes patch...")
        run_command(["git", "apply", UNSTAGED_PATCH])

    print(">>> Workspace restore completed successfully!")


def main():
    if len(sys.argv) < 2:
        print("Usage: python recovery.py [save|restore]")
        sys.exit(1)

    action = sys.argv[1].lower()
    if action == "save":
        save_checkpoint()
    elif action == "restore":
        restore_checkpoint()
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
