# 采集插件与多源集成详解 (Collector Plugins & Integrations)

DevOps Data Collector 采用插件化架构，支持通过 `BaseWorker` 快速扩展。目前已集成以下核心数据源：

## 1. 代码与协作 (GitLab)

- **全量元数据**: 同步项目、组、成员等基础信息。
- **代码提交 (Commits)**:
  - 采集 Commit 信息（作者、时间、Message）。
  - **深度 Diff 分析**: 自动拆解代码变更，区分有效代码行、注释行和空行。
- **合并请求 (Merge Requests)**: 记录状态、评审人、合并时间。自动计算 **评审轮次 (Review Cycles)** 和 **评审影响力**。
- **流水线与算力能效 (CI/CD FinOps) [NEW]**:
  - **算力成本采集**: 细化采集 `GitLabPipeline` 与 `GitLabJob`，追踪纯算力执行耗时 (Compute Duration) 与 Runner 排队时长 (Queue Time)。
  - **效能度量**: 自动计算单元测试覆盖率、Runner 利用率及由于资源竞争导致的“研发等待浪费”。
  - **血缘追踪**: 建立 `Pipeline -> Commit -> User` 的全链路追溯。
- **CALMS 深度扫描**: 追踪 Issue 的 `State/Label/Milestone` 原子事件，量化“等待浪费”与组织文化。
  *(Updated: 2026-05-03 by /doc-update)*

## 2. 代码质量 (SonarQube)

- **自动映射**: 基于项目路径规则自动关联 GitLab 项目。
- **质量快照**: 周期性拉取代码覆盖率 (Coverage)、技术债务 (Tech Debt)、Bug 数等。
- **Issue 同步**: 支持同步具体的代码异味、Bug 和漏洞详情。

## 3. 持续集成 (Jenkins)

- **任务发现**: 自动同步 Jenkins 实例中的所有 Job。
- **构建历史**: 识别构建触发源（SCM、用户、定时任务）。
- **血缘建立**: 自动通过 Job 名称匹配 GitLab 项目路径。

## 4. 敏捷管理 (Jira & 禅道)

- **Jira**: 完整拉取项目、看板、迭代和问题。记录状态流转过程（Changelog），支持计算周期时间 (Cycle Time)。
- **禅道 (ZenTao)**: 采集产品、计划、需求和执行。将复杂层级映射为统一的 Issue 模型。

## 5. 制品库 (Nexus & JFrog)

- **Nexus**: 自动同步组件与资产，记录校验和。
- **JFrog Artifactory**: 基于 AQL 采集制品元数据，同步 Xray 安全扫描摘要。提取 `build.name` 实现制品到构建任务的追溯。

## 6. 财务系统集成 (FinOps Integration) 🌟

- **成本科目 (CBS)**: 建立财务级的成本拆解树。
- **合同管理**: 记录支出与收入合同，支持线性摊销。
- **里程碑对齐**: 将合同回款节点与 GitLab Milestone 挂钩。

## 7. 安全扫描 (Dependency-Check)

- **组件普查**: 扫描开源依赖及其许可证。详见 [SECURITY_SCAN.md](../guides/SECURITY_SCAN.md)。
