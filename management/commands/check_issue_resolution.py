import logging

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.gitlab.gitlab_client import GitLabClient


logger = logging.getLogger("ResolutionChecker")


class Command(BaseCommand):
    help = "GitLab Issue 关闭原因检查工具：自动提醒负责人补充 resolution::* 标签。"

    def add_arguments(self, parser):
        parser.add_argument("--project-id", type=int, required=True, help="GitLab 项目 ID")
        parser.add_argument("--auto-comment", action="store_true", help="是否自动添加提醒评论")

    def handle(self, *args, **options):
        client = GitLabClient(self.settings.gitlab.url, self.settings.gitlab.token)
        project_id = options.get("project_id")
        self.stdout.write(f"正在扫描项目 {project_id} 中缺失关闭原因的 Issue...\n")

        try:
            # 获取已关闭的 Issue (通过 GitLabClient 简化)
            # 注意：GitLabClient 需要支持获取 closed issues 的能力
            # 如果不支持，我们沿用 requests 逻辑，但通过 settings 获取配置
            issues = list(client.get_project_issues(project_id, state="closed"))
        except Exception as e:
            self.stdout.write(f"❌ 获取 Issues 失败: {e}\n")
            return False

        target_issues = []
        for issue in issues:
            labels = issue.get("labels", [])
            if "type::bug" in labels or "type::requirement" in labels:
                if not any(l.startswith("resolution::") for l in labels):
                    target_issues.append(issue)

        if not target_issues:
            self.stdout.write("✓ 未发现异常 Issue，所有已关闭需求和缺陷均已标记原因。\n")
            return True

        self.stdout.write(f"发现 {len(target_issues)} 个 Issue 缺失关闭原因。\n")
        for issue in target_issues:
            self.stdout.write(f"⚠️ 异常 Issue: #{issue['iid']} - {issue['title']}\n")
            if options.get("auto_comment"):
                if not self._has_already_commented(client, project_id, issue["iid"]):
                    self._add_resolution_reminder(client, project_id, issue)
                else:
                    self.stdout.write(f"   - Issue #{issue['iid']} 已存在提醒评论，跳过。\n")

        return True

    def _has_already_commented(self, client, project_id, iid):
        try:
            notes = client.get_issue_notes(project_id, iid)
            return any("⚠️ **关闭原因缺失提醒**" in note.get("body", "") for note in notes)
        except Exception:
            return False

    def _add_resolution_reminder(self, client, project_id, issue):
        iid = issue["iid"]
        assignee = issue.get("assignee")
        mention = f"@{assignee['username']}" if assignee else "负责人"
        comment = (
            f"⚠️ **关闭原因缺失提醒**\n\n{mention} 您好，此议题已关闭，但尚未标记**关闭原因 (Resolution)**。\n\n"
            f"为了便于质量统计和复盘，请通过以下方式补充原因：\n"
            f"1. 在右侧标签栏手动选择 `resolution::*` 标签。\n"
            f'2. 或在评论区回复 Quick Action 指令，例如：`/label ~"resolution::done"`。\n\n'
            f"**可选原因说明**:\n- `resolution::done` - 已完成\n- `resolution::duplicate` - 重复\n- `resolution::postponed` - 延期\n- `resolution::wontfix` - 不做\n- `resolution::by_design` - 设计如此\n\n"
            f"---\n*此评论由自动化巡检工具生成*\n"
        )
        try:
            client.add_issue_note(project_id, iid, comment)
            self.stdout.write(f"   [FIXED] Added reminder to #{iid}\n")
            return True
        except Exception as e:
            self.stdout.write(f"   [FAILED] Failed to add reminder to #{iid}: {e}\n")
            return False
