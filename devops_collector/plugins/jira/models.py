import uuid
from datetime import datetime


"""Jira 数据模型

定义 Jira 相关的 SQLAlchemy ORM 模型，包括项目、看板、Sprint 和 Issue。
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devops_collector.models.base_models import Base, TimestampMixin, TraceabilityMixin, int_pk, json_dict


class JiraProject(Base, TimestampMixin, TraceabilityMixin):
    """Jira 项目模型 (jira_projects)。

    Attributes:
        id (int): 自增内部主键。
        key (str): Jira 项目的唯一标识符 (e.g. 'PROJ')。
        name (str): 项目名称。
        description (str): 项目描述。
        lead_name (str): 项目负责人。
        gitlab_project_id (int): 关联的 GitLab 项目 ID。
        last_synced_at (datetime): 最近同步时间。
        sync_status (str): 同步状态 (PENDING, SUCCESS, FAILED)。
        boards (List[JiraBoard]): 关联的看板列表。
        issues (List[JiraIssue]): 关联的问题列表。
    """

    __tablename__ = "jira_projects"
    id: Mapped[int_pk]
    key: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    lead_name: Mapped[str | None] = mapped_column(String(255))
    gitlab_project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("gitlab_projects.id"), nullable=True)
    gitlab_project: Mapped["GitLabProject | None"] = relationship("GitLabProject", back_populates="jira_projects")  # noqa: F821
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str | None] = mapped_column(String(20), default="PENDING")
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)
    boards: Mapped[list["JiraBoard"]] = relationship("JiraBoard", back_populates="project", cascade="all, delete-orphan")  # noqa: F821
    issues: Mapped[list["JiraIssue"]] = relationship("JiraIssue", back_populates="project", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<JiraProject(key='{self.key}', name='{self.name}')>"


class JiraBoard(Base, TimestampMixin, TraceabilityMixin):
    """Jira 看板模型 (jira_boards)。

    Attributes:
        id (int): Jira 原始 Board ID。
        project_id (int): 关联的 Jira 项目 ID。
        name (str): 看板名称。
        type (str): 看板类型 (kanban, scrum)。
        project (JiraProject): 关联的项目。
        sprints (List[JiraSprint]): 关联的迭代列表。
    """

    __tablename__ = "jira_boards"
    id: Mapped[int_pk]
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jira_projects.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(50))
    project: Mapped["JiraProject | None"] = relationship("JiraProject", back_populates="boards")  # noqa: F821
    sprints: Mapped[list["JiraSprint"]] = relationship("JiraSprint", back_populates="board", cascade="all, delete-orphan")  # noqa: F821
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
        return f"<JiraBoard(id={self.id}, name='{self.name}')>"


class JiraSprint(Base, TimestampMixin, TraceabilityMixin):
    """Jira Sprint (迭代) 模型 (jira_sprints)。

    Attributes:
        id (int): Jira 原始 Sprint ID。
        board_id (int): 关联的看板 ID。
        name (str): Sprint 名称。
        state (str): 状态 (active, closed, future)。
        start_date (datetime): 开始日期。
        end_date (datetime): 计划结束日期。
        complete_date (datetime): 实际完成日期。
        board (JiraBoard): 关联的看板。
        issues (List[JiraIssue]): 关联的问题列表。
    """

    __tablename__ = "jira_sprints"
    id: Mapped[int_pk]
    board_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jira_boards.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(20))
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    complete_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    board: Mapped["JiraBoard | None"] = relationship("JiraBoard", back_populates="sprints")  # noqa: F821
    issues: Mapped[list["JiraIssue"]] = relationship("JiraIssue", back_populates="sprint")  # noqa: F821
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
        return f"<JiraSprint(id={self.id}, name='{self.name}', state='{self.state}')>"


class JiraIssue(Base, TimestampMixin, TraceabilityMixin):
    """Jira Issue (问题/任务) 详情模型 (jira_issues)。

    Attributes:
        id (int): Jira 原始 Issue ID。
        key (str): 问题 Key (e.g. 'PROJ-123')。
        project_id (int): 所属项目 ID。
        sprint_id (int): 当前所属 Sprint ID。
        summary (str): 概要标题。
        description (str): 详细描述。
        status (str): 当前状态。
        priority (str): 优先级。
        issue_type (str): 类型 (Story, Bug, Task 等)。
        assignee_user_id (UUID): 负责人的 OneID。
        reporter_user_id (UUID): 报告人的 OneID。
        creator_user_id (UUID): 创建人的 OneID。
        reopening_count (int): 重开次数。
        time_to_first_response (int): 响应延迟 (秒)。
        original_estimate (int): 原始预估工时 (秒)。
        time_spent (int): 实际消耗工时 (秒)。
        labels (list): 标签列表 (JSON)。
        fix_versions (list): 修复版本列表 (JSON)。
    """

    __tablename__ = "jira_issues"
    id: Mapped[int_pk]
    key: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jira_projects.id"), nullable=False)
    sprint_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jira_sprints.id"), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[str | None] = mapped_column(String(50))
    issue_type: Mapped[str | None] = mapped_column(String(50))
    assignee_name: Mapped[str | None] = mapped_column(String(255))
    reporter_name: Mapped[str | None] = mapped_column(String(255))
    creator_name: Mapped[str | None] = mapped_column(String(255))
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=True)
    reporter_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=True)
    creator_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)
    first_commit_sha: Mapped[str | None] = mapped_column(String(100))
    first_fix_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reopening_count: Mapped[int | None] = mapped_column(Integer, default=0)
    time_to_first_response: Mapped[int | None] = mapped_column(BigInteger)
    original_estimate: Mapped[int | None] = mapped_column(BigInteger)
    time_spent: Mapped[int | None] = mapped_column(BigInteger)
    remaining_estimate: Mapped[int | None] = mapped_column(BigInteger)
    labels: Mapped[json_dict | None] = mapped_column(JSON)
    fix_versions: Mapped[json_dict | None] = mapped_column(JSON)
    project: Mapped["JiraProject | None"] = relationship("JiraProject", back_populates="issues")  # noqa: F821
    history: Mapped[list["JiraIssueHistory"]] = relationship("JiraIssueHistory", back_populates="issue", cascade="all, delete-orphan")  # noqa: F821
    sprint: Mapped["JiraSprint | None"] = relationship("JiraSprint", back_populates="issues")  # noqa: F821

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<JiraIssue(key='{self.key}', summary='{self.summary[:20]}...')>"


class JiraIssueHistory(Base, TimestampMixin, TraceabilityMixin):
    """Jira 问题变更历史表 (jira_issue_histories)。

    Attributes:
        id (str): Jira History ID。
        issue_id (int): 关联的问题 ID。
        author_name (str): 变更人名称。
        field (str): 变更字段。
        from_string (str): 变更前的值。
        to_string (str): 变更后的值。
    """

    __tablename__ = "jira_issue_histories"
    id: Mapped[str] = mapped_column(primary_key=True)
    issue_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("jira_issues.id"), nullable=False)
    author_name: Mapped[str | None] = mapped_column(String(100))
    field: Mapped[str | None] = mapped_column(String(100))
    from_string: Mapped[str | None] = mapped_column(Text)
    to_string: Mapped[str | None] = mapped_column(Text)
    issue: Mapped["JiraIssue | None"] = relationship("JiraIssue", back_populates="history")  # noqa: F821
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
        return f"<JiraIssueHistory(issue_id={self.issue_id}, field='{self.field}')>"
