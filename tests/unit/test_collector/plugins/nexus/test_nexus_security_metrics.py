from unittest.mock import MagicMock

from devops_collector.plugins.nexus.models import NexusAsset, NexusComponent
from devops_collector.plugins.nexus.worker import NexusWorker


def test_parse_security_and_usage_metrics(db_session):
    # Setup mock data
    comp = NexusComponent(id="comp-2", repository="maven-releases", name="my-secure-app")
    asset = NexusAsset(id="asset-2", component_id="comp-2", path="app.jar", download_url="http://test/app.jar")
    comp.assets = [asset]
    db_session.add(comp)
    db_session.commit()

    # We will simulate that the data dictionary fetched from Nexus API contains security and usage
    nexus_api_data = {
        "id": "comp-2",
        "name": "my-secure-app",
        # Simulating external metadata added by Nexus IQ or plugins
        "security": {"highest_cve_score": 9.8, "policy_status": "Fail", "license_type": "GPLv3"},
        "assets": [{"id": "asset-2", "path": "app.jar", "lastModified": "2025-01-01T12:00:00.000+00:00", "downloadCount": 1500}],
    }

    mock_client = MagicMock()
    # Not using list_components directly here to focus on the processing logic
    worker = NexusWorker(session=db_session, client=mock_client)
    worker._resolve_product_id = MagicMock(return_value=None)

    # Process the mock data through _save_batch
    worker._save_batch([nexus_api_data], "maven-releases")

    # Fetch from DB
    updated_comp = db_session.query(NexusComponent).filter_by(id="comp-2").first()
    updated_asset = db_session.query(NexusAsset).filter_by(id="asset-2").first()

    # Asserts for Security
    assert updated_comp.highest_cve_score == 9.8
    assert updated_comp.policy_status == "Fail"
    assert updated_comp.license_type == "GPLv3"

    # Asserts for Usage Metrics
    assert updated_asset.download_count == 1500
