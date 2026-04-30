# GitLab 需求管理与测试管理基础数据源

> **文档版本**: 2.0\
> **创建日期**: 2025-12-17\
> **最后更新**: 2025-12-17\
> **适用范围**: 需求管理、测试管理指标度量
>
> **更新日志**:
>
> - **v2.0** (2025-12-17): 整合 Issue 分类规范详细说明、快速开始指南和常见问题解答，形成完整的一体化文档
> - **v1.0** (2025-12-17): 初始版本，梳理 GitLab 数据源和指标度量体系

______________________________________________________________________

## 📋 目录

1. [概述](#%E6%A6%82%E8%BF%B0)
1. [需求管理数据源](#%E9%9C%80%E6%B1%82%E7%AE%A1%E7%90%86%E6%95%B0%E6%8D%AE%E6%BA%90)
1. [测试管理数据源](#%E6%B5%8B%E8%AF%95%E7%AE%A1%E7%90%86%E6%95%B0%E6%8D%AE%E6%BA%90)
1. [关键指标度量维度](#%E5%85%B3%E9%94%AE%E6%8C%87%E6%A0%87%E5%BA%A6%E9%87%8F%E7%BB%B4%E5%BA%A6)
1. [数据采集方案](#%E6%95%B0%E6%8D%AE%E9%87%87%E9%9B%86%E6%96%B9%E6%A1%88)
1. [最佳实践建议](#%E6%9C%80%E4%BD%B3%E5%AE%9E%E8%B7%B5%E5%BB%BA%E8%AE%AE)
1. [附录](#%E9%99%84%E5%BD%95)
1. [总结](#%E6%80%BB%E7%BB%93)
1. [快速开始指南](#%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B%E6%8C%87%E5%8D%97)
1. [常见问题解答](#%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98%E8%A7%A3%E7%AD%94)
1. [核心概念速查表](#%E6%A0%B8%E5%BF%83%E6%A6%82%E5%BF%B5%E9%80%9F%E6%9F%A5%E8%A1%A8)

______________________________________________________________________

## 概述

GitLab 作为一体化 DevOps 平台，提供了丰富的 API 接口和数据模型，可以支持需求管理和测试管理的全生命周期数据采集。本文档从**指标度量**的角度，系统性地梳理 GitLab 能够提供的基础数据。

### 核心价值

- **需求全生命周期追踪**: 从需求提出、评审、开发到验收的完整过程
- **测试覆盖度分析**: 代码覆盖率、测试执行情况、质量门禁
- **效能度量**: 需求交付周期、测试通过率、缺陷密度等关键指标
- **可追溯性**: 需求-代码-测试-部署的完整追溯链

______________________________________________________________________

## 需求管理数据源

### 1. Issues (议题/需求)

GitLab Issues 是需求管理的核心载体，可以用于记录用户故事、功能需求、缺陷等。

#### 1.1 基础属性数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | 全局唯一 ID | 需求标识 | `/api/v4/projects/:id/issues` |
| `iid` | 项目内序号 | 需求编号 | 同上 |
| `title` | 需求标题 | 需求描述 | 同上 |
| `description` | 详细描述 | 需求详情、验收标准 | 同上 |
| `state` | 状态 (opened/closed) | 需求完成度统计 | 同上 |
| `created_at` | 创建时间 | 需求提出时间 | 同上 |
| `updated_at` | 更新时间 | 需求活跃度 | 同上 |
| `closed_at` | 关闭时间 | 需求完成时间 | 同上 |

#### 1.2 需求分类与优先级

| 数据字段 | 字段说明 | 度量用途 | 示例值 |
|---------|---------|---------|--------|
| `labels` | 标签数组 | 需求类型分类、优先级标记 | `["feature", "P0", "backend"]` |
| `milestone` | 里程碑 | 版本规划、迭代管理 | `{"title": "v2.0", "due_date": "2025-12-31"}` |
| `weight` | 权重/工作量 | 需求规模估算 | `5` (故事点) |
| `epic` | 史诗 (Ultimate) | 大需求拆解、主题管理 | Epic ID |

**💡 如何区分需求和 Bug？**

GitLab Issue 本身没有内置的类型字段，而是通过 **Labels (标签)** 来区分需求、Bug、任务等不同类型。推荐使用 **Scoped Labels** 实现规范化分类。

**Scoped Labels 优势**:

- **互斥性**: 同一个 Issue 只能有一个相同 key 的标签（如 `type::feature` 和 `type::bug` 不能同时存在）
- **规范性**: 格式统一 `key::value`，便于管理
- **易统计**: 便于 API 查询和 SQL 分析

##### 类型标签 (Type Labels)

**格式**: `type::value`

| 标签名称 | 说明 | 使用场景 | 颜色建议 |
|---------|------|---------|---------|
| `type::feature` | 功能需求 | 新功能开发 | 🟦 蓝色 `#428BCA` |
| `type::bug` | 缺陷/Bug | 软件缺陷修复 | 🟥 红色 `#D9534F` |
| `type::test` | 测试用例 | 模拟测试管理 | 🟫 棕色 `#795548` |

##### 测试结果标签 (Test Result Labels) - 仅用于测试用例执行

**格式**: `test-result::value`

用于统计测试用例的通过率和质量覆盖情况。

| 标签名称 | 说明 | 颜色建议 |
|---------|------|---------|
| `test-result::passed` | 通过 | 功能验证通过 | 🟢 `#2ECC71` |
| `test-result::failed` | 失败 | 验证失败，需创建 Bug | 🔴 `#E74C3C` |
| `test-result::blocked` | 阻塞 | 外部原因无法执行 | 🟧 `#F39C12` |

##### 需求类型标签 (Requirement Type Labels) - 仅用于需求

**格式**: `requirement-type::value`

用于对业务需求进行更精细的分类统计。

| 标签名称 | 说明 | 颜色建议 |
|---------|------|---------|
| `requirement-type::feature` | 功能 | 新业务功能需求 | 🟦 `#3498DB` |
| `requirement-type::interface` | 接口 | 接口定义或变更需求 | 🟪 `#9B59B6` |
| `requirement-type::performance` | 性能 | 系统性能提升需求 | 🟧 `#E67E22` |
| `requirement-type::safe` | 安全 | 安全性加固及漏洞修复 | ⚫ `#000000` |
| `requirement-type::experience` | 体验 | 用户交互体验优化 | 🟩 `#1ABC9C` |
| `requirement-type::improve` | 改进 | 现有功能的完善与增强 | 🟢 `#27AE60` |
| `requirement-type::other` | 其他 | 无法归类的其他需求类型 | 🔘 `#95A5A6` |

##### 评审结论标签 (Review Result Labels) - 适用于需求、代码评审

**格式**: `review-result::value`

用于统计需求准入及代码合并的评审质量。

| 标签名称 | 说明 | 判定标准 | 颜色 |
|---------|------|---------|------|
| `review-result::approved` | 评审通过 | 需求可进入开发 或 代码允许合并 | 🟢 `#2ECC71` |
| `review-result::rework` | 需修正 | 存在逻辑缺陷或代码规范问题，需修改后复审 | 🟧 `#E67E22` |
| `review-result::rejected` | 驳回 | 需求不合理 或 代码质量太差被拒绝 | 🔴 `#D9534F` |

##### 代码评审状态标签 (Review Status Labels) - 仅用于合并请求 (MR)

**格式**: `review::value`

用于追踪 MR 的评审过程动态，识别评审瓶颈。

| 标签名称 | 说明 | 颜色 |
|---------|------|------|
| `review::speed-up` | 催审 | 属于紧急修复或核心功能，需优先评审 | 🔴 `#E74C3C` |
| `review::ping-pong` | 讨论中 | 评审者与提交者互动频繁，存在较大分歧 | 🟧 `#F39C12` |
| `review::on-hold` | 挂起 | 暂时无法评审，待环境、依赖或其它需求就绪 | 🔘 `#95A5A6` |

##### 优先级标签 (Priority Labels) - 适用于所有类型

**格式**: `priority::P0` ~ `priority::P3`

| 标签名称 | 优先级 | 说明 | 处理时效 | 判定标准 |
|---------|-------|------|---------|---------|
| `priority::P0` | 紧急 | 阻塞性问题，影响核心功能 | 立即处理 (4小时内) | 所有用户受影响，核心业务中断，无替代方案 |
| `priority::P1` | 高 | 重要功能，影响用户体验 | 1-2天内处理 | 大部分用户受影响，重要功能受限 |
| `priority::P2` | 中 | 一般功能，可计划处理 | 1周内处理 | 部分用户受影响，一般功能受限，有替代方案 |
| `priority::P3` | 低 | 次要功能，可延后处理 | 下个迭代处理 | 个别用户受影响，体验优化 |

##### 严重程度标签 (Severity Labels) - 仅用于 Bug

**格式**: `severity::S1` ~ `severity::S4`

| 标签名称 | 严重程度 | 说明 | 典型场景 | 判定标准 |
|---------|---------|------|---------|---------|
| `severity::S1` | 致命 (Blocker) | 系统崩溃、数据丢失、安全漏洞 | 生产环境宕机、数据泄露 | 系统不可用，数据丢失/损坏，严重安全漏洞 |
| `severity::S2` | 严重 (Critical) | 核心功能不可用，无替代方案 | 登录失败、支付失败 | 核心功能不可用，数据错误，无替代方案 |
| `severity::S3` | 一般 (Major) | 功能异常，有替代方案 | 页面显示错误、性能下降 | 部分功能不可用，数据显示异常，有替代方案 |
| `severity::S4` | 轻微 (Minor) | UI 问题、文案错误、小瑕疵 | 按钮错位、提示语错误 | 功能可用，UI/文案问题，无数据影响 |

##### Bug 类别标签 (Bug Category) - 仅用于 Bug

**格式**: `bug-category::value`

Bug 类别用于细分 Bug 的具体类型，便于问题分析和统计。

| 标签名称 | 说明 | 典型场景 | 颜色 |
|---------|------|---------|------|
| `bug-category::test-script` | 测试脚本问题 | 自动化测试脚本错误、测试用例设计问题 | 🟦 `#3498DB` |
| `bug-category::code-error` | 代码错误 | 逻辑错误、空指针、数组越界等编码问题 | 🟥 `#E74C3C` |
| `bug-category::configuration` | 配置相关 | 配置文件错误、环境变量问题、参数配置不当 | 🟨 `#F39C12` |
| `bug-category::design-defect` | 设计缺陷 | 架构设计问题、接口设计不合理、业务逻辑缺陷 | 🟪 `#9B59B6` |
| `bug-category::deployment` | 安装部署 | 部署脚本错误、依赖缺失、环境兼容性问题 | 🟧 `#E67E22` |
| `bug-category::performance` | 性能问题 | 响应慢、内存泄漏、CPU 占用高、并发问题 | 🟩 `#2ECC71` |
| `bug-category::security` | 安全相关 | SQL 注入、XSS、权限漏洞、数据泄露 | ⚫ `#34495E` |
| `bug-category::standard` | 标准规范 | 代码规范违反、文档不符合标准、命名不规范 | 🟫 `#795548` |
| `bug-category::other` | 其他 | 无法归类的其他问题 | ⚪ `#95A5A6` |

**Bug 类别判定指南**:

| 类别 | 判定依据 | 示例 |
|------|---------|------|
| **测试脚本** | 问题出现在测试代码中 | 测试用例断言错误、Mock 数据不正确 |
| **代码错误** | 业务代码逻辑错误 | 空指针异常、条件判断错误、循环逻辑问题 |
| **配置相关** | 配置文件或参数问题 | 数据库连接配置错误、超时参数设置不当 |
| **设计缺陷** | 设计层面的问题 | API 接口设计不合理、数据模型设计缺陷 |
| **安装部署** | 部署过程中的问题 | Docker 镜像构建失败、依赖包版本冲突 |
| **性能问题** | 性能指标不达标 | 接口响应时间 > 3s、内存占用持续增长 |
| **安全相关** | 安全漏洞或风险 | 未授权访问、敏感信息泄露 |
| **标准规范** | 不符合规范要求 | 代码不符合 PEP8、API 文档缺失 |
| **其他** | 无法明确分类 | 复杂的综合性问题 |

##### Bug 来源标签 (Bug Source) - 仅用于 Bug

**格式**: `bug-source::value`

Bug 来源用于区分 Bug 是在生产环境还是非生产环境发现的，用于统计**缺陷逃逸率**。

| 标签名称 | 说明 | 用途 | 颜色 |
|---------|------|------|------|
| `bug-source::production` | 生产环境发现 | 缺陷逃逸统计 | 🔴 `#E74C3C` |
| `bug-source::non-production` | 非生产环境发现 | 测试发现统计 | 🟢 `#27AE60` |

**环境定义**:

| 环境类型 | 说明 | 示例 |
|---------|------|------|
| **生产环境** | 正式对外提供服务的环境 | Production, Live |
| **非生产环境** | 开发、测试、预发布等环境 | Dev, Test, UAT, Staging, Pre-production |

**缺陷逃逸率计算**:

```sql
缺陷逃逸率 = (生产环境发现的 Bug 数 / 总 Bug 数) × 100%

-- SQL 示例
SELECT 
    COUNT(CASE WHEN labels::text LIKE '%bug-source::production%' THEN 1 END) AS production_bugs,
    COUNT(*) AS total_bugs,
    ROUND(
        COUNT(CASE WHEN labels::text LIKE '%bug-source::production%' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) AS defect_escape_rate
FROM gitlab_issues
WHERE labels::text LIKE '%type::bug%';
```

**业务价值**:

- ✅ 评估测试质量和有效性
- ✅ 识别测试覆盖的盲区
- ✅ 优化测试策略
- ✅ 降低生产环境风险

**⚠️ 重要**: 严重程度 (Severity) ≠ 优先级 (Priority)

- **严重程度**: 技术角度，Bug 对系统的影响程度
- **优先级**: 业务角度，修复/开发的紧急程度
- **关系**: 通常 S1→P0, S2→P0/P1, S3→P1/P2, S4→P2/P3，但可根据业务需求调整

**标签组合示例**:

```yaml
# 示例 1: 功能需求
type::feature + priority::P1
标题: "[P1] 用户登录功能"

# 示例 2: 代码错误导致的致命 Bug
type::bug + severity::S1 + priority::P0 + bug-category::code-error
标题: "[P0][S1][代码错误] 空指针异常导致服务崩溃"

# 示例 3: 配置问题导致的一般 Bug
type::bug + severity::S3 + priority::P2 + bug-category::configuration
标题: "[P2][S3][配置] 数据库连接池配置不当导致连接超时"

# 示例 4: 性能问题（严重但非紧急）
type::bug + severity::S2 + priority::P1 + bug-category::performance
标题: "[P1][S2][性能] 查询响应时间超过 5 秒"

# 示例 5: 安全漏洞（最高优先级）
type::bug + severity::S1 + priority::P0 + bug-category::security
标题: "[P0][S1][安全] SQL 注入漏洞"

# 示例 6: 设计缺陷（即将下线的功能）
type::bug + severity::S2 + priority::P3 + bug-category::design-defect
标题: "[P3][S2][设计缺陷] 旧版报表数据模型设计不合理"
说明: 严重度高但优先级低，因为该功能即将下线

# 示例 7: 部署问题
type::bug + severity::S3 + priority::P1 + bug-category::deployment
标题: "[P1][S3][部署] Docker 容器启动失败"

# 示例 8: 标准规范问题（轻微但客户要求）
type::bug + severity::S4 + priority::P1 + bug-category::standard
标题: "[P1][S4][标准规范] 登录按钮文案显示为英文"
说明: 严重度低但优先级高，因为客户强烈要求修复
```

##### 状态标签 (Status Labels) - 适用于所有类型

**格式**: `status::value`

用于追踪议题从创建到关闭的全生命周期状态。

| 标签名称 | 说明 | 业务阶段 | 颜色建议 |
|---------|------|---------|---------|
| `status::draft` | 草稿 | 议题正在起草中，尚未正式提交 | 🔘 `#BDC3C7` |
| `status::reviewing` | 评审中 | 需求/方案正在进行评审 | 🟪 `#9B59B6` |
| `status::feedback` | 修正中 | 评审未通过，需修正反馈意见 | 🟧 `#E67E22` |
| `status::todo` | 待处理 | 已准备就绪，等待开发排期 | 🔘 `#CCCCCC` |
| `status::in-progress` | 进行中 | 开发人员正在处理中 | 🟦 `#3498DB` |
| `status::testing` | 测试中 | 开发完成，正在进行验证 | 🟨 `#F39C12` |
| `status::blocked` | 阻塞 | 由于外部原因导致流程中断 | 🔴 `#E74C3C` |
| `status::done` | 已完成 | 议题已处理完毕并通过验证 | 🟢 `#2ECC71` |

##### 关闭原因标签 (Resolution Labels) - 用于关闭议题

**格式**: `resolution::value`

用于统计议题关闭的具体原因，以便后续效能复盘。

| 标签名称 | 适用类型 | 说明 | 颜色建议 |
|---------|---------|------|---------|
| `resolution::done` | 通用 | 已完成并交付 | 🟢 `#2ECC71` |
| `resolution::duplicate` | 通用 | 重复的议题 | 🔘 `#95A5A6` |
| `resolution::postponed` | 通用 | 决定延期处理 | 🟦 `#3498DB` |
| `resolution::wontfix` | 通用 | 经评审决定不做 | 🟧 `#E67E22` |
| `resolution::by_design` | 通用 | 经核实符合原始设计 | 🟪 `#9B59B6` |
| `resolution::cannot_reproduce` | 仅 Bug | 无法重现的问题 | 🟨 `#F1C40F` |
| `resolution::as_requirement` | 仅 Bug | 实际为新需求，转为需求处理 | ⚫ `#34495E` |

**创建标签**:

使用项目提供的批量创建工具：

```bash
# 为群组创建所有标签（推荐，可跨项目共享）
# 包含: type, priority, severity, status, bug_category, bug_source 共 6 类 33 个标签
python scripts/create_gitlab_labels.py --group-id <your_group_id>

# 为单个项目创建标签
python scripts/create_gitlab_labels.py --project-id <your_project_id>

# 只创建特定类型的标签
python scripts/create_gitlab_labels.py --group-id <your_group_id> --types type priority severity bug_category bug_source
```

#### 1.3 需求协作数据

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `author` | 创建人 | 需求来源分析 | 用户对象 |
| `assignees` | 指派人 | 需求负责人、工作量分配 | 用户数组 |
| `upvotes` | 点赞数 | 需求优先级评估 | 社区反馈 |
| `user_notes_count` | 评论数 | 需求讨论活跃度 | 协作指标 |

#### 1.4 需求工时数据

| 数据字段 | 字段说明 | 度量用途 | 单位 |
|---------|---------|---------|------|
| `time_estimate` | 预估工时 | 需求规模、计划工时 | 秒 |
| `total_time_spent` | 实际工时 | 实际投入、偏差分析 | 秒 |
| `time_stats.human_time_estimate` | 可读预估工时 | 报表展示 | `"2h 30m"` |
| `time_stats.human_total_time_spent` | 可读实际工时 | 报表展示 | `"3h 15m"` |

#### 1.5 需求关联关系

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `related_merge_requests` | 关联的 MR | 需求-代码追溯 | `/api/v4/projects/:id/issues/:issue_iid/related_merge_requests` |
| `links` | 关联的其他 Issue | 需求依赖关系 | `/api/v4/projects/:id/issues/:issue_iid/links` |
| `closed_by` | 关闭该 Issue 的 MR | 需求完成追溯 | Issue 对象中的字段 |

______________________________________________________________________

### 2. Milestones (里程碑)

里程碑用于版本规划和迭代管理，是需求管理的重要时间维度。

#### 2.1 里程碑基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | 里程碑 ID | 版本标识 | `/api/v4/projects/:id/milestones` |
| `title` | 里程碑名称 | 版本名称 | 同上 |
| `description` | 描述 | 版本目标 | 同上 |
| `state` | 状态 (active/closed) | 版本状态 | 同上 |
| `due_date` | 截止日期 | 版本计划时间 | 同上 |
| `start_date` | 开始日期 | 版本启动时间 | 同上 |
| `created_at` | 创建时间 | 版本创建时间 | 同上 |
| `updated_at` | 更新时间 | 版本更新时间 | 同上 |

#### 2.2 里程碑统计数据

| 数据字段 | 字段说明 | 度量用途 | 计算方式 |
|---------|---------|---------|----------|
| `total_issues_count` | 总需求数 | 版本规模 | API 返回 |
| `closed_issues_count` | 已完成需求数 | 版本完成度 | API 返回 |
| `percentage_complete` | 完成百分比 | 版本进度 | `closed / total * 100` |

______________________________________________________________________

### 3. Epics (史诗) - GitLab Ultimate

史诗用于管理大型需求主题，支持跨项目的需求组织。

#### 3.1 史诗基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | 史诗 ID | 主题标识 | `/api/v4/groups/:id/epics` |
| `title` | 史诗标题 | 主题名称 | 同上 |
| `description` | 描述 | 主题目标 | 同上 |
| `state` | 状态 | 主题状态 | 同上 |
| `start_date` | 开始日期 | 主题计划开始 | 同上 |
| `due_date` | 截止日期 | 主题计划结束 | 同上 |
| `labels` | 标签 | 主题分类 | 同上 |

#### 3.2 史诗关联数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `issues` | 关联的 Issues | 主题需求列表 | `/api/v4/groups/:id/epics/:epic_id/issues` |
| `parent_id` | 父史诗 ID | 史诗层级关系 | Epic 对象中的字段 |

______________________________________________________________________

### 4. Requirements (需求管理) - GitLab Ultimate

GitLab Ultimate 提供专门的需求管理功能，支持需求的正式化管理。

#### 4.1 需求基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `iid` | 需求 ID | 需求标识 | `/api/v4/projects/:id/requirements` |
| `title` | 需求标题 | 需求名称 | 同上 |
| `description` | 需求描述 | 需求详情 | 同上 |
| `state` | 状态 (opened/archived) | 需求状态 | 同上 |
| `created_at` | 创建时间 | 需求提出时间 | 同上 |
| `updated_at` | 更新时间 | 需求更新时间 | 同上 |

#### 4.2 需求满足状态

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `last_test_report_state` | 最后测试报告状态 | 需求验证状态 | `passed/failed` |
| `last_test_report_manually_created` | 是否手动创建 | 测试方式 | Boolean |

______________________________________________________________________

## 测试管理数据源

### 1. Pipelines (CI/CD 流水线)

Pipeline 是 GitLab 测试管理的核心，记录了自动化测试的执行情况。

#### 1.1 流水线基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | 流水线 ID | 测试执行标识 | `/api/v4/projects/:id/pipelines` |
| `status` | 状态 | 测试执行结果 | 同上 |
| `ref` | 分支/标签 | 测试环境 | 同上 |
| `sha` | Commit SHA | 代码版本追溯 | 同上 |
| `source` | 触发源 | 测试触发方式 | `push/merge_request_event/schedule` |
| `created_at` | 创建时间 | 测试开始时间 | 同上 |
| `updated_at` | 更新时间 | 测试结束时间 | 同上 |
| `duration` | 执行时长 | 测试效率 | 秒 |
| `coverage` | 代码覆盖率 | 测试覆盖度 | 百分比字符串 |

#### 1.2 流水线状态枚举

| 状态值 | 说明 | 度量用途 |
|-------|------|---------|
| `created` | 已创建 | 待执行 |
| `waiting_for_resource` | 等待资源 | 资源瓶颈分析 |
| `preparing` | 准备中 | 启动时间 |
| `pending` | 待执行 | 排队时间 |
| `running` | 执行中 | 执行中 |
| `success` | 成功 | **测试通过** |
| `failed` | 失败 | **测试失败** |
| `canceled` | 已取消 | 中断分析 |
| `skipped` | 已跳过 | 跳过分析 |
| `manual` | 手动 | 手动干预 |

______________________________________________________________________

### 2. Pipeline Jobs (流水线作业)

Job 是 Pipeline 的具体执行单元，通常对应具体的测试任务。

#### 2.1 作业基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | 作业 ID | 测试任务标识 | `/api/v4/projects/:id/pipelines/:pipeline_id/jobs` |
| `name` | 作业名称 | 测试类型 | 同上 |
| `stage` | 阶段 | 测试阶段 | `test/integration/e2e` |
| `status` | 状态 | 测试结果 | 同上 |
| `created_at` | 创建时间 | 任务创建时间 | 同上 |
| `started_at` | 开始时间 | 任务开始时间 | 同上 |
| `finished_at` | 完成时间 | 任务完成时间 | 同上 |
| `duration` | 执行时长 | 测试效率 | 秒 |
| `coverage` | 覆盖率 | 单个测试覆盖率 | 百分比 |

#### 2.2 作业失败信息

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `failure_reason` | 失败原因 | 失败分类分析 | `script_failure/runner_system_failure` |
| `allow_failure` | 允许失败 | 非阻塞测试识别 | Boolean |

#### 2.3 测试报告数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `artifacts` | 制品文件 | 测试报告、覆盖率报告 | `/api/v4/projects/:id/jobs/:job_id/artifacts` |
| `trace` | 执行日志 | 失败原因分析 | `/api/v4/projects/:id/jobs/:job_id/trace` |

______________________________________________________________________

### 3. Test Reports (测试报告)

GitLab 支持解析 JUnit XML 格式的测试报告，提供结构化的测试结果数据。

#### 3.1 测试报告汇总数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `total_time` | 总执行时间 | 测试效率 | `/api/v4/projects/:id/pipelines/:pipeline_id/test_report` |
| `total_count` | 总测试用例数 | 测试规模 | 同上 |
| `success_count` | 成功用例数 | 测试通过数 | 同上 |
| `failed_count` | 失败用例数 | 测试失败数 | 同上 |
| `skipped_count` | 跳过用例数 | 跳过用例数 | 同上 |
| `error_count` | 错误用例数 | 错误用例数 | 同上 |

#### 3.2 测试套件数据

| 数据字段 | 字段说明 | 度量用途 | 层级 |
|---------|---------|---------|------|
| `name` | 测试套件名称 | 测试模块 | Suite |
| `total_time` | 套件执行时间 | 模块测试效率 | Suite |
| `total_count` | 套件用例数 | 模块测试规模 | Suite |
| `success_count` | 套件成功数 | 模块通过率 | Suite |
| `failed_count` | 套件失败数 | 模块失败率 | Suite |

#### 3.3 测试用例数据

| 数据字段 | 字段说明 | 度量用途 | 层级 |
|---------|---------|---------|------|
| `name` | 用例名称 | 用例标识 | Case |
| `classname` | 类名 | 用例分类 | Case |
| `execution_time` | 执行时间 | 用例效率 | Case |
| `status` | 状态 | 用例结果 | `passed/failed/skipped/error` |
| `system_output` | 标准输出 | 失败详情 | Case |
| `stack_trace` | 堆栈跟踪 | 失败原因 | Case |

______________________________________________________________________

### 4. Code Coverage (代码覆盖率)

代码覆盖率是测试质量的重要指标。

#### 4.1 项目级覆盖率

| 数据字段 | 字段说明 | 度量用途 | 来源 |
|---------|---------|---------|------|
| `pipeline.coverage` | 流水线覆盖率 | 整体覆盖率 | Pipeline 对象 |
| `job.coverage` | 作业覆盖率 | 单个测试覆盖率 | Job 对象 |

#### 4.2 覆盖率趋势

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `coverage_history` | 历史覆盖率 | 覆盖率趋势 | 通过 Pipelines API 聚合 |

#### 4.3 覆盖率报告文件

| 文件格式 | 说明 | 工具示例 |
|---------|------|---------|
| Cobertura XML | 覆盖率详细报告 | pytest-cov, JaCoCo |
| SimpleCov JSON | Ruby 覆盖率 | SimpleCov |
| LCOV | C/C++ 覆盖率 | gcov, lcov |

______________________________________________________________________

### 5. Merge Requests (合并请求)

MR 是代码评审和测试的重要环节，包含丰富的测试相关数据。

#### 5.1 MR 基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | MR ID | MR 标识 | `/api/v4/projects/:id/merge_requests` |
| `iid` | 项目内序号 | MR 编号 | 同上 |
| `title` | 标题 | MR 描述 | 同上 |
| `state` | 状态 | MR 状态 | `opened/merged/closed` |
| `created_at` | 创建时间 | MR 创建时间 | 同上 |
| `merged_at` | 合并时间 | MR 合并时间 | 同上 |
| `closed_at` | 关闭时间 | MR 关闭时间 | 同上 |

#### 5.2 MR 测试状态

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `pipeline` | 关联的 Pipeline | MR 测试执行情况 | Pipeline 对象 |
| `head_pipeline` | 最新 Pipeline | 最新测试结果 | Pipeline 对象 |
| `merge_status` | 合并状态 | 是否可合并 | `can_be_merged/cannot_be_merged` |
| `blocking_discussions_resolved` | 讨论是否解决 | 评审通过状态 | Boolean |

#### 5.3 MR 代码变更数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `changes_count` | 变更文件数 | 变更规模 | MR 对象 |
| `diff_refs` | Diff 引用 | 代码对比 | MR 对象 |
| `changes` | 详细变更 | 文件级变更 | `/api/v4/projects/:id/merge_requests/:mr_iid/changes` |

#### 5.4 MR 评审数据

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `approvals` | 批准信息 | 评审通过情况 | Approvals API |
| `approvals_required` | 需要批准数 | 评审规则 | Integer |
| `approvals_left` | 剩余批准数 | 评审进度 | Integer |
| `approved_by` | 批准人列表 | 评审参与者 | User 数组 |

______________________________________________________________________

### 6. Commits (代码提交)

Commit 是代码变更的基本单元，与测试密切相关。

#### 6.1 提交基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | Commit SHA | 提交标识 | `/api/v4/projects/:id/repository/commits` |
| `short_id` | 短 SHA | 提交简称 | 同上 |
| `title` | 提交标题 | 提交描述 | 同上 |
| `message` | 提交信息 | 完整描述 | 同上 |
| `author_name` | 作者姓名 | 提交人 | 同上 |
| `author_email` | 作者邮箱 | 提交人标识 | 同上 |
| `authored_date` | 创作时间 | 提交时间 | 同上 |
| `committed_date` | 提交时间 | 实际提交时间 | 同上 |

#### 6.2 提交统计数据

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `stats.additions` | 新增行数 | 代码增量 | Integer |
| `stats.deletions` | 删除行数 | 代码删减 | Integer |
| `stats.total` | 总变更行数 | 变更规模 | Integer |

#### 6.3 提交关联数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `last_pipeline` | 最后的 Pipeline | 提交测试结果 | Commit 对象 |
| `status` | 提交状态 | 测试状态 | `success/failed/running` |

______________________________________________________________________

### 7. Deployments (部署记录)

部署记录用于追踪测试环境和生产环境的发布情况。

#### 7.1 部署基础数据

| 数据字段 | 字段说明 | 度量用途 | API 端点 |
|---------|---------|---------|----------|
| `id` | 部署 ID | 部署标识 | `/api/v4/projects/:id/deployments` |
| `iid` | 项目内序号 | 部署编号 | 同上 |
| `ref` | 分支/标签 | 部署版本 | 同上 |
| `sha` | Commit SHA | 代码版本 | 同上 |
| `environment` | 环境名称 | 部署环境 | `test/staging/production` |
| `status` | 部署状态 | 部署结果 | `created/running/success/failed/canceled` |
| `created_at` | 创建时间 | 部署开始时间 | 同上 |
| `updated_at` | 更新时间 | 部署结束时间 | 同上 |

#### 7.2 部署关联数据

| 数据字段 | 字段说明 | 度量用途 | 备注 |
|---------|---------|---------|------|
| `deployable` | 关联的 Job | 部署任务 | Job 对象 |
| `user` | 部署人 | 部署责任人 | User 对象 |

______________________________________________________________________

## 关键指标度量维度

基于上述数据源，可以构建以下关键指标度量体系：

### 1. 需求管理指标

#### 1.1 需求交付效率

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **需求交付周期** | `closed_at - created_at` | Issues | 衡量需求响应速度 |
| **需求吞吐量** | 单位时间内关闭的 Issue 数 | Issues | 衡量团队产能 |
| **需求完成率** | `closed_issues / total_issues * 100%` | Issues, Milestones | 衡量版本进度 |
| **需求变更率** | 需求变更次数 / 总需求数 | Issues (updated_at) | 衡量需求稳定性 |

#### 1.2 需求质量指标

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **需求缺陷率** | 缺陷类 Issue / 总 Issue | Issues (labels) | 衡量需求质量 |
| **需求返工率** | 重新打开的 Issue / 总 Issue | Issues (state history) | 衡量需求准确性 |
| **需求评审覆盖率** | 有评论的 Issue / 总 Issue | Issues (user_notes_count) | 衡量评审质量 |

#### 1.3 需求工时指标

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **工时估算准确率** | `1 - abs(time_spent - time_estimate) / time_estimate` | Issues (time_stats) | 衡量估算能力 |
| **需求平均工时** | `sum(time_spent) / count(issues)` | Issues (time_stats) | 衡量需求复杂度 |

______________________________________________________________________

### 2. 测试管理指标

#### 2.1 测试执行效率

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **测试通过率** | `success_pipelines / total_pipelines * 100%` | Pipelines | 衡量代码质量 |
| **测试执行时长** | `avg(pipeline.duration)` | Pipelines | 衡量测试效率 |
| **测试频率** | 单位时间内的 Pipeline 执行次数 | Pipelines | 衡量 CI/CD 活跃度 |
| **首次测试通过率** | 首次提交即通过的 Pipeline / 总 Pipeline | Pipelines, Commits | 衡量代码质量 |

#### 2.2 测试覆盖度指标

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **代码覆盖率** | `pipeline.coverage` | Pipelines | 衡量测试完整性 |
| **覆盖率趋势** | 覆盖率随时间的变化 | Pipelines (时间序列) | 衡量测试改进 |
| **分支覆盖率** | 不同分支的覆盖率 | Pipelines (ref) | 衡量分支质量 |

#### 2.3 测试质量指标

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **测试用例数** | `test_report.total_count` | Test Reports | 衡量测试规模 |
| **测试用例通过率** | `success_count / total_count * 100%` | Test Reports | 衡量测试质量 |
| **测试失败率** | `failed_count / total_count * 100%` | Test Reports | 识别问题区域 |
| **测试稳定性** | 连续通过的 Pipeline 数 | Pipelines | 衡量测试可靠性 |

#### 2.4 缺陷管理指标

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **缺陷密度** | 缺陷数 / 代码行数 | Issues (labels=bug), Commits (stats) | 衡量代码质量 |
| **缺陷修复周期** | `closed_at - created_at` (bug issues) | Issues | 衡量响应速度 |
| **缺陷逃逸率** | `bug-source::production / total bugs * 100%` | Issues (bug-source label) | 衡量测试有效性 |
| **缺陷重开率** | 重新打开的缺陷 / 总缺陷 | Issues (state history) | 衡量修复质量 |
| **按来源分布** | 生产环境 vs 非生产环境 Bug 数 | Issues (bug-source label) | 识别测试盲区 |

______________________________________________________________________

### 3. 需求-测试追溯指标

#### 3.1 追溯完整性

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **需求-代码追溯率** | 有关联 MR 的 Issue / 总 Issue | Issues, MergeRequests | 衡量追溯完整性 |
| **需求-测试追溯率** | 有测试覆盖的 Issue / 总 Issue | Issues, Pipelines (via MR) | 衡量测试覆盖 |
| **代码-测试追溯率** | 有 Pipeline 的 Commit / 总 Commit | Commits, Pipelines | 衡量 CI 覆盖 |

#### 3.2 质量门禁指标

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **MR 测试通过率** | 测试通过的 MR / 总 MR | MergeRequests, Pipelines | 衡量合并质量 |
| **MR 评审通过率** | 评审通过的 MR / 总 MR | MergeRequests (approvals) | 衡量评审质量 |
| **直接推送率** | 绕过 MR 的 Commit / 总 Commit | Commits, MergeRequests | 识别流程违规 |

______________________________________________________________________

### 4. DORA 指标 (DevOps 效能)

| 指标名称 | 计算公式 | 数据来源 | 业务价值 |
|---------|---------|---------|---------|
| **部署频率** | 单位时间内的部署次数 | Deployments | 衡量交付速度 |
| **变更前置时间** | `deployment.created_at - commit.authored_date` | Deployments, Commits | 衡量交付效率 |
| **变更失败率** | 失败的部署 / 总部署 | Deployments (status=failed) | 衡量变更质量 |
| **服务恢复时间** | 从失败到恢复的时间 | Deployments, Issues | 衡量恢复能力 |

______________________________________________________________________

## 数据采集方案

### 1. GitLab API 数据采集

#### 1.1 API 认证方式

```bash
# Personal Access Token (推荐)
curl --header "PRIVATE-TOKEN: <your_access_token>" "https://gitlab.example.com/api/v4/projects"

# OAuth2 Token
curl --header "Authorization: Bearer <oauth_token>" "https://gitlab.example.com/api/v4/projects"

# Job Token (CI/CD 内部)
curl --header "JOB-TOKEN: <job_token>" "https://gitlab.example.com/api/v4/projects"
```

#### 1.2 分页处理

```python
import requests

def get_all_pages(url, headers, params=None):
    """获取所有分页数据"""
    all_data = []
    page = 1
    per_page = 100  # 每页最多 100 条
    
    while True:
        params = params or {}
        params.update({'page': page, 'per_page': per_page})
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            break
            
        all_data.extend(data)
        
        # 检查是否还有下一页
        if 'x-next-page' not in response.headers or not response.headers['x-next-page']:
            break
            
        page += 1
    
    return all_data
```

#### 1.3 增量同步策略

```python
from datetime import datetime, timedelta

def sync_issues_incremental(project_id, last_sync_time):
    """增量同步 Issues"""
    url = f"https://gitlab.example.com/api/v4/projects/{project_id}/issues"
    headers = {"PRIVATE-TOKEN": "your_token"}
    
    # 只获取上次同步后更新的数据
    params = {
        'updated_after': last_sync_time.isoformat(),
        'order_by': 'updated_at',
        'sort': 'asc'
    }
    
    return get_all_pages(url, headers, params)
```

______________________________________________________________________

### 2. 数据采集最佳实践

#### 2.1 采集频率建议

| 数据类型 | 建议频率 | 原因 |
|---------|---------|------|
| Issues | 每小时 | 需求变化频繁 |
| Milestones | 每天 | 版本规划变化较慢 |
| Pipelines | 实时 (Webhook) | 测试结果需要及时反馈 |
| Test Reports | 每次 Pipeline 完成后 | 与 Pipeline 同步 |
| Merge Requests | 每 15 分钟 | 代码评审活跃 |
| Commits | 每小时 | 代码提交频繁 |
| Deployments | 实时 (Webhook) | 部署事件重要 |

#### 2.2 Webhook 事件订阅

GitLab 支持通过 Webhook 实时推送事件，推荐订阅以下事件：

| 事件类型 | 用途 | Webhook URL |
|---------|------|------------|
| `Push Hook` | 代码提交事件 | `/webhooks/gitlab/push` |
| `Merge Request Hook` | MR 事件 | `/webhooks/gitlab/merge_request` |
| `Pipeline Hook` | Pipeline 事件 | `/webhooks/gitlab/pipeline` |
| `Job Hook` | Job 事件 | `/webhooks/gitlab/job` |
| `Issue Hook` | Issue 事件 | `/webhooks/gitlab/issue` |
| `Deployment Hook` | 部署事件 | `/webhooks/gitlab/deployment` |

#### 2.3 数据存储建议

```sql
-- 示例：Issues 表结构
CREATE TABLE gitlab_issues (
    id INTEGER PRIMARY KEY,
    iid INTEGER,
    project_id INTEGER,
    title VARCHAR(500),
    description TEXT,
    state VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    closed_at TIMESTAMP,
    author_id INTEGER,
    assignee_ids INTEGER[],
    labels JSONB,
    milestone_id INTEGER,
    time_estimate INTEGER,
    total_time_spent INTEGER,
    weight INTEGER,
    user_notes_count INTEGER,
    upvotes INTEGER,
    raw_data JSONB,  -- 存储完整 JSON 数据
    synced_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_issues_project_id ON gitlab_issues(project_id);
CREATE INDEX idx_issues_state ON gitlab_issues(state);
CREATE INDEX idx_issues_created_at ON gitlab_issues(created_at);
CREATE INDEX idx_issues_updated_at ON gitlab_issues(updated_at);
CREATE INDEX idx_issues_labels ON gitlab_issues USING GIN(labels);
```

______________________________________________________________________

### 3. 数据质量保障

#### 3.1 数据完整性检查

```python
def validate_issue_data(issue):
    """验证 Issue 数据完整性"""
    required_fields = ['id', 'iid', 'project_id', 'title', 'state', 'created_at']
    
    for field in required_fields:
        if field not in issue or issue[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # 验证状态枚举
    if issue['state'] not in ['opened', 'closed']:
        raise ValueError(f"Invalid state: {issue['state']}")
    
    return True
```

#### 3.2 数据一致性校验

```sql
-- 检查 Issue 与 MR 的关联一致性
SELECT 
    i.id AS issue_id,
    i.title AS issue_title,
    COUNT(DISTINCT mr.id) AS related_mr_count
FROM gitlab_issues i
LEFT JOIN gitlab_merge_requests mr ON mr.description LIKE '%#' || i.iid || '%'
WHERE i.state = 'closed'
GROUP BY i.id, i.title
HAVING COUNT(DISTINCT mr.id) = 0;  -- 找出没有关联 MR 的已关闭 Issue
```

______________________________________________________________________

## 最佳实践建议

### 1. 需求管理最佳实践

#### 1.1 标签规范

建议建立统一的标签体系，便于数据分类和度量：

| 标签类型 | 示例 | 用途 |
|---------|------|------|
| **需求类型** | `feature`, `bug`, `enhancement`, `task` | 需求分类 |
| **优先级** | `P0`, `P1`, `P2`, `P3` | 优先级管理 |
| **模块** | `backend`, `frontend`, `database`, `infra` | 模块归属 |
| **状态** | `in-progress`, `review`, `testing`, `blocked` | 工作流状态 |
| **版本** | `v1.0`, `v2.0` | 版本标记 |

#### 1.2 Issue 模板

使用 Issue 模板规范需求描述，确保数据结构化：

```markdown
## 需求描述
[清晰描述需求背景和目标]

## 验收标准
- [ ] 标准 1
- [ ] 标准 2
- [ ] 标准 3

## 工作量估算
预估工时: [X] 小时

## 相关链接
- 设计文档: [链接]
- 原型图: [链接]
```

#### 1.3 里程碑规划

- 每个迭代/版本创建独立的 Milestone
- 设置明确的 `start_date` 和 `due_date`
- 定期审查 Milestone 进度

______________________________________________________________________

### 2. 测试管理最佳实践

#### 2.1 CI/CD 配置规范

```yaml
# .gitlab-ci.yml 示例
stages:
  - test
  - integration
  - deploy

# 单元测试
unit-test:
  stage: test
  script:
    - pytest tests/unit --cov=src --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      junit: test-results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# 集成测试
integration-test:
  stage: integration
  script:
    - pytest tests/integration --junitxml=integration-results.xml
  artifacts:
    reports:
      junit: integration-results.xml
```

#### 2.2 测试报告规范

- 使用 JUnit XML 格式输出测试结果
- 使用 Cobertura XML 格式输出覆盖率报告
- 在 MR 中自动展示测试结果和覆盖率变化

#### 2.3 质量门禁设置

在项目设置中配置质量门禁：

- **Pipeline 必须成功**: MR 合并前 Pipeline 必须通过
- **代码覆盖率阈值**: 例如不低于 80%
- **必须评审**: 至少 1 人批准
- **讨论必须解决**: 所有讨论必须标记为已解决

______________________________________________________________________

### 3. 数据追溯最佳实践

#### 3.1 需求-代码关联

在 Commit Message 和 MR 描述中引用 Issue：

```bash
# Commit Message
git commit -m "feat: 实现用户登录功能 #123"

# MR 描述
Closes #123
Related to #124, #125
```

GitLab 会自动建立关联关系。

#### 3.2 测试-需求关联

在测试用例中标记关联的需求：

```python
import pytest

@pytest.mark.issue("123")
def test_user_login():
    """测试用户登录功能 - 关联 Issue #123"""
    # 测试代码
    pass
```

#### 3.3 部署-需求关联

在部署时记录关联的需求和 MR：

```yaml
deploy-production:
  stage: deploy
  script:
    - echo "Deploying MR !456, Issue #123"
    - ./deploy.sh
  environment:
    name: production
```

______________________________________________________________________

### 4. 指标度量最佳实践

#### 4.1 建立基线

在开始度量前，先建立基线数据：

```sql
-- 计算过去 3 个月的基线数据
SELECT 
    AVG(EXTRACT(EPOCH FROM (closed_at - created_at)) / 3600) AS avg_issue_cycle_hours,
    AVG(time_estimate) AS avg_time_estimate,
    AVG(total_time_spent) AS avg_time_spent,
    COUNT(*) AS total_issues
FROM gitlab_issues
WHERE created_at >= NOW() - INTERVAL '3 months'
  AND state = 'closed';
```

#### 4.2 定期监控

建议建立定期监控机制：

- **每日**: 测试通过率、部署频率
- **每周**: 需求完成率、代码覆盖率
- **每月**: 需求交付周期、缺陷密度
- **每季度**: DORA 指标、团队效能趋势

#### 4.3 可视化展示

使用 BI 工具（如 Grafana, Tableau, Looker）可视化指标：

```sql
-- 示例：需求交付周期趋势
SELECT 
    DATE_TRUNC('week', closed_at) AS week,
    AVG(EXTRACT(EPOCH FROM (closed_at - created_at)) / 86400) AS avg_cycle_days,
    COUNT(*) AS closed_count
FROM gitlab_issues
WHERE state = 'closed'
  AND closed_at >= NOW() - INTERVAL '6 months'
GROUP BY week
ORDER BY week;
```

______________________________________________________________________

## 附录

### A. GitLab API 参考

| API 类别 | 端点示例 | 文档链接 |
|---------|---------|---------|
| Projects | `/api/v4/projects` | [Projects API](https://docs.gitlab.com/ee/api/projects.html) |
| Issues | `/api/v4/projects/:id/issues` | [Issues API](https://docs.gitlab.com/ee/api/issues.html) |
| Merge Requests | `/api/v4/projects/:id/merge_requests` | [MR API](https://docs.gitlab.com/ee/api/merge_requests.html) |
| Pipelines | `/api/v4/projects/:id/pipelines` | [Pipelines API](https://docs.gitlab.com/ee/api/pipelines.html) |
| Jobs | `/api/v4/projects/:id/jobs` | [Jobs API](https://docs.gitlab.com/ee/api/jobs.html) |
| Commits | `/api/v4/projects/:id/repository/commits` | [Commits API](https://docs.gitlab.com/ee/api/commits.html) |
| Deployments | `/api/v4/projects/:id/deployments` | [Deployments API](https://docs.gitlab.com/ee/api/deployments.html) |
| Milestones | `/api/v4/projects/:id/milestones` | [Milestones API](https://docs.gitlab.com/ee/api/milestones.html) |
| Requirements | `/api/v4/projects/:id/requirements` | [Requirements API](https://docs.gitlab.com/ee/api/requirements.html) |

### B. 数据采集工具推荐

| 工具名称 | 类型 | 特点 | 适用场景 |
|---------|------|------|---------|
| **GitLab API** | 官方 API | 功能完整、文档详细 | 所有场景 |
| **python-gitlab** | Python SDK | 易用、支持分页 | Python 项目 |
| **GitLab Runner** | CI/CD | 内置集成 | CI/CD 内部 |
| **Webhook** | 事件推送 | 实时性强 | 实时监控 |
| **GraphQL API** | 现代 API | 灵活查询、减少请求 | 复杂查询 |

### C. 相关资源

- [GitLab API 文档](https://docs.gitlab.com/ee/api/)
- [GitLab CI/CD 文档](https://docs.gitlab.com/ee/ci/)
- [GitLab Webhooks 文档](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [DORA Metrics 指南](https://docs.gitlab.com/ee/user/analytics/dora_metrics.html)

______________________________________________________________________

## 总结

GitLab 提供了丰富的数据源，可以支持需求管理和测试管理的全方位度量。通过合理利用这些数据，可以构建完整的效能度量体系，帮助团队持续改进。

**关键要点**:

1. **需求管理**: 以 Issues、Milestones、Epics 为核心，追踪需求全生命周期
1. **测试管理**: 以 Pipelines、Jobs、Test Reports 为核心，监控测试执行和质量
1. **数据追溯**: 通过 MR、Commits、Deployments 建立需求-代码-测试-部署的完整追溯链
1. **指标度量**: 基于 DORA 指标和自定义指标，建立多维度的效能度量体系
1. **最佳实践**: 规范化的标签、模板、CI/CD 配置是数据质量的基础

______________________________________________________________________

## 🚀 快速开始指南

### Step 1: 了解数据源

阅读本文档的[需求管理数据源](#%E9%9C%80%E6%B1%82%E7%AE%A1%E7%90%86%E6%95%B0%E6%8D%AE%E6%BA%90)和[测试管理数据源](#%E6%B5%8B%E8%AF%95%E7%AE%A1%E7%90%86%E6%95%B0%E6%8D%AE%E6%BA%90)章节，了解 GitLab 能提供哪些数据。

### Step 2: 建立标签体系

使用项目提供的批量创建工具在 GitLab 中创建标准化标签：

```bash
# 1. 预览将要创建的标签
python scripts/create_gitlab_labels.py --group-id <your_group_id> --dry-run

# 2. 实际创建标签（推荐群组级，可跨项目共享）
python scripts/create_gitlab_labels.py --group-id <your_group_id>

# 3. 或为单个项目创建
python scripts/create_gitlab_labels.py --project-id <your_project_id>
```

### Step 3: 制定 Issue 模板

在项目中创建 Issue 模板，引导团队正确标记：

**Bug 报告模板** (`.gitlab/issue_templates/Bug.md`):

```markdown
## Bug 描述
[清晰描述 Bug 的现象]

## 复现步骤
1. 步骤 1
2. 步骤 2
3. 步骤 3

## 预期行为 vs 实际行为
- 预期: [描述预期的正确行为]
- 实际: [描述实际发生的错误行为]

## 环境信息
- 操作系统: [例如: Windows 10]
- 浏览器: [例如: Chrome 120]
- 版本: [例如: v1.2.3]

## 严重程度与优先级
- [ ] `severity::S1` - 致命（系统崩溃、数据丢失）
- [ ] `severity::S2` - 严重（核心功能不可用）
- [ ] `severity::S3` - 一般（功能异常，有替代方案）
- [ ] `severity::S4` - 轻微（UI问题、文案错误）

- [ ] `priority::P0` - 紧急（立即处理）
- [ ] `priority::P1` - 高（1-2天内）
- [ ] `priority::P2` - 中（1周内）
- [ ] `priority::P3` - 低（下个迭代）

## Bug 类别
- [ ] `bug-category::test-script` - 测试脚本
- [ ] `bug-category::code-error` - 代码错误
- [ ] `bug-category::configuration` - 配置相关
- [ ] `bug-category::design-defect` - 设计缺陷
- [ ] `bug-category::deployment` - 安装部署
- [ ] `bug-category::performance` - 性能问题
- [ ] `bug-category::security` - 安全相关
- [ ] `bug-category::standard` - 标准规范
- [ ] `bug-category::other` - 其他

---
**建议标签**: `type::bug`, `severity::S?`, `priority::P?`, `bug-category::?`
```

**完整的 Bug 报告模板已创建**: `.gitlab/issue_templates/Bug.md`

**功能需求模板** (`.gitlab/issue_templates/Feature.md`):

```markdown
## 需求背景
[描述为什么需要这个功能]

## 需求描述
[清晰描述功能需求]

## 用户故事
作为 [角色]，我希望 [功能]，以便 [价值]。

## 验收标准
- [ ] 标准 1
- [ ] 标准 2
- [ ] 标准 3

## 优先级评估
- [ ] `priority::P0` - 紧急（核心功能，立即开发）
- [ ] `priority::P1` - 高（重要功能，优先开发）
- [ ] `priority::P2` - 中（一般功能，计划开发）
- [ ] `priority::P3` - 低（次要功能，可延后）

## 工作量估算
预估工时: [X] 小时 / 故事点: [Y]

---
**建议标签**: `type::feature`, `priority::P?`
```

### Step 4: 配置质量门禁

在 GitLab 项目设置中配置：

1. **Settings → Merge requests**

   - ✅ Pipelines must succeed
   - ✅ All discussions must be resolved
   - ✅ Require approval from code owners

1. **Settings → CI/CD → General pipelines**

   - 设置覆盖率阈值（例如: 80%）

### Step 5: 开始数据采集

使用现有的 `devops_collector` 系统采集 GitLab 数据：

```bash
# 初始化系统
python scripts/init_discovery.py

# 启动调度器
python -m devops_collector.scheduler

# 启动 Worker 执行采集
python -m devops_collector.worker
```

### Step 6: 构建指标度量

基于采集的数据，创建 SQL 视图和报表。参考[关键指标度量维度](#%E5%85%B3%E9%94%AE%E6%8C%87%E6%A0%87%E5%BA%A6%E9%87%8F%E7%BB%B4%E5%BA%A6)章节。

______________________________________________________________________

## ❓ 常见问题解答

### Q1: 为什么使用 Scoped Labels？

**A**: Scoped Labels (格式: `key::value`) 提供了互斥性保证，同一个 Issue 只能有一个相同 key 的标签。例如，添加 `type::bug` 会自动移除 `type::feature`，避免分类混乱，便于数据统计和分析。

### Q2: 优先级和严重程度有什么区别？

**A**:

- **严重程度 (Severity)**: 技术视角，描述 Bug 对系统的影响程度（S1~S4），仅用于 Bug
- **优先级 (Priority)**: 业务视角，描述修复/开发的紧急程度（P0~P3），适用于所有类型

两者是独立维度。例如：

- **高严重度 + 低优先级**: S2 的 Bug，但影响即将下线的功能 → `severity::S2` + `priority::P3`
- **低严重度 + 高优先级**: S4 的 UI 问题，但客户强烈要求修复 → `severity::S4` + `priority::P1`

### Q3: 需求也需要标记严重程度吗？

**A**: 不需要。严重程度 (Severity) 仅用于 Bug。需求只需要标记类型 (`type::feature`) 和优先级 (`priority::P?`)。

### Q4: 如何确保团队成员正确标记 Issue？

**A**:

1. **使用 Issue 模板**: 提供标记指南和选项
1. **定期数据质量检查**: 使用 SQL 查询找出未分类的 Issue
1. **团队培训**: 在团队内部宣导标签规范
1. **自动化辅助**: 使用 Webhook 根据标题自动添加标签

```sql
-- 查找没有类型标签的 Issue
SELECT id, iid, title, labels
FROM gitlab_issues
WHERE NOT (labels::text LIKE '%type::%')
AND state = 'opened';
```

### Q5: 标签应该创建在群组级还是项目级？

**A**:

- **群组级标签** (推荐): 用于通用分类（type, priority, severity, status），确保多项目一致性，便于跨项目统计
- **项目级标签**: 用于项目特有的分类（特定模块、特定功能）

### Q6: 如何统计各类型 Issue 的数量？

**A**: 使用 SQL 查询或 GitLab API：

```sql
-- SQL 查询示例
SELECT 
    CASE 
        WHEN labels::text LIKE '%type::feature%' THEN 'feature'
        WHEN labels::text LIKE '%type::bug%' THEN 'bug'
        WHEN labels::text LIKE '%type::enhancement%' THEN 'enhancement'
        ELSE 'other'
    END AS issue_type,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM gitlab_issues
GROUP BY issue_type;
```

```python
# Python API 示例
def get_issues_by_type(project_id, issue_type):
    """获取指定类型的 Issues"""
    url = f"https://gitlab.example.com/api/v4/projects/{project_id}/issues"
    headers = {"PRIVATE-TOKEN": "your_token"}
    params = {"labels": f"type::{issue_type}"}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# 获取所有 Bug
bugs = get_issues_by_type(project_id, "bug")
```

### Q7: 如何度量需求交付周期？

**A**: 使用 Issue 的 `created_at` 和 `closed_at` 字段：

```sql
-- 需求交付周期（按优先级）
SELECT 
    CASE 
        WHEN labels::text LIKE '%priority::P0%' THEN 'P0'
        WHEN labels::text LIKE '%priority::P1%' THEN 'P1'
        WHEN labels::text LIKE '%priority::P2%' THEN 'P2'
        WHEN labels::text LIKE '%priority::P3%' THEN 'P3'
    END AS priority,
    AVG(EXTRACT(EPOCH FROM (closed_at - created_at)) / 86400) AS avg_cycle_days,
    COUNT(*) AS count
FROM gitlab_issues
WHERE labels::text LIKE '%type::feature%'
  AND state = 'closed'
  AND closed_at IS NOT NULL
GROUP BY priority
ORDER BY priority;
```

### Q8: 如何追踪需求到代码的关联？

**A**: 在 Commit Message 和 MR 描述中引用 Issue：

```bash
# Commit Message
git commit -m "feat: 实现用户登录功能 #123"

# MR 描述
Closes #123
Related to #124, #125
```

GitLab 会自动建立关联关系，可通过 API 查询：

```python
# 获取 Issue 关联的 MR
url = f"/api/v4/projects/{project_id}/issues/{issue_iid}/related_merge_requests"
```

______________________________________________________________________

## 📊 核心概念速查表

### Issue 类型分类

| 类型 | 标签 | 说明 | 颜色 |
|------|------|------|------|
| 功能需求 | `type::feature` | 新功能开发 | 🟦 `#428BCA` |
| 缺陷 | `type::bug` | 软件缺陷修复 | 🟥 `#D9534F` |
| 测试用例 | `type::test` | 模拟测试管理 | 🟫 `#795548` |

### 优先级定义

| 优先级 | 标签 | 处理时效 | 影响范围 | 业务影响 |
|--------|------|---------|---------|---------|
| P0 | `priority::P0` | 立即处理 (4小时内) | 所有用户 | 核心业务中断 |
| P1 | `priority::P1` | 1-2天内 | 大部分用户 | 重要功能受限 |
| P2 | `priority::P2` | 1周内 | 部分用户 | 一般功能受限 |
| P3 | `priority::P3` | 下个迭代 | 个别用户 | 体验优化 |

### 严重程度定义 (仅 Bug)

| 严重程度 | 标签 | 系统可用性 | 数据完整性 | 典型场景 |
|---------|------|-----------|-----------|---------|
| S1 | `severity::S1` | 系统不可用 | 数据丢失/损坏 | 生产环境宕机、数据泄露 |
| S2 | `severity::S2` | 核心功能不可用 | 数据错误 | 登录失败、支付失败 |
| S3 | `severity::S3` | 部分功能不可用 | 数据显示异常 | 页面显示错误、性能下降 |
| S4 | `severity::S4` | 功能可用 | 无影响 | 按钮错位、提示语错误 |

### Bug 类别定义 (仅 Bug)

| Bug 类别 | 标签 | 说明 | 典型场景 |
|---------|------|------|---------|
| 测试脚本 | `bug-category::test-script` | 测试脚本问题 | 测试用例断言错误、Mock 数据不正确 |
| 代码错误 | `bug-category::code-error` | 代码逻辑错误 | 空指针异常、条件判断错误 |
| 配置相关 | `bug-category::configuration` | 配置问题 | 数据库连接配置错误、超时参数不当 |
| 设计缺陷 | `bug-category::design-defect` | 设计层面问题 | API 接口设计不合理、数据模型缺陷 |
| 安装部署 | `bug-category::deployment` | 部署问题 | Docker 镜像构建失败、依赖包冲突 |
| 性能问题 | `bug-category::performance` | 性能指标不达标 | 接口响应慢、内存泄漏 |
| 安全相关 | `bug-category::security` | 安全漏洞 | SQL 注入、XSS、权限漏洞 |
| 标准规范 | `bug-category::standard` | 不符合规范 | 代码不符合规范、文档缺失 |
| 其他 | `bug-category::other` | 其他问题 | 无法明确分类的问题 |

### 数据采集频率建议

| 数据类型 | 建议频率 | 采集方式 | 原因 |
|---------|---------|---------|------|
| Issues | 每小时 | API 增量同步 | 需求变化频繁 |
| Milestones | 每天 | API 全量同步 | 版本规划变化较慢 |
| Pipelines | 实时 | Webhook | 测试结果需要及时反馈 |
| Test Reports | Pipeline 完成后 | API | 与 Pipeline 同步 |
| Merge Requests | 每 15 分钟 | API 增量同步 | 代码评审活跃 |
| Commits | 每小时 | API 增量同步 | 代码提交频繁 |
| Deployments | 实时 | Webhook | 部署事件重要 |

### 关键指标公式

| 指标 | 公式 | 数据来源 |
|------|------|---------|
| 需求交付周期 | `closed_at - created_at` | Issues |
| 需求完成率 | `closed_issues / total_issues * 100%` | Issues, Milestones |
| 测试通过率 | `success_pipelines / total_pipelines * 100%` | Pipelines |
| 代码覆盖率 | `pipeline.coverage` | Pipelines |
| 缺陷密度 | `缺陷数 / 代码行数` | Issues (labels=bug), Commits |
| Bug 修复周期 | `closed_at - created_at` (bug issues) | Issues |
| 部署频率 | 单位时间内的部署次数 | Deployments |
| 变更前置时间 | `deployment.created_at - commit.authored_date` | Deployments, Commits |

______________________________________________________________________

**文档维护**: 本文档应随 GitLab 版本更新和团队实践演进而持续更新。

**反馈与建议**: 如有任何问题或建议，请通过 Issue 或 MR 反馈。
