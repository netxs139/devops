# Service Desk 与 GitLab Issue 字段对应关系分析

## 📊 字段对比总结

**回答您的问题**:

**部分是，部分不是**。Service Desk 的字段设计**参考了** GitLab Issue 的 Bug 和需求字段，但做了**简化和调整**，以适应业务方（非技术人员）的使用场景。

______________________________________________________________________

## 🔍 详细对比分析

### 1. Bug 字段对比

#### TEST HUB 专业 Bug（`BugCreate`）- 技术人员使用

```python
class BugCreate(BaseModel):
    title: str                    # 标题
    severity: str                 # 严重程度 (S0-S3)
    priority: str = "P2"          # 优先级 (P0-P3)
    category: str                 # 缺陷分类 ⭐ 专业字段
    source: str                   # 缺陷来源 ⭐ 专业字段
    province: str                 # 省份/地域
    environment: str              # 环境
    steps_to_repro: str          # 复现步骤
    actual_result: str           # 实际结果
    expected_result: str         # 期望结果
    linked_case_iid: int         # 关联测试用例 ⭐ 专业字段
    linked_req_iid: Optional[int] # 关联需求 ⭐ 专业字段
```

**字段数**: 12 个\
**特点**: 专业、完整、需要技术背景

______________________________________________________________________

#### Service Desk Bug（`ServiceDeskBugSubmit`）- 业务方使用

```python
class ServiceDeskBugSubmit(BaseModel):
    requester_name: str          # 提交人姓名 ⭐ Service Desk 特有
    requester_email: str         # 提交人邮箱 ⭐ Service Desk 特有
    title: str                   # 标题 ✅ 对应
    severity: str                # 严重程度 (S0-S3) ✅ 对应
    priority: str = "P2"         # 优先级 (P0-P3) ✅ 对应
    province: str = "nationwide" # 省份/地域 ✅ 对应
    environment: str             # 环境 ✅ 对应
    steps_to_repro: str         # 复现步骤 ✅ 对应
    actual_result: str          # 实际结果 ✅ 对应
    expected_result: str        # 期望结果 ✅ 对应
    attachments: Optional[List[str]] # 附件链接 ⭐ Service Desk 特有
```

**字段数**: 11 个\
**特点**: 简化、易用、无需技术背景

______________________________________________________________________

#### Bug 字段对应表

| 字段 | TEST HUB Bug | Service Desk Bug | 对应关系 | 说明 |
|------|-------------|------------------|---------|------|
| 标题 | ✅ title | ✅ title | 完全对应 | - |
| 严重程度 | ✅ severity | ✅ severity | 完全对应 | S0-S3 |
| 优先级 | ✅ priority | ✅ priority | 完全对应 | P0-P3 |
| 省份/地域 | ✅ province | ✅ province | 完全对应 | - |
| 环境 | ✅ environment | ✅ environment | 完全对应 | production/staging/test |
| 复现步骤 | ✅ steps_to_repro | ✅ steps_to_repro | 完全对应 | - |
| 实际结果 | ✅ actual_result | ✅ actual_result | 完全对应 | - |
| 期望结果 | ✅ expected_result | ✅ expected_result | 完全对应 | - |
| 缺陷分类 | ✅ category | ❌ 无 | **不对应** | 专业字段，业务方难以理解 |
| 缺陷来源 | ✅ source | ❌ 无 | **不对应** | 专业字段，业务方难以理解 |
| 关联测试用例 | ✅ linked_case_iid | ❌ 无 | **不对应** | 业务方不了解测试用例 |
| 关联需求 | ✅ linked_req_iid | ❌ 无 | **不对应** | 业务方不了解需求 IID |
| 提交人姓名 | ❌ 无 | ✅ requester_name | **Service Desk 特有** | 用于识别业务方 |
| 提交人邮箱 | ❌ 无 | ✅ requester_email | **Service Desk 特有** | 用于通知和追踪 |
| 附件链接 | ❌ 无 | ✅ attachments | **Service Desk 特有** | 业务方提供截图 |

**对应率**: 8/12 = **66.7%**

______________________________________________________________________

### 2. 需求字段对比

#### TEST HUB 需求（`RequirementCreate`）- 技术人员使用

```python
class RequirementCreate(BaseModel):
    title: str                   # 标题
    description: str = ""        # 描述
    priority: str = "P2"         # 优先级
    req_type: str = "feature"    # 需求类型
    province: str = "nationwide" # 省份/地域
```

**字段数**: 5 个\
**特点**: 简洁、技术导向

______________________________________________________________________

#### Service Desk 需求（`ServiceDeskRequirementSubmit`）- 业务方使用

```python
class ServiceDeskRequirementSubmit(BaseModel):
    requester_name: str          # 提交人姓名 ⭐ Service Desk 特有
    requester_email: str         # 提交人邮箱 ⭐ Service Desk 特有
    title: str                   # 标题 ✅ 对应
    description: str             # 描述 ✅ 对应
    priority: str = "P2"         # 优先级 ✅ 对应
    req_type: str = "feature"    # 需求类型 ✅ 对应
    province: str = "nationwide" # 省份/地域 ✅ 对应
    expected_delivery: Optional[str] # 期望交付时间 ⭐ Service Desk 特有
```

**字段数**: 8 个\
**特点**: 增强、业务友好

______________________________________________________________________

#### 需求字段对应表

| 字段 | TEST HUB 需求 | Service Desk 需求 | 对应关系 | 说明 |
|------|--------------|------------------|---------|------|
| 标题 | ✅ title | ✅ title | 完全对应 | - |
| 描述 | ✅ description | ✅ description | 完全对应 | - |
| 优先级 | ✅ priority | ✅ priority | 完全对应 | P0-P3 |
| 需求类型 | ✅ req_type | ✅ req_type | 完全对应 | feature/enhancement/bugfix |
| 省份/地域 | ✅ province | ✅ province | 完全对应 | - |
| 提交人姓名 | ❌ 无 | ✅ requester_name | **Service Desk 特有** | 用于识别业务方 |
| 提交人邮箱 | ❌ 无 | ✅ requester_email | **Service Desk 特有** | 用于通知和追踪 |
| 期望交付时间 | ❌ 无 | ✅ expected_delivery | **Service Desk 特有** | 业务方关注的时间 |

**对应率**: 5/5 = **100%**（核心字段完全对应）

______________________________________________________________________

## 🎯 设计原则

### 1. **核心字段保持一致**

Service Desk 保留了 TEST HUB 的核心字段：

- ✅ 标题、描述
- ✅ 严重程度、优先级
- ✅ 省份/地域
- ✅ 环境
- ✅ 复现步骤、实际/期望结果
- ✅ 需求类型

**目的**: 确保数据可以无缝同步到 GitLab Issue

______________________________________________________________________

### 2. **移除专业字段**

Service Desk 移除了技术性强的字段：

- ❌ category（缺陷分类）- 需要了解缺陷分类体系
- ❌ source（缺陷来源）- 需要了解来源定义
- ❌ linked_case_iid（关联测试用例）- 业务方不了解测试用例
- ❌ linked_req_iid（关联需求）- 业务方不了解需求 IID

**目的**: 降低使用门槛，业务方无需技术背景

______________________________________________________________________

### 3. **增加业务字段**

Service Desk 增加了业务相关字段：

- ✅ requester_name（提交人姓名）
- ✅ requester_email（提交人邮箱）
- ✅ attachments（附件链接）- Bug 专用
- ✅ expected_delivery（期望交付时间）- 需求专用

**目的**:

- 识别和联系业务方
- 提供业务方关注的信息
- 方便追踪和通知

______________________________________________________________________

## 📋 GitLab Issue 中的体现

### Bug 在 GitLab 中的存储

当 Service Desk 提交 Bug 时，在 GitLab Issue 中：

**标题**:

```
[Service Desk] 登录页面无法正常显示
```

**描述**（Markdown 格式）:

```markdown
## 🐛 业务方缺陷报告 (Service Desk)

**报告人**: 张三 (zhangsan@example.com)  
**追踪码**: BUG-20251227-001

### 缺陷信息
- **严重程度**: S2
- **优先级**: P2
- **省份/地域**: 广东
- **环境**: production

### 复现步骤
1. 打开登录页面
2. 输入用户名和密码
3. 点击登录按钮

### 实际结果
页面显示空白，无法登录

### 期望结果
应该正常跳转到主页

### 附件
- https://example.com/screenshot1.png

---
*此缺陷由业务方通过 Service Desk 提交，请及时处理并回复。*
```

**标签**:

```
type::bug
severity::S2
priority::P2
province::广东
origin::service-desk
```

______________________________________________________________________

### 需求在 GitLab 中的存储

**标题**:

```
[Service Desk] 增加数据导出功能
```

**描述**:

```markdown
## 📋 业务方需求提交 (Service Desk)

**提交人**: 李四 (lisi@example.com)  
**追踪码**: REQ-20251227-001

### 需求信息
- **需求类型**: feature
- **优先级**: P2
- **省份/地域**: nationwide
- **期望交付时间**: 2025-02-01

### 需求描述
希望能够将报表数据导出为 Excel 格式...

---
*此需求由业务方通过 Service Desk 提交，请评审后进入开发流程。*
```

**标签**:

```
type::requirement
req-type::feature
priority::P2
province::nationwide
origin::service-desk
review-state::draft
```

______________________________________________________________________

## 🔄 字段映射关系

### Service Desk → GitLab Issue

| Service Desk 字段 | GitLab 存储位置 | 存储方式 |
|------------------|----------------|---------|
| title | Issue.title | 添加 `[Service Desk]` 前缀 |
| severity | Issue.labels | `severity::{value}` |
| priority | Issue.labels | `priority::{value}` |
| province | Issue.labels | `province::{value}` |
| environment | Issue.description | Markdown 表格 |
| steps_to_repro | Issue.description | Markdown 章节 |
| actual_result | Issue.description | Markdown 章节 |
| expected_result | Issue.description | Markdown 章节 |
| requester_name | Issue.description | Markdown 元数据 |
| requester_email | Issue.description | Markdown 元数据 |
| attachments | Issue.description | Markdown 列表 |
| req_type | Issue.labels | `req-type::{value}` |
| expected_delivery | Issue.description | Markdown 表格 |
| tracking_code | Issue.description | Markdown 元数据 |

______________________________________________________________________

## 💡 设计优势

### 1. **兼容性**

- 核心字段与 TEST HUB 一致
- 可以无缝同步到 GitLab
- 技术团队可以在 GitLab 中正常处理

### 2. **易用性**

- 移除专业术语
- 业务方容易理解
- 降低使用门槛

### 3. **可追踪性**

- 记录提交人信息
- 生成唯一追踪码
- 方便状态查询

### 4. **灵活性**

- 支持附件链接
- 支持期望交付时间
- 满足业务方需求

______________________________________________________________________

## 📊 总结对比

| 维度 | TEST HUB Bug/需求 | Service Desk Bug/需求 |
|------|------------------|---------------------|
| **目标用户** | 技术人员（测试、开发） | 业务方（非技术人员） |
| **字段数量** | Bug: 12, 需求: 5 | Bug: 11, 需求: 8 |
| **核心字段** | 完整、专业 | 简化、易用 |
| **专业字段** | 有（category, source, linked\_*） | 无 |
| **业务字段** | 无 | 有（requester\_*, attachments, expected_delivery） |
| **使用门槛** | 需要技术背景 | 无需技术背景 |
| **GitLab 兼容** | 直接创建 Issue | 通过 Markdown 模板创建 |
| **字段对应率** | - | Bug: 66.7%, 需求: 100% |

______________________________________________________________________

## ✅ 结论

**Service Desk 的字段设计**：

1. **核心字段基于 GitLab Issue**：保留了 severity, priority, province, environment 等核心字段
1. **移除了专业字段**：去掉了 category, source, linked_case_iid 等技术性字段
1. **增加了业务字段**：添加了 requester_name, requester_email, attachments 等业务相关字段
1. **通过 Markdown 模板桥接**：将 Service Desk 的简化字段映射到 GitLab Issue 的描述和标签中

**这种设计既保证了与 GitLab 的兼容性，又降低了业务方的使用门槛，是一个很好的平衡方案。** ✨

______________________________________________________________________

**创建时间**: 2025-12-27\
**版本**: v1.0
