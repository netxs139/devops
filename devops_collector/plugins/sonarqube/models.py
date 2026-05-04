import uuid
from datetime import datetime


"""SonarQube 数据模型

定义 SonarQube 相关的 SQLAlchemy ORM 模型。
"""

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, and_, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from devops_collector.models.base_models import Base, TimestampMixin, TraceabilityMixin, int_pk, json_dict


class SonarProject(Base, TimestampMixin, TraceabilityMixin):
    """SonarQube 项目模型 (sonar_projects)。

    存储 SonarQube 项目信息，支持与 GitLab 项目关联。

    Attributes:
        id (int): 自增主键。
        key (str): SonarQube 项目唯一标识 (e.g. com.example:my-project)。
        name (str): 项目显示名称。
        qualifier (str): 标识类型 (TRK=项目, BRC=分支, FIL=文件)。
        gitlab_project_id (int): 关联的 GitLab 项目 ID。
        last_analysis_date (datetime): 最后分析时间。
        last_synced_at (datetime): 最近同步时间。
        sync_status (str): 同步状态 (PENDING, SUCCESS, FAILED)。
        measures (List[SonarMeasure]): 关联的指标快照列表。
        issues (List[SonarIssue]): 关联的问题详情列表。
    """

    __tablename__ = "sonar_projects"
    id: Mapped[int_pk]
    key: Mapped[str | None] = mapped_column(String(500), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    qualifier: Mapped[str | None] = mapped_column(String(10))
    gitlab_project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("gitlab_projects.id"), nullable=True)
    # MDM 拓扑关联
    mdm_project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mdm_projects.id"), nullable=True, comment="关联的 MDM 项目 ID")
    mdm_product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("mdm_products.id"), nullable=True, comment="关联的 MDM 产品 ID")

    last_analysis_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str | None] = mapped_column(String(20), default="PENDING")
    gitlab_project: Mapped["GitLabProject | None"] = relationship("GitLabProject", back_populates="sonar_projects")  # noqa: F821
    measures: Mapped[list["SonarMeasure"]] = relationship("SonarMeasure", back_populates="project", cascade="all, delete-orphan")  # noqa: F821
    issues: Mapped[list["SonarIssue"]] = relationship("SonarIssue", back_populates="project", cascade="all, delete-orphan")  # noqa: F821
    latest_measure = relationship(
        "SonarMeasure",
        primaryjoin=lambda: and_(SonarProject.id == SonarMeasure.project_id),
        order_by=lambda: desc(SonarMeasure.analysis_date),
        viewonly=True,
        uselist=False,
    )

    @hybrid_property
    def bugs(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return self.latest_measure.bugs if self.latest_measure else 0

    @hybrid_property
    def vulnerabilities(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return self.latest_measure.vulnerabilities if self.latest_measure else 0

    @hybrid_property
    def coverage(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return self.latest_measure.coverage if self.latest_measure else 0.0

    @hybrid_property
    def quality_gate(self):
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return self.latest_measure.quality_gate_status if self.latest_measure else "UNKNOWN"

    @hybrid_property
    def is_clean(self):
        """质量门禁是否通过。"""
        return self.quality_gate == "OK"

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<SonarProject(key='{self.key}', name='{self.name}')>"


class SonarMeasure(Base, TimestampMixin, TraceabilityMixin):
    """SonarQube 指标快照模型 (sonar_measures)。

    每次代码分析后记录一条快照，用于追踪质量趋势。

    Attributes:
        id (int): 自增主键。
        project_id (int): 关联的 Sonar 项目 ID。
        analysis_date (datetime): 分析执行时间。
        files (int): 文件数。
        lines (int): 总行数。
        ncloc (int): 有效代码行数 (Non-Comment Lines of Code)。
        coverage (float): 代码覆盖率 (%)。
        bugs (int): Bug 总数。
        vulnerabilities (int): 漏洞总数。
        security_hotspots (int): 安全热点总数。
        code_smells (int): 代码异味数。
        sqale_index (int): 技术债务 (分钟)。
        complexity (int): 圈复杂度。
        reliability_rating (str): 可靠性评级 (A-E)。
        security_rating (str): 安全性评级 (A-E)。
        sqale_rating (str): 可维护性评级 (A-E)。
        quality_gate_status (str): 质量门禁状态 (OK, WARN, ERROR)。
        project (SonarProject): 关联的项目对象。
    """

    __tablename__ = "sonar_measures"
    id: Mapped[int_pk]
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sonar_projects.id"), nullable=False)
    analysis_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)
    files: Mapped[int | None] = mapped_column(Integer)
    lines: Mapped[int | None] = mapped_column(Integer)
    ncloc: Mapped[int | None] = mapped_column(Integer)
    classes: Mapped[int | None] = mapped_column(Integer)
    functions: Mapped[int | None] = mapped_column(Integer)
    statements: Mapped[int | None] = mapped_column(Integer)
    coverage: Mapped[float | None] = mapped_column(Float)
    bugs: Mapped[int | None] = mapped_column(Integer)
    bugs_blocker: Mapped[int | None] = mapped_column(Integer, default=0)
    bugs_critical: Mapped[int | None] = mapped_column(Integer, default=0)
    bugs_major: Mapped[int | None] = mapped_column(Integer, default=0)
    bugs_minor: Mapped[int | None] = mapped_column(Integer, default=0)
    bugs_info: Mapped[int | None] = mapped_column(Integer, default=0)
    vulnerabilities: Mapped[int | None] = mapped_column(Integer)
    vulnerabilities_blocker: Mapped[int | None] = mapped_column(Integer, default=0)
    vulnerabilities_critical: Mapped[int | None] = mapped_column(Integer, default=0)
    vulnerabilities_major: Mapped[int | None] = mapped_column(Integer, default=0)
    vulnerabilities_minor: Mapped[int | None] = mapped_column(Integer, default=0)
    vulnerabilities_info: Mapped[int | None] = mapped_column(Integer, default=0)
    security_hotspots: Mapped[int | None] = mapped_column(Integer)
    security_hotspots_high: Mapped[int | None] = mapped_column(Integer, default=0)
    security_hotspots_medium: Mapped[int | None] = mapped_column(Integer, default=0)
    security_hotspots_low: Mapped[int | None] = mapped_column(Integer, default=0)
    code_smells: Mapped[int | None] = mapped_column(Integer)
    comment_lines_density: Mapped[float | None] = mapped_column(Float)
    duplicated_lines_density: Mapped[float | None] = mapped_column(Float)
    sqale_index: Mapped[int | None] = mapped_column(Integer)
    sqale_debt_ratio: Mapped[float | None] = mapped_column(Float)
    complexity: Mapped[int | None] = mapped_column(Integer)
    cognitive_complexity: Mapped[int | None] = mapped_column(Integer)
    reliability_rating: Mapped[str | None] = mapped_column(String(1))
    security_rating: Mapped[str | None] = mapped_column(String(1))
    sqale_rating: Mapped[str | None] = mapped_column(String(1))

    # --- 增量代码 (New Code) 指标，用于流水线质量门禁 ---
    new_coverage: Mapped[float | None] = mapped_column(Float, comment="新增代码覆盖率")
    new_bugs: Mapped[int | None] = mapped_column(Integer, comment="新增 Bug 数")
    new_vulnerabilities: Mapped[int | None] = mapped_column(Integer, comment="新增漏洞数")
    new_reliability_rating: Mapped[str | None] = mapped_column(String(1), comment="新增可靠性评级")
    new_security_rating: Mapped[str | None] = mapped_column(String(1), comment="新增安全性评级")
    quality_gate_status: Mapped[str | None] = mapped_column(String(10))
    project: Mapped["SonarProject | None"] = relationship("SonarProject", back_populates="measures")  # noqa: F821

    @hybrid_property
    def dev_cost(self) -> int:
        """预测开发总人月成本。
        公式: ((sqale_index / 60) / (sqale_debt_ratio / 100)) / 174
        """
        # 拦截债务率为 0 或数据缺失的情况
        if not self.sqale_index or not self.sqale_debt_ratio or self.sqale_debt_ratio == 0:
            return 0

        # 计算总开发工时 (小时)
        total_dev_time_hours = (self.sqale_index / 60.0) / (self.sqale_debt_ratio / 100.0)
        # 转换为人月 (基准 174 小时/人月)
        return int(round(total_dev_time_hours / 174.0))

    @dev_cost.expression
    def dev_cost(cls):
        """SQL 级别的开发人月计算表达式。"""
        # 适配 PostgreSQL 的浮点数除法要求 (LL #78)
        from sqlalchemy import cast, func

        return func.round(cast((cast(cls.sqale_index, Float) / 60.0) / (cast(cls.sqale_debt_ratio, Float) / 100.0) / 174.0, Float))

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<SonarMeasure(project_id={self.project_id}, date='{self.analysis_date}')>"


class SonarIssue(Base, TimestampMixin, TraceabilityMixin):
    """SonarQube 问题详情模型 (sonar_issues)。

    Attributes:
        id (int): 自增主键。
        issue_key (str): 问题唯一标识。
        project_id (int): 关联的项目 ID。
        type (str): 类型 (BUG, VULNERABILITY, CODE_SMELL)。
        severity (str): 严重级别 (BLOCKER, CRITICAL, MAJOR, MINOR, INFO)。
        status (str): 状态 (OPEN, CONFIRMED, RESOLVED, CLOSED)。
        message (str): 问题描述。
        component (str): 文件路径。
        line (int): 行号。
        assignee_user_id (UUID): 负责人的 OneID。
        author_user_id (UUID): 作者的 OneID。
        project (SonarProject): 关联的项目对象。
    """

    __tablename__ = "sonar_issues"
    id: Mapped[int_pk]
    issue_key: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sonar_projects.id"), nullable=False)
    type: Mapped[str | None] = mapped_column(String(20))
    severity: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(String(20))
    resolution: Mapped[str | None] = mapped_column(String(20))
    rule: Mapped[str | None] = mapped_column(String(200))
    message: Mapped[str | None] = mapped_column(Text)
    component: Mapped[str | None] = mapped_column(String(500))
    line: Mapped[int | None] = mapped_column(Integer)
    effort: Mapped[str | None] = mapped_column(String(20))
    debt: Mapped[str | None] = mapped_column(String(20))
    creation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    update_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assignee: Mapped[str | None] = mapped_column(String(100))
    author: Mapped[str | None] = mapped_column(String(100))
    assignee_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=True)
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mdm_identities.global_user_id"), nullable=True)
    raw_data: Mapped[json_dict | None] = mapped_column(JSON)
    project: Mapped["SonarProject | None"] = relationship("SonarProject", back_populates="issues")  # noqa: F821

    def __repr__(self) -> str:
        '''"""TODO: Add description.

        Args:
            self: TODO

        Returns:
            TODO

        Raises:
            TODO
        """'''
        return f"<SonarIssue(key='{self.issue_key}', severity='{self.severity}')>"
