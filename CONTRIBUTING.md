# 开发者与贡献指南 (Contributing Guide)

感谢您有兴趣为 DevOps Data Collector 贡献代码！

## 1. 开发规范 (Development Standards)

### 1.1 代码风格与质量

- 严格遵循 **Google Python Style Guide**。
- **语言与符号**:
  - 项目文档的主体语言必须是中文。
  - **严禁**在文件名称、文件内容、注释及 UI 界面出现表情符号。
- **Docstring 规范**: 所有类、方法及核心代码必须包含 **Google Style Docstrings**（中文）。
  - 必须包含 `Attributes` 或 `Args`/`Returns` 节段。
  - 每一项必须包含类型标注，如 `attr_name (type): description`。
- **语义分层规范 (Semantic Alignment)**：
  - **技术侧用英文**：数据库字段名、API Schema、核心代码变量必须使用标准英文命名（如 `pm_user_id`）。
  - **业务侧用中文**：数据库 `comment`、CSV 导入/导出表头、UI 界面显示、报表评估指标必须使用专业业务中文术语（如：项目经理、负责人邮箱、交付周期、ELOC等）。
  - **自适应映射机制**：初始化与导入脚本必须具备“中文表头 -> 英文变量”和“邮箱 -> 用户ID”的自动映射能力，降低业务侧维护成本。
- **模型命名原则**: 为了避免与测试框架（如 pytest）发生自动收集冲突，所有测试管理相关的核心模型必须加 `GTM` 前缀（例如：`GTMTestCase`、`GTMRequirement`）。
- **调试友好性**: 所有 ORM 模型类必须实现结构化的 `__repr__` 方法，包含关键识别字段。
- **高内聚，低耦合**: 代码应以模块化方式生成，实现高内聚，低耦合；功能逻辑应尽量下沉至 Service 或 Utility 层。
- **零硬编码原则 (Zero Hardcoding)**: API 地址、Token 及业务参数必须通过 `devops_collector.config.settings` 获取（对应 `.env` 注入），严禁任何形式的字符串硬编码。

### 1.2 提交规范 (Commit Message)

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat: ...` 新功能
- `fix: ...` 修复 Bug
- `docs: ...` 文档变更
- `refactor: ...` 代码重构
- `chore: ...` 构建/依赖杂项

### 1.3 架构原则与协作模型

1. **AI-Native 协作**: 本项目采用人机协同模式。所有逻辑变更必须遵守 [`AGENTS.md`](./AGENTS.md) 定义的物理红线与指令工作流。
1. **ELT 模式**: 采集中优先拉取原始数据入库 (`raw_data_staging`)，再在数据库中通过视图 (SQL Views) 或 dbt 模型实现业务逻辑转换。
1. **异步解耦**: 耗时任务（如全量同步）应通过 RabbitMQ 分发至 Worker 执行。

______________________________________________________________________

## 2. 插件开发规范 (Developing Plugins)

系统采用插件工厂模式。若要新增数据源（如飞书、钉钉、JFrog）：

### 2.1 目录结构

在 `plugins/` 目录下创建新文件夹，必须包含：

- `client.py`: 封装 API 请求逻辑。
- `worker.py`: 实现具体的采集与转换流程。
- `models.py`: 定义当前插件特有的数据库表。

### 2.2 注册插件

必须在 `devops_collector/core/registry.py` (或对应的 Registry 模块) 中注册您的 Worker 和 Client 类，以利用系统自动分发能力。

### 2.3 关键逻辑准则

- **身份归一化**: 严禁直接在插件中创建 User。必须调用 `IdentityManager.get_or_create_user()`，通过 Email 或工号进行全局对齐。
- **原始数据暂存**: 采集到的 JSON 数据必须优先通过 `save_to_staging` 方法保存，以支持数据回放 (Data Replay)。
- **断点续传**: 在 `worker.py` 中记录同步偏移量（如时间戳或 Page），确保任务中断后可恢复。

______________________________________________________________________

## 3. 测试、验证与文档 (Testing & Docs)

### 3.1 物理验证红线 (Verification)

任何 PR 提交前，必须在本地或容器环境执行：

```bash
just verify
```

- **硬性指标**: 核心层 (`devops_collector/core/`) 单元测试覆盖率必须达到 **100%**。
- **集成测试**: 必须通过所有业务集成场景测试。

### 3.2 文档同步 (SSOT)

任何功能变更或 Schema 修改，必须通过以下方式同步：

1. 更新 [`DOC_INDEX.md`](./docs/DOC_INDEX.md) 中受影响的模块。
1. 运行 `/doc-audit` 指令检查文档冲突。
1. 更新 [`progress.txt`](./progress.txt) 已更新至最新状态。

______________________________________________________________________

## 4. 运维与初始化脚本规范 (Operations & CLI Scripts)

为了降低运维碎片化并提升 AI 协作效率，所有位于 `scripts/` 目录下的运维、初始化及工具类脚本必须集成至 `cli.py` 调度总线。

### 4.1 入口单一原则 (Single Entry Point)

- **统一入口**: 禁止直接运行 `python scripts/xxx.py`。所有任务必须通过 `uv run scripts/cli.py <command> --module <name>` 触发。
- **调度分组**: 脚本必须按职责归入以下组别：
  - `init`: 数据初始化与重置。
  - `diag`: 环境诊断与连通性测试。
  - `check`: 静态代码质检与配置校验。
  - `verify`: 业务逻辑与数据完整性验证。
  - `run`: 常规作业同步任务。
  - `export`: 数据导出与报表生成。

### 4.2 深度整合规范 (Phase 2 标准)

为了实现资源共享（如共享数据库连接池）和事务控制，新脚本应遵循“模块化调用”设计：

1. **接口契约**: 脚本必须暴露 `execute_command(session: Session, **kwargs) -> bool` 函数。
1. **上下文注入**: 严禁在脚本内部自行创建 `engine` 或 `Session`。必须使用从 `cli.py` 注入的 `session`。
1. **事务控制**: 脚本内仅执行 `session.flush()`，由 `cli.py` 顶层统一控制 `commit` 或 `rollback`。
1. **兼容模式**: 保留 `if __name__ == "__main__":` 块用于本地独立调试。

### 4.3 自动发现机制 (Autodiscovery)

`cli.py` 具备自动探测能力。若新增脚本满足 `{group}_{name}.py` 命名规则且放入 `scripts/` 目录，它将自动出现在对应的 `--help` 列表中。

### 4.4 资源路径收拢 (Resource Path Alignment)

- **配置共享**: 脚本所需的外部 URL、敏感信息等配置必须统一从 `devops_collector.config.settings` 对象读取。
- **静态数据归口**: 所有初始化所需的 CSV 数据模版必须存放于 `docs/assets/sample_data/` 目录。脚本内应通过动态路径（如 `Path(__file__).parent.parent / "docs" / "assets" / "sample_data" / "xxx.csv"`) 定位，严禁在脚本内散落数据文件。
