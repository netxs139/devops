# ADR 0007: SCD2 性能治理与部分索引 (Partial Index) 优化

## 状态 (Status)

**已接受 (Accepted)** - 2026-04-30

## 背景 (Context)

DevOps 平台的核心主数据（如 `User`, `Organization`）采用 **SCD Type 2 (慢变维)** 模式进行历史追踪。
在早期实施中遇到了严重的物理冲突：

1. **唯一性冲突 (Unique Violation)**：业务要求在逻辑上确保“当前有效”的记录唯一（例如，一个工号同时只能属于一个活跃员工）。但在数据库表级设置 `unique=True` 会导致在插入历史快照时报错，因为旧版本记录占据了该业务键。
1. **查询性能退化**：随着历史快照增多（版本数 N 远大于当前活跃记录数），执行“获取当前有效状态”的查询性能随全表扫描而线性下降。
1. **静默失败风险**：由于 SQLAlchemy 在处理 `unique=True` 时可能无法正确感知 SCD 历史行，导致开发者误以为数据同步正常，实际由于约束冲突导致数据丢失。

## 决策 (Decision)

我们决定通过 **PostgreSQL 部分索引 (Partial Index)** 协议来重构 SCD2 的唯一性防线：

1. **废弃全局物理唯一约束**：

   - 在继承了 `SCDMixin` 的模型中，严禁在业务键（如 `org_code`, `emp_id`）上直接声明 `unique=True`。

1. **实施逻辑唯一性屏障 (Logical Unique Guard)**：

   - 使用 SQLAlchemy 的 `Index` 构造器手动创建索引。
   - 必须通过 `postgresql_where` 参数指定 `is_current IS TRUE` 过滤条件。
   - 示例：`Index("idx_unique_active_user", User.emp_id, unique=True, postgresql_where=(User.is_current == True))`

1. **高性能批量接口 (Batch Upsert Protocol)**：

   - 交付 `batch_upsert_scd2` 服务接口。
   - 核心逻辑：利用 `batch_update_mappings` 将旧版本 `is_current` 置为 `False`，并使用 `bulk_insert_mappings` 写入新版本，将事务开销降至最低。

## 后果与影响 (Consequences)

**正面收益 (Positive)**:

- **物理兼容**：完美解决了“活跃记录唯一”与“历史快照并存”的矛盾。
- **查询加速**：部分索引体积远小于全量索引，显著提升了 `is_current=True` 场景下的检索性能。
- **架构解耦**：将版本管理逻辑从应用代码下沉至数据库索引层，增强了数据一致性。

**负面影响/风险 (Negative/Risks)**:

- **方言依赖**：`postgresql_where` 是 PG 特有语法，这进一步强化了本项目对 PostgreSQL 的方言绑定（已在 `contexts.md` 声明）。
- **迁移复杂度**：存量数据的唯一约束需要通过 Alembic 手动编写 `DROP` 与 `CREATE INDEX` 逻辑，不能仅依赖自动生成的 `unique=True` 变更。
