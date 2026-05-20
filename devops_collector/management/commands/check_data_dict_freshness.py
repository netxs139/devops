from devops_collector.core.management import BaseCommand
from devops_collector.services.diagnostic_service import DiagnosticService


class Command(BaseCommand):
    help = "数据字典新鲜度检测脚本：检测模型变更后数据字典是否已更新。"

    def handle(self):
        self.stdout.write("Checking Data Dictionary freshness (via Service)...\n")

        service = DiagnosticService()

        modified_files = service.get_git_modified_files()
        models_changed = service.check_model_files_modified(modified_files)
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

        age = service.get_data_dict_age()
        if age > 7:
            self.stdout.write(f"Note: Data dictionary is {age} days old. Consider refreshing it.\n")

        self.stdout.write("✅ Data Dictionary check passed.\n")
        return True
