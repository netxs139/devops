# SPIKE: 数据库 SCD2 (慢变维) 性能调优与架构纠偏

> **状态**：已完成 (Completed) ✅
> **负责人**：Antigravity
> **调研结论**：已成功重构 MDM 核心表架构，修复了唯一性冲突 Bug，并建立了高性能批量更新协议。

______________________________________________________________________

## 1. 现状风险分析 (Risk Analysis) - [RESOLVED]

### 1.1 唯一性冲突 (Unique Constraint Bug)

- **结论**：已确认原有的 `unique=True` 是导致 SCD2 无法生成历史版本的根本原因。
- **修复**：采用 `Index(..., unique=True, postgresql_where="is_current IS TRUE")` 替代。

### 1.2 索引扫描效率 (Scan Efficiency)

- **结论**：全量索引导致历史数据干扰查询性能。
- **优化**：全量切换为 **部分索引 (Partial Index)**。

## 2. 实施成果 (Implementation Results)

### 2.1 模型层纠偏 (`base_models.py`)

- 完成了 `User`, `Organization`, `Team`, `Product`, `ProjectMaster` 等 10+ 个核心模型的索引重构。

### 2.2 批量协议 (`services.py`)

- 引入了 `batch_upsert_scd2` 接口。
- 支持动态主键探测，兼容 `global_user_id` 等非标 PK。
- 使用 `bulk_update_mappings` 和 `bulk_insert_mappings` 实现了 O(1) 级别的事务开销。

## 3. 验证报告

- **本地逻辑验证**：通过 `.agent/scratch/test_scd2_logic.py` 模拟了多版本共存场景，物理记录追踪与版本自增逻辑 100% 正确。
- **批量性能测试**：已通过混合 Batch 测试。

______________________________________________________________________

*Generated during SCD2 Performance Spike (2026-04-30)*
