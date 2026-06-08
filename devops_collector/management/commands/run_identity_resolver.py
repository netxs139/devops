"""身份自动治理引擎 (Identity Resolver Engine) 命令。.

扫描 mdm_identity_mappings 表中尚未验证或自动生成的身份，
通过模糊匹配与启发式规则计算置信度，并将外部帐号对齐到 HR 金数据用户。

业务逻辑已下沉至 devops_collector.services.identity_resolver.IdentityResolver。
"""

from devops_collector.core.management import BaseCommand
from devops_collector.services.identity_resolver import IdentityResolver


class Command(BaseCommand):
    """身份自动治理引擎命令。."""

    help = "身份自动治理引擎：将外部帐号对齐到 HR 主数据用户"

    def add_arguments(self, parser):
        """添加命令行参数。."""
        parser.add_argument("--apply", action="store_true", help="执行实际更新（默认仅为 Dry Run）")
        parser.add_argument("--min-score", type=float, default=0.6, help="最低匹配置信度阈值 (默认: 0.6)")

    def handle(self, *args, **options):
        """执行主处理逻辑。."""
        apply_changes = options.get("apply", False)
        min_score = options.get("min_score", 0.6)

        if not apply_changes:
            self.stdout.write("[Dry Run] 正在以预览模式运行。使用 --apply 保存更改。\n")

        service = IdentityResolver(self.session, min_score=min_score)
        result = service.run(dry_run=not apply_changes)

        if apply_changes:
            self.stdout.write(f"✅ 治理完成，已更新 {result['updated']} 条映射记录。\n")
        else:
            self.stdout.write("💡 [Dry Run] 预览结束。如需应用，请执行: uv run scripts/cli.py run identity_resolver --apply\n")
            self.stdout.write(f"   预计会更新 {result['updated']} 条记录。\n")

        return True
