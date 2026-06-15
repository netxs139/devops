from streamlit.testing.v1 import AppTest


def test_dashboard_home_apptest():
    """Verify the Streamlit Dashboard Home page loads without exceptions using AppTest."""
    at = AppTest.from_file("dashboard/Home.py")
    # Streamlit AppTest is extremely fast as it simulates the execution
    at.run()
    assert not at.exception, f"AppTest threw an exception: {at.exception}"
