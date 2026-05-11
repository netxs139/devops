import csv
import logging

from devops_collector.core.management import BaseCommand
from devops_collector.plugins.gitlab.gitlab_client import GitLabClient
from devops_collector.plugins.gitlab.labels import LABEL_DEFINITIONS


logger = logging.getLogger("LabelChecker")


class Command(BaseCommand):
    help = "GitLab Issue 标签完整性检查工具：自动识别不符合规范的 Issue。"

    def add_arguments(self, parser):
        parser.add_argument("--project-id", type=int, required=True, help="GitLab 项目 ID")
        parser.add_argument("--auto-fix", action="store_true", help="自动添加 needs-labels 标签和评论")
        parser.add_argument("--report", help="保存 CSV 报告路径")

    def handle(self, *args, **options):
        # 1. 初始化客户端
        client = GitLabClient(self.settings.gitlab.url, self.settings.gitlab.token)

        project_id = options.get("project_id")
        self.stdout.write(f"正在获取项目 {project_id} 的打开状态 Issue...\n")

        try:
            issues = list(client.get_project_issues(project_id))
        except Exception as e:
            self.stdout.write(f"❌ 获取 Issue 失败: {e}\n")
            return False

        # 2. 准备检查器逻辑
        label_pools = {}
        for category, items in LABEL_DEFINITIONS.items():
            label_pools[category] = {item["name"] for item in items}

        check_rules = {
            "bug": ["type", "severity", "priority", "bug_category", "bug_source", "province"],
            "feature": ["type", "priority"],
            "test": ["type", "priority"],
        }

        incomplete = []
        for issue in issues:
            labels = issue.get("labels", [])
            issue_type = None
            if "type::bug" in labels:
                issue_type = "bug"
            elif "type::feature" in labels:
                issue_type = "feature"
            elif "type::test" in labels:
                issue_type = "test"

            missing = []
            if not issue_type:
                missing.append("type (Missing or Unknown)")
            else:
                required = check_rules.get(issue_type, [])
                for cat in required:
                    if not any(label in label_pools.get(cat, set()) for label in labels):
                        missing.append(cat)

            if missing:
                item = {"iid": issue["iid"], "title": issue["title"], "type": issue_type or "Unknown", "missing": missing, "url": issue["web_url"]}
                incomplete.append(item)

        # 3. 输出与修复
        self.stdout.write(f"检查完成。总数: {len(issues)}, 不完整: {len(incomplete)}\n")

        for item in incomplete:
            self.stdout.write(f"⚠️ Issue #{item['iid']} 缺少: {', '.join(item['missing'])}\n")
            if options.get("auto_fix"):
                try:
                    client.add_issue_label(project_id, item["iid"], ["needs-labels"])
                    msg = f"⚠️ 标签不完整。缺少类别: {', '.join(item['missing'])}。请根据规范补充。"
                    client.add_issue_note(project_id, item["iid"], msg)
                    self.stdout.write(f"   [FIXED] Added needs-labels & comment to #{item['iid']}\n")
                except Exception as e:
                    self.stdout.write(f"   [FAILED] Fix failed for #{item['iid']}: {e}\n")

        if options.get("report") and incomplete:
            with open(options.get("report"), "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["iid", "title", "type", "missing", "url"])
                writer.writeheader()
                for item in incomplete:
                    row = item.copy()
                    row["missing"] = ",".join(item["missing"])
                    writer.writerow(row)
            self.stdout.write(f"报告已保存至: {options.get('report')}\n")

        return True
