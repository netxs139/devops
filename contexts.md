# DevOps Platform Project Contexts (Development Constitution)

> **Document Positioning**: This file is the project-specific constitution for **DevOps Platform**.
>
> - **全局原则 (Global Rules)**: 基础 AI 协作哲学定义在 `~/.gemini/gemini.md`。
> - **AI 导航路由 (Meta-Prompt)**: 自动化代理的入场规则、行为守则定义在库根目录 \[`AGENTS.md`\](file:///home/netxs/workspace/devops/AGENTS.md)。
> - **项目宪法 (Project Contexts)**: 本文件（`contexts.md`）包含全局架构与编码红线。
>
> *优先级：`contexts.md` (业务/技术真相) > `AGENTS.md` (AI 调度指令) > `gemini.md` (全局)。发生冲突时按此优先级执行。*

## 0. 领域契约路由表 (Domain Routing Table) [MANDATORY]

为防止认知超载，本代码库的深层技术细节已拆分为独立领域契约。AI Agent 在进行任何具有技术深度的变更前，**必须首先**通过 `view_file` 查阅对应的领域契约：

> 🛡️ **架构纪律：一域一档 (SSOT)**
> 任何领域的核心开发规范**必须且只能**存在于单一契约文档中。严禁将规范散落为“契约 (Contract)”与“指南 (Guide)”双轨制。若发现文档之间存在知识重叠或互相引用导致认知链路断裂，必须立即发起合并并废弃冗余文件。

| 触发条件 (如果你涉及以下领域...) | 必须查阅的契约文档 | 覆盖内容 |
| :--- | :--- | :--- |
| AI 调度规则、Skill 触发、会话交接 | \[`AGENTS.md`\](file:///home/netxs/workspace/devops/AGENTS.md) | 指令矩阵、生命周期红线、交互契约 |
| `models/`, 数据库 Schema, 实体映射 | \[`docs/contracts/database.md`\](file:///home/netxs/workspace/devops/docs/contracts/database.md) | Surrogate PK, SCD2, MDM 脱敏, 行级权限 |
| `devops_portal/static/`, CSS/JS | \[`docs/contracts/frontend.md`\](file:///home/netxs/workspace/devops/docs/contracts/frontend.md) | Apple Style, Dashboard Map 索引注册 |
| `dbt_project/`, SQL 数据转换 | \[`docs/contracts/dbt.md`\](file:///home/netxs/workspace/devops/docs/contracts/dbt.md) | dbt 分层规范, JSONB 类型安全, 报表视图约定 |
| Docker, RabbitMQ, 调度器, 插件集成 | \[`docs/contracts/ops.md`\](file:///home/netxs/workspace/devops/docs/contracts/ops.md) | 运维网关, 队列隔离, GitLab/ZenTao 特异防护 |
| `tests/`, Pytest, 排查Bug, 代码重构 | \[`docs/contracts/testing.md`\](file:///home/netxs/workspace/devops/docs/contracts/testing.md) | **防御性编程 10 大守则**, 测试层级, 代码门禁 |

______________________________________________________________________

## 1. 项目概览 (Overview)

**DevOps Data Application Platform** 是一套企业级研发效能数据底座。它通过插件化架构采集 GitLab, SonarQube, Jenkins, Zentao, Nexus 等工具链数据，并利用 dbt 进行指标建模，最终通过 Apple Style 的原生前端界面提供看板与追溯能力。

### 1.1 生命周期全局防线 (Lifecycle Global Guards)

- **执行态强解锁 (Execution Lock)**:
  - **背景**: 防止 AI 在探讨阶段擅自修改文件，造成意外的代码腐化。
  - **边界**: 只要用户的回复中带有“？”或表达了犹豫（如“让我想想”、“你觉得呢”），严禁调用任何写文件工具。
  - **DoD**: 必须在回复末尾询问：“方案已就绪，是否授权开始物理编码？”
- **中断恢复嗅探 (Interruption Recovery)**:
  - **动作**: 启动新会话或接手中断任务后的第一步必须是 `git status -u`。
  - **冲突处理**: 若发现未跟踪文件，必须假设发生了崩溃，先同步进度再继续工作。

## 1.5 核心协作与编码律 (AI-Native Engineering Principles) [MANDATORY]

为确保系统的高可靠性与代码极致简洁，所有开发者（含 AI 代理）必须遵守以下四大工程原则：

1. **编码前思考 (Ask > Guess)**:
   - **严实假设**: 严禁在存在 20% 以上理解模糊时盲目编码。如果不确定，必须停下来提问而不是猜测。
   - **双重路径**: 存在歧义或多种实现方案时，必须呈现 A/B 权衡选项供人类决策，不得默默选择一种并执行。
   - **诊断豁免**: 为确保排障效率，只读诊断指令（如 `ls`, `git status`, `cat`）豁免于“咨询态代码锁定”，AI 可自主执行。
1. **简洁优先 (Less is More)**:
   - **对抗过度工程**: 不要添加要求之外的功能，严禁为一次性代码创建复杂的抽象。
   - **逻辑重写律**: 如果 200 行代码可以通过逻辑优化写成 50 行，必须重写它。
1. **精准修改 (Precision First)**:
   - **局部封锁**: 修改现有代码时，严禁“顺手”改进相邻的无关代码、注释或格式。只准碰必须碰的部分。
   - **孤儿清理律**: 必须删除因本次改动而变得无用的导入 (import)、变量或函数。
1. **目标驱动验证 (Verify > Hope)**:
   - **可验证意图**: 将模糊指令转化为可物理验证的目标。
   - **计划先行**: 对于多步骤任务，必须先输出分步计划及每个步骤的物理验证方法 (`1.[步骤] -> 验证:[检查]`)，严禁“憋大招”。
1. **绝对复用原则 (Strict Reuse Principle) [MANDATORY]**:
   - **核心红线：能用成熟的组件的，严禁自行开发**。凡是能用开源生态或企业基础组件库解决的需求（详见下文白名单），绝不允许重新造轮子或封装低效的工具代码。
   - **生态对齐白名单与重构建议**（新代码必须遵循，旧代码逐步重构）：
     - **[UI 交互]**: 基础组件（按钮、表单、表格）必须使用 `Naive UI`；复杂图标一律使用 `Xicons`，禁止手动堆砌 SVG。
     - **[HTTP 缓存与状态]**: 严禁在组件中手写大量的 `loading / error / data` 模板代码，强烈推荐引入 `@tanstack/vue-query`。
     - **[工具与 Hook]**: 严禁手写防抖(debounce)、节流、深拷贝、窗口监听器，**必须强制引入** `VueUse` 与 `lodash-es`。
     - **[图表与可视化]**: 研发效能数据（如雷达图、趋势折线）严禁基于原生 Canvas 开发，**必须使用** `vue-echarts` (ECharts)。
     - **[时间处理]**: 前后端均严禁直接对原生 `Date/datetime` 进行繁琐的加减和格式化。前端**必须使用** `dayjs` 或 `date-fns`，后端**推荐使用** `pendulum` 或原生 datetime 的标准化扩展。
     - **[代码与文档编辑器]**: 凡涉及 CI/CD YAML 配置或 Markdown 编写，严禁使用原生 `<textarea>`，**必须引入** `monaco-editor` 及 `markdown-it`。
     - **[后端重试控制]**: 对接 GitLab/Jenkins 等外部不可靠网络时，严禁手写 `while / time.sleep`，**必须强制使用** `Tenacity` 实现指数退避重试。

## 1.6 负面模式与架构红线 (Anti-Patterns & Architectural Redlines)

为防止架构腐化并规避已知的物理坑位，所有开发必须避开以下负面模式：

1. **[Import] 插件自注册陷阱**: 在插件的 `__init__.py` 中直接导入 Worker/Client 会导致级联导入。正解：通过 `get_worker_class()` 延迟加载。
1. **[DB] SCD2 物理唯一性冲突**: 在 SCD2 表的业务键列上直接设置物理 `unique=True` 会阻止历史快照。正解：改用 **部分索引 (Partial Index)**。
1. **[Type] 过时类型引用**: 禁止在 Python 3.9+ 代码中使用 `from typing import Type, List, Dict`。
1. **[Hook] 静默抽象钩子**: 在 ABC 基类中定义空的 `pass` 方法必须显式标注 `# noqa: B027`。
1. **[Logic] 循环内 N+1 查询**: 在处理任务的循环中执行 `session.query().first()` 严禁使用。必须在循环外通过 `in_` 批量拉取数据并建立内存 Map。
1. **[FastAPI] 隐式路由前缀陷阱**: 所有的 `APIRouter` 必须在实例化时显式声明 `prefix`（例如：`router = APIRouter(prefix="/users")`），**严禁**在 `main.py` 的 `include_router` 中才迟迟声明前缀。此红线旨在确保静态 AST 扫描能够准确定位 API 契约，并防止路由挂载混乱。

## 2. 核心技术栈 (Technology Stack)

- **后端 (Backend)**: Python 3.12, FastAPI (Router-Service 模式), SQLAlchemy 2.0 (Typed).
- **数据层 (Data)**: PostgreSQL 15, dbt (数据转换层), RabbitMQ (任务分发控制).
- **前端 (Frontend)**: Native JS/CSS (Apple Style Edition), Web Components.
- **运维 (DevOps)**: Docker Compose, 多阶段镜像构建.

*(更深入的协议参见顶部的领域路由表。)*

## 3. 开发环境与兼容性 (Environment)

### 3.1 宿主机与容器隔离架构 [MANDATORY]

- **三层混合结构**: **物理机 (Windows)** → **容器引擎层 (Docker Desktop，Linux 模式)** → **开发执行层 (WSL2 Ubuntu / bash/zsh)**。
- **主验证环境**: **Docker Desktop (Linux 模式)**。所有功能逻辑、数据库变更、集成测试**必须**首先在容器内验证 (`docker-compose exec api ...`)。
- **辅助环境**: WSL2 Ubuntu。仅用于代码编写、轻量级 Lint 检查。**严禁**以“WSL2 宿主机能跑通”作为最终提测标准。

### 3.2 宿主机编码红线 (Host Environment Constraints)

- **关键禁令**: 若宿主机本质上通过 Windows 挂载代码，严禁使用 PowerShell 的 `>` 或 `>>` 进行文件重定向，这会导致 UTF-8 变成带 BOM 的乱码并破坏 Python 语法。
- **替代**: 跨平台数据处理必须调用 `python scripts/utils.py` 或由标准 Python 库处理。

### 6. 测试与持续集成策略 (Comprehensive Testing Strategy)

**6.1 核心原则**

- **严禁纯人工测试**：所有特性变更必须伴随至少一个自动化测试。
- **契约优先 (Contract First)**：测试首先应验证组件、API 的契约是否守住，再验证内部实现逻辑。
- **Fail Fast, TDD**：要求在编码时使用秒级响应的测试工具驱动修改。

**6.2 前端测试规范 (Vue3 + Vitest)**

- **工具链**：`Vitest` + `@vue/test-utils` + `happy-dom`。
- **职责**：
  - **组件渲染测试**：验证视图层能否根据给定 Props 正确渲染 DOM，拦截页面白屏。
  - **事件交互测试**：验证用户交互（点击、输入）是否触发了正确的 `emit` 或状态流转。
- **隔离性**：组件测试中所有外部依赖（如 `http.get`, 路由）必须被 `vi.mock`。

**6.3 后端 TDD 与秒级增量测试 (pytest-testmon)**

- **工具**：集成 `pytest-testmon` 以追踪代码到测试的映射关系。
- **纪律**：
  - 修改代码即测试：每次保存修改后，执行 `just test`（它映射到 `pytest --testmon`），仅运行受影响的用例。
  - 失败即回退：如果增量测试失败，必须立刻查清原因或 `git checkout`，严禁在红色状态下堆积新代码。

**6.4 API 契约测试 (Contract Testing)**

- **目的**：防御前后端分离带来的“接口结构变更导致前端崩溃”问题。
- **实现方式**：
  - 在 `tests/integration/` 下编写针对关键端点的契约测试。
  - **强制断言**：获取接口返回 `response.json()` 后，必须将其送入 FastAPI 定义的 Pydantic `ResponseSchema`（如 `UserResponse(**data)`）中进行实例化校验。如果后端字段名称被悄悄修改，该实例化会立刻抛出 `ValidationError` 并截断流水线。

### 3.3 目录与 CI 规程

- **`./tmp/`**：运行时生成的临时产物，CI 构建**不包含**此目录。
- **`./scratch/`**：一次性调试脚本，必须在任务结束前清理或归档，严禁混入业务逻辑。
- **原生 GitLab CI/CD**:
  - GitLab CI (私有化 Docker Runner, **GitLab CE 18.10**, `https://gitlab.tjhq.com`) 用于企业部署。
  - 流水线基于原生多阶段 (Multi-Stage) 并行架构，全量配置于 `.gitlab-ci.yml`，不依赖单体门禁脚本。
  - 本地 pre-commit hooks (`.pre-commit-config.yaml`) 负责极速左移拦截；远端 CI 负责深度安全审计与全量测试。两者互补而非重复。
- **外部工具链版本锚定**:
  - 禅道 (ZenTao): **开源版 20.7** — API 行为与字段约定以此版本为准，见 [`docs/contracts/ops.md §3.1`](docs/contracts/ops.md)。
  - GitLab: **CE 18.10** — CI/CD 流水线配置与 Runner 注册以此版本 API 为准，见 [`docs/contracts/gitlab-ci.md`](docs/contracts/gitlab-ci.md)。
- **CSV 编码**: 所有 CSV 强制使用 `utf-8-sig` 编码以防 Windows Excel 乱码。
- **配置一致性**: 所有配置通过 `.env` 注入。Pydantic 映射使用双下划线 (`GITLAB__URL`)。Logger 必须屏蔽敏感字段。
