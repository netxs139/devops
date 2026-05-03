import pytest

from devops_collector.plugins.gitlab.models import GitLabPipeline, GitLabProject
from devops_collector.plugins.gitlab.worker import GitLabWorker


@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    return client


def test_pipeline_and_job_sync_logic(db_session, mock_client):
    """测试流水线与 Job 的增量同步逻辑 (含 FinOps 指标提取)"""
    # 1. 初始化 Worker
    worker = GitLabWorker(db_session, client=mock_client)

    # 2. 准备项目数据
    from devops_collector.plugins.gitlab.models import GitLabCommit

    project = GitLabProject(id=1, name="test-project", path_with_namespace="group/test")
    commit = GitLabCommit(id="sha123", project_id=1, message="fix", author_name="admin", author_email="admin@test.com")
    db_session.add(project)
    db_session.add(commit)
    db_session.flush()

    # 3. 模拟 API 返回 (Pipeline 列表)
    mock_client.get_project_pipelines.return_value = iter(
        [{"id": 100, "status": "success", "ref": "main", "sha": "sha123", "created_at": "2024-05-01T10:00:00Z", "updated_at": "2024-05-01T10:10:00Z"}]
    )

    # 4. 模拟 API 返回 (Pipeline 详情 - 包含 duration 等精简 API 不含的字段)
    mock_client.get_pipeline_details.return_value = {
        "id": 100,
        "duration": 600,
        "queued_duration": 10,
        "started_at": "2024-05-01T10:00:05Z",
        "finished_at": "2024-05-01T10:10:05Z",
        "web_url": "https://gitlab.com/pipeline/100",
        "user": {"id": 1, "username": "admin"},
    }

    # 5. 模拟 API 返回 (Jobs 列表)
    mock_client.get_pipeline_jobs.return_value = iter(
        [
            {
                "id": 201,
                "name": "rspec",
                "stage": "test",
                "status": "success",
                "duration": 300.0,
                "queued_duration": 5.0,
                "created_at": "2024-05-01T10:00:05Z",
                "started_at": "2024-05-01T10:00:10Z",
                "finished_at": "2024-05-01T10:05:10Z",
                "runner": {"id": 50, "description": "shared-runner", "is_shared": True},
            }
        ]
    )

    # 6. 执行同步
    worker._sync_pipelines(project)
    db_session.flush()

    # 7. 断言数据持久化
    pipeline = db_session.query(GitLabPipeline).filter_by(id=100).first()
    assert pipeline is not None
    assert pipeline.duration == 600
    assert pipeline.queued_duration == 10
    assert pipeline.web_url == "https://gitlab.com/pipeline/100"

    # 断言 Job 持久化
    assert len(pipeline.jobs) == 1
    job = pipeline.jobs[0]
    assert job.name == "rspec"
    assert job.duration == 300.0
    assert job.runner_type == "shared"
