import uuid
from datetime import datetime


"""TODO: Add module description."""

from sqlalchemy import JSON, BigInteger, DateTime, Float, ForeignKey, Integer, String, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devops_collector.models.base_models import Base, TimestampMixin, TraceabilityMixin, User, int_pk, json_dict


class JFrogArtifact(Base, TimestampMixin, TraceabilityMixin):
    """JFrog 制品模型 (jfrog_artifacts)。

    存储从 Artifactory 采集的制品元数据，支持 SLSA 溯源。

    Attributes:
        id (int): 自增主键。
        repo (str): 仓库名称。
        path (str): 制品路径。
        name (str): 制品文件名。
        version (str): 版本号。
        package_type (str): 包类型 (docker, maven, pypi 等)。
        size_bytes (int): 文件大小 (字节)。
        sha256 (str): SHA256 校验码。
        download_count (int): 下载次数。
        last_downloaded_at (datetime): 最近下载时间。
        build_name (str): 关联的构建名称。
        build_number (str): 关联的构建号。
        build_url (str): 构建详情 URL。
        vcs_url (str): 源码仓库地址。
        vcs_revision (str): 源码修订版本 (Commit Hash)。
        builder_id (str): 构建平台标识。
        is_signed (int): 是否已签名 (0: 否, 1: 是)。
        promotion_status (str): 晋级状态 (staging, released 等)。
        properties (dict): 自定义属性 (JSON)。
        created_by_id (UUID): 创建者的 OneID。
        created_by_name (str): 创建者显示名。
        product_id (int): 关联的产品 ID。
        created_by (User): 关联的用户对象。
        product (Product): 关联的产品对象。
    """

    __tablename__ = "jfrog_artifacts"
    id: Mapped[int_pk]
    repo: Mapped[str | None] = mapped_column(String(100), nullable=False)
    path: Mapped[str | None] = mapped_column(String(500), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    package_type: Mapped[str | None] = mapped_column(String(50))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(String(64))
    download_count: Mapped[int | None] = mapped_column(Integer, default=0)
    last_downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    build_name: Mapped[str | None] = mapped_column(String(200))
    build_number: Mapped[str | None] = mapped_column(String(50))
    build_url: Mapped[str | None] = mapped_column(String(500))
    vcs_url: Mapped[str | None] = mapped_column(String(500))
    vcs_revision: Mapped[str | None] = mapped_column(String(100))
    builder_id: Mapped[str | None] = mapped_column(String(200))
    build_type: Mapped[str | None] = mapped_column(String(100))
    is_signed: Mapped[int | None] = mapped_column(Integer, default=0)
    external_parameters: Mapped[json_dict | None] = mapped_column(JSON)
    build_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    build_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    promotion_status: Mapped[str | None] = mapped_column(String(50))
    properties: Mapped[json_dict | None] = mapped_column(JSON)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"))
    created_by_name: Mapped[str | None] = mapped_column(String(100))
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mdm_products.id"))
    created_by: Mapped["User | None"] = relationship("User", primaryjoin=and_(User.global_user_id == created_by_id, User.is_current.is_(True)))  # noqa: F821
    product: Mapped["Product | None"] = relationship("Product")  # noqa: F821
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<JFrogArtifact(name='{self.name}', version='{self.version}')>"


class JFrogScan(Base, TimestampMixin, TraceabilityMixin):
    """JFrog Xray 扫描结果模型。

    Attributes:
        id (int): 自增主键。
        artifact_id (int): 关联的制品 ID。
        critical_count (int): 严重漏洞数。
        high_count (int): 高危漏洞数。
        medium_count (int): 中危漏洞数。
        low_count (int): 低危漏洞数。
        violation_count (int): 策略违反数。
        is_compliant (int): 是否合规 (1: 是, 0: 否)。
        scan_time (datetime): 扫描时间。
        artifact (JFrogArtifact): 关联的制品。
    """

    __tablename__ = "jfrog_scans"
    id: Mapped[int_pk]
    artifact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jfrog_artifacts.id"))
    critical_count: Mapped[int | None] = mapped_column(Integer, default=0)
    high_count: Mapped[int | None] = mapped_column(Integer, default=0)
    medium_count: Mapped[int | None] = mapped_column(Integer, default=0)
    low_count: Mapped[int | None] = mapped_column(Integer, default=0)
    violation_count: Mapped[int | None] = mapped_column(Integer, default=0)
    is_compliant: Mapped[int | None] = mapped_column(Integer)
    scan_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)
    artifact: Mapped["JFrogArtifact | None"] = relationship("JFrogArtifact")  # noqa: F821

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<JFrogScan(artifact_id={self.artifact_id}, compliant={self.is_compliant})>"


class JFrogVulnerabilityDetail(Base, TimestampMixin, TraceabilityMixin):
    """漏洞详情明细表。

    Attributes:
        id (int): 自增主键。
        artifact_id (int): 关联的制品 ID。
        cve_id (str): CVE 编号。
        severity (str): 严重程度。
        cvss_score (float): CVSS 评分。
        component (str): 受影响的组件名。
        fixed_version (str): 修复版本。
        description (str): 漏洞描述。
    """

    __tablename__ = "jfrog_vulnerability_details"
    id: Mapped[int_pk]
    artifact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jfrog_artifacts.id"))
    cve_id: Mapped[str | None] = mapped_column(String(50), index=True)
    severity: Mapped[str | None] = mapped_column(String(20))
    cvss_score: Mapped[float | None] = mapped_column(Float)
    component: Mapped[str | None] = mapped_column(String(200))
    fixed_version: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String)
    artifact: Mapped["JFrogArtifact | None"] = relationship("JFrogArtifact")  # noqa: F821

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<JFrogVulnerabilityDetail(cve='{self.cve_id}', severity='{self.severity}')>"


class JFrogDependency(Base, TimestampMixin, TraceabilityMixin):
    """制品依赖树模型 (SBoM)。

    Attributes:
        id (int): 自增主键。
        artifact_id (int): 关联的制品 ID。
        name (str): 依赖项名称。
        version (str): 依赖项版本。
        package_type (str): 包类型。
        scope (str): 依赖范围 (compile, runtime 等)。
    """

    __tablename__ = "jfrog_dependencies"
    id: Mapped[int_pk]
    artifact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jfrog_artifacts.id"))
    name: Mapped[str | None] = mapped_column(String(200), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    package_type: Mapped[str | None] = mapped_column(String(50))
    scope: Mapped[str | None] = mapped_column(String(50))
    artifact: Mapped["JFrogArtifact | None"] = relationship("JFrogArtifact")  # noqa: F821

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<JFrogDependency(name='{self.name}', version='{self.version}')>"
