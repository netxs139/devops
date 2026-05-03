"""Nexus Worker 单元测试"""

import unittest
from unittest.mock import MagicMock, patch

from devops_collector.plugins.nexus.models import NexusComponent
from devops_collector.plugins.nexus.worker import NexusWorker


class TestNexusWorker(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.client = MagicMock()
        self.worker = NexusWorker(self.session, self.client)

        # 模拟产品数据 (带 matching_patterns 字段)
        self.mock_products = [
            MagicMock(product_code="devops", matching_patterns=None, is_current=True),
            MagicMock(product_code="portal", matching_patterns=None, is_current=True),
            MagicMock(product_code="collector", matching_patterns=None, is_current=True),
        ]
        # 统一设置 query().filter().all() 的返回值
        self.session.query.return_value.filter.return_value.all.return_value = self.mock_products

    def test_product_cache_init(self):
        """测试产品缓存初始化。"""
        self.worker._init_product_cache()
        self.assertIn("devops", self.worker._product_map)
        self.assertEqual(self.worker._product_map["devops"], "devops")

    def test_resolve_product_id_by_group(self):
        """测试通过 Group 自动识别产品。"""
        self.worker._init_product_cache()

        # 匹配 devops
        pid = self.worker._resolve_product_id("com.tjhq.devops", "some-lib")
        self.assertEqual(pid, "devops")

        # 匹配 portal
        pid = self.worker._resolve_product_id("org.company.portal.submodule", "api")
        self.assertEqual(pid, "portal")

    def test_resolve_product_id_by_name(self):
        """测试通过组件名称精确匹配产品。"""
        self.worker._init_product_cache()

        pid = self.worker._resolve_product_id("random.group", "collector")
        self.assertEqual(pid, "collector")

    def test_resolve_product_id_by_explicit_patterns(self):
        """测试通过显式定义的 matching_patterns 进行正则匹配。"""
        # 模拟带正则的产品
        mock_products = [
            MagicMock(product_code="security-app", matching_patterns=["^sec-.*", "com.tjhq.security.*"], is_current=True),
        ]
        self.session.query.return_value.filter.return_value.all.return_value = mock_products
        self.worker._init_product_cache()

        # 1. 匹配名称前缀
        self.assertEqual(self.worker._resolve_product_id(None, "sec-scanner"), "security-app")
        # 2. 匹配 Group 前缀
        self.assertEqual(self.worker._resolve_product_id("com.tjhq.security.api", "util"), "security-app")
        # 3. 不匹配
        self.assertIsNone(self.worker._resolve_product_id("com.other", "app"))

    def test_resolve_product_id_not_found(self):
        """测试匹配失败情况。"""
        self.worker._init_product_cache()

        pid = self.worker._resolve_product_id("unknown.group", "unknown-lib")
        self.assertIsNone(pid)

    @patch("devops_collector.core.base_worker.BaseWorker.save_to_staging")
    def test_save_batch_with_auto_mapping(self, mock_staging):
        """测试批量保存时的自动映射逻辑。"""
        self.worker._init_product_cache()
        self.session.query(NexusComponent).filter_by().first.return_value = None

        batch = [
            {
                "id": "comp1",
                "repository": "maven-public",
                "format": "maven2",
                "group": "com.tjhq.devops",
                "name": "core",
                "version": "1.0.0",
                "assets": [],
            }
        ]

        # 3. Save batch
        self.worker._save_batch(batch, "maven-releases")

        # 验证是否创建了组件且绑定了 product_code
        args, kwargs = self.session.add.call_args
        comp = args[0]
        self.assertIsInstance(comp, NexusComponent)
        self.assertEqual(comp.product_id, "devops")
        self.session.commit.assert_called_once()

    def test_sync_components_paging(self):
        """测试组件同步的分页处理。"""
        self.client.list_components.return_value = iter([{"id": "c1", "name": "n1"}, {"id": "c2", "name": "n2"}])
        with patch.object(self.worker, "_save_batch") as mock_save:
            count = self.worker._sync_components("repo1")
            self.assertEqual(count, 2)
            mock_save.assert_called_once()

    @patch("devops_collector.plugins.nexus.worker._is_after_cutoff", return_value=True)
    @patch("devops_collector.core.base_worker.BaseWorker.save_to_staging")
    def test_sync_assets(self, mock_staging, mock_cutoff):
        """测试资产同步逻辑。"""
        comp = NexusComponent(id="c1", name="n1")
        comp.assets = []
        assets_data = [{"id": "a1", "path": "path/to/a1", "downloadUrl": "http://url1", "fileSize": 100, "lastModified": "2024-05-01T00:00:00Z"}]
        self.worker._sync_assets(comp, assets_data)
        self.assertEqual(len(self.session.add.call_args_list), 1)
        asset = self.session.add.call_args_list[0][0][0]
        self.assertEqual(asset.id, "a1")
        self.assertEqual(asset.download_url, "http://url1")

    def test_try_parse_traceability_success(self):
        """测试从 properties 文件解析追溯信息。"""
        # 1. 模拟组件和资产
        comp = MagicMock(spec=NexusComponent)
        comp.name = "test-comp"
        comp.assets = [MagicMock(path="release/devops-trace.properties", download_url="http://trace-url")]
        comp.raw_data = {}

        # 2. 模拟下载内容
        self.client.download_asset_content.return_value = "commit_sha=abcdef123456\nbuild_id=999"

        # 3. 执行
        self.worker._try_parse_traceability(comp)

        # 4. 验证
        self.assertEqual(comp.commit_sha, "abcdef123456")
        self.assertEqual(comp.raw_data["ext_info"]["commit_sha"], "abcdef123456")
