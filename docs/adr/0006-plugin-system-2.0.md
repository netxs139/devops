# ADR 0006: 插件系统 2.0 (声明式元数据与双阶段加载协议)

## 状态 (Status)

**已接受 (Accepted)** - 2026-04-30

## 背景 (Context)

DevOps 平台 1.0 版本的插件系统采用“自注册 (Self-Registration)”模式，在插件目录的 `__init__.py` 中直接导入 `Worker` 和 `Client` 类。
这导致了严重的物理副作用：

1. **启动性能瓶颈**：系统启动或加载 `PluginRegistry` 时，会触发所有插件逻辑类的全量导入。随着插件增多，启动时间呈线性增长。
1. **循环依赖风险**：由于核心基类 (`BasePlugin`) 与具体实现类在导入期交织，极易触发 `ImportError: cannot import name ... from partially initialized module`。
1. **环境脆弱性**：即使只启用一个插件，系统也会尝试导入所有插件的依赖库（如 Jenkins, SonarQube 等），如果宿主机缺失某个插件的特定 SDK，会导致整个平台无法启动。

## 决策 (Decision)

我们决定将插件架构升级为 **2.0 声明式协议 (Declarative Protocol)**，核心准则如下：

1. **元数据与逻辑物理隔离**：

   - 插件的 `__init__.py` 仅允许定义轻量级的 `PluginMetadata` 对象。
   - 严禁在 `__init__.py` 顶层导入 `Worker`、`Client` 或任何重型第三方 SDK。

1. **双阶段发现机制 (Two-Phase Discovery)**：

   - **第一阶段 (Discovery)**：系统仅扫描并加载各插件的 `PluginMetadata`，构建功能索引。此过程不涉及业务逻辑加载，性能损耗接近于零。
   - **第二阶段 (Execution)**：仅在真正需要执行任务时，通过 `get_worker_class()` 或 `get_client_class()` 动态导入业务类。

1. **可选钩子规范 (Optional Hooks)**：

   - 采用 `BasePlugin` 定义标准生命周期钩子 (`on_setup`, `on_teardown`)。
   - 默认实现为 `no-op`，并配合 `# noqa: B027` 消除静态审计告警。

## 后果与影响 (Consequences)

**正面收益 (Positive)**:

- **启动提速**：核心引擎启动时的模块导入深度减少约 70%。
- **架构健壮**：完全消除了插件间的交叉污染与循环依赖，支持插件按需动态加载。
- **依赖隔离**：未启用的插件即使缺失 SDK 也不再影响系统核心运行。

**负面影响/风险 (Negative/Risks)**:

- **开发门槛微增**：开发者需要额外维护 `PluginMetadata` 声明，且需习惯延迟加载模式。
- **反射开销**：动态导入在首次执行时会有微小的 CPU 开销，但相对于整体同步任务时间可忽略不计。
