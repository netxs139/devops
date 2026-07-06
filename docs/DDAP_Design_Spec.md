# DDAP 研发效能数据底座设计方案（DDAP — DevOps Data Application Platform）

> **标准模式文档** — 适用于企业级研发效能数据治理与质量中台的架构方案。
> **版本**: v3.0 | **日期**: 2026-07-06 | **作者**: netxs + Antigravity
> **代号**: DDAP
>
> 本文件定义项目全局标准与架构边界。新业务模块或前端界面接入时，请严格遵循本文件的**微内核+多租户模块化架构**指引。
>
> **v3.0 架构大爆炸 (当前版本)**：全面转型为“单体部署，模块化开发 (Modular Monolith)”架构。拆分 5 大独立 pip 包；废弃 DDAP 内置身份，全面接入 `identity_module` 并引入 `tenant_id` 支撑 3 公司多租户；ServiceDesk (SD) 面向外部客户实现身份物理隔离。

## 0. 架构选型总览

本平台已从传统的单体巨石 (Monolith) 进化为基于模块化组装的架构：

| 维度 | 核心技术栈选择 |
| -------------- | --------------------------------------- |
| **整体架构** | 单体部署，模块化开发 (FastAPI 微内核 + 独立 pip 组件包) |
| **多租户隔离** | 物理表级隔离 (`tenant_id`)，支撑集团 3 个子公司独立核算 |
| **前端架构** | 微前端基座 (Shell) + 业务组件包 (如 `@company/iam-kit`, `@company/agile-kit`) |
| **数据关联** | 跨域数据禁止使用物理外键 (Foreign Key)，强制使用 UUID/String 软引用 |

______________________________________________________________________

## 1. 核心业务演进：5 大解耦模块战略

为了解决系统日益庞大导致的逻辑耦合，DDAP 后端将剥离出以下 5+1 个高内聚、低耦合的独立领域模块。DDAP 的核心 FastAPI 程序仅作为**网关 (Gateway)** 进行聚合挂载。

### 1.1 模块 0：公共身份底座 (`identity_module`) [跨库复用]

- **职责**：提供全域统一的用户、组织架构、RBAC 权限流转。
- **特性**：全面引入 `tenant_id`，天然支持 3 公司数据隔离。包含 `hr_relationship` 与合并账号标识。
- **DDAP 现状变更**：彻底**废弃**原 DDAP 的 `mdm_identities`, `mdm_organizations`, `SysRole` 等旧表。

### 1.2 模块 1：DevOps 主数据模块 (`mdm_core_module`)

- **职责**：数据采集引擎与资产中心。负责对接 GitLab, Zentao, Sonar, Jenkins, Nexus。
- **边界**：仅做“原始事件”抓取（如 Commit 产生、Job 完成），向平台总线广播事件，自身不包含任何敏捷或业务逻辑。

### 1.3 模块 2：敏捷项目管理模块 (`agile_module`)

- **职责**：需求、缺陷、迭代看板的核心流转引擎。
- **边界**：消费主数据模块的原始 Issue 状态，建立轻量级看板并支持双向同步（对接 ZenTao/Gilab）。

### 1.4 模块 3：测试管理模块 (`test_module`)

- **职责**：管理测试用例树、测试执行计划。
- **边界**：单向依赖 `agile_module`。测试失败时可直接投递缺陷到敏捷模块进行闭环。

### 1.5 模块 4：服务台模块 (`servicedesk_module`) [特例隔离]

- **职责**：面向非研发人员（客户/运营）的支持工单通道。表单支持提交“需求”与“Bug”。
- **身份隔离契约**：ServiceDesk 提报人**绝对禁止**混入内部的 `identity_module`。SD 模块需独立建立 `CustomerIdentity` 表单，确保内部员工与外部人员物理隔离。
- **流转**：客服审批后，通过领域事件调用 `agile_module` 自动生成研发需求。

### 1.6 模块 5：BI 大屏与度量模块 (`bi_metrics_module`)

- **职责**：纯数据聚合呈现。生成 DORA 四大指标、ELOC 代码贡献度。
- **边界**：只读性质，基于 `dbt` 数据仓加工并渲染 ECharts 大屏。

______________________________________________________________________

## 2. 数据库与架构设计规范 (Constraints First)

在新的多模块架构下，开发任何新功能必须遵循以下**三大铁律**：

### 2.1 铁律一：多租户一致性契约 (Tenant Isolation)

所有业务核心表，无论在哪个模块中，**必须**包含 `tenant_id` 字段以支持 3 个公司的核算隔离。

```python
tenant_id: Mapped[str] = mapped_column(String(32), index=True, server_default='default')
```

后端所有 API 请求均需通过中间件提取 JWT 中的 `tenant_id`，在查询时强制作为 `WHERE` 过滤条件，严禁跨租户查库。

### 2.2 铁律二：跨域数据的软关联 (Soft References)

各模块（Pip包）之间的数据关联**严禁使用数据库外键 (ForeignKey)**。

- **错误做法**：在 `test_module` 中建立 `ForeignKey("identity_user.global_user_id")`。
- **正确做法**：将关联字段定义为普通的 `String(32)`。由业务逻辑层（Service）进行跨模块的数据一致性校验。
- **原因**：保持各模块能够独立迁移与部署，避免数据库层面的死锁和耦合。

### 2.3 铁律三：前端基座化 (Shell Application)

DDAP 的前端 (`devops_portal/frontend`) 不再开发庞大的业务代码，而是退化为一个**纯粹的基座框架 (Shell)**。

- 左侧菜单点击“用户管理”，基座动态加载从 AMDP 复用来的 `@company/iam-kit` 组件。
- 左侧菜单点击“敏捷看板”，动态加载 `@company/agile-kit` 组件。
- 实现各个 Kit 包在不同项目间的“绿地复用”。

______________________________________________________________________

## 3. 被废弃的旧版数据模型与代码 (Deletion & Refactoring Plan)

在平滑过渡到新架构的过程中，原有的强耦合代码将被采取“物理删除”或“逻辑重构”的策略：

### 3.1 物理删除 (Direct Deletion)

由于全面接入 `identity_module`，以下提供基础鉴权与组织架构的硬编码逻辑被完全废弃，**直接删除**：

- `devops_collector/auth/auth_router.py` (登录注册 API)
- `devops_collector/auth/auth_service.py` (JWT 鉴权逻辑)
- `devops_collector/models/base_models.py` 中的 `mdm_identities` (User), `mdm_organizations` (Org), `SysRole`, `SysMenu`, `IdentityMapping` 表定义。

### 3.2 逻辑重构 (Refactoring)

- **网关路由**：`devops_portal/main.py` 删除旧 Auth 路由，改为调用 `register_identity(app, db_session_factory)` 挂载联邦认证。
- **依赖注入**：`devops_portal/dependencies.py` 中的 `get_current_user` 被重构，底层改为调用 `identity_module` 解析 Token 返回 `IdentityUser`。
- **业务关联表**：如 `GitLabProject`, `TestCase` 中的外键 (`ForeignKey('mdm_identities.global_user_id')`) 被重构为普通的 `String(32)`，取消数据库硬约束。

______________________________________________________________________

## 4. 目录结构变更影响 (Directory Structure Impact)

转型“单体部署，模块化开发”后，工程目录结构将发生如下范式转变：

### 4.1 后端目录 (Backend)

```text
devops/
├── devops_portal/         # (Gateway) 核心网关与组合层，挂载各模块路由，提供全局中间件
│   ├── main.py            # 统一入口 (调用 register_identity, register_agile 等)
│   └── dependencies.py    # 跨模块通用依赖
├── devops_collector/      # (Monolith Legacy) 逐步按领域拆分
│   └── plugins/           # (模块1) 主数据采集中心 (GitLab/Zentao)
├── agile_module/          # (模块2) 新增：独立敏捷项目管理
├── test_module/           # (模块3) 新增：独立测试管理
├── servicedesk_module/    # (模块4) 新增：独立服务台 (外部用户隔离)
└── bi_metrics_module/     # (模块5) 新增：BI度量
```

### 4.2 前端目录 (Frontend)

```text
devops/devops_portal/static/
├── index.html             # (Shell) 基座入口
├── src/
│   ├── core/              # 微前端加载器 / 联邦挂载点
│   └── views/
│       ├── legacy/        # 遗留强耦合页面
│       └── portal/        # 新版组装页：动态加载远端/本地 Kit
```

前端开发范式从“在单一仓库堆砌页面”转变为“以基座加载 `@company/iam-kit`、`@company/agile-kit` 联邦组件包”的形式。
