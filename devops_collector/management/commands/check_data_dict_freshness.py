import subprocess
from datetime import datetime
from pathlib import Path

from devops_collector.core.management import BaseCommand


class Command(BaseCommand):
    help = "数据字典新鲜度检测脚本：检测模型变更后数据字典是否已更新。"

    def handle(self, *args, **options):
        self.stdout.write("Checking Data Dictionary freshness...\n")

        modified_files = self._get_git_modified_files()
        models_changed = self._check_model_files_modified(modified_files)
        dict_updated = "docs/api/DATA_DICTIONARY.md" in modified_files

        if models_changed and not dict_updated:
            self.stdout.write("\n" + "=" * 60 + "\n")
            self.stdout.write("WARNING: Model files changed but DATA_DICTIONARY.md not updated!\n")
            self.stdout.write("=" * 60 + "\n")
            self.stdout.write("\nThe following model-related files were modified:\n")
            for f in modified_files:
                if "models/" in f or "plugins/" in f:
                    self.stdout.write(f"  - {f}\n")
            self.stdout.write("\nPlease run: 'make docs' or 'just docs' to update.\n")
            return False

        age = self._get_data_dict_age()
        if age > 7:
            self.stdout.write(f"Note: Data dictionary is {age} days old. Consider refreshing it.\n")

        self.stdout.write("✅ Data Dictionary check passed.\n")
        return True

    def _get_git_modified_files(self) -> set:
        try:
            result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return set(result.stdout.strip().split("\n"))
        except Exception:
            pass
        return set()

    def _check_model_files_modified(self, modified_files: set) -> bool:
        patterns = ["devops_collector/models/", "devops_collector/plugins/"]
        for f in modified_files:
            if any(p in f for p in patterns) and f.endswith(".py"):
                return True
        return False

    def _get_data_dict_age(self) -> int:
        path = Path("docs/api/DATA_DICTIONARY.md")
        if not path.exists():
            return -1
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return (datetime.now() - mtime).days
