"""多渠道风险预警推送命令 (Multi-channel Risk Bot)。

从数据库风险宽表中获取异常记录，并推送到企业微信、飞书、钉钉。
"""

from sqlalchemy import text

from devops_collector.config import settings
from devops_collector.core.management import BaseCommand
from devops_collector.services.notifiers import DingTalkBot, FeishuBot, WeComBot


class Command(BaseCommand):
    help = "风险预警推送：扫描数据库风险视图并发送 IM 卡片告警"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="仅打印告警内容，不执行实际推送")

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        bots = []
        if settings.notifiers.wecom_webhook:
            bots.append(WeComBot(settings.notifiers.wecom_webhook))
        if settings.notifiers.feishu_webhook:
            bots.append(FeishuBot(settings.notifiers.feishu_webhook))
        if settings.notifiers.dingtalk_webhook:
            bots.append(DingTalkBot(settings.notifiers.dingtalk_webhook))

        if not bots and not dry_run:
            self.stderr.write("❌ 未配置任何通知渠道 Webhook (WeCom/Feishu/DingTalk)。\n")
            return False

        try:
            self.stdout.write("正在检索风险异常数据...\n")

            # 1. 业务风险查询
            query = text("SELECT project_name, risk_type, severity, description, owner FROM view_pmo_risk_anomalies")
            risks = self.session.execute(query).fetchall()

            risk_list = []
            for r in risks:
                risk_list.append(
                    {
                        "title": f"【风险预警】{r.project_name}",
                        "details": [{"风险类型": r.risk_type}, {"异常描述": r.description}, {"责任人": r.owner or "未指定"}],
                        "level": r.severity,
                    }
                )

            # 2. 系统数据质量风险
            try:
                dq_query = text("SELECT source_system, failure_count, success_rate_pct FROM rpt_system_data_quality WHERE (100 - success_rate_pct) > 10.0")
                dq_risks = self.session.execute(dq_query).fetchall()
                for dq in dq_risks:
                    risk_list.append(
                        {
                            "title": f"【系统质量告警】{dq.source_system}",
                            "details": [
                                {"风险类型": "SYS_QUALITY"},
                                {"异常描述": f"数据同步失败率超标: {100 - dq.success_rate_pct:.1f}%"},
                                {"失败次数": str(dq.failure_count)},
                            ],
                            "level": "CRITICAL",
                        }
                    )
            except Exception as e:
                self.stdout.write(f"WARN: 无法检查系统数据质量风险 (可能视图不存在): {e}\n")

            if not risk_list:
                self.stdout.write("✅ 未检测到任何风险异常。\n")
                return True

            self.stdout.write(f"共发现 {len(risk_list)} 条风险记录，准备广播...\n")

            for risk in risk_list:
                if dry_run:
                    self.stdout.write(f"[Dry Run] {risk['title']} | {risk['level']} | {risk['details']}\n")
                else:
                    for bot in bots:
                        bot.send_risk_card(risk["title"], risk["details"], level=risk["level"])

            self.stdout.write(f"✅ 广播完成 (渠道数: {len(bots)})。\n")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 风险推送失败: {e}\n")
            return False
