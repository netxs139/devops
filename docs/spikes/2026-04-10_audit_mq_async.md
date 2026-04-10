## Spike 结论报告: 审计写入异步化方案设计 [MANDATORY TAG: [Spike-Result]]

- **日期**: 2026-04-10
- **耗时**: 1.5h / 时间盒 4h
- **结论**: 🟢 Go 

### 发现 (Findings)
1. **基于 RabbitMQ 可完全复用现有基石引擎**: 我们在代码库里探索后发现，`devops_collector/mq.py` 提供了一个强大的 `MessageQueue` 客户端并挂载了心跳保活。完全可以通过动态拓展 `sys_audit_logs_queue` 来让 Pika 客户端直接为我们在 `after_update` 等钩子产生事件时进行削峰式投递。
2. **`bulk_save` 消费批处理模式可行性**: 在 `/tmp/spike_audit_mq/` 中进行的快速 POC (Proof-of-Concept) 验证证明，可以令 Consumer 层挂载基于 `prefetch_count` (例如 500次) 和 `inactivity_timeout` 的双端限流收集器，批量将 AuditLog 行级写盘化整为零，从而大幅度降低数据库事务碰撞阻塞，特别是能完美规避现有 SQLite 的死锁隐患。
3. **隔离性强**: 方案对原业务代码零侵入，只需要在 `devops_collector/models/audit_events.py` 中将原有的 `connection.execute(insert(...))` 替换成 `mq_client.publish_task()` 即可。

### 证据 (Evidence)
- **代码结构解耦POC**: `/tmp/spike_audit_mq/test_mq_spike.py` 已实现了基础的“事件收集序列化 -> MQ投递 -> 按 Batch+Timeout 脱水冲刷”生命周期骨架。其脱水算法通过 `delivery_tag` 能够保障事务层一旦执行插入失败，整个 Batch 返回 NACK 而进行重试防丢。

### 风险与限制 (Risks & Limitations)
- **依赖强制性**: 方案使底层审计日志与网络和 RabbitMQ 容量严重绑定。若配置错误的 VHost 或队列引发队列满了或无消费（如 Broker 拒绝服务），会导致 API 线程在尝试 `basic_publish` 时受阻，严重时可能阻塞普通业务 API，除非引入异步推送进程或更强硬的 `try..except` Fallback。

### 下一步 (Next Steps)
- 🟢 **Go**: 转为 [L3] 正式任务。下一步可开始清理 `/tmp/spike_audit_mq`，并开始执行具体改造：
  1. 在 `mq.py` 中注册 `sys_audit_tasks` 队列。
  2. 重构 `devops_collector/models/audit_events.py` 发送至新队列。
  3. 为 `devops_collector/worker.py` 补充挂载消费者协程逻辑并对接持久化数据库。
