# Iapetus 统一身份平台设计方案（IAP — Identity & Access Platform）

> **标准模式文档** — 适用于公司新开发系统的身份认证与自动分发架构方案。
> **版本**: v5.8 | **日期**: 2026-07-05 | **作者**: netxs + 云酱 + Trae
> **代号**: IAP
>
> 本文件定义企业级标准。新系统接入时，从 §17"适用性判断树"开始，确定本模式是否适合当前场景。
>
> **v5.5 变更**：补充 §26.2 §26.3 实现细节——明确 AI 功能为页内 UI 增强（不改菜单/不增路由）、后端新增 `app/ai/` 独立模块。
> **v5.4 变更**：新增 §26 AI 辅助功能章节——定义智能映射建议（P1）、Provisioning 异常根因分析（P2）、LLM 调用防护、提示词治理、前端 AI 区块规范及降级策略。
> **v5.3 变更**：新增 §25 前端架构章节——定义 iam-kit（NPM 共享包）、Iapetus 独立壳、AMDP 集成方式、Naive UI 主题统一方案及 AMDP 现有 CSS 重构策略。
> **v5.2 变更**：修订 §10 通知服务适用范围——通知是基础设施横切关注点，与 identity_module 的身份管理职责分离。方案A（独立 Identity Service）中通知作为 Iapetus 内置模块，方案B（嵌入式 identity_module）中通知由业务系统通过独立包自行集成，不纳入 identity_module。
> **v5.1 变更**：整合 §2.5 权限管理（原《IdentityService权限管理扩展方案》）、§3.8 审计日志（原《IdentityService审计日志扩展方案》）、§3.9 通知服务（原《IdentityService通知服务扩展方案》），分散文档并入主设计。4 份原文件标记归档。
> **v5.0 变更**：整合 §11 双模式认证方案——新增 OIDC + LDAP 双模式认证。
> **v4.8 变更**：§3.14 表关系总览重构为三层架构（身份层 + 权限层 + 审计层），纳入§8（权限管理）与 §9（审计日志）的新增表，形成完整的数据模型全景图。

## 0. 架构选型总览

> 本章为快速导引。新读者可从 §1 开始，需要时回溯此处对比方案A/B。

本模式提供两种部署架构，选择取决于业务系统的部署环境和管理模式：

| 维度 | 方案A：独立Identity Service | 方案B：嵌入式 identity-module |
| -------------- | --------------------------------------- | ------------------------------------------------ |
| **部署形态** | 独立容器 + 独立数据库 `identity_db` | `pip install` Python包，表建在业务系统自有DB内 |
| **数据归属** | 集中存储于 identity_db，单一事实源 | 各业务系统DB各自存储，Master/Replica同步保持一致 |
| **跨系统身份** | 天然统一（同一数据源） | 需Master→Replica同步机制保证 |
| **基础设施** | 需额外维护一个独立服务+DB | 零额外基础设施，随业务系统一起部署 |
| **查询性能** | 网络API调用，依赖Identity Service可用性 | 本地SQL查询，零延迟，业务系统自治 |
| **容错特性** | Identity故障→所有业务系统身份查询受影响 | 同步中断不影响本地查询，变更排队恢复后补写 |
| **升级方式** | 一个服务升级→全局生效 | `pip upgrade`→各业务系统独立升级 |
| **适用场景** | 多系统共享身份、跨系统SSO、需统一管理 | 新开发系统、单一应用、不想引入额外DB |

- **本文§2-§17基于方案A（独立Identity Service）设计**，是公司现有5个研发工具系统接入的推荐方案。
- **§附录A 给出方案B（嵌入式 identity-module）的完整设计**，适用于新开发系统或不想额外维护数据库的场景。
- **新项目决策路径**：先读§13"适用性判断树" → 根据结果选A或B → 按对应章节落地。

______________________________________________________________________

## 1. 背景与目标

### 1.1 现状问题

公司现有5个研发工具系统，各自独立维护账号：

| 系统 | 认证方式 | 账号命名 | 身份识别 |
| --------- | -------- | -------- | -------------------- |
| GitLab CE | 本地用户 | zhangsan | 无法跨系统识别同一人 |
| Zentao CE | 本地用户 | zs001 | 无法跨系统识别同一人 |
| SonarQube | 本地用户 | zhangsan | 无法跨系统识别同一人 |
| Nexus CE | 本地用户 | zhangs | 无法跨系统识别同一人 |
| Jenkins | 本地用户 | zhangsan | 无法跨系统识别同一人 |

**两个核心痛点**：

1. 管理员需要在5个系统分别创建用户，操作繁琐且容易遗漏
1. 同一个人在不同系统的账号名不一致，无法识别为"同一个张三"

### 1.2 目标

| 目标 | 说明 |
| -------------------- | ----------------------------------------------------------------------------- |
| **统一SSO** | 支持OIDC的系统（GitLab/SonarQube/Jenkins/DDAP/AMDP）通过Pocket-ID实现单次登录 |
| **身份归一** | 6系统用户全部映射到唯一`global_user_id`，实现跨系统身份追溯 |
| **统一Provisioning** | 管理员在 Identity Service 一次建人，按需自动推送到勾选的目标系统 |
| **部门同步** | 管理员在 Identity Service 一次建部门，自动推送到支持组/部门的系统 |

> **AMDP 身份功能声明**：AMDP 系统不独立开发身份管理（用户/部门/映射/SSO/权限/审计）功能。上述能力统一由 Iapetus 提供，AMDP 通过 §13 定义的 API 对接，通过 §24 定义的管理控制台操作。DDAP 同理。

### 1.3 系统约束（不可变）

| 系统 | 能SSO? | 能Provision? | 说明 |
| --------- | ------------------------------- | ----------------- | --------------------------------- |
| GitLab CE | [OK] Pocket-ID OAuth2 | [OK] API创建用户 | OmniAuth内置 |
| SonarQube | [OK] OIDC（OpenID Connect）插件 | [OK] API创建用户 | 26.1版支持 |
| Jenkins | [OK] OIDC插件 | [OK] API创建用户 | 需安装OIDC插件 |
| Nexus CE | [OK] LDAP | [OK] API创建用户 | 通过LLDAP + Traefik L4 TCP分流 |
| Zentao CE | [OK] LDAP | [OK] API创建用户 | 通过LLDAP + Traefik L4 TCP分流 |
| Pocket-ID | — | [OK] REST API创建 | OIDC IdP（Identity Provider）自身 |
| DDAP | [OK] Pocket-ID OIDC | [OK] 本地创建 | 自研系统 |
| AMDP | [OK] Pocket-ID OIDC | [OK] 调DDAP API | 自研系统 |

## 2. 架构设计

### 2.1 三层架构（最终版）

```
┌──────────────────────────────────────────────────────────────┐
│                    Traefik（入口层）                        │
│        L7 HTTP 路由（OIDC）+ L4 TCP 路由（LDAP）             │
│                                                              │
│  L7 HTTP → Pocket-ID（OIDC）                   │
│  L4 TCP  → LLDAP（LDAP，不解包直接转发原始包）               │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│              协议层（双认证源）                              │
│                                                           │
│  ┌─────────────────────┐  ┌─────────────────────────────┐│
│  │    Pocket-ID         │  │        LLDAP                ││
│  │  OIDC + Passkey      │  │  LDAP（Zentao/Nexus 直连）   ││
│  │                      │  │                             ││
│  │  覆盖：GitLab        │  │  覆盖：Zentao               ││
│  │        Jenkins       │  │        Nexus                ││
│  │        SonarQube     │  │                             ││
│  │        DDAP/AMDP     │  │  用户来源：Identity Service ││
│  │                      │  │  Provisioning 按需推送      ││
│  │  用户来源：Identity  │  │                             ││
│  │  Service 推送        │  │                             ││
│  └─────────────────────┘  └─────────────────────────────┘│
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│               Identity Service（数据+业务层）               │
│                                                           │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ identity_user    │  │ identity_provisioning_policy │  │
│  │ (用户主表, SSOT) │  │ (分发策略模板)                │  │
│  └──────────────────┘  └──────────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ identity_dept    │  │ identity_provisioning_log   │  │
│  │ (部门树)          │  │ (分发审计日志)               │  │
│  └──────────────────┘  └──────────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ identity_mapping │  │ identity_user_dept (SCD2)   │  │
│  │ (跨系统账号映射)  │  │ (人员部门归属历史)            │  │
│  └──────────────────┘  └──────────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ identity_tag    │  │ identity_sync_event_log     │  │
│  │ (标签系统)       │  │ (外部同步审计)                │  │
│  └──────────────────┘  └──────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │         IdentityManager + ProvisioningEngine       │  │
│  │   身份解析 + 并行向6系统+外部IdP推送建人/部门/停用   │  │
│  │   + Fan-out 密码修改（Pocket-ID + LLDAP 双写）     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │     REST API（/identity/v1/*）                      │  │
│  │     供所有业务系统（AMDP/DDAP/新系统）统一调用         │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2.2 组件职责边界

| 组件 | 职责 | 不负责 |
| -------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------- |
| **Pocket-ID** | OIDC IdP + Passkey认证 | 不管用户创建（由Identity Service推送） |
| **LLDAP** | LDAP认证源 + 供Zentao/Nexus通过Traefik L4 TCP直连 | 不管用户创建（由Identity Service按需推送）；不管理Pocket-ID用户 |
| **Identity Service** | 用户/部门唯一入口 + 身份映射 + 6系统Provisioning + 密码Fan-out双写 | 不管认证协议执行（由Pocket-ID和LLDAP各自独立完成） |
| **Traefik** | L7 HTTP路由（OIDC）+ L4 TCP路由（LDAP，不解包直接转发原始包）+ HTTPS | 不管认证逻辑 |

**SSOT（Single Source of Truth）选择**：Identity Service的**设置项**决定谁是人-数据的唯一事实源。后台UI提供配置开关：

- **OFF（默认）** → Iapetus 自身为SSOT，用户/部门通过UI或API直接创建
- **ON** → 指定一个外部IdP（企微/钉钉/飞书/HR系统/LDAP（Lightweight Directory Access Protocol））为SSOT，Identity Service自动从该源同步用户和部门变更，自身转为"映射+分发"角色

切换SSOT来源不影响已有数据的`global_user_id`，仅影响后续新建/更新操作的写入方向。

**SSOT回切（从外部IdP切回Identity Service自管）**：需手动确认冲突处理策略。

| 场景 | 外部IdP侧的状态 | 回切后Identity Service行为 |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------------------------------------------------------------------- |
| 用户/部门在IdP存在且与本地一致 | 正常 | 保持现状，不做变更 |
| 用户/部门在IdP存在但本地已删除 | 正常 | 保持删除，不重新创建（IdP不是SSOT了，不自动同步回写） |
| 用户/部门在IdP已删除但本地仍有 | 已删除 | 保持本地记录，标记为 `source: legacy` 供管理员手动处理 |
| 用户/部门仅在IdP中有但本地没有 | 新增 | 不自动创建（回切后IdP不再同步，需要管理员在Identity Service手动建人） |
| **原则**：回切后外部IdP降级为辅助数据源，Identity Service不再从IdP拉取变更。IdP中已有的数据差异由管理员通过"未映射清单"逐条确认，不做自动合并。 | | |

**独立服务边界**：Iapetus 不依赖DDAP进程存活，拥有独立数据库 `identity_db`，通过自身API向AMDP/DDAP/新系统提供身份服务。

## 3. 数据模型

> 身份服务独立部署，拥有自己的数据库 `identity_db`。所有表使用 `identity_` 前缀。
> `global_user_id` 即用户主键（UUID v7，CHAR(32)），时间有序、全局唯一。所有外部FK（Foreign Key）直接指向此字段。
> **UUID v7 选择理由**：前48位为毫秒级时间戳，天然按创建时间排序，索引友好；后74位为随机数，保证跨系统（多Master场景）无冲突。详见 §A.6.2。

### 3.1 identity_user（用户主表，SSOT）

```sql
CREATE TABLE identity_user (
    global_user_id    CHAR(32)     NOT NULL PRIMARY KEY,   -- UUID v7，ORM生成（含时间戳前缀，全局唯一）
    username          VARCHAR(64)  NOT NULL UNIQUE,        -- 统一登录名
    display_name      VARCHAR(128) NOT NULL,                -- 张三
    primary_email     VARCHAR(255),                         -- 邮箱
    phone             VARCHAR(32),                          -- 手机号（短信通知用）
    backup_email      VARCHAR(255),                         -- 备用邮箱（找回账户用）
    ext_idp_userid    VARCHAR(128),                         -- 外部IdP侧的用户ID（企微userid/钉钉userId/飞书open_id/HR系统员工编码）。
                                                             -- 启用条件：§10 ext_idp.ssot_enabled=true 且配置了对应的ssot_source。
                                                             -- ON  → 外部IdP为SSOT，用户信息由外部IdP同步生成，此字段为外部系统主键。
                                                             --        写入后由 ORM 层 `@listens_for(identity_user, 'after_insert')` 事件回调自动同步到
                                                             --        identity_mapping(source_system='ext_idp', external_username=ext_idp_userid)。
                                                             --        不使用 DB trigger（避免跨表耦合与事务隐式副作用），
                                                             --        以简化 testing 与 CI 环境中的表依赖。
                                                             -- OFF → 此字段为空，Iapetus 自身为事实源，用户通过UI新建。
                                                             -- 供回调反向查询：外部系统说"userid=xxx" → 直接查此字段定位 global_user_id。
    employee_id       VARCHAR(50),                          -- 工号（自动匹配链第1优先级）
    current_dept_code VARCHAR(64),                          -- 当前所属部门编码（冗余字段，由identity_user_department SCD2变更触发器自动维护）
    title             VARCHAR(100),                         -- 职位头衔（如：高级工程师）
    employee_type     VARCHAR(16)  DEFAULT 'full_time',    -- 员工类型：full_time/contractor/intern
    locale            VARCHAR(10)  DEFAULT 'zh-CN',         -- 语言偏好（zh-CN/en）
    office_location   VARCHAR(64),                          -- 办公城市/地点（北京/武汉/远程）
    hire_date         DATE,                                 -- 入职日期
    departure_date    DATE,                                 -- 计划离职日期
    manager_user_id   CHAR(32),                             -- 直属上级global_user_id
    is_active         BOOLEAN      DEFAULT TRUE,             -- 在职/离职
    extended_attrs    JSONB,                                -- 扩展属性兜底
    password_hash     VARCHAR(256),                         -- bcrypt 密码哈希（v5.6 新增，可为 NULL）。
                                                             -- 非 NULL 时用于 iapetus-app 独立登录的本地密码验证；
                                                             -- 为 NULL 时降级到 LLDAP bind 或 Pocket-ID OIDC 认证。
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  DEFAULT NOW()
);
```

### 3.2 identity_department（部门表）

> 部门自身不追SCD2——`dept_code`作为业务编码不变，名称可改，历史记录通过编码关联。

```sql
CREATE TABLE identity_department (
    id                SERIAL       PRIMARY KEY,            -- 自增主键（内部使用，不对外）
    dept_code         VARCHAR(64)  NOT NULL UNIQUE,        -- RD01（业务编码，不改）
    dept_name         VARCHAR(128) NOT NULL,                -- 财政研发中心（可改）
    parent_id         INT          REFERENCES identity_department(id),
    dept_level        INT          NOT NULL DEFAULT 0,     -- 0公司/1中心/2部门/3组
    org_path          VARCHAR(256),                         -- company/RDC/RD01（物化路径）
    dept_leader_id    CHAR(32),                              -- 部门负责人global_user_id
    center_type       VARCHAR(32),                           -- 研发中心/交付中心/职能部门
    sort_order        INT          DEFAULT 0,               -- 同层级排序
    source_system     VARCHAR(32),                           -- 数据来源：identity_plugin/ext_idp(企微/钉钉/飞书)/ldap
    source_id         VARCHAR(128),                          -- 外部系统部门ID（企微DeptID/钉钉DeptId/飞书department_id/LDAP的DN）
    is_active         BOOLEAN      DEFAULT TRUE,             -- 部门状态：TRUE正常/FALSE已裁撤
    extended_attrs    JSONB,                                -- 扩展属性兜底
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  DEFAULT NOW()
);
```

### 3.3 identity_user_department（用户-部门归属历史表，SCD2（Slowly Changing Dimension Type 2））

> **关键变更**：`identity_user` 不存 `dept_id`，人员与部门的归属关系通过本表追踪。张三转部门时，旧记录关停、新记录开启，历史可追溯。

```sql
CREATE TABLE identity_user_department (
    id                SERIAL       PRIMARY KEY,            -- 自增主键（避免NOW()精度不足导致PK冲突）
    global_user_id    CHAR(32)     NOT NULL REFERENCES identity_user(global_user_id),
    dept_code         VARCHAR(64)  NOT NULL REFERENCES identity_department(dept_code), -- 关联本系统的部门业务编码
    -- SCD2 字段
    is_current        BOOLEAN      NOT NULL DEFAULT TRUE,   -- 当前有效版本
    effective_from    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),  -- 部门归属生效时间（入职或转部门时间）
    effective_to      TIMESTAMPTZ,                           -- 部门归属失效时间，NULL=至今有效（当前记录）
    -- 变更审计
    changed_by        CHAR(32),                              -- 操作人global_user_id
    change_reason     VARCHAR(256),                          -- 转部门/组织调整/入职
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(global_user_id, dept_code, effective_from),     -- 业务唯一性（防止同一用户同部门同时段重复记录）
    CHECK(effective_from <= effective_to OR effective_to IS NULL)  -- 生效时间≤失效时间（允许同一时刻变更，应用层保证顺序）
);
-- 轻量化建议（Phase 2 参考）：SCD2 完整实现对身份管理场景可能过重。如初期需求仅为"追溯谁何时转了部门"，可降级为变更日志模式：
-- - 每次部门变更生成一条不可变记录：{global_user_id, old_dept, new_dept, changed_by, changed_at, reason}
-- - 查询当前归属仍使用 identity_user.current_dept_code 冗余字段
-- - 按 changed_at 时间线回放即可得到任意时间点的部门归属快照
-- - 验证需求真实性后再升级为完整 SCD2（含 effective_from/effective_to/is_current）

CREATE INDEX idx_udd_current ON identity_user_department(global_user_id, is_current)
    WHERE is_current = TRUE;
```

**部门变更操作**：

```sql
-- 关旧
UPDATE identity_user_department
SET is_current = FALSE, effective_to = NOW()
WHERE global_user_id = 'U001' AND is_current = TRUE;

-- 开新
INSERT INTO identity_user_department
    (global_user_id, dept_code, is_current, effective_from, changed_by, change_reason)
VALUES ('U001', 'RD02', TRUE, NOW(), 'admin_uuid', '组织调整：调往政务研发中心');

-- 查当前归属
SELECT d.dept_name FROM identity_user_department ud
JOIN identity_department d ON d.dept_code = ud.dept_code
WHERE ud.global_user_id = 'U001' AND ud.is_current = TRUE;

-- 查某人在2025年1月的归属
SELECT d.dept_name FROM identity_user_department ud
JOIN identity_department d ON d.dept_code = ud.dept_code
WHERE ud.global_user_id = 'U001'
  AND ud.effective_from <= '2025-01-01'
  AND (ud.effective_to IS NULL OR ud.effective_to > '2025-01-01');
```

### 3.4 identity_mapping（身份映射表）

> 跨系统账号关联表。
> `ext_idp_userid`与`identity_mapping(source_system='ext_idp')`保持同步，前者是identity_user上的冗余快速索引字段，后者是完整的关系记录。

```sql
CREATE TABLE identity_mapping (
    id                SERIAL       PRIMARY KEY,            -- 自增主键（内部使用，不对外）
    global_user_id    CHAR(32)     NOT NULL REFERENCES identity_user(global_user_id),
    source_system     VARCHAR(32)  NOT NULL,                -- 目标系统：gitlab/zentao/sonarqube/nexus/jenkins/pocketid                -- gitlab/zentao/nexus/sonarqube/jenkins/pocketid
    external_user_id  VARCHAR(100),                          -- 外部系统的内部用户ID（如GitLab user_id=45，用于API操作）
    external_username VARCHAR(100),                          -- 外部系统登录名（如GitLab的zhangsan或Nexus的zhangs）
    external_email    VARCHAR(255),                          -- 外部系统登记的邮箱（用于自动匹配链第2优先级）
    mapping_status    VARCHAR(20)  NOT NULL DEFAULT 'VERIFIED',
    -- VERIFIED:    OIDC自动匹配
    -- PROVISIONED: identity_plugin创建并推送
    -- MANUAL:      管理员手动映射（老用户不同username）
    -- EXPIRED:     离职标记
    last_active_at    TIMESTAMPTZ,                           -- 最后活跃时间（OIDC登录时更新）
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(source_system, external_username)    -- [WARN] 业务上确保 external_username 非空。PostgreSQL中NULL不参与唯一约束，允许多条空值。
                                                          -- 若某系统无用户名场景不可回避，应改为部分唯一索引：
                                                          -- CREATE UNIQUE INDEX idx_mapping_unique ON identity_mapping(source_system, external_username) WHERE external_username IS NOT NULL;
                                                          --
                                                          -- 约定：external_username 为 NULL 时，由应用层自动填充 external_user_id 的值，
                                                          -- 保证唯一约束生效且避免 NULL 行堆积。
);
```

### 3.5 identity_provisioning_policy（分发策略模板）

```sql
CREATE TABLE identity_provisioning_policy (
    id                  SERIAL       PRIMARY KEY,
    role_name           VARCHAR(64)  NOT NULL UNIQUE,
    description         VARCHAR(256),                       -- 角色描述（如：研发工程师-推送全部6个系统）
    target_gitlab       BOOLEAN      NOT NULL DEFAULT FALSE,
    target_zentao       BOOLEAN      NOT NULL DEFAULT FALSE,
    target_sonarqube    BOOLEAN      NOT NULL DEFAULT FALSE,
    target_nexus        BOOLEAN      NOT NULL DEFAULT FALSE,
    target_jenkins      BOOLEAN      NOT NULL DEFAULT FALSE,
    target_pocketid     BOOLEAN      NOT NULL DEFAULT TRUE,
    is_default          BOOLEAN      NOT NULL DEFAULT FALSE, -- 是否为默认策略（新建用户时自动选中）
    created_at          TIMESTAMPTZ  DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  DEFAULT NOW()
);
```

**默认策略**：

| role_name | GitLab | Zentao | SonarQube | Nexus | Jenkins | Pocket-ID |
| ------------- | ------ | ------ | --------- | ----- | ------- | --------- |
| dev_engineer | [OK] | [OK] | [OK] | [OK] | [OK] | [OK] |
| test_engineer | [NO] | [OK] | [NO] | [NO] | [NO] | [OK] |
| pm | [NO] | [OK] | [NO] | [NO] | [NO] | [OK] |
| delivery | [NO] | [NO] | [NO] | [OK] | [NO] | [OK] |
| manager | [NO] | [OK] | [NO] | [NO] | [NO] | [OK] |
| admin | [OK] | [OK] | [OK] | [OK] | [OK] | [OK] |

### 3.6 identity_provisioning_log（分发日志表）

```sql
CREATE TABLE identity_provisioning_log (
    id                SERIAL       PRIMARY KEY,            -- 自增主键（内部使用，不对外）
    global_user_id    CHAR(32)     NOT NULL REFERENCES identity_user(global_user_id),
    source_system     VARCHAR(32)  NOT NULL,                -- 目标系统：gitlab/zentao/sonarqube/nexus/jenkins/pocketid
    action            VARCHAR(16)  NOT NULL,                -- 操作类型：create_user/suspend_user/update_user/create_dept/append/delete_user
    status            VARCHAR(16)  NOT NULL,                -- 执行状态：pending待执行/success成功/failed可重试/permanent_failed人工介入/skipped未勾选
    retry_count       INT          NOT NULL DEFAULT 0,
    max_retries       INT          NOT NULL DEFAULT 3,
    error_code        VARCHAR(32),                           -- 错误分类码：network_timeout/api_rate_limit/auth_failed/invalid_response（聚合统计用，AMDP P3.4 对齐）
    error_message     TEXT,                                 -- 失败时的错误信息（用于排查问题）
    request_payload   JSONB,                                -- 发送给目标系统的API请求体（审计追溯用）
    response_data     JSONB,
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,                          -- 执行完成时间（NULL表示尚未完成）
    -- 审计标准化字段（与 §9.3 对齐，建表时直接包含，无需 ALTER）
    event_type        VARCHAR(64)  NOT NULL DEFAULT 'provisioning.execute',
    category          VARCHAR(32)  NOT NULL DEFAULT 'operation',
    actor_username    VARCHAR(64),
    actor_ip          INET,
    compliance_tags   VARCHAR(256)[] NOT NULL DEFAULT '{}'
);
```

### 3.7 identity_user_status（用户分发状态表）

```sql
CREATE TABLE identity_user_status (
    id                      SERIAL       PRIMARY KEY,
    global_user_id          CHAR(32)     NOT NULL UNIQUE REFERENCES identity_user(global_user_id),
    provisioning_policy_id  INT          REFERENCES identity_provisioning_policy(id),
    provisioning_status     VARCHAR(16)  NOT NULL DEFAULT 'pending',
    -- pending / in_progress / completed / partial / permanent_failed
    initial_token           VARCHAR(256),                    -- Pocket-ID生成的一次性登录token（供新用户首次设置Passkey）
    created_at              TIMESTAMPTZ  DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  DEFAULT NOW()
);
```

### 3.8 identity_tag + identity_user_tag（标签系统）

> 灵活分组，不改变用户表结构。筛选"核心研发+外派"等组合标签时不需要改Schema。

```sql
CREATE TABLE identity_tag (
    id              SERIAL       PRIMARY KEY,
    tag_name        VARCHAR(64)  NOT NULL UNIQUE,        -- 标签名（如：核心研发/新员工/高管/外派）
    tag_category    VARCHAR(32),                           -- 标签分类（如team团队标签/level职级标签/project项目标签）
    color           VARCHAR(7),                            -- 标签颜色（#FF0000格式，UI前端展示用）
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE TABLE identity_user_tag (
    global_user_id  CHAR(32)     NOT NULL REFERENCES identity_user(global_user_id),
    tag_id          INT          NOT NULL REFERENCES identity_tag(id),
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    PRIMARY KEY (global_user_id, tag_id)
);
```

### 3.9 identity_user_pending（用户预创建表）

> 已确定入职但未到岗——提前录入，到hire_date自动激活Provisioning。

```sql
CREATE TABLE identity_user_pending (
    id                      SERIAL       PRIMARY KEY,
    username                VARCHAR(64)  NOT NULL UNIQUE,
    display_name            VARCHAR(128) NOT NULL,
    primary_email           VARCHAR(255),
    phone                   VARCHAR(32),
    employee_id             VARCHAR(50),
    dept_code               VARCHAR(64),
    title                   VARCHAR(100),
    employee_type           VARCHAR(16)  DEFAULT 'full_time',
    provisioning_policy_id  INT          REFERENCES identity_provisioning_policy(id),
    expected_hire_date      DATE         NOT NULL,              -- 预计入职日期（系统每天检查此字段，到期自动激活并触发Provisioning）
    status                  VARCHAR(16)  NOT NULL DEFAULT 'pending',
    -- pending: 等待入职
    -- activated: 已激活为正式用户
    activated_at            TIMESTAMPTZ,
    created_by              CHAR(32),                            -- 录入人global_user_id
    created_at              TIMESTAMPTZ  DEFAULT NOW()
);
```

### 3.10 identity_department_mapping（外部系统部门ID映射）

> 企业微信/钉钉/飞书/LDAP有各自的部门ID，通过本表与内部`dept_code`双向映射。

```sql
CREATE TABLE identity_department_mapping (
    id                SERIAL       PRIMARY KEY,            -- 自增主键（内部使用，不对外）
    dept_code         VARCHAR(64)  NOT NULL REFERENCES identity_department(dept_code), -- 关联本系统的部门业务编码
    source_system     VARCHAR(32)  NOT NULL,                -- 目标系统：gitlab/zentao/sonarqube/nexus/jenkins/pocketid                -- ext_idp(企微/钉钉/飞书)/ldap
    source_dept_id    VARCHAR(128) NOT NULL,                 -- 外部系统部门ID
    source_dept_name  VARCHAR(256),                          -- 外部系统部门名称（人工对照确认用）
    created_at        TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(source_system, source_dept_id)
);
```

### 3.11 identity_sync_event_log（外部系统同步事件日志）

> 企业微信回调/钉钉事件订阅/飞书webhook/LDAP定时同步的每一条事件跟踪。幂等防重。

````sql
CREATE TABLE identity_sync_event_log (
    id                SERIAL       PRIMARY KEY,            -- 自增主键（内部使用，不对外）
    source            VARCHAR(32)  NOT NULL,                -- 事件来源：ext_idp(企微/钉钉/飞书)/ldap/identity_plugin
    event_type        VARCHAR(32)  NOT NULL,                -- 事件类型：user_add/user_update/user_depart/dept_add/dept_update/dept_delete/unknown
    external_id       VARCHAR(128) NOT NULL,                -- 外部系统用户ID或部门ID（用于identity_mapping/department_mapping关联）
    action            VARCHAR(16)  NOT NULL,                -- 处理结果：processed已处理/skipped已跳过(重复事件)/failed处理失败
    detail            VARCHAR(512),                          -- 处理详情（成功时记录做了哪些操作，失败时记录错误原因）
    raw_payload       JSONB,                                -- 外部系统回调的原始JSON内容（用于幂等防重和事后审计）
    event_time        TIMESTAMPTZ  DEFAULT NOW(),           -- 外部系统声称的事件发生时间（非系统入库时间）
    processed_at      TIMESTAMPTZ,                          -- 本系统处理完成时间（用于监控同步延迟）
    -- 审计标准化字段（与 §9.3 对齐，建表时直接包含，无需 ALTER）
    category          VARCHAR(32)  NOT NULL DEFAULT 'sync',
    compliance_tags   VARCHAR(256)[] NOT NULL DEFAULT '{}'
);

> **日志清理策略**：`identity_provisioning_log` 和 `identity_sync_event_log` 会随操作无限增长。
> 建议保留周期 **90天**，过期数据归档到冷存储（如OSS）后清理。首次实施时在应用层配置：
> ```yaml
> retention:
>   provisioning_log_days: 90
>   sync_event_log_days: 90
>   cleanup_cron: "0 3 * * 0"   # 每周日凌晨3点执行
> ```

### 3.12 identity_provisioning_dept_map（目标系统部门分发映射）

> 向 GitLab（Group）、Zentao（部门）、Nexus（权限域）等系统推送部门结构时，目标系统返回自己的 Group/Department ID。
> 本表存储此映射，后续更新/删除操作凭此 ID 操作，避免"推了部门但找不到ID更新"。

```sql
CREATE TABLE identity_provisioning_dept_map (
    id                  SERIAL       PRIMARY KEY,
    dept_code           VARCHAR(64)  NOT NULL REFERENCES identity_department(dept_code),
    target_system       VARCHAR(32)  NOT NULL,                -- 目标系统：gitlab/zentao/nexus/pocketid
    target_group_id     VARCHAR(128) NOT NULL,                 -- 目标系统返回的 Group/Department ID
    target_group_name   VARCHAR(256),                          -- 目标系统上的组名（人工确认用）
    provisioning_action VARCHAR(16)  DEFAULT 'created',        -- created/updated/deleted
    created_at          TIMESTAMPTZ  DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE(dept_code, target_system)
);
CREATE INDEX idx_prov_dept_map_system ON identity_provisioning_dept_map(target_system, target_group_id);
````

### 3.13 extended_attrs 扩展属性约定

> `ext_idp_userid` 是 identity_user 上的冗余快速索引字段，用于外部IdP回调直查。
> `identity_mapping(source_system='ext_idp', external_username=ext_idp_userid)` 是完整的关系记录，由系统自动同步保持对齐。
> `extended_attrs`(JSONB) 存放外部IdP的完整profile。各系统约定如下：

```json
{
  "ext_idp": {
    "source": "wecom",              // wecom/dingtalk/feishu/ldap
    "avatar_url": "https://...",
    "main_dept_id": 1,
    "status": 1,
    "position": "高级工程师",
    "address": "北京市海淀区",
    "telephone": "010-12345678",
    "alias": "张三(别名)"
  },
  "ldap": {
    "dn": "uid=zhangsan,ou=people,dc=company,dc=com",
    "gecos": "张三",
    "loginShell": "/bin/bash",
    "sshPublicKey": "..."
  }
}
```

### 3.14 表关系总览（三层架构全景图）

> 本图汇总 Iapetus 完整数据模型，按三层架构组织：身份层、权限层、审计层。

```
┌──────────────────────────────────────────────────────────────────┐
│                       审计层（Audit Layer）                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  identity_audit_event（统一审计存储，RANGE分区）                    │
│    ↑ 采集自各来源表，归一化写入                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                       权限层（Permission Layer）                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  identity_permission（权限定义）                                    │
│        ↑                                                         │
│        │ N:N                                                     │
│  identity_role_permission（角色-权限关联）                          │
│        │                                                         │
│        ↓ N:N                                                     │
│  identity_role（角色）—— policy_id ——→ identity_provisioning_policy │
│        ↑                                                         │
│   ┌────┴────┐                                                    │
│   │         │                                                    │
│  N:N       N:N                                                   │
│   │         │                                                    │
│ identity_user_role  identity_dept_role                            │
│   │         │                                                    │
│   ↓         ↓                                                    │
│ identity_user  identity_department                                │
│                                                                  │
│  identity_audit_log（权限审计日志）                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────┐
│                       身份层（Identity Layer）                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  identity_department（部门树）                                     │
│       │                                                          │
│       ├── (N) identity_user_department（SCD2，人员归属历史）          │
│       │         global_user_id → identity_user                    │
│       │         dept_code     → identity_department               │
│       │                                                          │
│       ├── (N) identity_department_mapping（外部部门ID映射）          │
│       │         source_system + source_dept_id                    │
│       │                                                          │
│       └── (N) identity_provisioning_dept_map（目标系统部门分发映射）  │
│                 target_system + target_group_id                   │
│                                                                  │
│  identity_user（global_user_id PK）                                │
│       │                                                          │
│       ├── (N) identity_mapping（外部系统账号映射）                   │
│       │         source_system='ext_idp' ↔ 同步 ext_idp_userid     │
│       ├── (N) identity_provisioning_log（分发审计日志）              │
│       ├── (N) identity_user_tag（标签关联）                         │
│       │         tag_id → identity_tag                             │
│       ├── (1) identity_user_status（分发状态）                      │
│       │         provisioning_policy_id → identity_provisioning_policy │
│       ├── ext_idp_userid（冗余快速索引）                             │
│       └── current_dept_code（冗余字段，SCD2触发器维护）               │
│                                                                  │
│  identity_provisioning_policy（分发策略模板）—— policy_id ← identity_role │
│                                                                  │
│  identity_user_pending（预创建）→ 到达expected_hire_date → 激活      │
│                                                                  │
│  identity_sync_event_log（外部IdP同步事件日志）                       │
│                                                                  │
│  identity_password_retry（密码同步失败重试队列）                       │
│                                                                  │
│  identity_frontend_error_log（前端错误日志）           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.15 identity_frontend_error_log（前端错误日志表）

> 设计参考：AMDP 前端错误监控（P3.4）。复用同一套三层捕获 → 匿名上报 → 去重存储模式。

```sql
CREATE TABLE identity_frontend_error_log (
    id                SERIAL       PRIMARY KEY,
    page_url          VARCHAR(1024) NOT NULL,                  -- 错误页面 URL
    error_type        VARCHAR(32)   NOT NULL,                  -- error / unhandledrejection / vue-error
    error_message     VARCHAR(1024) NOT NULL,                  -- 错误消息摘要
    error_stack       TEXT,                                    -- 完整堆栈信息
    user_agent        VARCHAR(512),                            -- 浏览器 UA
    user_id           CHAR(32),                                -- 登录用户 global_user_id（可空，匿名上报）
    occurred_at       TIMESTAMPTZ   NOT NULL,                  -- 客户端时间戳
    count             INT           NOT NULL DEFAULT 1,        -- 去重计数
    last_occurred_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),    -- 最近一次发生时间
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- 去重索引：同一 page_url + error_type + error_message 只累加 count
CREATE UNIQUE INDEX ix_identity_frontend_error_dedup
    ON identity_frontend_error_log (page_url, error_type, error_message);

-- 按最近发生时间查询索引
CREATE INDEX ix_identity_frontend_error_last_occurred
    ON identity_frontend_error_log (last_occurred_at DESC);
```

| 注意 | 说明 |
| -------- | ------------------------------------------------------------------------ |
| 匿名接入 | POST 端点无需认证，可选 `Authorization` header 提取 user_id |
| 去重策略 | 同 `(page_url, error_type, error_message)` 只更新 count/last_occurred_at |
| 权限 | admin+ 查看/删除管理页面；上报端点完全匿名开放 |
| 量级 | 日 PV 5000 场景下预计 0-20 条/天，DB 开销可忽略 |

## 4. IdentityManager 与 ProvisioningManager

> **说明**：IdentityManager是身份服务的核心类，负责身份解析（get_global_id）、全链路追溯（resolve_chain）、映射统计。ProvisioningManager负责分发推送。

### 4.1 IdentityManager（身份解析）

```python
class IdentityManager:
    """全局身份管理器——身份校准入口。

    遵循Identity First（身份对齐优先）原则：禁止直接使用原始账号作为关联键。
    强制转换链：采集原始账号 → 调用IdentityManager → 映射为UUID → 存入业务表。
    """

    def get_global_id(self, source_system: str, external_username: str) -> str | None:
        """核心身份解析方法，按优先级匹配。

        匹配优先级：
        1. mapping_status=MANUAL（管理员手动确认的映射）
        2. mapping_status=PROVISIONED（系统创建的映射）
        3. mapping_status=VERIFIED（OIDC自动发现的映射）

        Args:
            source_system: 来源系统，如'gitlab'、'nexus'。
            external_username: 在目标系统中的账号名称。

        Returns:
            全局UUID，未找到返回None（不报错，遵循异步对齐规范）。
        """
        ...

    def resolve_chain(self, global_user_id: str) -> list[dict]:
        """全链路追溯：查看指定人员在所有系统上的映射情况。

        Returns:
            [{"source_system": "gitlab", "username": "zhangsan", "mapping_status": "VERIFIED"}, ...]
        """
        ...

    def get_mapping_stats(self) -> dict:
        """映射覆盖率统计。

        Returns:
            {"total_users": 200, "fully_mapped": 180, "unmapped": 20}
        """
        ...
```

### 4.2 ProvisioningManager（身份分发）

```python
class ProvisioningManager:
    """身份分发管理器——新增，与IdentityManager协同工作。"""

    async def provision_user(
        self,
        global_user_id: str,
        policy: ProvisioningPolicy,
        overrides: dict[str, bool] | None = None,
    ) -> dict[str, bool]:
        """按策略并行推送用户到勾选的目标系统。

        Args:
            global_user_id: 用户在identity_user中的global_user_id。
            policy: 分发策略模板。
            overrides: 管理员逐条微调的勾选覆盖（可选）。

        Returns:
            {source_system: success/fail}状态字典。
        """
        ...

    async def retry_failed_provisioning(self, global_user_id: str) -> None:
        """重试失败的provisioning记录。最多3次。"""
        ...

    async def append_provisioning(
        self,
        global_user_id: str,
        new_sources: list[str],
    ) -> dict[str, bool]:
        """增量追加provisioning——员工角色变更时追加新系统。"""
        ...
```

## 5. ProvisioningEngine 设计

### 5.1 核心逻辑

```
ProvisioningEngine.provision_user() 执行流程：

  1. 从identity_provisioning_policy加载勾选模板
  2. 管理员微调覆盖（如有）
  3. asyncio.gather并行推送6个系统（return_exceptions=True）
     ├── 某系统成功 → identity_provisioning_log记success
     │   + identity_mapping插入该系统的映射记录(mapping_status=PROVISIONED)
     ├── 某系统失败 → identity_provisioning_log记failed + 自动3次重试
     │     ├── 重试成功 → 更新为success
     │     ├── 重试仍失败 → 标记permanent_failed，管理员UI可手动重试
     ├── 未勾选的系统 → identity_provisioning_log记skipped
  4. 更新identity_user_status.provisioning_status（completed/partial/permanent_failed）
  5. Pocket-ID成功 → 生成一次性token → 发邮件通知用户设置Passkey
```

### 5.2 各系统Provisioner

```python
"""identity_service/provisioner/"""

class BaseProvisioner:
    """Provisioner基类——统一接口。"""

    async def create_user(self, global_user_id: str, username: str,
                          display_name: str, email: str) -> dict:
        raise NotImplementedError

    async def create_group(self, dept_code: str, dept_name: str) -> dict:
        return {"status": "skipped"}  # 默认跳过，不支持组的系统覆盖

    async def suspend_user(self, global_user_id: str) -> dict:
        raise NotImplementedError

    async def update_password(self, global_user_id: str, new_password: str) -> bool:
        """向目标系统推送密码变更。鉴权相关Provisioner必须实现。

        Returns:
            True 成功，False 失败（由调用方进行重试）。
        """
        return True  # 默认跳过，不支持密码同步的系统覆盖


class GitLabProvisioner(BaseProvisioner):
    """GitLab CE Provisioner — API（Application Programming Interface）: POST /api/v4/users"""

    async def create_user(self, ...) -> dict:
        # POST /api/v4/users + skip_confirmation=True
        # 更新identity_mapping: source_system='gitlab', mapping_status='PROVISIONED'
        ...

    async def create_group(self, dept_code: str, dept_name: str) -> dict:
        # POST /api/v4/groups
        ...


class ZentaoProvisioner(BaseProvisioner):
    """禅道CE Provisioner — API: POST /users (session-based)"""
    ...

class SonarQubeProvisioner(BaseProvisioner):
    """SonarQube Provisioner — API: POST /api/users/create"""
    ...

class NexusProvisioner(BaseProvisioner):
    """Nexus CE Provisioner — API: POST /service/rest/v1/security/users"""
    ...

class JenkinsProvisioner(BaseProvisioner):
    """Jenkins Provisioner — API: POST /securityRealm/createAccountByAdmin"""
    ...

class PocketIdProvisioner(BaseProvisioner):
    """Pocket-ID Provisioner — REST API创建用户+生成一次性token"""

    async def update_password(self, global_user_id: str, new_password: str) -> bool:
        """向 Pocket-ID 推送密码变更。传入明文，Pocket-ID 自行哈希。"""
        ...

class LldapProvisioner(BaseProvisioner):
    """LLDAP Provisioner — 按需推送到 LLDAP（仅需访问 LDAP 系统的用户）。

    注意：密码必须重新哈希为 LLDAP 所需格式（SSHA），不可透传 Pocket-ID 的哈希。
    参见 §11.5 密码管理 Fan-out。
    """

    async def create_user(self, ...) -> dict:
        # 调用 LLDAP API 创建用户
        ...

    async def update_password(self, global_user_id: str, new_password: str) -> bool:
        """向 LLDAP 推送密码变更。使用 passlib 重新哈希为 SSHA。"""
        ...
```

### 5.3 建人、离职、追加流程

#### 建人流程

```
管理员在 Iapetus 管理控制台点击"新建员工"
  │
  ├── 填写：username=lisi, display_name=李四, email=lisi@company.com, dept=财政研发中心
  │   选择角色：dev_engineer（自动加载勾选模板）
  │   微调（可选）：取消勾选Jenkins
  │
  ├── ① 写入identity_user：生成global_user_id="uuid-xxx"
  │    is_active=TRUE
  │
  ├── ② 写入identity_user_status：global_user_id, provisioning_policy_id, status='in_progress'
  │
  ├── ③ ProvisioningEngine并行分发（按勾选策略）
  │     ├── Pocket-ID → 创建用户 + 生成一次性token → 存入identity_user_status.initial_token
  │     ├── GitLab    → 创建用户lisi
  │     ├── Zentao    → 创建用户lisi
  │     ├── SonarQube → 创建用户lisi
  │     ├── Nexus     → 创建用户lisi
  │     └── Jenkins   → skipped（已取消勾选）
  │
  ├── ④ 每个系统成功后，写入identity_mapping：
  │    (global_user_id, source_system, external_username=lisi, mapping_status='PROVISIONED')
  │
  ├── ⑤ 更新identity_user_status：provisioning_status='completed'（或partial）
  │
  └── ⑥ 发邮件通知李四：点击链接设置Passkey
```

#### 离职流程

```
管理员点击"停用员工"
  │
  ├── identity_user.is_active → FALSE
  │
  ├── ProvisioningEngine并行分发停用：
  │     ├── Pocket-ID → 删除用户（5个OIDC系统自动不可登录）
  │     ├── GitLab    → block用户（保留数据，禁止登录）
  │     ├── Zentao    → 禁用用户
  │     ├── SonarQube → deactivate用户
  │     ├── Nexus     → 删除用户
  │     └── Jenkins   → 删除用户
  │
  ├── identity_mapping：mapping_status → 'EXPIRED'
  └── identity_provisioning_log：记录depart_user动作
```

#### 重新入职流程

> 离职员工重新入职时，**复用原有 `global_user_id`**，保留历史归属记录和映射关系。

```
管理员搜索已离职员工 → "重新激活"
  │
  ├── identity_user.is_active → TRUE（恢复在职状态）
  ├── identity_user.hire_date → 更新为新入职日期
  ├── identity_mapping：mapping_status → 'ACTIVE'（恢复所有映射）
  │     （若某些系统的账号已删除，ProvisioningEngine自动重新创建）
  │
  ├── ProvisioningEngine并行分发：
  │     ├── Pocket-ID → 重建用户（发送一次性token邮件）
  │     ├── GitLab    → unblock用户（或重建）
  │     ├── Zentao    → 启用用户（或重建）
  │     ├── SonarQube → activate用户（或重建）
  │     ├── Nexus     → 重建用户
  │     └── Jenkins   → 重建用户
  │
  ├── identity_user_department：新增一条SCD2记录（is_current=TRUE）
  └── identity_provisioning_log：记录rehire动作
```

**与新建用户的差异**：复用global_user_id → 所有历史数据（提交记录、工单、代码review）仍然归于此人，不产生新身份。

#### 追加系统流程

> 用户已在 Iapetus 中，管理员授予其更多目标系统的访问权限（如新项目需要接入 SonarQube）。

```
管理员进入用户详情页 → "追加系统"
  │
  ├── 勾选目标系统（如 SonarQube）→ 可选指定角色模板
  │
  ├── ProvisioningEngine 按需分发（仅推送新勾选的系统）：
  │     ├── SonarQube → 创建用户
  │     └── （其他已有系统不受影响，不重复推送）
  │
  ├── identity_mapping：新增新系统的映射记录
  └── identity_provisioning_log：记录 append_user 动作
```

**追加行为的语义**：

- 只处理 `new_sources`（管理员本次勾选但用户尚未映射的系统），已有系统跳过不推送。
- 已有系统同步流程（`identity_mapping.mapping_status=PROVISIONED` 且 `is_active=TRUE`）不重复调用 provisioner。
- `global_user_id` 不变；不发送入职通知邮件；不触发 Pocket-ID 重建（已有账号）。
- 追加失败的重试策略与新建流程一致（3 次重试 → permanent_failed → 管理员手动重试）。
- API 响应中 `sources_skipped` 明确列出本次追加请求中哪些 target_system 因已有映射而被跳过。

### 5.4 通知通道

> Provisioning 向非 OIDC 系统（Nexus/Zentao）创建用户时生成临时密码，必须确保密码安全到达用户。

| 通道 | 触发条件 | 内容 | 备注 |
| -------------------- | -------------------------------- | ----------------------------------------- | ----------------------------- |
| **邮件** | 新建用户 / 重新激活 | Pocket-ID一次性token + 各系统临时密码列表 | 默认通道，`primary_email`必填 |
| **短信** | 新建用户（`phone`非空） | Pocket-ID一次性token + 临时密码简要提示 | 需配置短信网关 |
| **企微/钉钉Webhook** | 新建用户（`ext_idp_userid`非空） | 同上，发送到企业IM | 需对接企微应用消息API |

模板变量说明：`{pocketid_setup_url}` 由 ProvisioningEngine 根据 `identity_user_status.initial_token` 运行时生成（Pocket-ID一次性设置链接），`{nexus_temp_password}` 和 `{zentao_temp_password}` 由 ProvisioningEngine 在创建系统账号时生成并暂存用于通知（不落库，发送即丢弃）。

配置示例（§10 config.yml 已预留 `smtp_*` 配置）：

```yaml
notification:
  email:
    smtp_host: "${SMTP（Simple Mail Transfer Protocol）_HOST}"
    smtp_port: 587
    smtp_user: "${SMTP_USER}"
    smtp_password: "${SMTP_PASSWORD}"
    from_address: "identity@company.com"
    templates:
      onboarding_subject: " 您的系统账号已开通"
      onboarding_body: |
        亲爱的 {display_name}，您好：

        您的统一账号已创建。请使用以下信息登录各系统：

        Pocket-ID（SSO登录）：https://pocketid.company.com
        一次性设置链接：{pocketid_setup_url}

        系统临时密码（请首次登录后修改）：
        - Nexus: {nexus_temp_password}
        - Zentao: {zentao_temp_password}

        公司信息技术部
  sms:
    provider: "${SMS_PROVIDER}"     # aliyun/tencent
    api_key: "${SMS_API_KEY}"
  webhook:
    wecom_url: "${WECOM_WEBHOOK_URL（Uniform Resource Locator）}"
```

当用户创建或激活完成时，ProvisioningEngine 自动调用通知通道发送密码信息。

> **密码安全**：临时密码通过邮件/短信明文传输属于必要妥协。
> 安全增强手段（实施阶段应启用至少一项）：
>
> 1. 强制首次登录修改密码（Nexus/Zentao均支持首次登录改密）
> 1. 或发送一次性安全链接（含过期时间戳的URL），用户点击后重置密码，而非直接发送明文密码
> 1. 邮件/短信中不显示密码，改为"您的系统账号已开通，请联系管理员获取初始密码"
> 1. 建议至少落实"强制改密"（对用户影响最小，安全收益最高）

### 5.5 API认证与授权

> [WARN] **所有 API 必须经过认证**。Iapetus 管理敏感身份数据，不设防等于对内网开放所有用户信息的写权限。

#### 认证机制：API Key（双Token模型）

| Token类型 | 用途 | 有效期 | 示例 |
| --------------- | -------------------------------- | -------------------- | -------------------- |
| **Admin Token** | 写操作（创建用户/改部门/调策略） | 长期（存环境变量） | `idm_admin_xxxxxxxx` |
| **Read Token** | 只读操作（resolve/lookup） | 长期（按客户端分配） | `idm_read_xxxxxxxx` |

**请求方式**：所有 API 请求必须在 Header 中携带：

```
Authorization: Bearer <token>
```

**每条路由的权限要求**（标注在路由注释中）：

| scope | 允许的操作 |
| ------- | ---------------------------------- |
| `admin` | 所有写操作 + 所有读操作 + 审计查询 |
| `read` | resolve/chain/用户查询（GET类） |

#### 授权粒度

```plaintext
POST   /identity/v1/users          → scope=admin     # 创建用户，最高权限
GET    /identity/v1/users          → scope=read       # 查询用户列表
GET    /identity/v1/resolve        → scope=read       # 身份解析，最常用接口
GET    /identity/v1/provisioning-logs → scope=admin   # 审计数据仅admin可查
```

#### Key 管理

- Admin Token 仅1个，配置在 Iapetus 环境变量 `API_ADMIN_TOKEN` 中
- Read Token 可按消费系统分配（AMDP一个、DDAP一个），从 `identity_api_keys` 表管理
- Token 泄露时轮换：Admin Token 改环境变量重启，Read Token 更新数据库记录

```sql
-- API Key 管理表（可选，仅在需要细粒度 Read Token 时建）
CREATE TABLE identity_api_key (
    id            SERIAL       PRIMARY KEY,
    client_name   VARCHAR(64)  NOT NULL,           -- 消费方名称（如 AMDP、DDAP）
    token_hash    VARCHAR(128) NOT NULL UNIQUE,     -- Token的SHA256哈希，不存明文
    scope         VARCHAR(32)  NOT NULL DEFAULT 'read',
    is_active     BOOLEAN      DEFAULT TRUE,
    created_at    TIMESTAMPTZ  DEFAULT NOW(),
    expired_at    TIMESTAMPTZ                       -- NULL表示永不过期
);
```

#### Replica 角色下的 API 限制

当 identity-module 以 role="replica" 部署时，所有写 API（POST/PATCH/DELETE）不注册，仅挂载只读路由：

| replica 路径 | 说明 |
| --------------------------------- | -------------------- |
| GET /identity/v1/resolve | [OK] 身份解析 |
| GET /identity/v1/users | [OK] 查询用户 |
| GET /identity/v1/users/{id} | [OK] 查单个用户 |
| GET /identity/v1/users/{id}/chain | [OK] 身份链 |
| POST/PATCH/DELETE | [NO] 不注册，返回404 |

______________________________________________________________________

## 6. API设计

### 6.1 核心 API（全新设计，高起点）

> 以下 API 为 Iapetus 原生设计，路由统一在 `/identity/v1/*` 下。Iapetus 不与 DDAP Admin 模块共享任何路由，
> `/admin/*` 路径为 DDAP 自有业务路由，不应作为 Iapetus 的迁移来源或兼容目标。

| 路由 | 方法 | 用途说明 |
| ----------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| `/identity/v1/mappings` | GET | 查询所有跨系统身份映射记录，返回 `{id, global_user_id, source_system, external_username, mapping_status}` 列表 |
| `/identity/v1/mappings` | POST | 管理员手工创建一条身份映射（用于老用户不同 username 的手动关联） |
| `/identity/v1/mappings/{id}` | DELETE | 删除一条身份映射记录（谨慎操作，只删映射不删用户） |
| `/identity/v1/mappings/{id}/status` | PATCH | 启用/禁用一条身份映射，禁用的映射在 resolve 时会被忽略 |
| `/identity/v1/users` | GET | 分页查询用户列表（支持 `?is_active=true&dept_id=5&keyword=张三` 过滤） |
| `/identity/v1/users/{id}` | GET | 查询单个用户的完整信息（profile + 映射 + 标签 + 分发状态） |
| `/identity/v1/export/users` | GET | 导出全量用户为 CSV 格式（用于外部系统批量导入或备份） |
| `/identity/v1/import/users` | POST | 批量导入用户数据（CSV 格式：`username,display_name,email,phone,dept_code`） |
| `/identity/v1/import/depts` | POST | 批量导入组织架构（CSV 格式：`dept_code,dept_name,parent_code,center_type`） |

### 6.2 Identity Service新增API

> 以下API是Iapetus 的核心接口，所有新系统优先使用`/identity/v1/*`前缀。
> 各API所属功能组：用户管理组、部门管理组、身份解析组（对外只读）、策略配置组（管理员）、审计追溯组（管理员）。

#### 用户管理组

> **定位**：取代管理员在5个系统手动建人的操作。一次建人、按策略自动推送到勾选系统。

```
POST   /identity/v1/users                   创建用户 + 触发Provisioning
       Body: {username, display_name, email, phone, dept_code, role, overrides}
       Response: {global_user_id, provisioning_result}

PATCH  /identity/v1/users/{id}              更新用户信息（默认不触发重新Provisioning）
       ?trigger_provisioning=true              可选参数：同时触发字段变更同步到各目标系统
       Body: {display_name, email, phone, title, ...}
       Response: {global_user_id}

POST   /identity/v1/users/{id}/depart       停用用户 + 触发depart provisioning
       Body: {departure_date}
       Response: {global_user_id, provisioning_result}

POST   /identity/v1/users/{id}/retry        重试该用户所有失败系统的provisioning
       Response: {global_user_id, provisioning_result}

POST   /identity/v1/users/{id}/append       增量追加系统（员工角色变更时使用）
       Body: {new_systems: ["jenkins"]}
       Response: {global_user_id, provisioning_result}
```

**创建用户请求体字段说明**：

```json
{
  "username": "lisi",                  // 统一登录名。新用户在所有系统使用同名，老用户通过identity_mapping映射不同名
  "display_name": "李四",                // 中文显示名
  "email": "lisi@company.com",            // 公司邮箱。自动匹配链第2优先级
  "phone": "13800138000",              // 手机号。短信通知Pocket-ID一次性token用
  "dept_code": "RD01",                 // 部门业务编码。Provisioning时自动写入identity_user_department(SCD2)
  "role": "dev_engineer",              // 角色名。自动加载对应的identity_provisioning_policy模板，确定推送哪些系统
  "title": "高级工程师",                 // 职位头衔。推送到各系统的profile字段
  "employee_type": "full_time",        // 员工类型：full_time/contractor/intern。实习生不推送Jenkins
  "overrides": {                       // 选填。对policy模板的逐条覆盖
    "target_jenkins": false            // 例：dev_engineer默认推Jenkins，但这位员工暂不需要
  }
}
```

**创建用户响应体字段说明**：

```json
{
  "global_user_id": "uuid-xxx-001",        // 生成的全局用户UUID。此后所有系统通过此ID识别同一个人
  "initial_token": "abc123",               // Pocket-ID一次性登录token。邮件发送给用户设置Passkey
  "provisioning_result": {                 // 各系统Provisioning结果
    "pocketid":   {"status": "success"},   // Pocket-ID创建成功。用户可登录SSO
    "gitlab":     {"status": "success", "external_user_id": "45"},  // GitLab user_id=45，用于后续API操作
    "zentao":     {"status": "success"},   // Zentao创建成功
    "sonarqube":  {"status": "success"},   // SonarQube创建成功
    "nexus":      {"status": "success"},   // Nexus创建成功
    "jenkins":    {"status": "skipped"}    // skipped=未勾选(如上例overrides设了false)，failed=可重试
  }
}
```

#### 部门管理组

> **定位**：取代管理员在多个系统分别建部门的操作。部门创建后自动推送到支持组概念的系统（GitLab Group、Zentao部门、Pocket-ID组）。

```
POST   /identity/v1/depts/{code}/transfer-members   批量转移部门成员到目标部门
       Body: {target_dept_code, user_ids: ["uuid1", "uuid2"], change_reason: "组织调整"}
       → 自动完成：
         ① 关停每个用户的当前SCD2记录（effective_to=NOW, is_current=FALSE）
         ② 为每个用户创建新SCD2记录（dept_code=target_dept_code, is_current=TRUE）
         ③ identity_user.current_dept_code → target_dept_code
         ④ 记录identity_user_department.change_reason
       Response: {processed: 15, failed: 0, user_ids: [...]}
```

```
POST   /identity/v1/depts                 创建部门 + 触发group provisioning
       Body: {dept_code, dept_name, parent_code, center_type, dept_leader_id}
       Response: {dept_code, provisioning_result}

PATCH  /identity/v1/depts/{code}          更新部门信息（部门改名不触发重新Provisioning）
       Body: {dept_name, dept_leader_id, ...}

POST   /identity/v1/depts/{code}/depart   停用部门（人员必须先转部门，不能直接删）
```

#### 身份解析组（对外只读，所有业务系统调用）

> **定位**：最核心的对外接口。任何系统想知道"Nexus的zhangs是谁"，就调这个API。
> 它是全司身份统一的桥梁——每个系统只需维护自己的`(source_system, external_username)`，由identity_service返回全局`global_user_id`。

```
GET    /identity/v1/resolve               核心：将(来源系统, 用户名)解析为全局用户ID
       ?source_system=nexus&external_username=zhangs
       → {"global_user_id": "uuid-xxx", "mapping_status": "MANUAL", "profile": {"username": "zhangsan", "display_name": "张三"}}
       → 未命中返回404，系统响应超时自动降级为local pending

GET    /identity/v1/{global_user_id}/chain 全链路追溯：查看某人在所有系统的账号映射
       → [{"source_system":"gitlab",  "external_username":"zhangsan", "mapping_status":"VERIFIED"},
           {"source_system":"nexus",   "external_username":"zhangs",   "mapping_status":"MANUAL"},
           {"source_system":"zentao",  "external_username":"zs001",    "mapping_status":"MANUAL"}]

GET    /identity/v1/stats                 映射覆盖率统计（用于数据迁移或日常检查）
       → {"total_users":200, "fully_mapped":180, "unmapped":20, "by_source": {"nexus_manual":15, "zentao_manual":10}}
```

#### 策略配置组（管理员）

> **定位**：管理分发策略模板。建人时选角色→自动勾选目标系统。可预设6种默认角色，管理员也可自定义。

```
GET    /identity/v1/policies              列出所有策略模板
       → [{id:1, role_name:"dev_engineer", target_gitlab:true, ...}]

POST   /identity/v1/policies              新建策略模板
       Body: {role_name, target_gitlab, target_zentao, ...}

PATCH  /identity/v1/policies/{id}         更新策略模板（已关联的用户不受影响，新用户使用新模板）
```

#### 审计追溯组（管理员）

> **定位**：Provisioning操作的完整审计链。记录了"谁、在什么时间、向哪个系统、推送了什么操作、成功还是失败"。

```
GET    /identity/v1/provisioning-logs     查询分发日志
       ?global_user_id=xxx&status=failed&source_system=jenkins&date_from=2026-01-01
       → 支持多维筛选：按用户/按系统/按状态/按时间段
       → [{id, global_user_id, source_system, action, status, retry_count, error_message, ...}]

POST   /identity/v1/provisioning-logs/{id}/retry  手动重试单条失败的provisioning操作
       Response: {status, new_status}
```

## 7. 代码结构

### 7.1 独立服务目录结构

```
identity_service/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py              # FastAPI entry，uvicorn 启动
  │   ├── config.py            # 环境配置加载
  │   │
  │   ├── models/              # SQLAlchemy 模型（身份层 + 权限层 + 审计层）
  │   │   ├── user.py, department.py, mapping.py, policy.py
  │   │   ├── log.py, status.py, tag.py, pending.py
  │   │   ├── role.py, permission.py         # §8 RBAC 权限模型
  │   │   ├── audit_event.py                 # §9 统一审计日志
  │   │   └── frontend_error_log.py          # §3.15 前端错误日志
  │   │
  │   ├── schemas/             # Pydantic 请求/响应模型
  │   │
  │   ├── services/
  │   │   ├── identity_manager.py      # IdentityManager（身份解析）
  │   │   ├── provisioning_manager.py  # ProvisioningManager（分发管控）
  │   │   ├── authorization.py         # §8 AuthorizationManager（RBAC 权限校验）
  │   │   └── audit.py                 # §9 审计日志采集/查询服务
  │   │
  │   ├── api/                 # FastAPI 路由（/identity/v1/*）
  │   │   ├── users.py, departments.py, mappings.py
  │   │   ├── roles.py, permissions.py    # §8 权限管理 API
  │   │   ├── audit.py                    # §9 审计查询 API
  │   │   ├── frontend_errors.py          # 前端错误上报 API
  │   │   └── auth_config.py              # §11 双模式认证配置 API
  │   │
  │   ├── provisioner/         # 6 个系统适配器
  │   │   ├── engine.py        # ProvisioningEngine
  │   │   ├── base.py          # BaseProvisioner
  │   │   ├── gitlab.py, zentao.py, sonarqube.py
  │   │   └── nexus.py, jenkins.py, pocketid.py
  │   │
  │   ├── auth_provider/       # §11 双模式认证提供者
  │   │   ├── base.py          # AuthProvider 抽象基类
  │   │   ├── oidc.py          # OIDC Provider（Pocket-ID）
  │   │   └── ldap.py          # LDAP Provider（LLDAP）
  │   │
  │   ├── notification/        # §10 通知服务内置模块
  │   │   ├── email_sender.py  # SMTP 邮件发送器
  │   │   └── template_renderer.py  # 消息模板渲染器
  │   │
  │   └── cron/                # 定时任务（同步、清理、健康检查）
  │
  ├── alembic/                 # 数据库迁移
  ├── tests/                   # 测试
  ├── docker-compose.yml       # identity_service + identity_db(PG)
  └── Dockerfile
```

### 7.2 初始数据导入

> Iapetus 为全新设计，不依赖任何已有系统的数据库或路由。首次部署时的数据来源：

```
导入流程：
  1. 准备好用户/部门/映射数据（CSV 格式，字段对齐 identity_* 表）
  2. 通过 POST /identity/v1/import/users 导入用户
  3. 通过 POST /identity/v1/import/depts 导入组织架构
  4. 通过 POST /identity/v1/mappings 建立跨系统映射
  5. 验证数据完整性（总用户数、映射覆盖率）
  6. 配置各系统的 OIDC/LDAP 认证指向 Identity Service
```

**从第一天起，身份数据完全由 Iapetus 自主管理。**

## 8. 权限管理（RBAC）

> 本章整合自§8v1.5。定义细粒度 RBAC 权限模型、AuthorizationManager 服务层、API 扩展与 Break-Glass 紧急通道。

**版本**：v1.5
**日期**：2026-06-27
**关联文档**：《Iapetus 设计方案》v5.0
**整合方式**：本方案作为 §8 并入主设计，与方案A/方案B并列

**v1.5 变更**：§2.7 `identity_audit_log` 建表语句新增审计标准化字段（`event_type`/`category`/`target_type`/`target_id`/`target_name`/`compliance_tags`），与 §9.3 对齐。
**v1.4 变更**：明确 `identity_provisioning_policy` 不废弃，`identity_role` 通过 `policy_id` 外键关联，权限管理与分发策略各自独立演进。

______________________________________________________________________

### 8.1 定位与设计目标

#### 8.1.1 定位

本扩展在现有 **身份（Identity）** 和 **组织（Department）** 底座之上，新增一层 **权限管理层（Authorization Layer）**，使 Iapetus 从"身份数据源"升级为"身份+权限数据源"，为全公司系统提供**统一的身份认证与权限决策**能力。

扩展后，Iapetus 的总架构变为：
┌──────────────────────────────────────────────────────────────────┐
│ Identity Service │
├──────────────────────────────────────────────────────────────────┤
│ 身份层 (Identity Layer) │ 权限层 (Authorization) │
│ - identity_user │ - identity_permission │
│ - identity_department │ - identity_role ──policy_id──> │
│ - identity_mapping │ - identity_user_role │
│ - identity_provisioning_policy ◄─┘ - identity_dept_role │
│ - identity_provisioning │ │
├──────────────────────────────────┴────────────────────────────────┤
│ Provisioning Engine │
│ (分发身份 + 分发权限角色) │
└──────────────────────────────────────────────────────────────────┘

#### 8.1.2 设计目标

| 目标 | 说明 |
| :---------------- | :------------------------------------------------- |
| **角色管理** | 支持自定义角色，角色可绑定任意数量权限（权限集） |
| **RBAC 权限控制** | 基于角色的访问控制，用户通过角色获得权限 |
| **API 权限** | 对后端接口的访问权限控制（如 `user:create`） |
| **菜单权限** | 前端菜单/按钮的可见性控制，与API权限联动 |
| **数据权限** | 支持按部门、按用户、按资源归属等维度进行数据级过滤 |
| **权限继承** | 用户可从所属部门自动继承角色/权限（减少重复配置） |
| **审计合规** | 记录所有权限变更和鉴权行为，支持追溯 |

______________________________________________________________________

### 8.2 数据模型扩展

#### 8.2.1 新增表概览

| 表名 | 用途 |
| :------------------------- | :--------------------------------------------------------------------------------------- |
| `identity_permission` | 权限定义表（API权限 + 菜单权限） |
| `identity_role` | 角色定义表（通过 `policy_id` 外键关联 `identity_provisioning_policy`，保持分发策略独立） |
| `identity_role_permission` | 角色-权限关联表 |
| `identity_user_role` | 用户-角色分配表 |
| `identity_dept_role` | 部门-角色分配表（用于权限继承） |
| `identity_audit_log` | 权限审计日志表 |

#### 8.2.2 identity_permission（权限定义表）

```sql
CREATE TABLE identity_permission (
    id SERIAL PRIMARY KEY,
    permission_code VARCHAR(128) NOT NULL UNIQUE,          -- 权限唯一标识，如 'user:create'
    permission_type VARCHAR(16) NOT NULL,                  -- 'api' | 'menu' | 'button'
    resource_path VARCHAR(512),                            -- API路径 或 前端路由
    method VARCHAR(8),                                     -- HTTP方法 (GET/POST/PATCH/DELETE)
    menu_parent_code VARCHAR(128),                         -- 菜单层级关系 (父菜单code)
    menu_order INT DEFAULT 0,                              -- 菜单排序
    icon VARCHAR(64),                                      -- 菜单图标
    description VARCHAR(256),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP2 DEFAULT NOW(),
    updated_at TIMESTAMP2 DEFAULT NOW()
);

CREATE INDEX idx_permission_type ON identity_permission(permission_type);
CREATE INDEX idx_permission_resource ON identity_permission(resource_path);
```

权限编码规范：采用 资源:操作 格式，如：

user:create, user:update, user:delete, user:list, user:view

dept:create, dept:update, dept:delete, dept:list

role:manage, permission:manage

menu:dashboard, menu:user_management, menu:permission_management

#### 8.2.3 identity_role（角色定义表）

````sql
CREATE TABLE identity_role (
    id SERIAL PRIMARY KEY,
    role_code VARCHAR(64) NOT NULL UNIQUE,                 -- 角色编码，如 'sys_admin', 'dept_admin'
    role_name VARCHAR(128) NOT NULL,                       -- 角色显示名，如 '系统管理员'
    role_type VARCHAR(16) NOT NULL DEFAULT 'custom',       -- 'system' (系统内置) | 'custom' (自定义)
    description VARCHAR(256),
    policy_id INT REFERENCES identity_provisioning_policy(id) ON DELETE SET NULL,  -- 关联分发策略（不替代，保持独立）
    is_default BOOLEAN DEFAULT FALSE,                      -- 新建用户时自动分配
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP2 DEFAULT NOW(),
    updated_at TIMESTAMP2 DEFAULT NOW()
);

-- 设计说明：
-- identity_role 只负责权限控制（RBAC），不包含 Provisioning 分发目标字段。
-- 分发策略（target_gitlab/target_zentao 等）保留在 identity_provisioning_policy 表中，
-- 通过 policy_id 外键与 identity_role 建立松散关联。一个角色可以关联一个分发策略，
-- 也可以不关联（纯权限角色，不触发 Provisioning）。多个角色可以共享同一个分发策略。
-- 这样权限管理与分发管理各自独立演进，互不耦合。

#### 8.2.4 identity_role_permission（角色-权限关联表）

```sql
CREATE TABLE identity_role_permission (
    role_id INT NOT NULL REFERENCES identity_role(id) ON DELETE CASCADE,
    permission_id INT NOT NULL REFERENCES identity_permission(id) ON DELETE CASCADE,
    created_at TIMESTAMP2 DEFAULT NOW(),
    PRIMARY KEY (role_id, permission_id)
);

#### 8.2.5 identity_user_role（用户-角色分配表）

```sql
CREATE TABLE identity_user_role (
    id SERIAL PRIMARY KEY,
    global_user_id CHAR(32) NOT NULL REFERENCES identity_user(global_user_id) ON DELETE CASCADE,
    role_id INT NOT NULL REFERENCES identity_role(id) ON DELETE CASCADE,
    scope_type VARCHAR(16),                                -- 'global' | 'dept' | 'project' | 'custom'
    scope_value VARCHAR(128),                              -- 如 dept_code='RD01'
    granted_by CHAR(32),                                   -- 授权人 global_user_id
    granted_at TIMESTAMP2 DEFAULT NOW(),
    expired_at TIMESTAMP2,                                 -- 角色过期时间（临时授权）
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(global_user_id, role_id, scope_type, scope_value)
);

CREATE INDEX idx_user_role_user ON identity_user_role(global_user_id);
CREATE INDEX idx_user_role_scope ON identity_user_role(scope_type, scope_value);
数据权限实现：scope_type + scope_value 字段是实现数据权限的关键。例如：

给用户 zhangsan 分配 dept_admin 角色，scope_type='dept'，scope_value='RD01'，表示他只能管理 RD01 部门的数据

scope_type='global'，scope_value=NULL 表示全量权限（如系统管理员）

#### 8.2.6 identity_dept_role（部门-角色分配表，用于权限继承）

```sql
CREATE TABLE identity_dept_role (
    id SERIAL PRIMARY KEY,
    dept_code VARCHAR(64) NOT NULL REFERENCES identity_department(dept_code) ON DELETE CASCADE,
    role_id INT NOT NULL REFERENCES identity_role(id) ON DELETE CASCADE,
    scope_type VARCHAR(16) DEFAULT 'dept_self',            -- 'dept_self' 仅本部门 | 'dept_tree' 包含子部门
    granted_by CHAR(32),
    granted_at TIMESTAMP2 DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(dept_code, role_id)
);

CREATE INDEX idx_dept_role_dept ON identity_dept_role(dept_code);

**深层组织继承算法**：权限继承不仅限于用户直属部门，需沿组织树向上递归至根节点。

```
算法：get_user_permissions(global_user_id) → list[str]

  Step 1: 获取用户直属部门 dept_code（从 identity_user.current_dept_code 或
          is_current=TRUE 的 identity_user_department 记录）
  Step 2: 以直属部门为起点，沿 identity_department.parent_id 向上遍历，
          收集所有祖辈 dept_code（逐级 SELECT parent_id，终止条件 parent_id IS NULL）
  Step 3: 查 identity_dept_role，获取 ancestors 中所有部门关联的角色
          (scope_type: dept_self → 仅该部门 / dept_tree → 含子部门)
  Step 4: 查 identity_role_permission + identity_permission，展开角色 → 权限列表
  Step 5: 查 identity_user_role，获取直接分配的角色 → 权限列表
  Step 6: 合并去重（直接分配优先于继承，子部门优先于祖辈）
  Step 7: 缓存 — Python 进程内 @lru_cache (maxsize=2048)，
          通过 identity_permission_version 表的 version 整数值判断失效，
          角色/权限变更时对该表执行 UPDATE version = version + 1 WHERE table_name = 'identity_role'
```

例子：张三属于 RD01 → RD01 的 parent 是 RDC → RDC 的 parent 是 Company。
若 RDC 关联 `dept_engineer` 角色，张三自动获得此角色的权限（无论 RD01 是否直接关联了该角色）。

叠加规则：用户的最终权限 = 用户直接分配的权限 ∪ 从部门继承的权限。当发生冲突时，以更具体的（用户直接分配）为准。

#### 8.2.7 identity_audit_log（权限审计日志表）

```sql
CREATE TABLE identity_audit_log (
    id SERIAL PRIMARY KEY,
    global_user_id CHAR(32) REFERENCES identity_user(global_user_id),
    username VARCHAR(64),                                  -- 冗余字段，便于查询
    action VARCHAR(32) NOT NULL,                           -- login | logout | permission_check | role_assign | role_revoke | permission_change
    resource VARCHAR(256),                                 -- 操作资源，如 '/identity/v1/users'
    permission_code VARCHAR(128),                          -- 涉及权限，如 'user:create'
    result VARCHAR(16) NOT NULL,                           -- 'allow' | 'deny' | 'success' | 'failure'
    detail JSONB,                                          -- 额外上下文信息
    ip_address INET,
    user_agent TEXT,
    -- 审计标准化字段（与 §9.3 对齐）
    event_type VARCHAR(64) NOT NULL DEFAULT '',            -- 事件类型，如 permission.check_deny / role.assign / data.scope_applied
    category VARCHAR(32) NOT NULL DEFAULT 'permission',    -- 审计分类，固定为 permission
    target_type VARCHAR(64),                               -- 目标类型，如 user / role / permission
    target_id VARCHAR(128),                                -- 目标 ID
    target_name VARCHAR(256),                              -- 目标名称（冗余，便于查询）
    compliance_tags VARCHAR(256)[] NOT NULL DEFAULT '{}',  -- 合规标签数组，如 {iso27001,dsl}
    created_at TIMESTAMP2 DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON identity_audit_log(global_user_id);
CREATE INDEX idx_audit_time ON identity_audit_log(created_at DESC);
CREATE INDEX idx_audit_action ON identity_audit_log(action);

#### 8.2.8 表关系总览

identity_permission (权限定义)
       ↑
       │ N:N
identity_role_permission
       │
       ↓ N:N
identity_role (角色) ────── policy_id ──────> identity_provisioning_policy (分发策略，保留不废弃)
       ↑
       │ N:N
┌──────┴──────┐
│             │
N:N          N:N
│             │
identity_user_role    identity_dept_role
│             │
↓             ↓
identity_user       identity_department
(用户)              (部门)

### 8.3 核心服务层：AuthorizationManager

在现有 IdentityManager 和 ProvisioningManager 之外，新增 AuthorizationManager。

#### 8.3.1 核心方法定义

```python
class AuthorizationManager:
    """权限管理器 —— 负责权限加载、校验、缓存"""

    async def get_user_permissions(self, global_user_id: str) -> list[str]:
        """
        获取用户所有有效权限列表（去重）。
        来源：1) 直接分配的角色 → 权限  2) 部门继承的角色 → 权限
        缓存：使用 Python 进程内 @lru_cache（maxsize=2048），通过 identity_permission_version 表版本号判断失效（角色/权限变更时 UPDATE version = version + 1 WHERE table_name = 'identity_role'），缓存命中时对比版本号决定是否刷新。
        """
        pass

    async def get_user_roles(self, global_user_id: str) -> list[dict]:
        """获取用户所有有效角色及其数据范围（用于前端显示及权限校验）"""
        pass

    async def get_user_menu_tree(self, global_user_id: str) -> list[dict]:
        """根据用户权限，构建菜单树（用于前端动态渲染）"""
        pass

    async def has_permission(
        self,
        global_user_id: str,
        permission_code: str,
        resource_context: dict | None = None
    ) -> bool:
        """核心权限校验：用户是否拥有某权限？（支持数据权限上下文）"""
        pass

    async def has_data_permission(
        self,
        global_user_id: str,
        target_dept_code: str | None = None,
        target_global_user_id: str | None = None
    ) -> bool:
        """数据权限校验：用户是否有权访问指定部门或用户的数据？"""
        pass

    async def filter_by_dept_scope(
        self,
        global_user_id: str,
        dept_codes: list[str] | None = None
    ) -> list[str] | None:
        """
        数据权限过滤：从部门列表中，过滤出用户有权访问的部门。
        返回 None 表示无限制（系统管理员）
        """
        pass

    async def invalidate_cache(self, global_user_id: str) -> None:
        """主动失效用户权限缓存（角色/权限变更后调用）"""
        pass

    async def log_audit(
        self,
        global_user_id: str,
        action: str,
        resource: str,
        permission_code: str,
        result: str,
        detail: dict | None = None
    ) -> None:
        """写入审计日志"""
        pass

#### 8.3.2 数据权限实现策略：全局 Repository 拦截器

核心原则：数据权限必须物理强制，而非依赖开发者记忆。所有查询自动应用数据权限，消灭人工 `filter_by_dept_scope` 调用。

###### 两层架构

````

Request → AuthorizationManager.get_data_scope(user_id)
│
▼ 返回 DataScope 对象（dept_codes=[...] 或 None=全量）
│
Repository → BaseRepository.\_apply_data_scope(query, scope)
│
▼ 自动注入 WHERE 条件
│
→ 执行查询 + 日志记录

````

| 场景 | 实现方式 |
|------|---------|
| 部门管理员只能查看本部门数据 | `DataScope(dept_codes=['RD01'])` → 拦截器自动注入 `WHERE dept_code IN ('RD01')` |
| 系统管理员查看全量 | `DataScope.ALL` → 拦截器不追加任何 WHERE 条件 |
| 用户只能查看自己创建的数据 | 通过 `AuthorizationManager.has_data_permission()` 结合业务上下文（如 `created_by` 字段）校验 |
| 多维交叉权限 | 可扩展 `DataScope` 支持 `project`、`region` 等维度组合 |

###### 三个关键约束

**1. 旁路机制（Bypass）**

定时任务、Break-Glass、跨部门统计报表等场景需要跳过数据权限：

```python
@skip_data_permission  # 显式声明跳过
async def get_cross_dept_report(self): ...
```

**2. 表与字段的映射契约**

拦截器不猜测字段名，每个受控 Model 需声明数据权限锚点：

```python
class IdentityUser(BaseModel):
    __data_scope_field__ = "dept_code"  # 声明本表的数据权限过滤字段

class Project(BaseModel):
    __data_scope_field__ = "owner_dept"  # 不同表可有不同字段名
```

**3. 可观测性（日志）**

每次拦截器注入 SQL 条件时记录日志，确保调试时可追溯：

```
[DataScope] user=zhangsan, scope=dept:RD01, table=identity_user, applied_filter=dept_code IN ('RD01')
```

###### 与 AuthorizationManager 的协作

- `AuthorizationManager.get_data_scope(user_id)` → 计算数据范围，返回 `DataScope` 对象
- `BaseRepository._apply_data_scope(query, scope)` → 物理注入 SQL 条件
- Service 层不再手动调用 `filter_by_dept_scope`，只需在初始化 Repository 时传入 `DataScope`

### 8.4 API 扩展

#### 8.4.1 权限管理组（管理员专用）

| 方法 | 路径 | 所需权限 | 说明 |
|------|------|----------|------|
| GET | `/identity/v1/permissions` | `permission:manage` | 查询所有权限列表（分页/按类型过滤） |
| POST | `/identity/v1/permissions` | `permission:manage` | 创建新权限 |
| PATCH | `/identity/v1/permissions/{id}` | `permission:manage` | 更新权限 |
| DELETE | `/identity/v1/permissions/{id}` | `permission:manage` | 删除权限 |
| GET | `/identity/v1/roles` | `role:manage` | 查询所有角色列表（分页） |
| POST | `/identity/v1/roles` | `role:manage` | 创建新角色 |
| GET | `/identity/v1/roles/{id}` | `role:manage` | 查询角色详情（含关联权限列表） |
| PATCH | `/identity/v1/roles/{id}` | `role:manage` | 更新角色 |
| DELETE | `/identity/v1/roles/{id}` | `role:manage` | 删除角色 |
| POST | `/identity/v1/roles/{id}/permissions` | `role:manage` | 为角色绑定权限 |
| DELETE | `/identity/v1/roles/{id}/permissions/{perm_id}` | `role:manage` | 解绑权限 |

#### 8.4.2 用户-角色分配组

| 方法 | 路径 | 所需权限 | 说明 |
|------|------|----------|------|
| GET | `/identity/v1/users/{id}/roles` | `user:view` | 查询用户的所有角色 |
| POST | `/identity/v1/users/{id}/roles` | `user:assign_role` | 为用户分配角色 |
| DELETE | `/identity/v1/users/{id}/roles/{role_id}` | `user:assign_role` | 移除用户角色 |
| PATCH | `/identity/v1/users/{id}/roles/{role_id}/scope` | `user:assign_role` | 修改数据范围 |

#### 8.4.3 部门-角色分配组

| 方法 | 路径 | 所需权限 | 说明 |
|------|------|----------|------|
| GET | `/identity/v1/depts/{code}/roles` | `dept:view` | 查询部门的角色 |
| POST | `/identity/v1/depts/{code}/roles` | `dept:assign_role` | 为部门关联角色 |
| DELETE | `/identity/v1/depts/{code}/roles/{role_id}` | `dept:assign_role` | 移除部门角色 |

#### 8.4.4 当前用户权限查询（供前端使用）

| 方法 | 路径 | 所需权限 | 说明 |
|------|------|----------|------|
| GET | `/identity/v1/me/permissions` | 无（需认证） | 查询当前用户的所有权限列表 |
| GET | `/identity/v1/me/menus` | 无（需认证） | 查询当前用户的菜单树 |
| GET | `/identity/v1/me/roles` | 无（需认证） | 查询当前用户的角色列表 |

#### 8.4.5 权限审计日志组

| 方法 | 路径 | 所需权限 | 说明 |
|------|------|----------|------|
| GET | `/identity/v1/audit-logs` | `audit:view` | 查询审计日志（按用户/时间/操作过滤） |

#### 8.4.6 与现有 API 的整合（权限标签）

现有 API 需增加权限标签，作为内部文档和权限校验的依据：

| 现有路由 | 所需权限 |
|----------|----------|
| `POST /identity/v1/users` | `user:create` |
| `PATCH /identity/v1/users/{id}` | `user:update` |
| `GET /identity/v1/users` | `user:list` |
| `GET /identity/v1/users/{id}` | `user:view` |
| `POST /identity/v1/users/{id}/depart` | `user:delete` |
| `POST /identity/v1/depts` | `dept:create` |
| `PATCH /identity/v1/depts/{code}` | `dept:update` |
| `POST /identity/v1/depts/{code}/transfer-members` | `dept:update` |
| `GET /identity/v1/resolve` | 无（公开接口，但需认证） |
| `GET /identity/v1/{id}/chain` | 无（公开接口，但需认证） |
| `GET /identity/v1/provisioning-logs` | `audit:view` |
| `POST /identity/v1/provisioning-logs/{id}/retry` | `provisioning:retry` |

### 8.5 与 fast-api-jwt-middleware 的整合

#### 8.5.1 整合位置

在 identity_service/app/main.py 中：

```python
from fast_api_jwt_middleware import AuthMiddleware
from identity_service.services.authorization_manager import AuthorizationManager

# --- 1. 添加 OIDC 认证中间件 ---
app.add_middleware(
    AuthMiddleware,
    oidc_discovery_url=config.pocketid.discovery_url,
    roles_key="roles",  # 从 Pocket-ID JWT 中提取角色字段
)

# --- 2. 权限校验依赖注入 ---
async def require_permission(permission_code: str):
    async def dependency(
        request: Request,
        auth_mgr: AuthorizationManager = Depends(get_auth_manager),
    ):
        # 从 request.state 获取用户身份（由 AuthMiddleware 注入）
        user_payload = getattr(request.state, "user_payload", {})
        global_user_id = user_payload.get("sub")

        # 校验权限
        if not await auth_mgr.has_permission(global_user_id, permission_code):
            # 记录审计日志
            await auth_mgr.log_audit(
                global_user_id=global_user_id,
                action="permission_check",
                resource=request.url.path,
                permission_code=permission_code,
                result="deny"
            )
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # 记录允许
        await auth_mgr.log_audit(
            global_user_id=global_user_id,
            action="permission_check",
            resource=request.url.path,
            permission_code=permission_code,
            result="allow"
        )
        return user_payload
    return Depends(dependency)

# --- 3. 在路由中使用 ---
@app.post("/identity/v1/users")
async def create_user(
    user_data: UserCreateSchema,
    _: dict = Depends(require_permission("user:create")),
    db: AsyncSession = Depends(get_db),
    request: Request,
):
    manager = IdentityManager(db)
    provisioners = getattr(request.app.state, "identity_provisioners", [])
    manager.set_provisioners(provisioners)
    return await manager.create_user(user_data)

#### 8.5.2 数据权限在 Service 层的应用（拦截器模式）

~~~python
class UserService:
    def __init__(self, repo: BaseRepository, auth_mgr: AuthorizationManager):
        self.repo = repo
        self.auth_mgr = auth_mgr

    async def list_users(self, current_user_id: str, filters: dict):
        # 1. 获取当前用户的数据范围（一次性计算，可跨请求缓存）
        data_scope = await self.auth_mgr.get_data_scope(current_user_id)

        # 2. 查询自动应用数据权限（无需手动 filter_by_dept_scope）
        #    BaseRepository 拦截器根据 data_scope 自动注入 WHERE 条件
        return await self.repo.list(
            model=IdentityUser,
            scope=data_scope,        # ← 拦截器自动过滤
            filters=filters           # 业务过滤条件
        )

    async def get_user_detail(self, current_user_id: str, target_global_user_id: str):
        data_scope = await self.auth_mgr.get_data_scope(current_user_id)
        return await self.repo.get_by_id(
            model=IdentityUser,
            id=target_global_user_id,
            scope=data_scope           # 拦截器校验：目标用户是否在当前数据范围内
        )

### 8.6 与 Provisioning 的整合

#### 8.6.1 权限与 Provisioning 的协作

`identity_role` 通过 `policy_id` 外键关联 `identity_provisioning_policy`，两者保持独立、各司其职：

- **identity_role**：负责权限控制（RBAC），定义角色拥有的权限集
- **identity_provisioning_policy**：负责分发策略，定义目标系统和推送规则

Provisioning 流程增强为：

新建用户流程（权限扩展版）：
1. 写入 identity_user
2. 为用户分配角色（如 dept_admin）
   → 写入 identity_user_role (含 scope_type/scope_value)
3. 根据角色关联的 policy_id，查询对应的 identity_provisioning_policy
   → 获取 target_gitlab/target_zentao 等分发目标
4. 调用 ProvisioningEngine 向各系统分发用户
5. 同时可选的：将用户角色信息同步到各目标系统（如 GitLab 的 Group/权限）

#### 8.6.2 多系统权限同步（可选增强）

如果目标系统（如 GitLab、Jenkins）也支持细粒度权限，可以通过 Provisioning 适配器将角色映射为各系统的权限组。例如：

dept_admin → GitLab Maintainer 权限 → 映射为 access_level=40

这可以通过在 GitLabProvisioner 中读取用户的角色信息并同步到目标系统的 Group 权限来实现。

### 8.7 种子数据设计（初始化角色与权限）

#### 8.7.1 内置权限列表

| permission_code | permission_type | resource_path | 说明 |
|---|---|---|---|
| user:list | api | /identity/v1/users | 查看用户列表 |
| user:view | api | /identity/v1/users/{id} | 查看用户详情 |
| user:create | api | /identity/v1/users POST | 创建用户 |
| user:update | api | /identity/v1/users/{id} PATCH | 更新用户 |
| user:delete | api | /identity/v1/users/{id}/depart | 停用用户 |
| user:assign_role | api | /identity/v1/users/{id}/roles | 分配角色 |
| dept:list | api | /identity/v1/depts | 查看部门列表 |
| dept:view | api | /identity/v1/depts/{code} | 查看部门详情 |
| dept:create | api | /identity/v1/depts POST | 创建部门 |
| dept:update | api | /identity/v1/depts/{code} PATCH | 更新部门 |
| dept:delete | api | /identity/v1/depts/{code}/depart | 停用部门 |
| dept:assign_role | api | /identity/v1/depts/{code}/roles | 部门关联角色 |
| dept:transfer_members | api | /identity/v1/depts/{code}/transfer-members | 批量转移成员 |
| role:manage | api | /identity/v1/roles/* | 角色管理（全部操作） |
| permission:manage | api | /identity/v1/permissions/* | 权限管理（全部操作） |
| audit:view | api | /identity/v1/audit-logs | 查看审计日志 |
| provisioning:retry | api | /identity/v1/provisioning-logs/{id}/retry | 重试分发 |
| menu:dashboard | menu | /dashboard | 仪表盘菜单 |
| menu:user_management | menu | /users | 用户管理菜单 |
| menu:dept_management | menu | /departments | 部门管理菜单 |
| menu:permission_management | menu | /permissions | 权限管理菜单 |
| menu:audit_logs | menu | /audit-logs | 审计日志菜单 |
| menu:provisioning_logs | menu | /provisioning-logs | 分发日志菜单 |

#### 8.7.2 内置角色定义

| role_code | role_name | role_type | 关联权限 | 关联 policy | 说明 |
|---|---|---|---|---|---|
| sys_admin | 系统管理员 | system | 全部权限 | 全部 TRUE | 最高权限，管理所有 |
| dept_admin | 部门管理员 | system | 用户管理+部门管理+审计 | 全部 TRUE | 数据范围限定为本部门 |
| dev_engineer | 研发工程师 | custom | 基础菜单 | 全部 TRUE | 原有角色 |
| test_engineer | 测试工程师 | custom | 基础菜单 | 部分 TRUE | 同上 |
| pm | 项目经理 | custom | 基础菜单 | 部分 TRUE | 同上 |
| delivery | 交付工程师 | custom | 基础菜单 | 部分 TRUE | 同上 |
| auditor | 审计员 | system | audit:view, menu:audit_logs | 无 | 只读审计日志 |

#### 8.7.3 初始化 SQL 脚本

~~~sql
-- 1. 插入权限（示例，完整列表按需插入）
INSERT INTO identity_permission (permission_code, permission_type, resource_path, method, description) VALUES
('user:list', 'api', '/identity/v1/users', 'GET', '查看用户列表'),
('user:create', 'api', '/identity/v1/users', 'POST', '创建用户'),
('user:update', 'api', '/identity/v1/users/{id}', 'PATCH', '更新用户'),
('user:delete', 'api', '/identity/v1/users/{id}/depart', 'POST', '停用用户'),
('role:manage', 'api', '/identity/v1/roles/*', 'ALL', '角色管理'),
('menu:user_management', 'menu', '/users', NULL, '用户管理菜单');

-- 2. 插入角色（通过 policy_id 关联已有的 identity_provisioning_policy）
INSERT INTO identity_role (role_code, role_name, role_type, policy_id, is_default) VALUES
('sys_admin', '系统管理员', 'system',
    (SELECT id FROM identity_provisioning_policy WHERE role_name = 'sys_admin'), FALSE),
('dept_admin', '部门管理员', 'system',
    (SELECT id FROM identity_provisioning_policy WHERE role_name = 'sys_admin'), FALSE),
('dev_engineer', '研发工程师', 'custom',
    (SELECT id FROM identity_provisioning_policy WHERE role_name = 'dev_engineer'), TRUE);

-- 3. 关联角色-权限（根据实际 permission_id 调整）
-- sys_admin 关联所有权限
INSERT INTO identity_role_permission (role_id, permission_id)
SELECT r.id, p.id FROM identity_role r, identity_permission p WHERE r.role_code = 'sys_admin';

-- dept_admin 关联部分权限
INSERT INTO identity_role_permission (role_id, permission_id)
SELECT r.id, p.id FROM identity_role r, identity_permission p
WHERE r.role_code = 'dept_admin'
  AND p.permission_code IN ('user:list', 'user:view', 'user:update', 'user:delete', 'dept:list', 'dept:view', 'audit:view', 'menu:user_management', 'menu:dept_management');

-- dev_engineer 仅基础菜单
INSERT INTO identity_role_permission (role_id, permission_id)
SELECT r.id, p.id FROM identity_role r, identity_permission p
WHERE r.role_code = 'dev_engineer'
  AND p.permission_code IN ('menu:dashboard', 'menu:user_management', 'menu:provisioning_logs');

### 8.8 监控与审计

#### 8.8.1 Prometheus 指标

指标名	类型	说明
authz_check_total{result="allow|deny"}	Counter	权限校验总次数（成功/拒绝）
authz_check_latency_ms{quantile="0.99"}	Histogram	权限校验 P99 延迟
audit_log_count{action="login|role_assign"}	Counter	审计日志计数（按操作类型）

#### 8.8.2 审计日志策略

审计日志保留周期：建议 90 天（与 identity_provisioning_log 保持一致）

敏感操作强制记录：

- 所有权限变更（创建/修改/删除角色、分配/撤销角色）
- 所有权限校验失败（result=deny）
- 所有登录/登出操作
- 所有用户创建/删除/停用

#### 8.8.3 日志清理策略

~~~yaml
retention:
  audit_log_days: 90
  cleanup_cron: "0 3 * * 0"  # 每周日凌晨3点执行

### 8.9 与现有设计方案的关系

#### 8.9.1 对原设计的影响

原设计元素	影响	处理方式
identity_provisioning_policy 表	保留，不废弃	通过 identity_role.policy_id 外键关联，分发策略独立维护
identity_user 表	无影响	角色分配通过 identity_user_role 实现，不修改 identity_user 结构
Provisioning 执行流程	调整	从 identity_role.policy_id → identity_provisioning_policy 读取分发目标
创建用户 API	扩展	增加角色分配逻辑
API 认证	增强	增加 fast-api-jwt-middleware + 权限校验依赖

#### 8.9.2 向后兼容性

本扩展方案为绿地项目（新系统）设计，无存量数据需要迁移。所有权限相关的表从头创建，角色和权限通过种子数据初始化，无需处理历史数据兼容问题。

### 8.10 紧急通道（Break-Glass）超级管理员应急预案

在系统发生逻辑死锁或外部依赖瘫痪时，常规的身份认证（OIDC）与授权链条可能彻底失效。为此，系统设计了物理级、最高权限、绕过常规逻辑且被强审计的后门通道。

#### 8.10.1 核心特征

- 绝对独立：不依赖进程内缓存、不依赖 OIDC IdP 的 JWT，甚至不依赖 identity_role 表的完好性。
- 最高特权：激活后，对系统的所有 API 拥有 100% 读写权限（等同全局 sys_admin）。
- 警报联动：被使用时自动在 identity_audit_log 写入 allow_bypass，并触发向安全委员会/运维团队的最高级别告警，事后强制轮换凭证。

#### 8.10.2 触发场景与原因

灾难场景导      致的后果                                           常规手段失效原因
高管误操作      UI 上误删 sys_admin 角色或解绑其所有权限              所有人失去管理权限，无法调 API 重建角色，系统逻辑死锁
基础设施雪崩    Pocket-ID 宕机且无法重启，或 permission_version 表被意外清空   用户无法获取 JWT，或缓存版本号解析错误，API 拒绝所有请求
核心数据污染    identity_user_role 等底层关联表被意外清空             即便系统正常运行，也没有任何人拥有访问下游/执行修复的权限

#### 8.10.3 双维度破窗实现机制

维度一：API 级别的硬编码超级令牌 (Super Admin Token)

将原设计中的 API_ADMIN_TOKEN 直接升级为 Break-Glass 令牌 。

实现逻辑：在 FastAPI 的权限校验中间件（或依赖注入 require_permission）中，增加最优先的"绕过逻辑"。如果请求头携带了特权 Token，则直接放行，不查询数据库，不查进程内缓存。

维度二：数据库级别的“出厂重置”脚本 (DB Reset Vault)

- Break-Glass Token 必须放在 AuthMiddleware 之前（优先于 OIDC JWT 校验），否则 Pocket-ID 宕机时 Token 无法解析，形同虚设
- 如果灾难发生在数据库的种子数据被破坏，需准备一个只读的 SQL 修复脚本，保存在代码仓库或安全的运维 Vault 中 。

实现逻辑：准备名为 emergency_restore_sys_admin.sql 的脚本，其功能是无视当前状态，强行插入或更新 sys_admin 角色，并将其强行绑定给某个预设的恢复账号 。

~~~sql
-- 强行恢复最高权限角色的 Break-Glass 脚本
INSERT INTO identity_role (role_code, role_name, role_type)
VALUES ('sys_admin', '系统管理员', 'system')
ON CONFLICT (role_code) DO UPDATE SET is_active = TRUE;

-- 强行将所有权限绑定给该角色
INSERT INTO identity_role_permission (role_id, permission_id)
SELECT (SELECT id FROM identity_role WHERE role_code='sys_admin'), id
FROM identity_permission
ON CONFLICT DO NOTHING;

-- 强行指派给紧急恢复账号 (例如一个预设的应急 UUID)
INSERT INTO identity_user_role (global_user_id, role_id, scope_type)
VALUES ('EMERGENCY-UUID-0000', (SELECT id FROM identity_role WHERE role_code='sys_admin'), 'global')
ON CONFLICT DO NOTHING;
~~~sql

维度三：Break-Glass 网络层依赖（缺少 CLI 工具补充）

极端场景：Pocket-ID 宕机的同时，Traefik 配置错误导致 HTTPS 路由不可达。此时 Break-Glass Token 无法送达，系统彻底瘫痪。
该 CLI 工具 仅用于灾难恢复，生产环境应严格限制访问（仅运维主管持有）。

~~~bash
# --- 1. 激活应急管理员（直连DB） ---
identity-cli emergency-activate --user-id EMERGENCY-UUID-0000

# --- 2. 修复角色（直连DB） ---
identity-cli emergency-restore-role --role sys_admin --permission all

# --- 3. 生成新 Break-Glass Token（更新环境变量 + 邮件通知管理员） ---
identity-cli rotate-break-glass-token --notify admin@company.com
~~~bash

#### 8.10.4 标准操作规程 (SOP)

Break-Glass 是具有严格操作纪律的“红色按钮”。当必须触发时，遵循以下 SOP：

- 破窗 (Break the Glass)：运维主管从安全的密码库（如 1Password、物理保险箱）中提取 BREAK_GLASS_TOKEN。
- 介入 (Intervene)：使用该 Token 通过 CLI 强行调用 Iapetus API 修复错误配置；或直连数据库执行 DB Reset 脚本。
- 监控触发 (Sirens Go Off)：系统捕捉到应急动作，自动向内部安全组发送最高告警。
- 修复与核对 (Fix & Verify)：恢复常规管理员权限，确认常规登录及权限校验链路重新打通。
- 换玻璃 (Replace the Glass)：必须强制生成新的 BREAK_GLASS_TOKEN 更新到环境变量并重启服务，彻底废弃旧 Token。
- 复盘 (Post-Mortem)：导出 identity_audit_log 相关记录，复盘常规系统瘫痪原因并输出故障报告。

### 8.11 总结

本扩展方案以 最小侵入 的方式，在现有身份服务之上构建了完整的权限管理体系。核心设计原则如下：

分层清晰：身份层（用户/部门） → 权限层（权限/角色/分配） → 访问控制层（API/菜单/数据权限）

复用现有资产：identity_provisioning_policy 保留不废弃，通过 identity_role.policy_id 外键关联，权限管理与分发策略各自独立演进；部门继承机制复用 identity_department + identity_dept_role

数据权限可扩展：通过 scope_type + scope_value 支持多维度数据范围控制，辅以下游 Base Repository 拦截，实现全局透明过滤。

认证与授权分离：fast-api-jwt-middleware 处理认证，AuthorizationManager 处理授权

极致安全与高可用：所有权限校验都有日志留存，配合 Break-Glass 紧急通道，确保系统在面临死锁或雪崩时依然具备自救能力。

该方案可直接作为 Iapetus 设计方案的 §8 整合到主文档中，与现有的方案A（独立部署）和方案B（嵌入式模块）并行共存，不破坏原有架构设计。

---
```

## 9. 审计日志

> 本章整合自§9v1.14。定义四层审计模型、统一审计事件结构、采集策略、保留归档与合规性映射。

**版本**：v1.14
**日期**：2026-06-27
**关联文档**：《Iapetus 设计方案》v5.0、§8v1.5
**整合方式**：本方案作为 §9 并入主设计，与方案A/方案B/§8 并列

**v1.14 变更**：§2.3 事件类型枚举新增 `auth.password_changed` / `auth.password_sync_failed` 事件类型，与 §11.5 密码管理 Fan-out 对齐。
**v1.13 变更**：§2.3 事件类型枚举表新增"通知"类别，含 `notification.email_send` / `notification.email_failed` / `notification.email_rate_limited` 三个事件类型，审计联动见 §10.9。
**v1.12 变更**：§6.3 归档校验阶段新增 JSON 格式逐行校验（`json.loads` 验证每行可解析），防止因归档文件损坏而错误执行 DROP；新增关键字段抽样警告（`event_id`/`event_time` 缺失时记录 Warning，不阻断）。
**v1.11 变更**：B.3.2 聚合查询实现从 `asyncio.gather` 改为 `asyncio.wait`，新增 `TOTAL_TIMEOUT`（30s）整体超时兜底 + `ON_TOTAL_TIMEOUT` 策略（`return_partial`/`fail`）；YAML 配置补充 `on_total_timeout` 字段。
**v1.10 变更**：§3.1 DEFAULT 分区新增风险提示 SQL 注释（"分区自动创建任务失败将导致数据无法按月归档"），引导运维配置大小监控；§7.2 新增 `DEFAULT 分区异常增长` 告警规则（阈值 100 MB，Warning 级别）。
**v1.9 变更**：§3.1 `identity_audit_event` 主键由 `(event_id, event_time)` 调整为 `(event_time, event_id)`，时间列优先，与 99% 时间范围审计查询模式对齐。
**v1.8 变更**：§4.1 采集原则新增"敏感操作同事务写入"，确保审计与业务原子性；§4.2 新增 `log_sync()` 方法（同事务写入）+ 调用示例；§4.3 升级为同事务写入清单，补充权限校验拒绝的例外说明和性能权衡分析。
**v1.6 变更**：§4.2 新增合规标签自动映射机制（`_COMPLIANCE_MAP`），开发者无需手动填写；§4.2 异步写入失败兜底闭环补充 RabbitMQ 补偿链路（stderr → Fluentd → RabbitMQ → 补偿任务 → DB）；§7.2 新增 `AuditBufferHigh` 异步队列堆积告警。
**v1.5 变更**：§8.3 数据权限拦截器采样率从硬编码 `0.01` 改为环境变量 `DATA_SCOPE_AUDIT_SAMPLE_RATE` 可配置；§3.2 与权限管理方案 §2.7 字段对齐确认（`identity_audit_log` 建表时直接包含审计标准化字段）。
**v1.4 变更**：B.3.2 跨系统聚合查询增加可用性保障：Replica 超时控制（3s 可配置）、降级返回（`sources_skipped` + `partial: true`）、状态枚举（`success`/`timeout`/`connection_refused`/`http_error_4xx`/`http_error_5xx`）、前端处理建议、合规导出完整性校验。
**v1.3 变更**：§3.1 建表语句改为 PG 原生 RANGE 分区（按月） + 默认分区 + 分区自动管理（pg_partman/CronJob）；§6 归档方案从逐条 DELETE 改为 DETACH PARTITION → 导出 → DROP PARTITION 流程，消除大表 DELETE 的性能风险。
**v1.2 变更**：新增附录「方案B（嵌入式 identity-module）下的审计日志适配」，覆盖方案B下的审计存储、查询、采集、归档、监控、合规导出适配说明。
**v1.1 变更**：基于 DDAP/AMDP 均为绿地系统的前提，移除渐进式迁移策略，改为一次性最终态设计；现有关联表字段在建表时直接包含，不再使用 ALTER 语句。

______________________________________________________________________

### 9.1 定位与设计目标

#### 9.1.1 定位

Identity Service 已有两套日志体系，但分散在多个表中，缺乏统一的审计视图和查询入口：

| 现有日志表                         | 来源文档               | 覆盖范围                                    |
| :--------------------------------- | :--------------------- | :------------------------------------------ |
| `identity_provisioning_log`        | Iapetus 设计方案 §3.6  | 分发操作日志（谁向哪个系统推送了什么）      |
| `identity_sync_event_log`          | Iapetus 设计方案 §3.11 | 外部 IdP 同步事件日志（企微/钉钉/飞书回调） |
| `identity_user_department`（SCD2） | Iapetus 设计方案 §3.3  | 人员部门归属变更历史                        |
| `identity_audit_log`               | §8.2.7                 | 权限校验日志（鉴权通过/拒绝）               |

本扩展方案在现有日志体系之上，构建**统一的审计日志层**，目标：

1. **统一审计入口**：提供单一 API 端点，跨表查询所有审计事件
1. **标准化事件模型**：定义审计事件的统一结构（who/when/what/where/result）
1. **合规性覆盖**：满足 ISO 27001、等保 2.0 对审计日志的完整性要求
1. **生命周期管理**：统一的保留、归档、清理策略

> **方案适用范围**：本文 §2-§11 基于方案A（独立 Identity Service）设计，审计日志集中在 `identity_db` 统一管理。方案B（嵌入式 identity-module）的适配见 [附录：方案B适配](#%E9%99%84%E5%BD%95%E6%96%B9%E6%A1%88b%E5%B5%8C%E5%85%A5%E5%BC%8F-identity-module-%E4%B8%8B%E7%9A%84%E5%AE%A1%E8%AE%A1%E6%97%A5%E5%BF%97%E9%80%82%E9%85%8D)。

#### 9.1.2 设计目标

| 目标           | 说明                                                                                |
| :------------- | :---------------------------------------------------------------------------------- |
| **统一查询**   | 单次 API 调用即可跨表检索所有审计事件，按时间线排序                                 |
| **事件标准化** | 所有审计事件遵循统一结构，便于日志分析系统（如 ELK/Splunk）消费                     |
| **不可篡改**   | 审计日志只追加不修改，应用层禁止 UPDATE/DELETE                                      |
| **分级存储**   | 热数据（近 30 天）存 PG → 温数据（30~90 天）存 PG → 冷数据（90+ 天）归档到 OSS/文件 |
| **合规映射**   | 明确每条审计日志对应的合规控制项（ISO 27001 A.12.4 / 等保 8.1.4）                   |
| **性能隔离**   | 审计日志写入异步化，不阻塞业务主流程                                                |

______________________________________________________________________

### 9.2 审计日志体系总览

#### 9.2.1 四层审计模型

```
┌─────────────────────────────────────────────────────────────────┐
│                    统一审计查询层 (Unified Audit API)              │
│              GET /identity/v1/audit/events                       │
│              跨表联合查询，按时间线统一排序                          │
├─────────────────────────────────────────────────────────────────┤
│  认证审计 (Auth)   │  操作审计 (Operation)  │  权限审计 (AuthZ)    │
│  登录/登出/SSO     │  用户CRUD/部门变更/     │  权限校验/角色分配/   │
│  Token 签发/吊销   │  分发操作/策略变更      │  权限继承/越权尝试    │
├─────────────────────────────────────────────────────────────────┤
│  同步审计 (Sync)   │  数据审计 (Data)        │  系统审计 (System)   │
│  IdP 回调事件/     │  SCD2 部门变更/         │  Break-Glass 激活/   │
│  同步成功/失败/    │  映射关系变更/           │  配置变更/           │
│  幂等去重          │  标签变更                │  缓存失效/服务启停   │
├─────────────────────────────────────────────────────────────────┤
│                    审计存储层 (Audit Storage)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ 热数据 (PG)  │  │ 温数据 (PG)  │  │ 冷归档 (OSS/文件)    │   │
│  │ 0~30 天      │  │ 30~90 天     │  │ 90+ 天              │   │
│  │ 全字段查询   │  │ 全字段查询   │  │ JSON 压缩包          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### 9.2.2 审计事件统一结构

所有审计事件遵循以下标准结构，无论存储在哪个底层表中：

```json
{
    "event_id": "evt_01JQXXXXX",         // 事件唯一ID（UUID v7）
    "event_type": "user.create",         // 事件类型（见 §2.3）
    "event_time": "2026-06-27T10:30:00Z",// 事件发生时间
    "category": "operation",             // 审计类别
    "actor": {
        "global_user_id": "01JQ...",     // 操作人
        "username": "zhangsan",
        "ip_address": "10.0.1.100",
        "user_agent": "Mozilla/5.0..."
    },
    "target": {
        "resource_type": "user",         // 资源类型
        "resource_id": "01JQ...",        // 资源ID
        "resource_name": "lisi"          // 资源名称
    },
    "action": "create",                  // 动作
    "result": "success",                 // success / failure / denied
    "detail": {                          // 上下文（JSONB）
        "old_value": null,
        "new_value": {"username": "lisi", "display_name": "李四"}
    },
    "compliance_tags": ["iso27001:A.12.4.1", "dsl:8.1.4"],  // 合规标签（框架自动注入，开发者无需手动填写）
    "source_table": "identity_provisioning_log"              // 来源表
}

// 合规标签赋值逻辑：框架根据 event_type 自动映射，不依赖开发者手动指定。
// 映射关系在 AuditLogger 内部维护（_COMPLIANCE_MAP），详见 §4.2。
```

#### 9.2.3 事件类型枚举

| 类别     | event_type                        | 说明                                 | 来源表                    | 敏感级别 |
| :------- | :-------------------------------- | :----------------------------------- | :------------------------ | :------- |
| **认证** | `auth.login`                      | 用户登录                             | identity_audit_log        | 中       |
|          | `auth.logout`                     | 用户登出                             | identity_audit_log        | 低       |
|          | `auth.sso_callback`               | OIDC 回调                            | identity_audit_log        | 中       |
|          | `auth.token_refresh`              | Token 刷新                           | identity_audit_log        | 低       |
|          | `auth.login_failed`               | 登录失败                             | identity_audit_log        | 高       |
|          | `auth.password_changed`           | 密码修改（Fan-out 双写成功）         | identity_audit_event      | 中       |
|          | `auth.password_sync_failed`       | 密码同步失败（重试耗尽，需人工介入） | identity_audit_event      | 高       |
| **操作** | `user.create`                     | 创建用户                             | identity_audit_log        | 高       |
|          | `user.update`                     | 更新用户                             | identity_audit_log        | 中       |
|          | `user.depart`                     | 停用用户                             | identity_audit_log        | 高       |
|          | `user.reactivate`                 | 重新激活                             | identity_audit_log        | 高       |
|          | `dept.create`                     | 创建部门                             | identity_audit_log        | 中       |
|          | `dept.update`                     | 更新部门                             | identity_audit_log        | 中       |
|          | `dept.delete`                     | 删除部门                             | identity_audit_log        | 高       |
|          | `dept.transfer_members`           | 批量转移成员                         | identity_audit_log        | 高       |
|          | `mapping.create`                  | 创建映射                             | identity_audit_log        | 中       |
|          | `mapping.delete`                  | 删除映射                             | identity_audit_log        | 中       |
|          | `policy.create`                   | 创建分发策略                         | identity_audit_log        | 中       |
|          | `policy.update`                   | 更新分发策略                         | identity_audit_log        | 中       |
|          | `policy.delete`                   | 删除分发策略                         | identity_audit_log        | 高       |
|          | `provisioning.execute`            | 执行分发                             | identity_provisioning_log | 中       |
|          | `provisioning.retry`              | 重试分发                             | identity_provisioning_log | 低       |
| **权限** | `role.create`                     | 创建角色                             | identity_audit_log        | 高       |
|          | `role.update`                     | 更新角色                             | identity_audit_log        | 中       |
|          | `role.delete`                     | 删除角色                             | identity_audit_log        | 高       |
|          | `role.assign`                     | 分配角色给用户                       | identity_audit_log        | 高       |
|          | `role.revoke`                     | 撤销用户角色                         | identity_audit_log        | 高       |
|          | `role.dept_assign`                | 部门关联角色                         | identity_audit_log        | 中       |
|          | `permission.check_allow`          | 权限校验通过                         | identity_audit_log        | 低       |
|          | `permission.check_deny`           | 权限校验拒绝                         | identity_audit_log        | 高       |
|          | `permission.create`               | 创建权限                             | identity_audit_log        | 中       |
|          | `permission.delete`               | 删除权限                             | identity_audit_log        | 高       |
| **同步** | `sync.idp_event`                  | 外部 IdP 事件                        | identity_sync_event_log   | 中       |
|          | `sync.idp_event_duplicate`        | 重复事件（幂等跳过）                 | identity_sync_event_log   | 低       |
|          | `sync.idp_event_failed`           | 同步失败                             | identity_sync_event_log   | 高       |
| **数据** | `data.dept_change`                | 人员部门变更（SCD2）                 | identity_user_department  | 中       |
|          | `data.tag_add`                    | 添加标签                             | identity_audit_log        | 低       |
|          | `data.tag_remove`                 | 移除标签                             | identity_audit_log        | 低       |
| **系统** | `system.break_glass`              | Break-Glass 激活                     | identity_audit_log        | 严重     |
|          | `system.config_change`            | 系统配置变更                         | identity_audit_log        | 高       |
|          | `system.cache_invalidate`         | 缓存失效                             | identity_audit_log        | 低       |
| **通知** | `notification.email_send`         | 邮件发送成功                         | identity_audit_event      | 低       |
|          | `notification.email_failed`       | 邮件发送失败（含重试耗尽）           | identity_audit_event      | 中       |
|          | `notification.email_rate_limited` | 被 SMTP 限流                         | identity_audit_event      | 低       |

______________________________________________________________________

### 9.3 审计日志表设计

#### 9.3.1 统一审计日志表（核心新增）

> 本表为审计日志的**统一存储后端**，所有审计事件归一化写入此表。DDAP、AMDP 等均为绿地系统，无需考虑存量数据迁移，直接采用最终态设计。
>
> **分区策略**：按月份 RANGE 分区，配合 DROP PARTITION 实现毫秒级归档（详见 §6）。主键必须包含分区键 `event_time`。

```sql
-- 分区主表（不存储数据，仅定义结构）
CREATE TABLE identity_audit_event (
    event_id         CHAR(32)     NOT NULL,               -- UUID v7（含时间戳，天然按时间排序）
    event_type       VARCHAR(64)  NOT NULL,               -- 事件类型枚举（见 §2.3）
    event_time       TIMESTAMPTZ  NOT NULL DEFAULT NOW(), -- 事件发生时间（分区键）
    category         VARCHAR(16)  NOT NULL,               -- auth / operation / authz / sync / data / system

    -- 操作人
    actor_user_id    CHAR(32)     REFERENCES identity_user(global_user_id),
    actor_username   VARCHAR(64),                          -- 冗余，便于查询
    actor_ip         INET,
    actor_user_agent TEXT,

    -- 操作目标
    target_type      VARCHAR(32),                          -- user / dept / role / policy / permission / mapping / tag / token
    target_id        VARCHAR(128),                         -- 目标资源ID（可能跨表，不用外键）
    target_name      VARCHAR(256),                         -- 目标资源名称（冗余）

    -- 操作
    action           VARCHAR(32)  NOT NULL,               -- create / update / delete / assign / revoke / check
    result           VARCHAR(16)  NOT NULL,               -- success / failure / denied / skipped

    -- 详情
    detail           JSONB,                                -- 上下文信息（old_value / new_value / error_message）

    -- 合规
    compliance_tags  TEXT[],                                -- PostgreSQL 数组：'{iso27001:A.12.4.1, dsl:8.1.4}'

    -- 来源追溯
    source_table     VARCHAR(64),                           -- 原始表名（如 identity_provisioning_log）
    source_id        INT,                                   -- 原始表记录ID

    -- 元数据
    created_at       TIMESTAMPTZ  DEFAULT NOW(),

    PRIMARY KEY (event_time, event_id)                      -- 分区键必须包含在主键中；时间优先，符合 99% 时间范围审计查询模式
) PARTITION BY RANGE (event_time);

-- 默认分区（兜底未匹配的数据，避免插入失败）
-- [WARN] 此分区为数据兜底，正常情况下应为空或极小。
-- 如分区自动创建任务失败，所有新数据将涌入此分区，导致无法按月归档。
-- 必须在运维监控中配置 DEFAULT 分区大小告警（参见 §7.2），阈值建议 > 100MB 触发 Warning。
CREATE TABLE identity_audit_event_default PARTITION OF identity_audit_event DEFAULT;

-- 首个分区（2026年7月）
CREATE TABLE identity_audit_event_202607 PARTITION OF identity_audit_event
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

-- 索引（在父表上定义，自动继承到各分区；每个分区独立维护索引统计）
CREATE INDEX idx_audit_event_time    ON identity_audit_event(event_time DESC);
CREATE INDEX idx_audit_event_type    ON identity_audit_event(event_type, event_time);
CREATE INDEX idx_audit_event_category ON identity_audit_event(category, event_time);
CREATE INDEX idx_audit_event_actor   ON identity_audit_event(actor_user_id, event_time);
CREATE INDEX idx_audit_event_target  ON identity_audit_event(target_type, target_id, event_time);
CREATE INDEX idx_audit_event_result  ON identity_audit_event(event_time) WHERE result IN ('failure', 'denied');
CREATE INDEX idx_audit_event_compliance ON identity_audit_event USING GIN(compliance_tags);
```

> **分区自动管理**：推荐使用 [pg_partman](https://github.com/pgpartman/pg_partman) 扩展自动创建未来分区，避免手动维护。
>
> ```sql
> SELECT partman.create_parent(
>     p_parent_table := 'public.identity_audit_event',
>     p_control      := 'event_time',
>     p_type         := 'native',
>     p_interval     := '1 month',
>     p_premake      := 2              -- 提前创建 2 个未来分区
> );
> ```
>
> 如不使用 pg_partman，可通过 CronJob 每月初执行 `CREATE TABLE ... PARTITION OF` 语句。

#### 9.3.2 现有日志表（原生包含标准化字段）

> 以下四张表在绿地建表时**直接包含标准化审计字段**，无需后续 ALTER。此处列出各表需要新增的字段（相对于原设计方案），建表时与业务字段一同写入 CREATE TABLE。

###### identity_audit_log（§8.2.7）

```sql
-- 建表时直接包含以下字段（非 ALTER），与原有字段一同定义
event_type       VARCHAR(64),                          -- 事件类型枚举
category         VARCHAR(16) DEFAULT 'authz',          -- 审计类别
target_type      VARCHAR(32),                          -- 目标资源类型
target_id        VARCHAR(128),                         -- 目标资源ID
target_name      VARCHAR(256),                         -- 目标资源名称
compliance_tags  TEXT[],                                -- 合规标签
```

###### identity_provisioning_log（Iapetus 设计方案 §3.6）—— [OK] 已同步至主文档 v4.7

```sql
-- 建表时直接包含以下字段（主文档 §3.6 已完成同步）
event_type       VARCHAR(64) NOT NULL DEFAULT 'provisioning.execute',
category         VARCHAR(32) NOT NULL DEFAULT 'operation',
actor_username   VARCHAR(64),
actor_ip         INET,
compliance_tags  VARCHAR(256)[] NOT NULL DEFAULT '{}',
```

###### identity_sync_event_log（Iapetus 设计方案 §3.11）—— [OK] 已同步至主文档 v4.7

```sql
-- 建表时直接包含以下字段（主文档 §3.11 已完成同步）
category         VARCHAR(32) NOT NULL DEFAULT 'sync',
compliance_tags  VARCHAR(256)[] NOT NULL DEFAULT '{}',
```

> 注：`identity_sync_event_log` 原表已含 `event_type VARCHAR(32)`，无需额外添加。

````

###### identity_user_department（Iapetus 设计方案 §3.3）

> SCD2 表结构天然满足审计需求，通过查询视图映射即可。

#### 9.3.3 统一查询视图（辅助工具）

`identity_audit_event` 是主存储，其他四张表也保留各自的业务查询能力。以下视图提供跨表联合查询，方便直接查看所有来源的审计事件：

```sql
CREATE VIEW v_audit_event_unified AS
-- 权限审计日志
SELECT
    ('audit_' || id)::VARCHAR(64)            AS event_id,
    COALESCE(event_type, 'permission.check') AS event_type,
    created_at                               AS event_time,
    COALESCE(category, 'authz')              AS category,
    global_user_id                           AS actor_user_id,
    username                                 AS actor_username,
    ip_address                               AS actor_ip,
    user_agent                               AS actor_user_agent,
    NULL                                     AS target_type,
    NULL                                     AS target_id,
    NULL                                     AS target_name,
    action                                   AS action,
    result                                   AS result,
    detail                                   AS detail,
    NULL                                     AS compliance_tags,
    'identity_audit_log'                     AS source_table,
    id                                       AS source_id
FROM identity_audit_log

UNION ALL

-- 分发操作日志
SELECT
    ('prov_' || id)::VARCHAR(64)             AS event_id,
    COALESCE(event_type, 'provisioning.execute') AS event_type,
    created_at                               AS event_time,
    COALESCE(category, 'operation')          AS category,
    global_user_id                           AS actor_user_id,
    actor_username                           AS actor_username,
    actor_ip                                 AS actor_ip,
    NULL                                     AS actor_user_agent,
    'system'                                 AS target_type,
    source_system                            AS target_id,
    source_system                            AS target_name,
    action                                   AS action,
    status                                   AS result,
    jsonb_build_object(
        'error', error_message,
        'request', request_payload,
        'response', response_data,
        'retry_count', retry_count
    )                                        AS detail,
    NULL                                     AS compliance_tags,
    'identity_provisioning_log'              AS source_table,
    id                                       AS source_id
FROM identity_provisioning_log

UNION ALL

-- 同步事件日志
SELECT
    ('sync_' || id)::VARCHAR(64)             AS event_id,
    COALESCE(event_type, 'sync.idp_event')   AS event_type,
    event_time                               AS event_time,
    COALESCE(category, 'sync')               AS category,
    NULL                                     AS actor_user_id,
    NULL                                     AS actor_username,
    NULL                                     AS actor_ip,
    NULL                                     AS actor_user_agent,
    source                                   AS target_type,
    external_id                              AS target_id,
    NULL                                     AS target_name,
    event_type                               AS action,
    action                                   AS result,
    jsonb_build_object(
        'detail', detail,
        'raw_payload', raw_payload
    )                                        AS detail,
    NULL                                     AS compliance_tags,
    'identity_sync_event_log'                AS source_table,
    id                                       AS source_id
FROM identity_sync_event_log

UNION ALL

-- 部门变更历史（SCD2）
SELECT
    ('dept_' || id)::VARCHAR(64)             AS event_id,
    'data.dept_change'                       AS event_type,
    effective_from                           AS event_time,
    'data'                                   AS category,
    changed_by                               AS actor_user_id,
    NULL                                     AS actor_username,
    NULL                                     AS actor_ip,
    NULL                                     AS actor_user_agent,
    'department'                             AS target_type,
    dept_code                                AS target_id,
    NULL                                     AS target_name,
    'change'                                 AS action,
    CASE WHEN is_current THEN 'active' ELSE 'deprecated' END AS result,
    jsonb_build_object(
        'dept_code', dept_code,
        'effective_from', effective_from,
        'effective_to', effective_to,
        'change_reason', change_reason
    )                                        AS detail,
    NULL                                     AS compliance_tags,
    'identity_user_department'               AS source_table,
    id                                       AS source_id
FROM identity_user_department;
```

______________________________________________________________________

### 9.4 审计日志采集策略

#### 9.4.1 采集原则

| 原则 | 说明 |
| :--------------------- | :---------------------------------------------------------------------------------------------------------------- |
| **异步写入** | 非敏感操作（如权限校验允许）通过异步/批量写入，不阻塞业务响应 |
| **只追加不修改** | 审计日志一旦写入，应用层禁止 UPDATE/DELETE，不可篡改 |
| **写入失败不阻塞业务** | 非敏感操作审计写入失败时记录到 `stderr` + 监控告警，不影响主流程返回 |
| **敏感操作同事务写入** | 用户创建/停用、角色分配/撤销等敏感操作，审计与业务在**同一 DB 事务**中完成，确保"操作生效 = 审计落盘"的无缺口语义 |
| **批量写入** | 高吞吐场景（如权限校验）采用批量写入，每 100 条或每 5 秒 flush 一次 |

> **事务一致性取舍**：敏感操作同事务写入会**增加持锁时间**。如果审计表写入成为性能瓶颈，可通过审计表独立表空间、异步复制等手段缓解，但不能以牺牲审计完整性为代价。非敏感操作（如权限校验允许）不纳入业务事务，异步即可。

#### 9.4.2 采集架构

###### 合规标签自动映射

合规标签**不应当**由开发者在调用 `AuditLogger.log()` 时手动填写——这容易遗漏或填错。
框架内部维护一个 `event_type → compliance_tags` 的**硬编码映射表**，作为"合规标准 → 代码"的单一事实来源。
开发者只需传入 `event_type`，合规标签由框架自动注入：

```python
# --- 合规映射表：event_type → 适用的合规标准控制项 ---
# --- 维护者：安全架构师，新增事件类型时同步更新此处 ---
_COMPLIANCE_MAP = {
    # ---- 认证类 ----
    "auth.login":       ["iso27001:A.9.2.1", "dsl:8.1.4.1"],
    "auth.logout":      ["iso27001:A.9.2.1"],
    "auth.login_failed": ["iso27001:A.9.4.2", "dsl:8.1.4.3"],

    # ---- 用户操作类 ----
    "user.create":      ["iso27001:A.9.2.1", "dsl:8.1.4.1"],
    "user.update":      ["iso27001:A.9.2.1", "dsl:8.1.4.1"],
    "user.delete":      ["iso27001:A.9.2.5", "dsl:8.1.4.1"],
    "user.depart":      ["iso27001:A.9.2.5", "dsl:8.1.4.1"],
    "user.rehire":      ["iso27001:A.9.2.1", "dsl:8.1.4.1"],

    # ---- 权限审计类 ----
    "permission.check_allow":  ["iso27001:A.9.4.2"],
    "permission.check_deny":   ["iso27001:A.5.15", "iso27001:A.9.4.2", "dsl:8.1.4.3"],
    "role.assign":       ["iso27001:A.5.18", "dsl:8.1.4.1"],
    "role.revoke":       ["iso27001:A.5.18", "dsl:8.1.4.1"],
    "role.create":       ["iso27001:A.5.18"],
    "role.delete":       ["iso27001:A.5.18"],
    "permission.create": ["iso27001:A.5.15"],
    "permission.delete": ["iso27001:A.5.15"],

    # ---- 分发运维类 ----
    "provisioning.execute": ["iso27001:A.12.4.1", "dsl:8.1.4.1"],
    "provisioning.failed":  ["iso27001:A.12.4.1"],

    # ---- 同步类 ----
    "sync.user_add":    ["iso27001:A.12.4.1"],
    "sync.user_update": ["iso27001:A.12.4.1"],
    "sync.user_depart": ["iso27001:A.9.2.5"],

    # ---- 系统安全类 ----
    "system.break_glass":    ["iso27001:A.5.18", "iso27001:A.9.2.5", "dsl:8.1.4.3"],
    "system.token_rotate":   ["iso27001:A.5.18"],
    "system.cert_expiry":    ["iso27001:A.12.4.1"],

    # ---- 数据权限类 ----
    "data.scope_applied":    ["iso27001:A.9.4.2", "dsl:8.1.4.2"],
}
```

###### AuditLogger 实现

```python
class AuditLogger:
    """统一审计日志采集器"""

    def __init__(self, db_session_factory, async_mode: bool = True):
        self.db_session_factory = db_session_factory
        self.async_mode = async_mode
        self.buffer: list[dict] = []
        self._lock = asyncio.Lock()

    def _inject_compliance_tags(self, event: AuditEvent) -> None:
        """根据 event_type 自动注入合规标签（开发者无需手动填写）"""
        if not event.compliance_tags:
            event.compliance_tags = _COMPLIANCE_MAP.get(event.event_type, [])

    async def log(self, event: AuditEvent) -> None:
        """记录审计事件"""
        self._inject_compliance_tags(event)  # 自动注入合规标签
        if self.async_mode and not event.sync_required:
            # 异步写入（默认，非敏感操作）
            asyncio.create_task(self._write_event(event))
        else:
            # 同步写入（敏感操作，同一 DB 事务内）
            await self._write_event(event)

    async def log_sync(self, session, event: AuditEvent) -> None:
        """
        敏感操作专用：在业务事务内写入审计，确保原子性。

        调用方将 session 传入，审计写入使用与业务相同的数据库连接和事务。
        业务 commit → 审计 + 业务同时落盘；业务 rollback → 审计也回滚。
        """
        self._inject_compliance_tags(event)
        session.add(event.to_orm())
        # 不在此处 commit——由调用方的业务事务统一 commit

    async def _write_event(self, event: AuditEvent) -> None:
        """写入 identity_audit_event 表（独立事务，异步写入用）"""
        try:
            async with self.db_session_factory() as session:
                session.add(event.to_orm())
                await session.commit()
        except Exception as e:
            logger.error(f"Audit write failed: {e}", exc_info=True)
            # 写入失败兜底：输出到 stderr，由日志采集器捕获
            # 格式统一为 JSON，便于下游解析
            print(json.dumps({
                "type": "audit_event_fallback",
                "event": event.to_dict(),
                "error": str(e),
                "timestamp_utc": datetime.utcnow().isoformat() + "Z"
            }), file=sys.stderr, flush=True)
            AUDIT_WRITE_FAILURES.inc()
```

###### 异步写入失败兜底闭环

`print(stderr)` 只是兜底的**第一跳**，完整的恢复链路如下：

```
┌─────────────────────────────────────────────────────────────────┐
│ 审计写入失败兜底闭环                                              │
│                                                                 │
│  AuditLogger._write_event() 失败                                 │
│         │                                                       │
│         ▼                                                       │
│  print(json, stderr) ──── 容器 stdout/stderr 流                  │
│         │                                                       │
│         ▼                                                       │
│  Fluentd / Filebeat ──── 日志采集器，tail 容器日志               │
│         │                                                       │
│         ▼                                                       │
│  RabbitMQ (exchange: identity.audit.dlq) ──── 持久化缓冲，防丢  │
│         │                                                       │
│         ▼                                                       │
│  审计补偿任务 (audit-recovery-worker) ──── 消费 RabbitMQ，重试   │
│         │                                                       │
│         ├── 成功 → ack 确认，指标 audit_recovery_success +1     │
│         └── 超过最大重试 → 写入 dead_letter，人工介入             │
└─────────────────────────────────────────────────────────────────┘
```

**Fluentd 配置示例**：

```yaml
### fluentd.conf — 从容器 stderr 提取审计兜底日志，转发到 RabbitMQ
<filter containers.**>
  @type grep
  <regexp>
    key log
    pattern "audit_event_fallback"
  </regexp>
</filter>

<match containers.**>
  @type rabbitmq
  host mq
  port 5672
  exchange identity.audit.dlq
  exchange_type fanout
  durable true
  <format>
    @type json
  </format>
</match>
```

**补偿任务伪代码**：

```python
### audit_recovery_worker.py — RabbitMQ 消费端，重试写入数据库
async def recover_audit_events():
    connection = await aio_pika.connect_robust("amqp://admin:pass@mq:5672//")  # pragma: allowlist secret
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "identity.audit.dlq", aio_pika.ExchangeType.FANOUT, durable=True
        )
        queue = await channel.declare_queue("identity.audit.dlq.recovery", durable=True)
        await queue.bind(exchange)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(requeue=True):
                    event_data = json.loads(message.body)
                    try:
                        await write_to_db(event_data["event"])
                        await message.ack()
                        AUDIT_RECOVERY_SUCCESS.inc()
                    except Exception:
                        retry_count = int(
                            message.headers.get("x-retry-count", 0)
                        )
                        if retry_count > 5:
                            await write_dead_letter(event_data)
                            await message.ack()  # 死信，不再 requeue
                            AUDIT_RECOVERY_DEAD_LETTER.inc()
                        else:
                            await asyncio.sleep(
                                min(2 ** retry_count, 60)
                            )
                            # message.nack() → requeue (requeue=True)
```

**监控指标补充**：

| 指标名 | 类型 | 说明 |
| :--------------------------------- | :------ | :----------------------------------------- |
| `audit_recovery_success_total` | Counter | 补偿任务成功恢复的审计事件数 |
| `audit_recovery_dead_letter_total` | Counter | 补偿失败进入死信队列的事件数（需人工介入） |
| `audit_buffer_size` | Gauge | 异步写入缓冲区当前积压量（条） |

###### 敏感操作事务内审计调用示例

```python
# --- 敏感操作（如创建用户）—— 审计与业务在同一事务中 ---
async def create_user(user_data: dict, db: AsyncSession, audit: AuditLogger):
    async with db.begin():  # 开启业务事务
        user = await user_repo.create(db, user_data)  # 业务写入

        # 审计写入使用同一个 db session，纳入当前事务
        await audit.log_sync(db, AuditEvent(
            event_type="user.create",
            category="operation",
            actor_user_id=current_user_id,
            target_type="user",
            target_id=user.global_user_id,
            target_name=user.display_name,
            action="create",
            result="success",
            detail={"new_value": user_data},
        ))
    # 事务提交：user 和审计记录同时落盘
    # 若抛异常 → 回滚：user 和审计记录同时丢弃

### 非敏感操作（如权限校验允许）—— 异步，不纳入业务事务
async def check_permission(user_id: str, perm: str, audit: AuditLogger):
    allowed = await authz.has_permission(user_id, perm)
    if allowed:
        # 异步写入，不阻塞、不纳事务
        await audit.log(AuditEvent(
            event_type="permission.check_allow",
            category="authz",
            actor_user_id=user_id,
            action="check",
            result="allow",
            detail={"permission": perm},
            async_mode=True,
        ))
    return allowed
```

```
### ---- 便捷方法 ----

async def log_auth(self, action: str, user_id: str, result: str, **kwargs):
    await self.log(AuditEvent(
        event_type=f"auth.{action}",
        category="auth",
        actor_user_id=user_id,
        action=action,
        result=result,
        **kwargs
    ))

async def log_operation(self, target_type: str, action: str, user_id: str,
                        target_id: str, target_name: str, result: str,
                        old_value: dict = None, new_value: dict = None):
    await self.log(AuditEvent(
        event_type=f"{target_type}.{action}",
        category="operation",
        actor_user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        action=action,
        result=result,
        detail={"old_value": old_value, "new_value": new_value},
        sync_required=(action in ("create", "delete", "depart"))
    ))

async def log_authz(self, action: str, user_id: str, result: str, **kwargs):
    await self.log(AuditEvent(
        event_type=f"permission.{action}",
        category="authz",
        actor_user_id=user_id,
        action=action,
        result=result,
        **kwargs
    ))
```

```

#### 9.4.3 强制记录清单（同事务写入）

以下操作必须与业务操作在**同一数据库事务**中写入审计日志（通过 `audit.log_sync(session, event)`），实现"操作生效 = 审计落盘"的原子性语义：

| 操作 | event_type | 写入方式 | 风险等级 |
| :--- | :--- | :--- | :--- |
| 创建用户 | `user.create` | `log_sync`（同事务） | 高 |
| 停用用户 | `user.depart` | `log_sync`（同事务） | 高 |
| 删除部门 | `dept.delete` | `log_sync`（同事务） | 高 |
| 分配角色 | `role.assign` | `log_sync`（同事务） | 高 |
| 撤销角色 | `role.revoke` | `log_sync`（同事务） | 高 |
| 删除权限 | `permission.delete` | `log_sync`（同事务） | 高 |
| 删除分发策略 | `policy.delete` | `log_sync`（同事务） | 高 |
| Break-Glass 激活 | `system.break_glass` | `log_sync`（同事务） | 严重 |
| 权限校验拒绝 | `permission.check_deny` | `log()`（同步，独立事务） | 高 |

> **权限校验拒绝为何不用同事务**：权限校验通常是轻量级的布尔判断，没有业务写入。此时 `sync_required=True` + 独立事务的 `log()` 足够：如果 DB 不可用导致审计写入失败，校验结果仍然返回"拒绝"（安全侧正确），同时触发 `audit_write_failures_total` 告警。

> **性能权衡**：同事务写入增加持锁时间约 1-3ms（审计表单行 INSERT）。对于用户创建这类低频操作（<100 QPS），影响可忽略。若未来某高频操作也需强制记录（如 >1000 QPS），可考虑审计表独立表空间或 WAL 级异步，但 Phase 1 统一使用同事务，优先保证完整性。

---

### 9.5 审计日志查询与 API

#### 9.5.1 统一查询 API

```

GET /identity/v1/audit/events

````

**查询参数**：

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `event_type` | string | 事件类型（支持逗号分隔多个，如 `user.create,user.depart`） |
| `category` | string | 审计类别 |
| `actor_user_id` | string | 操作人 global_user_id |
| `target_type` | string | 目标资源类型 |
| `target_id` | string | 目标资源 ID |
| `result` | string | 结果过滤（`success` / `failure` / `denied`） |
| `date_from` | datetime | 起始时间 |
| `date_to` | datetime | 结束时间 |
| `compliance` | string | 合规标签过滤（如 `iso27001`） |
| `page` | int | 页码（默认 1） |
| `page_size` | int | 每页条数（默认 50，最大 200） |
| `sort` | string | 排序方向（`asc` / `desc`，默认 `desc`） |

**响应示例**：

```json
{
    "total": 12345,
    "page": 1,
    "page_size": 50,
    "events": [
        {
            "event_id": "evt_01JQXXXXX",
            "event_type": "user.create",
            "event_time": "2026-06-27T10:30:00Z",
            "category": "operation",
            "actor": {
                "global_user_id": "01JQA...",
                "username": "zhangsan",
                "ip_address": "10.0.1.100"
            },
            "target": {
                "type": "user",
                "id": "01JQB...",
                "name": "lisi"
            },
            "action": "create",
            "result": "success",
            "detail": {
                "new_value": {"username": "lisi", "display_name": "李四", "dept_code": "RD01"}
            },
            "compliance_tags": ["iso27001:A.12.4.1"]
        }
    ]
}
````

#### 9.5.2 审计统计 API

```
GET /identity/v1/audit/stats
```

| 参数 | 说明 |
| :---------------------- | :------------------------------ |
| `date_from` / `date_to` | 统计时间范围 |
| `granularity` | 粒度（`hour` / `day` / `week`） |

**响应**：

```json
{
    "period": {"from": "2026-06-01", "to": "2026-06-27"},
    "total_events": 45678,
    "by_category": {
        "auth": 15000,
        "operation": 12000,
        "authz": 18000,
        "sync": 500,
        "data": 100,
        "system": 78
    },
    "by_result": {
        "success": 45000,
        "failure": 300,
        "denied": 350,
        "skipped": 28
    },
    "top_denied_actions": [
        {"event_type": "permission.check_deny", "count": 200},
        {"event_type": "auth.login_failed", "count": 150}
    ],
    "break_glass_activations": 0
}
```

#### 9.5.3 审计导出 API

```
POST /identity/v1/audit/export
```

```json
{
    "filters": { ... },           // 同查询参数
    "format": "csv",              // csv / json / jsonl
    "date_from": "2026-06-01",
    "date_to": "2026-06-27"
}
```

返回文件下载流，用于合规审计时导出给审计方。

______________________________________________________________________

### 9.6 审计日志保留与归档

#### 9.6.1 三级存储策略

> 审计日志表按月份 RANGE 分区（见 §3.1），归档通过 DROP PARTITION 实现，避免逐条 DELETE 带来的性能问题。

```
┌──────────────────────────────────────────────────────────────────────┐
│  热数据 (Hot)          │  温数据 (Warm)          │  冷数据 (Cold)      │
│  0 ~ 30 天             │  30 ~ 90 天              │  90+ 天             │
├────────────────────────┼─────────────────────────┼────────────────────┤
│  存储: PostgreSQL      │  存储: PostgreSQL        │  存储: OSS/文件     │
│  查询: 全字段索引      │  查询: 全字段索引        │  查询: 需还原       │
│  性能: 毫秒级          │  性能: 毫秒级            │  性能: 分钟级       │
│  清理: 无              │  清理: DETACH + DROP     │  清理: 按年删除文件 │
│                        │  PARTITION（毫秒级）      │                    │
└────────────────────────┴─────────────────────────┴────────────────────┘
```

**为什么用 DROP PARTITION 而不是 DELETE：**

| 操作 | DELETE | DROP PARTITION |
| :--------- | :------------------------- | :-------------------------------------- |
| 时间复杂度 | O(n)，千万级数据耗时数分钟 | O(1)，毫秒级 |
| WAL 日志量 | 逐行记录，GB 级别 | 仅一条 catalog 变更 |
| 表膨胀 | 产生死元组，需 autovacuum | 无膨胀 |
| 死锁风险 | 与并发写入竞争行锁 | `DETACH CONCURRENTLY`（PG 14+）几乎无感 |

**DEFAULT 分区数据迁移**：当分区自动创建任务失败（如 CronJob 挂死或 pg_partman 异常退出），新数据会涌入 DEFAULT 分区。当月表创建恢复后，需将 DEFAULT 分区中的数据迁移到正确的月份分区：

```sql
-- 步骤 1：确认 DEFAULT 分区中待迁移的数据范围
SELECT MIN(event_time), MAX(event_time), COUNT(*)
FROM identity_audit_event_default;

-- 步骤 2：DETACH DEFAULT 分区，变为独立表
ALTER TABLE identity_audit_event
    DETACH PARTITION identity_audit_event_default CONCURRENTLY;

-- 步骤 3：创建缺失的月份分区（按需创建）
CREATE TABLE identity_audit_event_202608 PARTITION OF identity_audit_event
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE identity_audit_event_202609 PARTITION OF identity_audit_event
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

-- 步骤 4：将独立表中的数据 INSERT 到正确的月份分区
INSERT INTO identity_audit_event
SELECT * FROM identity_audit_event_default;

-- 步骤 5：重建 DEFAULT 分区（空表兜底）
CREATE TABLE identity_audit_event_default
    PARTITION OF identity_audit_event DEFAULT;

-- 步骤 6：DROP 独立表（释放磁盘空间）
DROP TABLE identity_audit_event_default;
```

> 替代方案：使用 pg_partman 的 `partman.partition_data_time()` 自动迁移。
> 建议将此流程封入运维 Runbook，作为分区自动创建告警（§7.2）的响应 SOP。

#### 9.6.2 归档策略配置

```yaml
### identity_service/config/audit_retention.yaml
retention:
  audit_event:
    hot_days: 30           # 热数据保留天数（当前月份 + 上一月）
    warm_days: 90          # 温数据保留天数（累计，即 30+60=90 天后归档）
    cold_days: 365         # 冷数据保留天数（累计，即 90+365=455 天后删除）
    archive_format: jsonl  # 归档格式（jsonl / parquet）
    archive_path: s3://audit-archive/identity/  # 归档存储路径

  partition:
    interval: 1 month       # 分区粒度（与 §3.1 分区键一致）
    premake: 2              # 提前创建未来分区数（pg_partman 或 CronJob）
    default_partition: true # 是否创建默认分区兜底

  cleanup:
    cron: "0 3 * * 0"       # 每周日凌晨 3 点执行（低峰期）
    # 归档流程：DETACH → 导出到 S3 → DROP（详见 §6.3）

  # 合规要求的最小保留期（防止误配置）
  compliance_min_days: 180
```

#### 9.6.3 归档任务伪代码

> 核心思路：**DETACH PARTITION → 导出到冷存储 → DROP PARTITION**，而非逐条 DELETE。

```python
import asyncio
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

async def archive_audit_events():
    """
    每周日凌晨执行（低峰期）。
    将 90 天前的月份分区归档到冷存储。

    流程：
    1. 计算目标分区月份（当前月 - 3 个月）
    2. DETACH CONCURRENTLY（PG 14+）— 分区脱离主表，停止接收写入
    3. COPY 导出到 S3/OSS
    4. 校验归档文件完整性
    5. DROP TABLE — 释放磁盘空间
    """
    now = datetime.now(timezone.utc)
    target_month = now - relativedelta(months=3)
    partition_name = f"identity_audit_event_{target_month.strftime('%Y%m')}"
    archive_key = f"audit/{target_month.year}/{target_month.strftime('%m')}/events_{partition_name}.jsonl"

    # 1. DETACH — 分区脱离主表，变为独立表
    #    使用 CONCURRENTLY 避免 AccessExclusiveLock 阻塞写入（需 PG 14+）
    try:
        await db.execute(
            f"ALTER TABLE identity_audit_event "
            f"DETACH PARTITION {partition_name} CONCURRENTLY"
        )
        logger.info(f"Detached partition: {partition_name}")
    except Exception as e:
        logger.error(f"Failed to detach partition {partition_name}: {e}")
        return

    # 2. 导出到冷存储（S3/OSS/本地文件）
    try:
        row_count = await db.fetchval(
            f"SELECT COUNT(*) FROM {partition_name}"
        )
        if row_count == 0:
            logger.info(f"Partition {partition_name} is empty, skipping archive")
            await db.execute(f"DROP TABLE IF EXISTS {partition_name}")
            return

        # COPY 导出为 JSONL（每行一个 JSON 对象）
        await db.execute(
            f"COPY (SELECT row_to_json(t) FROM {partition_name} t) "
            f"TO '/tmp/{partition_name}.jsonl'"
        )
        await storage.upload(
            f"/tmp/{partition_name}.jsonl",
            f"{config.retention.audit_event.archive_path}{archive_key}",
        )
        logger.info(
            f"Archived {row_count} events from {partition_name} to {archive_key}"
        )
    except Exception as e:
        logger.error(f"Failed to archive partition {partition_name}: {e}")
        # 归档失败，不删除分区，保留数据安全
        return

    # 3. 校验 — 确认归档文件完整可读
    try:
        archive_content = await storage.download(
            f"{config.retention.audit_event.archive_path}{archive_key}"
        )
        archived_lines = archive_content.strip().count("\n") + 1 if archive_content.strip() else 0
        if archived_lines != row_count:
            logger.error(
                f"Archive verification failed for {partition_name}: "
                f"expected {row_count} rows, got {archived_lines}"
            )
            return

        # 逐行校验 JSON 格式有效性（防止归档文件损坏）
        lines = archive_content.strip().splitlines()
        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Archive file {archive_key} contains malformed JSON "
                    f"at line {i + 1}: {e}"
                )
                return

        # 可选：抽样校验关键字段是否存在（如 event_id / event_time）
        sample_lines = lines[:min(10, len(lines))]
        for i, line in enumerate(sample_lines):
            record = json.loads(line)
            if not record.get("event_id") or not record.get("event_time"):
                logger.warning(
                    f"Archive file {archive_key} line {i + 1}: "
                    f"missing critical fields (event_id/event_time)"
                )
                # 仅记录警告，不阻断归档（部分字段缺失不一定是损坏）
    except Exception as e:
        logger.error(f"Archive verification failed for {partition_name}: {e}")
        return

    # 4. DROP — 归档校验通过，删除已脱离的独立表
    await db.execute(f"DROP TABLE IF EXISTS {partition_name}")
    logger.info(f"Dropped partition: {partition_name} (archived to {archive_key})")


async def cleanup_cold_storage():
    """
    删除超过冷数据保留期（365 天）的归档文件。
    与 archive_audit_events 在同一 CronJob 中先后执行。
    """
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=config.retention.audit_event.cold_days
    )
    prefix = f"audit/{cutoff.year}/"

    objects = await storage.list(prefix=prefix)
    for obj in objects:
        if obj.last_modified < cutoff:
            await storage.delete(obj.key)
            logger.info(f"Deleted cold archive: {obj.key}")
```

> **分区自动创建**（pg_partman 或 CronJob）：
>
> ```sql
> -- 每月初自动执行，提前创建未来 2 个月的分区
> -- 如当前为 2026-07，则创建 2026-08 和 2026-09
> CREATE TABLE IF NOT EXISTS identity_audit_event_202608
>     PARTITION OF identity_audit_event
>     FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
> CREATE TABLE IF NOT EXISTS identity_audit_event_202609
>     PARTITION OF identity_audit_event
>     FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
> ```
>
> **DETACH CONCURRENTLY 最低要求**：PostgreSQL 14+。若使用 PG 12/13，需改用普通 `DETACH PARTITION`（会短暂持有 AccessExclusiveLock），建议在凌晨低峰期（写入量最小）执行。

______________________________________________________________________

### 9.7 监控与告警

#### 9.7.1 Prometheus 指标

| 指标名 | 类型 | 说明 |
| :------------------------------------ | :-------- | :----------------------------------------- |
| `audit_event_total{category,result}` | Counter | 审计事件总数（按类别和结果） |
| `audit_write_latency_ms{quantile}` | Histogram | 审计写入延迟 |
| `audit_write_failures_total` | Counter | 审计写入失败次数（直接落 stderr） |
| `audit_recovery_success_total` | Counter | 补偿任务成功恢复的审计事件数 |
| `audit_recovery_dead_letter_total` | Counter | 补偿失败进入死信队列的事件数（需人工介入） |
| `audit_buffer_size` | Gauge | 异步写入缓冲区当前积压量（条） |
| `audit_denied_total{event_type}` | Counter | 权限拒绝次数（按事件类型） |
| `audit_break_glass_activations_total` | Counter | Break-Glass 激活次数 |
| `audit_archive_bytes_total` | Counter | 归档数据量（bytes） |
| `audit_cleanup_duration_ms` | Histogram | 清理任务执行耗时 |

#### 9.7.2 告警规则

| 告警 | 条件 | 级别 | 说明 |
| :------------------- | :-------------------------------------------------------------------------- | :------- | :-------------------------------------------------------------------- |
| 审计写入失败率过高 | `rate(audit_write_failures_total[5m]) / rate(audit_event_total[5m]) > 0.01` | Critical | 审计数据库可能不可用 |
| 审计补偿死信堆积 | `audit_recovery_dead_letter_total > 0` | Critical | 补偿任务也无法恢复，需人工介入核查丢失的审计事件 |
| 审计异步缓冲区堆积 | `audit_buffer_size > 10000`（持续 5 分钟） | Warning | 消费跟不上生产，可能丢失审计事件（缓冲区满后新事件直接降级到 stderr） |
| 权限拒绝突增 | `rate(audit_denied_total[5m]) / rate(audit_denied_total[1h]) > 3` | Warning | 可能存在暴力破解或越权攻击 |
| Break-Glass 激活 | `audit_break_glass_activations_total > 0` | Critical | |
| 归档任务失败 | `audit_cleanup_duration_ms` 连续 3 次 > 30 分钟 | Warning | |
| 磁盘空间不足 | 审计表所在磁盘使用率 > 85% | Warning | |
| DEFAULT 分区异常增长 | `pg_table_size('identity_audit_event_default') > 104857600`（100 MB） | Warning | 分区自动创建任务失败，所有数据涌入 DEFAULT 分区将导致无法按月归档 |

______________________________________________________________________

### 9.8 与权限管理的整合

#### 9.8.1 权限校验审计（已有，来自§8.5）

在 `require_permission` 依赖注入中，每次权限校验自动记录审计日志：

```python
async def require_permission(permission_code: str):
    async def dependency(request: Request, auth_mgr = Depends(get_auth_manager)):
        user_payload = getattr(request.state, "user_payload", {})
        global_user_id = user_payload.get("sub")

        if not await auth_mgr.has_permission(global_user_id, permission_code):
            # 拒绝 → 强制同步写入审计日志
            await audit_logger.log_authz(
                action="check_deny",
                user_id=global_user_id,
                result="denied",
                target_type="api",
                target_id=request.url.path,
                detail={"permission_code": permission_code},
                sync_required=True           # 敏感操作，同步写入
            )
            raise HTTPException(status_code=403)

        # 允许 → 异步批量写入（高频，用 batch）
        await audit_logger.log_authz(
            action="check_allow",
            user_id=global_user_id,
            result="success",
            target_type="api",
            target_id=request.url.path,
            detail={"permission_code": permission_code}
        )
        return user_payload
    return Depends(dependency)
```

#### 9.8.2 角色变更审计

在 `AuthorizationManager` 的角色操作方法中，变更前后均记录 old_value/new_value：

```python
async def assign_role(self, user_id: str, role_id: int, scope: dict, granted_by: str):
    # 变更前记录
    old_roles = await self.get_user_roles(user_id)

    # 执行变更
    await self.repo.assign_role(user_id, role_id, scope, granted_by)

    # 变更后记录
    await audit_logger.log_operation(
        target_type="role",
        action="assign",
        user_id=granted_by,
        target_id=str(role_id),
        target_name=(await self.repo.get_role(role_id)).role_name,
        result="success",
        old_value={"roles": old_roles},
        new_value={"roles": await self.get_user_roles(user_id)},
        sync_required=True     # 角色分配是敏感操作
    )
```

#### 9.8.3 数据权限拦截器审计

Repository 拦截器每次注入数据权限条件时，记录一条 debug 级别审计日志（不阻塞、可采样）：

```python
### 采样率可配置（环境变量 DATA_SCOPE_AUDIT_SAMPLE_RATE，默认 0.01 = 1%）
### 生产环境临时排查时可调至 1.0 全量捕获
import os, random

SAMPLE_RATE = float(os.getenv("DATA_SCOPE_AUDIT_SAMPLE_RATE", "0.01"))

if random.random() < SAMPLE_RATE:
    await audit_logger.log(AuditEvent(
        event_type="data.scope_applied",
        category="data",
        actor_user_id=current_user_id,
        target_type=model.__tablename__,
        action="filter",
        result="success",
        detail={"scope": scope.to_dict(), "applied_filter": filter_clause},
        async_mode=True
    ))
```

______________________________________________________________________

### 9.9 合规性映射

#### 9.9.1 ISO 27001:2022 对照

| ISO 控制项 | 要求 | 本方案覆盖 |
| :---------------------- | :------------------------- | :-------------------------------------- |
| **A.8.15 日志记录** | 记录活动、异常、故障等事件 | 六类审计事件全覆盖 |
| **A.8.16 日志保护** | 防篡改、防未授权访问 | 只追加不修改、管理员权限查询 |
| **A.8.17 时钟同步** | 事件时间戳可靠 | PostgreSQL `TIMESTAMPTZ` + NTP |
| **A.5.15 访问控制** | 基于业务需求的访问控制 | 权限校验审计（`permission.check_deny`） |
| **A.5.18 特权访问管理** | 特权账户使用受控 | Break-Glass 激活审计 + 强制告警 |
| **A.8.9 配置管理** | 配置变更记录 | `system.config_change` 事件 |

#### 9.9.2 等保 2.0 对照

| 等保要求 | 对应条款 | 本方案覆盖 |
| :----------------------------- | :--------- | :------------------------------------------------------ |
| 安全审计覆盖每个用户 | 8.1.4.1 a) | `actor_user_id` 全覆盖 |
| 审计记录包括事件类型、时间、IP | 8.1.4.1 b) | 统一事件结构中的 `event_type`、`event_time`、`actor_ip` |
| 审计记录保护，避免被删除/修改 | 8.1.4.2 | 只追加不修改、应用层禁止 DELETE |
| 审计日志定期备份 | 8.1.4.3 | 冷归档到 OSS，保留 365 天 |
| 审计进程故障不影响业务 | — | 异步写入，失败不阻塞主流程 |

______________________________________________________________________

### 9.10 实施路线图

> DDAP、AMDP 等均为绿地系统，无需考虑存量迁移。以下为一次性交付计划。

| 阶段 | 内容 | 交付物 |
| :--------------- | :---------------------------------------------------------------------------------------------------- | :----------------- |
| **建表与采集器** | `identity_audit_event` 建表（含分区），四张现有表在建表时直接包含标准化字段，`AuditLogger` 采集器实现 | 审计存储就绪 |
| **API 与监控** | 统一审计 API（`/audit/events`、`/audit/stats`、`/audit/export`），Prometheus 指标 + 告警规则 | 审计查询与监控可用 |
| **归档** | 归档任务（热/温/冷三级存储），定时清理 CronJob | 全生命周期管理就绪 |

以上三项可在同一迭代内并行或顺序交付，无需分多期。

______________________________________________________________________

### 9.11 总结

本扩展方案在现有分散的日志体系之上，构建了统一的审计日志层。核心设计原则：

- **统一但不破坏**：`identity_audit_event` 作为统一审计存储，四张现有表在建表时直接包含标准化字段，无需后续迁移
- **标准化事件模型**：who/when/what/where/result 六要素统一结构，内置合规标签映射
- **异步不阻塞**：审计写入默认异步，敏感操作强制同步，确保业务不受影响
- **分级存储**：热/温/冷三级存储，兼顾查询性能与存储成本
- **合规可追溯**：每条审计事件映射到 ISO 27001 / 等保 2.0 控制项，审计时可直接导出

______________________________________________________________________

#### 附录：方案B（嵌入式 identity-module）下的审计日志适配

> 本文 §2-§11 基于方案A（独立 Identity Service，审计日志集中于 `identity_db`）设计。方案B（嵌入式 identity-module）将审计日志分散到各业务系统自有 DB 中，需要以下适配。

##### B.1 架构差异

| 维度 | 方案A（独立 Identity Service） | 方案B（嵌入式 identity-module） |
| :-------------- | :------------------------------------------------ | :------------------------------------------------------- |
| **审计存储** | 集中在 `identity_db` 的 `identity_audit_event` 表 | 分散在各业务系统自有 DB 中（DDAP、AMDP 等各存一份） |
| **审计查询** | 单次查询覆盖全部审计事件 | 默认查询本地，跨系统需聚合 |
| **审计 API** | `GET /identity/v1/audit/events` 直接返回全量 | 各系统暴露 `/identity/v1/audit/events`，仅返回本系统事件 |
| **AuditLogger** | 全局单一实例，写入 `identity_db` | 各系统独立实例，写入各自 DB |
| **归档** | 集中归档到统一 OSS 路径 | 各系统独立归档，路径可配置 |
| **监控** | 单一 Prometheus 端点 | 各系统独立暴露指标，需聚合 |
| **合规审计** | 一次性导出全量 | 需从各系统导出后合并 |

##### B.2 审计组件在 identity-module 中的位置

在方案B的包结构中，审计相关组件作为 `identity-module` 的扩展模块：

```
identity-module/
├── identity_module/
│   ├── models/
│   │   ├── ...（原有模型）
│   │   ├── audit_event.py          # identity_audit_event（统一审计表）
│   │   └── audit_log.py            # identity_audit_log（权限审计日志）
│   │
│   ├── routers/
│   │   ├── ...（原有路由）
│   │   └── audit.py                # /identity/v1/audit/*（审计查询API）
│   │
│   ├── services/
│   │   ├── ...（原有服务）
│   │   ├── audit_logger.py         # AuditLogger（审计采集器）
│   │   └── audit_archiver.py       # 归档任务
│   │
│   └── config/
│       └── audit_retention.yaml    # 保留策略配置
```

##### B.3 各组件适配说明

###### B.3.1 审计存储（§3.1）

**无需修改**。`identity_audit_event` 表结构不变，建表语句随 `identity-module` 安装时自动在业务系统 DB 中执行。各系统的 `identity_audit_event` 表结构一致，互不感知。

> **关联表同步确认**：方案B中各业务系统的 `identity_provisioning_log`、`identity_sync_event_log`、`identity_audit_log` 在建表时同样包含 [§3.2](#932-%E7%8E%B0%E6%9C%89%E6%97%A5%E5%BF%97%E8%A1%A8%E5%8E%9F%E7%94%9F%E5%8C%85%E5%90%AB%E6%A0%87%E5%87%86%E5%8C%96%E5%AD%97%E6%AE%B5) 定义的标准化字段（`event_type`/`category`/`target_type`/`target_id`/`target_name`/`compliance_tags` 等），与方案A完全一致。三张表的建表语句由 `identity-module` 统一管理，方案A/B共享同一份 DDL。

```python
### identity_module/models/audit_event.py
class IdentityAuditEvent(Base):
    __tablename__ = "identity_audit_event"
    # 字段定义与方案A完全一致
    event_id = Column(String(32), primary_key=True)
    event_type = Column(String(64), nullable=False)
    # ...（其余字段见 §3.1）
```

###### B.3.2 审计查询 API（§5.1）

**局部适配**。方案B中，`GET /identity/v1/audit/events` 挂载在各业务系统路由下，**默认仅返回本系统事件**。

```python
### identity_module/routers/audit.py
@router.get("/identity/v1/audit/events")
async def list_audit_events(
    # ... 查询参数与方案A完全一致
    request: Request,
    db: Session = Depends(get_db),
):
    # 关键差异：默认限定 scope = "local"，仅查本系统DB
    query = db.query(IdentityAuditEvent)
    # ... 应用过滤条件
    return paginate(query)
```

**跨系统聚合查询**：如需跨系统审计，由 Master 节点提供聚合端点：

```
GET /identity/v1/audit/events?scope=all
```

Master 收到 `scope=all` 后，并行查询所有 Replica 的审计端点，合并结果按 `event_time` 排序后返回。

**可用性保障**：

| 机制 | 说明 |
| :------------- | :------------------------------------------------------------------------- |
| **超时控制** | 每个 Replica 查询超时 3s（可配置），超时则标注状态并跳过 |
| **降级返回** | 仅返回已成功查询的数据，不因单个 Replica 不可达而整体失败 |
| **部分性标记** | 响应中携带 `partial: true` 和 `sources_skipped` 列表，告知客户端数据不完整 |

**聚合配置**（`identity-module` 统一配置，方案A/B均适用）：

```yaml
### identity_module/config/audit_aggregation.yaml
audit_aggregation:
  scope_default: "local"           # 默认查询范围：local（仅本系统） | all（跨系统聚合）
  query_timeout: 3                 # 每个 Replica 的 HTTP 请求超时（秒）
  max_replicas: 10                 # 最大并行查询数（防止连接池耗尽）
  partial_on_timeout: true         # 部分 Replica 超时后返回 partial=true（不整体失败）
  total_timeout: 30                # 聚合查询整体超时（秒），超时后强制返回已有结果
  on_total_timeout: "return_partial"  # 整体超时后的行为：return_partial（返回已有数据）| fail（整体失败）
```

> **默认策略说明**：方案B中 `scope_default` 为 `local`，避免每次查询都产生跨系统网络调用。仅在 Master 节点且显式传入 `?scope=all` 时才触发聚合。方案A中 `scope_default` 为 `all`（所有数据在同一个 DB 中）。

**聚合查询实现**：

```python
import asyncio
from httpx import AsyncClient, TimeoutException

REPLICA_ENDPOINTS = {
    "ddap":  "http://ddap:8000/identity/v1/audit/events",
    "amdp":  "http://amdp:8000/identity/v1/audit/events",
    # 其他系统按需注册
}
REPLICA_TIMEOUT = 3.0  # 秒，可通过环境变量覆盖
TOTAL_TIMEOUT = 30.0   # 聚合查询整体超时，超时后返回已有结果
ON_TOTAL_TIMEOUT = "return_partial"  # return_partial | fail

async def aggregate_audit_events(params: dict) -> dict:
    """并行查询所有 Replica，合并结果（带整体超时兜底）"""
    async with AsyncClient(timeout=REPLICA_TIMEOUT) as client:
        tasks = {
            name: client.get(url, params=params)
            for name, url in REPLICA_ENDPOINTS.items()
        }
        # 使用 asyncio.wait 替代 gather，支持整体超时
        done, pending = await asyncio.wait(
            tasks.values(),
            timeout=TOTAL_TIMEOUT,
            return_when=asyncio.ALL_COMPLETED
        )

    sources = {}
    sources_skipped = []
    all_events = []

    # 处理已完成的请求
    name_by_task = {id(t): n for n, t in tasks.items()}
    for task in done:
        name = name_by_task[id(task)]
        try:
            result = task.result()
            if result.status_code != 200:
                sources[name] = f"http_error_{result.status_code}"
                sources_skipped.append(name)
            else:
                data = result.json()
                sources[name] = "success"
                all_events.extend(data.get("events", []))
        except TimeoutException:
            sources[name] = "timeout"
            sources_skipped.append(name)
            logger.warning(f"Replica {name} timeout (per-request)")
        except Exception as e:
            sources[name] = "error"
            sources_skipped.append(name)
            logger.warning(f"Replica {name} error: {e}")

    # 处理超时未完成的请求（整体超时）
    for task in pending:
        name = name_by_task[id(task)]
        sources[name] = "timeout"
        sources_skipped.append(name)
        task.cancel()  # 取消仍在等待的请求，释放连接
        logger.warning(f"Replica {name} timeout (aggregation total timeout {TOTAL_TIMEOUT}s)")

    # 整体超时策略
    if pending and ON_TOTAL_TIMEOUT == "fail":
        raise TimeoutError(
            f"Aggregation total timeout ({TOTAL_TIMEOUT}s), "
            f"{len(pending)}/{len(tasks)} replicas incomplete"
        )

    # 按 event_time 降序排序
    all_events.sort(key=lambda e: e["event_time"], reverse=True)

    return {
        "sources": sources,
        "sources_skipped": sources_skipped,
        "events": all_events,
        "total_events": len(all_events),
        "partial": len(sources_skipped) > 0,
    }
```

**聚合响应格式**：

```json
{
    "sources": {
        "ddap": "success",
        "amdp": "timeout",
        "sonarqube": "http_error_503"
    },
    "sources_skipped": ["amdp", "sonarqube"],
    "events": [
        {"event_id": "...", "event_type": "user.create", "event_time": "2026-07-15T10:30:00Z", ...},
        {"event_id": "...", "event_type": "auth.login",   "event_time": "2026-07-15T10:25:00Z", ...}
    ],
    "total_events": 12345,
    "partial": true
}
```

**`sources` 状态枚举**：

| 状态值 | 含义 |
| :------------------- | :-------------------------- |
| `success` | 查询成功，数据已合并 |
| `timeout` | 超时（默认 3s） |
| `connection_refused` | 连接被拒绝 |
| `http_error_4xx` | 客户端错误（如 401 未授权） |
| `http_error_5xx` | 服务端错误（如 503 不可用） |

**前端处理建议**：

```javascript
// 当 partial === true 时，显示警告横幅
if (response.partial) {
    showWarningBanner(
        `审计数据不完整：以下系统不可达 — ${response.sources_skipped.join("、")}`
    );
}
```

**合规导出特殊处理**：合规审计要求全量数据。`POST /audit/export?scope=all` 在 `partial: true` 时应拒绝导出正式报告，或仅导出带水印的"草稿"版本，并在导出元数据中标注缺失系统。

###### B.3.3 AuditLogger 采集器（§4.2）

**无需修改**。`AuditLogger` 的接口和逻辑不变，各系统独立实例化，写入各自的 DB：

```python
### 方案A：全局单例
audit_logger = AuditLogger(db_session_factory)

### 方案B：各系统独立实例（代码相同）
audit_logger = AuditLogger(db_session_factory)  # db_session_factory 指向各系统自有DB
```

###### B.3.4 审计归档（§6）

**配置级差异**。归档逻辑不变，但归档路径需区分系统：

```yaml
### 方案A（一个路径）
audit_retention:
  archive_path: s3://audit-archive/identity/

### 方案B（各系统独立路径）
audit_retention:
  archive_path: s3://audit-archive/${SYSTEM_NAME}/   # 如 ddap/、amdp/
```

归档任务通过 `identity-module` 的 `role` 控制：Master 可归档全量（如有聚合），Replica 仅归档本地。

###### B.3.5 监控指标（§7）

**无需修改**。Prometheus 指标定义不变，各系统独立暴露。如需全局视图，Grafana 面板按 `instance` 标签聚合即可。

###### B.3.6 统一查询视图（§3.3）

**局部适配**。`v_audit_event_unified` 视图在各系统 DB 内独立存在，仅覆盖本系统的四张日志表。跨系统视图需在 Master 层通过应用代码聚合（同 B.3.2）。

###### B.3.7 合规审计导出（§5.3）

**Master 聚合导出**。方案B中，合规审计通常要求全量导出。由 Master 节点提供聚合导出：

```
POST /identity/v1/audit/export?scope=all
```

Master 并行从各 Replica 拉取审计数据，合并为单一文件后返回。导出元数据中标注各分片来源：

```json
{
    "format": "jsonl",
    "scope": "all",
    "sources": [
        {"system": "ddap", "event_count": 12345},
        {"system": "amdp", "event_count": 6789}
    ],
    "total_events": 19134
}
```

###### B.3.8 Replica 角色下的审计 API 可用性

与权限管理方案的 Replica 角色设计一致，审计方案也需区分 Master/Replica 的 API 可用范围，避免数据不一致：

| API | Master | Replica | 说明 |
| :------------------- | :----------------------- | :------------------------ | :---------------------------------------------- |
| `GET /audit/events` | 可用（支持 `scope=all`） | 可用（仅 `scope=local`） | Replica 默认仅返回本系统数据 |
| `GET /audit/stats` | 可用（全量统计） | 可用（本地统计） | 本地统计在 Replica 上仍有意义 |
| `POST /audit/export` | 可用（支持跨系统导出） | **禁用（403 Forbidden）** | 防止每个 Replica 独立导出导致数据碎片化、不一致 |

> **设计理由**：审计导出是合规审计的核心入口，数据必须完整且一致。若允许多个 Replica 各自导出，审计员将拿到多份不完整的碎片数据，无法拼出一份统一的审计报告。强制由 Master 聚合导出，确保单一可信源。

**实现**：`identity-module` 通过角色标记控制 API 可用性：

```python
### identity_module/routers/audit.py
from identity_module.config import get_module_role  # "master" | "replica"

@router.post("/identity/v1/audit/export")
async def export_audit(request: Request, scope: str = "local"):
    role = get_module_role()
    if role == "replica":
        raise HTTPException(
            status_code=403,
            detail="Audit export is only available on the Master node. "
                   "Please use the Master endpoint for cross-system export."
        )
    # Master 正常处理导出
    return await do_export(scope=scope)
```

##### B.4 方案B下的审计能力矩阵

| 能力 | 方案A | 方案B（本地） | 方案B（Master聚合） |
| :------------- | :----------- | :------------ | :------------------ |
| 单系统审计查询 | 直接（全量） | 直接（本地） | 同左 |
| 跨系统审计查询 | 直接（全量） | 不可用 | Master 聚合 |
| 审计统计 | 全量 | 本地 | Master 聚合 |
| 合规导出 | 一键导出 | 单系统导出 | Master 聚合导出 |
| 实时告警 | 全局 | 本系统 | 各系统独立告警 |
| 归档 | 集中 | 独立 | 独立 |
| 事件写入 | 中心化 | 本地化 | 本地化 |

##### B.5 建议

对于审计合规要求较高的场景，推荐：

- **主路径**：方案A（独立 Identity Service），审计日志天然集中，合规审计一键导出
- **混合路径**：方案A 做 Master + 业务系统装方案B Replica，Replica 的审计日志定期或按需同步到 Master 的 `identity_audit_event` 表，实现审计集中化
- **纯方案B**：适用于审计要求较低或单系统场景，各系统独立管理审计日志，合规审计时手动聚合

## 10. 通知服务

> **方案适用范围**：本章描述方案A（独立 Identity Service）的通知架构——通知作为 Iapetus 内置模块，通过 `/identity/v1/notifications/*` API 对外暴露。方案B（嵌入式 identity_module）不内置通知服务，业务系统通过独立的 `notification-kit` 包自行集成 SMTP 能力，不经过 identity_module 路由。两者职责分离依据：通知是基础设施横切关注点（SMTP 管道），identity_module 仅关注身份管理领域（用户/部门/认证/Provisioning）。详见 §10.7 方案A/B适配。

> 本章整合自原通知服务设计 v1.9。通知服务为 Iapetus 内置核心模块，提供 SMTP 邮件发送器、模板渲染器及审计联动能力，供 Iapetus 内部各子模块（Provisioning、权限管理、审计告警）统一使用。其他业务系统（AMDP、DDAP）通过调用 Iapetus 通知 API 使用此能力。

**版本**：v1.9
**日期**：2026-06-27
**关联文档**：本设计方案 v5.0、§8（权限管理）、§9（审计日志）
**定位**：Iapetus 核心功能模块（非独立 kit）

**v1.9 变更**：§5.3 其他通知场景新增"密码同步失败告警"行（`auth.password_sync_failed` 重试耗尽），与主文档 v5.0 §21.5 密码管理 Fan-out + Saga 补偿对齐。
**v1.8 变更**：§4.2 `TemplateRenderer` 新增 `notification_template_missing_var_total{missing_key}` Counter 指标；`render()` 的 KeyError 捕获处增加 `.inc()` 调用，便于 Grafana 监控模板变量不匹配趋势；§8.1 Prometheus 指标表新增对应行。
**v1.7 变更**：§3.2 `EmailSender.send()` / `send_bulk()` 新增可选参数 `actor_user_id`（默认 `None` → 内部填充 `"system"`），由调用方区分自动发送与管理员手动操作；§9 审计日志联动表新增 `actor_user_id` 规则列，代码示例展示自动发送和管理员手动操作两种场景的传值方式。
**v1.6 变更**：模块内部结构从独立包重构为 Iapetus 内置模块（`app/notification/`）；删除 `pyproject.toml` 独立打包配置。
**v1.5 变更**：§10.6.2 AMDP 集成从 `pip install notification-kit` 改为调用 Iapetus 通知 API（`/identity/v1/notifications/email`），AMDP 不再维护 SMTP 配置。
**v1.4 变更**：§3.2 `EmailSender.__init__` 新增 `max_attachment_size_mb`（默认 10MB，附件超限拒绝发送并记录审计日志）和 `pool_size`（默认 5，连接池复用减少 TLS 握手延迟）；`_send_one()` 从 `aiosmtplib.send()` 改为 `SMTP` 客户端连接池模式；新增 `health_check()` 方法（发送 NOOP 命令，用于监控探测 SMTP 连通性）。
**v1.3 变更**：§4.2 `TemplateRenderer.render()` 新增 KeyError 防御 — 变量缺失时用 `"（未提供）"` 占位符替代，不中断邮件发送；记录 Warning 日志含缺失键名和可用变量列表，便于运维排查。
**v1.2 变更**：§3.2 `EmailSender.__init__` 新增 `max_concurrent` 参数（默认 5）；`send_bulk()` 从串行改为 `asyncio.Semaphore` 有限并发，避免大批量（如 100 封入职邮件）串行发送长尾延迟（~20s → ~4s）。
**v1.1 变更**：§2 的 `EmailMessage` 新增 `to_dict()` / `from_dict()` 序列化方法，支持持久化存储；§3.1 设计原则由"指数退避重试"改为"持久化重试"；§3.2 新增 `PostgreSQLRetryQueue` 和 `RetryWorker` 类，`EmailSender.send()` 发送失败后投递到 PostgreSQL 持久化表 `notification_email_retry` 而非 `asyncio.sleep()` 内存重试，进程崩溃重启不丢失待重试邮件；§3.3 配置入口新增 `PostgreSQLRetryQueue` 和 `RetryWorker` 初始化示例；§7.3 差异对照表新增"站内通知"行。

______________________________________________________________________

### 10.1 定位与设计目标

#### 10.1.1 定位

Iapetus 设计方案 §5.6 已定义了通知通道的初步框架（SMTP 邮件 + 短信 + 企微 Webhook），但分散在 Provisioning 流程中，缺乏统一的发送、重试、模板和监控能力。

本章将通知能力系统化为 Iapetus 内置的核心功能模块，包含：

| 组件 | 说明 |
| :-------------- | :-------------------------------------------------------------------------------------- |
| SMTP 邮件发送器 | 连接池、持久化重试、HTML/文本双模，为 Identity Service 所有子模块提供统一的邮件发送能力 |
| 消息模板渲染器 | 变量替换 + 多通道渲染，支持邮件/短信/企微等通道 |
| 审计日志联动 | 发送成功/失败/限流事件自动记入 §9 统一审计日志 |
| 通知 API | 对外暴露 `/identity/v1/notifications/*`，供 AMDP、DDAP 等业务系统调用 |

**定位原则**：

- 通知模块是 Iapetus 的原生功能，不作为独立的 pip 包或 kit 发布
- 其他业务系统（AMDP、DDAP）不安装任何通知相关包，统一通过 Iapetus 通知 API 发送邮件
- 发送器内部直接使用 aiosmtplib（Identity Service 已有多元基础设施），不引入额外依赖

#### 10.1.2 设计目标

| 目标 | 说明 |
| :------------------------ | :--------------------------------------------------------------------------------------------------- |
| **Identity Service 原生** | 通知模块编译在 Identity Service 内，不拆分为独立包 |
| **统一发送入口** | Provisioning、权限告警、审计告警等子模块统一通过此模块发送 |
| **对外 API** | 业务系统（AMDP、DDAP）通过 `/identity/v1/notifications/*` 调用 |
| **方案A/B分离** | 方案A：通知内置于 Iapetus；方案B：业务系统通过 `notification-kit` 独立包集成，不纳入 identity_module |
| **异步优先** | 邮件发送不阻塞业务主流程 |

______________________________________________________________________

### 10.2 通知模块设计

> 位于 `app/notification/` 目录，与 `app/services/`、`app/api/`、`app/provisioner/` 平级，是 Iapetus 的一等模块。

#### 10.2.1 模块结构

```
app/notification/
├── __init__.py              # 公开 API：EmailSender, TemplateRenderer, EmailMessage, SendResult
├── email_sender.py          # SMTP 邮件发送器（连接池 + 持久化重试）
├── template_renderer.py     # 消息模板渲染器（变量替换 + 多通道）
└── types.py                 # 类型定义（EmailMessage, SendResult, Channel 等）
```

#### 10.2.2 核心类型定义

```python
### app/notification/types.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Channel(Enum):
    """发送通道"""
    EMAIL_HTML = "email_html"     # 邮件 HTML 格式
    EMAIL_TEXT = "email_text"     # 邮件纯文本（自动 strip HTML tags）
    SMS = "sms"                   # 短信（截断到 140 字）
    WECOM = "wecom"               # 企微消息（Markdown 格式）
    DINGTALK = "dingtalk"         # 钉钉消息（Markdown 格式）


class SendStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"  # 被限流


@dataclass
class EmailAddress:
    email: str
    name: Optional[str] = None     # 收件人显示名


@dataclass
class EmailAttachment:
    filename: str
    content: bytes                 # 二进制内容
    mime_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    to: list[EmailAddress]
    subject: str
    body_html: Optional[str] = None       # HTML 正文
    body_text: Optional[str] = None       # 纯文本正文（兜底）
    cc: list[EmailAddress] = field(default_factory=list)
    bcc: list[EmailAddress] = field(default_factory=list)
    attachments: list[EmailAttachment] = field(default_factory=list)
    reply_to: Optional[EmailAddress] = None
    tags: dict = field(default_factory=dict)  # 自定义标签（用于监控/追踪）

    def to_dict(self) -> dict:
        """序列化为 dict（供 PostgreSQLRetryQueue 持久化）"""
        return {
            "to": [{"email": a.email, "name": a.name} for a in self.to],
            "cc": [{"email": a.email, "name": a.name} for a in self.cc],
            "bcc": [{"email": a.email, "name": a.name} for a in self.bcc],
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "reply_to": {"email": self.reply_to.email, "name": self.reply_to.name}
                if self.reply_to else None,
            "attachments": [
                {"filename": a.filename, "content": a.content.hex(), "mime_type": a.mime_type}
                for a in self.attachments
            ],
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmailMessage":
        """从 dict 反序列化"""
        return cls(
            to=[EmailAddress(**a) for a in data["to"]],
            cc=[EmailAddress(**a) for a in data.get("cc", [])],
            bcc=[EmailAddress(**a) for a in data.get("bcc", [])],
            subject=data["subject"],
            body_html=data.get("body_html"),
            body_text=data.get("body_text"),
            reply_to=EmailAddress(**data["reply_to"]) if data.get("reply_to") else None,
            attachments=[
                EmailAttachment(
                    filename=a["filename"],
                    content=bytes.fromhex(a["content"]),
                    mime_type=a.get("mime_type", "application/octet-stream"),
                ) for a in data.get("attachments", [])
            ],
            tags=data.get("tags", {}),
        )


@dataclass
class SendResult:
    message_id: str                # 唯一消息ID
    status: SendStatus
    recipient: str                 # 收件人邮箱
    error_message: Optional[str] = None
    retry_count: int = 0
    elapsed_ms: float = 0.0
```

______________________________________________________________________

### 10.3 SMTP 邮件发送器

#### 10.3.1 设计原则

- **传输层职责**：只管建立连接、发送字节、处理重试，不关心邮件内容
- **连接池复用**：多封邮件批量发送时复用同一 SMTP 连接
- **持久化重试**：发送失败后投递到 PostgreSQL 持久化重试表 `notification_email_retry`（`PostgreSQLRetryQueue`），后台 `RetryWorker` 按指数退避（5s / 30s / 120s，与 Identity Service §10 的 Provisioning 重试策略一致）轮询重试；Identity Service 进程崩溃重启不丢失待重试邮件
- **异步发送**：默认 `asyncio.create_task` 异步，发送失败不阻塞主流程
- **可观测**：每次发送记录 Prometheus 指标 + 结构化日志

#### 10.3.2 接口定义

````python
### app/notification/email_sender.py

import asyncio
import json
import logging
import smtplib
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosmtplib
from aiosmtplib import SMTP
from .types import EmailMessage, SendResult, SendStatus

logger = logging.getLogger(__name__)


class PostgreSQLRetryQueue:
    """持久化重试队列 — 使用 PostgreSQL 表存储待重试邮件，进程重启后恢复。

    设计原则：
    - 基于 PostgreSQL 持久化表 notification_email_retry，零新基础设施
    - 通过 FOR UPDATE SKIP LOCKED 并发取到期任务，多 worker 安全
    - 每条记录包含重试次数、下次重试时间戳
    - 重试耗尽后的最终失败状态通过审计日志（§5.2）和 Prometheus 指标暴露

    表结构（由 migration 创建）：
    ```sql
    CREATE TABLE notification_email_retry (
        id            BIGSERIAL PRIMARY KEY,
        message       JSONB NOT NULL,
        retry_count   INT NOT NULL DEFAULT 0,
        next_retry_at TIMESTAMPTZ NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_email_retry_due ON notification_email_retry(next_retry_at)
        WHERE retry_count <= 3;
    ```
    """

    BACKOFF_SECONDS = [5, 30, 120]       # 指数退避间隔
    MAX_RETRIES = 3                       # 最大重试次数

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def enqueue(self, message: EmailMessage, retry_count: int = 0) -> None:
        """将发送失败的邮件入队，计算下次重试时间"""
        now = datetime.now(timezone.utc)
        next_retry_at = now + timedelta(seconds=self.BACKOFF_SECONDS[min(
            retry_count,
            len(self.BACKOFF_SECONDS) - 1
        )])

        async with self.session_factory() as db:
            stmt = text("""
                INSERT INTO notification_email_retry (message, retry_count, next_retry_at)
                VALUES (:message, :retry_count, :next_retry_at)
            """).bindparams(
                message=json.dumps(message.to_dict()),
                retry_count=retry_count,
                next_retry_at=next_retry_at,
            )
            await db.execute(stmt)
            await db.commit()

    async def dequeue_due(self, batch_size: int = 50) -> list[dict]:
        """取出到期需重试的任务（FOR UPDATE SKIP LOCKED，并发安全）"""
        async with self.session_factory() as db:
            stmt = text("""
                SELECT id, message, retry_count
                FROM notification_email_retry
                WHERE next_retry_at <= now()
                ORDER BY next_retry_at
                LIMIT :batch_size
                FOR UPDATE SKIP LOCKED
            """).bindparams(batch_size=batch_size)
            result = await db.execute(stmt)
            rows = result.fetchall()
            if not rows:
                await db.commit()
                return []

            ids = [row[0] for row in rows]
            del_stmt = text("DELETE FROM notification_email_retry WHERE id = ANY(:ids)")
            await db.execute(del_stmt.bindparams(ids=ids))
            await db.commit()

            return [
                {"message": json.loads(row[1]), "retry_count": row[2]}
                for row in rows
            ]


class RetryWorker:
    """后台重试 Worker — 周期性取出到期任务，调用 EmailSender 重试"""

    def __init__(self, email_sender: "EmailSender", retry_queue: PostgreSQLRetryQueue,
                 poll_interval: float = 5.0):
        self.email_sender = email_sender
        self.retry_queue = retry_queue
        self.poll_interval = poll_interval
        self._running = False

    async def start(self):
        """启动 worker 循环"""
        self._running = True
        while self._running:
            try:
                due_tasks = await self.retry_queue.dequeue_due()
                for task in due_tasks:
                    message = EmailMessage.from_dict(task["message"])
                    retry_count = task["retry_count"] + 1
                    message_id = f"<retry-{uuid.uuid4()}@{message.to[0].email}>"
                    result = await self.email_sender._send_one(message_id, message)
                    if result.status == SendStatus.FAILED and retry_count <= PostgreSQLRetryQueue.MAX_RETRIES:
                        await self.retry_queue.enqueue(message, retry_count)
                    # success / rate_limited 均不需重试
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"RetryWorker error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """优雅停止"""
        self._running = False


class EmailSender:
    """SMTP 邮件发送器 — 传输层，不关心邮件内容。

    变更说明（v1.1）：
    - 发送失败不再使用 asyncio.sleep() 内存重试
    - 改为投递到 PostgreSQLRetryQueue 持久化表，由 RetryWorker 后台轮询重试
    - Identity Service 进程重启不丢失待重试邮件
    """

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_address: str = "noreply@company.com",
        from_name: str = "信息技术部",
        use_tls: bool = True,
        retry_queue: Optional[PostgreSQLRetryQueue] = None,
        timeout: float = 30.0,
        max_concurrent: int = 5,              # 批量发送最大并发数，避免被 SMTP 视为垃圾流量
        max_attachment_size_mb: int = 10,     # 附件大小上限（MB），超过则拒绝发送
        pool_size: int = 5,                   # SMTP 连接池大小，预热减少 TLS 握手延迟
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_address = from_address
        self.from_name = from_name
        self.use_tls = use_tls
        self.timeout = timeout
        self.retry_queue = retry_queue  # 未传入则降级为无重试（仅一次尝试）
        self.max_attachment_size = max_attachment_size_mb * 1024 * 1024
        self._bulk_semaphore = asyncio.Semaphore(max_concurrent)
        self._pool_size = pool_size

    async def send(self, message: EmailMessage, actor_user_id: Optional[str] = None) -> SendResult:
        """发送单封邮件。发送失败后投递到持久化重试队列（如有配置）。

        Args:
            message: 待发送邮件
            actor_user_id: 操作人标识。自动发送传入 "system"，管理员手动操作传入 global_user_id。
                           None 时由 EmailSender 内部填充 "system"。
        """
        message_id = self._generate_message_id()
        start = time.monotonic()

        # 前置校验：附件大小上限
        for att in message.attachments:
            if len(att.content) > self.max_attachment_size:
                logger.warning(
                    f"Attachment {att.filename} ({len(att.content)} bytes) "
                    f"exceeds limit ({self.max_attachment_size} bytes)"
                )
                return SendResult(
                    message_id=message_id,
                    status=SendStatus.FAILED,
                    recipient=message.to[0].email,
                    error_message=f"Attachment {att.filename} exceeds size limit",
                    retry_count=0,
                )

        result = await self._send_one(message_id, message)

        # 发送失败且配置了持久化重试队列 → 入队
        if result.status == SendStatus.FAILED and self.retry_queue:
            await self.retry_queue.enqueue(message, retry_count=0)
            logger.info(f"Email {message_id} queued for retry (PostgreSQLRetryQueue)")

        elapsed = (time.monotonic() - start) * 1000
        return result

    async def send_bulk(self, messages: list[EmailMessage], actor_user_id: Optional[str] = None) -> list[SendResult]:
        """批量发送，有限并发。

        使用 Semaphore 控制并发数（默认 5），避免：
        - 被邮件服务商视为垃圾流量而限流
        - 单一大批量（如 100 封入职邮件）串行发送耗时过长
        - 同时避免 aiosmtplib 连接池被耗尽

        性能参考（SMTP RTT ≈ 200ms/封）：
        - 串行：100 封 → ~20s
        - 并发 5：100 封 → ~4s
        """
        semaphore = self._bulk_semaphore

        async def _send_with_semaphore(msg: EmailMessage) -> SendResult:
            async with semaphore:
                return await self.send(msg, actor_user_id=actor_user_id)

        return await asyncio.gather(
            *[_send_with_semaphore(m) for m in messages]
        )

    async def _send_one(self, message_id: str, message: EmailMessage) -> SendResult:
        """单次发送尝试（不含重试），使用连接池复用 SMTP 连接。"""
        try:
            mime_msg = self._build_mime(message_id, message)
            smtp = SMTP(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
                timeout=self.timeout,
                pool_size=self._pool_size,
            )
            async with smtp:
                await smtp.send_message(mime_msg)
            return SendResult(
                message_id=message_id,
                status=SendStatus.SUCCESS,
                recipient=message.to[0].email,
                retry_count=0,
                elapsed_ms=0,
            )
        except aiosmtplib.SMTPRateLimitExceeded:
            return SendResult(
                message_id=message_id,
                status=SendStatus.RATE_LIMITED,
                recipient=message.to[0].email,
                error_message="SMTP rate limited",
                retry_count=0,
            )
        except Exception as e:
            return SendResult(
                message_id=message_id,
                status=SendStatus.FAILED,
                recipient=message.to[0].email,
                error_message=str(e),
                retry_count=0,
            )

    async def health_check(self) -> bool:
        """SMTP 连通性健康检查（发送 NOOP 命令），用于监控探测。

        返回 True 表示 SMTP 服务可用，False 表示不可用。
        耗时 ≈ 1-3 秒（含 TLS 握手）。
        """
        try:
            smtp = SMTP(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls,
                timeout=10.0,          # 健康检查超时短于正常发送
            )
            async with smtp:
                await smtp.noop()
            return True
        except Exception as e:
            logger.error(f"SMTP health check failed: {e}")
            return False

    def _build_mime(self, message_id: str, message: EmailMessage) -> MIMEMultipart:
        """构建 MIME 邮件对象"""
        msg = MIMEMultipart("alternative")
        msg["Message-ID"] = message_id
        msg["From"] = f"{self.from_name} <{self.from_address}>"
        msg["To"] = ", ".join(
            f"{a.name} <{a.email}>" if a.name else a.email
            for a in message.to
        )
        msg["Subject"] = message.subject
        if message.reply_to:
            msg["Reply-To"] = (
                f"{message.reply_to.name} <{message.reply_to.email}>"
                if message.reply_to.name
                else message.reply_to.email
            )

        # 纯文本兜底
        if message.body_text:
            msg.attach(MIMEText(message.body_text, "plain", "utf-8"))
        # HTML 正文
        if message.body_html:
            msg.attach(MIMEText(message.body_html, "html", "utf-8"))

        # 附件
        for att in message.attachments:
            part = MIMEBase(*att.mime_type.split("/", 1))
            part.set_payload(att.content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{att.filename}"',
            )
            msg.attach(part)

        return msg

    def _generate_message_id(self) -> str:
        import uuid
        return f"<{uuid.uuid4()}@{self.host}>"
````

#### 10.3.3 配置入口

各系统在自己的配置文件中初始化 `EmailSender` 和重试队列：

```python
# --- Identity Service 初始化代码 ---
from app.notification.email_sender import EmailSender, PostgreSQLRetryQueue, RetryWorker
from app.core.db import async_session_factory

retry_queue = PostgreSQLRetryQueue(async_session_factory)

email_sender = EmailSender(
    host=config.notification.smtp_host,
    port=config.notification.smtp_port,
    username=config.notification.smtp_user,
    password=config.notification.smtp_password,
    from_address=config.notification.from_address,
    from_name=config.notification.from_name,
    retry_queue=retry_queue,       # 持久化重试（PostgreSQL），进程重启不丢失
)

### 后台重试 worker
retry_worker = RetryWorker(email_sender, retry_queue, poll_interval=5.0)

### 应用启动时：await retry_worker.start()
### 应用关闭时：await retry_worker.stop()
```

> **注意**：未传入 `retry_queue` 时，`EmailSender.send()` 降级为一次发送尝试（无重试），适用于测试环境。

配置与 Identity Service §10 config.yml 完全兼容，无需修改现有配置结构。

______________________________________________________________________

### 10.4 消息模板渲染器

#### 10.4.1 设计原则

- **纯函数**：不依赖外部存储，模板由调用方传入
- **多通道渲染**：同一模板 + 同一变量集，按通道输出不同格式
- **安全**：默认 HTML 转义，防止 XSS
- **简单**：底层用 Python `str.format()`，不引入 Jinja2 依赖（如需复杂逻辑，各系统自行引入）

#### 10.4.2 接口定义

```python
### app/notification/template_renderer.py

import html
import re
from typing import Any

from prometheus_client import Counter

from .types import Channel

### ---- Prometheus 指标 ----

TEMPLATE_MISSING_VAR_TOTAL = Counter(
    "notification_template_missing_var_total",
    "模板渲染时变量缺失次数（按缺失键名统计）",
    labelnames=["missing_key"],
)


class TemplateRenderer:
    """消息模板渲染器 — 变量替换 + 多通道渲染"""

    MAX_SMS_LENGTH = 140
    MAX_WECOM_LENGTH = 4096

    def render(
        self, template: str, variables: dict[str, Any], channel: Channel
    ) -> str:
        """
        渲染模板为指定通道格式。

        防御性设计：
        - 变量缺失时不抛 KeyError，使用占位符 "（未提供）" 替代
        - 记录 Warning 日志并暴露 metrics，便于运维发现模板不匹配

        Args:
            template: 模板字符串，变量用 {var_name} 标记
            variables: 变量字典
            channel: 目标通道

        Returns:
            渲染后的消息文本
        """
        # 1. 变量替换（安全模式：缺失变量用占位符替代）
        try:
            result = template.format(**variables)
        except KeyError as e:
            missing_key = str(e)
            logger.warning(
                f"Template missing variable: {missing_key}, "
                f"available: {list(variables.keys())}, "
                f"template: {template[:100]}"
            )
            TEMPLATE_MISSING_VAR_TOTAL.labels(missing_key=missing_key).inc()
            # 提取模板中所有变量名，使用安全值填充
            safe_vars = {
                k: variables.get(k, "（未提供）")
                for k in re.findall(r"\{(\w+)\}", template)
            }
            result = template.format(**safe_vars)

        # 2. 按通道处理
        if channel == Channel.EMAIL_HTML:
            return result
        elif channel == Channel.EMAIL_TEXT:
            return self._strip_html(result)
        elif channel == Channel.SMS:
            return self._truncate(result, self.MAX_SMS_LENGTH)
        elif channel in (Channel.WECOM, Channel.DINGTALK):
            return self._truncate(result, self.MAX_WECOM_LENGTH)
        else:
            return result

    def render_safe(
        self, template: str, variables: dict[str, Any], channel: Channel
    ) -> str:
        """渲染模板，自动对变量值做 HTML 转义（防止用户输入注入）"""
        safe_vars = {
            k: html.escape(str(v)) if isinstance(v, str) else v
            for k, v in variables.items()
        }
        return self.render(template, safe_vars, channel)

    @staticmethod
    def _strip_html(text: str) -> str:
        """移除 HTML 标签，生成纯文本版本"""
        clean = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        clean = re.sub(r"</p>", "\n", clean, flags=re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", "", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean)
        return clean.strip()

    @staticmethod
    def _truncate(text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
```

#### 10.4.3 使用示例

```python
from app.notification.template_renderer import TemplateRenderer
from app.notification.types import Channel

renderer = TemplateRenderer()

### 模板来自 Identity Service §10 config.yml
template = """
<p>亲爱的 {display_name}，您好：</p>
<p>您的统一账号已创建。</p>
<p>Pocket-ID 一次性设置链接：{pocketid_setup_url}</p>
"""

variables = {
    "display_name": "张三",
    "pocketid_setup_url": "https://pocketid.company.com/setup?token=abc123",
}

### 邮件 HTML 版本
html_version = renderer.render(template, variables, Channel.EMAIL_HTML)

### 邮件纯文本版本（自动 strip HTML）
text_version = renderer.render(template, variables, Channel.EMAIL_TEXT)
### → "亲爱的 张三，您好：\n\n您的统一账号已创建。\n\nPocket-ID 一次性设置链接：https://..."

### SMS 版本（截断到 140 字）
sms_version = renderer.render(template, variables, Channel.SMS)
```

______________________________________________________________________

### 10.5 与 Iapetus 的集成

#### 10.5.1 替换 §5.6 通知通道

原 §5.6 的通知发送逻辑由 ProvisioningEngine 直接调用 `smtplib`，替换为通过通知模块发送：

```python
### Iapetus 中的 ProvisioningEngine（替换后）

from app.notification.email_sender import EmailSender
from app.notification.template_renderer import TemplateRenderer, Channel
from app.notification.types import EmailMessage, EmailAddress

class ProvisioningEngine:
    def __init__(self, config, email_sender: EmailSender):
        self.config = config
        self.email_sender = email_sender
        self.renderer = TemplateRenderer()

    async def _send_onboarding_email(
        self, user: IdentityUser, token: str, temp_passwords: dict
    ) -> None:
        """发送新用户入职邮件（替代原 §5.6 中的 smtplib 直连代码）"""
        template = self.config.notification.templates.onboarding_body
        subject_tpl = self.config.notification.templates.onboarding_subject

        variables = {
            "display_name": user.display_name,
            "pocketid_setup_url": f"https://pocketid.company.com/setup?token={token}",
            "nexus_temp_password": temp_passwords.get("nexus", "（无）"),
            "zentao_temp_password": temp_passwords.get("zentao", "（无）"),
        }

        message = EmailMessage(
            to=[EmailAddress(email=user.primary_email, name=user.display_name)],
            subject=self.renderer.render(subject_tpl, variables, Channel.EMAIL_TEXT),
            body_html=self.renderer.render(template, variables, Channel.EMAIL_HTML),
            body_text=self.renderer.render(template, variables, Channel.EMAIL_TEXT),
            tags={"type": "onboarding", "user_id": user.global_user_id},
        )

        # 异步发送，不阻塞 Provisioning 流程
        asyncio.create_task(self._send_and_log(message))

    async def _send_and_log(self, message: EmailMessage) -> None:
        result = await self.email_sender.send(message)
        if result.status == SendStatus.FAILED:
            logger.error(
                f"Failed to send onboarding email to {result.recipient}: "
                f"{result.error_message}"
            )
            # 发送失败依然写入审计日志
            await audit_logger.log_operation(
                target_type="notification",
                action="email_send",
                user_id="system",
                target_id=result.recipient,
                target_name=result.recipient,
                result="failure",
                new_value={"message_id": result.message_id, "error": result.error_message},
            )
```

#### 10.5.2 配置兼容性

Identity Service §10 config.yml 的 `notification` 段**无需修改**，通知模块的 `EmailSender` 直接读取现有配置字段：

```yaml
### §10 config.yml — 保持不变
notification:
  smtp_host: "${SMTP_HOST}"
  smtp_port: 587
  smtp_user: "${SMTP_USER}"
  smtp_password: "${SMTP_PASSWORD}"
  from_address: "identity@company.com"
  templates:
    onboarding_subject: " 您的系统账号已开通"
    onboarding_body: |
      <p>亲爱的 {display_name}，您好：</p>
      <p>您的统一账号已创建。请使用以下信息登录各系统：</p>
      ...
```

#### 10.5.3 其他通知场景

除 Provisioning 入职邮件外，Iapetus 中以下场景也可复用通知模块：

| 场景 | 触发条件 | 邮件内容 |
| :------------------- | :----------------------------------- | :-------------------------------------------------- |
| 用户停用通知 | `POST /users/{id}/depart` | 告知用户账号已停用 |
| 用户重新激活 | `POST /users/{id}/reactivate` | 同入职邮件（含新 token） |
| 未映射用户提醒 | 定时任务扫 `identity_mapping` 空值 | 提醒管理员手动关联 |
| Break-Glass 激活告警 | `system.break_glass` 事件 | 告知安全管理员紧急通道已激活 |
| 分发失败告警 | Provisioning 重试耗尽 | 告知管理员某系统分发失败 |
| 密码同步失败告警 | `auth.password_sync_failed` 重试耗尽 | 告知管理员用户密码 Fan-out 双写失败，需人工介入修复 |

______________________________________________________________________

### 10.6 与其他业务系统的集成

通知服务作为 Iapetus 的核心模块，通过 API 对外暴露邮件发送能力。其他业务系统（AMDP、DDAP）不引入任何通知相关的依赖包，统一通过 HTTP 调用 Iapetus。

#### 10.6.1 通知 API

| 路由 | 方法 | 说明 |
| :----------------------------------------------- | :--- | :------------------- |
| `/identity/v1/notifications/email` | POST | 发送单封邮件 |
| `/identity/v1/notifications/email/batch` | POST | 批量发送邮件 |
| `/identity/v1/notifications/templates` | GET | 查询可用邮件模板列表 |
| `/identity/v1/notifications/status/{message_id}` | GET | 查询邮件发送状态 |

**请求示例**：

```json
POST /identity/v1/notifications/email
{
    "to": [{"email": "zhangsan@company.com", "name": "张三"}],
    "subject": "发布审核通知",
    "body_html": "<p>您的发布包已通过审核</p>",
    "tags": {"type": "release_approval", "bundle_id": "rb-001"}
}
```

**响应**：

```json
{
    "message_id": "msg-abc123@identity",
    "status": "queued",
    "recipient": "zhangsan@company.com"
}
```

#### 10.6.2 AMDP 集成

AMDP 中 `notification_service.py` 的 `_send_smtp()` 函数改为调用 Iapetus 通知 API：

```python
# --- AMDP notification_service.py（替换后）---

import httpx

IDENTITY_NOTIFY_URL = "http://identity-service:8000/identity/v1/notifications/email"

async def _send_smtp(to: str, subject: str, body: str) -> None:
    """通过 Iapetus 统一通知 API 发送邮件"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            IDENTITY_NOTIFY_URL,
            json={
                "to": [{"email": to}],
                "subject": subject,
                "body_html": body,
                "tags": {"source": "amdp", "type": "internal_notification"},
            },
            timeout=10.0,
        )
        resp.raise_for_status()
```

**优势**：AMDP 不再维护 SMTP 配置（host/port/user/password），全部由 Iapetus 集中管理，配置变更只需改一处。

#### 10.6.3 DDAP 集成

DDAP 同理，调用同一 API，传入自有 tags 标识来源即可。

#### 10.6.4 架构总览

```
┌─────────────────────────────────────────────────┐
│                 Identity Service                │
│  ┌──────────────────┐ ┌──────────────────────┐  │
│  │  EmailSender     │ │  TemplateRenderer    │  │
│  │  (SMTP 传输层)    │ │  (变量替换+多通道)    │  │
│  └────────┬─────────┘ └──────────┬───────────┘  │
│           │                      │              │
│  ┌────────┴──────────────────────┴───────────┐  │
│  │  /identity/v1/notifications/*  (HTTP API)  │  │
│  └──────────────────┬────────────────────────┘  │
└─────────────────────┼───────────────────────────┘
                      │  HTTP
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │  AMDP   │  │  DDAP    │  │  其他系统  │
   │         │  │          │  │          │
   │ 站内通知  │  │ 站内通知  │  │ 站内通知  │
   │（自建）  │  │（自建）   │  │（自建）   │
   └─────────┘  └──────────┘  └──────────┘
```

______________________________________________________________________

### 10.7 方案A/B适配

通知服务是基础设施横切关注点，与 identity_module 的身份管理职责不在同一抽象层。判断标准：

- 通知功能去掉 SMTP 配置，identity_module 核心 CRUD 是否受影响？**不受影响**。
- 通知与被通知的业务事件（制品发布、系统告警）是否属于身份管理领域？**不属于**——这是跨领域的横切基础设施。

因此，方案A与方案B采取不同的集成策略：

| 维度 | 方案A（独立 Identity Service） | 方案B（嵌入式 identity_module） |
| :----------- | :------------------------------------------------------ | :---------------------------------------------------------------------- |
| 通知代码位置 | `identity_service/app/notification/` | **独立包** `notification-kit/`，与 identity_module 平级，互不依赖 |
| 集成方式 | Identity Service 内置，Iapetus 启动时初始化 | 业务系统（AMDP）在 `app/main.py` 中导入并初始化，不经过 identity_module |
| 对外 API | `POST /identity/v1/notifications/email` | **无** — identity_module 不暴露任何通知路由 |
| SMTP 配置 | Identity Service config.yml 统一管理 | 业务系统自有配置（如 AMDP 的 `settings.SMTP_*`） |
| 发送方式 | Iapetus 内部 `from app.notification import EmailSender` | 业务系统 `from notification_kit import EmailSender` |
| 依赖关系 | aiosmtplib 为 Iapetus 主依赖 | aiosmtplib 为 notification-kit 可选依赖，业务系统按需安装 |

**方案B 不将通知纳入 identity_module 的设计理由**：

1. **单一职责**：identity_module 仅关注身份管理（用户/部门/认证/Provisioning），通知是独立的横向基础设施
1. **零耦合**：identity_module 内部没有任何邮件发送或消息通知逻辑——所有 "email" 字段均为用户数据属性（primary_email），所有 "notification" 引用均为审计分类标签
1. **可复用**：notification-kit 作为独立 pip 包，可被任意业务系统引用，不强制绑定在 identity_module 上
1. **可选依赖**：业务系统不需要通知能力时，不安装 notification-kit 也不影响 identity_module 正常工作
1. **架构对齐**：符合 AGENTS.md §7.4 的降级原则——去掉通知不影响身份管理核心链路

______________________________________________________________________

### 10.8 监控与可观测性

#### 10.8.1 Prometheus 指标

| 指标名 | 类型 | 说明 |
| :----------------------------------------------------- | :-------- | :--------------------------------------- |
| `notification_email_total{status, tag}` | Counter | 邮件发送总数（按状态和自定义标签） |
| `notification_email_latency_ms{quantile}` | Histogram | 邮件发送延迟（含重试） |
| `notification_email_retry_total` | Counter | 重试总次数 |
| `notification_email_rate_limited_total` | Counter | 被 SMTP 限流次数 |
| `notification_template_missing_var_total{missing_key}` | Counter | 模板渲染时变量缺失次数（按缺失键名统计） |

#### 10.8.2 结构化日志

每次发送记录一条结构化日志：

```json
{
    "event": "email_sent",
    "message_id": "<uuid@host>",
    "recipient": "zhangsan@company.com",
    "subject_hash": "sha256:abc123",
    "status": "success",
    "retry_count": 0,
    "elapsed_ms": 234.5,
    "tags": {"type": "onboarding", "user_id": "01JQ..."}
}
```

______________________________________________________________________

### 10.9 与审计日志的联动

邮件发送事件纳入审计日志体系（参见 §9.2.3 审计事件统一结构）：

| event_type | 说明 | actor_user_id 规则 |
| :-------------------------------- | :------------------------- | :---------------------------------------------------------------------------------------- |
| `notification.email_send` | 邮件发送成功 | 自动发送（Provisioning/定时任务）→ `"system"`；管理员手动操作 → 操作人的 `global_user_id` |
| `notification.email_failed` | 邮件发送失败（含重试耗尽） | 同上 |
| `notification.email_rate_limited` | 被 SMTP 限流 | 同上 |

`EmailSender.send()` 新增可选参数 `actor_user_id`（v1.6），由调用方根据场景传入：

```python
### 场景一：自动发送（Provisioning 流程）
await email_sender.send(message)  # actor_user_id 默认为 "system"

### 场景二：管理员手动操作（如重发通知）
await email_sender.send(message, actor_user_id="u-2a3b4c5d")

### 在 EmailSender.send() 内部，发送完成后调用审计日志
await audit_logger.log(AuditEvent(
    event_type=f"notification.email_{result.status.value}",
    category="system",
    actor_user_id=actor_user_id or "system",
    target_type="email",
    target_id=result.recipient,
    target_name=result.recipient,
    action="send",
    result=result.status.value,
    detail={
        "message_id": result.message_id,
        "retry_count": result.retry_count,
        "elapsed_ms": result.elapsed_ms,
        "subject": message.subject[:100],  # 截断，避免日志过长
        "tags": message.tags,
    },
))
```

______________________________________________________________________

### 10.10 实施路线图

> 通知模块为 Iapetus 内置组件，与 Iapetus 主体代码同步开发交付。

| 步骤 | 内容 | 交付物 |
| :--------------------------- | :------------------------------------------------------------------------- | :------------------------- |
| **1. 模块开发** | 通知模块核心代码：`EmailSender` + `TemplateRenderer` + 类型定义 + 单元测试 | `app/notification/` 目录 |
| **2. Identity Service 集成** | 替换 §5.6 中的 SMTP 直连代码，改为调用 `app.notification` | ProvisioningEngine 更新 |
| **3. 通知 API 开发** | 实现 `/identity/v1/notifications/*` 端点，供 AMDP/DDAP 调用 | API 路由 + Pydantic schema |
| **4. 监控对接** | Prometheus 指标暴露 + 审计日志联动 | 可观测性就绪 |

以上四步随 Iapetus 主体开发节奏推进。

______________________________________________________________________

### 10.11 总结

本章描述方案A（独立 Identity Service / Iapetus）的通知架构，将 SMTP 邮件能力从 Provisioning 流程中解耦，系统化为 Iapetus 内置模块。核心设计原则：

- **方案A专属**：§10.2-§10.6 的通知模块代码（`app/notification/`）仅适用于方案A，通知作为 Iapetus 的一等模块，编译在 Identity Service 内
- **统一入口**：Provisioning、权限告警、审计告警等子模块统一通过 `app.notification` 发送
- **对外 API**：业务系统（AMDP、DDAP）通过 `/identity/v1/notifications/*` 调用，无需引入任何通知依赖
- **方案B分离**：方案B（嵌入式 identity_module）不含通知服务代码，业务系统通过独立的 `notification-kit` 包按需集成 SMTP 能力（详见 §10.7 方案A/B适配）
- **可观测**：内置 Prometheus 指标 + 结构化日志 + §9 审计日志联动（方案A/B通用）

§10.8-§10.9 的监控指标和审计联动设计对两个方案通用。

## 11. 双模式认证（OIDC + LDAP）

> 本章整合自§11（双模式认证）v2.5，是该方案的**精简版本**。
> 完整实现细节（AuthProvider 抽象、Traefik 完整配置、Saga Worker 代码）参见原文档。

### 11.1 设计动机

v4.8 架构仅支持 Pocket-ID 单一 OIDC 认证源，存在两个关键局限：

| 问题 | 影响 |
| :--------------------------------- | :---------------------------------------- |
| **认证源单点故障** | Pocket-ID 宕机 → 所有用户无法登录任何系统 |
| **Zentao/Nexus 社区版不支持 OIDC** | 必须单独维护本地账号，无法统一 SSO |

解决方案：引入 LLDAP 作为第二认证源，覆盖 Zentao/Nexus 的 LDAP 认证需求。Pocket-ID 继续服务 GitLab/Jenkins/SonarQube 的 OIDC 认证。

### 11.2 网络层分流架构（Traefik L4/L7）

核心设计原则：**认证路由下沉到网络层，Iapetus 不参与认证协议执行**。

```
          OIDC 系统（L7 HTTP）                 LDAP 系统（L4 TCP）
    GitLab/Jenkins/SonarQube/DDAP          Zentao/Nexus
    回调: https://idp.company.com          直连: ldap://idp.company.com:389
              │                                       │
              ▼                                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    Traefik 网络路由层                          │
│                                                              │
│  L7 HTTP Router                   L4 TCP Router              │
│  Host(`idp.example.com`)         EntryPoint: ldap (:389)     │
│  → Pocket-ID upstream            → LLDAP upstream            │
│  (不解包 HTTP body)               (不解包 TCP，转发原始包)     │
└──────────────────────────────────────────────────────────────┘
              │                                       │
              ▼                                       ▼
        ┌──────────┐                          ┌──────────┐
        │ Pocket-ID │                          │  LLDAP   │
        │ (OIDC)    │                          │ (LDAP)   │
        └──────────┘                          └──────────┘
```

**关键设计收益**：

- Zentao 配置 `ldap://idp.company.com:389` 直连，完全感知不到中间路由，零代码改造
- Traefik 在 L4 TCP 层**不解包应用协议**，仅转发原始 TCP 包
- Iapetus 不参与任何认证协议执行，认证由 Pocket-ID 和 LLDAP 各自独立完成

### 11.3 Traefik 配置

```yaml
# traefik/static/entrypoints.yml
entryPoints:
  websecure:
    address: ":443"
  ldap:
    address: ":389"   # L4 TCP entrypoint
```

```yaml
# traefik/dynamic/ldap-tcp.yml
tcp:
  routers:
    ldap-router:
      entryPoints: ["ldap"]
      rule: "HostSNI(`*`)"
      service: "lldap-backend"

  services:
    lldap-backend:
      loadBalancer:
        servers:
          - address: "lldap:3890"
```

### 11.4 按需 Provisioning

LLDAP 定位为**下游分发目标**（与 GitLab/Jenkins 同级），而非全局认证源。用户**不**全量推送到 LLDAP：

```
新建用户时：
  1. 始终推送到 Pocket-ID（OIDC 是主认证源）
  2. 按需推送到 LLDAP：仅当用户被分配了需要 LDAP 的系统访问权限时
     （通过 _user_needs_ldap_provisioning 判定）
```

```python
async def _user_needs_ldap_provisioning(self, user) -> bool:
    """判定用户是否需要推送到 LLDAP"""
    assigned_systems = await self._get_user_assigned_systems(user.global_user_id)
    ldap_systems = await self.config_service.get_ldap_systems()  # ['zentao', 'nexus']
    return any(s in ldap_systems for s in assigned_systems)
```

**收益**：

- 消除 Passkey 用户无密码可同步到 LDAP 的问题（不需要 LDAP 的用户不会进入 LLDAP）
- 避免 LLDAP 中产生大量无用账户

### 11.5 密码管理 Fan-out + Saga 补偿

Iapetus 是唯一的**修改密码中枢**。用户统一修改密码后，Fan-out 双写到 Pocket-ID 和 LLDAP：

```text
密码修改流程:
  1. 用户 → Identity Service 前端：输入旧密码 + 新密码
  2. Identity Service 后端：验证旧密码
  3. PocketIdProvisioner.update_password(user_id, new_password)  → 明文，Pocket-ID 自行哈希
  4. LldapProvisioner.update_password(user_id, new_password)     → passlib 重新哈希为 SSHA
  5. 全部成功 → 返回成功
  6. 部分失败 → Saga 补偿
```

**Saga 补偿策略**：

| 场景 | 用户侧表现 | 后台处理 |
| :------- | :------------- | :------------------------------------------------------------------------- |
| 全部失败 | 返回错误 | 无需补偿 |
| 部分失败 | 显示"修改成功" | 投递到 `identity_password_retry` 队列表，指数退避重试（5s→30s→2m→10m→30m） |

重试耗尽后：发送告警通知 + 锁定账号 + 创建人工修复工单。

**密码哈希适配**：Pocket-ID（Argon2）和 LLDAP（SSHA）的哈希算法不同，`LldapProvisioner.update_password` 内部使用 `passlib` 重新哈希，**不可直接透传** Pocket-ID 的哈希值。

#### 11.5.1 LLDAP 密码验证（v5.6 新增）

> 为支持 iapetus-app 独立登录的双通道认证，`LldapAuthProvider` 新增 `verify_password()` 方法。

```python
class LldapAuthProvider:
    """LLDAP 认证提供者 — 实现 LLDAP 用户密码验证（v5.6 新增）。"""

    async def verify_password(self, uid: str, password: str) -> bool:
        """通过 LLDAP /auth/simple/login REST API 验证用户密码。
        返回 True 表示密码正确，False 表示验证失败或 LLDAP 不可达。
        用于 iapetus-app 登录流程中 IdentityUser.password_hash 为空时的降级验证。
        """
        ...

    async def get_user_info(self, uid: str) -> dict | None:
        """获取 LLDAP 用户信息（已有方法）。"""
        ...

    async def health_check(self) -> bool:
        """LLDAP 健康检查（已有方法）。"""
        ...
```

**验证流程**：`POST /identity/v1/auth/login` → 查 `IdentityUser` → `password_hash` 非空时 bcrypt 本地验证 → `password_hash` 为空时调用 `LldapAuthProvider.verify_password()` 通过 LLDAP API 验证 → 均失败则返回 401。

### 11.6 侧门封堵

为防止用户绕过 Iapetus 直接修改密码导致双端不一致：

| 约束 | 措施 |
| :------------------------------ | :---------------------------------------------------- |
| **禁用 Pocket-ID 自改密码** | Pocket-ID 配置中关闭"允许用户自行修改密码" |
| **LLDAP Web 界面保护** | Traefik IP 白名单 middleware，仅管理员可访问 |
| **ProvisionerAdapter 强制接口** | 鉴权类 Provisioner 必须实现 `update_password`（§5.2） |

### 11.7 认证源健康监控

```text
# 认证源健康检查
GET /identity/v1/auth/health
Response: {
  "oidc": true,
  "ldap": true,
  "frontend_error_rate": 0       -- 最近 5 分钟前端错误数（AMDP P3.4 对齐）
}
```

Prometheus 指标：

| 指标 | 说明 |
| :------------------------------------- | :----------------------------------------------------- |
| `auth_provider_health{provider}` | 认证源健康状态（1=健康，0=异常） |
| `auth_resolve_total{provider, result}` | 身份映射请求总数 |
| `frontend_error_total{error_type}` | 前端错误上报总数（error/unhandledrejection/vue-error） |

### 11.8 系统认证方式映射

| 系统 | 认证方式 | 认证路径 |
| :-------- | :------- | :-------------------------------------- |
| GitLab CE | OIDC | 跳转 Pocket-ID（Traefik L7） |
| Jenkins | OIDC | 跳转 Pocket-ID（Traefik L7） |
| SonarQube | OIDC | 跳转 Pocket-ID（Traefik L7） |
| DDAP | OIDC | 跳转 Pocket-ID（Traefik L7） |
| AMDP | OIDC | 跳转 Pocket-ID（Traefik L7） |
| Zentao CE | LDAP | ldap://idp:389 → Traefik L4 TCP → LLDAP |
| Nexus CE | LDAP | ldap://idp:389 → Traefik L4 TCP → LLDAP |

### 11.9 API 变更

| API | 说明 |
| :------------------------------------------ | :-------------------------- |
| `GET /identity/v1/auth/health` | 认证源健康检查 |
| `POST /identity/v1/auth/config/switch` | 切换全局认证模式（管理员） |
| `PATCH /identity/v1/auth/config/system-map` | 更新系统-认证映射（管理员） |
| `GET /identity/v1/resolve?sub=xxx` | OIDC 登录后身份映射 |
| `GET /identity/v1/resolve?uid=xxx` | LDAP 登录后身份映射 |

#### 11.9.1 iapetus-app 独立登录认证（v5.6 新增）

> 为支持 iapetus-app 独立壳的部署场景，identity_module 新增自包含 JWT 认证端点。
> 该机制独立于 Pocket-ID / LLDAP 的外部认证流程，仅用于 iapetus-app 前端登录。

| API | 说明 |
| :----------------------------- | :---------------------------------------------------------------------- |
| `POST /identity/v1/auth/login` | 用户名密码登录，返回 JWT（HS256，双通道验证：本地 bcrypt > LLDAP bind） |
| `POST /identity/v1/auth/token` | 滑动过期刷新 Token（每次刷新重置 8h 有效期） |
| `GET /identity/v1/auth/me` | 当前用户信息（需 Bearer Token） |

**JWT 配置**：`IdentityConfig` 新增 `jwt_secret_key`（环境变量 `IDENTITY_JWT_SECRET_KEY`）和 `jwt_expire_minutes`（默认 480 分钟）。若 `IDENTITY_JWT_SECRET_KEY` 未设置，fallback 到 AMDP 的 `SECRET_KEY`（兼容嵌入场景），独立部署时必须显式配置。

**双通道密码验证**：`IdentityUser.password_hash`（bcrypt，本地）优先于 LLDAP bind 验证。password_hash 为空且 LLDAP 已启用时才走 LLDAP 通道。两者均不可用时返回 401。

______________________________________________________________________

*完整实现细节参见 §11（双模式认证 OIDC + LDAP）。*

______________________________________________________________________

## 12. 老用户迁移方案

### 12.1 自动映射匹配链（Auto-Matching Priority）

对于老用户在不同系统有不同username的情况（Nexus的zhangs ≠ GitLab的zhangsan），identity_plugin启动时对现有`identity_mapping`做**自动匹配发现**，按优先级逐级尝试。

**各系统独立可配的匹配优先级**：每个外部系统声明自己的匹配字段优先级链，避免"一刀切"导致某个系统因缺少关键字段而全量失败。

```yaml
# config/matching_policies.yaml
matching_policies:
  gitlab:
    priority: [employee_id, email, username, full_name]
  zentao:
    priority: [email, full_name, employee_id]
  nexus:
    priority: [manual]  # 无工号/邮箱字段，必须人工关联
  sonarqube:
    priority: [email, username, manual]
  jenkins:
    priority: [email, employee_id, manual]
```

| 优先级 | 匹配依据 | 说明 | 覆盖度预期 |
| ---------- | -------------------------- | ------------------------------------------------------- | ---------------------------------- |
| **1** | 工号（`employee_id`） | 各系统profile中的员工工号字段。若一致则100%确定为同一人 | 高（有HR数据源时） |
| **2** | 邮箱（`email`） | 跨系统邮箱一致。企业邮箱唯一性强 | 高（大部分系统有邮箱字段） |
| **3** | 用户名（`username`） | 如果两个系统username相同，大概率是同一人 | 中（但问题就在于不同名才需要映射） |
| **4** | 中文姓名（`display_name`） | 同名不同人的概率低，命中后自动建议待人工确认 | 低（边缘场景） |
| **manual** | 人工关联（管理员手动操作） | 无可用字段时强制人工干预 | — |

命中策略：匹配到第一条即停止，不再继续尝试后续优先级。命中后自动创建`identity_mapping`记录，`mapping_status=VERIFIED`。

**第4优先级（中文姓名）特殊处理**：命中后`mapping_status=AUTO_SUGGESTED`（建议状态）而非`VERIFIED`，标记在UI"未映射清单"中供管理员确认，确认后升级为`VERIFIED`。

**四优先级链全部未命中**（或系统配置为 `manual`） → 写入`identity_user_pending`（pending_type='mapping_pending'）并：

- 后台站内信/邮件通知管理员（"张三的GitLab账号无法自动匹配，请手动关联"）
- 管理员在Web UI"未映射清单"中按系统筛选、搜索用户名、逐条手动关联
- 手动关联结果记入`identity_sync_event_log`（含操作人admin_id + 时间戳 + 变更前映射值 + 变更后映射值）
- 支持映射回滚：管理界面"映射变更历史"可查看某用户在所有时间点的映射快照，确认误匹配后可一键回滚到旧版本

**映射表版本管理**：

- `identity_mapping` 增加 `effective_from` / `effective_to` 时间戳字段
- 每次变更写入新行，标记旧行 `effective_to=now()`（不原地覆盖）
- 管理界面提供"映射变更时间线"视图：可按用户查看映射历史、按时间点回滚
- 自动清理策略：保留最近24个月的历史版本

## 13. 业务系统对接方式

> AMDP 等业务系统的身份相关功能统一由 Iapetus 提供，业务系统不独立建设身份管理模块。

### 13.1 调用接口

```python
"""AMDP 通过 httpx 异步调用 Iapetus API。"""

IDENTITY_API = "http://identity-service:8002/identity/v1"

async def get_global_user_id(source_system: str, external_username: str) -> str | None:
    """从 Iapetus 获取全局用户ID，用于身份归一。

    Args:
        source_system: 来源系统名（如 nexus）。
        external_username: 该系统中的账号名。

    Returns:
        global_user_id字符串，或None（未映射/Iapetus 离线）。
    """
    try:
        resp = await AsyncClient().get(
            f"{IDENTITY_API}/resolve",
            params={"source_system": source_system,
                     "external_username": external_username},
            timeout=5.0,
        )
        if resp.status_code == 200:
            return resp.json()["global_user_id"]
    except Exception:
        pass  # Iapetus 离线 → 降级返回None
    return None


async def get_identity_chain(global_user_id: str) -> list[dict]:
    """获取某人在所有系统的账号链路。"""
    resp = await AsyncClient().get(
        f"{IDENTITY_API}/{global_user_id}/chain",
        timeout=5.0,
    )
    return resp.json()
```

### 13.2 降级策略（AMDP 不依赖 Identity Service 存活）

| Iapetus 状态 | AMDP 行为 |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **在线** | 调 API 获取 global_user_id，写入业务表 |
| **离线** | 降级：记录 `(source_system, external_username)`，标记 `identity_status=pending`，存入 local pending 表。业务逻辑跳过身份关联继续运行，不阻塞 |
| **恢复后** | 后台定时任务扫 pending 表，补调 resolve API，补写 `global_user_id`。补写完成后发通知 |

**AMDP 不硬依赖 Iapetus 进程存活**——离线时 AMDP 功能不受影响，只是身份关联延迟修复。降级决策在调用侧做。

## 14. 配置项

### 14.1 系统连接配置（独立服务的 yaml/环境变量）

> Iapetus 独立部署，运行时可使用独立 config.yaml 或环境变量注入。

```yaml
# ========================================================
# Identity Service 配置
# ========================================================

server:
  host: "0.0.0.0"
  port: 8002
  log_level: "INFO"

database:
  url: "postgresql://identity:identity_pwd@identity_db:5432/identity_db"  # pragma: allowlist secret

# Pocket-ID OIDC IdP连接
pocketid:
  url: "https://pocketid.company.com"
  admin_token: "${POCKETID_ADMIN_TOKEN}"

# 各目标系统Provisioning配置
provisioning:
  gitlab:
    url: "https://gitlab.company.com"
    admin_token: "${GITLAB_ADMIN_TOKEN}"
    enabled: true
  zentao:
    url: "https://rdm.company.com"
    admin_account: "${ZENTAO_ADMIN_ACCOUNT}"
    admin_password: "${ZENTAO_ADMIN_PASSWORD}"
    enabled: true
  sonarqube:
    url: "http://192.168.5.65:9000"
    admin_token: "${SONARQUBE_ADMIN_TOKEN}"
    enabled: true
  nexus:
    url: "http://192.168.5.64:8081"
    admin_account: "${NEXUS_ADMIN_ACCOUNT}"
    admin_password: "${NEXUS_ADMIN_PASSWORD}"
    enabled: true
  jenkins:
    url: "http://jenkins.company.com"
    admin_account: "${JENKINS_ADMIN_ACCOUNT}"
    admin_password: "${JENKINS_ADMIN_PASSWORD}"
    enabled: true

# 外部身份源配置（后续接入时启用）
# 启用任意一个外部IdP后，还需在UI中开启"外部IdP作为事实源(SSOT)"开关
#   ON  → 人员信息以外部IdP为准，Identity Service只做映射和分发
#   OFF → Iapetus 自身为事实源，外部IdP仅作为辅助数据源
ext_idp:
  ssot_enabled: false                    # 整体开关：是否将外部IdP作为单一事实源
  ssot_source: ""                        # 事实源标识：wecom/feishu/ldap（ssot_enabled=true时必填）
  wecom:
    enabled: false
    corp_id: "${WECOM_CORP_ID}"
    secret: "${WECOM_SECRET}"
    callback_token: "${WECOM_CALLBACK_TOKEN}"
  feishu:
    enabled: false
    app_id: "${FEISHU_APP_ID}"
    app_secret: "${FEISHU_APP_SECRET}"
  ldap:
    enabled: false
    server: "ldap://ldap.company.com:389"
    bind_dn: "cn=admin,dc=company,dc=com"
    bind_password: "${LDAP_BIND_PASSWORD}"
    search_base: "dc=company,dc=com"

# 缓存与重试
cache:
  ttl_seconds: 3600                     # 兜底TTL。建议配合事件驱动的主动失效：用户变更时由ProvisioningEngine广播失效事件
  max_entries: 1000
  enable_events: true                # 设为true时，用户信息变更触发缓存主动失效

retry:
  max_retries: 3
  backoff_seconds: [5, 30, 120]

# 通知
notification:
  smtp_host: "${SMTP_HOST}"
  smtp_port: 587
  smtp_user: "${SMTP_USER}"
  smtp_password: "${SMTP_PASSWORD}"
  from_address: "identity@company.com"
  templates:
    onboarding: "欢迎加入公司 — 请设置您的Passkey"
    depart: "您的系统账号已被停用"

# 监控指标（Prometheus /metrics 端点）
monitoring:
  enabled: true
  metrics_path: "/metrics"
  # 暴露指标说明：
  # provisioning_success_total{system="gitlab"}  — 各系统Provisioning成功次数
  # provisioning_failed_total{system="nexus"}     — 各系统Provisioning失败次数
  # resolve_latency_ms{quantile="0.99"}           — resolve API响应延迟P99
  # identity_user_total{status="active"}           — 活跃用户数
  # pending_mapping_unresolved                    — 未映射用户数
  # sync_event_total{source="wecom"}              — 外部IdP同步事件总数
  # last_sync_timestamp{source="ldap"}            — 最后同步时间戳
```

## 16. 模式定义（Pattern Definition）

### 16.1 模式名称

**统一身份供应模式（Unified Identity Provisioning Pattern）**

### 16.2 核心范式

```
一个身份源 + 双 IdP（OIDC 主 + LDAP 辅）+ 自动 Provisioning + 降级兼容
                              ↑
                        人定义意图 → AI/系统生成实现 → 人验证结果
```

> **降级兼容**：LLDAP 作为 OIDC 的降级兜底，覆盖 Zentao/Nexus 等不支持 OIDC 的老系统（见 §11 双模式认证）。

### 16.3 模式四要素

| 要素 | 定义 | 实例 |
| -------------------- | ---------------------------------------------------------------------------------------- | -------------------- |
| **身份源** | 单一权威数据源（SSOT），所有用户信息的增删改查都在此发生 | `identity_user` 表 |
| **OIDC IdP（主）** | 主认证源，OIDC 协议 + Passkey/WebAuthn 无密码认证，覆盖**全量用户** | Pocket-ID |
| **LDAP IdP（辅）** | 补充认证源，LDAP 协议，仅覆盖**需 Zentao/Nexus 权限的用户**（按需 Provisioning，见 §11） | LLDAP |
| **Provisioning引擎** | 按策略向多个目标系统（含两个 IdP）自动分发用户/部门创建请求 | `ProvisioningEngine` |

> **双 IdP 分工**：Pocket-ID 是主认证源（全量推送），LLDAP 是补充——仅当用户被分配了需要 LDAP 的系统权限时才推送到 LLDAP。Traefik 在网络层按协议分流：OIDC → Pocket-ID，LDAP → LLDAP。详细设计见 §11 双模式认证。

### 16.4 适用范围

| 适用 | 不适用 |
| ------------------------------------------ | ----------------------------------- |
| 多系统共用的身份管理场景 | 单一系统独立运行，无跨系统身份需求 |
| 管理员需要集中管理员工生命周期的场景 | 纯日志/监控/告警系统，无用户交互 |
| 合规审计要求跨系统身份统一追溯的场景 | 公共互联网应用，用户自主注册 |
| 员工入职/离职/调动需要在多个系统同步的场景 | 第三方SaaS系统自身已提供完整IdP集成 |

### 16.5 架构原则（Architecture Principles）

> 以下原则为该项目所有模块的开发规范，任何功能扩展必须遵循。参考 Keycloak IdentityProviderMapper（插件化翻译器）和 Casdoor Syncer（适配器模式）设计。

**原则一：适配器模式（Adapter Pattern）——所有外部系统集成必须通过适配器接口**

无论是出站方向（Iapetus → 目标系统）还是入站方向（外部 IdP → Iapetus），都遵循同一规范：定义一个统一接口，每种外部系统实现一个适配器，核心引擎只依赖接口。

| 方向 | 接口 | 实现示例 | 定义位置 |
| ------------ | -------------------- | ----------------------------------------- | -------- |
| 出站（分发） | `ProvisionerAdapter` | `GitLabProvisioner`, `JenkinsProvisioner` | §19 |
| 入站（同步） | `IdPSyncAdapter` | `WeComAdapter`, `DingTalkAdapter` | §20 |

**原则二：插件化架构（Plugin Architecture）——每种外部系统对应一个独立插件**

适配器即插件。新增一种外部系统 = 新增一个适配器类，不修改核心引擎、不修改已有适配器。

```python
# 核心原则：对扩展开放，对修改封闭
# 新增飞书 IdP：
class FeishuAdapter(IdPSyncAdapter): ...  # 只需写这个文件
# SyncEngine 一行代码不动
```

**原则三：对称设计（Symmetric Design）——入站和出站使用样式一致的接口体系**

两个方向的设计哲学一致（统一接口 + 插件化），但接口不同、方向不同、职责不同，不能混用。

| | 入站（IdP Sync Adapter） | 出站（Provisioner Adapter） |
| -------- | -------------------------------------- | ------------------------------------- |
| 数据流向 | 外部IdP → Identity Service | Iapetus → 目标系统 |
| 触发时机 | 定时/事件驱动 | 管理员操作/自动策略 |
| 接口方法 | `fetch_users()`, `fetch_departments()` | `create_user()`, `suspend_user()` |
| 典型实现 | WeComAdapter, DingTalkAdapter | GitLabProvisioner, JenkinsProvisioner |

______________________________________________________________________

## 17. 适用性判断树（Applicability Decision Tree）

新系统接入前，按此决策流程判断是否需要套用该模式：

```
新系统是否涉及用户/账号？
  ├── NO  → 不需要此模式（e.g. 纯日志系统、ETL管道）
  │
  └── YES → 是否有多个外部系统需要登录？
        ├── NO → 使用本地认证即可（e.g. 单机工具、本地GUI）
        │
        └── YES → 是否需要跨系统身份统一？
              ├── NO → 只用Pocket-ID OIDC，跳过Provisioning
              │       （e.g. 内部Wiki自建账号，不需要与研发系统打通）
              │
              ├── 部分需要 → L2 身份归一（接入resolve API）
              │             （e.g. 监控系统只查看不操作，不需Persona）
              │             L2 限定：不接入 Provisioning 反向通知（§18.3 user_created/
              │             mapping_updated/user_departed），身份映射为只读查询，
              │             变更由管理员在 Iapetus 控制台手工触发。
              │
              └── YES → 完全适用此模式（标准实施）
                    ├── 期望管理员一次建人 → L3 完整Provisioning
                    │                         L3 完整接入：resolve + chain + Provisioning
                    │                         反向通知 + 事件推送。系统接收 user_created/
                    │                         mapping_updated/user_departed 事件后自行更新本地缓存。
                    └── 用户自行注册 → L1 SSO即可
```

**决策输出**：

```json
{
  "pattern": "unified_identity_provisioning",
  "level": "L3",
  "rationale": "新研发效能平台，5个外部系统需统一登录，管理员有集中建人需求"
}
```

______________________________________________________________________

## 18. 标准化API契约（Standardized API Contract）

> 此契约定义了**任何新系统接入identity_plugin时必须遵循的接口规范**。语言/框架无关。

### 18.1 身份解析（必需）

```
GET /identity/v1/resolve

参数：
  source_system     string    必需  来源系统标识（如 nexus）
  external_username string    必需  该系统中的账号名

成功响应 200：
{
  "global_user_id":    "uuid-xxx",       // 全局用户ID
  "previous_aliases":  ["zhangs", "zs001"], // 历史曾用名
  "profile": {
    "username":     "zhangsan",          // 统一用户名
    "display_name": "张三",
    "email":        "zhangsan@company.com",
    "employee_id":  "EMP001",
    "dept":         "财政研发中心"
  },
  "mapping_status": "VERIFIED"           // VERIFIED | PROVISIONED | MANUAL
}

未命中 404：
{
  "error": "identity_not_found",
  "source_system": "nexus",
  "external_username": "zhangs"
}

降级超时 503 + Local Pending：
无需等待 → 系统记录(source_system, external_username, timestamp)
          → 本地标记 identity_status = "pending"
          → 业务继续运行，不阻塞
```

### 18.2 身份链查询（可选）

```
GET /identity/{global_user_id}/chain

成功响应 200：
{
  "global_user_id": "uuid-xxx",
  "display_name": "张三",
  "mappings": [
    { "source_system": "gitlab",    "external_username": "zhangsan", "mapping_status": "VERIFIED" },
    { "source_system": "nexus",     "external_username": "zhangs",   "mapping_status": "MANUAL" },
    { "source_system": "zentao",    "external_username": "zs001",    "mapping_status": "MANUAL" },
    { "source_system": "pocketid",  "external_username": "zhangsan", "mapping_status": "PROVISIONED" }
  ]
}
```

### 18.3 身份同步推送（写操作——Provisioning反向通知）

当identity_plugin创建了新用户或更新了映射关系，需通知已注册的系统：

```json
// POST /identity/v1/events (由identity_plugin主动推送)
{
  "event_type": "user_created",          // user_created | mapping_updated | user_departed
  "global_user_id": "uuid-xxx",
  "profile": {
    "username": "zhangsan",
    "display_name": "张三",
    "email": "zhangsan@company.com",
    "dept_code": "RD01"
  },
  "timestamp": "2026-06-24T12:00:00Z"
}
```

### 18.4 语言无关的接入Demo

```python
# Python版
async def resolve_user(source_system, username):
    resp = await httpx.get(f"{IDENTITY_URL}/identity/resolve",
                           params={"source_system": source_system,
                                   "external_username": username},
                           timeout=5.0)
    if resp.status_code == 200:
        return resp.json()["global_user_id"]
    return None  # 降级

# Java版
String resolveUser(String sourceSystem, String username) {
    // 等效逻辑，调用相同REST接口
}
```

______________________________________________________________________

## 19. Provisioner适配器接口规范（Adapter Interface Specification）

> 任何目标系统要接入统一Provisioning，必须按此接口实现一个适配器。语言无关。

### 19.1 创建用户（必需）

```
create_user(request) → response

request:
{
  "username":       "zhangsan",     // 统一登录名
  "display_name":   "张三",
  "email":          "zhangsan@company.com",
  "password":       "temp123!!",    // pragma: allowlist secret
  "groups":         ["财政研发中心"], // 所属组/部门列表
  "global_user_id": "uuid-xxx"      // 可选，用于关联OIDC身份
}

response:
{
  "status":     "created",          // created | existing(幂等) | error
  "user_id":    "45",               // 目标系统内部的用户ID
  "user_url":   "https://gitlab.company.com/zhangsan"  // 可选，用户页面链接
}

幂等要求：同username重复调用必须返回existing而非error。
密码策略：OIDC系统可设随机密码；非OIDC系统（Nexus/Zentao）设统一临时密码。
```

### 19.2 停用用户（必需）

```
suspend_user(user_id) → response

response:
{
  "status":   "suspended"    // suspended | not_found
}

要求：保留数据不物理删除，仅禁止登录。
```

### 19.3 创建组/部门（可选）

```
create_group(group) → response

request:
{
  "group_code": "RD01",
  "group_name": "财政研发中心",
  "parent_group_code": "RDC"       // 可选，上级组编码
}

response:
{
  "status":   "created",           // created | existing | not_supported
  "group_id": "88"
}

不支持组的系统直接返回 status="not_supported"。
```

### 19.4 适配器注册表

每个适配器需在配置中声明能力：

```yaml
# config.yaml 适配器声明
adapter_gitlab:
  type: provisioner
  system: gitlab
  capabilities:         # 声明能力清单
    create_user:    true
    suspend_user:   true
    create_group:   true
    require_email:  true         # GitLab要求email必填
    max_username_len: 50        # 限制用户名最大长度

adapter_nexus:
  type: provisioner
  system: nexus
  capabilities:
    create_user:    true
    suspend_user:   true
    create_group:   false       # Nexus无组概念
    require_email:  false
```

ProvisioningEngine根据capabilities自动判断能否推送，不需要硬编码。

______________________________________________________________________

## 20. 外部IdP同步适配器接口（IdP Sync Adapter）

> 参考 Keycloak 的 IdentityProviderMapper（插件化翻译器）和 Casdoor 的 Syncer（适配器模式）设计。
> 为 Phase 3 外部 IdP 同步定义统一适配器接口，每种外部 IdP（企微/钉钉/飞书/LDAP/HR系统）实现一个适配器。

### 20.1 核心接口

```python
# 统一的 IdP 同步适配器接口
class IdPSyncAdapter(ABC):
    @abstractmethod
    def fetch_users(self) -> List[ExternalUser]:
        \"\"\"从外部 IdP 拉取用户列表。返回统一的 ExternalUser 格式。\"\"\"

    @abstractmethod
    def fetch_departments(self) -> List[ExternalDept]:
        \"\"\"从外部 IdP 拉取部门列表。返回统一的 ExternalDept 格式。\"\"\"

    @abstractmethod
    def fetch_changes_since(self, since: datetime) -> SyncDiff:
        \"\"\"增量拉取变更（增量同步时使用）。返回新增/修改/删除的差异集。\"\"\"

    @abstractmethod
    def test_connection(self) -> bool:
        \"\"\"测试与外部 IdP 的连通性。用于配置验证。\"\"\"

# 统一数据格式
class ExternalUser:
    ext_user_id: str       # 外部系统用户唯一标识（企微userid/钉钉userId/飞书open_id）
    username: str | None   # 外部系统用户名（可选，企微有/钉钉无）
    display_name: str      # 中文姓名
    email: str | None
    phone: str | None
    dept_ids: List[str]    # 外部系统部门ID列表（企微支持多部门）
    employee_id: str | None # 工号

class ExternalDept:
    ext_dept_id: str       # 外部系统部门ID
    name: str              # 部门名称
    parent_id: str | None  # 上级部门ID
```

### 20.2 适配器实现示例

```python
# 企微适配器示例
class WeComAdapter(IdPSyncAdapter):
    def __init__(self, config: WeComConfig):
        self.client = WeComClient(corp_id=config.corp_id,
                                  agent_id=config.agent_id,
                                  secret=config.secret)

    def fetch_users(self) -> List[ExternalUser]:
        raw_users = self.client.user.list(department_id=1, fetch_child=True)
        return [
            ExternalUser(
                ext_user_id=u["userid"],
                username=u.get("name"),       # 企微有 name 字段
                display_name=u["name"],
                email=u.get("email"),
                phone=u.get("mobile"),
                dept_ids=u.get("department", []),
                employee_id=None
            )
            for u in raw_users
        ]

# 钉钉适配器示例
class DingTalkAdapter(IdPSyncAdapter):
    def fetch_users(self) -> List[ExternalUser]:
        raw_users = self.client.user.list()
        return [
            ExternalUser(
                ext_user_id=u["userid"],
                username=None,                # 钉钉无用户名概念
                display_name=u["name"],
                email=u.get("email"),
                phone=u.get("mobile"),
                dept_ids=[u.get("dept_id")],
                employee_id=u.get("job_number")
            )
            for u in raw_users
        ]
```

### 20.3 核心同步引擎

```python
class SyncEngine:
    \"\"\"依赖 IdPSyncAdapter 接口，不关心背后是企微还是钉钉。\"\"\"
    def __init__(self, adapter: IdPSyncAdapter, identity_service: IdentityService):
        self.adapter = adapter
        self.service = identity_service

    def full_sync(self) -> SyncReport:
        \"\"\"全量同步：拉取外部 IdP 全量数据 → 与 identity_user 比对 → 创建/更新/停用\"\"\"
        ext_users = self.adapter.fetch_users()
        ext_depts = self.adapter.fetch_departments()
        # ... 统一比对逻辑，不关心 IdP 类型

    def incremental_sync(self) -> SyncReport:
        \"\"\"增量同步：拉取外部 IdP 变更集 → 增量更新\"\"\"
        changes = self.adapter.fetch_changes_since(self.last_sync_time)
        # ... 增量处理逻辑
```

### 20.4 设计价值

| 原则 | 体现 |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **开闭原则** | 新增 IdP（如飞书/OKTA）只需新增一个 adapter 类，核心引擎零修改 |
| **隔离复杂性** | 每个 adapter 封装特定 IdP 的 API 差异（企微的"部门"vs 钉钉的"组织"vs 飞书的"部门群组"） |
| **可测试性** | 每个 adapter 可独立 Mock 测试 |
| **对称设计** | 与 §19 Provisioner Adapter（出站方向）形成完整对称：入站（IdP→Identity Service）用 IdPSyncAdapter，出站（Identity Service→目标系统）用 ProvisionerAdapter |

### 20.5 与已有设计的映射

| 已有设计 | 对应关系 |
| ------------------------------- | --------------------------------- |
| §19 Provisioner Adapter（出站） | Iapetus → GitLab/Zentao 等系统 |
| §20 IdP Sync Adapter（入站） | 企微/钉钉/飞书 → Identity Service |
| §14 SSOT 配置 (`ssot_source`) | 指定激活哪个 adapter |
| §3.11 sync_event_log | 记录每个 adapter 的同步事件 |

> 注意区分：§23 和 §24 是两个完全独立的适配器体系，前者解决"向下分发"，后者解决"向上同步"。接口不同、方向不同、职责不同，不应混用。

## 21. 成熟度模型（Maturity Model）

> 新系统不必一步到位。按此分级渐进落地。

### 21.1 分级定义

| 级别 | 名称 | 做了什么 | DDAP参考 | 新系统工作量 |
| ------ | ---------------- | -------------------------------------------------- | ------------------------- | ---------------- |
| **L0** | 无身份统一 | 各系统独立认证，无关联 | 现状 | 0 |
| **L1** | OIDC SSO | 系统接入Pocket-ID，用户用Passkey单次登录 | GitLab/SonarQube OIDC配置 | ~1天 |
| **L2** | 身份归一 | 接入identity resolve API，建立`global_user_id`映射 | AMDP身份追踪 | ~2天 |
| **L3** | 自动Provisioning | 管理员一次建人，按策略自动推送到所有勾选系统 | Identity Service | ~5天（含适配器） |

### 21.2 升级路径

```
L0（现状）
  │ ① 部署Pocket-ID + 配置OIDC客户端
  ▼
L1（SSO，消除密码输入）
  │ ② 接入resolve API + 建立identity_mapping
  ▼
L2（身份归一，人机可追溯）
  │ ③ 写适配器 + 注册到ProvisioningEngine
  ▼
L3（自动Provisioning，完全自动化）
```

### 21.3 每个级别的验收标准

| 级别 | 验收标准 |
| ------ | -------------------------------------------------------------------------------------------------------------------------- |
| **L1** | ① 用户可用Passkey登录该系统 [OK] ② 登录后跳回原系统正常 [OK] ③ 登出后清除session [OK] |
| **L2** | ① 系统调用resolve API能返回global_user_id [OK] ② 未映射用户能降级不报错 [OK] ③ 管理员可在UI手动建立映射 [OK] |
| **L3** | ① 在identity_plugin建人→目标系统自动出现该用户 [OK] ② 停用用户 → 目标系统禁止登录 [OK] ③ 重试3次失败→日志留痕人工介入 [OK] |

______________________________________________________________________

## 22. 设计原则（设计规范总结）

| 原则 | 说明 | 贯彻方式 |
| ---------------- | -------------------------------------------------- | ------------------------------------------------------ |
| **UUID唯一标识** | `global_user_id`即用户表PK，所有外部FK直接指向 | 无代理键，无INT→UUID转换层 |
| **关联解耦** | FK指向物理PK（`global_user_id`），不用业务code | identity_mapping用global_user_id关联 |
| **SCD Type 2** | 人员-部门归属变化可追溯 | identity_user_department的is_current+effective_from/to |
| **软删除** | 停用不物理删除 | identity_user.is_active=FALSE，mapping_status=EXPIRED |
| **审计字段** | 所有表继承created_at/updated_at | 追踪数据变更时间 |
| **命名风格统一** | source_system / external_username / mapping_status | 跨系统一致 |
| **幂等性** | 重复调用create_user不报错 | provisioner返回existing状态 |
| **JSONB兜底** | 不确定的扩展属性存JSONB | extended_attrs约定namespace |

> Identity Service独立部署后，不再受DDAP数据库规范约束。上述原则是自身的设计契约。

## 23. 风险与缓解

| 风险 | 影响 | 缓解措施 |
| ----------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Nexus/Zentao无外部认证** | 永远需要本地密码 | Provisioning创建时设临时密码，OIDC系统无需密码 |
| **Zentao session认证不稳定** | API需先登录获session | 实现session池+自动刷新+重试 |
| **各系统API版本差异** | 参数不兼容 | Provisioner按版本适配，config中可指定版本 |
| **DDAP离线导致新员工无法provision** | 无法建人 | Identity Service独立运行不受DDAP影响，管理员可直接调Identity Service API（`POST /identity/v1/users`）建人；或使用独立CLI工具`identity-cli create-user`（后续提供） |
| **Passkey设备兼容性** | 老设备不支持WebAuthn | Pocket-ID一次性登录码兜底 |
| **老用户映射工作量大** | 200人手动映射耗时 | 先自动匹配一致username（预计覆盖70%），余下批量CSV导入 |
| **自动匹配误判（同名不同人）** | 中文姓名匹配（第4优先级）可能误匹配 | 第4优先级命中后自动建议待人工确认，不作为最终结果；在UI"未映射清单"中标注"建议匹配"而非自动写入 |

______________________________________________________________________

## 24. 管理控制台界面说明

> **AMDP 声明**：AMDP 系统不再独立开发身份管理相关前端页面（用户管理、部门管理、映射管理、SSOT 配置、分发日志等）。以上功能统一由 Iapetus 管理控制台提供，AMDP 仅通过 §13 定义的 API 调用 Identity Service 获取身份数据。
>
> 本章面向 **UI 开发者与功能验证者**，定义 Iapetus 管理控制台的功能模块划分、导航结构、关键页面的内容与操作流程。
> 不定义具体 CSS/组件库（留给前端框架决策），只定义"有什么、怎么操作、数据从哪来"。

### 24.1 功能模块总览

#### 导航菜单结构

```
后台管理首页
│
├── 身份管理（管理员）
│   ├── 用户管理        → 用户列表 / 新建用户 / 批量导入
│   ├── 部门管理        → 部门树 / 新建部门 / 人员转部门
│   ├── 标签管理        → 标签列表 / 新建标签
│   └── 映射管理        → 映射列表 / 手动映射 / 未映射清单
│
├── 分发配置（管理员）
│   ├── 策略模板        → 角色模板列表 / 新建模板
│   ├── 分发日志        → 日志查询 / 失败重试
│   └── 目标系统状态    → 各系统连接状态 / 健康检查
│
├── 审计与监控（管理员）
│   ├── 操作审计        → 所有变更操作的时间线
│   ├── 同步事件        → 外部IdP同步事件记录
│   └── 错误监控        → 前端 JS 异常收集与诊断（POST 匿名上报 + 去重 + 堆栈追踪）
│
└── 系统设置（超级管理员）
    ├── 基本设置        → 服务名称 / 通知通道配置
    ├── SSOT配置        → 事实源选择 / 外部IdP对接
    ├── API密钥管理     → Admin Token / Read Token
    └── 缓存管理        → 缓存状态 / 手动失效
```

#### 功能入口汇总

| 功能 | 入口 | 调用API | 依赖条件 |
| ----------------- | ---------------------------- | ----------------------------------------------- | ----------------------- |
| 新建用户 | 用户管理→新建 | POST /identity/v1/users | 已配置策略模板 |
| 停用用户 | 用户管理→搜索→操作 | POST /identity/v1/users/{id}/depart | 无 |
| 重新激活 | 用户管理→搜索已离职→操作 | PATCH /identity/v1/users/{id} | 用户已离职 |
| 批量转部门 | 部门管理→选择部门→转移成员 | POST /identity/v1/depts/{code}/transfer-members | 目标部门已存在 |
| 手动映射 | 映射管理→新建映射 | POST /identity/v1/mappings | 用户已在identity_user中 |
| 重试分发 | 分发日志→筛选失败→重试 | POST /identity/v1/provisioning-logs/{id}/retry | 无 |
| 查看错误 | 错误监控→查看详情 | GET /identity/v1/frontend-errors | admin+ |
| 全量同步（方案B） | Master端→同步管理→全量导出 | GET /identity/v1/sync/full | 仅Master角色可见 |
| SSOT切换 | 系统设置→SSOT配置→选择事实源 | 更新 ext_idp.ssot_enabled | 已配置对应外部IdP连接 |

### 24.2 关键页面说明

#### 页面1：新建用户

| 区域 | 内容 | 字段来源 | 必填 |
| -------- | ----------------------------------------------------------------------------------------------------- | ---------------------------- | ----------------- |
| 基本信息 | 登录名 / 显示名 / 邮箱 / 手机 | identity_user | 登录名+显示名必填 |
| 组织信息 | 部门选择（部门树下拉） / 工号 / 职位 / 员工类型 | identity_department | 部门必填 |
| 角色选择 | 策略模板单选（默认选中is_default模板） | identity_provisioning_policy | 必选 |
| 覆盖设置 | 勾选覆盖目标系统（如dev_engineer默认推Jenkins→去掉勾选） | 基于模板 | 可选 |
| SSOT模式 | 若ssot_enabled=true→用户信息从外部IdP同步→新建页面**不可用**→显示提示"事实源为企微，请在企微添加人员" | ext_idp.ssot_enabled | — |

**操作流程**：

```
填写表单 → 选择部门 → 选角色 → 可选覆盖 → 提交
  → API返回global_user_id和provisioning_result
  → 页面跳转到用户详情页，显示各系统推送状态
  → 非OIDC系统(Nexus/Zentao)的临时密码 → 系统自动通过通知通道发送
```

#### 页面2：用户详情

| 卡片 | 内容 |
| ---------- | -------------------------------------------- |
| 用户资料 | identity_user所有字段（只读），编辑按钮 |
| 部门归属 | 当前部门 + 历史归属时间线（SCD2记录列表） |
| 跨系统映射 | 列表：系统 |
| 分发状态 | 各系统推送状态 + 最后操作时间 + 失败原因 |
| 操作按钮 | 编辑 / 停用 / 重新激活 / 重试推送 / 追加系统 |

#### 页面3：映射管理

**未映射清单**——这是老用户迁移期间的核心工作台：

| 列 | 说明 |
| ------------ | ------------------------------------------ |
| 系统 | 来源系统 |
| 用户名 | 该系统的原始账号名 |
| 邮箱 | 匹配建议依据 |
| 自动匹配结果 | 命中优先级的建议映射（如：工号匹配到张三） |
| 操作 | 确认 / 跳过 / 手动指定global_user_id |

**搜索过滤**：按系统(source_system)、按状态(VERIFIED/PROVISIONED/MANUAL/EXPIRED)、按用户名模糊搜索。

**批量操作**：勾选多条 → "确认匹配" / "导出未映射CSV"。

#### 页面4：SSOT配置页

> 此页面的设计直接体现 §2.2 的 SSOT选择 概念。

| 配置项 | 控件类型 | 说明 |
| -------- | -------------------------------------- | ------------------------------------ |
| 启用SSOT | 开关 (ON/OFF) | 对应 `ext_idp.ssot_enabled` |
| 事实源 | 单选：企业微信/钉钉/飞书/HR系统/LDAP | 对应 `ext_idp.ssot_source`，ON时必选 |
| 连接状态 | 状态指示器（绿色/红色 + 最后同步时间） | 调用外部IdP API健康检查 |
| 同步配置 | 同步间隔（分钟）/ 首次全量同步按钮 | 仅MQ模式需要 |

**切换提示**：切换SSOT来源时弹窗确认——"切换后，用户数据将从新来源覆盖已有数据。已有global_user_id不变，仅更新字段值。确认？"

#### 页面5：分发日志

| 过滤条件 | 说明 |
| -------- | -------------------------------------------------------- |
| 按用户 | 输入global_user_id或用户名搜索 |
| 按系统 | 下拉选择：gitlab/zentao/sonarqube/nexus/jenkins/pocketid |
| 按状态 | 多选：pending/success/failed/permanent_failed |
| 按时间 | 日期范围选择器 |

**日志列表列定义**：

| 列 | 排序 | 说明 |
| -------- | ---- | --------------------------------------- |
| 时间 | [OK] | created_at |
| 用户 | — | 显示名 + 用户名 |
| 系统 | [OK] | 目标系统图标+名称 |
| 操作 | — | create_user/suspend_user/depart_user 等 |
| 状态 | [OK] | 带颜色的状态标签 |
| 重试次数 | — | 3/3（失败时高亮） |
| 操作 | — | "重试"按钮（仅failed状态可点） |

**错误码聚合卡片**（页面顶部，AMDP P3.4 对齐）：

| 卡片 | 统计口径 | 说明 |
| ---------------- | ------------------------------- | -------------------------- |
| network_timeout | `error_code='network_timeout'` | 目标系统网络不可达 |
| api_rate_limit | `error_code='api_rate_limit'` | 触发 API 限流 |
| auth_failed | `error_code='auth_failed'` | Admin Token 过期或权限不足 |
| invalid_response | `error_code='invalid_response'` | 目标系统返回非预期格式 |

______________________________________________________________________

## 25. 前端架构（iapetus-frontend & iam-kit）

> **定位**：本章定义 Iapetus 前端技术架构，与 §24"管理控制台界面说明"的产品级描述互补——§24 定义"有什么"，本章定义"怎么实现"。

### 25.1 架构概览

本节遵循 §0 方案A（独立Identity Service）的部署模型，Iapetus 前端支持两种交付形态：

```
                        @company/iam-kit
                   (私有 NPM 包，单一事实源)
                  ┌────────────────────────────┐
                  │  theme.ts     ← 统一主题    │
                  │  api/         ← 接口封装    │
                  │  stores/      ← Pinia       │
                  │  components/  ← Vue 组件    │
                  └───────┬────────────────────┘
                          │ npm install
          ┌───────────────┼───────────────┐
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────┐
│  AMDP frontend       │     │  Iapetus 独立壳          │
│  (嵌入式消费)         │     │  (独立交付)              │
│                      │     │                         │
│  在 AMDP 布局中挂载   │     │  自有 layout + router    │
│  /admin/iam/* 路由    │     │  独立域名部署            │
│  复用 AMDP 菜单框架   │     │  面向外部客户            │
└─────────────────────┘     └─────────────────────────┘
```

**设计原则**：

| 原则 | 说明 |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 单一事实源 | 所有身份管理 UI 代码只在 `iam-kit` 中维护，两消费方零重复 |
| 依赖注入 | 组件不创建 axios 实例，由消费方注入已配置 Token 拦截器的 http-client |
| 主题穿透 | 通过 Naive UI CSS 变量 + theme-overrides 实现消费方品牌色自动适配 |
| 路由隔离 | 组件暴露路由数组，消费方以嵌套子路由方式挂载，不污染全局路由 |
| 虚拟滚动 | 所有可能超过 200 条数据的 `n-data-table` 与 `n-tree` 必须开启 `virtual-scroll`（UserTable / DeptTree / ProvisioningLog / AuditLogViewer / MappingPanel） |
| 逻辑抽离 | 单个 `.vue` 文件 `<script setup>` 严禁超过 400 行；复杂业务状态机抽离至 `composables/` 目录 |
| 样式覆盖 | 修改主题必须通过 `iam-kit/theme.ts` 的 `theme-overrides`，严禁 `:deep()` 强行覆盖 Naive UI 内置 class |

### 25.2 技术栈

| 层级 | 选型 | 版本 | 理由 |
| -------- | ----------------------- | ---- | -------------------------- |
| 框架 | Vue 3 (Composition API) | 3.4+ | 与 AMDP 统一 |
| 构建 | Vite (Library Mode) | 5.x | 打包为 NPM 包 |
| 语言 | TypeScript | 5.3+ | 类型安全，API 契约可校验 |
| UI 库 | Naive UI | 2.x | 项目宪法约定，Tree-shaking |
| 状态管理 | Pinia | 2.1+ | 与 AMDP 统一 |
| HTTP | axios | 1.6+ | 拦截器注入 Token |
| 包管理 | pnpm | 9.x | Monorepo workspace 支持 |

### 25.3 项目目录结构

#### 25.3.1 iam-kit（共享包）

```
iam-kit/
├── src/
│   ├── theme.ts                    # Naive UI theme-overrides（统一主题配置）
│   │
│   ├── api/                        # /identity/v1/* 接口封装
│   │   ├── client.ts               # axios 实例工厂（接收 httpClient 注入）
│   │   ├── inject.ts               # provide/inject 工具（注入 IAM 客户端）
│   │   ├── users.ts                # GET/POST/PATCH /identity/v1/users
│   │   ├── departments.ts          # GET/POST/PATCH /identity/v1/depts
│   │   ├── roles.ts                # GET/POST/DELETE /identity/v1/roles
│   │   ├── permissions.ts          # GET/POST/DELETE /identity/v1/permissions
│   │   ├── audit.ts                # GET /identity/v1/audit/logs
│   │   ├── auth.ts                 # POST /identity/v1/auth/login, /token, /me
│   │   ├── mappings.ts             # GET/POST/DELETE /identity/v1/mappings
│   │   ├── provisioning.ts         # GET/POST /identity/v1/provision
│   │   └── types.ts                # API 请求/响应 TypeScript 类型定义
│   │
│   ├── stores/                     # Pinia 状态管理
│   │   ├── index.ts                # 统一导出（useUserStore, useDeptStore, ...）
│   │   ├── userStore.ts            # useUserStore（用户列表/详情/CRUD）
│   │   ├── deptStore.ts            # useDeptStore（部门树/CRUD）
│   │   ├── roleStore.ts            # useRoleStore（角色/权限管理）
│   │   ├── permissionStore.ts      # usePermissionStore（权限列表）
│   │   ├── auditStore.ts           # useAuditStore（审计日志查询）
│   │   ├── mappingStore.ts         # useMappingStore（映射列表/手动映射）
│   │   ├── provisioningStore.ts    # useProvisioningStore（分发日志/重试）
│   │   ├── tagStore.ts             # useTagStore（标签列表/CRUD）
│   │   └── systemStore.ts          # useSystemStore（系统设置/缓存/API Key）
│   │
│   ├── composables/                # 通用逻辑抽离（<script setup> 严禁超过 400 行）
│   │   ├── useIdentityApi.ts       # 封装 IAM API 调用的通用 composable
│   │   ├── useAuditLogger.ts       # 审计日志前端上报工具
│   │   ├── useUserActions.ts       # 用户批量操作（停用/激活/转部门/重试分发）
│   │   ├── useDeptTree.ts          # 部门树交互（展开/收起/拖拽/搜索过滤）
│   │   ├── useMappingLogic.ts      # 自动匹配建议/手动关联/批量确认
│   │   ├── useProvisioningRetry.ts # 分发失败重试/批量重试/错误摘要
│   │   ├── useAuditQuery.ts        # 审计日志分页/筛选/排序/导出
│   │   └── useVirtualScroll.ts     # Naive UI virtual-scroll 约束工具（>200 条自动开启）
│   │
│   ├── components/                 # 可复用 Vue 组件
│   │   ├── UserTable.vue           # 用户列表（搜索/筛选/分页/批量操作）
│   │   ├── UserForm.vue            # 新建/编辑用户弹窗
│   │   ├── UserDetail.vue          # 用户详情（资料/部门/映射/分发状态）
│   │   ├── DeptTree.vue            # 部门树（展开/收起/拖拽转部门）
│   │   ├── DeptForm.vue            # 新建/编辑部门弹窗
│   │   ├── RoleManage.vue          # 角色管理（RBAC 角色 CRUD）
│   │   ├── PermissionManage.vue    # 权限管理（权限列表/分配）
│   │   ├── AuditLogViewer.vue      # 审计日志查看器
│   │   ├── AuthProvider.vue        # 认证上下文包装器（provide IAM client）
│   │   ├── PasswordChangePanel.vue # 密码修改面板
│   │   ├── PermissionGuard.vue     # 权限守卫（路由级权限控制）
│   │   ├── TagManage.vue           # 标签管理（列表/新建）
│   │   ├── MappingPanel.vue        # 映射管理面板
│   │   ├── PolicyTemplate.vue      # 策略模板（列表/新建/编辑）
│   │   ├── ProvisioningLog.vue     # 分发日志列表
│   │   ├── TargetSystemStatus.vue  # 目标系统连接状态/健康检查
│   │   ├── SyncEventLog.vue        # 外部 IdP 同步事件记录
│   │   ├── ErrorMonitor.vue        # 前端错误监控面板
│   │   ├── SsoTConfig.vue          # SSOT 配置页
│   │   ├── ApiKeyManage.vue        # API 密钥管理
│   │   └── CacheManage.vue         # 缓存状态/手动失效
│   │
│   ├── pages/                      # 业务页面级组件（v5.7 新增）
│   │   ├── UserManagePage.vue      # 用户管理页面（UserTable + UserForm 聚合）
│   │   ├── DeptManagePage.vue      # 部门管理页面（DeptTree + DeptForm 聚合）
│   │   ├── RolePermissionPage.vue  # 角色权限页面（RoleManage + PermissionManage 聚合）
│   │   └── AuditLogPage.vue        # 审计日志页面（AuditLogViewer 聚合）
│   │
│   ├── router.ts                   # iamRoutes 预置路由
│   └── index.ts                    # 统一导出入口
│
├── package.json                    # name: "@company/iam-kit"
├── vite.config.ts                  # Library Mode 配置
└── tsconfig.json
```

**Vite Library Mode 配置**：

```typescript
// iam-kit/vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'IamKit',
      fileName: (format) => `iam-kit.${format}.js`,
      formats: ['es', 'cjs'],
    },
    rollupOptions: {
      // 关键：消费方提供，不打包进组件
      external: ['vue', 'pinia', 'axios', 'naive-ui', 'vue-router', '@vueuse/core'],
      output: {
        globals: {
          vue: 'Vue',
          'naive-ui': 'NaiveUI',
          pinia: 'Pinia',
        },
      },
    },
  },
})
```

**统一导出入口（v5.7 更新：全部已实现）**：

```typescript
// iam-kit/src/index.ts
// 主题
export { iamThemeOverrides } from './theme'

// API 客户端
export { createIamClient, injectIamClient, useIamClient } from './api/client'
export type * from './api/types'

// API 模块类型
export type { AuthApi } from './api/auth'
export type { UsersApi } from './api/users'
export type { DepartmentsApi } from './api/departments'
export type { RolesApi } from './api/roles'
export type { PermissionsApi } from './api/permissions'
export type { AuditApi } from './api/audit'

// Stores
export { useUserStore } from './stores/userStore'
export { useDeptStore } from './stores/deptStore'
export { useRoleStore } from './stores/roleStore'
export { usePermissionStore } from './stores/permissionStore'
export { useAuditStore } from './stores/auditStore'
export { useMappingStore } from './stores/mappingStore'
export { useProvisioningStore } from './stores/provisioningStore'
export { useTagStore } from './stores/tagStore'
export { useSystemStore } from './stores/systemStore'

// Components
export { default as UserTable } from './components/UserTable.vue'
export { default as UserForm } from './components/UserForm.vue'
export { default as DeptTree } from './components/DeptTree.vue'
export { default as DeptForm } from './components/DeptForm.vue'
export { default as RoleManage } from './components/RoleManage.vue'
export { default as PermissionManage } from './components/PermissionManage.vue'
export { default as AuditLogViewer } from './components/AuditLogViewer.vue'
export { default as AuthProvider } from './components/AuthProvider.vue'
export { default as PasswordChangePanel } from './components/PasswordChangePanel.vue'
export { default as PermissionGuard } from './components/PermissionGuard.vue'
export { default as UserDetail } from './components/UserDetail.vue'
export { default as TagManage } from './components/TagManage.vue'
export { default as MappingPanel } from './components/MappingPanel.vue'
export { default as PolicyTemplate } from './components/PolicyTemplate.vue'
export { default as ProvisioningLog } from './components/ProvisioningLog.vue'
export { default as TargetSystemStatus } from './components/TargetSystemStatus.vue'
export { default as SyncEventLog } from './components/SyncEventLog.vue'
export { default as ErrorMonitor } from './components/ErrorMonitor.vue'
export { default as SsoTConfig } from './components/SsoTConfig.vue'
export { default as ApiKeyManage } from './components/ApiKeyManage.vue'
export { default as CacheManage } from './components/CacheManage.vue'

// Pages（v5.7 新增）
export { default as UserManagePage } from './pages/UserManagePage.vue'
export { default as DeptManagePage } from './pages/DeptManagePage.vue'
export { default as RolePermissionPage } from './pages/RolePermissionPage.vue'
export { default as AuditLogPage } from './pages/AuditLogPage.vue'

// Composables
export { useAuditLogger, resetAuditLogger } from './composables/useAuditLogger'
export { useIdentityApi } from './composables/useIdentityApi'

// 路由（消费方以嵌套方式挂载）
export { iamRoutes } from './router'
```

#### 25.3.2 Iapetus 独立壳

```
iapetus-app/
├── src/
│   ├── main.ts                    # 独立入口（挂载 Naive UI + iam-kit stores）
│   ├── App.vue                    # 根组件
│   ├── layouts/
│   │   └── AdminLayout.vue        # 独立壳布局（顶栏 + 侧边栏 + 内容区）
│   ├── router/
│   │   └── index.ts               # 独立路由（嵌套挂载 iamRoutes）
│   ├── utils/
│   │   ├── request.ts             # axios 实例（JWT 拦截器）
│   │   └── auth.ts                # 登录/登出/Token 管理
│   └── views/
│       ├── LoginPage.vue          # 登录页
│       └── DashboardPage.vue      # 首页/概览
│
├── package.json
├── vite.config.ts
├── tsconfig.json
└── index.html
```

#### 25.3.3 整体仓库位置

```
amdp/                               ← Monorepo 根
├── packages/
│   ├── iam-kit/                    ← @company/iam-kit 源码（发布到私有 NPM）
│   └── iapetus-app/                ← Iapetus 独立壳 SPA
├── frontend/                       ← AMDP 前端（消费 iam-kit）
├── app/                            ← 后端（Identity Service / AMDP 业务）
└── docs/                           ← 设计文档
```

### 25.4 消费方集成方式

#### 25.4.1 AMDP 集成（嵌入式消费）

**步骤 1：安装**

```bash
cd frontend
npm install @company/iam-kit
```

**步骤 2：路由挂载（嵌套子路由）**

```typescript
// frontend/src/router/index.ts
import { iamRoutes } from '@company/iam-kit'

const routes = [
  // ... AMDP 现有路由
  {
    path: '/admin',
    component: () => import('@/components/AdminLayout.vue'),
    children: [
      // AMDP 自带管理页面
      { path: 'users', component: () => import('@/views/admin/UserManagePage.vue') },
      { path: 'products', component: () => import('@/views/admin/ProductManagePage.vue') },
      // ...
      // Iapetus 身份管理页面（嵌套挂载）
      {
        path: 'iam',
        children: iamRoutes.map(r => ({
          ...r,
          meta: { ...r.meta, requiresAdmin: true }
        }))
      }
    ]
  }
]
```

**步骤 3：Token 依赖注入**

```vue
<!-- frontend/src/views/admin/IamContainer.vue -->
<template>
  <n-config-provider :theme-overrides="iamThemeOverrides">
    <router-view />
  </n-config-provider>
</template>

<script setup lang="ts">
import { provide } from 'vue'
import { iamThemeOverrides } from '@company/iam-kit'
import apiClient from '@/utils/axios'

// 注入到 iam-kit 组件使用的 Pinia store 中
provide('iamHttpClient', apiClient)
</script>
```

**效果**：

- URL 完全在 AMDP 域下：`https://amdp.company.com/admin/iam/users`
- 左侧是 AMDP 的 SidebarMenu，右侧渲染 iam-kit 的 UserTable
- 与 AMDP 其他管理页面共享同一 axios 实例（Token 自动携带）

#### 25.4.2 Iapetus 独立壳集成

```typescript
// iapetus-app/src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { iamThemeOverrides, createIamClient } from '@company/iam-kit'
import router from './router'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// 创建独立的 axios 实例（OIDC JWT 拦截器）
const iamClient = createIamClient({
  baseURL: import.meta.env.VITE_API_BASE,
  getToken: () => localStorage.getItem('iam_token'),
  onUnauthorized: () => router.push('/login'),
})

app.provide('iamHttpClient', iamClient)
app.mount('#app')
```

独立壳是**完全自包含的 SPA**，不依赖 AMDP 任何代码，可直接部署到客户环境。

### 25.5 Token 传递机制

> 消费方（AMDP / 独立壳）各有一套 axios + JWT 拦截器。iam-kit 组件**不创建自己的 axios 实例**，通过 Vue `provide/inject` 接收。

```
消费方（AMDP frontend / Iapetus 独立壳）
  │
  ├── 自己的 axios 实例（Token 拦截器已配置）
  │     └── request interceptor: 自动附加 Authorization header
  │     └── response interceptor: 401 → 跳转登录
  │
  └── provide('iamHttpClient', myAxiosInstance)
        │
        ▼
iam-kit 组件内部
  └── inject('iamHttpClient') → 调用 /identity/v1/* API
       → Token 由消费方管理，组件零感知
```

**设计理由**：

| 问题 | 错误做法 | 正确做法 |
| ------------ | ------------------------------ | ---------------------------------------------------- |
| Token 获取 | 组件内读取 localStorage | 消费方通过 provide/inject 注入已配置好拦截器的 axios |
| 登录态失效 | 组件内 `router.push('/login')` | 依赖注入时注册 `onUnauthorized` 回调 |
| API Base URL | 组件内写死 | 由消费方创建 axios 实例时配置 |

### 25.6 路由隔离机制

iam-kit 不使用独立的 `vue-router` 实例，而是**导出一个路由配置数组**：

```typescript
// iam-kit/src/router.ts
import type { RouteRecordRaw } from 'vue-router'

export const iamRoutes: RouteRecordRaw[] = [
  {
    path: 'users',
    name: 'IAM-Users',
    component: () => import('./components/UserTable.vue'),
    meta: { title: '用户管理' },
  },
  {
    path: 'users/new',
    name: 'IAM-UserNew',
    component: () => import('./components/UserForm.vue'),
    meta: { title: '新建用户' },
  },
  {
    path: 'users/:id',
    name: 'IAM-UserDetail',
    component: () => import('./components/UserDetail.vue'),
    meta: { title: '用户详情' },
  },
  {
    path: 'departments',
    name: 'IAM-Departments',
    component: () => import('./components/DeptTree.vue'),
    meta: { title: '部门管理' },
  },
  {
    path: 'departments/new',
    name: 'IAM-DeptNew',
    component: () => import('./components/DeptForm.vue'),
    meta: { title: '新建部门' },
  },
  {
    path: 'tags',
    name: 'IAM-Tags',
    component: () => import('./components/TagManage.vue'),
    meta: { title: '标签管理' },
  },
  {
    path: 'mappings',
    name: 'IAM-Mappings',
    component: () => import('./components/MappingPanel.vue'),
    meta: { title: '映射管理' },
  },
  {
    path: 'policies',
    name: 'IAM-Policies',
    component: () => import('./components/PolicyTemplate.vue'),
    meta: { title: '策略模板' },
  },
  {
    path: 'provisioning-logs',
    name: 'IAM-ProvisioningLogs',
    component: () => import('./components/ProvisioningLog.vue'),
    meta: { title: '分发日志' },
  },
  {
    path: 'target-status',
    name: 'IAM-TargetStatus',
    component: () => import('./components/TargetSystemStatus.vue'),
    meta: { title: '目标系统状态' },
  },
  {
    path: 'roles',
    name: 'IAM-Roles',
    component: () => import('./components/RoleManage.vue'),
    meta: { title: '角色管理' },
  },
  {
    path: 'permissions',
    name: 'IAM-Permissions',
    component: () => import('./components/PermissionManage.vue'),
    meta: { title: '权限管理' },
  },
  {
    path: 'audit',
    name: 'IAM-Audit',
    component: () => import('./components/AuditLogViewer.vue'),
    meta: { title: '操作审计' },
  },
  {
    path: 'sync-events',
    name: 'IAM-SyncEvents',
    component: () => import('./components/SyncEventLog.vue'),
    meta: { title: '同步事件' },
  },
  {
    path: 'errors',
    name: 'IAM-Errors',
    component: () => import('./components/ErrorMonitor.vue'),
    meta: { title: '错误监控' },
  },
  {
    path: 'ssot-config',
    name: 'IAM-SsoTConfig',
    component: () => import('./components/SsoTConfig.vue'),
    meta: { title: 'SSOT 配置' },
  },
  {
    path: 'api-keys',
    name: 'IAM-ApiKeys',
    component: () => import('./components/ApiKeyManage.vue'),
    meta: { title: 'API 密钥管理' },
  },
  {
    path: 'cache',
    name: 'IAM-Cache',
    component: () => import('./components/CacheManage.vue'),
    meta: { title: '缓存管理' },
  },
]
```

所有路由名使用 `IAM-` 前缀，消费方挂载时加上父路径前缀：

- AMDP: `/admin/iam/users`、`/admin/iam/departments`
- 独立壳: `/users`、`/departments`

### 25.7 Naive UI 主题统一方案

> **目标**：AMDP、Iapetus 独立壳、DDAP（后续）视觉风格一致，修改主题只需改 `iam-kit/theme.ts` 一处。

#### 25.7.1 主题配置文件

```typescript
// iam-kit/src/theme.ts
import type { GlobalThemeOverrides } from 'naive-ui'

export const iamThemeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#4C6EF5',
    primaryColorHover: '#3B5BDB',
    primaryColorPressed: '#2B4ACB',
    borderRadius: '4px',
    fontSize: '14px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  Button: {
    borderRadiusMedium: '4px',
  },
  DataTable: {
    borderRadius: '4px',
  },
}
```

#### 25.7.2 消费方使用方式

各消费方在应用入口 `<n-config-provider>` 中加载：

```vue
<!-- 消费方的 App.vue -->
<template>
  <n-config-provider :theme-overrides="iamThemeOverrides">
    <router-view />
  </n-config-provider>
</template>

<script setup>
import { iamThemeOverrides } from '@company/iam-kit'
</script>
```

#### 25.7.3 主题扩展机制

消费方可在 `iamThemeOverrides` 之上叠加自己的覆盖：

```typescript
import { merge } from 'lodash-es'
import { iamThemeOverrides } from '@company/iam-kit'

const appThemeOverrides = merge({}, iamThemeOverrides, {
  common: {
    primaryColor: '#E8590C', // 消费方自有品牌色
  },
})
```

### 25.8 AMDP 现有 CSS 重构策略

> **背景**：AMDP frontend 当前采用自定义 CSS，未使用任何 UI 库。为对齐宪法约定的 Naive UI 规范，需进行渐进式重构。

#### 25.8.1 分步计划

| 阶段 | 任务 | 影响范围 | 阻塞关系 |
| ---- | ----------------------------------------------------------------- | ----------------------------- | ------------------------------ |
| P0 | `npm install naive-ui`，验证构建通过 | `package.json` | 无 |
| P1 | 建立 `iam-kit` 包，发布 `theme.ts` 初版 | 新文件 | 无，可与 P0 并行 |
| P2 | 重构基础组件：按钮 `.btn-primary` → `<n-button>` | LoginPage、弹窗、表单提交按钮 | 页面少，先跑通流程 |
| P3 | 重构表单类页面：UserManagePage、ProductManagePage、DeptManagePage | ~6 个页面 | 复杂度较高，需积累 P2 经验 |
| P4 | 重构复杂组件：DataTable → Naive UI `n-data-table` | 所有列表页 | 影响面最大 |
| P5 | 重构布局与导航：SidebarMenu、MainLayout | 全局 | 依赖 Naive UI Layout/Menu 组件 |
| P6 | 删除自研组件：DataTable.vue、Modal、StatusBadge 等 | 清理 | 依赖 P2-P5 完成 |

#### 25.8.2 新旧组件对照

| AMDP 自研组件 | 替换为 | 备注 |
| -------------------------------- | ----------------------------- | ----------------------------------- |
| `<button class="btn-primary">` | `<n-button type="primary">` | 一次性全局替换 |
| `<button class="btn-secondary">` | `<n-button>` | |
| `<input class="search-input">` | `<n-input>` | |
| `<select class="status-select">` | `<n-select>` | |
| `<DataTable>` | `<n-data-table>` | 排序/筛选/分页开箱即用 |
| 自研 Modal | `<n-modal>` + `<n-form>` | 表单校验规则定义在 `n-form-item` 上 |
| `<StatusBadge>` | `<n-tag>` | 用 theme-overrides 统一颜色 |
| `<Toast>` | `useMessage()` (Discrete API) | 非组件式调用 |
| `<ConfirmDialog>` | `useDialog()` (Discrete API) | 非组件式调用 |

#### 25.8.3 迁移原则

1. **每页独立 PR**：先局部验证，不阻塞其他页面开发
1. **功能等价优先**：先保证行为不变，再调 visual polish
1. **theme-overrides 优先**：样式差异用 theme-overrides 解决，严禁 `:deep()` 强行覆盖 Naive UI 内置 class
1. **路由级 `n-config-provider`**：AMDP 自有页面和 iam-kit 页面使用同一份 theme-overrides

### 25.9 本地开发与调试

#### 25.9.1 iam-kit 独立开发

```bash
# 在 packages/iam-kit 目录
pnpm dev          # Vite Library Mode watch
pnpm build        # 构建 NPM 包
pnpm publish      # 发布到私有 NPM（Verdaccio）
```

#### 25.9.2 yalc 联调（iam-kit ↔ 消费方）

> 避免反复 `npm publish` 的低效迭代。

```bash
# iam-kit 侧
cd packages/iam-kit
pnpm build
yalc publish

# AMDP 侧
cd frontend
yalc add @company/iam-kit
pnpm dev    # HMR 保留

# 独立壳侧
cd packages/iapetus-app
yalc add @company/iam-kit
pnpm dev
```

修改 iam-kit 源码 → `pnpm build` → yalc push → 消费方自动刷新。

### 25.10 交付产物

| 产物 | 构建命令 | 输出 | 部署方式 |
| ------------------ | --------------------------- | -------------------------- | ---------------------- |
| `@company/iam-kit` | `pnpm build` (Library Mode) | `.js` + `.d.ts` | 私有 NPM (Verdaccio) |
| Iapetus 独立壳 | `pnpm build` (App Mode) | `dist/` 静态文件 | Nginx/Traefik 静态服务 |
| AMDP (含 iam-kit) | `npm run build` | `dist/`（含 iam-kit 组件） | 与现有 AMDP 部署一致 |

______________________________________________________________________

## 26. AI 辅助功能（LLM Enhancement）

> **定位**：大模型是增强插件，不是核心依赖。即使 LLM 完全不可用，Iapetus 的核心业务（身份管理 / Provisioning / SSO）必须零影响。
>
> 本章遵循 [AGENTS.md §7 AI/LLM 调用红线](../AGENTS.md#7-aillm-%E8%B0%83%E7%94%A8%E7%BA%A2%E7%BA%BF) 的全部约束，所有功能点均通过 §7.4 适用性三问过滤。

### 26.1 适用性判断（三问过滤）

根据 AGENTS.md §7.4，引入 LLM 前必须自问：

| 问题 | 含义 |
| ---------------------------------------- | ---------------------------------- |
| Q1: LLM 不可用时，用户能否完成核心任务？ | 功能是否在核心链路之外 |
| Q2: 降级行为是否比"没有这个功能"好？ | 降级后是否有可接受的替代路径 |
| Q3: 是否可以用规则引擎（if-else）替代？ | LLM 是否带来规则引擎无法实现的价值 |

任一回答"否"即禁止引入 LLM。

**已过滤掉的功能**（不通过三问）：

| 功能 | 驳回理由 |
| --------------------- | -------------------------------------- |
| 角色/策略模板自动推荐 | 部门统计规则即可替代（Q3 不通过） |
| 通知消息个性化生成 | 模板化已足够（Q3 不通过） |
| SSOT 冲突解决建议 | SSOT 策略本身就是规则引擎（Q3 不通过） |
| 审计日志自然语言查询 | 结构化查询构建器可替代（Q3 不通过） |

### 26.2 功能一：智能跨系统身份映射建议（P1）

> **所属模块**：§12 老用户迁移 / §24 映射管理面板
> **触发方式**：管理员在映射管理面板手动点击，非自动触发

#### 26.2.1 问题

老用户迁移时，5 个系统（GitLab / Zentao / SonarQube / Nexus / Jenkins）的账号需映射到同一个 `global_user_id`。当前自动匹配链（email → 工号 → 手机 → 中文姓名）可处理精确匹配，但**跨系统的命名差异**仍需人工判断：

| 系统 | 账号名 | 中文名 | 部门 |
| ------- | --------- | ------ | ------------ |
| GitLab | zhangwei | 张伟 | 财政研发中心 |
| Zentao | wzhang | 张伟 | 财政研发中心 |
| Jenkins | zhang.wei | — | 财政研发中心 |

规则引擎无法理解 `wzhang` = `zhangwei` = `zhang.wei` 是同一人。

#### 26.2.2 AI 方案

```
输入: 未映射用户列表（跨系统的 username / email / department / display_name）
  ↓
LLM 分析: 命名规律、部门归属、邮箱前缀模式、中文名与拼音的对应关系
  ↓
输出: 匹配置信度列表
  - {global_user_id: "已存在或新建", confidence: 0.92}
  - {matched_accounts: ["gitlab:zhangwei", "zentao:wzhang", "jenkins:zhang.wei"],
     reasoning: "同部门 + 邮箱前缀一致 + 中文名相同"}
```

**置信度阈值**：

| 置信度 | 行为 |
| ----------- | --------------------------------------------- |
| >= 0.85 | 自动标记 `VERIFIED`，无需人工确认 |
| 0.60 - 0.84 | 标记 `AUTO_SUGGESTED`，显示在"建议匹配"清单中 |
| < 0.60 | 不自动建议，留在"未映射清单"供手动处理 |

#### 26.2.3 降级设计

```
LLM 可用:
  管理员点"AI 智能匹配" → LLM 分析 → 高置信度自动确认 + 低置信度建议清单

LLM 不可用:
  回退到现有优先级匹配链（email → 工号 → 手机 → 中文姓名）
  → 中文姓名匹配仍标记 AUTO_SUGGESTED
  → 管理员逐条手动确认（与现有流程一致）
```

降级后用户**仍能完成所有映射操作**，仅失去跨系统命名推理能力。

#### 26.2.4 提示词治理

> 遵循 AGENTS.md §7.1：提示词存储在 `prompt_template` 表，支持热加载和 A/B 测试。

```sql
-- 提示词模板注册
INSERT INTO prompt_template (name, version, content, is_active) VALUES
('iam_mapping_suggestion', 'v1',
 'You are an identity mapping assistant. Given user records from multiple systems,
  identify which records likely belong to the same person.

  Consider: display_name similarity, email prefix patterns, department consistency,
  Chinese name → pinyin mapping patterns.

  For each group of matched accounts, provide:
  - confidence score (0-1)
  - reasoning in Chinese (one sentence)
  - suggested action: VERIFIED (≥0.85) / SUGGEST (0.60-0.84) / SKIP (<0.60)

  Input records: {user_records_json}',
 TRUE);
```

#### 26.2.5 UI 交互

在 §24 映射管理面板的"未映射清单"顶部新增操作区：

```
┌──────────────────────────────────────────────────────────┐
│  未映射清单                        [AI 智能匹配]  [导出CSV] │
│                                                          │
│  ┌─ AI 建议（8 组匹配） ─────────────────────────────┐   │
│  │  [VERIFIED 3组]  [SUGGESTED 5组]                  │   │
│  │                                                   │   │
│  │ ▸ wzhang / zhangwei / zhang.wei → 张伟           │   │
│  │   置信度 0.92 | 同部门+邮箱前缀一致  [确认] [驳回]  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  剩余未映射: 12 条                                       │
│  ┌──────┬──────────┬──────────┬──────┬────────┐         │
│  │ 系统  │ 用户名    │ 建议映射  │ 状态  │ 操作   │         │
│  ├──────┼──────────┼──────────┼──────┼────────┤         │
│  │ ...  │          │          │      │        │         │
└──────────────────────────────────────────────────────────┘
```

> **实现要点**：上述改动为页内 UI 增强——在映射管理面板页面内新增"AI 智能匹配"按钮及建议结果卡片区，不改动导航菜单、不新增路由、不新增独立页面。后端新增 `app/ai/mapping_suggester.py` 服务模块，独立于现有 `app/services/` 层。

### 26.3 功能二：Provisioning 异常根因分析（P2）

> **所属模块**：§5 ProvisioningEngine / §24 分发日志页面
> **触发方式**：管理员在分发日志页面的错误聚合区手动点击

#### 26.3.1 问题

分发日志中某系统持续报错，管理员需翻阅多条日志手动排查根因。当前 §24 已有错误码聚合卡片（`network_timeout` / `api_rate_limit` / `auth_failed` / `invalid_response`），但无法回答"为什么"：

```
Jenkins: 最近 2 小时 15 次 auth_failed
→ 是 Token 过期？还是 Jenkins 服务宕机？
→ 为什么同一时间段 GitLab 和 SonarQube 都正常？
```

#### 26.3.2 AI 方案

```
输入: 最近 N 条 failed provisioning_log 记录（含 target_system / error_code / error_message / created_at）
  ↓
LLM 分析: 错误码时间分布、跨系统对比、错误模式识别
  ↓
输出: 根因分析摘要
  - "Jenkins 连续 15 次 auth_failed（集中在 14:00-16:00），
     同期 GitLab 和 SonarQube 所有请求正常。
     判断: 非网络问题，Jenkins Admin Token 可能已过期。
     建议: 检查 /identity/v1/system/jenkins 的健康检查结果，必要时更换 Token。"
```

#### 26.3.3 降级设计

```
LLM 可用:
  错误聚合区显示"AI 根因分析"按钮 → 点击后显示分析结果

LLM 不可用:
  错误聚合区仅显示统计卡片（现有功能）
  → 管理员根据错误码和经验手动排查
```

#### 26.3.4 UI 交互

在 §24 分发日志页面的错误码聚合卡片区域新增入口：

```
┌──────────────────────────────────────────────────────────────┐
│  错误摘要                                        [AI 根因分析] │
│                                                              │
│  ▸ network_timeout: 3 次  ▸ auth_failed: 15 次 (集中!)      │
│                                                              │
│  ┌─ AI 根因分析结果 ─────────────────────────────────────┐  │
│  │  Jenkins auth_failed 集中爆发（14:00-16:00，15次）    │  │
│  │  同期 GitLab/SonarQube 正常 → 排除网络问题            │  │
│  │  建议: 检查 Jenkins API Token 有效期                   │  │
│  │  快捷操作: [跳转 Jenkins 健康检查] [标记已知问题]       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  分发日志列表 ...                                            │
└──────────────────────────────────────────────────────────────┘
```

> **实现要点**：上述改动为页内 UI 增强——在分发日志页面的错误聚合区新增"AI 根因分析"按钮及分析结果面板，不改动导航菜单、不新增路由、不新增独立页面。后端新增 `app/ai/provisioning_analyzer.py` 服务模块，独立于现有 `app/services/` 层。

### 26.4 调用防护（强制）

所有 LLM 调用点必须遵循 AGENTS.md §7.2 三条军规：

| 机制 | 参数 | 实施位置 |
| -------- | ------------------------------- | ----------------------- |
| 物理超时 | `asyncio.wait_for(timeout=10s)` | `ai/llm_client.py` |
| 并发限流 | `asyncio.Semaphore(5)` | `ai/llm_client.py` |
| 短路熔断 | 5 次失败 → OPEN 300s | `ai/circuit_breaker.py` |

**后端目录结构**（`app/ai/`）：

```
app/ai/
├── __init__.py
├── llm_client.py          # DeepSeek 客户端（超时 + 限流）
├── circuit_breaker.py     # 熔断器（5 次失败 → 300s OPEN）
├── prompt_loader.py       # 从 prompt_template 表加载提示词
├── mapping_suggester.py   # 智能映射建议服务
└── provisioning_analyzer.py  # Provisioning 异常分析服务
```

**降级约定**：每个 LLM 调用点必须有 `fallback_fn`，返回结构化退化结果（含 `degraded: true`），不抛异常。

```python
# app/ai/mapping_suggester.py
async def suggest_mappings(unmapped_users: list) -> dict:
    try:
        result = await asyncio.wait_for(
            llm_client.chat(prompt, unmapped_users),
            timeout=10.0
        )
        return {"suggestions": result, "degraded": False}
    except (asyncio.TimeoutError, CircuitBreakerOpen, LLMError):
        # 降级：返回空的建议列表，由调用方走原有匹配链
        return {"suggestions": [], "degraded": True,
                "fallback_reason": "LLM unavailable, using rule-based matching"}
```

### 26.5 前端 AI 区块规范

> 遵循 AGENTS.md §8.1-§8.3 前端 UI 红线。

| 规范 | 实现 |
| -------------------- | ---------------------------------------------------------------------------- |
| 禁止全屏 Loading | AI 分析结果渲染在独立面板中，不阻塞页面其余部分 |
| AI 区块三态 | `Skeleton`（加载中 shimmer）→ `Analysis`（正常结果）/ `Degraded`（降级提示） |
| 业务主链路零 AI 依赖 | 映射确认、分发重试等核心操作不依赖 LLM，AI 区块不加载时仍可操作 |

### 26.6 优先级与阶段

| 功能 | 优先级 | 阶段 | 理由 |
| --------------------- | ------ | -------------------- | ------------------------------------ |
| 智能映射建议 | P1 | 与老用户迁移同期交付 | 迁移期最大收益，直接影响管理员效率 |
| Provisioning 异常分析 | P2 | 运维稳定期后交付 | 迁移期数据量不足以做有意义的模式分析 |

> Break-Glass 事件摘要因触发频率极低（预计 0-1 次/年），不纳入当前开发计划。

______________________________________________________________________

## 附录A：嵌入式 identity-module 方案（方案B）

> 本附录定义方案B的全部内容。方案B不依赖独立数据库，将身份管理功能作为Python包嵌入到业务系统中。
> **适用前提**：业务系统使用Python（FastAPI/Flask/Django） + PostgreSQL（建议同一PG实例）。

### A.1 架构说明

```
┌──────────────────────────────────────────────────────┐
│                 业务系统（如AMDP、新系统X）               │
│                                                        │
│  ┌────────────────────────────────────┐                │
│  │        identity-module 包           │                │
│  │  ┌────────────┐  ┌──────────────┐  │                │
│  │  │ /models/   │  │ /routers/    │  │  业务自有DB    │
│  │  │  identity_ │  │  /identity/  │  │  ┌──────────┐ │
│  │  │  *.py      │  │  v1/*        │  │  │ identity_│ │
│  │  └────────────┘  └──────────────┘  │  │ *表       │ │
│  │  ┌────────────┐  ┌──────────────┐  │  │ (本地)    │ │
│  │  │ /services/ │  │ /sync/       │  │  └──────────┘ │
│  │  │  业务逻辑   │  │  Master↔    │  │               │
│  │  │            │  │  Replica同步 │  │  业务自有表   │
│  │  └────────────┘  └──────────────┘  │  ┌──────────┐ │
│  └────────────────────────────────────┘  │ biz_*    │ │
│                                          └──────────┘ │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│              Identity Hub（Master角色）                 │
│                                                        │
│  职责：用户/部门CRUD入口 → 写本地 → 发同步事件           │
│        → 调用Pocket-ID API创建认证账号                   │
│                                                        │
│  也可以指定一个现有业务系统兼任（如DDAP或AMDP）            │
└──────────────────────────────────────────────────────┘
```

**三角色分工**：

| 角色 | 系统 | 职责 |
| ----------------------- | ------------ | ------------------------------------------------------- |
| **认证源** | Pocket-ID | OIDC认证、Passkey登录、Token签发（唯一，不变） |
| **数据主源（Master）** | Identity Hub | 用户/部门CRUD，变更事件发布，Pocket-ID同步 |
| **数据副本（Replica）** | 各业务系统 | 安装identity-module(role="replica")，接收同步，本地查询 |

### A.2 与方案A的差异对照

| 维度 | 方案A（独立Identity Service） | 方案B（嵌入式 identity-module） |
| ---------- | ------------------------------------------------------------- | ---------------------------------------------------------------- |
| 数据库 | 独立 `identity_db` | 建在业务系统自有DB内 |
| 部署 | `docker-compose up -d` | `pip install identity-module` |
| 表名 | 不变（identity_user 等） | 不变（identity_user 等），可配表名前缀 |
| API路由 | 独立端口暴露 | 挂载在业务系统路由下 `/identity/v1/*` |
| 跨系统查询 | 直接调独立API | 需走Sync转发或MQ事件 |
| 同步 | 不需要（集中存储天然一致） | Master↔Replica，事件驱动或API轮询 |
| 容错 | Identity宕机→所有系统身份查询降级 | 各系统自治，同步中断不影响本地 |
| 升级 | 一个服务更新→全部生效 | 各系统独立 `pip upgrade` |
| 运维 | 多一个容器+DB要维护 | 零额外运维 |
| 通知服务 | 内置 `app/notification/` + `/identity/v1/notifications/*` API | **不含通知功能**，业务系统通过独立 `notification-kit` 包按需集成 |

### A.3 包结构

```
identity-module/
│
├── identity_module/
│   ├── __init__.py               # register_identity() 入口函数
│   │
│   ├── models/                   # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py               # identity_user
│   │   ├── department.py         # identity_department
│   │   ├── user_department.py    # identity_user_department (SCD2)
│   │   ├── mapping.py            # identity_mapping
│   │   ├── tag.py                # identity_tag
│   │   ├── user_tag.py           # identity_user_tag
│   │   ├── user_pending.py       # identity_user_pending
│   │   ├── department_mapping.py # identity_department_mapping
│   │   ├── sync_event_log.py     # identity_sync_event_log
│   │   ├── provisioning_policy.py# identity_provisioning_policy
│   │   ├── provisioning_log.py   # identity_provisioning_log
│   │   └── user_status.py        # identity_user_status
│   │
│   ├── routers/                  # FastAPI路由（与方案A同套API契约）
│   │   ├── __init__.py
│   │   ├── user.py               # /identity/v1/users
│   │   ├── department.py         # /identity/v1/departments
│   │   ├── mapping.py            # /identity/v1/mappings
│   │   ├── tag.py                # /identity/v1/tags
│   │   ├── resolve.py            # /identity/v1/resolve
│   │   └── provision.py          # /identity/v1/provision
│   │
│   ├── services/                 # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── identity_manager.py      # IdentityManager（用户CRUD编排 + 按需Provisioning）
│   │   ├── permission_service.py    # §8 RBAC 权限校验
│   │   ├── role_service.py          # §8 角色管理
│   │   ├── audit_service.py         # §9 审计日志采集/查询
│   │   ├── password_service.py      # Fan-out 密码双写 + 持久化重试
│   │   └── sync_service.py          # Master-Replica 同步核心
│   │
│   ├── sync/                     # 同步机制
│   │   ├── __init__.py
│   │   ├── master.py             # Master端：全量/增量导出端点
│   │   ├── replica.py            # Replica端：API轮询 + MQ消费
│   │   ├── protocols.py          # 同步协议抽象层（SyncEvent/SyncResponse）
│   │   ├── mq_client.py          # RabbitMQ 连接管理器（sync_mode=mq）
│   │   ├── mq_publisher.py       # Master 端 MQ 事件发布器
│   │   └── mq_consumer.py        # Replica 端 MQ 幂等消费者
│   │
│   ├── migrations/               # Alembic迁移脚本
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │
│   └── config.py                 # 配置：role/sync_mode/master_url
│
├── setup.py / pyproject.toml
├── README.md
└── tests/
```

### A.4 集成方式

业务系统只需3步集成：

```python
# step 1: pip install identity-module

# step 2: 在FastAPI应用入口注册
from fastapi import FastAPI
from identity_module import register_identity

app = FastAPI()

register_identity(
    app=app,
    role="replica",             # "master" | "replica"
    master_url="https://hub.company.com",  # Master端地址（replica必填）
    db_session_factory=get_session,     # 共享业务系统DB session
    table_prefix="idm_",                # 可选：表名前缀，默认"identity_"
    sync_mode="mq",                     # "mq"(RabbitMQ) | "api"(轮询)
    mq_url="amqp://user:pass@mq:5672/"  # pragma: allowlist secret
)
# → 自动完成：
#   ① 注册 identity_* 模型到业务系统DB
#   ② 自动创建/更新表结构（通过Alembic）
#   ③ 挂载 /identity/v1/* 路由
#   ④ role=master: 启动变更事件发布
#   ⑤ role=replica: 启动初始全量同步+增量监听
#   [WARN] role=replica：写API（POST/PATCH/DELETE）自动禁用，仅挂载只读路由

# step 3: 业务代码中直接用本地模型查询
from identity_module.models import IdentityUser
user = await db.query(IdentityUser).filter_by(global_user_id=uid).first()
```

### A.5 同步机制

#### A.5.1 同步模式选择

| 模式 | 原理 | 延迟 | 依赖 | 推荐场景 |
| -------------- | ------------------------------------ | ---------------- | -------------- | ---------------------- |
| **MQ事件驱动** | Master变更→发MQ→Replica消费→更新本地 | 实时（毫秒级） | RabbitMQ | 已接入MQ的系统，如DDAP |
| **API轮询** | Replica定时轮询Master API增量接口 | 分钟级（可配置） | Master API可用 | 无MQ环境、轻量场景 |
| **双写回退** | MQ失败→自动回退到API轮询 | 取决于降级策略 | 两者 | 高可用场景推荐 |

#### A.5.2 MQ事件格式

```json
{
    "event_id": "evt_xxxxxxxxxxxx",
    "event_type": "user.created | user.updated | user.deleted | user.dept_changed | dept.created | dept.updated | dept.deleted | mapping.created | mapping.updated",
    "protocol_version": 1,              # 同步协议版本号（低版本Replica不兼容时报警）
    "timestamp": "2026-06-24T12:00:00Z",
    "full_entity": {                     # 完整实体数据（Replica重建用，无需回查Master）
        "global_user_id": "UUID",
        "username": "zhangsan",
        "display_name": "张三",
        "primary_email": "zhangsan@company.com",
        "phone": "13800138000",
        "employee_id": "EMP001",
        "current_dept_code": "RD01",
        "is_active": true
    },
    "changed_fields": ["display_name", "department_id"],  # 本次变更字段索引
    "diff": {                                              # 差值（Replica可按需选消费）
        "before": { "display_name": "张三(旧)", "department_id": "dept_old" },
        "after": { "display_name": "张三", "department_id": "dept_new" }
    },
    "source": "hub.company.com"
}
```

#### A.5.3 同步可靠性保证

| 保障 | MQ模式 | API轮询模式 |
| ---------------- | ------------------------------ | ------------------------- |
| **至少一次送达** | MQ确认机制 + 消费者幂等 | 幂等更新 + 偏移量offset |
| **顺序保证** | 同一实体按change_seq排序 | 按updated_at排序 + 乐观锁 |
| **断线恢复** | Replica重启→拉全量diff | 记录last_sync_at→拉增量 |
| **冲突检测** | MD5校验 + updated_at比大小 | 同左 |
| **监控告警** | sync_event_log记录每次同步结果 | 同左 |

#### A.5.4 同步API端点（Master必备）

> Replica 初始化全量同步、断线恢复增量同步均依赖以下 API。Master 角色必须实现。

```
GET /identity/v1/sync/full
  → 全量导出所有用户+部门+映射的当前快照
  Response: {
    "users": [{...全部identity_user字段}],
    "departments": [{...全部identity_department字段}],
    "mappings": [{...全部identity_mapping字段}],
    "exported_at": "2026-06-24T12:00:00Z"
  }

GET /identity/v1/sync/incremental?since=2026-06-24T12:00:00Z
  → 导出指定时间之后的增量变更
  Response: {
    "events": [
      {
        "event_type": "user.created",
        "timestamp": "...",
        "full_entity": {...},
        "diff": {...}
      }
    ],
    "next_offset": "2026-06-24T12:05:00Z"
  }
  → 空增量：events=[], next_offset=since
```

**协议版本兼容**：Master 的同步 API 在 Response Header 中携带 `X-Protocol-Version: 1`。
Replica 启动时检查版本，不兼容时报警并阻止同步，避免静默数据损坏。

**版本号递增规则**：

| 变更类型 | 示例 | 版本号变动 |
| ------------------ | ------------------------ | ----------------------- |
| 向后兼容的新增字段 | 事件中新增 optional 字段 | `patch` 递增（1.0→1.1） |
| 不兼容的字段变动 | 删除字段、改字段类型 | `major` 递增（1→2） |
| 非功能性修复 | 文档修正、日志优化 | 版本不变 |

各 Replica 在 `config.py` 中声明自己支持的协议版本范围（如 `min_protocol_version=1, max_protocol_version=1`），Master 根据此范围决定推送事件格式。

**Master SPOF 风险**：Master 宕机时新用户无法创建、部门无法同步。
低变更频率场景可接受，高频场景建议：

- 使用方案A（独立Identity Service + PG主备）
- 或方案B仅用于小型、低频变更系统

### A.6 Master角色部署选项

| 选项 | 方案 | 优点 | 缺点 |
| ------ | ---------------------------------------------------------- | -------------------------------------- | ------------------------------------------- |
| **M1** | 轻量Identity Hub独立部署（仅identity-module master + DB） | 专职管理，不受其他系统影响 | 仍需额外容器 |
| **M2** | 指定一个现有业务系统兼任（如DDAP） | 零额外基础设施 | 业务系统变更会影响身份管理可用性 |
| **M3** | 沿用方案A的独立Identity Service做Master，业务系统装replica | 复用方案A基础设施 | 回到方案A的架构 |
| **M4** | 新业务系统自建Master（如AMDP独立部署，`role="master"`） | 完全自治，独立部署，不依赖任何外部系统 | 需自行解决初始数据导入（CSV/Pocket-ID同步） |

**推荐路径**：

- **DDAP 已存在且为 Master**：新系统装 Replica，指向 DDAP（M2 路径）
- **新系统完全独立部署（DDAP 不可达/不存在）**：新系统自建 Master（M4），DDAP 后续可选装 Replica 指向新系统
- **长期演进**：M1（独立 Identity Hub），所有业务系统统一装 Replica

### A.6.1 DDAP 作为 Replica 部署场景

当 AMDP 或其他新系统作为 Master 独立部署时，DDAP 的 identity-module 需要支持 Replica 角色，从新 Master 同步身份数据。

**配置示例（DDAP 作为 Replica）**：

```python
# DDAP 当前配置（Master）→ 新配置（Replica）
register_identity(
    app=app,
    role="replica",                        # Master → Replica
    master_url="https://amdp.company.com",    # 指向 AMDP Master
    db_session_factory=get_session,        # 共享 DDAP 业务 DB
    sync_mode="api",                       # API 轮询
    sync_interval=3600,
)
```

**DDAP Replica 生命周期**：

| 阶段 | 操作 | 说明 |
| ---------------- | ----------------------------------------------------------------- | ---------------------------------------- |
| **初始全量同步** | `GET /identity/v1/sync/full` 拉取 Master 全量用户+部门+映射 | 首次启动时执行，写入本地 `identity_*` 表 |
| **增量同步** | `GET /identity/v1/sync/incremental?since={last_sync_at}` 定时轮询 | 每小时增量：用户创建/修改/禁用、部门变更 |
| **断线恢复** | 记录 `last_sync_at`，恢复后拉增量差量 | Master 端变更排队，恢复后自动补写 |
| **写操作** | Replica 写 API 自动禁用 | 所有用户 CRUD 操作在 Master 端完成 |

**DDAP 现有设计需适配项**：

| 适配项 | 说明 |
| ------------------ | ---------------------------------------------------------------------------- |
| **配置模板** | 新增 `role="replica"` 配置路径和部署文档 |
| **初始同步** | DDAP 首次作为 Replica 启动时，需清空本地 `identity_*` 表并从 Master 全量拉取 |
| **数据迁移** | 如果 DDAP 之前作为 Master 已有用户数据，需先导出到 Master 再切换角色 |
| **Pocket-ID 去重** | DDAP 不再向 Pocket-ID 推送用户，由 Master 统一推送 |

### A.6.2 双 Master 独立域场景

当两个系统（如 AMDP 和 DDAP）的用户群体不完全重叠、各自独立管理身份时，可各自作为 Master，互不干扰。

```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│  AMDP (Master)              │    │  DDAP (Master)              │
│  identity_* 表（独立）       │    │  identity_* 表（独立）       │
│  用户：研发工具使用者         │    │  用户：数据平台使用者         │
│  global_user_id: UUID v7    │    │  global_user_id: UUID v7    │
└─────────────┬───────────────┘    └─────────────┬───────────────┘
              │                                   │
              │  Provisioning                     │  Provisioning
              ▼                                   ▼
      ┌─────────────────────────────────────────────────┐
      │              Pocket-ID（统一认证）                │
      │  按 employee_id 去重，同一员工不重复创建账号       │
      └─────────────────────────────────────────────────┘
```

**关键设计要求**：

**1. global_user_id 跨系统唯一性（UUID v7）**

| 维度 | 说明 |
| ------------ | ------------------------------------------------------------------------- |
| **格式** | UUID v7（RFC 9562），48位毫秒时间戳 + 74位随机数 |
| **生成位置** | 各 Master 的 ORM 本地生成，无需中心化协调 |
| **冲突概率** | 74位随机数空间，同一毫秒内生成 10^9 个 ID 的冲突概率 < 10^-10，实际可忽略 |
| **索引优势** | 时间戳前缀使 B-Tree 索引插入接近顺序写，性能优于 UUID v4 |
| **示例** | `018f3a5c-9b00-7d4e-8a2c-3f1b6e9d0a47`（前8字符含时间戳，可排序） |

```python
# Python 生成 UUID v7（Python 3.14+ 内置，低版本用 uuid6 库）
import uuid
user_id = uuid.uuid7()  # → UUID('018f3a5c-9b00-7d4e-8a2c-3f1b6e9d0a47')
```

**2. identity_mapping 跨 Master 可见**

当 AMDP 用户也需要访问 DDAP（或反之），映射表需支持跨 Master 查询：

```sql
-- identity_mapping 新增字段（已有 source_system 字段支持）
-- source_system 可取值扩展：
--   'amdp'         — 用户在 AMDP Master 创建
--   'ddap'         — 用户在 DDAP Master 创建
--   'gitlab'       — 传统外部系统映射
--   ...
```

**3. 跨 Master 用户查询流程**：

```
AMDP 用户登录 DDAP
  → Pocket-ID 认证通过（共享 OIDC）
  → DDAP 查本地 identity_mapping 表（source_system='amdp'）
    → 找到：该用户已存在于 DDAP 本地映射，直接使用
    → 未找到：DDAP 调用 AMDP Master API 查询用户信息
      → 在 DDAP 本地创建 identity_mapping 记录（status='MANUAL'）
      → 后续查询走本地映射
```

**4. 双 Master 适用条件**：

| 条件 | 说明 |
| ------------------------ | ------------------------------------------ |
| 用户群体基本不重叠 | 两系统服务不同团队，交叉用户 < 10% |
| 各自独立运维 | 部署、升级、数据管理互不依赖 |
| 可接受交叉用户的手动映射 | 少数交叉用户通过 identity_mapping 手动关联 |

> **不满足以上条件时**：应选择单 Master + 多 Replica 架构，而非双 Master。

**备升主降级**：当Master不可用且恢复时间不可接受时（如机器故障需重建），可选方案B的任一Replica实例作为临时Master。操作步骤：

1. 停用原Master的同步事件发布
1. 在目标Replica实例上执行 `register_identity(role="master")` 完成角色切换
1. 其他Replica的 `master_url` 指向新Master
1. 新Master从Pocket-ID和identity_db重建完整数据集

备升主是**人工操作**，不可自动化以避免脑裂。恢复后建议切回原架构。

**双 Master 独立域下的权限冲突策略**：按 source_system 隔离角色定义

````sql
-- identity_role 增加 source_system 字段
ALTER TABLE identity_role ADD COLUMN source_system VARCHAR(32) DEFAULT 'identity';
~~~sql

- AMDP 定义的 dept_admin 仅在 AMDP 域内生效。
- DDAP 定义的 dept_admin 仅在 DDAP 域内生效。
- 跨系统访问时，权限合并取 并集（Union），以较宽松的权限为准（安全妥协：宁可多给权限，也不阻断业务流程）。

### A.7 Provisioning（多 Master 适配）

ProvisioningEngine 为独立模块，方案A和方案B复用同一套接口。但在多 Master 场景下，需要增强以下能力：

#### A.7.1 单 Master 场景（不变）

```
identity-module(Master) → ProvisioningEngine → Pocket-ID / GitLab / ...
```

#### A.7.2 多 Master 场景（新增）

```
AMDP (Master)  ──→ ProvisioningEngine ──→ Pocket-ID
DDAP (Master)  ──→ ProvisioningEngine ──→ Pocket-ID  ← 同一 Pocket-ID 收到多份推送
```

**Pocket-ID 适配器新增能力**：

| 能力 | 实现方式 | 说明 |
|------|----------|------|
| **幂等推送** | 按 `employee_id` 去重 | `GET /api/users?employee_id=xxx` 先查是否存在，存在则走更新而非创建 |
| **来源标记** | 推送事件携带 `source_system` 字段 | `identity_provisioning_log.source_system` 记录推送来源（`amdp`/`ddap`），Pocket-ID 侧可追溯 |
| **冲突策略** | 以 `updated_at` 时间戳为准 | 两 Master 对同一用户推送不同字段时，保留 `updated_at` 更新的版本 |
| **人工兜底** | 冲突无法自动裁决时标记 `permanent_failed` | 通知管理员手动选择权威源，记录到 `identity_provisioning_log` |

**冲突示例与处理**：

```
场景：AMDP 和 DDAP 都向 Pocket-ID 推送了用户 zhangsan
  AMDP 推送：{ dept_code: "RD01", updated_at: "2026-06-25T10:00:00Z" }
  DDAP 推送：{ dept_code: "RD02", updated_at: "2026-06-25T11:00:00Z" }

处理：DDAP 的 updated_at 更新 → Pocket-ID 保留 dept_code="RD02"
      同时在 identity_provisioning_log 记录冲突来源，供审计追溯
```

#### A.7.3 Provisioning 配置扩展

```yaml
# 多 Master 场景下，各 Master 独立配置 provisioning
provisioning:
  source_system: "amdp"          # 新增：推送来源标识
  pocket_id:
    dedup_key: "employee_id"     # 新增：去重键
    conflict_strategy: "latest_updated_at"  # 新增：冲突策略
  adapters:
    - pocketid
    - gitlab
```

Provisinoing适配器接口（§19）、Pocket-ID推送逻辑（§5.4 通知通道）均复用，仅新增上述配置项。

### A.8 适用场景判断

| 场景 | 推荐方案 |
|------|----------|
| 新开发一个独立系统（如AMDP），不想额外维护DB | **方案B（嵌入式）** |
| 新开发系统完全独立部署，Master（DDAP）不可达 | **方案B（嵌入式，自建Master，M4）** |
| 已有多个系统需要统一身份 | **方案A（独立）** |
| 系统规模小（<50用户），只有一个应用 | **方案B（嵌入式，replica只读模式）** |
| 需要跨系统SSO（GitLab/SonarQube等） | **方案A（独立）** |
| 系统对Identity Service的可用性高度敏感 | **方案B（嵌入式，本地自治）** |
| 需要审计合规、全量操作日志集中管理 | **方案A（独立）** |
| 混合：已有多个系统+新开发系统 | **方案A（独立Identity）+ 方案B（新系统装replica）** |
| 两个系统用户群体不重叠，各自独立运维 | **方案B（双Master独立域，§A.6.2）** |
| DDAP 已有 Master，新系统接入 | **方案B（新系统装 Replica，指向 DDAP）** |
| 新系统自建 Master，DDAP 后续接入 | **DDAP 装 Replica 指向新系统（§A.6.1）** |
````
