"""Unit tests for devops_portal/routers/webhook_router.py

覆盖路径：
- POST /webhooks/gitlab  — Issue Hook (test case label / requirement label)
- POST /webhooks/gitlab  — Pipeline Hook (status 更新写入 PIPELINE_STATUS)
- POST /webhooks/gitlab  — 未知 event_type (直接返回 accepted)
- POST /webhooks/gitlab  — JSON 解析异常返回 error
- POST /webhooks/sonarqube — 正常推送 → MQ publish
- POST /webhooks/sonarqube — 无 project_key → MQ 不发布
- POST /webhooks/sonarqube — 异常返回 error
- POST /webhooks/triggers/sonarqube — 正常触发 → MQ publish
- POST /webhooks/triggers/sonarqube — 缺少 project_key → error
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def webhook_client(client):
    """复用 conftest 中的 client fixture（已注入 DB override）。"""
    return client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def gitlab_issue_payload(event_type="Issue Hook", labels=None, old_labels=None,
                         iid=42, action="open", project_id=99):
    label_list = [{"title": l} for l in (labels or [])]
    old_label_list = [{"title": l} for l in (old_labels or [])]
    return {
        "headers": {"X-Gitlab-Event": event_type},
        "payload": {
            "object_attributes": {"iid": iid, "action": action},
            "labels": label_list,
            "changes": {"labels": {"previous": old_label_list}},
            "project": {"id": project_id},
        }
    }


# ---------------------------------------------------------------------------
# /webhooks/gitlab — Issue Hook: test case label
# ---------------------------------------------------------------------------

def test_gitlab_webhook_test_case_label(webhook_client):
    """type::test 标签的 Issue Hook 被接受，返回 accepted。"""
    data = gitlab_issue_payload(labels=["type::test"], action="open")
    response = webhook_client.post(
        "/webhooks/gitlab",
        json=data["payload"],
        headers={"X-Gitlab-Event": "Issue Hook"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# /webhooks/gitlab — Issue Hook: requirement label, review state change
# ---------------------------------------------------------------------------

def test_gitlab_webhook_requirement_review_state_change(webhook_client):
    """type::requirement 且 review-state 发生变化，触发通知逻辑返回 accepted。"""
    payload = {
        "object_attributes": {"iid": 10, "action": "update"},
        "labels": [{"title": "type::requirement"}, {"title": "review-state::approved"}],
        "changes": {"labels": {"previous": [{"title": "review-state::draft"}]}},
        "project": {"id": 1},
    }

    with patch("devops_portal.routers.webhook_router.get_requirement_author", return_value=None), \
         patch("devops_portal.routers.webhook_router.asyncio.create_task"):
        response = webhook_client.post(
            "/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Event": "Issue Hook"}
        )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# /webhooks/gitlab — Issue Hook: requirement, no review state change → no notify
# ---------------------------------------------------------------------------

def test_gitlab_webhook_requirement_no_state_change(webhook_client):
    """review-state 相同时，不触发通知，返回 accepted。"""
    payload = {
        "object_attributes": {"iid": 11, "action": "update"},
        "labels": [{"title": "type::requirement"}, {"title": "review-state::draft"}],
        "changes": {"labels": {"previous": [{"title": "review-state::draft"}]}},
        "project": {"id": 1},
    }

    with patch("devops_portal.routers.webhook_router.asyncio.create_task") as mock_task:
        response = webhook_client.post(
            "/webhooks/gitlab",
            json=payload,
            headers={"X-Gitlab-Event": "Issue Hook"}
        )

    assert response.status_code == 200
    mock_task.assert_not_called()


# ---------------------------------------------------------------------------
# /webhooks/gitlab — Pipeline Hook: status written to PIPELINE_STATUS
# ---------------------------------------------------------------------------

def test_gitlab_webhook_pipeline_hook_updates_state(webhook_client):
    """Pipeline Hook 写入全局 PIPELINE_STATUS 状态字典。"""
    from devops_portal.state import PIPELINE_STATUS

    payload = {
        "project": {"id": 55},
        "object_attributes": {
            "id": 999,
            "status": "success",
            "ref": "main",
            "sha": "abc123defgh",
            "finished_at": "2026-04-15T10:00:00Z",
        },
        "user_name": "dev_user",
    }

    response = webhook_client.post(
        "/webhooks/gitlab",
        json=payload,
        headers={"X-Gitlab-Event": "Pipeline Hook"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert PIPELINE_STATUS.get(55, {}).get("status") == "success"
    assert PIPELINE_STATUS[55]["sha"] == "abc123de"  # 截断为前 8 位


# ---------------------------------------------------------------------------
# /webhooks/gitlab — Pipeline Hook: failed status (pass-through, no error)
# ---------------------------------------------------------------------------

def test_gitlab_webhook_pipeline_failed_status(webhook_client):
    """Pipeline status=failed 被正确处理（当前 pass），不抛错。"""
    payload = {
        "project": {"id": 56},
        "object_attributes": {
            "id": 888,
            "status": "failed",
            "ref": "feature",
            "sha": "deadbeefcafe",
            "finished_at": None,
        },
        "user_name": "ci_bot",
    }

    response = webhook_client.post(
        "/webhooks/gitlab",
        json=payload,
        headers={"X-Gitlab-Event": "Pipeline Hook"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# /webhooks/gitlab — Unknown event type → just accepted
# ---------------------------------------------------------------------------

def test_gitlab_webhook_unknown_event(webhook_client):
    """未知 event_type 不做处理，直接返回 accepted。"""
    response = webhook_client.post(
        "/webhooks/gitlab",
        json={"foo": "bar"},
        headers={"X-Gitlab-Event": "Push Hook"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# /webhooks/sonarqube — Normal push with project_key → MQ publish
# ---------------------------------------------------------------------------

def test_sonarqube_webhook_publishes_task(webhook_client):
    """有 project_key 时 MQ.publish_task 被调用。"""
    payload = {"project": {"key": "my-service"}, "status": "SUCCESS"}

    with patch("devops_portal.routers.webhook_router.MessageQueue") as mock_mq_cls:
        mock_mq = MagicMock()
        mock_mq_cls.return_value = mock_mq

        response = webhook_client.post("/webhooks/sonarqube", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    mock_mq.publish_task.assert_called_once()
    published = mock_mq.publish_task.call_args[0][0]
    assert published["source"] == "sonarqube"
    assert published["project_key"] == "my-service"


# ---------------------------------------------------------------------------
# /webhooks/sonarqube — No project_key → MQ not called
# ---------------------------------------------------------------------------

def test_sonarqube_webhook_no_project_key_skips_mq(webhook_client):
    """payload 中无 project_key 时不触发 MQ。"""
    payload = {"status": "ERROR"}

    with patch("devops_portal.routers.webhook_router.MessageQueue") as mock_mq_cls:
        mock_mq = MagicMock()
        mock_mq_cls.return_value = mock_mq

        response = webhook_client.post("/webhooks/sonarqube", json=payload)

    assert response.status_code == 200
    mock_mq.publish_task.assert_not_called()


# ---------------------------------------------------------------------------
# /webhooks/triggers/sonarqube — Normal trigger with project_key
# ---------------------------------------------------------------------------

def test_sonarqube_trigger_publishes_ci_task(webhook_client):
    """CI trigger 端点正常发布 ci_triggered 任务。"""
    payload = {"project_key": "backend-api"}

    with patch("devops_portal.routers.webhook_router.MessageQueue") as mock_mq_cls:
        mock_mq = MagicMock()
        mock_mq_cls.return_value = mock_mq

        response = webhook_client.post("/webhooks/triggers/sonarqube", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    published = mock_mq.publish_task.call_args[0][0]
    assert published["job_type"] == "ci_triggered"
    assert published["project_key"] == "backend-api"


# ---------------------------------------------------------------------------
# /webhooks/triggers/sonarqube — Missing project_key → error
# ---------------------------------------------------------------------------

def test_sonarqube_trigger_missing_project_key(webhook_client):
    """缺少 project_key 时返回 error message。"""
    response = webhook_client.post("/webhooks/triggers/sonarqube", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "project_key" in body["message"]
