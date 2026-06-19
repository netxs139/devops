/**
 * @file api.d.ts
 * @description 后端 Pydantic Schema 的前端强类型镜像。
 * 字段命名与 Python Schema 字段名完全对齐（snake_case），
 * 禁止在此文件外使用字面量硬编码 API 响应结构。
 *
 * SSOT: devops_portal/schemas.py & schemas_*.py
 */

// =============================================================================
// 通用基础类型
// =============================================================================

/** 统一 API 响应包装 */
export interface ApiResponse<T> {
  data: T
  message?: string
  code: number
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 业务异常（对应后端 BusinessException） */
export interface BusinessException {
  code: string         // 错误码，如 "PERMISSION_DENIED"
  message: string      // 用户友好的错误描述
  detail?: unknown     // 可选的调试信息
  correlation_id: string
}

// =============================================================================
// 认证与权限
// =============================================================================

/** POST /auth/login 返回的 OAuth2 Bearer Token 响应体 */
export interface AuthToken {
  access_token: string
  token_type: string   // 固定为 "bearer"
}

/** JWT Payload 解析结果 */
export interface JwtPayload {
  sub: string             // 用户 email
  username: string
  roles: string[]         // 如 ["admin", "tester"]
  permissions: string[]   // 如 ["rpt:quality:view", "USER:MANAGE"]
  department?: string     // 部门隔离作用域
  location?: string       // 省份数据隔离作用域
  exp: number
  iat: number
}

export interface UserProfile {
  id: number
  username: string
  email: string
  department?: string
  location?: string
  roles: string[]
  permissions: string[]
}

// =============================================================================
// 质量管理 - 测试用例
// =============================================================================

export type TestCaseStatus = 'passed' | 'failed' | 'pending' | 'blocked' | 'skipped'
export type TestCasePriority = 'P0' | 'P1' | 'P2' | 'P3'

export interface TestCase {
  iid: number
  title: string
  description?: string
  status: TestCaseStatus
  priority: TestCasePriority
  assignee?: string
  created_at: string
  updated_at: string
  project_id: number
  labels: string[]
}

export interface TestCaseExecutionPayload {
  iid: number
  result: TestCaseStatus
  report: string
}

export interface TestSummary {
  total: number
  passed: number
  failed: number
  pending: number
  pass_rate: number
}

// =============================================================================
// 需求与缺陷管理
// =============================================================================

export type IssueType = 'bug' | 'requirement' | 'task'
export type IssueState = 'opened' | 'closed' | 'merged'

export interface BugDetail {
  iid: number
  title: string
  description: string
  state: IssueState
  severity: 'critical' | 'major' | 'minor' | 'trivial'
  assignee?: string
  project_id: number
  created_at: string
  updated_at: string
  labels: string[]
}

export interface Requirement {
  iid: number
  title: string
  description: string
  state: IssueState
  milestone?: string
  assignee?: string
  project_id: number
  created_at: string
}

// =============================================================================
// 服务台工单
// =============================================================================

export type TicketStatus = 'pending' | 'processing' | 'resolved' | 'rejected' | 'closed'
export type TicketType = 'bug' | 'requirement'

export interface Ticket {
  id: number
  title: string
  description: string
  ticket_type: TicketType
  status: TicketStatus
  submitter_email: string
  product_id: number
  created_at: string
  updated_at: string
  gitlab_issue_iid?: number
}

export interface TicketSubmitPayload {
  product_id: number
  title: string
  description: string
  ticket_type: TicketType
  attachment_urls?: string[]
}

// =============================================================================
// Traceability 雷达
// =============================================================================

export interface RadarMetric {
  name: string
  value: number
  max: number
  unit?: string
}

export interface RadarResponse {
  project_id: number
  days: number
  flow_efficiency: RadarMetric      // 流动效率
  review_quality: RadarMetric       // 协同评审率
  security_posture: RadarMetric     // 安全态势
  eloc: RadarMetric                 // 代码 ELOC
  timeline: RadarDetailItem[]       // 价值流 Timeline
}

export interface RadarDetailItem {
  metric_type: string
  title: string
  value: string | number
  timestamp: string
  actor?: string
  project_name?: string
}

// =============================================================================
// 审计日志（等保三级）
// =============================================================================

export interface AuditLog {
  id: number
  correlation_id: string
  user_email: string
  action: string
  resource_type: string
  resource_id?: string
  ip_address: string
  user_agent: string
  timestamp: string
  success: boolean
  detail?: Record<string, unknown>
}

// =============================================================================
// 实时通知
// =============================================================================

export type NotificationType = 'info' | 'success' | 'warning' | 'error'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  content: string
  timestamp: string
  read: boolean
  link?: string
}

// =============================================================================
// 迭代看板
// =============================================================================

export type BoardColumn = 'todo' | 'in_progress' | 'review' | 'done'

export interface BoardItem {
  iid: number
  title: string
  type: IssueType
  state: IssueState
  assignee?: string
  priority?: TestCasePriority
  column: BoardColumn
  story_points?: number
}

export interface IterationBoard {
  milestone: string
  project_id: number
  columns: Record<BoardColumn, BoardItem[]>
}
