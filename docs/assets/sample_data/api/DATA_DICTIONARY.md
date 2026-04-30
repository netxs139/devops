# DevOps 效能平台 - 数据字典 (Data Dictionary)

> **生成时间**: 2026-04-30 01:29:09
> **版本**: v2.2 (企业级标准版)
> **状态**: 有效 (Active)

______________________________________________________________________

## 文档说明

本数据字典基于系统最新的 SQLAlchemy ORM 模型自动生成，确保与实际数据库结构的一致性。

### 文档结构

- **表名**: 数据库表的物理名称
- **模型类**: 对应的 Python ORM 模型类名
- **业务描述**: 从模型 Docstring 提取的业务用途说明
- **字段定义**: 包含字段名、类型、约束、可空性、默认值和业务说明
- **关系映射**: 表间 ORM 关系（一对多、多对一等）

### 字段注释规范

- 所有新增字段必须在模型定义中使用 `comment` 参数添加业务说明
- 枚举类型字段需列出所有可选值
- 外键字段需说明关联的业务实体

______________________________________________________________________

## 数据表清单

本系统共包含 **75 个数据表**，分为以下几个业务域:

### 核心主数据域

- `mdm_business_systems` - BusinessSystem
- `mdm_calendar` - Calendar
- `mdm_companies` - Company
- `mdm_compliance_issues` - ComplianceIssue
- `mdm_contract_payment_nodes` - ContractPaymentNode
- `mdm_cost_codes` - CostCode
- `mdm_entity_topology` - EntityTopology
- `mdm_epics` - EpicMaster
- `mdm_identities` - User
- `mdm_identity_mappings` - IdentityMapping
- `mdm_incidents` - Incident
- `mdm_labor_rate_config` - LaborRateConfig
- `mdm_locations` - Location
- `mdm_metric_definitions` - MetricDefinition
- `mdm_okr_key_results` - OKRKeyResult
- `mdm_okr_objectives` - OKRObjective
- `mdm_organizations` - Organization
- `mdm_products` - Product
- `mdm_projects` - ProjectMaster
- `mdm_purchase_contracts` - PurchaseContract
- `mdm_rel_project_product` - ProjectProductRelation
- `mdm_revenue_contracts` - RevenueContract
- `mdm_service_project_mapping` - ServiceProjectMapping
- `mdm_services` - Service
- `mdm_slo_definitions` - SLO
- `mdm_systems_registry` - SystemRegistry
- `mdm_traceability_links` - TraceabilityLink
- `mdm_vendors` - Vendor
- `stg_mdm_resource_costs` - ResourceCost

### 测试管理域

- `gtm_requirements` - GTMRequirement
- `gtm_test_case_issue_links` - GTMTestCaseIssueLink
- `gtm_test_cases` - GTMTestCase
- `gtm_test_execution_records` - GTMTestExecutionRecord
- `qa_jenkins_test_executions` - JenkinsTestExecution

### GitLab 集成域

- `gitlab_branches` - GitLabBranch
- `gitlab_commits` - GitLabCommit
- `gitlab_deployments` - GitLabDeployment
- `gitlab_group_members` - GitLabGroupMember
- `gitlab_groups` - GitLabGroup
- `gitlab_issues` - GitLabIssue
- `gitlab_merge_requests` - GitLabMergeRequest
- `gitlab_milestones` - GitLabMilestone
- `gitlab_notes` - GitLabNote
- `gitlab_packages` - GitLabPackage
- `gitlab_pipelines` - GitLabPipeline
- `gitlab_project_members` - GitLabProjectMember
- `gitlab_projects` - GitLabProject
- `gitlab_releases` - GitLabRelease
- `gitlab_tags` - GitLabTag

### 认证与授权域

- `sys_user_credentials` - UserCredential
- `sys_user_oauth_tokens` - UserOAuthToken
- `sys_user_roles` - UserRole

### 其他辅助域

- `dependencies` - Dependency
- `dependency_cves` - DependencyCVE
- `dependency_scans` - DependencyScan
- `jira_boards` - JiraBoard
- `jira_issues` - JiraIssue
- `jira_projects` - JiraProject
- `jira_sprints` - JiraSprint
- `license_risk_rules` - LicenseRiskRule
- `rpt_commit_metrics` - CommitMetrics
- `rpt_daily_dev_stats` - DailyDevStats
- `service_desk_tickets` - ServiceDeskTicket
- `sonar_issues` - SonarIssue
- `sonar_measures` - SonarMeasure
- `sonar_projects` - SonarProject
- `stg_raw_data` - RawDataStaging
- `sys_audit_logs` - AuditLog
- `sys_menu` - SysMenu
- `sys_role` - SysRole
- `sys_role_dept` - SysRoleDept
- `sys_role_menu` - SysRoleMenu
- `sys_sync_logs` - SyncLog
- `sys_team_members` - TeamMember
- `sys_teams` - Team

______________________________________________________________________

## 核心主数据域

### BusinessSystem (`mdm_business_systems`)

**业务描述**: 业务系统模型 (Backstage System Concept). 代表一组协作提供业务能力的组件集合 (如: 交易系统, 用户中心)。 它是微服务(Service)的聚合层级，用于界定架构边界和治理粒度。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `code` | String(255) | UNIQUE, INDEX | × | - | 系统标准代号 (如 trade-center) |
| `name` | String(100) | - | × | - | 系统中文名称 |
| `description` | Text | - | √ | - | 系统业务描述与边界定义 |
| `domain` | String(50) | INDEX | √ | - | 所属业务域 (如 电商/供应链/财务) |
| `status` | String(20) | - | √ | PRODUCTION | 生命周期状态 (PLANNING/DEV/PRODUCTION/DEPRECATED) |
| `rank` | String(10) | - | √ | T1 | 重要性分级 (T0/T1/T2/T3) |
| `architecture_type` | String(50) | - | √ | - | 架构类型 (Microservices/Monolith/Serverless) |
| `primary_tech_stack` | String(100) | - | √ | - | 主要技术栈 (如 Java/SpringCloud) |
| `dr_level` | String(50) | - | √ | - | 容灾等级要求 (双活/冷备/单点) |
| `owner_id` | UUID | FK | √ | - | 技术负责人 |
| `business_owner_id` | UUID | FK | √ | - | 业务负责人 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **services**: one-to-many -> `Service`
- **owner**: many-to-one -> `User`
- **business_owner**: many-to-one -> `User`

______________________________________________________________________

### Calendar (`mdm_calendar`)

**业务描述**: 公共日历/节假日参考表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `date_day` | Date | UNIQUE, INDEX | × | - | 日期 |
| `year_number` | Integer | INDEX | √ | - | 年份 |
| `month_number` | Integer | - | √ | - | 月份 (1-12) |
| `quarter_number` | Integer | - | √ | - | 季度 (1-4) |
| `day_of_week` | Integer | - | √ | - | 星期几 (1=周一, 7=周日) |
| `is_workday` | Boolean | - | √ | True | 是否工作日 |
| `is_holiday` | Boolean | - | √ | False | 是否节假日 |
| `holiday_name` | String(100) | - | √ | - | 节假日名称 |
| `fiscal_year` | String(20) | - | √ | - | 财年 |
| `fiscal_quarter` | String(20) | - | √ | - | 财务季度 |
| `week_of_year` | Integer | - | √ | - | 年内周数 |
| `season_tag` | String(20) | - | √ | - | 季节标签 (春/夏/秋/冬) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### Company (`mdm_companies`)

**业务描述**: 公司实体参考表 (Legal Entity)。 用于定义集团内的法律实体/纳税主体，支持财务核算和合同签署主体的管理。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `company_code` | String(50) | UNIQUE, INDEX | × | - | 公司唯一业务标识 (如 COM-BJ-01) |
| `name` | String(200) | - | × | - | 公司注册全称 |
| `short_name` | String(100) | - | √ | - | 公司简称 |
| `tax_id` | String(50) | UNIQUE, INDEX | √ | - | 统一社会信用代码/税号 |
| `currency` | String(10) | - | √ | CNY | 本位币种 (CNY/USD) |
| `fiscal_year_start` | String(10) | - | √ | 01-01 | 财年开始日期 (MM-DD) |
| `registered_address` | String(255) | - | √ | - | 注册地址 |
| `location_id` | Integer | FK, INDEX | √ | - | 主要办公地点ID |
| `is_active` | Boolean | - | √ | True | 是否存续经营 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **location**: many-to-one -> `Location`

______________________________________________________________________

### ComplianceIssue (`mdm_compliance_issues`)

**业务描述**: 合规风险与审计问题记录表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `issue_type` | String(50) | - | √ | - | 问题类型 (安全漏洞/许可证违规/合规缺失) |
| `severity` | String(20) | - | √ | - | 严重等级 (Critical/High/Medium/Low) |
| `entity_id` | String(100) | INDEX | √ | - | 关联实体ID (项目/服务) |
| `status` | String(20) | - | √ | OPEN | 状态 (OPEN/IN_REVIEW/RESOLVED/ACCEPTED) |
| `description` | Text | - | √ | - | 问题详情 |
| `metadata_payload` | JSON | - | √ | - | 额外元数据 (JSON) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### ContractPaymentNode (`mdm_contract_payment_nodes`)

**业务描述**: 合同付款节点/收款计划记录表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `contract_id` | Integer | FK, INDEX | × | - | 关联合同ID |
| `node_name` | String(200) | - | × | - | 节点名称 |
| `billing_percentage` | Numeric | - | √ | - | 收款比例 (%) |
| `billing_amount` | Numeric | - | √ | - | 收款金额 |
| `linked_system` | String(50) | - | √ | - | 关联系统 (gitlab/jira/manual) |
| `linked_milestone_id` | Integer | - | √ | - | 关联里程碑ID |
| `is_achieved` | Boolean | - | √ | False | 是否已达成 |
| `achieved_at` | DateTime | - | √ | - | 达成时间 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **contract**: many-to-one -> `RevenueContract`

______________________________________________________________________

### CostCode (`mdm_cost_codes`)

**业务描述**: 成本科目 (CBS) 模型。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `code` | String(50) | UNIQUE, INDEX | × | - | 科目编码 |
| `name` | String(200) | - | × | - | 科目名称 |
| `category` | String(50) | - | √ | - | 科目分类 (人力/硬件/软件/服务) |
| `description` | Text | - | √ | - | 科目描述 |
| `parent_id` | Integer | FK | √ | - | 上级科目ID |
| `default_capex_opex` | String(10) | - | √ | - | 默认CAPEX/OPEX属性 |
| `is_active` | Boolean | - | √ | True | 是否启用 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **parent**: many-to-one -> `CostCode`
- **children**: one-to-many -> `CostCode`

______________________________________________________________________

### EntityTopology (`mdm_entity_topology`)

**业务描述**: 实体-资源映射表 (Infrastructure Mapping). 将逻辑上的业务服务 (Service) 绑定到物理上的基础设施资源 (GitLab Repo, Sonar Project, Jenkins Job)。 它是连接 "业务架构" (Service) 与 "工具设施" (SystemRegistry) 的胶水层。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `service_id` | Integer | FK, INDEX | √ | - | 所属业务服务ID |
| `project_id` | Integer | FK, INDEX | √ | - | 所属项目ID |
| `system_id` | Integer | FK, INDEX | × | - | 来源系统物理ID (如 gitlab-corp 对应的 ID) |
| `external_resource_id` | String(100) | - | × | - | 外部资源唯一标识 (如 Project ID, Repo URL) |
| `resource_name` | String(200) | - | √ | - | 资源显示名称快照 (如 backend/payment-service) |
| `env_tag` | String(20) | - | √ | PROD | 环境标签 (PROD/UAT/TEST/DEV) |
| `element_type` | String(50) | - | √ | source-code | 资源类型 (source-code/ci-pipeline/k8s-deployment/db-instance) |
| `is_active` | Boolean | - | √ | True | 关联是否有效 |
| `last_verified_at` | DateTime | - | √ | - | 最后一次验证连接有效的时间 |
| `meta_info` | JSON | - | √ | - | 额外元数据连接信息 (JSON, 如 webhook_id, bind_key) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **service**: many-to-one -> `Service`
- **project**: many-to-one -> `ProjectMaster`
- **target_system**: many-to-one -> `SystemRegistry`

______________________________________________________________________

### EpicMaster (`mdm_epics`)

**业务描述**: 跨团队/长期史诗需求 (Epic) 主数据。 用于管理跨越多个迭代、涉及多个团队的战略级需求组件 (Initiatives/Epics)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `parent_id` | Integer | FK, INDEX | √ | - | 父级 Epic ID (支持多层级) |
| `epic_code` | String(50) | UNIQUE, INDEX | × | - | 史诗唯一编码 (如 EPIC-24Q1-001) |
| `title` | String(200) | - | × | - | 史诗标题 |
| `description` | Text | - | √ | - | 价值陈述与详细描述 |
| `status` | String(50) | - | √ | ANALYSIS | 状态 (ANALYSIS/BACKLOG/IN_PROGRESS/DONE/CANCELLED) |
| `priority` | String(20) | - | √ | P1 | 优先级 (P0-Strategic / P1-High) |
| `okr_objective_id` | Integer | FK, INDEX | √ | - | 关联战略目标ID |
| `investment_theme` | String(100) | - | √ | - | 投资主题 (如 技术债/新业务/合规/客户体验) |
| `budget_cap` | Numeric | - | √ | - | 预算上限 (人天或金额) |
| `owner_id` | UUID | FK, INDEX | √ | - | 史诗负责人 |
| `org_id` | Integer | FK, INDEX | √ | - | 负责人所属组织/部门ID |
| `start_date_is_fixed` | Boolean | - | √ | False | 是否固定开始时间 (False则自动继承子任务) |
| `due_date_is_fixed` | Boolean | - | √ | False | 是否固定结束时间 |
| `planned_start_date` | Date | - | √ | - | 计划开始日期 |
| `planned_end_date` | Date | - | √ | - | 计划完成日期 |
| `actual_start_date` | Date | - | √ | - | 实际开始日期 |
| `actual_end_date` | Date | - | √ | - | 实际完成日期 |
| `progress` | Numeric | - | √ | 0.0 | 总体进度 (0.0-1.0, 基于子任务聚合) |
| `color` | String(20) | - | √ | - | Roadmap展示颜色 (Hex Code) |
| `is_confidential` | Boolean | - | √ | False | 是否机密 Epic |
| `web_url` | String(255) | - | √ | - | GitLab 原始链接 |
| `external_id` | String(50) | - | √ | - | 外部系统ID (如 GitLab Epic IID) |
| `involved_teams` | JSON | - | √ | - | 涉及团队列表 (JSON List) |
| `tags` | JSON | - | √ | - | 标签 (JSON List) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **owner**: many-to-one -> `User`
- **organization**: many-to-one -> `Organization`
- **okr_objective**: many-to-one -> `OKRObjective`
- **parent**: many-to-one -> `EpicMaster`
- **children**: one-to-many -> `EpicMaster`

______________________________________________________________________

### User (`mdm_identities`)

**业务描述**: 全局用户映射表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `global_user_id` | UUID | PK | × | (auto) | 全局唯一用户标识 |
| `employee_id` | String(50) | UNIQUE, INDEX | √ | - | HR系统工号 |
| `username` | String(100) | - | √ | - | 登录用户名 |
| `full_name` | String(200) | - | √ | - | 用户姓名 |
| `primary_email` | String(255) | UNIQUE, INDEX | √ | - | 主邮箱地址 |
| `department_id` | Integer | FK, INDEX | √ | - | 所属部门ID |
| `position` | String(100) | - | √ | - | 职位/岗位名称 |
| `hr_relationship` | String(50) | - | √ | - | 人事关系 (如：正式/外协/实习) |
| `location_id` | Integer | FK, INDEX | √ | - | 常驻办公地点ID |
| `source_system` | String(50) | - | √ | - | 创建/更新来源系统 |
| `correlation_id` | String(100) | INDEX | √ | - | 关联的同步任务追踪 ID |
| `is_active` | Boolean | - | √ | True | 是否在职 |
| `is_survivor` | Boolean | - | √ | False | 是否通过合并保留的账号 |
| `total_eloc` | Numeric | - | √ | 0.0 | 累计有效代码行数 |
| `eloc_rank` | Integer | - | √ | 0 | ELOC排名 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **location**: many-to-one -> `Location`
- **department**: many-to-one -> `Organization`
- **managed_organizations**: one-to-many -> `Organization`
- **identities**: one-to-many -> `IdentityMapping`
- **roles**: one-to-many -> `SysRole`
- **test_cases**: one-to-many -> `GTMTestCase`
- **requirements**: one-to-many -> `GTMRequirement`
- **managed_products_as_pm**: one-to-many -> `Product`
- **managed_products_as_dev**: one-to-many -> `Product`
- **managed_products_as_qa**: one-to-many -> `Product`
- **managed_products_as_release**: one-to-many -> `Product`
- **project_memberships**: one-to-many -> `GitLabProjectMember`
- **team_memberships**: one-to-many -> `TeamMember`
- **credential**: many-to-one -> `UserCredential`

______________________________________________________________________

### IdentityMapping (`mdm_identity_mappings`)

**业务描述**: 外部身份映射表，连接 MDM 用户与第三方系统账号。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `global_user_id` | UUID | FK, INDEX | √ | - | 全局用户ID |
| `source_system` | String(50) | INDEX | × | - | 来源系统 (gitlab/jira/sonar) |
| `external_user_id` | String(100) | - | × | - | 外部系统用户ID |
| `external_username` | String(100) | - | √ | - | 外部系统用户名 |
| `external_email` | String(100) | - | √ | - | 外部系统邮箱 |
| `mapping_status` | String(20) | - | √ | VERIFIED | 映射状态 (VERIFIED/PENDING/REJECTED) |
| `confidence_score` | Numeric | - | √ | 1.0 | 匹配置信度 (0.0-1.0) |
| `last_active_at` | DateTime | - | √ | - | 最后活跃时间 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **user**: many-to-one -> `User`

______________________________________________________________________

### Incident (`mdm_incidents`)

**业务描述**: 线上事故/线上问题记录表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `title` | String(200) | - | × | - | 事故标题 |
| `description` | Text | - | √ | - | 事故详细描述 |
| `severity` | String(20) | - | √ | - | 严重等级 (P0/P1/P2/P3) |
| `status` | String(20) | - | √ | OPEN | 状态 (OPEN:处理中 / RESOLVED:已恢复 / CLOSED:已结单 / MONITORING:观察中) |
| `occurred_at` | DateTime | - | √ | - | 故障发生时间 (用于计算 TTI: Time to Impact) |
| `detected_at` | DateTime | - | √ | - | 故障发现时间 (用于计算 MTTD: Time to Detect) |
| `resolved_at` | DateTime | - | √ | - | 业务恢复时间 (用于计算 MTTR: Time to Restore) |
| `location_id` | Integer | FK, INDEX | √ | - | 故障发生地点ID |
| `root_cause_category` | String(50) | - | √ | - | 根因分类 (Code Change/Config Change/Capacity/Infrastructure/Exteanl) |
| `post_mortem_url` | String(255) | - | √ | - | 复盘报告链接 (Confluence/Doc URL) |
| `affected_users` | Integer | - | √ | - | 受影响用户数量预估 |
| `financial_loss` | Numeric | - | √ | 0.0 | 预估经济损失金额 (CNY) |
| `owner_id` | UUID | FK, INDEX | √ | - | 主责任人 |
| `project_id` | Integer | FK, INDEX | √ | - | 关联项目ID |
| `service_id` | Integer | FK, INDEX | √ | - | 故障服务ID |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **location**: many-to-one -> `Location`
- **owner**: many-to-one -> `User`
- **project**: many-to-one -> `ProjectMaster`
- **service**: many-to-one -> `Service`

______________________________________________________________________

### LaborRateConfig (`mdm_labor_rate_config`)

**业务描述**: 人工标准费率配置表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `job_title_level` | String(50) | - | × | - | 职级 (P5/P6/P7/M1/M2) |
| `daily_rate` | Numeric | - | × | - | 日费率 (元) |
| `hourly_rate` | Numeric | - | √ | - | 时费率 (元) |
| `currency` | String(10) | - | √ | CNY | 币种 |
| `effective_date` | DateTime | - | √ | - | 生效日期 |
| `is_active` | Boolean | - | √ | True | 是否启用 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### Location (`mdm_locations`)

**业务描述**: 地理位置或机房位置参考表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `location_code` | String(50) | UNIQUE, INDEX | √ | - | 位置唯一业务标识 (如 LOC_BJ_01) |
| `code` | String(20) | INDEX | √ | - | 行政区划或业务编码 (如 CN-GD, 440000) |
| `location_name` | String(200) | - | × | - | 位置名称 (如 广东省) |
| `short_name` | String(50) | - | √ | - | 简称 (如 广东) |
| `location_type` | String(50) | - | √ | - | 位置类型 (country/province/city/site/datacenter) |
| `parent_id` | Integer | FK | √ | - | 上级位置物理ID |
| `region` | String(50) | - | √ | - | 区域 (华北/华东/华南) |
| `is_active` | Boolean | - | √ | True | 是否启用 |
| `manager_user_id` | UUID | FK | √ | - | 负责人 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### MetricDefinition (`mdm_metric_definitions`)

**业务描述**: 指标语义定义表 (mdm_metric_definitions)。 这是 "指标字典" 的核心，确保全集团计算逻辑一致 (Single Source of Truth)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `metric_code` | String(100) | UNIQUE, INDEX | × | - | 指标唯一编码 (如 DORA_MTTR_PROD) |
| `metric_name` | String(200) | - | × | - | 指标展示名称 (如 生产环境平均修复时间) |
| `domain` | String(50) | - | × | - | 所属业务域 (DEVOPS/FINANCE/OPERATION) |
| `metric_type` | String(50) | - | √ | - | 指标类型 (ATOMIC:原子指标 / DERIVED:派生指标 / COMPOSITE:复合指标) |
| `calculation_logic` | Text | - | √ | - | 计算逻辑说明 (SQL公式或自然语言描述) |
| `unit` | String(50) | - | √ | - | 度量单位 (%, ms, Hours, Count, CNY) |
| `aggregate_type` | String(20) | - | √ | - | 聚合方式 (SUM, AVG, COUNT, MAX, MIN) |
| `source_model` | String(200) | - | √ | - | 来源数据模型 (关联 dbt 模型或数据库表名) |
| `dimension_scope` | JSON | - | √ | - | 允许下钻的维度列表 (JSON List, 如 ["dept", "application", "priority"]) |
| `is_standard` | Boolean | - | √ | True | 是否集团标准指标 (True: 锁定口径, 不允许随意修改) |
| `business_owner_id` | UUID | FK, INDEX | √ | - | 业务负责人 |
| `technical_owner_id` | UUID | FK, INDEX | √ | - | 技术负责人 |
| `time_grain` | String(50) | - | √ | - | 统计时间粒度 (Daily, Weekly, Monthly) |
| `update_cycle` | String(50) | - | √ | - | 数据刷新周期 (Realtime, T+1, Hourly) |
| `status` | String(50) | - | √ | RELEASED | 生命周期状态 (DRAFT:草稿 / RELEASED:已发布 / DEPRECATED:已废弃) |
| `is_active` | Boolean | - | √ | True | 是否启用 (逻辑删除标志) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **business_owner**: many-to-one -> `User`
- **technical_owner**: many-to-one -> `User`

______________________________________________________________________

### OKRKeyResult (`mdm_okr_key_results`)

**业务描述**: OKR 关键结果 (KR) 定义表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `objective_id` | Integer | FK, INDEX | × | - | 关联目标ID |
| `title` | String(255) | - | × | - | KR标题 |
| `target_value` | Numeric | - | × | - | 目标值 |
| `initial_value` | Numeric | - | √ | 0.0 | 初始基线值 |
| `current_value` | Numeric | - | √ | 0.0 | 当前值 |
| `metric_unit` | String(20) | - | √ | - | 单位 (%/天/个) |
| `weight` | Numeric | - | √ | 1.0 | 权重 |
| `owner_id` | UUID | FK, INDEX | √ | - | 负责人 |
| `progress` | Numeric | - | √ | 0.0 | 进度 (0.0-1.0) |
| `linked_metrics_config` | JSON | - | √ | - | 关联度量配置 (JSON) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **objective**: many-to-one -> `OKRObjective`
- **owner**: many-to-one -> `User`

______________________________________________________________________

### OKRObjective (`mdm_okr_objectives`)

**业务描述**: OKR 目标定义表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `objective_id` | String(50) | UNIQUE, INDEX | √ | - | 目标唯一标识 |
| `title` | String(255) | - | × | - | 目标标题 |
| `description` | Text | - | √ | - | 目标描述 |
| `period` | String(20) | INDEX | √ | - | 周期 (2024-Q1/2024-H1) |
| `owner_id` | UUID | FK, INDEX | √ | - | 负责人 |
| `org_id` | Integer | FK, INDEX | √ | - | 所属组织ID |
| `parent_id` | Integer | FK, INDEX | √ | - | 上级目标ID |
| `product_id` | Integer | FK, INDEX | √ | - | 关联产品ID |
| `status` | String(20) | - | √ | ACTIVE | 状态 (ACTIVE/COMPLETED/ABANDONED) |
| `progress` | Numeric | - | √ | 0.0 | 进度 (0.0-1.0) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **owner**: many-to-one -> `User`
- **organization**: many-to-one -> `Organization`
- **parent**: many-to-one -> `OKRObjective`
- **product**: many-to-one -> `Product`
- **key_results**: one-to-many -> `OKRKeyResult`
- **children**: one-to-many -> `OKRObjective`

______________________________________________________________________

### Organization (`mdm_organizations`)

**业务描述**: 组织架构表，支持 SCD Type 2 生命周期管理。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `org_code` | String(100) | INDEX | × | - | 组织唯一标识 (HR系统同步) |
| `org_name` | String(200) | - | × | - | 组织名称 |
| `org_level` | Integer | - | √ | 1 | 组织层级 (1=公司, 2=部门, 3=团队) |
| `parent_id` | Integer | FK, INDEX | √ | - | 上级组织ID |
| `manager_user_id` | UUID | FK, INDEX | √ | - | 部门负责人 |
| `manager_raw_id` | String(100) | - | √ | - | 负责人原始标识(工号/WeCom ID/LDAP ID/邮箱) |
| `is_active` | Boolean | - | √ | True | 是否启用 |
| `cost_center` | String(100) | - | √ | - | 成本中心编码 |
| `business_line` | String(50) | - | √ | - | 所属业务线/体系 (如 研发体系/交付体系/营销体系) |
| `source_system` | String(50) | - | √ | - | 创建/更新来源系统 (如 wecom/zentao) |
| `correlation_id` | String(100) | INDEX | √ | - | 关联的同步任务追踪 ID |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **parent**: many-to-one -> `Organization`
- **manager**: many-to-one -> `User`
- **users**: one-to-many -> `User`
- **products**: one-to-many -> `Product`
- **gitlab_projects**: one-to-many -> `GitLabProject`
- **children**: one-to-many -> `Organization`
- **roles**: one-to-many -> `SysRole`

______________________________________________________________________

### Product (`mdm_products`)

**业务描述**: 产品主数据表 (mdm_product)。 支持 SCD Type 2，记录产品生命周期状态、负责人变更及规格调整的历史轨迹。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `product_code` | String(100) | UNIQUE, INDEX | × | - | 产品业务唯一标识 |
| `product_name` | String(255) | - | × | - | 产品名称 |
| `product_description` | Text | - | × | - | 产品描述 |
| `category` | String(100) | - | √ | - | 产品分类 (平台/应用/组件) |
| `version_schema` | String(50) | - | × | - | 版本命名规则 (SemVer/CalVer) |
| `specification` | JSON | - | √ | - | 产品规格配置 (JSON) |
| `runtime_env` | JSON | - | √ | - | 运行环境配置 (JSON) |
| `checksum` | String(255) | - | √ | - | 最新版本校验码 |
| `lifecycle_status` | String(50) | - | √ | Active | 生命周期状态 (Active/Deprecated/EOL) |
| `repo_url` | String(255) | - | √ | - | 主代码仓库URL |
| `artifact_path` | String(255) | - | √ | - | 制品存储路径 |
| `owner_team_id` | Integer | FK, INDEX | √ | - | 负责团队ID |
| `product_manager_id` | UUID | FK, INDEX | √ | - | 产品经理 |
| `dev_lead_id` | UUID | FK, INDEX | √ | - | 开发经理 |
| `qa_lead_id` | UUID | FK, INDEX | √ | - | 测试经理 |
| `release_lead_id` | UUID | FK, INDEX | √ | - | 发布经理 |
| `matching_patterns` | JSON | - | √ | - | 自动识别匹配模式列表 (JSON) |
| `parent_product_id` | Integer | FK, INDEX | √ | - | 上级产品ID |
| `node_type` | String(20) | - | √ | APP | 节点类型 (LINE=产品线 / APP=应用) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **parent**: many-to-one -> `Product`
- **owner_team**: many-to-one -> `Organization`
- **product_manager**: many-to-one -> `User`
- **dev_lead**: many-to-one -> `User`
- **qa_lead**: many-to-one -> `User`
- **release_lead**: many-to-one -> `User`
- **project_relations**: one-to-many -> `ProjectProductRelation`
- **children**: one-to-many -> `Product`
- **objectives**: one-to-many -> `OKRObjective`

______________________________________________________________________

### ProjectMaster (`mdm_projects`)

**业务描述**: 项目全生命周期主数据 (mdm_projects)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `project_code` | String(100) | UNIQUE, INDEX | × | - | 项目业务唯一标识 |
| `project_name` | String(200) | - | × | - | 项目名称 |
| `project_type` | String(50) | - | √ | - | 项目类型 (研发项目/运维项目/POC) |
| `status` | String(50) | - | √ | PLAN | 项目状态 (PLAN/ACTIVE/SUSPENDED/CLOSED) |
| `is_active` | Boolean | - | √ | True | 是否启用 |
| `pm_user_id` | UUID | FK, INDEX | √ | - | 项目经理 |
| `product_owner_id` | UUID | FK, INDEX | √ | - | 产品经理 |
| `dev_lead_id` | UUID | FK, INDEX | √ | - | 开发经理 |
| `qa_lead_id` | UUID | FK, INDEX | √ | - | 测试经理 |
| `release_lead_id` | UUID | FK, INDEX | √ | - | 发布经理 |
| `org_id` | Integer | FK, INDEX | √ | - | 负责部门ID |
| `location_id` | Integer | FK, INDEX | √ | - | 项目所属/实施地点ID |
| `plan_start_date` | Date | - | √ | - | 计划开始日期 |
| `plan_end_date` | Date | - | √ | - | 计划结束日期 |
| `actual_start_at` | DateTime | - | √ | - | 实际开始时间 |
| `actual_end_at` | DateTime | - | √ | - | 实际结束时间 |
| `external_id` | String(100) | UNIQUE | √ | - | 外部系统项目ID |
| `system_id` | Integer | FK, INDEX | √ | - | 数据来源系统 |
| `budget_code` | String(100) | - | √ | - | 预算编码 |
| `budget_type` | String(50) | - | √ | - | 预算类型 (CAPEX/OPEX) |
| `lead_repo_id` | Integer | - | √ | - | 主代码仓库ID |
| `description` | Text | - | √ | - | 项目描述 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **organization**: many-to-one -> `Organization`
- **project_manager**: many-to-one -> `User`
- **product_owner**: many-to-one -> `User`
- **dev_lead**: many-to-one -> `User`
- **qa_lead**: many-to-one -> `User`
- **release_lead**: many-to-one -> `User`
- **source_system**: many-to-one -> `SystemRegistry`
- **gitlab_repos**: one-to-many -> `GitLabProject`
- **product_relations**: one-to-many -> `ProjectProductRelation`

______________________________________________________________________

### PurchaseContract (`mdm_purchase_contracts`)

**业务描述**: 采购/支出合同主数据。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `contract_no` | String(100) | UNIQUE, INDEX | × | - | 合同编号 |
| `title` | String(255) | - | √ | - | 合同标题 |
| `vendor_name` | String(255) | - | √ | - | 供应商名称 |
| `vendor_id` | String(100) | - | √ | - | 供应商ID |
| `total_amount` | Numeric | - | √ | 0.0 | 合同总额 |
| `currency` | String(10) | - | √ | CNY | 币种 |
| `start_date` | Date | - | √ | - | 合同开始日期 |
| `end_date` | Date | - | √ | - | 合同结束日期 |
| `cost_code_id` | Integer | FK, INDEX | √ | - | 成本科目ID |
| `capex_opex_flag` | String(10) | - | √ | - | CAPEX/OPEX标志 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **cost_code**: many-to-one -> `CostCode`

______________________________________________________________________

### ProjectProductRelation (`mdm_rel_project_product`)

**业务描述**: 项目与产品的关联权重表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `project_id` | Integer | FK, INDEX | × | - | 项目ID |
| `org_id` | Integer | FK, INDEX | × | - | 所属组织ID |
| `product_id` | Integer | FK, INDEX | × | - | 产品ID |
| `relation_type` | String(50) | - | √ | PRIMARY | 关联类型 (PRIMARY/SECONDARY) |
| `allocation_ratio` | Numeric | - | √ | 1.0 | 工作量分配比例 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **project**: many-to-one -> `ProjectMaster`
- **product**: many-to-one -> `Product`

______________________________________________________________________

### RevenueContract (`mdm_revenue_contracts`)

**业务描述**: 销售/收入合同主数据表格。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `contract_no` | String(100) | UNIQUE, INDEX | × | - | 合同编号 |
| `title` | String(255) | - | √ | - | 合同标题 |
| `client_name` | String(255) | - | √ | - | 客户名称 |
| `total_value` | Numeric | - | √ | 0.0 | 合同总额 |
| `currency` | String(10) | - | √ | CNY | 币种 |
| `sign_date` | Date | - | √ | - | 签约日期 |
| `product_id` | Integer | FK, INDEX | √ | - | 关联产品ID |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **product**: many-to-one -> `Product`
- **payment_nodes**: one-to-many -> `ContractPaymentNode`

______________________________________________________________________

### ServiceProjectMapping (`mdm_service_project_mapping`)

**业务描述**: 服务与工程项目的多对多关联映射表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `service_id` | Integer | FK, INDEX | × | - | 服务ID |
| `source` | String(50) | - | √ | - | 项目来源系统 (gitlab/jira) |
| `project_id` | Integer | - | √ | - | 外部项目ID |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **service**: many-to-one -> `Service`

______________________________________________________________________

### Service (`mdm_services`)

**业务描述**: 服务/组件目录表 (Extended with Backstage Component Model). 支持 SCD Type 2，记录服务定级 (Tier)、生命周期 (Lifecycle) 及归属权的历史演进。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `name` | String(200) | - | × | - | 服务名称 |
| `tier` | String(20) | - | √ | - | 服务级别 (T0/T1/T2/T3) |
| `org_id` | Integer | FK | √ | - | 负责组织ID |
| `description` | Text | - | √ | - | 服务描述 |
| `system_id` | Integer | FK | √ | - | 所属业务系统ID |
| `lifecycle` | String(20) | - | √ | production | 生命周期 (experimental/production/deprecated) |
| `component_type` | String(20) | - | √ | service | 组件类型 (service/library/website/tool) |
| `tags` | JSON | - | √ | - | 标签列表 (JSON) |
| `links` | JSON | - | √ | - | 相关链接 (JSON) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **system**: many-to-one -> `BusinessSystem`
- **organization**: many-to-one -> `Organization`
- **costs**: one-to-many -> `ResourceCost`
- **slos**: one-to-many -> `SLO`
- **project_mappings**: one-to-many -> `ServiceProjectMapping`
- **resources**: one-to-many -> `EntityTopology`

______________________________________________________________________

### SLO (`mdm_slo_definitions`)

**业务描述**: SLO (服务水平目标) 定义表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `service_id` | Integer | FK, INDEX | × | - | 关联服务ID |
| `name` | String(100) | - | × | - | SLO 名称 |
| `indicator_type` | String(50) | - | √ | - | 指标类型 (Availability/Latency/Throughput) |
| `target_value` | Numeric | - | √ | - | 目标值 |
| `metric_unit` | String(20) | - | √ | - | 度量单位 (%/ms) |
| `time_window` | String(20) | - | √ | - | 统计窗口期 (28d/7d) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **service**: many-to-one -> `Service`

______________________________________________________________________

### SystemRegistry (`mdm_systems_registry`)

**业务描述**: 三方系统注册表，记录对接的所有外部系统 (GitLab, Jira, Sonar 等)。 作为数据源治理注册中心，定义了连接方式、同步策略及数据治理属性。 - 用于管理 Collector 采集目标 - 用于 Issue Tracking 集成配置 支持 SCD Type 2 以审计连接配置的变更记录。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `system_code` | String(50) | UNIQUE, INDEX | × | - | 系统唯一标准代号 (如 gitlab-corp) |
| `system_name` | String(100) | - | × | - | 系统显示名称 |
| `system_type` | String(50) | - | √ | - | 工具类型 (VCS/TICKET/CI/SONAR/K8S) |
| `env_tag` | String(20) | - | √ | PROD | 环境标签 (PROD/Stage/Test) |
| `base_url` | String(255) | - | √ | - | API 基础地址 (Base URL) |
| `api_version` | String(20) | - | √ | - | API 接口版本 (如 v4, api/v2) |
| `auth_type` | String(50) | - | √ | - | 认证方式 (OAuth2/Token/Basic) |
| `credential_key` | String(100) | - | √ | - | 凭证引用Key (指向Vault或Env Var) |
| `plugin_config` | JSON | - | √ | - | 插件特定配置 (JSON, 如过滤规则、超时设置) |
| `sync_method` | String(50) | - | √ | - | 同步方式 (CDC/Polling/Webhook) |
| `update_cycle` | String(50) | - | √ | - | 更新频率 (Realtime/Hourly/Daily) |
| `enabled_plugins` | String(255) | - | √ | - | 启用的采集插件列表 (逗号分隔) |
| `data_sensitivity` | String(20) | - | √ | - | 数据敏感级 (L1-L4) |
| `sla_level` | String(20) | - | √ | - | 服务等级 (P0-Critical / P1-High) |
| `technical_owner_id` | UUID | FK, INDEX | √ | - | 技术负责人 |
| `is_active` | Boolean | - | √ | True | 是否启用采集 |
| `last_heartbeat` | DateTime | - | √ | - | 最后连通性检查时间 |
| `last_sync_at` | DateTime | - | √ | - | 最后一次数据同步时间 |
| `remarks` | Text | - | √ | - | 备注说明 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **technical_owner**: many-to-one -> `User`
- **projects**: one-to-many -> `ProjectMaster`

______________________________________________________________________

### TraceabilityLink (`mdm_traceability_links`)

**业务描述**: 跨系统追溯链路表，连接需求与代码、测试与发布。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `source_system` | String(50) | - | √ | - | 源系统 (jira/gitlab) |
| `source_type` | String(50) | - | √ | - | 源实体类型 (requirement/story) |
| `source_id` | String(100) | INDEX | √ | - | 源实体ID |
| `target_system` | String(50) | - | √ | - | 目标系统 (gitlab/jenkins) |
| `target_type` | String(50) | - | √ | - | 目标实体类型 (commit/merge_request/build) |
| `target_id` | String(100) | INDEX | √ | - | 目标实体ID |
| `link_type` | String(50) | - | √ | - | 链路类型 (implements/tests/deploys) |
| `raw_data` | JSON | - | √ | - | 原始关联数据 (JSON) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### Vendor (`mdm_vendors`)

**业务描述**: 外部供应商主数据表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `vendor_code` | String(50) | UNIQUE, INDEX | × | - | 供应商唯一业务编码 |
| `name` | String(200) | - | × | - | 供应商全称 |
| `short_name` | String(100) | - | √ | - | 供应商简称 |
| `category` | String(50) | - | √ | - | 供应商类别 (人力外包/软件许可/云服务/硬件) |
| `status` | String(20) | - | √ | ACTIVE | 合作状态 (ACTIVE/BLACKLIST/INACTIVE) |
| `tax_id` | String(50) | - | √ | - | 统一社会信用代码/税号 |
| `payment_terms` | String(100) | - | √ | - | 默认账期 (e.g. Net 30, Net 60) |
| `currency` | String(10) | - | √ | CNY | 默认结算币种 |
| `contact_person` | String(100) | - | √ | - | 主要联系人 |
| `contact_email` | String(100) | - | √ | - | 联系邮箱 |
| `contact_phone` | String(50) | - | √ | - | 联系电话 |
| `rating` | Numeric | - | √ | 0.0 | 供应商绩效评分 (0-5) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

______________________________________________________________________

### ResourceCost (`stg_mdm_resource_costs`)

**业务描述**: 资源成本记录明细表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `service_id` | Integer | FK, INDEX | √ | - | 关联服务ID |
| `cost_code_id` | Integer | FK, INDEX | √ | - | 成本科目ID |
| `purchase_contract_id` | Integer | FK, INDEX | √ | - | 采购合同ID |
| `period` | String(20) | INDEX | √ | - | 费用周期 (YYYY-MM) |
| `amount` | Numeric | - | √ | 0.0 | 费用金额 |
| `currency` | String(10) | - | √ | CNY | 币种 |
| `cost_type` | String(50) | - | √ | - | 成本类型 (云资源/人力/软件) |
| `cost_item` | String(200) | - | √ | - | 成本项目名称 |
| `vendor_name` | String(200) | - | √ | - | 供应商名称 |
| `capex_opex_flag` | String(10) | - | √ | - | CAPEX/OPEX标志 |
| `source_system` | String(100) | - | √ | - | 数据来源系统 |
| `correlation_id` | String(100) | INDEX | √ | - | 关联追踪ID |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **service**: many-to-one -> `Service`
- **cost_code**: many-to-one -> `CostCode`
- **purchase_contract**: many-to-one -> `PurchaseContract`

______________________________________________________________________

## 测试管理域

### GTMRequirement (`gtm_requirements`)

**业务描述**: GitLab 需求模型。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `author_id` | UUID | FK | × | - | - |
| `iid` | Integer | - | × | - | - |
| `title` | String(255) | - | × | - | - |
| `description` | Text | - | √ | - | - |
| `state` | String(20) | - | √ | opened | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **author**: many-to-one -> `User`
- **project**: many-to-one -> `GitLabProject`
- **test_cases**: one-to-many -> `GTMTestCase`

______________________________________________________________________

### GTMTestCaseIssueLink (`gtm_test_case_issue_links`)

**业务描述**: 测试用例与 Issue 的关联表 (gtm_test_case_issue_links)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `test_case_id` | Integer | FK | × | - | - |
| `issue_id` | Integer | FK | × | - | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### GTMTestCase (`gtm_test_cases`)

**业务描述**: GitLab 测试用例模型。 存储测试用例的结构化信息，包括标题、描述（预置条件）和详细的执行步骤。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `author_id` | UUID | FK | × | - | - |
| `iid` | Integer | - | × | - | - |
| `title` | String(255) | - | × | - | - |
| `priority` | String(20) | - | √ | - | - |
| `test_type` | String(50) | - | √ | - | - |
| `pre_conditions` | Text | - | √ | - | - |
| `description` | Text | - | √ | - | - |
| `test_steps` | JSON | - | √ | [] | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **author**: many-to-one -> `User`
- **project**: many-to-one -> `GitLabProject`
- **linked_issues**: one-to-many -> `GitLabIssue`
- **associated_requirements**: one-to-many -> `GTMRequirement`
- **execution_records**: one-to-many -> `GTMTestExecutionRecord`

______________________________________________________________________

### GTMTestExecutionRecord (`gtm_test_execution_records`)

**业务描述**: 测试执行完整审计记录模型 (gtm_test_execution_records)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `test_case_iid` | Integer | INDEX | × | - | - |
| `result` | String(20) | - | × | - | - |
| `executed_at` | DateTime | - | √ | now() | - |
| `executor_name` | String(100) | - | √ | - | - |
| `executor_uid` | UUID | - | √ | - | - |
| `comment` | Text | - | √ | - | - |
| `pipeline_id` | Integer | - | √ | - | - |
| `environment` | String(50) | - | √ | Default | - |
| `title` | String(255) | - | √ | - | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

### JenkinsTestExecution (`qa_jenkins_test_executions`)

**业务描述**: Jenkins 测试执行汇总记录表。 存储来自 Jenkins 持续集成工具的测试报告汇总数据。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `project_id` | Integer | INDEX | √ | - | 关联 GitLab 项目 ID |
| `build_id` | String(100) | INDEX | × | - | 构建 ID (Jenkins Build Number) |
| `test_level` | String(50) | - | √ | - | 测试层级 (Unit/API/UI/Performance/Automation) |
| `test_tool` | String(100) | - | √ | - | 测试工具 (Jenkins/JUnit/Pytest) |
| `total_cases` | Integer | - | √ | 0 | 用例总数 |
| `passed_count` | Integer | - | √ | 0 | 通过用例数 |
| `failed_count` | Integer | - | √ | 0 | 失败用例数 |
| `skipped_count` | Integer | - | √ | 0 | 跳过用例数 |
| `pass_rate` | Numeric | - | √ | 0.0 | 通过率 (%) |
| `duration_ms` | Integer | - | √ | 0 | 执行时长 (毫秒) |
| `raw_data` | JSON | - | √ | - | 原始测试报告 JSON |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

## GitLab 集成域

### GitLabBranch (`gitlab_branches`)

**业务描述**: 分支模型。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | √ | - | - |
| `name` | String | - | √ | - | - |
| `last_commit_sha` | String | - | √ | - | - |
| `last_commit_date` | DateTime | - | √ | - | - |
| `last_committer_name` | String | - | √ | - | - |
| `is_merged` | Boolean | - | √ | - | - |
| `is_protected` | Boolean | - | √ | - | - |
| `is_default` | Boolean | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

### GitLabCommit (`gitlab_commits`)

**业务描述**: GitLab 提交模型。 记录 Git 仓库的原子变更，并关联到项目和作者。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | String | PK | × | - | - |
| `project_id` | Integer | FK, INDEX | √ | - | - |
| `short_id` | String | - | √ | - | - |
| `title` | String | - | √ | - | - |
| `author_name` | String | - | √ | - | - |
| `author_email` | String | - | √ | - | - |
| `message` | Text | - | √ | - | - |
| `authored_date` | DateTime | - | √ | - | - |
| `committed_date` | DateTime | INDEX | √ | - | - |
| `additions` | Integer | - | √ | 0 | - |
| `deletions` | Integer | - | √ | 0 | - |
| `total` | Integer | - | √ | 0 | - |
| `is_off_hours` | Boolean | - | √ | False | - |
| `linked_issue_ids` | JSON | - | √ | - | - |
| `issue_source` | String(50) | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |
| `gitlab_user_id` | UUID | FK | √ | - | - |
| `eloc_score` | Numeric | - | √ | 0.0 | 有效代码行数得分 |
| `impact_score` | Numeric | - | √ | 0.0 | 代码影响力得分 |
| `churn_lines` | Integer | - | √ | 0 | 代码翻动行数 |
| `file_count` | Integer | - | √ | 0 | 涉及文件数 |
| `test_lines` | Integer | - | √ | 0 | 测试代码行数 |
| `comment_lines` | Integer | - | √ | 0 | 注释行数 |
| `refactor_ratio` | Numeric | - | √ | 0.0 | 重构代码占比 |
| `promoted_at` | DateTime | - | √ | - | 上架到主数据的时间 |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`
- **author**: many-to-one -> `User`

______________________________________________________________________

### GitLabDeployment (`gitlab_deployments`)

**业务描述**: 部署记录模型。 记录代码被部署到不同环境的执行结果及其追踪 SHA。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `iid` | Integer | - | √ | - | - |
| `project_id` | Integer | FK, INDEX | √ | - | - |
| `status` | String | - | √ | - | - |
| `created_at` | DateTime | INDEX | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `ref` | String | - | √ | - | - |
| `sha` | String | - | √ | - | - |
| `environment` | String | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |
| `mdm_project_id` | Integer | FK, INDEX | √ | - | 关联的 MDM 项目 ID |
| `is_production` | Boolean | INDEX | √ | False | 是否为生产环境部署 |
| `promoted_at` | DateTime | - | √ | - | 上架时间 |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

### GitLabGroupMember (`gitlab_group_members`)

**业务描述**: GitLab 群组成员模型。 维护用户与群组之间的多对多关联及权限信息。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `group_id` | Integer | FK | √ | - | - |
| `user_id` | UUID | FK | √ | - | - |
| `gitlab_uid` | Integer | - | √ | - | - |
| `access_level` | Integer | - | √ | - | - |
| `state` | String(20) | - | √ | - | - |
| `joined_at` | DateTime | - | √ | - | - |
| `expires_at` | DateTime | - | √ | - | - |

#### 关系映射

- **group**: many-to-one -> `GitLabGroup`
- **user**: many-to-one -> `User`

______________________________________________________________________

### GitLabGroup (`gitlab_groups`)

**业务描述**: GitLab 群组模型。 代表 GitLab 中的顶级或子群组，支持树形嵌套结构。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `name` | String(255) | - | √ | - | - |
| `path` | String(255) | - | √ | - | - |
| `full_path` | String(500) | UNIQUE | √ | - | - |
| `description` | Text | - | √ | - | - |
| `parent_id` | Integer | FK | √ | - | - |
| `visibility` | String(20) | - | √ | - | - |
| `avatar_url` | String(500) | - | √ | - | - |
| `web_url` | String(500) | - | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **children**: one-to-many -> `GitLabGroup`
- **projects**: one-to-many -> `GitLabProject`
- **members**: one-to-many -> `GitLabGroupMember`
- **parent**: many-to-one -> `GitLabGroup`

______________________________________________________________________

### GitLabIssue (`gitlab_issues`)

**业务描述**: 议题 (Issue) 模型。 代表项目中的任务、缺陷或需求。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `iid` | Integer | - | √ | - | - |
| `project_id` | Integer | FK, INDEX | √ | - | - |
| `title` | String | - | √ | - | - |
| `description` | String | - | √ | - | - |
| `state` | String | INDEX | √ | - | - |
| `created_at` | DateTime | INDEX | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `closed_at` | DateTime | - | √ | - | - |
| `time_estimate` | Integer | - | √ | - | - |
| `total_time_spent` | Integer | - | √ | - | - |
| `weight` | Integer | - | √ | - | - |
| `work_item_type` | String(50) | - | √ | - | - |
| `ai_category` | String(50) | - | √ | - | - |
| `ai_summary` | Text | - | √ | - | - |
| `ai_confidence` | Numeric | - | √ | - | - |
| `labels` | JSON | - | √ | - | - |
| `first_response_at` | DateTime | - | √ | - | - |
| `milestone_id` | Integer | FK | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |
| `author_id` | UUID | FK | √ | - | - |

#### 关系映射

- **author**: many-to-one -> `User`
- **project**: many-to-one -> `GitLabProject`
- **events**: one-to-many -> `GitLabIssueEvent`
- **transitions**: one-to-many -> `GitLabIssueStateTransition`
- **blockages**: one-to-many -> `GitLabBlockage`
- **milestone**: many-to-one -> `GitLabMilestone`
- **merge_requests**: one-to-many -> `GitLabMergeRequest`
- **associated_test_cases**: one-to-many -> `GTMTestCase`

______________________________________________________________________

### GitLabMergeRequest (`gitlab_merge_requests`)

**业务描述**: 合并请求 (MR) 模型。 存储代码合并请求的核心数据及其在 DevOps 生命周期中的协作元数据。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `iid` | Integer | - | √ | - | - |
| `project_id` | Integer | FK, INDEX | √ | - | - |
| `title` | String | - | √ | - | - |
| `description` | String | - | √ | - | - |
| `state` | String | INDEX | √ | - | - |
| `author_username` | String | - | √ | - | - |
| `created_at` | DateTime | INDEX | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `merged_at` | DateTime | INDEX | √ | - | - |
| `closed_at` | DateTime | - | √ | - | - |
| `reviewers` | JSON | - | √ | - | - |
| `changes_count` | String | - | √ | - | - |
| `diff_refs` | JSON | - | √ | - | - |
| `merge_commit_sha` | String | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |
| `external_issue_id` | String(100) | - | √ | - | - |
| `issue_source` | String(50) | - | √ | - | - |
| `first_response_at` | DateTime | - | √ | - | - |
| `review_cycles` | Integer | - | √ | 1 | - |
| `human_comment_count` | Integer | - | √ | 0 | - |
| `approval_count` | Integer | - | √ | 0 | - |
| `review_time_total` | BigInteger | - | √ | - | - |
| `quality_gate_status` | String(20) | - | √ | - | - |
| `ai_category` | String(50) | - | √ | - | - |
| `ai_summary` | Text | - | √ | - | - |
| `ai_confidence` | Numeric | - | √ | - | - |
| `author_id` | UUID | FK | √ | - | - |

#### 关系映射

- **deployments**: one-to-many -> `GitLabDeployment`
- **author**: many-to-one -> `User`
- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

### GitLabMilestone (`gitlab_milestones`)

**业务描述**: 里程碑模型。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `iid` | Integer | - | √ | - | - |
| `project_id` | Integer | FK | √ | - | - |
| `title` | String | - | √ | - | - |
| `description` | String | - | √ | - | - |
| `state` | String | - | √ | - | - |
| `due_date` | DateTime | - | √ | - | - |
| `start_date` | DateTime | - | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`
- **releases**: one-to-many -> `GitLabRelease`
- **issues**: one-to-many -> `GitLabIssue`

______________________________________________________________________

### GitLabNote (`gitlab_notes`)

**业务描述**: 评论/笔记模型。 存储 Issue、MR 等对象下的讨论内容和系统通知。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | √ | - | - |
| `noteable_type` | String | - | √ | - | - |
| `noteable_iid` | Integer | - | √ | - | - |
| `body` | String | - | √ | - | - |
| `author_id` | UUID | - | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `system` | Boolean | - | √ | - | - |
| `resolvable` | Boolean | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

### GitLabPackage (`gitlab_packages`)

**业务描述**: GitLab 制品库包模型。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | √ | - | - |
| `name` | String(255) | - | × | - | - |
| `version` | String(100) | - | √ | - | - |
| `package_type` | String(50) | - | √ | - | - |
| `status` | String(50) | - | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `web_url` | String(500) | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`
- **files**: one-to-many -> `GitLabPackageFile`

______________________________________________________________________

### GitLabPipeline (`gitlab_pipelines`)

**业务描述**: 流水线 (CI/CD Pipeline) 模型。 记录 CI/CD 执行的结果、时长和覆盖率等工程效能核心指标。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK, INDEX | √ | - | - |
| `status` | String | - | √ | - | - |
| `ref` | String | - | √ | - | - |
| `sha` | String | - | √ | - | - |
| `source` | String | - | √ | - | - |
| `duration` | Integer | - | √ | - | - |
| `created_at` | DateTime | INDEX | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `coverage` | String | - | √ | - | - |
| `failure_reason` | String | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

### GitLabProjectMember (`gitlab_project_members`)

**业务描述**: GitLab 项目成员模型 (Project Level RBAC)。 用于在更细粒度（项目级）控制用户权限。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | √ | - | - |
| `user_id` | UUID | FK | √ | - | - |
| `gitlab_uid` | Integer | - | √ | - | - |
| `access_level` | Integer | - | √ | - | - |
| `role_id` | Integer | FK | √ | - | - |
| `job_title` | String(100) | - | √ | - | - |
| `joined_at` | DateTime | - | √ | - | - |
| `expires_at` | DateTime | - | √ | - | - |

#### 关系映射

- **role**: many-to-one -> `SysRole`
- **project**: many-to-one -> `GitLabProject`
- **user**: many-to-one -> `User`

______________________________________________________________________

### GitLabProject (`gitlab_projects`)

**业务描述**: GitLab 项目模型。 存储 GitLab 中项目的元数据，并关联到组织架构。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `name` | String | - | √ | - | - |
| `path_with_namespace` | String | - | √ | - | - |
| `description` | String | - | √ | - | - |
| `department` | String | - | √ | - | - |
| `group_id` | Integer | FK | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `last_activity_at` | DateTime | - | √ | - | - |
| `last_synced_at` | DateTime | - | √ | - | - |
| `sync_status` | String | INDEX | √ | PENDING | - |
| `raw_data` | JSON | - | √ | - | - |
| `sync_state` | JSON | - | √ | {} | - |
| `storage_size` | BigInteger | - | √ | - | - |
| `star_count` | Integer | - | √ | - | - |
| `forks_count` | Integer | - | √ | - | - |
| `open_issues_count` | Integer | - | √ | - | - |
| `commit_count` | Integer | - | √ | - | - |
| `tags_count` | Integer | - | √ | - | - |
| `branches_count` | Integer | - | √ | - | - |
| `organization_id` | Integer | FK | √ | - | - |
| `mdm_project_id` | Integer | FK | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |

#### 关系映射

- **group**: many-to-one -> `GitLabGroup`
- **organization**: many-to-one -> `Organization`
- **mdm_project**: many-to-one -> `ProjectMaster`
- **dependency_scans**: one-to-many -> `DependencyScan`
- **dependencies**: one-to-many -> `Dependency`
- **milestones**: one-to-many -> `GitLabMilestone`
- **members**: one-to-many -> `GitLabProjectMember`
- **commits**: one-to-many -> `GitLabCommit`
- **merge_requests**: one-to-many -> `GitLabMergeRequest`
- **issues**: one-to-many -> `GitLabIssue`
- **pipelines**: one-to-many -> `GitLabPipeline`
- **deployments**: one-to-many -> `GitLabDeployment`
- **test_cases**: one-to-many -> `GTMTestCase`
- **requirements**: one-to-many -> `GTMRequirement`
- **test_execution_records**: one-to-many -> `GTMTestExecutionRecord`
- **sonar_projects**: one-to-many -> `SonarProject`
- **jira_projects**: one-to-many -> `JiraProject`

______________________________________________________________________

### GitLabRelease (`gitlab_releases`)

**业务描述**: GitLab 发布记录模型。 对应 GitLab 的 Release 对象。一个 Release 基于一个 Tag，可以关联多个 Milestone。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `tag_name` | String(255) | - | × | - | - |
| `name` | String(255) | - | √ | - | - |
| `description` | Text | - | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `released_at` | DateTime | - | √ | - | - |
| `author_id` | UUID | FK | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`
- **milestones**: one-to-many -> `GitLabMilestone`

______________________________________________________________________

### GitLabTag (`gitlab_tags`)

**业务描述**: 标签/版本号模型。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | √ | - | - |
| `name` | String | - | √ | - | - |
| `message` | String | - | √ | - | - |
| `commit_sha` | String | - | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`

______________________________________________________________________

## 认证与授权域

### UserCredential (`sys_user_credentials`)

**业务描述**: 用户凭证表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `user_id` | UUID | FK, UNIQUE | √ | - | 用户ID |
| `password_hash` | String(255) | - | × | - | 密码哈希值 |
| `last_login_at` | DateTime | - | √ | - | 最后登录时间 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **user**: many-to-one -> `User`

______________________________________________________________________

### UserOAuthToken (`sys_user_oauth_tokens`)

**业务描述**: 用户 OAuth 令牌存储表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `user_id` | UUID | FK, INDEX | √ | - | 关联用户ID |
| `provider` | String(50) | INDEX | √ | - | OAuth 提供商 (gitlab/github/azure) |
| `access_token` | String(1024) | - | × | - | 访问令牌 (加密存储) |
| `refresh_token` | String(1024) | - | √ | - | 刷新令牌 |
| `token_type` | String(50) | - | √ | - | 令牌类型 (Bearer) |
| `expires_at` | DateTime | - | √ | - | 过期时间 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### UserRole (`sys_user_roles`)

**业务描述**: 用户与角色关联表 (sys_user_role)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `user_id` | UUID | PK, FK | × | - | 用户ID |
| `role_id` | Integer | PK, FK | × | - | 角色ID |

______________________________________________________________________

## 其他辅助域

### Dependency (`dependencies`)

**业务描述**: 项目依赖清单表 (dependencies)。 存储扫描发现的每一个具体的三方类库及其安全和合规状态。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `scan_id` | Integer | FK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `package_name` | String(500) | - | × | - | - |
| `package_version` | String(100) | - | √ | - | - |
| `package_manager` | String(50) | - | √ | - | - |
| `dependency_type` | String(20) | - | √ | direct | - |
| `license_name` | String(200) | - | √ | - | - |
| `license_spdx_id` | String(100) | - | √ | - | - |
| `license_url` | Text | - | √ | - | - |
| `license_risk_level` | String(20) | - | √ | - | - |
| `has_vulnerabilities` | Boolean | - | √ | False | - |
| `highest_cvss_score` | Numeric | - | √ | - | - |
| `critical_cve_count` | Integer | - | √ | 0 | - |
| `high_cve_count` | Integer | - | √ | 0 | - |
| `medium_cve_count` | Integer | - | √ | 0 | - |
| `low_cve_count` | Integer | - | √ | 0 | - |
| `is_ignored` | Boolean | - | √ | False | - |
| `ignore_reason` | Text | - | √ | - | - |
| `ignore_by` | String(50) | - | √ | - | - |
| `ignore_at` | DateTime | - | √ | - | - |
| `file_path` | Text | - | √ | - | - |
| `description` | Text | - | √ | - | - |
| `homepage_url` | Text | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **scan**: many-to-one -> `DependencyScan`
- **project**: many-to-one -> `GitLabProject`
- **cves**: one-to-many -> `DependencyCVE`

______________________________________________________________________

### DependencyCVE (`dependency_cves`)

**业务描述**: CVE 漏洞详情表 (dependency_cves)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `dependency_id` | Integer | FK | × | - | - |
| `cve_id` | String(50) | - | × | - | - |
| `cvss_score` | Numeric | - | √ | - | - |
| `cvss_vector` | String(200) | - | √ | - | - |
| `severity` | String(20) | - | √ | - | - |
| `description` | Text | - | √ | - | - |
| `published_date` | DateTime | - | √ | - | - |
| `last_modified_date` | DateTime | - | √ | - | - |
| `fixed_version` | String(100) | - | √ | - | - |
| `remediation` | Text | - | √ | - | - |
| `references` | JSON | - | √ | - | - |
| `is_ignored` | Boolean | - | √ | False | - |
| `ignore_reason` | Text | - | √ | - | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **dependency**: many-to-one -> `Dependency`

______________________________________________________________________

### DependencyScan (`dependency_scans`)

**业务描述**: 依赖扫描记录表 (dependency_scans)。 存储 OWASP Dependency-Check 等工具生成的扫描任务概览。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `scan_date` | DateTime | - | × | - | - |
| `scanner_name` | String(50) | - | × | OWASP Dependency-Check | - |
| `scanner_version` | String(20) | - | √ | - | - |
| `total_dependencies` | Integer | - | √ | 0 | - |
| `vulnerable_dependencies` | Integer | - | √ | 0 | - |
| `high_risk_licenses` | Integer | - | √ | 0 | - |
| `scan_status` | String(20) | - | √ | completed | - |
| `ci_job_id` | String(50) | - | √ | - | CI Job ID |
| `ci_job_url` | String(500) | - | √ | - | CI Job URL |
| `commit_sha` | String(40) | - | √ | - | Commit SHA |
| `branch` | String(100) | - | √ | - | Branch Name |
| `report_url` | String(500) | - | √ | - | Report Storage URL |
| `scan_duration_seconds` | Numeric | - | √ | - | Scan Duration (Seconds) |
| `raw_json` | JSON | - | √ | - | - |
| `created_by` | UUID | FK | √ | - | 创建人 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **project**: many-to-one -> `GitLabProject`
- **dependencies**: one-to-many -> `Dependency`

______________________________________________________________________

### JiraBoard (`jira_boards`)

**业务描述**: Jira 看板模型 (jira_boards)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `name` | String(255) | - | √ | - | - |
| `type` | String(50) | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `JiraProject`
- **sprints**: one-to-many -> `JiraSprint`

______________________________________________________________________

### JiraIssue (`jira_issues`)

**业务描述**: Jira Issue (问题/任务) 详情模型 (jira_issues)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `key` | String(50) | UNIQUE | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `sprint_id` | Integer | FK | √ | - | - |
| `summary` | String(500) | - | √ | - | - |
| `description` | Text | - | √ | - | - |
| `status` | String(50) | - | √ | - | - |
| `priority` | String(50) | - | √ | - | - |
| `issue_type` | String(50) | - | √ | - | - |
| `assignee_name` | String(255) | - | √ | - | - |
| `reporter_name` | String(255) | - | √ | - | - |
| `creator_name` | String(255) | - | √ | - | - |
| `assignee_user_id` | UUID | FK | √ | - | - |
| `reporter_user_id` | UUID | FK | √ | - | - |
| `creator_user_id` | UUID | FK | √ | - | - |
| `user_id` | UUID | FK | √ | - | - |
| `created_at` | DateTime | - | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |
| `resolved_at` | DateTime | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |
| `first_commit_sha` | String(100) | - | √ | - | - |
| `first_fix_date` | DateTime | - | √ | - | - |
| `reopening_count` | Integer | - | √ | 0 | - |
| `time_to_first_response` | BigInteger | - | √ | - | - |
| `original_estimate` | BigInteger | - | √ | - | - |
| `time_spent` | BigInteger | - | √ | - | - |
| `remaining_estimate` | BigInteger | - | √ | - | - |
| `labels` | JSON | - | √ | - | - |
| `fix_versions` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `JiraProject`
- **history**: one-to-many -> `JiraIssueHistory`
- **sprint**: many-to-one -> `JiraSprint`

______________________________________________________________________

### JiraProject (`jira_projects`)

**业务描述**: Jira 项目模型 (jira_projects)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `key` | String(50) | UNIQUE | × | - | - |
| `name` | String(255) | - | × | - | - |
| `description` | Text | - | √ | - | - |
| `lead_name` | String(255) | - | √ | - | - |
| `gitlab_project_id` | Integer | FK | √ | - | - |
| `last_synced_at` | DateTime | - | √ | - | - |
| `sync_status` | String(20) | - | √ | PENDING | - |
| `created_at` | DateTime | - | √ | (auto) | - |
| `updated_at` | DateTime | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **gitlab_project**: many-to-one -> `GitLabProject`
- **boards**: one-to-many -> `JiraBoard`
- **issues**: one-to-many -> `JiraIssue`

______________________________________________________________________

### JiraSprint (`jira_sprints`)

**业务描述**: Jira Sprint (迭代) 模型 (jira_sprints)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `board_id` | Integer | FK | × | - | - |
| `name` | String(255) | - | √ | - | - |
| `state` | String(20) | - | √ | - | - |
| `start_date` | DateTime | - | √ | - | - |
| `end_date` | DateTime | - | √ | - | - |
| `complete_date` | DateTime | - | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **board**: many-to-one -> `JiraBoard`
- **issues**: one-to-many -> `JiraIssue`

______________________________________________________________________

### LicenseRiskRule (`license_risk_rules`)

**业务描述**: 许可证风险规则配置表 (license_risk_rules)。 用于定义不同开源许可证的合规性风险评级。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `license_name` | String(200) | UNIQUE | × | - | - |
| `license_spdx_id` | String(100) | - | √ | - | - |
| `risk_level` | String(20) | - | × | - | - |
| `is_copyleft` | Boolean | - | √ | False | - |
| `commercial_use_allowed` | Boolean | - | √ | True | - |
| `modification_allowed` | Boolean | - | √ | True | - |
| `distribution_allowed` | Boolean | - | √ | True | - |
| `patent_grant` | Boolean | - | √ | False | - |
| `description` | Text | - | √ | - | - |
| `policy_notes` | Text | - | √ | - | - |
| `is_active` | Boolean | - | √ | True | - |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### CommitMetrics (`rpt_commit_metrics`)

**业务描述**: 单个提交的详细度量数据 (ELOC)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `commit_sha` | String(100) | UNIQUE, INDEX | √ | - | 提交SHA哈希值 |
| `project_id` | Integer | FK, INDEX | √ | - | 所属项目物理ID |
| `author_email` | String(255) | INDEX | √ | - | 提交者邮箱 |
| `author_user_id` | UUID | FK, INDEX | √ | - | 作者全局用户ID |
| `committed_at` | DateTime | - | √ | - | 提交时间 |
| `raw_additions` | Integer | - | √ | 0 | 原始新增行数 |
| `raw_deletions` | Integer | - | √ | 0 | 原始删除行数 |
| `eloc_score` | Numeric | - | √ | 0.0 | 有效代码行数得分 |
| `impact_score` | Numeric | - | √ | 0.0 | 代码影响力得分 |
| `churn_lines` | Integer | - | √ | 0 | 代码翻动行数 |
| `comment_lines` | Integer | - | √ | 0 | 注释行数 |
| `test_lines` | Integer | - | √ | 0 | 测试代码行数 |
| `file_count` | Integer | - | √ | 0 | 涉及文件数 |
| `is_merge` | Boolean | - | √ | False | 是否为合并提交 |
| `is_legacy_refactor` | Boolean | - | √ | False | 是否为遗留代码重构 |
| `refactor_ratio` | Numeric | - | √ | 0.0 | 重构代码占比 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### DailyDevStats (`rpt_daily_dev_stats`)

**业务描述**: 开发人员行为的每日快照。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `user_id` | UUID | FK, INDEX | √ | - | 用户ID |
| `date` | Date | INDEX | √ | - | 统计日期 |
| `first_commit_time` | DateTime | - | √ | - | 当日首次提交时间 |
| `last_commit_time` | DateTime | - | √ | - | 当日最后提交时间 |
| `commit_count` | Integer | - | √ | 0 | 当日提交次数 |
| `total_impact` | Numeric | - | √ | 0.0 | 当日总影响力得分 |
| `total_churn` | Integer | - | √ | 0 | 当日总代码翻动行数 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### ServiceDeskTicket (`service_desk_tickets`)

**业务描述**: 服务台工单表 (service_desk_tickets)。 实现工单的持久化存储，支持跨部门标签审计与状态追溯。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `gitlab_project_id` | Integer | INDEX | × | - | - |
| `gitlab_issue_iid` | Integer | - | × | - | - |
| `title` | String(255) | - | × | - | - |
| `description` | Text | - | √ | - | - |
| `issue_type` | String(50) | INDEX | √ | - | - |
| `status` | String(50) | INDEX | √ | opened | - |
| `origin_dept_id` | Integer | INDEX | √ | - | - |
| `origin_dept_name` | String(100) | - | √ | - | - |
| `target_dept_id` | Integer | INDEX | √ | - | - |
| `target_dept_name` | String(100) | - | √ | - | - |
| `requester_id` | UUID | FK | √ | - | - |
| `requester_email` | String(100) | INDEX | √ | - | - |
| `bug_category` | String(50) | - | √ | - | 缺陷分类 (code-error/configuration/performance等) |
| `req_type` | String(50) | - | √ | - | 需求类型 (feature/config/interface等) |
| `created_at` | DateTime | - | √ | - | - |
| `updated_at` | DateTime | - | √ | - | - |

______________________________________________________________________

### SonarIssue (`sonar_issues`)

**业务描述**: SonarQube 问题详情模型 (sonar_issues)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `issue_key` | String(50) | UNIQUE | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `type` | String(20) | - | √ | - | - |
| `severity` | String(20) | - | √ | - | - |
| `status` | String(20) | - | √ | - | - |
| `resolution` | String(20) | - | √ | - | - |
| `rule` | String(200) | - | √ | - | - |
| `message` | Text | - | √ | - | - |
| `component` | String(500) | - | √ | - | - |
| `line` | Integer | - | √ | - | - |
| `effort` | String(20) | - | √ | - | - |
| `debt` | String(20) | - | √ | - | - |
| `creation_date` | DateTime | - | √ | - | - |
| `update_date` | DateTime | - | √ | - | - |
| `close_date` | DateTime | - | √ | - | - |
| `assignee` | String(100) | - | √ | - | - |
| `author` | String(100) | - | √ | - | - |
| `assignee_user_id` | UUID | FK | √ | - | - |
| `author_user_id` | UUID | FK | √ | - | - |
| `raw_data` | JSON | - | √ | - | - |

#### 关系映射

- **project**: many-to-one -> `SonarProject`

______________________________________________________________________

### SonarMeasure (`sonar_measures`)

**业务描述**: SonarQube 指标快照模型 (sonar_measures)。 每次代码分析后记录一条快照，用于追踪质量趋势。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `project_id` | Integer | FK | × | - | - |
| `analysis_date` | DateTime | - | × | - | - |
| `files` | Integer | - | √ | - | - |
| `lines` | Integer | - | √ | - | - |
| `ncloc` | Integer | - | √ | - | - |
| `classes` | Integer | - | √ | - | - |
| `functions` | Integer | - | √ | - | - |
| `statements` | Integer | - | √ | - | - |
| `coverage` | Numeric | - | √ | - | - |
| `bugs` | Integer | - | √ | - | - |
| `bugs_blocker` | Integer | - | √ | 0 | - |
| `bugs_critical` | Integer | - | √ | 0 | - |
| `bugs_major` | Integer | - | √ | 0 | - |
| `bugs_minor` | Integer | - | √ | 0 | - |
| `bugs_info` | Integer | - | √ | 0 | - |
| `vulnerabilities` | Integer | - | √ | - | - |
| `vulnerabilities_blocker` | Integer | - | √ | 0 | - |
| `vulnerabilities_critical` | Integer | - | √ | 0 | - |
| `vulnerabilities_major` | Integer | - | √ | 0 | - |
| `vulnerabilities_minor` | Integer | - | √ | 0 | - |
| `vulnerabilities_info` | Integer | - | √ | 0 | - |
| `security_hotspots` | Integer | - | √ | - | - |
| `security_hotspots_high` | Integer | - | √ | 0 | - |
| `security_hotspots_medium` | Integer | - | √ | 0 | - |
| `security_hotspots_low` | Integer | - | √ | 0 | - |
| `code_smells` | Integer | - | √ | - | - |
| `comment_lines_density` | Numeric | - | √ | - | - |
| `duplicated_lines_density` | Numeric | - | √ | - | - |
| `sqale_index` | Integer | - | √ | - | - |
| `sqale_debt_ratio` | Numeric | - | √ | - | - |
| `complexity` | Integer | - | √ | - | - |
| `cognitive_complexity` | Integer | - | √ | - | - |
| `reliability_rating` | String(1) | - | √ | - | - |
| `security_rating` | String(1) | - | √ | - | - |
| `sqale_rating` | String(1) | - | √ | - | - |
| `new_coverage` | Numeric | - | √ | - | 新增代码覆盖率 |
| `new_bugs` | Integer | - | √ | - | 新增 Bug 数 |
| `new_vulnerabilities` | Integer | - | √ | - | 新增漏洞数 |
| `new_reliability_rating` | String(1) | - | √ | - | 新增可靠性评级 |
| `new_security_rating` | String(1) | - | √ | - | 新增安全性评级 |
| `quality_gate_status` | String(10) | - | √ | - | - |
| `created_at` | DateTime | - | √ | (auto) | - |

#### 关系映射

- **project**: many-to-one -> `SonarProject`

______________________________________________________________________

### SonarProject (`sonar_projects`)

**业务描述**: SonarQube 项目模型 (sonar_projects)。 存储 SonarQube 项目信息，支持与 GitLab 项目关联。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | - |
| `key` | String(500) | UNIQUE | × | - | - |
| `name` | String(255) | - | √ | - | - |
| `qualifier` | String(10) | - | √ | - | - |
| `gitlab_project_id` | Integer | FK | √ | - | - |
| `mdm_project_id` | Integer | FK | √ | - | 关联的 MDM 项目 ID |
| `mdm_product_id` | Integer | FK | √ | - | 关联的 MDM 产品 ID |
| `last_analysis_date` | DateTime | - | √ | - | - |
| `last_synced_at` | DateTime | - | √ | - | - |
| `sync_status` | String(20) | - | √ | PENDING | - |
| `created_at` | DateTime | - | √ | (auto) | - |
| `updated_at` | DateTime | - | √ | - | - |

#### 关系映射

- **gitlab_project**: many-to-one -> `GitLabProject`
- **measures**: one-to-many -> `SonarMeasure`
- **issues**: one-to-many -> `SonarIssue`
- **latest_measure**: many-to-one -> `SonarMeasure`

______________________________________________________________________

### RawDataStaging (`stg_raw_data`)

**业务描述**: 原始数据暂存表 (Staging 层)，用于存放未经处理的 API Payload。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `source` | String(50) | - | √ | - | 数据来源系统 (gitlab/jira/sonar) |
| `entity_type` | String(50) | - | √ | - | 实体类型 (project/issue/pipeline) |
| `external_id` | String(100) | INDEX | √ | - | 外部系统记录ID |
| `payload` | JSON | - | √ | - | 原始 JSON 数据负载 |
| `schema_version` | String(20) | - | √ | - | Payload 结构版本 |
| `correlation_id` | String(100) | INDEX | √ | - | 关联追踪ID |
| `collected_at` | DateTime | - | √ | - | 采集时间 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### AuditLog (`sys_audit_logs`)

**业务描述**: 系统合规审计日志表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 审计记录ID |
| `timestamp` | DateTime | INDEX | √ | (auto) | 物理操作发生时间 |
| `actor_id` | UUID | INDEX | √ | - | 操作者全局唯一标识 (Global User ID) |
| `actor_name` | String(200) | - | √ | - | 操作者姓名快照 |
| `client_ip` | String(50) | - | √ | - | 来源 IP 地址 |
| `action` | String(50) | INDEX | × | - | 动作类型 |
| `resource_type` | String(50) | INDEX | √ | - | 操作对象类型 (一般为表名) |
| `resource_id` | String(100) | INDEX | √ | - | 操作对象实例 ID |
| `changes` | JSONB | - | √ | - | 字段级变更增量 Diff (JSON) |
| `request_id` | String(100) | INDEX | √ | - | 关联请求追踪 ID (全链路对齐) |
| `correlation_id` | String(100) | INDEX | √ | - | 业务关联 ID (如同步任务ID) |
| `status` | String(20) | INDEX | √ | SUCCESS | 操作执行状态 (SUCCESS/FAILURE) |
| `remark` | Text | - | √ | - | 详细备注或报错信息堆栈 |

______________________________________________________________________

### SysMenu (`sys_menu`)

**业务描述**: 系统菜单/权限表 (sys_menu)。 统一管理系统菜单结构和功能权限标识。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 菜单ID |
| `menu_name` | String(50) | - | × | - | 菜单名称 |
| `parent_id` | Integer | FK | √ | - | 父菜单ID (0或NULL表示顶级) |
| `order_num` | Integer | - | √ | 0 | 显示顺序 |
| `path` | String(200) | - | √ | | 路由地址 |
| `component` | String(255) | - | √ | - | 组件路径 |
| `query` | String(255) | - | √ | - | 路由参数 |
| `is_frame` | Boolean | - | √ | False | 是否为外链 |
| `is_cache` | Boolean | - | √ | True | 是否缓存 |
| `menu_type` | String(1) | - | √ | | 菜单类型 (M目录 C菜单 F按钮) |
| `visible` | Boolean | - | √ | True | 菜单状态 (True显示 False隐藏) |
| `status` | Boolean | - | √ | True | 菜单状态 (True正常 False停用) |
| `perms` | String(100) | - | √ | - | 权限标识 (e.g. system:user:list) |
| `icon` | String(100) | - | √ | # | 菜单图标 |
| `remark` | String(500) | - | √ | | 备注 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **children**: one-to-many -> `SysMenu`
- **parent**: many-to-one -> `SysMenu`
- **roles**: one-to-many -> `SysRole`

______________________________________________________________________

### SysRole (`sys_role`)

**业务描述**: 系统角色表 (sys_role)。 扩展支持数据范围权限及角色继承。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 角色ID |
| `role_name` | String(30) | - | × | - | 角色名称 |
| `role_key` | String(100) | UNIQUE | × | - | 角色权限字符串 |
| `role_sort` | Integer | - | × | 0 | 显示顺序 |
| `data_scope` | Integer | - | √ | 1 | 数据范围 |
| `parent_id` | Integer | - | √ | 0 | 父角色ID (RBAC1) |
| `status` | Boolean | - | √ | True | 角色状态 |
| `is_deleted` | Boolean | - | √ | False | 删除标志 |
| `remark` | String(500) | - | √ | - | 备注 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **menus**: one-to-many -> `SysMenu`
- **depts**: one-to-many -> `Organization`
- **users**: one-to-many -> `User`

______________________________________________________________________

### SysRoleDept (`sys_role_dept`)

**业务描述**: 角色和部门关联表 (sys_role_dept)，用于自定义数据权限。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `role_id` | Integer | PK, FK | × | - | - |
| `dept_id` | Integer | PK, FK | × | - | - |

______________________________________________________________________

### SysRoleMenu (`sys_role_menu`)

**业务描述**: 角色和菜单关联表 (sys_role_menu)。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `role_id` | Integer | PK, FK | × | - | - |
| `menu_id` | Integer | PK, FK | × | - | - |

______________________________________________________________________

### SyncLog (`sys_sync_logs`)

**业务描述**: 插件数据同步日志记录表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `project_id` | Integer | FK, INDEX | √ | - | 关联项目物理ID |
| `external_id` | String(100) | INDEX | √ | - | 来源系统原始ID |
| `source` | String(50) | INDEX | √ | - | 来源系统类型 (gitlab/zentao/sonarqube) |
| `status` | String(50) | - | √ | - | 同步状态 (SUCCESS/FAILED/RUNNING) |
| `message` | Text | - | √ | - | 同步结果信息 |
| `correlation_id` | String(100) | INDEX | √ | - | 关联追踪ID |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

______________________________________________________________________

### TeamMember (`sys_team_members`)

**业务描述**: 团队成员关联表。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `team_id` | Integer | FK | × | - | 团队ID |
| `user_id` | UUID | FK | × | - | 成员用户ID |
| `role_code` | String(50) | - | √ | MEMBER | 团队角色 (LEADER/MEMBER/CONSULTANT) |
| `allocation_ratio` | Numeric | - | √ | 1.0 | 工作量分配比例 (0.0-1.0) |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |

#### 关系映射

- **team**: many-to-one -> `Team`
- **user**: many-to-one -> `User`

______________________________________________________________________

### Team (`sys_teams`)

**业务描述**: 虚拟业务团队/项目组表。 支持 SCD Type 2，用于精确追踪团队名称、负责人及组织归属的历史变更， 确保 DORA 等效能指标能准确归因到"当时的团队"。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 可空 | 默认值 | 说明 |
|:-------|:---------|:-----|:-----|:-------|:-----|
| `id` | Integer | PK | × | - | 自增主键 |
| `name` | String(100) | - | × | - | 团队名称 |
| `team_code` | String(50) | UNIQUE, INDEX | √ | - | 团队代码 |
| `description` | Text | - | √ | - | 团队描述 |
| `parent_id` | Integer | FK | √ | - | 上级团队ID |
| `org_id` | Integer | FK | √ | - | 所属组织ID |
| `leader_id` | UUID | FK | √ | - | 团队负责人 |
| `created_at` | DateTime | - | √ | (auto) | 创建时间 |
| `updated_at` | DateTime | - | √ | - | 最后更新时间 |
| `created_by` | UUID | FK, INDEX | √ | - | 创建者ID |
| `updated_by` | UUID | FK, INDEX | √ | - | 最后操作者ID |
| `sync_version` | Integer | - | × | 1 | - |
| `effective_from` | DateTime | - | √ | (auto) | - |
| `effective_to` | DateTime | - | √ | - | - |
| `is_current` | Boolean | INDEX | √ | True | - |
| `is_deleted` | Boolean | - | √ | False | - |

#### 关系映射

- **parent**: many-to-one -> `Team`
- **leader**: many-to-one -> `User`
- **members**: one-to-many -> `TeamMember`
- **children**: one-to-many -> `Team`

______________________________________________________________________

## 变更日志

### v2.2 (自动生成)

- 基于最新 SQLAlchemy 模型自动生成
- 支持变更检测和 Diff 对比
- 增强字段注释提取
- 优化默认值显示

______________________________________________________________________

**维护说明**: 本文档由 `scripts/generate_data_dictionary.py` 自动生成。
如需更新，请修改模型定义并运行 `just docs` 命令。
