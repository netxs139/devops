## Spike 结论报告: SonarQube 插件深度架构评估与优化方案 \[MANDATORY TAG: [Spike-Result]\]

- **日期**: 2026-04-14
- **耗时**: 2h / 时间盒 4h
- **结论**: 🟢 Go

### 发现 (Findings)

1. **[架构违规] 门禁通信契约错位 (缺失 Webhook):** 根据 `contexts.md` 第 17.1 节约定，CI 分析结果应当采用接收式 Webhook 主动推送。而目前 `client.py / worker.py` 均维持着极其沉重的全量主动拉取 (`Pull / Pagination`) 机制，且统查发现 `devops_portal/routers/webhook_router.py` 尚未分配处理 `/sonarqube` 推送的相关入口。
1. **[性能红线] 遭遇 N+1 查询与事务雪崩:** 分析 `worker._sync_issues` 调度发现，解析器 `transformer.py` 在执行模型包装时使用了按个查找更新 `session.query(SonarIssue).filter_by(...).first()`，完全背离了宪章 `4.1` 定义的 "Transform 层批处理规范" 和 `bulk_save_to_staging` 的底层高速 COPY 隧道，面对成千上万个 Code Smells 将引发严重的性能瓶颈。
1. **[数据血缘界限] 隐式耦合污染:** `worker.py` 第 16 行直接导入并调用了 `GitLabProject` 模型，打破了各个 `plugins` 数据源必须自给自足、物理隔离的设计界限，未来若 GitLab 模块停运将殃及 SonarQube 的运行。

### 证据 (Evidence)

- **N+1 高危瓶颈代码截取** (`devops_collector/plugins/sonarqube/transformer.py:124`):
  ```python
  def transform_issue(self, project: SonarProject, i_data: dict) -> SonarIssue:
      # 致命缺陷: 这里的循环查询将会导致每出现一个 Issue 就发生一次 RTT 查询。
      issue = self.session.query(SonarIssue).filter_by(issue_key=i_data["key"]).first()
      # ...
  ```
- **Webhook 接收口未实装**: 查阅 Webhook 路由总署仅包含了关于 GitLab 的解析，完全没有对应 SonarQube `Task Completed` 事件的 Webhook 定义。

### 风险与限制 (Risks & Limitations)

- 当系统接入企业级包含几十万上百万行代码的核心工程时，成千上万条技术债指标会在 Worker 端单线程串行中卡死，不仅造成资源 OOM，更会挤死 `sonarqube_tasks` 消费者队列，导致无法承接新的任务。
- 直接利用 Transformer 写原表丢失了 Staging 层溯源属性（无法防御数据篡改追溯）。

### 下一步 (Next Steps)

- 🟢 Go: 建议立刻终止对该插件现存逻辑的扩张，整体定级为 [L3] 任务进入重构，分拆如下行动点：
  1. **架构倒置与多源触发机制**:
     - 在 `webhook_router.py` 里建立专用 SonarQube 端点，承接质量门禁的 Webhook 打击。
     - **[方案 A 增强预案]**: 为了绕过系统管理员权限限制并增强血缘追溯，支持 CI/CD 管道在 `sonar-scanner` 结束后通过 API 主动触发同步。该模式需配合「状态探测 (Task Status Check)」逻辑，确保服务端分析完成后再执行抽取。
     - **[方案 B 降级预案]**: 若 Webhook 与 CI 钩子均不可用，实现基于“水位线 (Watermarks)”的增量轮询模型。通过记录 `last_analysis_date` 将全量重扫降级为针对性的增量同步。
  1. **存储层革新**: 在 `worker.py` 切换引入 `bulk_save_to_staging` 和内存 Dictionary 预加载映射（Map Load），彻底根除 N+1 循环查库陷阱。
  1. **架构解绑**: 彻底移除对 GitLab Models 的显式加载，将异构模型对齐丢入第二阶段自愈协议 (`Two-Phase Protocol`) 和 SQL dbt 中间层处理。

### 数据指标与建模补充 (Data Metrics & Modeling)

为了支持业务侧的“质量中心看板”导出需求，模型层需完成以下核心指标的计算闭环：

1. **开发总人月预测 (Development Effort)**:
   - **公式**: `dev_cost = round(((sqale_index / 60) / (sqale_debt_ratio / 100)) / 174)`
   - **边界处理**: 需拦截 `sqale_debt_ratio == 0` 的异常波段，默认返回 0。
1. **字段对齐规范**:
   - **总行数**: 统一锚定 Sonar 原生 `lines` 字段（含空行与注释）。
   - **门禁状态**: 在 `SonarMeasure` 中显式存储 `quality_gate_status` 字符串，用于报表导出。
1. **导出视图**:
   - 支持“最快照模式 (Latest Snapshot)”，聚合获取每个项目的最新一次分析指标。
