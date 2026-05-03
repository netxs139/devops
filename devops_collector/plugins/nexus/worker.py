"""Nexus 数据采集 Worker"""

import logging
import re
from datetime import datetime

from devops_collector.core.base_worker import BaseWorker
from devops_collector.core.identity_manager import IdentityManager

# from .client import NexusClient
from devops_collector.models.base_models import Product

from .models import NexusAsset, NexusComponent


SYNC_SINCE_DATE = datetime(2024, 1, 1)
TRACE_FILE_NAME = "devops-trace.properties"


def _is_after_cutoff(dt_str: str | None) -> bool:
    """判断给定时间字符串是否在 cutoff_date 之后"""
    if not dt_str:
        return True  # 如果没有时间，保守起见默认拉取
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt >= SYNC_SINCE_DATE
    except Exception:
        return True  # 解析失败默认拉取


logger = logging.getLogger(__name__)


class NexusWorker(BaseWorker):
    """Nexus 数据采集 Worker。"""

    SCHEMA_VERSION = "1.0"

    def process_task(self, task: dict) -> None:
        """处理 Nexus 同步任务。
        task 结构示例: {'repository': 'maven-releases', 'job_type': 'full'}
        """
        repository = task.get("repository")
        if not repository:
            raise ValueError("Nexus task missing 'repository'")
        logger.info(f"Syncing Nexus repository: {repository}")

        # 预加载产品缓存
        self._init_product_cache()

        try:
            count = self._sync_components(repository)
            self.log_success(f"Nexus repository {repository} synced: {count} components")
        except Exception as e:
            self.log_failure(f"Failed to sync Nexus repository {repository}", e)
            raise

    def _init_product_cache(self):
        """初始化产品代码缓存及匹配模式列表。"""
        # 查询产品 ID 和匹配模式
        products = self.session.query(Product.product_code, Product.matching_patterns).filter(Product.is_current).all()

        self._product_map = {p.product_code.lower(): p.product_code for p in products}

        # 编译所有产品的匹配正则
        self._pattern_rules = []
        for p in products:
            patterns = p.matching_patterns
            if not patterns:
                continue
            if isinstance(patterns, str):
                patterns = [patterns]

            for pat in patterns:
                try:
                    # 智能判断是正则还是简单通配符
                    if pat.startswith("^") or pat.endswith("$") or "\\" in pat:
                        regex_str = pat
                    else:
                        # 简单模式：将 . 替换为 \.，将 * 替换为 .*
                        p_norm = pat.replace(".", r"\.").replace("*", ".*")
                        regex_str = f"^{p_norm}$"

                    self._pattern_rules.append({"re": re.compile(regex_str, re.I), "pid": p.product_code})
                except Exception as e:
                    logger.warning(f"Invalid matching pattern '{pat}' for product {p.product_code}: {e}")

        logger.info(f"Loaded {len(self._product_map)} products and {len(self._pattern_rules)} patterns.")

    def _resolve_product_id(self, group: str | None, name: str) -> str | None:
        """根据 Group 或 Name 智能解析所属 Product ID (优先匹配显式模式)。"""
        target_str = f"{group or ''}:{name}"

        # 1. 优先使用显式定义的 matching_patterns (正则匹配)
        for rule in self._pattern_rules:
            if rule["re"].match(group or "") or rule["re"].match(name) or rule["re"].match(target_str):
                return rule["pid"]

        # 2. 降级策略: 尝试通过 group 拆分匹配 (Maven 风格)
        if group:
            parts = group.lower().split(".")
            for part in reversed(parts):
                if part in self._product_map:
                    return self._product_map[part]

        # 3. 降级策略: 尝试通过 name 精确匹配
        name_lower = name.lower()
        if name_lower in self._product_map:
            return self._product_map[name_lower]

        return None

    def _sync_components(self, repository: str) -> int:
        """拉取并保存组件及其资产。"""
        generator = self.client.list_components(repository)
        count = 0
        batch = []
        batch_size = 100
        for item in generator:
            batch.append(item)
            if len(batch) >= batch_size:
                self._save_batch(batch, repository)
                count += len(batch)
                batch = []
        if batch:
            self._save_batch(batch, repository)
            count += len(batch)
        return count

    def _save_batch(self, batch: list[dict], repository: str) -> None:
        """批量保存到数据库，并执行身份/产品识别。"""
        for data in batch:
            comp_id = data["id"]
            comp_repo = data.get("repository") or repository
            comp = self.session.query(NexusComponent).filter_by(id=comp_id).first()
            if not comp:
                comp = NexusComponent(
                    id=comp_id,
                    repository=comp_repo,
                    name=data["name"],
                    format=data.get("format"),
                    group=data.get("group"),
                    version=data.get("version"),
                )
                self.session.add(comp)
            else:
                comp.repository = comp_repo
                comp.format = data.get("format")
                comp.group = data.get("group")
                comp.name = data["name"]
                comp.version = data.get("version")

            # DevSecOps: Parse security metadata
            security_data = data.get("security", {})
            if security_data:
                comp.highest_cve_score = security_data.get("highest_cve_score")
                comp.policy_status = security_data.get("policy_status")
                comp.license_type = security_data.get("license_type")

            self.save_to_staging(
                source="nexus",
                entity_type="component",
                external_id=comp_id,
                payload=data,
                schema_version=self.SCHEMA_VERSION,
            )

            # 深度集成：自动产品对齐
            resolved_pid = self._resolve_product_id(comp.group, comp.name)
            if resolved_pid:
                comp.product_id = resolved_pid

            comp.raw_data = data

            # 使用最新可用时间来进行时间隔离网判断
            # 如果资产中的 last_modified 都小于 2024 年，也可以在 asset 级别拦截
            self._sync_assets(comp, data.get("assets", []))

            # 尝试从资产中解析追溯信息
            self._try_parse_traceability(comp)

        self.session.commit()

    def _sync_assets(self, component: NexusComponent, assets_data: list[dict]) -> None:
        """同步组件关联的资产。"""
        existing_assets = {a.id: a for a in component.assets}
        for asset_data in assets_data:
            a_id = asset_data["id"]

            # Nexus API lastModified example: '2022-09-08T12:00:00.000+00:00'
            last_modified_str = asset_data.get("lastModified")
            if not _is_after_cutoff(last_modified_str):
                continue  # 如果文件本身是在 2024年1月1日之前修改/创建的，跳过入库

            self.save_to_staging(
                source="nexus",
                entity_type="asset",
                external_id=a_id,
                payload=asset_data,
                schema_version=self.SCHEMA_VERSION,
            )

            if a_id in existing_assets:
                asset = existing_assets[a_id]
                asset.download_count = asset_data.get("downloadCount", asset.download_count)
                asset.raw_data = asset_data
                # Update checksums if needed
                checksums = asset_data.get("checksum", {})
                if checksums:
                    asset.checksum_sha1 = checksums.get("sha1", asset.checksum_sha1)
                    asset.checksum_sha256 = checksums.get("sha256", asset.checksum_sha256)
                    asset.checksum_md5 = checksums.get("md5", asset.checksum_md5)
                continue

            asset = NexusAsset(
                id=a_id,
                component_id=component.id,
                path=asset_data["path"],
                download_url=asset_data.get("downloadUrl"),
                size_bytes=asset_data.get("fileSize"),
                download_count=asset_data.get("downloadCount", 0),  # FinOps: Usage metrics
                raw_data=asset_data,
            )

            checksums = asset_data.get("checksum", {})
            asset.checksum_sha1 = checksums.get("sha1")
            asset.checksum_sha256 = checksums.get("sha256")
            asset.checksum_md5 = checksums.get("md5")
            self.session.add(asset)

    def _try_parse_traceability(self, component: NexusComponent) -> None:
        """尝试从组件的资产中寻找并解析 devops-trace.properties。"""
        # 注意：component.assets 可能还在 Session 中未完全同步，此处优先利用同步后的属性
        trace_asset = next((a for a in component.assets if a.path.endswith(TRACE_FILE_NAME)), None)
        if not trace_asset or not trace_asset.download_url:
            return

        try:
            logger.info(f"Found trace file for component {component.name}: {trace_asset.path}")
            content = self.client.download_asset_content(trace_asset.download_url)

            # 简单解析 properties 格式 (key=value)
            props = {}
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if "=" in line and not line.startswith("#") and not line.startswith("!"):
                    k, v = line.split("=", 1)
                    props[k.strip()] = v.strip()

            commit_sha = props.get("commit_sha")
            build_pipeline_id = props.get("build_pipeline_id")
            build_url = props.get("build_url")
            uploader = props.get("uploader")

            # 1. 直接填入“专座”（物理列）
            if commit_sha:
                component.commit_sha = commit_sha
            if build_pipeline_id:
                component.build_pipeline_id = build_pipeline_id
            if build_url:
                component.build_url = build_url
            if uploader:
                component.uploader_account = uploader
                # 身份对齐：将上传者原始账号转换为 global_user_id
                global_id = IdentityManager.get_global_id(self.session, uploader, "nexus")
                if global_id:
                    component.owner_id = global_id

            # 2. 同时也保留在元数据大合集里备用
            if not component.raw_data:
                component.raw_data = {}

            if "ext_info" not in component.raw_data:
                component.raw_data["ext_info"] = {}

            component.raw_data["ext_info"].update(props)
            logger.info(f"Successfully processed trace file for {component.name}")

        except Exception as e:
            logger.warning(f"Failed to parse trace file {trace_asset.path}: {e}")
