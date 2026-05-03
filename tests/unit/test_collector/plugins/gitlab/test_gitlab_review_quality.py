from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from devops_collector.plugins.gitlab.models import GitLabMergeRequest, GitLabProject
from devops_collector.plugins.gitlab.worker import GitLabWorker


@pytest.fixture
def worker(db_session):
    client = MagicMock()
    worker = GitLabWorker(db_session, client=client, correlation_id="test-review-quality")
    worker.user_resolver = MagicMock()
    worker.user_resolver.resolve.return_value = None
    return worker


def test_effective_comment_calculation(worker, db_session):
    # Setup
    project = GitLabProject(id=1, name="Quality Project")
    db_session.add(project)
    db_session.commit()

    t0 = datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)  # Created/Ready
    t1 = t0 + timedelta(minutes=10)  # Human Comment 1
    t2 = t1 + timedelta(minutes=20)  # System Note: Added commit (Response to Comment 1)
    t3 = t2 + timedelta(minutes=10)  # Human Comment 2
    # No more commits after t3

    mr_data = {
        "id": 201,
        "iid": 1,
        "project_id": 1,
        "title": "Quality MR",
        "state": "merged",
        "created_at": t0.isoformat(),
        "updated_at": t3.isoformat(),
        "merged_at": t3.isoformat(),
        "author": {"id": 1, "username": "dev1"},
    }

    notes = [
        {"id": 1, "system": False, "body": "Fix this", "created_at": t1.isoformat()},
        {"id": 2, "system": True, "body": "added 1 commit", "created_at": t2.isoformat()},
        {"id": 3, "system": False, "body": "Thanks!", "created_at": t3.isoformat()},
    ]
    worker.client.get_mr_notes.return_value = notes
    worker.client.get_mr_approvals.return_value = {"approved_by": []}
    worker.client.get_merge_request_state_events.return_value = []
    worker.client.get_mr_pipelines.return_value = []

    # Run
    worker._transform_mrs_batch(project, [mr_data])
    db_session.flush()

    # Verify
    mr = db_session.query(GitLabMergeRequest).filter_by(id=201).first()
    assert mr.human_comment_count == 2
    # Only the first comment (id=1) is effective because it's followed by a commit (id=2)
    assert mr.effective_comment_count == 1


def test_rubber_stamp_detection(worker, db_session):
    # Setup
    project = GitLabProject(id=2, name="Rubber Project")
    db_session.add(project)
    db_session.commit()

    t0 = datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)  # Ready
    t1 = t0 + timedelta(minutes=2)  # Approved (Fast!)

    mr_data = {
        "id": 202,
        "iid": 2,
        "project_id": 2,
        "title": "Quick MR",
        "state": "merged",
        "created_at": t0.isoformat(),
        "updated_at": t1.isoformat(),
        "merged_at": t1.isoformat(),
        "author": {"id": 1, "username": "dev1"},
    }

    notes = [
        {"id": 10, "system": True, "body": "approved this merge request", "created_at": t1.isoformat()},
    ]
    worker.client.get_mr_notes.return_value = notes
    worker.client.get_mr_approvals.return_value = {"approved_by": [{"id": 2}]}
    worker.client.get_merge_request_state_events.return_value = []
    worker.client.get_mr_pipelines.return_value = []

    # Run
    worker._transform_mrs_batch(project, [mr_data])
    db_session.flush()

    # Verify
    mr = db_session.query(GitLabMergeRequest).filter_by(id=202).first()
    assert mr.rubber_stamp is True
    assert mr.human_comment_count == 0


def test_deep_review_not_rubber_stamp(worker, db_session):
    # Setup
    project = GitLabProject(id=3, name="Deep Project")
    db_session.add(project)
    db_session.commit()

    t0 = datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)  # Ready
    t1 = t0 + timedelta(minutes=60)  # Approved (Deep!)

    mr_data = {
        "id": 203,
        "iid": 3,
        "project_id": 3,
        "title": "Deep MR",
        "state": "merged",
        "created_at": t0.isoformat(),
        "updated_at": t1.isoformat(),
        "merged_at": t1.isoformat(),
        "author": {"id": 1, "username": "dev1"},
    }

    notes = [
        {"id": 11, "system": True, "body": "approved this merge request", "created_at": t1.isoformat()},
    ]
    worker.client.get_mr_notes.return_value = notes
    worker.client.get_mr_approvals.return_value = {"approved_by": [{"id": 2}]}
    worker.client.get_merge_request_state_events.return_value = []
    worker.client.get_mr_pipelines.return_value = []

    # Run
    worker._transform_mrs_batch(project, [mr_data])
    db_session.flush()

    # Verify
    mr = db_session.query(GitLabMergeRequest).filter_by(id=203).first()
    assert mr.rubber_stamp is False  # Because delay (60m) > 5m
