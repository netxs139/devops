import uuid
from datetime import UTC, datetime

from devops_collector.models.base_models import User
from devops_collector.plugins.gitlab.models import GitLabCommit, GitLabJob, GitLabPipeline, GitLabProject


def test_gitlab_pipeline_and_job_models(db_session):
    """测试 GitLab 流水线与算力消耗数据模型 (FinOps)"""
    # 1. 准备前置数据 (Project & User)
    project = GitLabProject(
        id=9999,
        name="test-finops",
        path_with_namespace="test/test-finops",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    user = User(global_user_id=uuid.uuid4(), username="devops_finops", is_current=True)
    commit = GitLabCommit(id="abc123def456", project_id=9999, short_id="abc123d", title="fix: performance", committed_date=datetime(2024, 5, 1, tzinfo=UTC))

    db_session.add_all([project, user, commit])
    db_session.flush()

    # 2. 创建 Pipeline
    pipeline = GitLabPipeline(
        id=8888,
        project_id=project.id,
        sha=commit.id,
        ref="main",
        status="success",
        source="merge_request_event",
        created_at=datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC),
        started_at=datetime(2024, 5, 1, 10, 0, 5, tzinfo=UTC),
        finished_at=datetime(2024, 5, 1, 10, 5, 5, tzinfo=UTC),
        duration=300,  # 算力运行 5 分钟
        queued_duration=5,  # 排队 5 秒
        coverage=85.5,
        user_id=user.global_user_id,
    )
    db_session.add(pipeline)
    db_session.flush()

    # 3. 创建 Job (算力颗粒)
    job1 = GitLabJob(
        id=7771,
        pipeline_id=pipeline.id,
        name="build:docker",
        stage="build",
        status="success",
        created_at=datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC),
        started_at=datetime(2024, 5, 1, 10, 0, 5, tzinfo=UTC),
        finished_at=datetime(2024, 5, 1, 10, 2, 5, tzinfo=UTC),
        duration=120.0,
        queued_duration=5.0,
        runner_id=101,
        runner_type="shared",
    )

    job2 = GitLabJob(
        id=7772,
        pipeline_id=pipeline.id,
        name="test:pytest",
        stage="test",
        status="success",
        created_at=datetime(2024, 5, 1, 10, 2, 5, tzinfo=UTC),
        started_at=datetime(2024, 5, 1, 10, 5, 5, tzinfo=UTC),  # 排队等了3分钟
        finished_at=datetime(2024, 5, 1, 10, 8, 5, tzinfo=UTC),
        duration=180.0,
        queued_duration=180.0,
        runner_id=202,
        runner_type="specific",
    )
    db_session.add_all([job1, job2])
    db_session.flush()

    # 4. 断言结构和外键联级
    fetched_pipeline = db_session.query(GitLabPipeline).filter_by(id=8888).first()
    assert fetched_pipeline is not None
    assert fetched_pipeline.duration == 300
    assert len(fetched_pipeline.jobs) == 2

    # 测试血缘映射
    assert fetched_pipeline.project.name == "test-finops"
    assert fetched_pipeline.commit.title == "fix: performance"
    assert fetched_pipeline.trigger_user.username == "devops_finops"

    # 算力指标提取
    assert fetched_pipeline.jobs[1].queued_duration == 180.0
    assert fetched_pipeline.jobs[1].runner_type == "specific"
