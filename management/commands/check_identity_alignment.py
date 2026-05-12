import csv
import logging
from pathlib import Path

from devops_collector.core.management import BaseCommand


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "身份对齐检查脚本 (Identity Alignment Checker)"

    def handle(self, *args, **options):
        docs_dir = Path("docs/assets/sample_data")
        employees_csv = docs_dir / "employees.csv"
        gitlab_csv = docs_dir / "gitlab-user.csv"
        zentao_csv = docs_dir / "zentao-user.csv"

        self.stdout.write("=" * 50 + "\n")
        self.stdout.write("身份对齐检查工具 (Identity Alignment Checker)\n")
        self.stdout.write("=" * 50 + "\n")

        # 1. 加载员工主数据
        self.stdout.write("\n正在加载员工主数据...\n")
        employees_by_email, employees_by_id = self._load_employees(employees_csv)
        self.stdout.write(f"  已加载 {len(employees_by_email)} 条邮箱索引\n")
        self.stdout.write(f"  已加载 {len(employees_by_id)} 条工号索引\n")

        # 2. 检查 GitLab 对齐
        self._check_gitlab_alignment(gitlab_csv, employees_by_email)

        # 3. 检查禅道对齐
        self._check_zentao_alignment(zentao_csv, employees_by_email, employees_by_id)

        self.stdout.write("\n" + "=" * 50 + "\n")
        self.stdout.write("检查完成!\n")
        self.stdout.write("=" * 50 + "\n")
        return True

    def _load_employees(self, csv_path):
        employees_by_email = {}
        employees_by_id = {}
        if not csv_path.exists():
            self.stdout.write(f"❌ 员工主数据文件不存在: {csv_path}\n")
            return employees_by_email, employees_by_id

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                emp_id = row.get("工号", "").strip()
                name = row.get("姓名", "").strip()
                email = row.get("邮箱", "").strip().lower()
                if email:
                    employees_by_email[email] = {"employee_id": emp_id, "name": name, "email": email}
                if emp_id:
                    employees_by_id[emp_id] = {"employee_id": emp_id, "name": name, "email": email}
        return employees_by_email, employees_by_id

    def _check_gitlab_alignment(self, csv_path, employees_by_email):
        self.stdout.write("\n========== GitLab 身份对齐检查 ==========\n")
        if not csv_path.exists():
            self.stdout.write(f"⚠️ GitLab 用户文件不存在: {csv_path}\n")
            return

        issues = []
        matched = 0
        unmatched = 0

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                g_id = row.get("GitLab用户ID", "").strip()
                f_name = row.get("全名", "").strip()
                email = row.get("Email", "").strip().lower()

                if not g_id or not email:
                    continue

                if email in employees_by_email:
                    emp = employees_by_email[email]
                    if emp["name"] != f_name:
                        issues.append({"type": "姓名不一致", "gitlab_name": f_name, "mdm_name": emp["name"], "email": email})
                    else:
                        matched += 1
                else:
                    unmatched += 1
                    issues.append({"type": "未匹配主数据", "gitlab_name": f_name, "gitlab_email": email})

        self.stdout.write(f"✅ 匹配成功: {matched} 条 | ⚠️ 问题记录: {len(issues)} 条 | ❌ 未匹配: {unmatched} 条\n")
        for idx, issue in enumerate(issues[:10], 1):
            self.stdout.write(
                f"  {idx}. [{issue['type']}] {issue.get('gitlab_name')} - {issue.get('mdm_name', '')} ({issue.get('email', issue.get('gitlab_email'))})\n"
            )

    def _check_zentao_alignment(self, csv_path, employees_by_email, employees_by_id):
        self.stdout.write("\n========== 禅道身份对齐检查 ==========\n")
        if not csv_path.exists():
            self.stdout.write(f"⚠️ 禅道用户文件不存在: {csv_path}\n")
            return

        issues = []
        matched = 0

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                emp_id = row.get("工号", "").strip()
                name = row.get("姓名", "").strip()
                email = row.get("邮箱", "").strip().lower()

                if not emp_id and not email:
                    continue

                if emp_id and emp_id in employees_by_id:
                    mdm = employees_by_id[emp_id]
                    if email and mdm["email"] and email != mdm["email"]:
                        issues.append({"type": "邮箱不一致", "name": name, "zentao_email": email, "mdm_email": mdm["email"]})
                    elif mdm["name"] != name:
                        issues.append({"type": "姓名不一致", "zentao_name": name, "mdm_name": mdm["name"]})
                    else:
                        matched += 1
                elif email and email in employees_by_email:
                    matched += 1
                else:
                    issues.append({"type": "未匹配主数据", "name": name, "email": email})

        self.stdout.write(f"✅ 匹配成功: {matched} 条 | ⚠️ 问题记录: {len(issues)} 条\n")
        for idx, issue in enumerate(issues[:10], 1):
            self.stdout.write(f"  {idx}. [{issue['type']}] {issue.get('name', issue.get('zentao_name'))}\n")
