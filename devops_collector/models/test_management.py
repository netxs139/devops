from __future__ import annotations


"""GitLab 测试管理模块数据模型。

本模块定义了用于二开测试管理功能的核心模型，包括测试用例实体及其与 Issue 的关联关系。
遵循 GitLab 社区版二开建议书中的数据库设计原则。
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship
from sqlalchemy.sql import func

from devops_collector.models.base_models import Base, TimestampMixin, TraceabilityMixin, User


class GTMTestCase(Base, TimestampMixin, TraceabilityMixin):
    """GitLab 测试用例模型。

    存储测试用例的结构化信息，包括标题、描述（预置条件）和详细的执行步骤。
    """

    __tablename__ = "gtm_test_cases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("gitlab_projects.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=False)
    iid: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str | None] = mapped_column(String(20))
    test_type: Mapped[str | None] = mapped_column(String(50))
    pre_conditions: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    test_steps: Mapped[list | dict] = mapped_column(JSON, default=[])

    author: Mapped[User] = relationship(
        "User",
        primaryjoin=and_(User.global_user_id == author_id, User.is_current.is_(True)),
        back_populates="test_cases",
        overlaps="requirements,test_cases",
    )
    project: Mapped[Any] = relationship("GitLabProject", back_populates="test_cases")
    linked_issues: Mapped[list[Any]] = relationship("GitLabIssue", secondary="gtm_test_case_issue_links", back_populates="associated_test_cases")
    associated_requirements: Mapped[list[Any]] = relationship("GTMRequirement", secondary="gtm_requirement_test_case_links", back_populates="test_cases")

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
        primaryjoin=lambda: foreign(GTMTestExecutionRecord.test_case_iid) == GTMTestCase.iid,
        viewonly=True,
        overlaps="project",
    )

    def __repr__(self) -> str:
        """返回测试用例的字符串表示。"""
        return f"<GTMTestCase(iid={self.iid}, title='{self.title}')>"


class GTMTestCaseIssueLink(Base, TimestampMixin):
    """测试用例与 Issue 的关联表 (gtm_test_case_issue_links)。"""

    __tablename__ = "gtm_test_case_issue_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    test_case_id: Mapped[int] = mapped_column(Integer, ForeignKey("gtm_test_cases.id", ondelete="CASCADE"), nullable=False)
    issue_id: Mapped[int] = mapped_column(Integer, ForeignKey("gitlab_issues.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        """返回用例与 Issue 关联的字符串表示。"""
        return f"<GTMTestCaseIssueLink(tc={self.test_case_id}, issue={self.issue_id})>"


class GTMRequirement(Base, TimestampMixin):
    """GitLab 需求模型。"""

    __tablename__ = "gtm_requirements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("gitlab_projects.id", ondelete="CASCADE"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=False)
    iid: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), default="opened")

    author: Mapped[User] = relationship(
        "User",
        primaryjoin=and_(User.global_user_id == author_id, User.is_current.is_(True)),
        back_populates="requirements",
        overlaps="requirements,test_cases",
    )
    project: Mapped[Any] = relationship("GitLabProject", back_populates="requirements")
    test_cases: Mapped[list[GTMTestCase]] = relationship("GTMTestCase", secondary="gtm_requirement_test_case_links", back_populates="associated_requirements")
    linked_bugs = association_proxy("test_cases", "linked_issues")

    def __repr__(self) -> str:
        """返回需求的字符串表示。"""
        return f"<GTMRequirement(iid={self.iid}, title='{self.title}', state='{self.state}')>"


class GTMRequirementTestCaseLink(Base, TimestampMixin):
    """需求与测试用例的关联表 (gtm_requirement_test_case_links)。"""

    __tablename__ = "gtm_requirement_test_case_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_id: Mapped[int] = mapped_column(Integer, ForeignKey("gtm_requirements.id", ondelete="CASCADE"), nullable=False)
    test_case_id: Mapped[int] = mapped_column(Integer, ForeignKey("gtm_test_cases.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        """返回需求与用例关联的字符串表示。"""
        return f"<GTMRequirementTestCaseLink(req={self.requirement_id}, tc={self.test_case_id})>"


class GTMTestExecutionRecord(Base, TimestampMixin):
    """测试执行完整审计记录模型 (gtm_test_execution_records)。"""

    __tablename__ = "gtm_test_execution_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("gitlab_projects.id", ondelete="CASCADE"), nullable=False)
    test_case_iid: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    executor_name: Mapped[str | None] = mapped_column(String(100))
    executor_uid: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    comment: Mapped[str | None] = mapped_column(Text)
    pipeline_id: Mapped[int | None] = mapped_column(Integer)
    environment: Mapped[str | None] = mapped_column(String(50), default="Default")
    title: Mapped[str | None] = mapped_column(String(255))
    project: Mapped[Any] = relationship("GitLabProject", back_populates="test_execution_records")

    def __repr__(self) -> str:
        """返回执行记录的字符串表示。"""
        return f"<GTMTestExecutionRecord(iid={self.test_case_iid}, result={self.result})>"


# 动态挂载反向关联，规避 base_models 中的循环引用 NameError
User.test_cases = relationship("GTMTestCase", back_populates="author", primaryjoin=lambda: User.global_user_id == GTMTestCase.author_id)
User.requirements = relationship("GTMRequirement", back_populates="author", primaryjoin=lambda: User.global_user_id == GTMRequirement.author_id)
