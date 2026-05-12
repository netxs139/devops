"""自动发现外部系统资产（GitLab / SonarQube / ZenTao）。"""

from devops_collector.config import settings
from devops_collector.core.management import BaseCommand
from devops_collector.plugins.gitlab.gitlab_client import GitLabClient
from devops_collector.plugins.gitlab.models import GitLabProject as Project
from devops_collector.plugins.sonarqube.client import SonarQubeClient
from devops_collector.plugins.sonarqube.models import SonarProject
from devops_collector.plugins.zentao.client import ZenTaoClient
from devops_collector.plugins.zentao.models import ZenTaoProduct


class Command(BaseCommand):
    help = "连接外部系统执行资产自动发现（GitLab / SonarQube / ZenTao）"

    def add_arguments(self, parser):
        parser.add_argument("--skip-gitlab", action="store_true", help="跳过 GitLab 发现")
        parser.add_argument("--skip-sonar", action="store_true", help="跳过 SonarQube 发现")
        parser.add_argument("--skip-zentao", action="store_true", help="跳过禅道发现")

    def handle(self, *args, **options):
        try:
            if not options.get("skip_gitlab"):
                self._discover_gitlab()
            if not options.get("skip_sonar"):
                self._discover_sonarqube()
            if not options.get("skip_zentao"):
                self._discover_zentao()
            self.session.flush()
            self.stdout.write("✅ 自动化发现任务执行完成。\n")
            return True
        except Exception as e:
            self.stderr.write(f"❌ 发现任务失败: {e}\n")
            return False

    def _discover_gitlab(self) -> None:
        if not settings.gitlab.url or not settings.gitlab.private_token:
            self.stdout.write("WARN: GitLab 配置缺失，跳过发现。\n")
            return

        self.stdout.write(f"正在连接 GitLab: {settings.gitlab.url}...\n")
        client = GitLabClient(settings.gitlab.url, settings.gitlab.private_token, verify_ssl=settings.gitlab.verify_ssl)
        if not client.test_connection():
            self.stderr.write("❌ 无法连接 GitLab，请检查配置。\n")
            return

        page = 1
        total = 0
        while True:
            try:
                response = client._get("projects", params={"page": page, "per_page": 100})
                projects_data = response.json()
                if not projects_data:
                    break
                for p_data in projects_data:
                    pid = p_data["id"]
                    existing = self.session.query(Project).filter_by(id=pid).first()
                    if not existing:
                        self.session.add(
                            Project(
                                id=pid,
                                name=p_data.get("name"),
                                path_with_namespace=p_data.get("path_with_namespace"),
                                description=p_data.get("description"),
                                sync_status="PENDING",
                            )
                        )
                    else:
                        existing.name = p_data.get("name")
                        existing.path_with_namespace = p_data.get("path_with_namespace")
                    total += 1
                self.session.flush()
                self.stdout.write(f"  GitLab 第 {page} 页已处理...\n")
                page += 1
            except Exception as e:
                self.stderr.write(f"GitLab 发现失败（第{page}页）: {e}\n")
                break
        self.stdout.write(f"  GitLab 发现完成，共处理 {total} 个项目。\n")

    def _discover_sonarqube(self) -> None:
        if not settings.sonarqube.url or not settings.sonarqube.token:
            self.stdout.write("WARN: SonarQube 配置缺失，跳过发现。\n")
            return

        self.stdout.write(f"正在连接 SonarQube: {settings.sonarqube.url}...\n")
        client = SonarQubeClient(settings.sonarqube.url, settings.sonarqube.token)
        if not client.test_connection():
            self.stderr.write("❌ 无法连接 SonarQube，请检查配置。\n")
            return

        try:
            projects = client.get_all_projects()
            for p_data in projects:
                key = p_data["key"]
                existing = self.session.query(SonarProject).filter_by(key=key).first()
                if not existing:
                    self.session.add(SonarProject(key=key, name=p_data.get("name"), qualifier=p_data.get("qualifier"), sync_status="PENDING"))
                else:
                    existing.name = p_data.get("name")
            self.session.flush()
            self.stdout.write(f"  SonarQube 发现完成，共处理 {len(projects)} 个项目。\n")
        except Exception as e:
            self.stderr.write(f"SonarQube 发现失败: {e}\n")

    def _discover_zentao(self) -> None:
        if not settings.zentao.url or not settings.zentao.account:
            self.stdout.write("WARN: ZenTao 配置缺失，跳过发现。\n")
            return

        self.stdout.write(f"正在连接禅道: {settings.zentao.url}...\n")
        client = ZenTaoClient(settings.zentao.url, settings.zentao.token, settings.zentao.account, settings.zentao.password)
        try:
            if not client.test_connection():
                self.stderr.write("❌ 无法连接禅道，请检查配置。\n")
                return

            products = client.get_products()
            for p_data in products:
                pid = p_data.get("id")
                if not pid:
                    continue
                existing = self.session.query(ZenTaoProduct).filter_by(id=pid).first()
                if not existing:
                    self.session.add(
                        ZenTaoProduct(
                            id=pid,
                            name=p_data.get("name"),
                            code=p_data.get("code"),
                            status=p_data.get("status", "normal"),
                            sync_status="PENDING",
                        )
                    )
                else:
                    existing.name = p_data.get("name")
                    existing.status = p_data.get("status", "normal")
            self.session.flush()
            self.stdout.write(f"  禅道发现完成，共处理 {len(products)} 个产品。\n")
        except Exception as e:
            self.stderr.write(f"禅道发现失败: {e}\n")
