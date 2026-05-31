# 测试门禁与防御性编程契约 (Testing & Defensive Programming)

> **定位**: 本文档是 `contexts.md` 的领域扩展，涵盖代码测试规范、质量门禁、代码风格 (Ruff) 以及核心的“防御性编程 10 大守则”。当编写测试用例、排查缺陷或实施代码重构时，必须以此为准绳。

## 1. 测试目录分层与准入原则

### 1.1 测试目录物理隔离规范

为防止测试代码腐化，严格遵循以下物理结构。**严禁**跨层级存放脚本（如在 unit 中存放 selenium 脚本）。

| 层级 | 目录路径 | 职责定义 | 外部依赖 | 默认状态 |
| :--- | :--- | :--- | :--- | :--- |
| **Unit** | `tests/unit/` | 验证纯业务逻辑、Service 层、Helper。 | **禁止**。必须 100% Mock。 | **必选 (Fast)** |
| **Integration (API)** | `tests/integration/api/` | 验证 Router -> Service -> DB 的契约。 | **允许**。仅限 `sqlite:///:memory:`。 | **必选 (Internal)** |
| **Integration (UI)** | `tests/integration/ui/` | 验证前端 DOM -> 后端 API 的端到端。 | **必须**。Selenium / Playwright。 | **可选 (Slow)** |
| **E2E / System** | `tests/e2e/` | 跨服务大周期验证（完整容器链）。 | **必须**。独立 Compose 环境。 | **发布准入** |

### 1.2 测试原子性与准入原则 [MANDATORY]

1. **100ms 准则**: 单个 Unit Test 文件执行时间严禁超过 100ms。
2. **超时熔断 (Timeout)**: 每个测试用例由 `pytest-timeout` 强制守护，上限为 **30s**。超过阈值的任务必须被物理杀死。
3. **测试 I/O 性能守卫**: 集成测试的数据库 Engine 必须设置为 `scope="session"`。表 (Base.metadata) 只需在会话开始时创建一次。
4. **默认运行策略**: `addopts` 必须默认包含 `-m "not slow"`。耗时超过 2s 的脚本必须手动标记 `@pytest.mark.slow`。
5. **模型导入警告**: 在 `conftest.py` 中执行 `create_all` 前，必须显式导入所有相关 `models` 模块，否则 `sqlite` 报错。
6. **依赖级联注入规范 (Dependency Seeding)**:
   - 集成测试**严禁**假设数据库中已有现成底数。
   - 任何涉及外键约束的操作，测试 Setup 阶段必须显式创建并 `flush()` 其关联的父表实体。严禁 Mock 不存在的外键 ID。

### 1.3 幂等性与重放安全测试 (Idempotency) [MANDATORY]

- **核心**: 确保在同步任务中断重启后，数据不会重复。
- **测试强制**: 任何数据采集 Worker 必须编写一个单元测试，连续运行两次 `worker.run()`（提供相同的模拟数据源），断言第二次执行后数据库物理记录数不变。

### 1.4 全链路仿真测试 (Full-system Simulation) 🌟

- **路径**: `tests/simulations/run_full_integration.py`
- **逻辑**: 模拟 7 大系统（GitLab, Jira, Sonar, Jenkins, ZenTao, Nexus, JFrog）的完整 API 响应。
- **关键验证项**:
  - **流水线追踪**: 验证 Jenkins Build 的 `commit_sha` 是否能精准关联到 GitLab 对应的提交记录。
  - **身份扇出**: 验证修改 `IdentityMapping` 后，是否所有关联系统的 Activity 全部归并至同一 User 下。
  - **依赖图谱**: 验证 `issuelinks` 导出的 `traceability_links` 是否能正确呈现跨项目阻塞逻辑。

### 1.5 数据重播验证 (Data Replay & Reprocessing)

- **脚本**: `scripts/reprocess_staging_data.py`
- **验证流程**:
  1. 清空事实表 (Fact Tables)。
  2. 保持 `raw_data_staging` 原始数据不变。
  3. 修改 Transform 映射逻辑（如调整 `ai_category` 判定准则）。
  4. 运行重播脚本。
  5. 校验事实表中的分类是否符合新准则。

### 1.6 专项测试场景 (Special Scenarios)

- **容错与重试**:
  - 模拟 API 429 (Rate Limit) 响应，验证 Worker 是否正确执行指数退避。
  - 模拟 API 500 错误，验证任务是否正确放回 RabbitMQ 延迟队列。
- **性能压力**:
  - 模拟 10 万级 Commit 的同步，验证 `Generator` 和 `Batch Commit` 机制下内存占用是否保持在 500MB 以下。

### 1.7 验收指南 (Acceptance Criteria)

任何发布版本必须通过以下“三道关卡”：
1. **静默期**: 在沙箱环境运行全量同步任务，且无 ERROR 日志。
2. **数据穿透**: 随机抽取 5 个项目，手动核对页面指标与看板指标是否一致。
3. **多端推送**: 确认异常告警能正确触达飞书/企微/钉钉机器人。

## 2. 代码质量与 Ruff 规范 (Code Quality & Ruff)

### 2.1 统一工具链

- 项目全面采用 **Ruff** 作为唯一的静态代码检查 (Lint) 与格式化工具。必须遵循根目录 `ruff.toml` 配置。
- 命令：`just lint`, `just ruff-fix`, `just fmt`。

### 2.2 关键编码禁令 (Hard Rules)

- **禁止 Bare Except**: 严禁使用 `except:` 捕获所有异常，必须显式捕获具体异常类，防止屏蔽系统级信号。
- **禁止环境变量类型混淆**: 使用 `os.getenv` 时，默认值必须为**字符串**（如 `"600"`），并在使用处显式转换。
- **行宽限制**: 默认 160。对于超长 SQL，允许在行尾添加 `# noqa: E501`。

### 2.3 门禁防御左移与并发提速 (Left-Shift & Concurrency)

- **检查左移**: 高频静态扫描通过 `.pre-commit-config.yaml` 挂载在本地 Git Commit 阶段，严禁下沉到生产容器栈执行。
- **并发提速**: 单元测试强制使用 `pytest-xdist (-n auto)`。流水线引擎 (`gatekeeper.py`) 利用并发组最大化资源。

## 3. 防御性编程十大守则 (Defensive Programming Mandates) [MANDATORY]

> **定位**：本章是跨越所有模块的**强制性编码红线**。任何新增代码在 Code Review 时必须对照自检。

### 3.1 永远不信任外部输入 (Never Trust Input)

- 来自外部 API、MQ 消息的数据，进入业务逻辑前**必须**经过类型校验与脱敏清洗。
- Worker 从 API 获取的外键 ID，必须显式 `int()`/`str()` 转换，严禁直接透传。Router 层强制使用 Pydantic 校验。

### 3.2 快速失败 (Fail Fast)

- 前置条件不满足（如必填缺失、数据库断开），**立即抛出明确异常并终止**。
- **严禁**吞掉错误继续执行。配置缺失时，插件初始化必须抛出 `ValueError`。

### 3.3 原子性操作 (Atomicity)

- 多步写操作必须包裹在事务中。跨表操作强制使用 `with db.begin():` 包裹。整体回滚，严禁中间态。

### 3.4 错误谱系强契约 (Error Pedigree) [MANDATORY]

- 所有的 Exception 必须包装成预定义的错误谱系（如 `AppException(code=xxx)`）。
- 交付报告中必须注明：本次修改涉及哪些潜在失败点，对应的错误码是多少。

### 3.5 超时与熔断 (Timeout & Circuit Breaker)

- 所有外部 HTTP 调用**必须**设置 `timeout` 参数（推荐 10-30 秒），严禁无限等待。

### 3.6 资源泄漏防护 (Resource Leak Prevention)

- 数据库连接、文件句柄、HTTP Session 必须使用 `with` 语句或 `try-finally` 确保释放。
- 临时文件必须在使用完毕后通过 `os.remove()` 自动清理。

### 3.7 边界值防护 (Boundary Protection)

- 分页查询必须设置 `max_page_size` 上限。批量操作必须设置 `batch_size` 限制。
- 字符串字段必须在数据库层面定义 `max_length` 约束。

### 3.8 日志即证据 (Logging as Evidence)

- 关键业务流转必须记录 `INFO` 级别日志。异常日志必须包含完整上下文（`correlation_id`、输入参数、堆栈）。
- **严禁**输出敏感信息，必须配置脱敏过滤器。

### 3.9 默认安全 (Secure by Default)

- 权限默认 `Deny All`。配置项缺失时走最保守默认值。新插件默认不启用。

### 3.10 意图锚点 (ADR Protocol) [MANDATORY]

- 每次代码重构前必须扫描 `docs/adr/`。如果某段代码写得很“奇怪”，大概率是为了规避底层坑，必须确认意图后再动手。

## 4. 架构专项防御韧性

### 4.1 审计引擎韧性规范

- `capture_audit_event` 必须独立包裹在 `try-except` 中，严禁因审计写入失败导致主业务回滚。
- 必须过滤掉所有 `RelationshipProperty`，仅记录物理列变更。

### 4.2 循环依赖处理规范

- 严禁在初始化阶段（`__init__` 或全局变量）引入交叉引用。
- 所有“负责人/所有者”外键对齐操作必须具备防御性：允许在第一阶段为空，由异步流程第二阶段填充。
