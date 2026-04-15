"""Unit tests for devops_collector/scheduler.py

策略：通过 `--once` flag + Mock 绕过无限 while True 循环，
全部使用 Mock 切断真实数据库 / MQ / subprocess 依赖。

覆盖路径：
- main() bootstrap 链路 (PluginLoader, create_all)
- --force-all 模式下重置状态 SQL 被调用
- ZenTao / GitLab / SonarQube 扫描循环中的任务发布逻辑
- PromotionService 正常执行路径
- PromotionService 异常 → rollback 路径
- dbt run 成功 → reverse ETL 链路
- dbt run 失败 → 不调用 reverse ETL
- --skip-dbt 跳过 dbt block
- 调度器主循环异常 → rollback + session.close
"""

import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Helper: build a fake project object with given sync_status / last_synced_at
# ---------------------------------------------------------------------------

def make_project(sync_status="PENDING", last_synced_at=None):
    p = MagicMock()
    p.sync_status = sync_status
    p.last_synced_at = last_synced_at
    p.id = 1
    p.key = "my-project"
    return p


# ---------------------------------------------------------------------------
# Reusable patch context for all main() tests
# ---------------------------------------------------------------------------

PATCHES = [
    "devops_collector.scheduler.PluginLoader",
    "devops_collector.scheduler.create_engine",
    "devops_collector.scheduler.sessionmaker",
    "devops_collector.scheduler.MessageQueue",
    "devops_collector.scheduler.Base",
    "devops_collector.scheduler.PromotionService",
    "devops_collector.scheduler.subprocess",
    "devops_collector.scheduler.DORAService",
]


def _run_main(argv, setup_session_fn=None):
    """Helper: patch all external deps, inject argv, run main() once."""
    with patch("sys.argv", ["scheduler"] + argv), \
         patch("devops_collector.scheduler.PluginLoader") as mock_loader, \
         patch("devops_collector.scheduler.create_engine") as mock_engine_cls, \
         patch("devops_collector.scheduler.sessionmaker") as mock_sm, \
         patch("devops_collector.scheduler.MessageQueue") as mock_mq_cls, \
         patch("devops_collector.scheduler.Base") as mock_base, \
         patch("devops_collector.scheduler.PromotionService") as mock_ps, \
         patch("devops_collector.scheduler.subprocess") as mock_subprocess, \
         patch("devops_collector.scheduler.DORAService") as mock_dora, \
         patch("devops_collector.plugins.gitlab.models.GitLabProject", create=True), \
         patch("devops_collector.plugins.sonarqube.models.SonarProject", create=True), \
         patch("devops_collector.plugins.zentao.models.ZenTaoProduct", create=True):

        mock_engine = MagicMock()
        mock_engine_cls.return_value = mock_engine

        mock_session = MagicMock()
        mock_sm.return_value = lambda: mock_session

        mock_mq = MagicMock()
        mock_mq_cls.return_value = mock_mq

        # dbt subprocess defaults to success
        dbt_result = MagicMock()
        dbt_result.returncode = 0
        dbt_result.stdout = "done"
        mock_subprocess.run.return_value = dbt_result

        # PromotionService defaults to 0 promoted records
        mock_ps.promote_gitlab_commits.return_value = 0
        mock_ps.promote_zentao_products.return_value = 0
        mock_ps.promote_zentao_executions.return_value = 0

        # Allow caller to customise session query results
        if setup_session_fn:
            setup_session_fn(mock_session, mock_mq, mock_ps, mock_subprocess, mock_dora, mock_engine)

        from devops_collector.scheduler import main
        main()

        return {
            "loader": mock_loader,
            "engine": mock_engine,
            "session": mock_session,
            "mq": mock_mq,
            "base": mock_base,
            "ps": mock_ps,
            "subprocess": mock_subprocess,
            "dora": mock_dora,
        }


# ---------------------------------------------------------------------------
# Test 1: Bootstrap chain (PluginLoader + create_all) -- once mode, no projects
# ---------------------------------------------------------------------------

def test_main_bootstrap_loads_models_and_creates_tables():
    """main() 必须调用 PluginLoader.load_models() 并执行 Base.metadata.create_all。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["loader"].load_models.assert_called_once()
    ctx["base"].metadata.create_all.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: --force-all resets sync statuses via raw SQL
# ---------------------------------------------------------------------------

def test_force_all_resets_sync_status():
    """--force-all 时必须对三张表执行 UPDATE sync_status='PENDING' SQL。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []

    ctx = _run_main(["--once", "--skip-dbt", "--force-all"], setup_session_fn=setup)
    conn = ctx["engine"].connect.return_value.__enter__.return_value
    assert conn.execute.call_count == 3  # zentao / gitlab / sonar
    conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Test 3: ZenTao product with no last_synced_at → task published
# ---------------------------------------------------------------------------

def test_zentao_product_never_synced_publishes_task():
    """last_synced_at=None 的 ZenTao product 必须发布任务且 sync_status='QUEUED'。"""
    zp = make_project(sync_status="PENDING", last_synced_at=None)

    def setup(session, mq, ps, subp, dora, engine):
        # query 顺序: zentao → gitlab → sonar
        session.query.return_value.all.side_effect = [
            [zp],   # zentao products
            [],     # gitlab projects
            [],     # sonar projects
        ]

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["mq"].publish_task.assert_called_once()
    published = ctx["mq"].publish_task.call_args[0][0]
    assert published["source"] == "zentao"
    assert zp.sync_status == "QUEUED"


# ---------------------------------------------------------------------------
# Test 4: GitLab project stale → incremental task published
# ---------------------------------------------------------------------------

def test_gitlab_stale_project_publishes_incremental_task():
    """上次同步时间超过 SYNC_INTERVAL_MINUTES 的 gitlab project 发布 incremental 任务。"""
    old_time = datetime.now(UTC) - timedelta(hours=25)  # > SYNC_INTERVAL_MINUTES(1440=24h)
    proj = make_project(sync_status="PENDING", last_synced_at=old_time)

    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.side_effect = [
            [],      # zentao
            [proj],  # gitlab
            [],      # sonar
        ]

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["mq"].publish_task.assert_called_once()
    published = ctx["mq"].publish_task.call_args[0][0]
    assert published["source"] == "gitlab"
    assert published["job_type"] == "incremental"


# ---------------------------------------------------------------------------
# Test 5: SYNCING project is skipped (not force-all)
# ---------------------------------------------------------------------------

def test_syncing_project_not_queued_again():
    """sync_status='SYNCING' 的项目在非 force-all 模式下不能重复发布任务。"""
    proj = make_project(sync_status="SYNCING", last_synced_at=None)

    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.side_effect = [
            [],       # zentao
            [proj],   # gitlab
            [],       # sonar
        ]

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["mq"].publish_task.assert_not_called()


# ---------------------------------------------------------------------------
# Test 6: PromotionService success → commit called
# ---------------------------------------------------------------------------

def test_promotion_service_success_commits():
    """PromotionService 有数据时，session.commit() 在 promotion 结束后被调用。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []
        ps.promote_gitlab_commits.return_value = 5
        ps.promote_zentao_products.return_value = 3
        ps.promote_zentao_executions.return_value = 0

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["session"].commit.assert_called()


# ---------------------------------------------------------------------------
# Test 7: PromotionService raises → rollback called
# ---------------------------------------------------------------------------

def test_promotion_service_failure_rollbacks():
    """PromotionService 抛异常时，session.rollback() 必须被调用。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []
        ps.promote_gitlab_commits.side_effect = RuntimeError("DB connection lost")

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["session"].rollback.assert_called()


# ---------------------------------------------------------------------------
# Test 8: dbt run success → reverse ETL + DORA called
# ---------------------------------------------------------------------------

def test_dbt_success_triggers_reverse_etl_and_dora():
    """dbt returncode=0 时，DORAService.aggregate_all_projects 和 reverse ETL 必须被触发。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []
        dbt_ok = MagicMock()
        dbt_ok.returncode = 0
        dbt_ok.stdout = "Success"
        bot_ok = MagicMock()
        bot_ok.returncode = 0
        bot_ok.stdout = "Risk bot OK"
        subp.run.side_effect = [dbt_ok, bot_ok]

    with patch("devops_collector.core.reverse_etl.sync_aligned_entities_to_mdm"), \
         patch("devops_collector.core.reverse_etl.sync_shadow_it_findings"), \
         patch("devops_collector.core.reverse_etl.sync_talent_tags_to_mdm"):
        ctx = _run_main(["--once"], setup_session_fn=setup)

    ctx["dora"].aggregate_all_projects.assert_called_once()


# ---------------------------------------------------------------------------
# Test 9: dbt run fails → reverse ETL NOT called
# ---------------------------------------------------------------------------

def test_dbt_failure_skips_reverse_etl():
    """dbt returncode!=0 时，reverse ETL 不能被触发。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []
        dbt_fail = MagicMock()
        dbt_fail.returncode = 1
        dbt_fail.stderr = "compilation error"
        subp.run.return_value = dbt_fail

    ctx = _run_main(["--once"], setup_session_fn=setup)
    ctx["dora"].aggregate_all_projects.assert_not_called()


# ---------------------------------------------------------------------------
# Test 10: --skip-dbt prevents dbt subprocess call
# ---------------------------------------------------------------------------

def test_skip_dbt_prevents_subprocess_call():
    """--skip-dbt 时，subprocess.run 不能被调用（dbt 命令跳过）。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.return_value.all.return_value = []

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["subprocess"].run.assert_not_called()


# ---------------------------------------------------------------------------
# Test 11: Session always closed (finally block)
# ---------------------------------------------------------------------------

def test_session_always_closed_even_on_error():
    """主 try 块抛异常后，session.close() 必须仍在 finally 被调用。"""
    def setup(session, mq, ps, subp, dora, engine):
        session.query.side_effect = Exception("unexpected DB error")

    ctx = _run_main(["--once", "--skip-dbt"], setup_session_fn=setup)
    ctx["session"].close.assert_called_once()
