# DevOps Platform API 路由清单

本文件详列了本项目的所有 API 接口路由定义，涵盖中台核心模块（测试管理、流水线质量、工单服务台、Traceability 协同雷达、安全扫描、后台管理等），作为开发与对接的唯一真实性数据源 (SSOT)。

______________________________________________________________________

## 📌 全局基础路由 (Global Base Routes)

注册于 \[main.py\](file:///home/netxs/devops/devops_portal/main.py) 的应用级基础接口：

| 请求方法 | 路由路径 | 功能描述 | 身份与权限校验 |
| :--- | :--- | :--- | :--- |
| `GET` | `/callback` | 兼容性重定向：将旧的根路径回调重定向到 API 路由 | 无 |
| `GET` | `/health` | 基础健康检查端点 | 无 |
| `GET` | `/notifications/stream` | SSE 通知流，实现实时状态更新推送 | 需要登录 |
| `Static` | `/static` | 静态资源挂载（前台 assets 目录） | 无 |
| `Static` | `/` | 静态网站承载挂载目录（fallback） | 无 |

______________________________________________________________________

## 🔒 认证模块 (Authentication)

路由前缀：`/auth` | 源码位置：\[auth_router.py\](file:///home/netxs/devops/devops_collector/auth/auth_router.py)

| 请求方法 | 路由路径 | 功能描述 | 参数与响应 |
| :--- | :--- | :--- | :--- |
| `GET` | `/gitlab/bind` | 发起 GitLab OAuth 绑定 | **Headers**: JWT Bearer Token |
| `GET` | `/gitlab/login` | 发起 GitLab OAuth 登录 | 无 |
| `GET` | `/gitlab/callback` | GitLab OAuth 回调处理 (登录/绑定) | **Query**: `code`, `state` |
| `POST` | `/register` | 注册新用户（验证公司邮箱域名） | **Body**: `AuthRegisterRequest` |
| `POST` | `/login` | 登录获取访问令牌 (RBAC 2.0 权限聚合) | **Form**: `OAuth2PasswordRequestForm` |
| `GET` | `/me` | 获取当前登录用户信息（含角色与组织） | **Headers**: JWT Bearer Token |

______________________________________________________________________

## 🧪 测试管理模块 (Test Management)

路由前缀：`/test-management` | 源码位置：\[test_management_router.py\](file:///home/netxs/devops/devops_portal/routers/test_management_router.py)

| 请求方法 | 路由路径 | 功能描述 | 权限要求 |
| :--- | :--- | :--- | :--- |
| `GET` | `/projects/{project_id}/test-cases` | 获取并解析 GitLab 项目中的所有用例 | 需登录 |
| `GET` | `/aggregated/test-cases` | 跨项目聚合获取测试用例 (产品/部门) | 需登录 |
| `GET` | `/aggregated/requirements` | 跨项目聚合获取需求及其追溯矩阵信息 | 需登录 |
| `POST` | `/projects/{project_id}/test-cases` | 在线录入并创建测试用例 | `maintainer`, `admin` |
| `POST` | `/projects/{project_id}/test-cases/import` | 批量从 Excel/CSV 导入测试用例 | `maintainer`, `admin` |
| `POST` | `/projects/{project_id}/test-cases/clone` | 从源项目克隆所有测试用例到当前项目 | `maintainer`, `admin` |
| `POST` | `/projects/{project_id}/test-cases/generate-from-ac` | **[AI]** 根据关联需求的验收标准自动生成步骤 | 需登录 |
| `GET` | `/projects/{project_id}/requirements` | 获取项目中的所有需求 | 需登录 |
| `GET` | `/projects/{project_id}/requirements/{iid}` | 获取单个需求详情 | 需登录 |
| `POST` | `/projects/{project_id}/requirements` | 创建新的需求 | 需登录 |
| `GET` | `/projects/{project_id}/bugs` | 获取项目中所有的缺陷 | 需登录 |
| `POST` | `/projects/{project_id}/defects` | QA 专业缺陷提报接口 | 需登录 |
| `POST` | `/projects/{project_id}/test-cases/{issue_iid}/execute` | 执行用例，更新标签、状态与审计记录 | `tester`, `maintainer`, `admin` |
| `GET` | `/projects/{project_id}/test-summary` | 获取测试用例执行状态的统计摘要 | 需登录 |
| `GET` | `/global/alerts` | 获取全网质量同步预警 | 无 |

______________________________________________________________________

## 📈 质量分析与门禁模块 (Quality Gate)

路由前缀：`/quality` | 源码位置：\[quality_router.py\](file:///home/netxs/devops/devops_portal/routers/quality_router.py)

| 请求方法 | 路由路径 | 功能描述 | 权限要求与依赖 |
| :--- | :--- | :--- | :--- |
| `GET` | `/projects/{project_id}/province-quality` | 获取各省份的质量分布数据 (数据隔离) | `rpt:quality:view` |
| `GET` | `/projects/{project_id}/quality-gate` | 自动化运行质量门禁合规性检查 | `rpt:quality:view` |
| `GET` | `/projects/{project_id}/test-summary` | 获取测试用例执行状态的统计摘要 (快捷路由) | `rpt:quality:view` |
| `GET` | `/projects/{project_id}/mr-summary` | 获取并计算合并请求 (MR) 的评审统计信息 | 需登录 |
| `GET` | `/projects/{project_id}/quality-report` | 动态生成质量分析报告 | 需登录 |

______________________________________________________________________

## 💁 工单服务台 (Service Desk)

路由前缀：`/service-desk` | 源码位置：\[service_desk_router.py\](file:///home/netxs/devops/devops_portal/routers/service_desk_router.py)

| 请求方法 | 路由路径 | 功能描述 | 权限要求 |
| :--- | :--- | :--- | :--- |
| `GET` | `/business-projects` | 获取用户可见的业务系统列表 | 需登录 |
| `POST` | `/upload` | 基于 MDM 项目 ID 的附件上传路由 | 需登录 |
| `POST` | `/submit-bug` | 三层映射：通过产品 ID 受理中心提交 Bug | 需登录 |
| `POST` | `/submit-requirement` | 三层映射：通过产品 ID 受理中心提交需求 | 需登录 |
| `POST` | `/tickets/{iid}/reject` | RD 拒绝并关闭服务台工单 | 需登录 |
| `GET` | `/tickets` | 基于数据库查询 Service Desk 工单列表 (部门隔离) | 需登录 |
| `GET` | `/track/{ticket_id}` | 通过数据库 ID 查询工单详情与状态追踪 | 需登录 |
| `PATCH` | `/tickets/{ticket_id}/status` | 更新工单状态 (支持审计记录) | 需登录 |
| `GET` | `/my-tickets` | 获取当前登录用户创建的工单列表 | 需登录 |
| `GET` | `/admin/all-users` | 管理后台：获取所有用户申请记录及统计 | `USER:MANAGE` |
| `POST` | `/admin/approve-user` | 管理后台：审批用户申请并绑定身份标识 | `USER:MANAGE` |

______________________________________________________________________

## 🎯 Traceability 协同雷达 (Traceability Radar)

路由前缀：`/traceability` | 源码位置：\[traceability_router.py\](file:///home/netxs/devops/devops_portal/routers/traceability_router.py)

| 请求方法 | 路由路径 | 功能描述 | 参数与说明 |
| :--- | :--- | :--- | :--- |
| `GET` | `/detail` | 获取指定维度的详情下钻列表 | **Query**: `metric_type`, `days`, `limit`, `project_id` |
| `GET` | `/radar` | 获取 Traceability Radar 聚合指标数据 | **Query**: `project_id`, `days` (流动效率/协同质量/安全态势/ELOC/Timeline) |

______________________________________________________________________

## 🔌 插件集成模块 (Plugins)

路由前缀：`/plugins` | 源码位置：\[plugin_router.py\](file:///home/netxs/devops/devops_portal/routers/plugin_router.py)

| 请求方法 | 路由路径 | 功能描述 | 权限与组织隔离 |
| :--- | :--- | :--- | :--- |
| `GET` | `/jenkins/jobs` | 获取 Jenkins 任务列表 | 组织级隔离 |
| `GET` | `/jenkins/jobs/{job_id}/builds` | 获取特定任务的构建历史 | 含项目权限校验 |
| `GET` | `/artifacts/jfrog` | 获取 JFrog 制品列表 | 组织级隔离 |
| `GET` | `/artifacts/nexus` | 获取 Nexus 组件列表 | 组织级隔离 |

______________________________________________________________________

## 🛡️ 安全扫描模块 (Security)

路由前缀：`/security` | 源码位置：\[security_router.py\](file:///home/netxs/devops/devops_portal/routers/security_router.py)

| 请求方法 | 路由路径 | 功能描述 | 输入与解析格式 |
| :--- | :--- | :--- | :--- |
| `POST` | `/dependency-check/upload` | 上传 Dependency-Check 扫描报告 (CI 集成) | **Form & File**: 接收 CI 流水线 JSON 报告入库 |
| `GET` | `/dependency-scans` | 获取 Dependency Check 历史扫描结果 | 组织级隔离 |

______________________________________________________________________

## 🤖 开发者体验反馈 (DevEx Pulse)

路由前缀：`/devex-pulse` | 源码位置：\[devex_pulse_router.py\](file:///home/netxs/devops/devops_portal/routers/devex_pulse_router.py)

| 请求方法 | 路由路径 | 功能描述 | 输入与输出 |
| :--- | :--- | :--- | :--- |
| `POST` | `/submit` | 提交每日心情指数反馈 | **Body**: `PulseSubmission` |
| `GET` | `/status/{user_email}` | 检查用户今日是否已提交反馈 | 路径参数：`user_email` |

______________________________________________________________________

## ⚙️ 后台管理与同步 (Administration)

路由前缀：`/admin` | 源码位置：\[admin_router.py\](file:///home/netxs/devops/devops_portal/routers/admin_router.py)

由于此模块涉及企业架构/权限控制，大部分端点均需要 `ADMIN` 角色或特定权限凭证。

| 请求方法 | 路由路径 | 功能描述 |
| :--- | :--- | :--- |
| `GET` | `/organizations` | 获取所有组织机构列表 |
| `POST` | `/organizations` | 创建组织机构 |
| `POST` | `/import/users` | 批量导入用户数据 |
| `POST` | `/import/organizations` | 批量导入组织架构 |
| `GET` | `/export/users` | 导出用户列表 |
| `GET` | `/export/organizations` | 导出组织架构 |
| `GET` | `/users` | 获取用户列表 |
| `GET` | `/users/{user_id}` | 获取特定用户完整画像 |
| `GET` | `/identity-mappings` | 获取身份映射关系列表 |
| `POST` | `/identity-mappings` | 创建身份映射映射关系 |
| `DELETE` | `/identity-mappings/{mapping_id}` | 删除身份映射 |
| `PATCH` | `/identity-mappings/{mapping_id}/status` | 启用/禁用身份映射 |
| `GET` | `/audit-logs` | 获取系统审计日志列表 |
| `GET` | `/teams` | 获取团队列表 |
| `POST` | `/teams` | 创建团队 |
| `POST` | `/teams/{team_id}/members` | 绑定团队成员 |
| `GET` | `/mdm-projects` | 获取主数据项目列表 |
| `POST` | `/mdm-projects` | 新建主数据项目 |
| `GET` | `/unlinked-repos` | 获取未关联的 GitLab 仓库列表 |
| `POST` | `/link-repo` | 关联 GitLab 仓库到主数据项目 |
| `POST` | `/mdm-projects/{project_id}/set-lead` | 设置主数据项目的受理仓库 (Lead Repo) |
| `GET` | `/products` | 获取业务系统/产品列表 |
| `POST` | `/products` | 新建业务系统/产品 |
| `POST` | `/link-product` | 关联项目与业务系统/产品关系 |
| `GET` | `/export/products` | 导出业务系统列表 |
| `POST` | `/import/products` | 导入业务系统列表 |
| `GET` | `/export/product-mappings` | 导出项目产品映射关系 |
| `POST` | `/import/product-mappings` | 导入项目产品映射关系 |
| `GET` | `/okrs` | 获取 OKR 数据列表 |
| `GET` | `/export/okrs` | 导出 OKR 列表 |

______________________________________________________________________

## 📑 Webhook 接收模块 (Webhooks)

路由前缀：`/webhooks` | 源码位置：\[webhook_router.py\](file:///home/netxs/devops/devops_portal/routers/webhook_router.py)

| 请求方法 | 路由路径 | 功能描述 | 触发源与说明 |
| :--- | :--- | :--- | :--- |
| `POST` | `/gitlab` | 接收并分发 GitLab 系统事件钩子 | GitLab Webhook (含 `X-Gitlab-Token` 安全验证) |
| `POST` | `/sonarqube` | 接收并记录 SonarQube 分析完成事件 | SonarQube Webhook |
| `POST` | `/triggers/sonarqube` | 手动/流水线触发 SonarQube 数据增量同步 | 用于补偿同步 |
