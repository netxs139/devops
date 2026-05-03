from devops_collector.plugins.nexus.models import NexusAsset, NexusComponent
from devops_collector.plugins.nexus.worker import NexusWorker


def test_try_parse_traceability_with_new_fields(mocker, db_session):
    # Setup mock data
    comp = NexusComponent(id="comp-1", repository="maven-releases", name="my-app")
    asset = NexusAsset(id="asset-1", component_id="comp-1", path="devops-trace.properties", download_url="http://test")
    comp.assets = [asset]
    db_session.add(comp)
    db_session.commit()

    # Mock the client's download method to return our rich trace properties
    mock_client = mocker.MagicMock()
    trace_content = """
commit_sha=abcdef123456
build_pipeline_id=10045
build_url=http://jenkins.local/job/10045
uploader=john.doe
"""
    mock_client.download_asset_content.return_value = trace_content

    # Mock IdentityManager (no more context manager indentation hell)
    mock_im = mocker.patch("devops_collector.plugins.nexus.worker.IdentityManager")
    mock_im.get_global_id.return_value = "uuid-1234-5678"

    # Initialize worker
    worker = NexusWorker(session=db_session, client=mock_client)

    # Run parsing
    worker._try_parse_traceability(comp)

    # Asserts
    assert comp.commit_sha == "abcdef123456"
    assert comp.build_pipeline_id == "10045"
    assert comp.build_url == "http://jenkins.local/job/10045"
    assert comp.uploader_account == "john.doe"

    # Check identity resolution
    mock_im.get_global_id.assert_called_once_with(db_session, "john.doe", "nexus")
    assert comp.owner_id == "uuid-1234-5678"
