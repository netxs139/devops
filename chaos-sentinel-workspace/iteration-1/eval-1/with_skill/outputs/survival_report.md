# 《生存报告》: 数据库连接池挤压测试 (Eval-1)

## 1. 破坏点 (Blast Radius)

- **目标**: `SQLAlchemy Engine` (SQLite)
- **注入手段**: `ChaosEngine.db_pool_starvation(count=5)`
- **触发状态**: 通过强制占满 5 个连接，模拟高并发写入 `AuditLog` 的极端场景。

## 2. 生存状态 (Status)

- **结论**: **[优雅失效]**
- **表现**: 业务事务在尝试写入审计日志时触发了 `sqlalchemy.exc.TimeoutError`。
- **韧性证据**:
  - 审计监听器 `capture_audit_event` 正确捕获了异常。
  - 业务事务（User Creation）未被中断，返回了成功响应。
  - 日志记录: `[AUDIT-ENGINE] Audit record failed: (sqlite3.OperationalError) database is locked`

## 3. 改进建议

- 建议将 `db_pool_starvation` 注入阈值设置为动态，以适配不同的 `max_overflow` 配置。
- Audit Log 的写入可以考虑使用 **独立连接池** 隔离，彻底防止审计层耗尽业务层资源。
