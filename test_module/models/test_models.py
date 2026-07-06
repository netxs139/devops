"""Test Module Models

独立测试管理域的纯领域模型。
所有对外部领域（敏捷缺陷、IAM身份、项目主数据）的物理外键均已被重构为软引用（逻辑外键）。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from devops_collector.models.base_models import Base, TimestampMixin, TraceabilityMixin


class GTMTestCase(Base, TimestampMixin, TraceabilityMixin):
    """测试用例模型。

    存储测试用例的结构化信息，包括标题、描述（预置条件）和详细的执行步骤。
    """

    __tablename__ = "gtm_test_cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Soft references (跨域逻辑外键，无物理约束)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="软外键 -> gitlab_projects.id")
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, comment="软外键 -> mdm_identities.global_user_id")

    iid: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str | None] = mapped_column(String(20))
    test_type: Mapped[str | None] = mapped_column(String(50))
    pre_conditions: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    test_steps: Mapped[list | dict] = mapped_column(JSON, default=[])

    # Internal relationships (within test_module only)
    associated_requirements: Mapped[list[GTMRequirement]] = relationship(
        "GTMRequirement",
        secondary="gtm_requirement_test_case_links",
        back_populates="test_cases",
    )

    @hybrid_property
    def execution_count(self) -> int:
        """用例被执行的总次数。"""
        return len(self.execution_records)

    @execution_count.inplace.expression
    @classmethod
    def _execution_count_expression(cls):
        """用例被执行的总次数的 SQL 表达式。"""
        return func.count(GTMTestExecutionRecord.id).label("execution_count")

    execution_records: Mapped[list[GTMTestExecutionRecord]] = relationship(
        "GTMTestExecutionRecord",
        primaryjoin="foreign(GTMTestExecutionRecord.test_case_iid) == GTMTestCase.iid",
        viewonly=True,
    )

    def __repr__(self) -> str:
        """返回测试用例的字符串表示。"""
        return f"<GTMTestCase(iid={self.iid}, title='{self.title}')>"


class GTMTestCaseIssueLink(Base, TimestampMixin):
    """测试用例与缺陷(Issue)的关联表。"""

    __tablename__ = "gtm_test_case_issue_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Hard reference (internal)
    test_case_id: Mapped[int] = mapped_column(Integer, ForeignKey("gtm_test_cases.id", ondelete="CASCADE"), nullable=False)

    # Soft reference (external to agile issues)
    issue_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="软外键 -> gitlab_issues.id")

    def __repr__(self) -> str:
        """返回用例与 Issue 关联的字符串表示。"""
        return f"<GTMTestCaseIssueLink(tc={self.test_case_id}, issue={self.issue_id})>"


class GTMRequirement(Base, TimestampMixin):
    """测试需求模型。"""

    __tablename__ = "gtm_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Soft references
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="软外键 -> gitlab_projects.id")
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True, comment="软外键 -> mdm_identities.global_user_id")

    iid: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), default="opened")

    # Internal relationships
    test_cases: Mapped[list[GTMTestCase]] = relationship(
        "GTMTestCase",
        secondary="gtm_requirement_test_case_links",
        back_populates="associated_requirements",
    )

    def __repr__(self) -> str:
        """返回需求的字符串表示。"""
        return f"<GTMRequirement(iid={self.iid}, title='{self.title}', state='{self.state}')>"


class GTMRequirementTestCaseLink(Base, TimestampMixin):
    """需求与测试用例的关联表。"""

    __tablename__ = "gtm_requirement_test_case_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Hard references (internal to test_module)
    requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("gtm_requirements.id", ondelete="CASCADE"), nullable=False)
    test_case_id: Mapped[int] = mapped_column(Integer, ForeignKey("gtm_test_cases.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        """返回需求与用例关联的字符串表示。"""
        return f"<GTMRequirementTestCaseLink(req={self.requirement_id}, tc={self.test_case_id})>"


class GTMTestExecutionRecord(Base, TimestampMixin):
    """测试执行完整审计记录模型。"""

    __tablename__ = "gtm_test_execution_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Soft reference
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="软外键 -> gitlab_projects.id")

    test_case_iid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    executor_name: Mapped[str | None] = mapped_column(String(100))
    executor_uid: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    comment: Mapped[str | None] = mapped_column(Text)
    pipeline_id: Mapped[int | None] = mapped_column(Integer)
    environment: Mapped[str | None] = mapped_column(String(50), default="Default")
    title: Mapped[str | None] = mapped_column(String(255))

    def __repr__(self) -> str:
        """返回执行记录的字符串表示。"""
        return f"<GTMTestExecutionRecord(iid={self.test_case_iid}, result={self.result})>"
