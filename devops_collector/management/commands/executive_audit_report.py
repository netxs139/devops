import logging
import os
from datetime import datetime

from sqlalchemy import text

from devops_collector.core.management import BaseCommand
from devops_collector.services.notifiers import WeComBot


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "研发体系月度效能与审计自动播报脚本 (Executive Audit & Efficiency Report)"

    def handle(self, *args, **options):
        report_date = datetime.now().strftime("%Y-%m-%d")

        # 初始化机器人
        bots = []
        wecom_webhook = os.getenv("WECOM_WEBHOOK")
        if wecom_webhook:
            bots.append(WeComBot(wecom_webhook))

        self.stdout.write("Starting Executive Audit Report Generation...\n")

        try:
            hotspots = self._fetch_hotspots()
            bus_risks = self._fetch_bus_factor_risks()
            fin_audit = self._fetch_financial_audit()
            talents = self._fetch_talent_spotlight()

            # 构建报告内容
            title = f"[Audit] 研发效能与风险月度审计报告 ({report_date})"
            details = []

            # 1. 技术风险
            hotspot_str = "\n".join([f"• {r.file_path.split('/')[-1]} (Risk: {r.risk_factor})" for r in hotspots])
            details.append({"技术热点风险": hotspot_str or "暂无显著红区"})

            # 2. 知识风险
            bus_risk_str = "\n".join([f"• {r.subsystem}: {r.subsystem_ownership_pct}% by user_id {str(r.author_user_id)[:8]}" for r in bus_risks])
            details.append({"知识孤岛预警": bus_risk_str or "知识分布健康"})

            # 3. 财务核算
            if fin_audit:
                fin_str = f"本周资本化率: {fin_audit.capitalization_rate}% | 状态: {fin_audit.audit_status}"
                details.append({"研发投入审计": fin_str})

            # 4. 人才星探
            talent_str = "\n".join([f"• {r.real_name} [{r.talent_archetype}] (Index: {r.talent_influence_index})" for r in talents])
            details.append({"关键影响力人才": talent_str or "数据计算中"})

            # 执行推送
            if not bots:
                self.stdout.write(f"\n=== {title} ===\n")
                for d in details:
                    for k, v in d.items():
                        self.stdout.write(f"\n[{k}]\n{v}\n")
                return True

            for bot in bots:
                try:
                    bot.send_risk_card(title, details, level="HIGH" if hotspots else "INFO")
                    self.stdout.write(f"Report sent to {bot.__class__.__name__}\n")
                except Exception as e:
                    logger.error(f"Failed to send report: {e}")

            return True
        except Exception as e:
            logger.error(f"Executive Audit failed: {e}")
            return False

    def _fetch_hotspots(self):
        query = text("""
            SELECT file_path, risk_factor, churn_90d
            FROM fct_code_hotspots
            WHERE risk_zone = 'RED_ZONE'
            ORDER BY risk_factor DESC
            LIMIT 5
        """)
        return self.session.execute(query).fetchall()

    def _fetch_bus_factor_risks(self):
        query = text("""
            SELECT subsystem, author_user_id, subsystem_ownership_pct, knowledge_risk_status
            FROM dws_subsystem_bus_factor
            WHERE knowledge_risk_status IN ('KNOWLEDGE_SILO', 'TRUCK_FACTOR_ONE')
            ORDER BY subsystem_ownership_pct DESC
            LIMIT 5
        """)
        return self.session.execute(query).fetchall()

    def _fetch_financial_audit(self):
        query = text("""
            SELECT audit_week, capitalization_rate, audit_status
            FROM fct_capitalization_audit
            ORDER BY audit_week DESC
            LIMIT 1
        """)
        return self.session.execute(query).fetchone()

    def _fetch_talent_spotlight(self):
        query = text("""
            SELECT real_name, talent_archetype, talent_influence_index
            FROM fct_talent_radar
            ORDER BY talent_influence_index DESC
            LIMIT 3
        """)
        return self.session.execute(query).fetchall()
