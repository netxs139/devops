"""DevOps Collector Models Package

聚合核心数据模型。
插件模型应直接从插件包导入，或通过 plugin_loader 动态加载。

架构说明:
    - 第1层: base_models.py 定义公共基础模型
    - 第2层: 核心功能模块 (dependency)
    - 测试管理模型已迁移至独立的 test_module
"""

from .audit import AuditLog
from .base_models import (
    SLO,
    Base,
    BusinessSystem,
    Calendar,
    CommitMetrics,
    Company,
    ComplianceIssue,
    ContractPaymentNode,
    CostCode,
    DailyDevStats,
    EntityTopology,
    Incident,
    JenkinsTestExecution,
    LaborRateConfig,
    MetricDefinition,
    OKRKeyResult,
    OKRObjective,
    OwnableMixin,
    Product,
    ProjectMaster,
    ProjectProductRelation,
    PurchaseContract,
    RawDataMixin,
    RawDataStaging,
    ResourceCost,
    RevenueContract,
    Service,
    ServiceProjectMapping,
    SyncLog,
    SystemRegistry,
    TimestampMixin,
    TraceabilityLink,
    Vendor,
)
from .dependency import Dependency, DependencyCVE, DependencyScan, LicenseRiskRule
from .marts import DeveloperActivityProfile, DoraDashboardSummary
from .service_desk import ServiceDeskTicket


# --- 插件模型导入 (用于 SQLAlchemy 模型注册) ---

# GitLab
try:
    from devops_collector.plugins.gitlab.models import (
        GitLabBranch,
        GitLabCommit,
        GitLabDeployment,
        GitLabGroup,
        GitLabGroupMember,
        GitLabIssue,
        GitLabJob,
        GitLabMergeRequest,
        GitLabMergeRequestStateTransition,
        GitLabMilestone,
        GitLabNote,
        GitLabPackage,
        GitLabPipeline,
        GitLabProject,
        GitLabProjectMember,
        GitLabRelease,
        GitLabTag,
        GitLabVulnerability,
    )
except ImportError:
    pass

# SonarQube
try:
    from devops_collector.plugins.sonarqube.models import SonarIssue, SonarMeasure, SonarProject
except ImportError:
    pass

# ZenTao
try:
    from devops_collector.plugins.zentao.models import (
        ZenTaoAction,
        ZenTaoBuild,
        ZenTaoExecution,
        ZenTaoIssue,
        ZenTaoProduct,
        ZenTaoProductPlan,
        ZenTaoRelease,
        ZenTaoTestCase,
        ZenTaoTestResult,
    )
except ImportError:
    pass

# Jira
try:
    from devops_collector.plugins.jira.models import (
        JiraBoard,
        JiraIssue,
        JiraProject,
        JiraSprint,
    )
except ImportError:
    pass

# Nexus
try:
    from devops_collector.plugins.nexus.models import NexusAsset, NexusComponent
except ImportError:
    pass

# Jenkins
try:
    from devops_collector.plugins.jenkins.models import JenkinsBuild, JenkinsJob
except ImportError:
    pass

# JFrog
try:
    from devops_collector.plugins.jfrog.models import (
        JFrogArtifact,
        JFrogDependency,
        JFrogScan,
        JFrogVulnerabilityDetail,
    )
except ImportError:
    pass


__all__ = [
    "Base",
    "Calendar",
    "SyncLog",
    "RawDataStaging",
    "Product",
    "OKRObjective",
    "OKRKeyResult",
    "TraceabilityLink",
    "JenkinsTestExecution",
    "Incident",
    "ResourceCost",
    "Service",
    "ServiceProjectMapping",
    "SLO",
    "TimestampMixin",
    "RawDataMixin",
    "ProjectMaster",
    "ContractPaymentNode",
    "RevenueContract",
    "PurchaseContract",
    "MetricDefinition",
    "SystemRegistry",
    "EntityTopology",
    "Company",
    "Vendor",
    "ComplianceIssue",
    "CommitMetrics",
    "DailyDevStats",
    "OwnableMixin",
    "LaborRateConfig",
    "CostCode",
    "ProjectProductRelation",
    "BusinessSystem",
    "DependencyScan",
    "LicenseRiskRule",
    "Dependency",
    "DependencyCVE",
    "ServiceDeskTicket",
    "AuditLog",
    "DoraDashboardSummary",
    "DeveloperActivityProfile",
]

from . import events
from .audit_events import bind_audit_listeners


# 核心资产审计绑定 (等保三级合规要求)
# 仅对高敏感管理表启用字段级变更追踪，避免批量采集表产生审计风暴
bind_audit_listeners(
    [
        Product,
        ProjectMaster,
    ]
)

from .base_models import (
    IdentityMapping,
    Organization,
    SysMenu,
    SysRole,
    SysRoleDept,
    SysRoleMenu,
    Team,
    TeamMember,
    User,
    UserCredential,
    UserOAuthToken,
    UserRole,
)
