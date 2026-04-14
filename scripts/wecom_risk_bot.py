"""多渠道风险预警推送脚本 (Multi-channel Risk Bot)

该脚本定时运行，从数据库风险宽表中获取异常记录，并推送到企业微信、飞书、钉钉。
"""

import logging
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from devops_collector.config import settings
from devops_collector.core.notifiers import DingTalkBot, FeishuBot, WeComBot


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_risk_check():
    """执行风险检查并发送告警。"""
    db_uri = settings.database.uri
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    bots = []
    wecom_url = settings.notifiers.wecom_webhook
    if wecom_url:
        bots.append(WeComBot(wecom_url))
    feishu_url = settings.notifiers.feishu_webhook
    if feishu_url:
        bots.append(FeishuBot(feishu_url))
    dingtalk_url = settings.notifiers.dingtalk_webhook
    if dingtalk_url:
        bots.append(DingTalkBot(dingtalk_url))
    if not bots:
        logger.error("No notification channels configured.")
        return
    try:
        query = text("SELECT project_name, risk_type, severity, description, owner FROM view_pmo_risk_anomalies")
        risks = session.execute(query).fetchall()
        
        # 将查询结果转换为可变的列表，或者使用自定义对象
        class RiskObj:
            def __init__(self, project_name, risk_type, severity, description, owner):
                self.project_name = project_name
                self.risk_type = risk_type
                self.severity = severity
                self.description = description
                self.owner = owner

        # 映射原有的 Row 对象为 RiskObj
        risk_objects = [RiskObj(r.project_name, r.risk_type, r.severity, r.description, r.owner) for r in risks]

        # 增加 P2 指标：当质量失败率超标时自动触发 Webhook 告警
        try:
            dq_query = text("SELECT source_system, failure_count, success_rate_pct FROM rpt_system_data_quality WHERE (100 - success_rate_pct) > 10.0")
            dq_risks = session.execute(dq_query).fetchall()
            for dq in dq_risks:
                risk_objects.append(
                    RiskObj(
                        project_name=f"System Quality ({dq.source_system})",
                        risk_type="SYS_QUALITY",
                        severity="CRITICAL",
                        description=f"同步失败率超标: {100 - dq.success_rate_pct:.1f}% (失败 {dq.failure_count} 次)",
                        owner="DevOps Admin"
                    )
                )
        except Exception as e:
            logger.warning(f"Could not check system data quality risks: {e}")

        if not risk_objects:
            logger.info("No risks detected.")
            return

        for r in risk_objects:
            title = f"【风险预警】{r.project_name}"
            details = [{"风险类型": r.risk_type}, {"异常描述": r.description}, {"责任人": r.owner or "未指定"}]
            for bot in bots:
                bot.send_risk_card(title, details, level=r.severity)
        logger.info(f"Broadcasted {len(risk_objects)} risks to {len(bots)} channels.")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    run_risk_check()
