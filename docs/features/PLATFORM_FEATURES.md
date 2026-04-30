# 平台核心功能详解 (Platform Core Features)

除了数据采集，本平台内置了多项企业级管理与 AI 辅助能力。

## 1. 企业级 RBAC 2.0 权限体系 🚀

系统内置了工业级的权限引擎，实现了从“功能权限”到“行级数据权限”的深度管控：

- **标准化模型**: 基于 `sys_role`, `sys_menu`, `sys_user_roles`, `sys_role_menu`, `sys_role_dept`。
- **多维行级隔离 (RLS)**: 支持“全部数据”、“自定义部门”、“本部门及以下”、“仅本人”等五大权限范围。系统通过 `data_scope` 自动在查询层注入 SQL 过滤条件。
- **JWT 动态同步**: Token 载荷中实时注入用户的角色、权限标识符及最优 `data_scope`。

## 2. 智能测试管理 (GTM - Generic Test Management) 🚀

针对 GitLab 社区版缺乏用例管理的痛点，提供嵌入式解决方案：

- **议题驱动存储**: 用例以 Markdown 模板形式存储在 GitLab Issues 中，利用 `type::test` 标签进行自动识别。
- **AI 辅助生成**: 利用 LLM 自动将验收标准 (AC) 转化为结构化测试步骤。
- **实时反馈 (SSE)**: 引入 Server-Sent Events，将测试执行结果毫秒级推送到用户浏览器。
- **地域质量分析**: 自动识别 `province::*` 标签，构建极坐标热力图定位缺陷积压地域。

## 3. 统一身份归一化 (Identity Resolver)

- **OneID 机制**: 优先基于 **Email** 将不同系统的账号归并到全局唯一的 `global_user_id`。
- **SCD Type 2**: 核心身份与组织主数据采用“生效/失效日期”管理，确保历史度量数据在人员调岗后仍可准确回溯。

## 4. 服务台与认证 (Service Desk & Auth)

- **独立认证**: 内置基于 OAuth2 + JWT 的用户注册/登录模块，不再依赖第三方 IM。
- **极简提单**: 提单页面自动透传登录态，业务人员无需重复输入部门等基础信息。

## 5. 智能归因与分类 (AI Enrichment)

- **自动化分类**: 基于 LLM 对 Commit 和 Issue 内容进行语义识别（Feature/Maintenance/Internal）。
- **置信度审计**: 记录 AI 分类的置信度，支持人工抽检。
