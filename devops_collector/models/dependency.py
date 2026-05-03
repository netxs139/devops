from __future__ import annotations


"""
OWASP Dependency-Check 数据模型
存储依赖扫描、许可证信息和 CVE 漏洞数据
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base_models import Base, SCDMixin, TimestampMixin


class DependencyScan(Base, TimestampMixin, SCDMixin):
    """依赖扫描记录表 (dependency_scans)。

    存储 OWASP Dependency-Check 等工具生成的扫描任务概览。
    """

    __tablename__ = "dependency_scans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("gitlab_projects.id", ondelete="CASCADE"), nullable=False)
    scan_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scanner_name: Mapped[str] = mapped_column(String(50), nullable=False, default="OWASP Dependency-Check")
    scanner_version: Mapped[str | None] = mapped_column(String(20))
    total_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    vulnerable_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    high_risk_licenses: Mapped[int] = mapped_column(Integer, default=0)
    scan_status: Mapped[str] = mapped_column(String(20), default="completed")
    ci_job_id: Mapped[str | None] = mapped_column(String(50), comment="CI Job ID")
    ci_job_url: Mapped[str | None] = mapped_column(String(500), comment="CI Job URL")
    commit_sha: Mapped[str | None] = mapped_column(String(40), comment="Commit SHA")
    branch: Mapped[str | None] = mapped_column(String(100), comment="Branch Name")
    report_url: Mapped[str | None] = mapped_column(String(500), comment="Report Storage URL")
    scan_duration_seconds: Mapped[float | None] = mapped_column(Float, comment="Scan Duration (Seconds)")
    raw_json: Mapped[dict | None] = mapped_column(JSON)

    # created_by is inherited from TimestampMixin

    project: Mapped[Any] = relationship("GitLabProject", back_populates="dependency_scans")
    dependencies: Mapped[list[Dependency]] = relationship("Dependency", back_populates="scan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """返回依赖扫描记录的字符串表示。"""
        return f"<DependencyScan(id={self.id}, project_id={self.project_id}, status='{self.scan_status}')>"


class LicenseRiskRule(Base, TimestampMixin):
    """许可证风险规则配置表 (license_risk_rules)。

    用于定义不同开源许可证的合规性风险评级。
    """

    __tablename__ = "license_risk_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    license_name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    license_spdx_id: Mapped[str | None] = mapped_column(String(100))
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    is_copyleft: Mapped[bool] = mapped_column(Boolean, default=False)
    commercial_use_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    modification_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    distribution_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    patent_grant: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)
    policy_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        """返回许可证风险规则的字符串表示。"""
        return f"<LicenseRiskRule(name='{self.license_name}', risk='{self.risk_level}')>"


class Dependency(Base, TimestampMixin):
    """项目依赖清单表 (dependencies)。

    存储扫描发现的每一个具体的三方类库及其安全和合规状态。
    """

    __tablename__ = "dependencies"
    __table_args__ = (UniqueConstraint("scan_id", "package_name", "package_version", name="uq_dependency_scan_package"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[int] = mapped_column(Integer, ForeignKey("dependency_scans.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("gitlab_projects.id", ondelete="CASCADE"), nullable=False)
    package_name: Mapped[str] = mapped_column(String(500), nullable=False)
    package_version: Mapped[str | None] = mapped_column(String(100))
    package_manager: Mapped[str | None] = mapped_column(String(50))
    dependency_type: Mapped[str] = mapped_column(String(20), default="direct")
    license_name: Mapped[str | None] = mapped_column(String(200))
    license_spdx_id: Mapped[str | None] = mapped_column(String(100))
    license_url: Mapped[str | None] = mapped_column(Text)
    license_risk_level: Mapped[str | None] = mapped_column(String(20))
    has_vulnerabilities: Mapped[bool] = mapped_column(Boolean, default=False)
    highest_cvss_score: Mapped[float | None] = mapped_column(Float)
    critical_cve_count: Mapped[int] = mapped_column(Integer, default=0)
    high_cve_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_cve_count: Mapped[int] = mapped_column(Integer, default=0)
    low_cve_count: Mapped[int] = mapped_column(Integer, default=0)

    # 误报管理
    is_ignored: Mapped[bool] = mapped_column(Boolean, default=False)
    ignore_reason: Mapped[str | None] = mapped_column(Text)
    ignore_by: Mapped[str | None] = mapped_column(String(50))
    ignore_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    file_path: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    homepage_url: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    scan: Mapped[DependencyScan] = relationship("DependencyScan", back_populates="dependencies")
    project: Mapped[Any] = relationship("GitLabProject", back_populates="dependencies")
    cves: Mapped[list[DependencyCVE]] = relationship("DependencyCVE", back_populates="dependency", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """返回项目依赖的字符串表示。"""
        return f"<Dependency(name='{self.package_name}', version='{self.package_version}')>"


class DependencyCVE(Base, TimestampMixin):
    """CVE 漏洞详情表 (dependency_cves)。"""

    __tablename__ = "dependency_cves"
    __table_args__ = (UniqueConstraint("dependency_id", "cve_id", name="uq_dependency_cve"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dependency_id: Mapped[int] = mapped_column(Integer, ForeignKey("dependencies.id", ondelete="CASCADE"), nullable=False)
    cve_id: Mapped[str] = mapped_column(String(50), nullable=False)
    cvss_score: Mapped[float | None] = mapped_column(Float)
    cvss_vector: Mapped[str | None] = mapped_column(String(200))
    severity: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    published_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_modified_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fixed_version: Mapped[str | None] = mapped_column(String(100))
    remediation: Mapped[str | None] = mapped_column(Text)
    references: Mapped[list | dict | None] = mapped_column(JSON)

    # 误报管理
    is_ignored: Mapped[bool] = mapped_column(Boolean, default=False)
    ignore_reason: Mapped[str | None] = mapped_column(Text)

    dependency: Mapped[Dependency] = relationship("Dependency", back_populates="cves")

    def __repr__(self) -> str:
        """返回漏洞详情的字符串表示。"""
        return f"<DependencyCVE(cve_id='{self.cve_id}', severity='{self.severity}')>"
