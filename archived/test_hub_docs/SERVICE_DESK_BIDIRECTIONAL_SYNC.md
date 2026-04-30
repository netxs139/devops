# Service Desk 双向同步功能文档

## 📋 功能概述

Service Desk 现已实现与 GitLab Issue 的**完整双向同步**，确保两个系统的数据始终保持一致。

______________________________________________________________________

## 🔄 双向同步机制

### 1. GitLab → Service Desk（自动同步）

**触发方式**: GitLab Webhook\
**触发事件**: Issue Hook\
**同步时机**: GitLab Issue 发生任何变更时

#### 同步内容

| GitLab 字段 | Service Desk 字段 | 说明 |
|------------|------------------|------|
| `state` (closed) | `status` (completed) | Issue 关闭 → 工单完成 |
| `labels` (in-progress) | `status` (in-progress) | 添加处理中标签 → 工单处理中 |
| `labels` (rejected) | `status` (rejected) | 添加拒绝标签 → 工单已拒绝 |
| `state` (opened) | `status` (pending) | Issue 打开 → 工单待处理 |
| `title` | `title` | 标题同步（自动去除 [Service Desk] 前缀） |
| `updated_at` | `updated_at` | 更新时间同步 |

#### 识别机制

通过 `origin::service-desk` 标签识别 Service Desk 工单，只同步带此标签的 Issue。

#### 实现代码位置

`main.py` - `gitlab_webhook()` 函数（约 1450 行）

```python
# --- Service Desk 工单双向同步（GitLab → Service Desk）---
if "origin::service-desk" in labels:
    # 查找对应工单并同步状态、标题、时间
    # 自动持久化保存
```

______________________________________________________________________

### 2. Service Desk → GitLab（API 触发）

**触发方式**: REST API\
**API 端点**: `PATCH /service-desk/tickets/{tracking_code}/status`\
**触发时机**: 管理员或系统主动更新工单状态时

#### API 参数

```json
{
  "new_status": "in-progress",  // 必填: pending, in-progress, completed, rejected
  "comment": "开始处理此工单"    // 可选: 状态变更备注
}
```

#### 同步内容

| Service Desk 状态 | GitLab 操作 | 说明 |
|------------------|------------|------|
| `completed` | `state_event: close` | 关闭 Issue |
| `rejected` | `state_event: close` + 添加 `status::rejected` 标签 | 关闭并标记为已拒绝 |
| `in-progress` | 添加 `in-progress` 标签 | 标记为处理中 |
| `pending` | 移除 `in-progress` 标签 | 移除处理中标记 |

#### 额外功能

1. **自动添加评论**: 在 GitLab Issue 中添加状态变更记录
1. **智能重开**: 如果 Issue 已关闭但状态改为 `in-progress` 或 `pending`，自动重新打开
1. **标签管理**: 自动添加/移除相关标签

#### 返回示例

```json
{
  "status": "success",
  "tracking_code": "BUG-20251227-001",
  "old_status": "pending",
  "new_status": "in-progress",
  "gitlab_synced": true,
  "gitlab_message": "已添加处理中标签",
  "message": "工单状态已从 pending 更新为 in-progress"
}
```

______________________________________________________________________

## 🎯 使用场景

### 场景 1: 业务方提交 Bug

1. 业务方通过 Service Desk 提交 Bug
1. 系统自动在 GitLab 创建 Issue（带 `origin::service-desk` 标签）
1. 技术团队在 GitLab 中处理 Issue
1. **自动同步**: GitLab 的任何变更自动同步到 Service Desk
1. 业务方通过追踪码查看最新状态

### 场景 2: 管理员更新工单状态

1. 管理员调用 API 更新工单状态为 `in-progress`
1. **自动同步**: GitLab Issue 自动添加 `in-progress` 标签
1. **自动评论**: GitLab Issue 中自动添加状态变更记录
1. 技术团队在 GitLab 中看到最新状态

### 场景 3: 技术团队关闭 Issue

1. 技术团队在 GitLab 中关闭 Issue
1. **Webhook 触发**: GitLab 发送 Issue Hook 到 Service Desk
1. **自动同步**: Service Desk 工单状态自动更新为 `completed`
1. **持久化保存**: 状态变更自动保存到 JSON 文件
1. 业务方查询时看到工单已完成

______________________________________________________________________

## 🔧 配置 Webhook

### 步骤 1: 在 GitLab 中配置 Webhook

1. 进入 GitLab 项目
1. 导航到 **Settings** → **Webhooks**
1. 添加新的 Webhook：
   - **URL**: `http://your-server:8000/webhook`
   - **Trigger**: 勾选 `Issue events`
   - **SSL verification**: 根据实际情况选择
1. 点击 **Add webhook**

### 步骤 2: 测试 Webhook

1. 在 Webhook 列表中找到刚添加的 Webhook
1. 点击 **Test** → **Issue events**
1. 检查响应状态（应该返回 200）

### 步骤 3: 验证同步

1. 在 GitLab 中修改一个 Service Desk Issue
1. 检查 Service Desk 工单状态是否自动更新
1. 查看日志确认同步成功

______________________________________________________________________

## 📊 状态映射表

### GitLab → Service Desk

| GitLab 状态 | GitLab 标签 | Service Desk 状态 |
|------------|------------|------------------|
| opened | - | pending |
| opened | in-progress | in-progress |
| opened | status::rejected | rejected |
| closed | - | completed |
| closed | status::rejected | rejected |

### Service Desk → GitLab

| Service Desk 状态 | GitLab 操作 |
|------------------|------------|
| pending | 移除 in-progress 标签，重开 Issue（如已关闭） |
| in-progress | 添加 in-progress 标签，重开 Issue（如已关闭） |
| completed | 关闭 Issue |
| rejected | 关闭 Issue + 添加 status::rejected 标签 |

______________________________________________________________________

## 🧪 测试双向同步

### 方法 1: 使用测试脚本

```bash
python test_bidirectional_sync.py
```

测试脚本会：

1. 提交一个测试工单
1. 通过 API 更新状态（Service Desk → GitLab）
1. 查询工单状态验证同步
1. 提供手动测试 Webhook 的指导

### 方法 2: 手动测试

#### 测试 Service Desk → GitLab

```bash
# 1. 提交工单
curl -X POST "http://localhost:8000/service-desk/submit-bug?project_id=1" \
  -H "Content-Type: application/json" \
  -d '{"requester_name":"测试","requester_email":"test@example.com","title":"测试","severity":"S2","priority":"P2","province":"nationwide","environment":"test","steps_to_repro":"测试","actual_result":"测试","expected_result":"测试"}'

# 2. 更新状态
curl -X PATCH "http://localhost:8000/service-desk/tickets/BUG-20251227-001/status?new_status=in-progress&comment=开始处理"

# 3. 在 GitLab 中验证 Issue 是否添加了 in-progress 标签
```

#### 测试 GitLab → Service Desk

1. 在 GitLab 中找到 Service Desk Issue（带 `origin::service-desk` 标签）
1. 添加 `in-progress` 标签或关闭 Issue
1. 查询工单状态：
   ```bash
   curl http://localhost:8000/service-desk/track/BUG-20251227-001
   ```
1. 验证状态是否已自动更新

______________________________________________________________________

## 🔍 日志监控

### 查看同步日志

同步操作会记录详细日志：

**GitLab → Service Desk 同步成功**:

```
✅ Service Desk Sync: BUG-20251227-001 status updated from GitLab: pending → in-progress
```

**Service Desk → GitLab 同步成功**:

```
✅ Service Desk → GitLab Sync: BUG-20251227-001 status updated: pending → in-progress
```

**同步失败**:

```
❌ Failed to sync status to GitLab for BUG-20251227-001: [错误信息]
```

______________________________________________________________________

## ⚠️ 注意事项

### 1. Webhook 配置

- 确保 Service Desk 服务可以从 GitLab 访问
- 如果使用 HTTPS，确保证书有效
- 测试 Webhook 连通性

### 2. 权限要求

- GitLab Token 需要有 Issue 的读写权限
- Webhook 需要配置在项目级别

### 3. 冲突处理

- 如果同时在两边修改状态，以最后一次操作为准
- 建议通过一个系统进行主要操作

### 4. 性能考虑

- Webhook 是异步处理，不会阻塞 GitLab 操作
- 状态更新 API 会等待 GitLab 同步完成
- 大量并发更新时注意 GitLab API 限流

______________________________________________________________________

## 🚀 API 使用示例

### Python 示例

```python
import requests

# 更新工单状态
def update_ticket_status(tracking_code, new_status, comment=None):
    url = f"http://localhost:8000/service-desk/tickets/{tracking_code}/status"
    params = {
        "new_status": new_status,
        "comment": comment
    }
    
    response = requests.patch(url, params=params)
    return response.json()

# 使用示例
result = update_ticket_status(
    "BUG-20251227-001", 
    "in-progress",
    "技术团队已开始处理此问题"
)

print(f"同步状态: {result['gitlab_synced']}")
print(f"同步信息: {result['gitlab_message']}")
```

### JavaScript 示例

```javascript
async function updateTicketStatus(trackingCode, newStatus, comment) {
    const url = `http://localhost:8000/service-desk/tickets/${trackingCode}/status`;
    const params = new URLSearchParams({
        new_status: newStatus,
        comment: comment || ''
    });
    
    const response = await fetch(`${url}?${params}`, {
        method: 'PATCH'
    });
    
    return await response.json();
}

// 使用示例
const result = await updateTicketStatus(
    'BUG-20251227-001',
    'in-progress',
    '技术团队已开始处理此问题'
);

console.log('同步状态:', result.gitlab_synced);
console.log('同步信息:', result.gitlab_message);
```

______________________________________________________________________

## 📈 功能对比

| 功能 | 实现前 | 实现后 |
|------|--------|--------|
| GitLab → Service Desk | ❌ 仅查询时同步 | ✅ Webhook 实时同步 |
| Service Desk → GitLab | ❌ 不支持 | ✅ API 主动同步 |
| 状态同步 | ⚠️ 部分支持 | ✅ 完整支持 |
| 标题同步 | ❌ 不支持 | ✅ 支持 |
| 时间同步 | ✅ 支持 | ✅ 支持 |
| 评论记录 | ❌ 不支持 | ✅ 自动添加 |
| 标签管理 | ❌ 不支持 | ✅ 自动管理 |

______________________________________________________________________

## ✅ 总结

Service Desk 现已实现**完整的双向同步**：

1. **GitLab → Service Desk**: 通过 Webhook 实时自动同步
1. **Service Desk → GitLab**: 通过 API 主动同步
1. **数据一致性**: 两个系统的状态始终保持同步
1. **审计追踪**: 所有状态变更都有日志和评论记录
1. **持久化保存**: 所有变更自动保存到 JSON 文件

______________________________________________________________________

**更新时间**: 2025-12-27\
**版本**: v2.0 - 双向同步版本
