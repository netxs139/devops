import datetime


"""Nexus 插件数据模型。"""

from sqlalchemy import JSON, BigInteger, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devops_collector.models.base_models import (
    Base,
    OwnableMixin,
    SCDMixin,
    TimestampMixin,
    json_dict,
)


class NexusComponent(Base, TimestampMixin, SCDMixin, OwnableMixin):
    """Nexus 组件模型 (nexus_components)。

    Attributes:
        id (str): Nexus 内部组件 ID。
        repository (str): 仓库名称。
        format (str): 格式 (maven2, npm, docker 等)。
        group (str): 组织/分组。
        name (str): 组件名称。
        version (str): 版本号。
        product_id (str): 关联的产品 ID。
        product (Product): 关联的产品对象。
        assets (List[NexusAsset]): 该组件包含的资产列表。
    """

    __tablename__ = "nexus_components"
    id: Mapped[str] = mapped_column(primary_key=True)
    repository: Mapped[str | None] = mapped_column(String(100), nullable=False)
    format: Mapped[str | None] = mapped_column(String(50))
    group: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mdm_products.id"), nullable=True)
    commit_sha: Mapped[str | None] = mapped_column(String(100), index=True)  # 直接存储 Git Commit SHA，提升 DORA 关联性能
    build_pipeline_id: Mapped[str | None] = mapped_column(String(100))  # 新增：构建流水线 ID (CI Context)
    build_url: Mapped[str | None] = mapped_column(String(500))  # 新增：流水线 URL
    uploader_account: Mapped[str | None] = mapped_column(String(100))  # 新增：原始上传者账号名 (Identity Context)

    # 新增：组件安全漏洞与合规数据 (DevSecOps)
    highest_cve_score: Mapped[float | None] = mapped_column(Float)  # 最高 CVE 漏洞评分 (如 9.8)
    policy_status: Mapped[str | None] = mapped_column(String(50))  # 安全门禁状态 (如 Pass, Fail, Warn)
    license_type: Mapped[str | None] = mapped_column(String(100))  # 传染性开源协议分析结果 (如 GPLv3, MIT)

    # 索引优化：为常用的查询组合建立联合索引
    __table_args__ = (Index("ix_nexus_components_lookup", "repository", "group", "name"),)

    product: Mapped["Product | None"] = relationship("Product")  # noqa: F821
    assets: Mapped[list["NexusAsset"]] = relationship("NexusAsset", back_populates="component", cascade="all, delete-orphan")  # noqa: F821
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<NexusComponent(name='{self.name}', version='{self.version}')>"


class NexusAsset(Base, TimestampMixin, SCDMixin):
    """Nexus 资产（文件）模型 (nexus_assets)。

    Attributes:
        id (str): Nexus 资产唯一 ID。
        component_id (str): 关联的组件 ID。
        path (str): 文件路径。
        download_url (str): 下载链接。
        size_bytes (int): 文件大小 (字节)。
        checksum_sha256 (str): SHA256 校验码。
        component (NexusComponent): 关联的组件对象。
    """

    __tablename__ = "nexus_assets"
    id: Mapped[str] = mapped_column(primary_key=True)
    component_id: Mapped[str | None] = mapped_column(String(100), ForeignKey("nexus_components.id"))
    path: Mapped[str | None] = mapped_column(String(500), nullable=False)
    download_url: Mapped[str | None] = mapped_column(String(1000))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    checksum_sha1: Mapped[str | None] = mapped_column(String(40))
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    checksum_md5: Mapped[str | None] = mapped_column(String(32))

    last_modified: Mapped[datetime | None] = mapped_column(DateTime)
    last_downloaded: Mapped[datetime | None] = mapped_column(DateTime)
    download_count: Mapped[int | None] = mapped_column(Integer, default=0)  # 新增：真实下载/使用频率 (FinOps & Lifecycle)

    component: Mapped["NexusComponent | None"] = relationship("NexusComponent", back_populates="assets")  # noqa: F821
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        return f"<NexusAsset(path='{self.path}')>"
