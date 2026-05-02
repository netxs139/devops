# ADR 0008: ORM 延迟解析隔离 (ORM Lazy Resolution Isolation)

## 状态 (Status)
已接受 (Accepted) - 2026-05-01

## 背景 (Context)
在 DevOps 平台的自动化测试（特别是全局集成测试）中，SQLAlchemy 的 ORM 映射存在“初始化污染”风险。

**核心问题：**
1. **Mock 污染**：当使用字符串（如 `relationship("User", ...)`）定义模型关系时，SQLAlchemy 会在测试发现阶段（Discovery）尝试解析这些字符串。如果此时 `User` 类已被 `unittest.mock` 替换为 `MagicMock`，SQLAlchemy 会将 Mock 对象存入全局 Mapper 注册表。
2. **初始化顺序崩溃**：跨插件的循环引用在全局扫描时极易引发 `NameError`。

## 决策 (Decision)
强制在所有 `relationship`、`primaryjoin` 和 `foreign_keys` 中使用 **lambda 表达式** 进行延迟解析。

**物理规范：**
- 严禁使用裸字符串：`relationship("SomeClass", foreign_keys="SomeClass.id")` ❌
- 强制使用 lambda：`relationship("SomeClass", primaryjoin=lambda: MyClass.id == SomeClass.id)` ✅

## 后果 (Consequences)
- **正面**：彻底隔离了 Mock 环境对 ORM 映射的侵入，确保全局测试的稳定性。
- **负面**：代码略显冗长，且需要开发者意识到 `lambda` 的重要性。
- **自动审计**：该决策已通过 `ARCH-009` 自动化审计规则固化，任何回归到字符串引用的尝试将被 CI 拦截。

## 意图锚点 (Intent Anchor)
此设计并非为了简洁，而是为了“物理隔离”。严禁以“重构简化”为由将其改回字符串形式。
