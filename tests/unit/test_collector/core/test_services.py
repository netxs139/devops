from datetime import datetime

import pytest

from devops_collector.core.services import ConcurrencyError, close_current_and_insert_new
from devops_collector.models.base_models import Organization


def test_close_current_and_insert_new_success(db_session):
    # 1. Create initial record
    org = Organization(org_code="ORG1", org_name="Original Name", sync_version=1, is_current=True, effective_from=datetime(2023, 1, 1))
    db_session.add(org)
    db_session.commit()

    # 2. Update via SCD Type 2
    new_data = {"org_name": "Updated Name", "sync_version": 1}
    new_org = close_current_and_insert_new(db_session, Organization, {"org_code": "ORG1"}, new_data)
    db_session.commit()

    # 3. Verify
    # Old record should be expired
    db_session.refresh(org)
    assert org.is_current is False
    assert org.effective_to is not None

    # New record should be active
    assert new_org.id != org.id
    assert new_org.org_name == "Updated Name"
    assert new_org.sync_version == 2
    assert new_org.is_current is True
    assert new_org.effective_from == org.effective_to


def test_close_current_and_insert_new_not_found(db_session):
    with pytest.raises(ConcurrencyError, match="未找到 Organization"):
        close_current_and_insert_new(db_session, Organization, {"org_code": "NONEXISTENT"}, {"sync_version": 1})


def test_close_current_and_insert_new_missing_version(db_session):
    org = Organization(org_code="ORG2", org_name="N2", sync_version=1, is_current=True)
    db_session.add(org)
    db_session.commit()

    with pytest.raises(ConcurrencyError, match="new_data 必须包含 sync_version"):
        close_current_and_insert_new(db_session, Organization, {"org_code": "ORG2"}, {"org_name": "New"})


def test_close_current_and_insert_new_version_mismatch(db_session):
    org = Organization(org_code="ORG3", org_name="N3", sync_version=5, is_current=True)
    db_session.add(org)
    db_session.commit()

    with pytest.raises(ConcurrencyError, match="乐观锁冲突"):
        close_current_and_insert_new(
            db_session,
            Organization,
            {"org_code": "ORG3"},
            {"org_name": "New", "sync_version": 4},  # Wrong version
        )
