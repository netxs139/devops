from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from devops_collector.plugins.gitlab.models import GitLabMergeRequest, GitLabMergeRequestStateTransition, GitLabProject
from devops_collector.plugins.gitlab.worker import GitLabWorker


@pytest.fixture
def worker(db_session):
    client = MagicMock()
    worker = GitLabWorker(db_session, client=client, correlation_id="test-vsm")
    # Mock UserResolver to prevent DB interaction with Mocks
    worker.user_resolver = MagicMock()
    worker.user_resolver.resolve.return_value = None
    return worker


def test_mr_vsm_metrics_calculation(worker, db_session):
    # 1. Mock Project
    project = GitLabProject(id=1, name="VSM Project")
    db_session.add(project)
    db_session.commit()

    # 2. Mock MR Data (Initial Draft)
    t0 = datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(hours=2)  # Marked as ready
    t2 = t1 + timedelta(hours=1)  # First response
    t3 = t2 + timedelta(hours=5)  # Merged

    mr_data = {
        "id": 101,
        "iid": 1,
        "project_id": 1,
        "title": "VSM MR",
        "state": "merged",
        "draft": False,  # Current state is not draft
        "created_at": t0.isoformat(),
        "updated_at": t3.isoformat(),
        "merged_at": t3.isoformat(),
        "author": {"id": 1, "username": "dev1"},
    }

    # Mock Notes (System note for ready, Human note for response)
    notes = [
        {"id": 1, "system": True, "body": "marked as ready", "created_at": t1.isoformat()},
        {"id": 2, "system": False, "body": "Looks good!", "created_at": t2.isoformat()},
    ]
    worker.client.get_mr_notes.return_value = notes

    # Mock State Events
    state_events = [{"state": "opened", "created_at": t0.isoformat()}, {"state": "merged", "created_at": t3.isoformat()}]
    worker.client.get_merge_request_state_events.return_value = state_events
    worker.client.get_mr_approvals.return_value = {"approved_by": []}
    worker.client.get_mr_pipelines.return_value = []

    # 3. Run Sync
    # Manually trigger the mixin logic for this MR
    worker._transform_mrs_batch(project, [mr_data])
    db_session.flush()

    # 4. Verify
    mr = db_session.query(GitLabMergeRequest).filter_by(id=101).first()
    assert mr is not None

    # Helper to compare datetimes regardless of tzinfo
    def assert_dt_equal(dt1, dt2):
        if dt1 is None or dt2 is None:
            assert dt1 == dt2
            return
        d1 = dt1.replace(tzinfo=None)
        d2 = dt2.replace(tzinfo=None)
        assert d1 == d2

    # Verify VSM Dates
    assert_dt_equal(mr.draft_at, t0)
    assert_dt_equal(mr.ready_at, t1)
    assert_dt_equal(mr.first_response_at, t2)

    # Verify Durations
    assert mr.draft_duration == 2 * 3600  # 2 hours
    assert mr.wait_time_to_review == 1 * 3600  # 1 hour

    # Verify Transitions
    transitions = db_session.query(GitLabMergeRequestStateTransition).filter_by(mr_id=mr.id).all()
    assert len(transitions) >= 1
    # Check merged transition duration
    merged_trans = [t for t in transitions if t.to_state == "merged"][0]
    assert merged_trans.from_state == "opened"
    assert merged_trans.duration_hours == 8.0  # Total time from t0 to t3
