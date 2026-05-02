"""TODO: Add module description."""

import unittest
from unittest.mock import MagicMock, patch

from devops_collector.plugins.zentao.client import ZenTaoClient


class TestZenTaoClient(unittest.TestCase):
    '''"""TODO: Add class description."""'''

    def setUp(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        self.client = ZenTaoClient("http://zentao.fake.com/api.php/v1", "token")

    @patch("time.sleep", return_value=None)
    @patch("requests.Session.request")
    def test_get_products(self, mock_request, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": [{"id": 1, "name": "Prod 1"}]}
        mock_request.return_value = mock_response

        products = self.client.get_products()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["name"], "Prod 1")

    @patch("time.sleep", return_value=None)
    @patch("requests.Session.request")
    def test_refresh_token_success(self, mock_request, mock_sleep):
        self.client.account = "admin"
        self.client.password = "123456"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "new-secret-token"}
        mock_request.return_value = mock_response

        success = self.client._refresh_token()
        self.assertTrue(success)
        self.assertEqual(self.client.headers["Token"], "new-secret-token")

    @patch("time.sleep", return_value=None)
    @patch("requests.Session.request")
    def test_get_with_401_retry(self, mock_request, mock_sleep):
        from requests.exceptions import HTTPError

        # 模拟第一次 401，然后刷新 Token 成功，第二次 200
        mock_401 = MagicMock()
        mock_401.status_code = 401
        mock_401.raise_for_status.side_effect = HTTPError(response=mock_401)

        mock_refresh = MagicMock()
        mock_refresh.status_code = 200
        mock_refresh.json.return_value = {"token": "refreshed"}

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"users": []}

        mock_request.side_effect = [mock_401, mock_refresh, mock_200]
        self.client.account = "admin"
        self.client.password = "pwd"

        resp = self.client._get("users")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(mock_request.call_count, 3)

    def test_handle_list_response(self):
        # 测试 404
        mock_404 = MagicMock(status_code=404)
        self.assertEqual(self.client._handle_list_response(mock_404, "key"), [])

        # 测试直接返回列表
        mock_list = MagicMock(status_code=200)
        mock_list.json.return_value = [{"id": 1}]
        self.assertEqual(self.client._handle_list_response(mock_list, "key"), [{"id": 1}])

        # 测试字典包装
        mock_dict = MagicMock(status_code=200)
        mock_dict.json.return_value = {"items": [{"id": 2}]}
        self.assertEqual(self.client._handle_list_response(mock_dict, "items"), [{"id": 2}])

    @patch("time.sleep", return_value=None)
    @patch("requests.Session.request")
    def test_refresh_token_failure(self, mock_request, mock_sleep):
        self.client.account = "admin"
        self.client.password = "123"
        mock_request.return_value = MagicMock(status_code=403)
        success = self.client._refresh_token()
        self.assertFalse(success)

    @patch("requests.Session.request")
    def test_all_getters_with_pagination(self, mock_request):
        # 模拟多页返回，触发分页逻辑
        mock_request.side_effect = [
            # projects page 1
            MagicMock(status_code=200, json=lambda: {"total": 3, "projects": [{"id": 1}, {"id": 2}]}),
            # projects page 2
            MagicMock(status_code=200, json=lambda: {"total": 3, "projects": [{"id": 3}]}),
            # others return 200
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            MagicMock(status_code=200, json=lambda: {"items": []}),
            # test_connection
            MagicMock(status_code=200),
            # bugs paged
            MagicMock(status_code=200, json=lambda: {"total": 2, "bugs": [{"id": 1}]}),
            MagicMock(status_code=200, json=lambda: {"total": 2, "bugs": [{"id": 2}]}),
        ]

        self.client.get_projects()
        self.client.get_programs()
        self.client.get_plans(1)
        self.client.get_executions(product_id=1)
        self.client.get_test_cases(1)
        self.client.get_test_results(1)
        self.client.get_builds(1)
        self.client.get_releases(1)
        self.client.get_actions(1)
        self.client.get_tasks(1)
        self.client.get_departments()
        self.client.get_users()
        self.client.test_connection()
        self.client.get_bugs(1)

    @patch("time.sleep", return_value=None)
    @patch("requests.Session.request")
    def test_get_stories_pagination(self, mock_request, mock_sleep):
        mock_request.side_effect = [
            MagicMock(status_code=200, json=lambda: {"total": 3, "stories": [{"id": 1}, {"id": 2}]}),
            MagicMock(status_code=200, json=lambda: {"total": 3, "stories": [{"id": 3}]}),
        ]
        stories = self.client.get_stories(1)
        self.assertEqual(len(stories), 3)
        self.assertGreaterEqual(mock_request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
