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

export interface TestStep {
  step_number: number
  action: string
  expected_result: string
}

export interface TestCase {
  id: number
  iid: number
  title: string
  priority?: TestCasePriority
  test_type?: string
  requirement_id?: string
  pre_conditions: string[]
  steps: TestStep[]
  result: TestCaseStatus
  web_url?: string
  linked_bugs?: Record<string, string>[]
  project_name?: string
}

export interface TestCaseCreate {
  title: string
  priority: string
  test_type: string
  pre_conditions: string
  steps: Array<{ action: string; expected: string }>
  requirement_iid?: number | null
  product_id?: string | null
  org_id?: string | null
}

export interface ExecutionReport {
  result?: string | null
  executor?: string
  comment?: string | null
  environment?: string | null
}

export interface TestSummary {
  total: number
  passed: number
  failed: number
  blocked?: number
  pending: number
  pass_rate?: number
}

// =============================================================================
// 需求与缺陷管理
// =============================================================================

export type IssueType = 'bug' | 'requirement' | 'task'
export type IssueState = 'opened' | 'closed' | 'merged'

export interface RequirementSummary {
  iid: number
  title: string
  state: string
  review_state: string
}

export interface RequirementDetail {
  id: number
  iid: number
  title: string
  description?: string | null
  state: string
  review_state: string
  test_cases: TestCase[]
}

export interface BugCreate {
  title: string
  severity: string
  priority?: string
  category: string
  source: string
  province: string
  environment: string
  steps_to_repro: string
  actual_result: string
  expected_result: string
  linked_case_iid: number
  linked_req_iid?: number | null
}

export interface BugDetail {
  iid: number
  title: string
  state: string
  created_at: string
  author: string
  web_url: string
  labels: string[]
}

export interface TraceabilityMRItem {
  iid: number
  title: string
  state: string
  web_url: string
  created_at: string
}

export interface TraceabilityCommitItem {
  id: string
  short_id: string
  title: string
  created_at: string
  web_url: string
}

export interface TraceabilityMatrixItem {
  requirement: RequirementSummary
  test_cases: TestCase[]
  defects: BugDetail[]
  merge_requests: TraceabilityMRItem[]
  commits: TraceabilityCommitItem[]
}

// =============================================================================
// 服务台工单
// =============================================================================

export type TicketStatus = 'opened' | 'pending' | 'processing' | 'resolved' | 'rejected' | 'closed'
export type TicketType = 'bug' | 'requirement'

export interface Ticket {
  id: number
  title: string
  description?: string
  issue_type: TicketType
  status: TicketStatus
  origin_dept_id?: number
  origin_dept_name?: string
  target_dept_id?: number
  target_dept_name?: string
  requester_email?: string
  gitlab_project_id?: number
  gitlab_issue_iid?: number
  bug_category?: string
  req_type?: string
  created_at: string
  updated_at?: string
}

export interface ServiceDeskBugSubmit {
  title: string
  severity: string
  priority?: string
  province?: string
  environment: string
  steps_to_repro: string
  actual_result: string
  expected_result: string
  bug_category?: string
  attachments?: string[]
}

export interface ServiceDeskRequirementSubmit {
  title: string
  description: string
  priority?: string
  req_type?: string
  province?: string
  expected_delivery?: string
  attachments?: string[]
}

// =============================================================================
// Traceability 雷达
// =============================================================================

export interface RadarMeta {
  project_id?: number | null
  days: number
  total_merged_mrs: number
}

export interface RadarVSM {
  avg_wait_minutes: number
  avg_draft_minutes: number
  flow_efficiency?: number | null
}

export interface RadarCollaboration {
  rubber_stamp_rate: number
  effective_review_rate: number
  avg_effective_comments: number
}

export interface RadarSecurity {
  critical: number
  high: number
  medium: number
  low: number
  total_active: number
}

export interface VSMTimelineItem {
  id: string
  title: string
  draft_minutes?: number | null
  wait_minutes?: number | null
  review_minutes?: number | null
  total_minutes?: number | null
  rubber_stamp: boolean
  effective_comments: number
}

export interface RadarELOC {
  labels: string[]
  values: number[]
}

export interface RadarResponse {
  meta: RadarMeta
  vsm: RadarVSM
  collaboration: RadarCollaboration
  security: RadarSecurity
  eloc: RadarELOC
  vsm_timeline: VSMTimelineItem[]
}

export interface RadarDetailItem {
  id: string | number
  title: string
  author?: string | null
  value?: string | number | null
  url?: string | null
  timestamp?: string | null
}

export interface RadarDetailResponse {
  type: string
  items: RadarDetailItem[]
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

export interface SprintBoard {
  milestone: string
  project_id: number
  columns: Record<BoardColumn, BoardItem[]>
}

/**
 * 团队心情打点条目（前端 localStorage 本地存储，非后端 API Schema）
 * key 格式：pulse_<date>_<userId>
 */
export interface PulseEntry {
  userId: string
  emoji: string   // 对应 EmojiOption.key
  date: string    // 'YYYY-MM-DD'
  ts: number      // Unix timestamp ms
}


// =============================================================================
// 主数据项目和产品 (MDM)
// =============================================================================

export interface MDMProjectProduct {
  product_id: string
  product_name: string
  relation_type?: string
}

export interface MDMProject {
  project_id: string
  project_name: string
  lead_repo_id: number | null
  products: MDMProjectProduct[]
}

// =============================================================================
// 服务台 (ServiceDesk)
// =============================================================================

export interface CustomerIdentityCreate {
  tenant_id?: string
  email: string
  company_name?: string
  contact_name?: string
  phone?: string
}

export interface CustomerIdentityResponse {
  id: string
  tenant_id: string
  email: string
  company_name?: string
  contact_name?: string
  phone?: string
  is_active: boolean
  created_at: string
}

export interface TicketCreateExternal {
  title: string
  description?: string
  ticket_type: string
}

export interface TicketTriageUpdate {
  ticket_type?: string
  product_id?: string
}

export interface TicketResponse {
  id: string
  tenant_id: string
  reporter_id: string
  title: string
  description?: string
  ticket_type: string
  status: string
  product_id?: string
  department_id?: string
  assignee_id?: string
  agile_issue_id?: string
  gitlab_group_id?: number
  gitlab_project_id?: number
  created_at: string
  updated_at: string
}
