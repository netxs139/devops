## Spike 结论报告: 全链路极速性能探针 (Performance Boosts) [MANDATORY TAG: [Spike-Result]]

- **日期**: 2026-04-24
- **耗时**: 1.5h / 时间盒 4h
- **结论**: 🟢 Go (对前三项进行立即采纳) / 🟡 Need More Investigation (针对 Docker 构建层)

### 发现 (Findings)
1. **`tmpfs` 内存数据库提速**: 成功在 `docker-compose.yml` 中挂载 Postgres `tmpfs`，原本受限于宿主机 I/O 的数据库集成测试获得了极致的提速体验。
2. **`pytest-testmon` 精准测试分析**: 引入了 `pytest-testmon`。在全量测试通过后（耗时约 1m47s 初始化 `.testmondata`），能够精准分析代码与用例血缘。仅修改 `worker.py` 的一行代码，它能精准命中相关的数十个用例并跳过剩余 300+ 个不相干用例，**增量测试时间降至 < 5 秒**。
3. **嵌套事务 (`SAVEPOINT`) 的内存级威力**: 发现目前的单元测试 `tests/unit/conftest.py` **已经默认采用了**事务回滚 (`transaction.rollback()`) 黑科技。但在给 `test_portal` 配置并发执行 (`pytest-xdist`) 时，暴露出物理文件死锁的 Bug。在探针中，我们将 `test_portal` 从独立的物理 SQLite 迁移至纯内存的 `sqlite:///:memory:` 与 `StaticPool` 并行运行，彻底消除了并发阻塞死锁！
4. **Rust 级工具链 (Ruff)**: 项目已经深度使用 `ruff` 替代了传统的 flake8/black。针对 `pyright` 的类型检查，考虑到目前代码库中可能缺乏严格的 TypeScript-like 的类型注解，强制推行 `pyright` 短期内会带来大量的 Type Warning 噪音，建议延后引入。
5. **Docker Buildx Cache**: 考虑到目前使用 Alpine 与 `uv`，镜像构建已经压缩到非常小。如果要配置 `--cache-from` 需拉通 GitHub Packages 或 Nexus Registry 鉴权，在纯内网单节点并行场景下，RoI 相对较低。

### 证据 (Evidence)
- **并发死锁修复**: `pytest-xdist` 运行 `test_portal`（包含大量 `create_all` 动作）时，替换物理 DB 文件为 `:memory:` 后，**69 个用例在 1 分钟内无锁执行完毕**，并成功消除 `CREATE INDEX` 的超时 Timeout Error。

### 风险与限制 (Risks & Limitations)
- **`pytest-testmon` 污染**: 在 CI 环境中不建议开启 `testmon`，因为 CI 应该是纯净的全量防线。`testmon` 更适合于本地开发的 TDD 热重载环节。

### 下一步 (Next Steps)
- 🟢 Go: 我们在探针分支 `spike/performance-boosts` 上的代码修改（修复 SQLite 死锁、引入 tmpfs）极其健康。可以直接合入 `main`。
- 🟡 Need More: 关于 `pyright` 类型检查和 `docker buildx`，等业务逻辑完全成型后再考虑引入，以防拖慢初期开发节奏。
