# DevOps Platform 机器人协作守则 (AGENTS.md)

> **调度中心**：继承 [GEMINI.md](/home/netxs/.gemini/GEMINI.md) (底座) 与 [contexts.md](contexts.md) (宪法)。
> **新 Agent 提示**：若不理解下述规则边界或在特定领域开发，**必须首先**查阅 [contexts.md](contexts.md) 顶部的「领域契约路由表」。

## 1. 指令调度与专家矩阵 (The Dispatcher)

| 指令 | 触发时机 | 动作目标 |
| :--- | :--- | :--- |
| **`/task-kickoff`** | 处理新任务 | 任务定级 [L1-L4]、风险预判、**环境健康度检查**、**文档影响分析**与逻辑切片 |
| **`/evolve-skill`** | 产生新教训 | 将 `lessons-learned` 转化为自动化审计规则 (Arbiter) |
| **`/session-handover`** | 关闭会话 | **[DoD]**：取证、日志落盘 (session-history/lessons-learned)、状态对齐 (`just progress-add/done`) |

| **`/bug-triage`** | 处理缺陷 | 复现 -> 归因 -> TDD 修复 |
| **`/ai-solve`** | TDD 驱动编码 (v2.3) | **双轨制**：后端轨道（pytest + 方言检测 + 导入验证）+ 前端轨道（HTTP可达 + API契约对齐 + 容器高度冒烟）|
| **`/codify-rule`**| 固化契约 | 读取 MD 文档的自然语言规则，自动提取并注入 `arch_auditor.py` |
| **`/doc-update`** | 逻辑变更/完工 | 更新 progress/contexts (SSOT) |
| **`/rollback`** | 执行变更前 | 生成应急恢复清单与 Git Tag |
| **辅助指令** | `/spike` (探针), `/plugin-init` (初始化), `/doc-audit` (查重), `/lint` (自查) |

### 1.1 语义映射与专家链

- **意图映射**: `"下班" / "吃饭" / "休息"` ➜ `/session-handover` | `"开始" / "上班" / "干活"` ➜ `/session-handover (Bootstrap)` | `"复杂/未知需求"` ➜ `/task-kickoff (SPIKE-FIRST Evaluation)`。
- **专家链**: `模型变更` ➜ `mdm-integrity-arbiter` | `SQL评审` ➜ `dbt-pipeline-auditor` | `高危重构` ➜ `chaos-sentinel` | `严谨性` ➜ `engineering-rigor-arbiter`。
- **技术锚点**: `编码`➜[`contexts.md §1.5`](contexts.md), `DB`➜[`contracts/database.md`](docs/contracts/database.md), `UI`➜[`contracts/frontend.md`](docs/contracts/frontend.md), `命名`➜[`frontend.md §3`](docs/contracts/frontend.md)。
- **UI 开发强制前置** \[MANDATORY\]: 任何涉及 `devops_portal/static/` 的前端工作，**必须**先激活 `frontend-design` SKILL，执行 **Step 0（项目合规性预检）**，依次完成：Dashboard Map 注册核查 → 读取 `docs/contracts/frontend.md` → 确认 API ResponseSchema 存在。

## 2. 软件生命周期红线 (Lifecycle Laws) [MANDATORY]

1. **执行锁 (Execution Lock)**: 仅在显式信号（“OK/开始”）后修改代码；“？”判定为咨询态，禁止物理编码。→ *规则定义继承自 `GEMINI.md §二.2`，本项目无覆盖；项目级 DoD 扩展见 `contexts.md §1.1`。*
1. **交接审计自进化**: [L2-L4] 离场 DoD 强制执行 `/evolve-skill`；严禁在未持久化日志时宣告完工。
1. **偏航必锚与计划外资产**: 偏离 Focus > 1 回合必须同步文档；临时优化标记为 `[Ad-hoc]` 并沉淀入 ADR。
1. **中断恢复嗅探**: 启动/收尾强制 `git status -u` 并前置读取 `git log -n 3` 对齐物理提交线；发现未跟踪脚本必须汇报并整合进 `progress.txt`。
1. **临时脚本隔离**: 严禁在业务目录排错，必须写入 `.agent/scratch/`。
1. **统一运维入口 (CLI Mandate)**: **绝对严禁**直接执行 `python scripts/xxx.py`。所有运维任务、初始化、诊断及数据导出操作，必须通过 `uv run scripts/cli.py <group> --module <name>` 触发。**新功能优先采用类模式实现**（存放在 `devops_collector/management/commands/`），以确保日志轨迹、数据库连接池及事务的一致性。
1. **管理命令规范 (Command Framework)**: 新增运维逻辑必须继承 `BaseCommand` 基类。禁止在 `scripts/` 下创建新的独立 Python 脚本。执行前应先运行 `uv run scripts/cli.py list` 核实已存在的命令。
1. **修订记录一致性协议 (Changelog Integrity) [MANDATORY]**: 历史进度归档已彻底并入 `CHANGELOG.md`。**严禁**使用已废弃的 `progress_archive.md`。执行归档时，必须将 `progress.txt` 中的任务摘要提炼并置顶于 `CHANGELOG.md` 的最新版本或 `[Unreleased]` 节段。
1. **导入完整性与预飞行 (Import Integrity & Pre-flight)**: 任何 Model/Service 变更必须首先通过 `python -c "import ..."` 冒烟测试。严禁在宿主机环境未安装依赖时强行运行 `pytest`，必须使用沙箱模式。
1. **文码同行律 (Code-Doc Co-evolution) [MANDATORY]**: 任何涉及业务逻辑、模型 Schema、指标口径或 UI 架构的变更，**必须**在提交代码的同时完成相关文档（如 `docs/`, `contexts.md`, `AGENTS.md`, `GLOSSARY.md`）的同步更新。严禁在文档滞后的情况下宣告完工。
1. **交付闭环律 (Delivery Closure)**: 建立物理卡点：任何核心逻辑切片（Focus）宣告完成且 `just verify` 100% 通过后，**必须立即执行本地 `git commit` 落库**（使用 Conventional Commits 格式），并将 Hash 登记入交付日志，无论是否处于离场态，做到“验证通过即 commit，交付即闭环”。
1. **记忆闭环律 (KI Closure) [MANDATORY]**: 每个 L2+ Focus 完工（`git commit` 落库后），AI **必须主动**执行以下知识沉淀动作，这是 DoD 的物理检查点，不可跳过、不可推迟至离场时：

- **事实提炼**：从本次 Focus 中提取 3-5 条 Key Facts（架构决策、已知 Bug 修复方式、新增模式、反面教材等），用自然语言写入 KI artifact（路径：`<appDataDir>/knowledge/<topic>/artifacts/`）。
- **KI 元数据更新**：同步更新对应 KI 的 `metadata.json`（`updated_at`、`summary` 字段）。
- **禁止遗漏**：严禁以"会话已长"、"任务紧急"为由跳过此步骤。若 KI 目录不存在，AI 必须新建并初始化。
- **验收标准**：KI 文件写入完毕后，AI 在回复中明确报告："✅ KI 已更新：`<path>`"。

## 3. 工程严谨性基准 (Engineering Rigor) [MANDATORY]

1. **物理验证**: L2+ 必须执行 `just verify` (覆盖率 >= 80%)；交付报告必须粘贴终端日志碎片。
1. **环境安全**: 宿主机为 **WSL Ubuntu (Linux/zsh)**；涉及核心变更必须执行 `just security-audit`；**[Sync-Only]** `git push` 仅限跨设备同步时显式执行，严禁自动推送。
1. **提交语言**: Commit Message 强制使用英文 Conventional Commits 格式，严禁使用中文。
1. **离场审计与交接协议 (Exit & Handover Protocol) [MANDATORY]**: 凡用户宣告“下班”、“任务结束”或会话离场前，必须强制执行以下动作：
   - **审计登记**：按照 `docs/history/session-history.log` 规范，置顶登记本次会话的 Session ID、耗时及核心交付物。
   - **物理清理**：执行 `just clean` 移除临时文件；若涉及模型变更，执行 `just docs-verify`。
   - **SSOT 对齐**：同步更新 `progress.txt` (当前看板) 与 `CHANGELOG.md` (版本履历)。

## 4. 架构契约原则 (Architectural Contracts) [AI-NATIVE]

1. **Schema-First**: 逻辑前必须输出 `Schema Proposal` 并获准；强制使用 Pydantic/SQLAlchemy 强类型。
1. **幂等性与重放**: 变更逻辑必须幂等；单元测试必须包含连续调用两次的“重放断言”。
1. **结构化观测**: 强制埋点 `correlation_id` 与关键指标；Schema 必须包含 `__metrics__` 元数据。
1. **错误谱系**: 禁止模糊异常，必须基于 `ErrorSchema` 抛出结构化错误码。
1. **状态机行为锁**: 状态流转必须定义 `VALID_TRANSITIONS` 并通过 `.transition_to()` 封装。
1. **意图锚点 (ADR)**: 方案设计前必查 `docs/adr/`；技术妥协必须生成极简 ADR。
1. **性能取证**: L3/L4 任务必须执行 `just profile-db/code`，交付需含“优化前后”对比数据。
1. **服务层与命令层分离 (Service/Command Separation) [MANDATORY]**:
   - **Command 类职责**: 仅负责解析参数、调用服务、报告结果。严禁在 `handle()` 中直接编写复杂业务算法或 SQL。
   - **业务下沉**: 所有核心业务逻辑、数据同步算法、报表生成逻辑必须封装在 `devops_collector/services/` 中。
   - **价值目标**: 确保业务代码可被 CLI (Typer/Command)、API (FastAPI) 或 UI (Streamlit) 无差异调用，Command 仅作为 Service 的一个“UI 分身”。

## 5. 交互与决策契约 (Interaction & Decision Contract) [MANDATORY]

1. **交互前置审计锁 (The Inquiry Lock) [MANDATORY]**:
   - **问号拦截 (The Question-Mark Gate)**: 若用户请求以“？”结尾或包含疑问语气，AI 必须进入“方案呈报模式”。在该模式下，**严禁调用任何物理写操作工具**。
   - **方案呈报**: 必须提供 A/B 方案及其推荐理由。凡是提供 A/B/C 结构化选项时，必须显式包含 **“AI 视角推荐路径”**。一旦用户做出决策：
     - 被选中的方案必须立即通过 `just progress-focus` 更新到 `progress.txt` 的 **Current Focus**。
     - 未被选中或被推迟 (Deferred) 的方案必须通过 `just progress-mirror` 镜像到 **Tasks** 列表，确保意图不丢失。
   - **执行态解锁序列 (Execution Unlock Sequence) [MANDATORY]**: 用户确认进入执行态（"OK/开始/确认方案X"）后，AI **必须严格按以下 3 步顺序执行**，任何步骤不可跳过、不可延后、不可乱序：
     1. **🔑 锁定 Focus**: 执行 `just progress-focus "..."` 将确认的方案写入 `progress.txt` 的 **Current Focus**。**此步是解锁编码权限的物理钥匙——未执行此步前，编码权限保持锁定状态。**
     1. **📋 拆解子任务**: 创建或更新 `task.md`，将 Focus 拆解为可执行的子任务清单。
     1. **⌨️ 开始物理编码**: 完成前两步后，方可调用代码写操作工具。
   - **违规判定**: 若 AI 在未完成 Step 1 的情况下直接编码，视为违反「执行锁」红线（§2.1），等同于在咨询态下修改代码。
1. **UI 集成决策锁**: 涉及 `devops_portal/static/` (Portal) 的新视图集成时，**必须**首先向用户呈报以下决策路径：
   - **方案 A: Streamlit 分析版 (Decision Hub)**: 适合**非高频、重分析、重度量**的决策需求（如：效能雷达、成本审计、质量趋势）。
   - **方案 B: Portal 操作版 (Operational)**: 适合**高频交互、低延迟、重流程**的操作需求（如：用例执行、缺陷处理、即时追溯）。
   - 由用户决策后再行编码。
1. **反向追问深度**: 若用户意图存在 20% 以上模糊，必须停止执行并提供至少 2 个具象化的逻辑切片供用户确认。

## 6. 工具执行与安全规范 (Tool Execution & Safety) [MANDATORY]

1. **强制确认红线 [仅此3类，不得扩展]**: 以下操作**严禁自动执行**，必须等待用户明确点击确认：

   - **环境配置**: 任何对 `.env` 文件（含 `.env.prod`, `.env.staging` 等所有变体）的写入或覆盖操作。
   - **密钥操作**: 任何明文出现或写入 `password`, `token`, `api_key`, `secret` 字段的操作。
   - **远程推送**: `git push`（含 `--force`）。跨设备同步时，须用户显式触发。

______________________________________________________________________

*Generated by Antigravity-Core (2026-05-22T00:15:00+08:00)*
