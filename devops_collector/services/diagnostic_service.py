"""诊断服务：处理系统状态检查、对齐检查等操作。"""

import csv
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


class DiagnosticService:
    """诊断相关服务。"""

    def get_git_modified_files(self) -> set[str]:
        """获取 Git 暂存区的文件。"""
        try:
            result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return set(result.stdout.strip().split("\n"))
        except Exception:
            pass
        return set()

    def check_model_files_modified(self, modified_files: set[str]) -> bool:
        """检查是否有模型文件变更。"""
        patterns = ["devops_collector/models/", "devops_collector/plugins/"]
        for f in modified_files:
            if any(p in f for p in patterns) and f.endswith(".py"):
                return True
        return False

    def get_data_dict_age(self) -> int:
        """获取数据字典的新鲜度（天数）。"""
        path = Path("docs/api/DATA_DICTIONARY.md")
        if not path.exists():
            return -1
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime).days

    def load_employees(self, csv_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
        """加载员工主数据。"""
        employees_by_email: dict[str, Any] = {}
        employees_by_id: dict[str, Any] = {}
        if not csv_path.exists():
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

    def check_gitlab_alignment(self, csv_path: Path, employees_by_email: dict[str, Any]) -> dict[str, Any]:
        """检查 GitLab 身份对齐情况。"""
        result: dict[str, Any] = {"matched": 0, "unmatched": 0, "issues": [], "exists": csv_path.exists()}
        if not result["exists"]:
            return result

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
                        result["issues"].append({"type": "姓名不一致", "gitlab_name": f_name, "mdm_name": emp["name"], "email": email})
                    else:
                        result["matched"] += 1
                else:
                    result["unmatched"] += 1
                    result["issues"].append({"type": "未匹配主数据", "gitlab_name": f_name, "gitlab_email": email})
        return result

    def check_zentao_alignment(self, csv_path: Path, employees_by_email: dict[str, Any], employees_by_id: dict[str, Any]) -> dict[str, Any]:
        """检查禅道身份对齐情况。"""
        result: dict[str, Any] = {"matched": 0, "unmatched": 0, "issues": [], "exists": csv_path.exists()}
        if not result["exists"]:
            return result

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
                        result["issues"].append({"type": "邮箱不一致", "name": name, "zentao_email": email, "mdm_email": mdm["email"]})
                    elif mdm["name"] != name:
                        result["issues"].append({"type": "姓名不一致", "zentao_name": name, "mdm_name": mdm["name"]})
                    else:
                        result["matched"] += 1
                elif email and email in employees_by_email:
                    result["matched"] += 1
                else:
                    result["issues"].append({"type": "未匹配主数据", "name": name, "email": email})
                    result["unmatched"] += 1
        return result
