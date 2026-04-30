# ADR 005: 门禁防御全量左移与并发提速策略 (Full Gate Left-Shift & Concurrency)

## 状态 (Status)

**已接受 (Accepted)** - 2026-04-23

## 背景 (Context)

DevOps 平台引入了极其严格的 L1-L4 级别门禁（包含 Ruff 格式化、Bandit 安全扫描、detect-secrets 机密泄露扫描、pytest 覆盖率校验等）。
由于早期的 `gatekeeper.py` 以及 GitLab CI 采用完全串行的全量执行模式，随着项目规模扩大，每次本地提交及云端 CI 均需耗费 3-5 分钟以上。长反馈弧严重拖慢了研发节奏，导致“频繁提交”的敏捷原则受阻，开发者为了绕过漫长的等待，甚至产生了违规跳过门禁的冲动。

## 决策 (Decision)

我们决定对流水线防御阵地进行**左移 (Left-Shift)**，并通过**并行化 (Concurrency)** 来大幅缩短反馈时间：

1. **L1 轻量级检查彻底左移 (Pre-commit)**：

   - 引入 `pre-commit` 框架，将 `Ruff`、`Bandit`、`detect-secrets` 等静态工具挂载于 Git Commit 阶段。
   - 这类检查仅需毫秒至秒级，阻断动作发生在本地代码存入版本库的瞬间，实现“零等待反馈”。
   - 强制隔离律：依赖 `.git` 元数据或高度依赖宿主机的工具（如 `detect-secrets`），严禁装入生产容器内运行，必须在宿主机经由 `uv run` 执行。

1. **单元测试引入极致加速插件**：

   - 引入 `pytest-xdist` 利用宿主机多核 CPU 实施并发测试。
   - 引入 `pytest-picked`，在日常开发时仅运行被 Git 标记为“已修改/未提交”的文件对应的测试用例（增量测试）。

1. **Gatekeeper.py 多线程统筹重构**：

   - 摒弃单纯的串行执行模式。
   - 利用 `concurrent.futures` 建立两大并行执行组。
   - **安全并发组**：`just security-audit` 与 `just verify` 同时被唤起并行执行，耗时取决于两者中最长的一方。
   - **构建并发组**：如果安全检测通过，进入下一阶段后，`just build`（镜像打包）与 `just dbt-build`（数据模型跑批）同时执行。

## 后果与影响 (Consequences)

**正面收益 (Positive)**:

- **反馈极速**：大部分愚蠢的语法和安全漏洞在 Commit 瞬间（\<2秒）即被拦截。全量门禁的运行时间断崖式下降至原本的 30% 以下。
- **强制对齐**：本地门禁脚本（`gatekeeper.py`）成为唯一真理（Single Source of Truth），GitLab CI 仅做空壳代理调用 `gatekeeper.py`，确保开发与生产的校验逻辑永远不分叉。

**负面影响/风险 (Negative/Risks)**:

- **输出交错 (Interleaved Output)**：由于多线程同时执行外部子进程，若控制不当，控制台输出会错乱。必须通过拦截 `stdout` 并延后统一打印来保证日志可读性。
- **环境隔离挑战**：部分测试或扫描对隔离度要求极高。本地并行运行测试时需要特别关注是否存在文件读写锁冲突或 SQLite in-memory 竞态问题（需依赖 pytest-xdist 的合理调度）。
