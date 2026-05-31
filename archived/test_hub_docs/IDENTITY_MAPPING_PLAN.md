# Service Desk 动态身份关联与重构实施计划

## 📋 优化目标

消除代码中硬编码的 `user_id = 1`，建立 Service Desk 用户与 GitLab 操作者身份的动态关联机制，实现真实的操作审计。

______________________________________________________________________

## 🎯 实施步骤

### 阶段 1: 后端模型与逻辑重构 (main.py)

1. **增强用户模型**: 在 `SERVICE_DESK_USERS` 中增加 `gitlab_user_id` 字段，默认为 `None`。
1. **实现操作者获取函数**: 编写 `get_current_gitlab_user_id(token)`，根据 Session 动态获取关联的 GitLab ID。
1. **重构 Issue 创建/更新逻辑**: 将所有硬编码的 `1` 替换为动态获取的值。
1. **增强管理员 API**: 允许管理员在审批时指定关联的 GitLab 用户。

### 阶段 2: 前端页面增强

1. **更新管理员页面 (`service_desk_admin.html`)**:
   - 审批弹窗中增加 "关联 GitLab User ID" 输入框。
   - 列表展示用户关联的 GitLab ID。
1. **更新我的工单页面**: 在提交或操作时带上正确的身份信息。

______________________________________________________________________

## 🔧 详细技术方案

### 1. 动态身份获取逻辑

```python
def get_current_gitlab_user_id(token: str) -> int:
    """根据 Service Desk Token 获取关联的 GitLab 用户 ID

    1. 验证 token 有效性
    2. 获取对应的 email
    3. 在 SERVICE_DESK_USERS 中查找关联的 gitlab_user_id
    4. 如果没有关联，返回默认机器人 ID (1)
    """
    if token not in SESSION_TOKENS:
        return 1 # 默认回退到管理员

    email = SESSION_TOKENS[token]["email"]
    user_info = SERVICE_DESK_USERS.get(email, {})
    return user_info.get("gitlab_user_id") or 1
```

______________________________________________________________________

## 📊 进度表

| 步骤 | 内容 | 状态 |
|------|------|------|
| 1.1 | 增强数据模型与载入逻辑 | ⏳ 准备中 |
| 1.2 | 重构核心 API 调用的 user_id | ⏳ 准备中 |
| 2.1 | 管理员页面增加关联字段 | ⏳ 准备中 |

______________________________________________________________________

**开始实施！**
