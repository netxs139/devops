from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

from devops_collector.core.base_worker import BaseWorker


Base = declarative_base()


class MockSyncModel(Base):
    __tablename__ = "mock_sync_model"
    id = Column(Integer, primary_key=True)
    sync_status = Column(String(20))
    last_synced_at = Column(DateTime)


class ConcreteWorker(BaseWorker):
    def process_task(self, task):
        if task.get("should_fail"):
            raise ValueError("Forced failure")
        return "Task Result"


@pytest.fixture
def db_session():
    session = MagicMock()
    return session


@pytest.fixture
def worker(db_session):
    client = MagicMock()
    return ConcreteWorker(db_session, client, correlation_id="test-cid")


def test_worker_init(worker, db_session):
    assert worker.session == db_session
    assert worker.correlation_id == "test-cid"
    assert isinstance(worker.logger.logger, logging.Logger)  # LoggerAdapter.logger


import logging


def test_run_sync_success(worker, db_session):
    task = {"source": "test_src"}
    mock_instance = MagicMock(spec=MockSyncModel)
    mock_instance.sync_status = "PENDING"

    # Setup query mock
    db_session.query.return_value.filter_by.return_value.first.return_value = mock_instance

    result = worker.run_sync(task, model_cls=MockSyncModel, pk_value=1)

    assert result == "Task Result"
    assert mock_instance.sync_status == "SUCCESS"
    assert mock_instance.last_synced_at is not None
    assert db_session.commit.call_count >= 1


def test_run_sync_failure(worker, db_session):
    task = {"source": "test_src", "should_fail": True}
    mock_instance = MagicMock(spec=MockSyncModel)

    db_session.query.return_value.filter_by.return_value.first.return_value = mock_instance

    with pytest.raises(ValueError, match="Forced failure"):
        worker.run_sync(task, model_cls=MockSyncModel, pk_value=1)

    assert mock_instance.sync_status == "FAILED"
    db_session.rollback.assert_called_once()


def test_logging(worker):
    with patch.object(worker.logger, "info") as mock_info:
        worker.log_success("Great success")
        mock_info.assert_called_with("[SUCCESS] Great success")

        worker.log_progress("Work", 1, 2)
        mock_info.assert_called_with("[PROGRESS] Work: 1/2 (50.0%)")


def test_save_to_staging_fallback(worker, db_session):
    # Mock dialect to not be postgresql
    db_session.bind.dialect.name = "sqlite"
    # Force exception in execute to trigger fallback
    db_session.execute.side_effect = Exception("Mock Upsert Failure")
    # Make query return None to trigger session.add
    db_session.query.return_value.filter_by.return_value.first.return_value = None

    payload = {"key": "val"}
    worker.save_to_staging("src", "type", "ext123", payload)

    # Check if RawDataStaging was added or queried in fallback
    db_session.query.assert_called()
    db_session.add.assert_called()


def test_save_to_staging_update(worker, db_session):
    db_session.bind.dialect.name = "sqlite"
    db_session.execute.side_effect = Exception("Mock Upsert Failure")

    mock_existing = MagicMock()
    db_session.query.return_value.filter_by.return_value.first.return_value = mock_existing

    worker.save_to_staging("src", "type", "ext123", {"new": "data"})

    assert mock_existing.payload == {"new": "data"}


def test_bulk_save_to_staging_sqlite(worker, db_session):
    db_session.bind.dialect.name = "sqlite"
    items = [{"id": 1, "data": "a"}, {"id": 2, "data": "b"}]

    with patch.object(worker, "save_to_staging") as mock_save:
        worker.bulk_save_to_staging("src", "type", items)
        assert mock_save.call_count == 2


def test_bulk_save_to_staging_postgresql(worker, db_session):
    db_session.bind.dialect.name = "postgresql"
    items = [{"id": 1, "data": "a"}]

    mock_cursor = MagicMock()
    # Handle the dbapi_connection check in base_worker.py
    mock_raw_conn = MagicMock()
    del mock_raw_conn.dbapi_connection  # Force it to use the raw_conn itself
    mock_raw_conn.cursor.return_value = mock_cursor

    db_session.connection.return_value.connection = mock_raw_conn

    worker.bulk_save_to_staging("src", "type", items)

    assert mock_cursor.execute.call_count >= 1
    assert mock_cursor.copy_expert.call_count == 1
    assert mock_cursor.close.call_count == 1
