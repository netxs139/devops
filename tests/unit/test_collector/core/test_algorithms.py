from datetime import datetime

from devops_collector.core.algorithms import AgileMetrics, CodeMetrics, QualityMetrics


def test_calculate_cycle_time():
    histories = [
        {"to_string": "In Progress", "created_at": datetime(2023, 1, 1, 10, 0)},
        {"to_string": "Done", "created_at": datetime(2023, 1, 1, 12, 30)},
    ]
    # (12:30 - 10:00) = 2.5 hours
    assert AgileMetrics.calculate_cycle_time(histories) == 2.5

    # Should return None if no start/end match
    assert AgileMetrics.calculate_cycle_time([]) is None


def test_calculate_dora_lead_time():
    deployment = datetime(2023, 1, 1, 15, 0)
    commits = [
        datetime(2023, 1, 1, 10, 0),
        datetime(2023, 1, 1, 12, 0),
    ]
    # (15:00 - 10:00) = 5 hours
    assert AgileMetrics.calculate_dora_lead_time(commits, deployment) == 5.0
    assert AgileMetrics.calculate_dora_lead_time([], deployment) is None


def test_is_ignored():
    assert CodeMetrics.is_ignored("node_modules/abc.js") is True
    assert CodeMetrics.is_ignored("src/main.py") is False
    assert CodeMetrics.is_ignored("package-lock.json") is True


def test_analyze_diff():
    diff = """+ def hello():
+     # This is a comment
+     pass
- old_code()
+
"""
    # 2 lines of code added (def, pass), 1 comment added, 1 blank added. 1 code deleted.
    stats = CodeMetrics.analyze_diff(diff, "test.py")
    assert stats["code_added"] == 2
    assert stats["comment_added"] == 1
    assert stats["blank_added"] == 1
    assert stats["code_deleted"] == 1


def test_get_file_category():
    assert CodeMetrics.get_file_category("src/main.py") == "Code"
    assert CodeMetrics.get_file_category("tests/test_unit.py") == "Test"
    assert CodeMetrics.get_file_category("deploy/k8s/service.yaml") == "IaC"
    assert CodeMetrics.get_file_category("Dockerfile") == "IaC"
    assert CodeMetrics.get_file_category("config/app.conf") == "Config"


def test_rating_to_letter():
    assert QualityMetrics.rating_to_letter("1.0") == "A"
    assert QualityMetrics.rating_to_letter(2.0) == "B"
    assert QualityMetrics.rating_to_letter(100) == "E"
