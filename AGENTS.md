# DevOps Platform 机器人协作守则 (AGENTS.md)

> **定位声明**：本文件是 DevOps Platform 项目的 **Meta-Prompt（AI 全局调度中心）**。
> 所有 AI 助手（antigravity, Cursor, Claude 等）在进入本项目时**必须**首先加载并以此作为任务指令的唯一入口。
> 
> **继承优先级**：`contexts.md` (技术标准) > 本文件 (行为调度) > `gemini.md` (全局哲学)。

## 1. 规则继承 (Inheritance)
AI 助手在本项目的所有行为均继承自全局协作规范。**[MANDATORY]**
*   **底座**：遵循 [`~/.gemini/gemini.md`](c:/users/netxs/.gemini/gemini.md) 定义的“物理真实性”、“意图语义锚点”及“小白解说”逻辑。
*   **宪法**：执行 [`contexts.md`](contexts.md) 定义的技术架构标准与开发红线。

## 2. 指令调度层 (The Dispatcher)
AI 助手必须通过调用 `.agent/workflows/` 下的原子流程来驱动任务执行。

| 指令 (Slash Command) | 触发时机 | 动作目标 | 执行流程文件 |
| :--- | :--- | :--- | :--- |
| **`/task-kickoff`** | 接收并处理新任务 | 任务定级 [L1-L4]、风险预判与逻辑切片 | `task-kickoff.md` |
| **`/spike`** | 任务涉及未知领域/探索 | **[探针]**：4h Timebox 调研并产出的结论 | `spike.md` |
| **`/evolve-skill`** | 产生新的教训/知识 | **[自进化]**：将教训转化为自动化审计能力 | `evolve-skill.md` |
| **`/rollback`** | 执行 L3/L4/DB 变更前 | **[安全]**：生成应急恢复清单与 Git Tag | `rollback.md` |
| **`/plugin-init`** | 需要接入新数据源 | **[工厂]**：5 分钟内初始化插件四层骨架 | `plugin-init.md` |
| **`/bug-triage`** | 处理缺陷/失败用例 | **[排错]**：复现 -> 归因 -> TDD 隔离修复 | `bug-triage.md` |
| **`/doc-update`** | 产生逻辑变更或完工 | **[同步]**：更新 progress/contexts 等文档 (SSOT) | `doc-update.md` |
| **`/code-review`** | 交付前质量校验 | **[审计]**：业务域命名审计与代码质量检查 | `code-review.md` |
| **`/lint`** | 编码中途或 L1 交付前 | **[自查]**：静默修复 Ruff 与 Format 问题 | `lint.md` |
| **`/merge`** | 分支合入 main 前 | **[准入]**：检查 Rebase、容器测试与部署 | `merge.md` |
| **`/deploy`** | 准备发布至生产 | **[交付]**：数据库备份 + 滚动更新 + 健康探针 | `deploy.md` |
| **`/session-handover`** | 准备关闭会话 | **[交接]**：物理真实取证、审计与状态落盘 | `session-handover.md` |

## 2.1 意图与语义锚点 (Intent Mapping) [NEW]
当用户发出以下自然语言指令时，Agent **必须强制执行** 对应的原子工作流，不得仅以纯文本回复：

*   **指令**: `"下班了"`, `"我要走了"`, `"今天先到这"`
    *   **映射动作**: 执行 **`/session-handover`**。
    *   **核心要求**: 必须依照 `session-handover.md` 完成五项 DoD（含 `session-history.log` 与 `lessons-learned.log` 落盘）。
    *   **歧义阈值 [NEW]**: 若触发语义模糊度 > 20%（如"该收摊了吧"、"差不多了"），**优先执行** `gemini.md` 的反向确认机制，向用户提供结构化选项确认意图，不得盲目触发工作流。
*   **指令**: `"开始工作"`, `"刚收网/刚收摊"` (或其他恢复语境)
    *   **映射动作**: 执行 **`/session-handover` (Part A: Bootstrap)**。
    *   **核心要求**: 必须读取 `progress.txt`并输出会话恢复摘要。
    *   **歧义阈值 [NEW]**: 同上，语义模糊度 > 20% 时先确认再执行。

## 2.2 专家技能链协作矩阵 (Expert Skill Chaining) [NEW]
为实现自动化审计闭环，Agent 在执行特定指令时必须按以下链路触发技能联动：

| 触发场景 | 主导指令 / Skill | 随动联动 (Chain To) | 自动化目标 |
| :--- | :--- | :--- | :--- |
| **高危重构/变更** | `/task-kickoff` (L3/L4) | `chaos-sentinel` | 在开发前注入仿真故障，验证防御逻辑是否在预案中。 |
| **模型/Schema 变更**| `mdm-integrity-arbiter`| `/rollback` | Arbiter 审计通过后，**强制自动生成** 一键回滚 SQL。 |
| **Pipeline 全链路修复**| `dbt-pipeline-auditor` | `webapp-testing` | dbt 脚本修复后，自动通过 Playwright 验证 Portal 看板指标是否恢复。 |
| **新坑位发现** | `lessons-learned.log` | `skill-creator` | 每当产生 Blocker 级教训，强制触发技能重构，将坑位转化为自动化用例。 |

## 3. 技术标准锚点 (Technical Anchors)
当执行涉及以下具体领域的任务时，AI 必须动态锚定并重读 `contexts.md` 的对应章节：

*   **编码原则 (Engineering Principles)** ➜ 查阅 [`contexts.md#1.5`](contexts.md#L12) (四大 AI 原生编码原则)。
*   **数据模型 (DB/Schema)** ➜ 查阅 [`contexts.md#5`](contexts.md#L91) (Surrogate PK 与两阶段对齐协议)。
*   **前端设计 (UI/CSS)** ➜ 查阅 [`contexts.md#6`](contexts.md#L153) (Apple Style 组件变量约定)。
*   **命名规范 (Naming)** ➜ 查阅 [`contexts.md#11`](contexts.md#L323) (业务域前缀注册表)。
*   **集成测试 (Testing)** ➜ 查阅 [`contexts.md#9.5`](contexts.md#L270) (本地与容器化测试分工红线)。

## 3.1 专家技能挂载 (Expert Skill Anchors) [NEW]
当任务涉及以下深度技术域时，Agent **必须首先激活** 对应的 Skill 进行前置审计：

*   **dbt 模型评审 (SQL Audit)** ➜ 激活 `dbt-pipeline-auditor` (执行五大防线检查)。
*   **MDM 建模/Schema 变更** ➜ 激活 `mdm-integrity-arbiter` (检查 ORM 关联与双重对齐协议)。
*   **测试隔离、独立脚本规范与事务嵌套审查** ➜ 激活 `engineering-rigor-arbiter` (排查测试依赖污染、方言冲突与游离态并发缺陷)。
*   **韧性验证/高危变更验证** ➜ 激活 `chaos-sentinel` (注入物理故障验证防御代码)。

## 4. 物理红线 (The Physical Redlines) [MANDATORY]
1.  **终极验证律 (The Law of Verify)**：所有 L2 及以上任务完成前，**必须执行** `make verify`。
    - **硬性标准**：严格依据 `contexts.md` 第9章要求（核心模块 >= 80%, 插件层 >= 60%），不达标严禁交付。
    - **操作要求**：必须在回复中粘贴 `make verify` 的终端输出日志碎片，作为物理取证。
    - **仲裁规则 [NEW]**：「最小改动」原则**不豁免**覆盖率要求。若改动模块的历史覆盖率不足 80%，必须补充对应测试至达标后方可交付，即使补测范围超出本次改动的最小边界。
2.  **指令校验律 (The Law of Command Validation) [NEW]**: 
    - 凡涉及修改 `Makefile`、`Dockerfile`、`CI` 脚本或引入新的 CLI 工具指令，**严禁**凭记忆编写。
    - **强制要求**: 必须首先在终端执行 `[command] --help` 进行物理取证，确保参数 100% 正确后方可写入。
    - **静默预检 (Pre-flight Check)**: 指令写入后，在向用户反馈前，建议执行该指令的 `--dry-run` 模式（如果支持）或简单的语法探测，确保“所见即所得”，严防部署崩溃。
3.  **容器强制验证**：所有涉及后端逻辑的变更必须通过容器内测试验证。**严禁**以“本地 Windows 跑通”作为 DoD 标准。
4.  **环境自愈清场**：离场前强制执行 `make clean`。**严禁**在根目录残留任何调试脚本、临时日志或导出文件。
5.  **安全审计律 (The Law of Security)**：涉及 core/mdm 核心表变更或引入新依赖的 [L3/L4] 任务，**必须执行** `make security-audit`。
    - **标准**：必须通过 Bandit (代码逻辑安全)、detect-secrets (无机密泄露) 与 Safety (无高危依赖)。
    - **操作要求**：必须在交付报告中包含安全审计摘要。
6.  **绝对取证原则**：进度汇报必须包含控制台输出碎片。**严禁**出现“逻辑预测认为代码正确”的幻觉。
7.  **文档归档律 (The Law of Archiving) [NEW]**: 
    - **绝对前置律**: **严禁** Agent 直接使用底层的 `write_to_file` 或 `replace_file_content` 等文件编辑工具绕开流程修改 `progress.txt`。所有的进度更新必须强制切入且仅能通过 `/doc-update` 原子工作流进行。
    - **硬性标准**: `Recently Completed`仅保留最近 5 条。**严禁**直接删除溢出条目，必须同步迁移至 `progress_archive.md`。
8.  **看板开发验证律 (The Law of Dashboard Validation) [NEW]**:
    - **SQL 预检**: 凡涉及在看板中编写的裸 SQL，**必须**先执行探测脚本验证表名与字段存在性，严禁凭记忆编写项。
    - **UI 冒烟**: 提交前**必须**使用 `browser_subagent` 或 `webapp-testing` 确认新页面无 Python 报错截图。
9.  **执行态强解锁协议 (Execution Lock Protocol) [MANDATORY]**:
    - **核心定义**: 只有在用户明确给出否定「咨询态」转向「执行态」的显式信号（如“开始”、“执行”、“OK”、“同意该方案”、“GO”等）后，方可对逻辑代码（.py, .js, .go 等）进行物理修改。
    - **疑问句强制挂起 [NEW]**: 凡是包含“？”（中英文）、“吗”、“对吗”、“是吗”、“如何”等疑问/探讨特征的语句，**强制判定**为「咨询态」。Agent 此时仅允许查阅与探讨，**严禁**执行物理编码改动。
    - **反向确认限制**: 若任务处于 [L2-L4] 级别或涉及核心模型重构，Agent 在完成 `/task-kickoff` 方案对齐后，**必须**主动暂停并询问：“方案已就绪，是否授权开始物理编码？”。
    - **违规阻断**: 严禁将含有疑问词的“伪指令”或系统的“Continue/继续”指令判定为执行授权。
10. **文档完整性守则 (The Law of Document Integrity) [MANDATORY]**: 
    - **严禁盲写**: 修改已存数据/日志类文档（.log/.md/.txt）严禁使用 `write_to_file`。
    - **强制流程**: 必须遵循「读-搜-改」三位一体：1. 先执行 `view_file` 建立物理快照；2. 识别历史锚点；3. 使用 `replace_file_content` 执行安全增量更新。
11. **dbt 全量建模审计律 (The Law of dbt Audit) [NEW]**:
    - **触发场景**: 凡涉及 `stg_` 映射层、核心 `models/` 逻辑重构、全局字段更名（如 `committed_date` ➜ `committed_at`）或 Schema 类型调整。
    - **强制要求**: 在交付前必须在容器内执行 `make dbt-build`。
    - **DoD 标准**: 必须在回复中粘贴 dbt 构建摘要（如 `PASS=xx ERROR=0`），确保血缘链路完整。严禁仅凭 Python 单元测试通过即宣布完工。
12. **交接日志物理先行律 (The Law of Log-First Handover) [MANDATORY]**:
    - **核心约束**: 任何宣告“交接完成”、“完工”或发出交付总结的指令，**必须**在同一回合内包含对 `docs/session-history.log` 与 `docs/lessons-learned.log` 的物理更新（`replace_file_content`）。
    - **严禁行为**: 严禁在尚未执行文件持久化的情况下输出带有“圆满完成”语义的纯文本总结。
    - **违规判定**: 若交付报告中未包含对应日志更新的 Tool Call 碎片，视为 L4 级流程违规，必须撤回并重做。
13. **计划外资产沉淀律 (The Ad-hoc Asset Rule) [NEW]**:
    - **核心约束**: 凡是在执行任务过程中临时起意、计划外衍生的优化与变更，完工后必须在 `progress.txt` 的 `Recently Completed` 中显式打上 `[Ad-hoc]` 或 `[计划外]` 标签。
    - **资产转化**: 此类临时产生的架构级调整或重大最佳实践，必须同步提炼并沉淀入 `contexts.md` (编码规范) 或 `docs/adr/` (架构决策记录) 中，严禁让其随对话流失。
14. **偏航必锚定律 (The Detour-Anchor Rule) [MANDATORY]**:
    - **核心约束**: 一旦当前操作偏离了 `progress.txt` 既定的 `Current Focus`（例如在写前端时顺手修了后端的 Bug），若偏航时间超过 1 个对话回合且产生了实际的代码修改。
    - **强制动作**: 在结束该临时分支、准备回到主线任务之前，Agent **必须**主动执行一次文档同步，确保最新的临时产物已经被固化成基建资产。
15. **宿主机环境声明律 (The Law of Host Environment) [MANDATORY]**:
    - **物理事实**: 本项目的开发宿主机为 **Windows + PowerShell**。CI 运行环境为 **Linux (GitHub Actions `ubuntu-latest`)**。
    - **Shell 方言红线**: Agent 在通过 `run_command` 工具执行终端指令时，**严禁**使用以下 bash/zsh-only 语法：
      - `&&` (逻辑与链式执行) — PowerShell 不支持，必须拆分为**独立的 `run_command` 调用**或使用 `;` 分号。
      - `||` (逻辑或 fallback) — 同上，必须使用 PowerShell 原生的 `try/catch` 或 `if ($LASTEXITCODE)` 替代。
      - `>` / `>>` (重定向) — 需使用 PowerShell 的 `Out-File` 或 `Tee-Object`，或确认 PowerShell 兼容后方可使用。
      - `$(...)` (命令替换) — 在 PowerShell 中是变量语法，bash 的命令替换功能需改用 `$(...)` 内嵌或反引号。
    - **跨平台 Makefile 约束**: `Makefile` 中涉及 OS 特有指令（如 `Get-ChildItem` vs `find`）的 target，**必须**使用 `ifeq ($(OS),Windows_NT)` 进行环境嗅探并提供双分支实现。严禁在 target 内部硬编码单一 shell 名称。
    - **黄金分割线**: **宿主机 (Windows)** 执行代码检查类工具（`ruff`, `detect-secrets`, `pytest` 本地快跑）；**容器 (Linux)** 执行业务逻辑验证（`make verify`, `make test`, `dbt build`）。两端职责不可混淆。
16. **凭据隔离与二次确认协议 (The Law of Credential Isolation) [MANDATORY]**:
    - **核心约束**: 凡涉及通过 `sudo` 或敏感凭据操作宿主机/WSL 环境，Agent **必须**遵循“三步走”：1. 发现缺失凭据 ➜ 2. 引导用户提供 ➜ **3. [中断并询问] 明确获得执行授权。**
    - **语义红线**: 收到 username/password 等敏感凭据**绝不**代表获得执行授权。Agent **严禁**在接收到凭据的回合内直接调用 `run_command` 进行物理操作。
    - **违规判定**: 若 Agent 在未获得显式执行指令（如“开始”、“执行”、“OK”）的情况下擅自利用凭据进行环境配置，视为 L4 级流程违规，必须立即停止并道歉。

---
*Generated by Antigravity-Core (2026-04-13T14:55+08:00)*
