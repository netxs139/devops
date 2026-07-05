<script setup lang="ts">
/**
 * @file AuditLogAdmin.vue
 * @description 系统安全审计日志与 OKR 预览组件，支持高级过滤与详情展示
 */
import { ref, onMounted } from 'vue'
import {
  NCard,
  NTabs,
  NTabPane,
  NTable,
  NSpace,
  NButton,
  NTag,
  NForm,
  NFormItem,
  NInput,
  NDatePicker,
  NProgress,
  NModal,
  NList,
  NListItem,
  NDescriptions,
  NDescriptionsItem,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'

interface AuditLog {
  id: number
  timestamp: string
  actor_name: string | null
  client_ip: string | null
  action: string
  resource_type: string
  resource_id: string
  changes: Record<string, unknown> | null
  correlation_id: string | null
  status: string
  remark: string | null
}

interface OKRObjective {
  id: number
  title: string
  owner_name: string
  period: string
  status: string
  progress: number
  key_results: Array<{ title: string; progress: number }>
}

const message = useMessage()
const loadingLogs = ref(false)
const loadingOkrs = ref(false)
const logs = ref<AuditLog[]>([])
const okrs = ref<OKRObjective[]>([])

// 审计查询条件
const logQuery = ref({
  action: '',
  resource_type: '',
  start_time: null as number | null,
  end_time: null as number | null,
  page: 1,
  page_size: 50
})

// OKR 查询条件
const okrQuery = ref({
  period: '',
  status: ''
})

// 日志详情
const showDetailModal = ref(false)
const selectedLog = ref<AuditLog | null>(null)

// 加载审计日志
async function loadAuditLogs() {
  loadingLogs.value = true
  try {
    const params: Record<string, string | number> = {
      page: logQuery.value.page,
      page_size: logQuery.value.page_size
    }
    if (logQuery.value.action) params.action = logQuery.value.action
    if (logQuery.value.resource_type) params.resource_type = logQuery.value.resource_type
    if (logQuery.value.start_time) {
      params.start_time = new Date(logQuery.value.start_time).toISOString()
    }
    if (logQuery.value.end_time) {
      params.end_time = new Date(logQuery.value.end_time).toISOString()
    }

    const data = await http.get<AuditLog[]>('/admin/audit-logs', params)
    logs.value = data
  } catch (err: unknown) {
    message.error('加载审计日志失败: ' + (err as Error).message)
  } finally {
    loadingLogs.value = false
  }
}

// 加载 OKR
async function loadOkrs() {
  loadingOkrs.value = true
  try {
    const params: Record<string, string> = {}
    if (okrQuery.value.period) params.period = okrQuery.value.period
    if (okrQuery.value.status) params.status = okrQuery.value.status

    const data = await http.get<OKRObjective[]>('/admin/okrs', params)
    okrs.value = data
  } catch (err: unknown) {
    message.error('加载 OKR 列表失败: ' + (err as Error).message)
  } finally {
    loadingOkrs.value = false
  }
}

// 导出 OKR CSV
async function handleExportOkrs() {
  try {
    let endpoint = '/admin/export/okrs'
    const q: string[] = []
    if (okrQuery.value.period) q.push(`period=${okrQuery.value.period}`)
    if (okrQuery.value.status) q.push(`status=${okrQuery.value.status}`)
    if (q.length > 0) endpoint += `?${q.join('&')}`

    const response = await http.get(endpoint, { responseType: 'blob' })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const blob = new Blob([response as any], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'okr_export.csv'
    link.click()
    URL.revokeObjectURL(link.href)
    message.success('OKR 导出成功')
  } catch (err: unknown) {
    message.error('导出失败: ' + (err as Error).message)
  }
}

// 重置查询
function resetLogQuery() {
  logQuery.value.action = ''
  logQuery.value.resource_type = ''
  logQuery.value.start_time = null
  logQuery.value.end_time = null
  logQuery.value.page = 1
  loadAuditLogs()
}

// 显示日志详情
function showLogDetails(log: AuditLog) {
  selectedLog.value = log
  showDetailModal.value = true
}

onMounted(() => {
  loadAuditLogs()
  loadOkrs()
})
</script>

<template>
  <div class="audit-log-admin">
    <NCard :bordered="false" size="small">
      <NTabs type="line" animated>
        <!-- 审计日志 -->
        <NTabPane name="audit" tab="🔒 安全审计日志 (Audit Logs)">
          <!-- 高级查询面板 -->
          <div class="filter-panel">
            <NForm inline :model="logQuery" label-placement="left" size="small" class="filter-form">
              <NFormItem label="行为 (Action)">
                <NInput v-model:value="logQuery.action" placeholder="如 USER_LOGIN" style="width: 140px;" />
              </NFormItem>
              <NFormItem label="资源类型">
                <NInput v-model:value="logQuery.resource_type" placeholder="如 Organization" style="width: 140px;" />
              </NFormItem>
              <NFormItem label="起止时间">
                <NDatePicker v-model:value="logQuery.start_time" type="datetime" placeholder="开始时间" style="width: 170px;" />
                <span class="date-sep">-</span>
                <NDatePicker v-model:value="logQuery.end_time" type="datetime" placeholder="结束时间" style="width: 170px;" />
              </NFormItem>
              <NFormItem>
                <NSpace>
                  <NButton type="primary" @click="loadAuditLogs">查询</NButton>
                  <NButton @click="resetLogQuery">重置</NButton>
                </NSpace>
              </NFormItem>
            </NForm>
          </div>

          <NTable :single-line="false" size="small" class="admin-table">
            <thead>
              <tr>
                <th style="width: 160px;">发生时间</th>
                <th>操作人</th>
                <th>行为 (Action)</th>
                <th>资源类型</th>
                <th>客户端 IP</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id">
                <td class="time-col">{{ log.timestamp ? log.timestamp.replace('T', ' ').slice(0, 19) : '-' }}</td>
                <td class="weight-medium">{{ log.actor_name || 'System' }}</td>
                <td>
                  <NTag size="small" :bordered="false" type="info">{{ log.action }}</NTag>
                </td>
                <td>{{ log.resource_type }}</td>
                <td class="monospace-small">{{ log.client_ip || '-' }}</td>
                <td>
                  <NTag size="small" :bordered="false" :type="log.status === 'success' ? 'success' : 'error'">
                    {{ log.status }}
                  </NTag>
                </td>
                <td>
                  <NButton size="tiny" secondary type="primary" @click="showLogDetails(log)">
                    详情
                  </NButton>
                </td>
              </tr>
              <tr v-if="logs.length === 0 && !loadingLogs">
                <td colspan="7" class="empty-cell">🔍 暂无匹配的审计日志记录</td>
              </tr>
            </tbody>
          </NTable>
        </NTabPane>

        <!-- OKR 预览 -->
        <NTabPane name="okrs" tab="🎯 OKR 业务指标 (OKRs)">
          <div class="tab-header">
            <NSpace inline align="center">
              <NInput v-model:value="okrQuery.period" placeholder="周期 (如 2026-Q1)" size="small" style="width: 140px;" @keyup.enter="loadOkrs" />
              <NInput v-model:value="okrQuery.status" placeholder="状态" size="small" style="width: 100px;" @keyup.enter="loadOkrs" />
              <NButton type="primary" size="small" @click="loadOkrs">检索</NButton>
              <NButton size="small" secondary type="info" @click="handleExportOkrs">
                导出 OKR CSV
              </NButton>
            </NSpace>
          </div>

          <div v-if="loadingOkrs" class="empty-cell">加载 OKRs 中...</div>
          <div v-else class="okr-list">
            <NCard v-for="obj in okrs" :key="obj.id" :title="obj.title" size="small" class="okr-card">
              <template #header-extra>
                <NSpace>
                  <NTag size="small" :bordered="false" type="info">{{ obj.period }}</NTag>
                  <NTag size="small" :bordered="false" type="success">{{ obj.status }}</NTag>
                  <span class="owner-text">负责人: {{ obj.owner_name }}</span>
                </NSpace>
              </template>
              <div class="okr-progress-section">
                <div class="progress-title">目标完成度</div>
                <NProgress type="line" :percentage="Math.round(obj.progress * 100)" status="success" :height="8" />
              </div>
              <div v-if="obj.key_results && obj.key_results.length > 0" class="kr-section">
                <div class="kr-header">关键结果 (Key Results)：</div>
                <NList size="small" hoverable>
                  <NListItem v-for="kr in obj.key_results" :key="kr.title">
                    <NSpace justify="space-between" align="center" style="width: 100%;">
                      <span class="kr-title">{{ kr.title }}</span>
                      <NProgress type="line" :percentage="Math.round(kr.progress * 100)" style="width: 150px;" :height="6" />
                    </NSpace>
                  </NListItem>
                </NList>
              </div>
            </NCard>
            <div v-if="okrs.length === 0" class="empty-cell">🔍 暂无符合条件的 OKR 目标</div>
          </div>
        </NTabPane>
      </NTabs>
    </NCard>

    <!-- 日志详情 Modal -->
    <NModal v-model:show="showDetailModal" preset="card" title="🔒 审计日志详情" style="width: 600px;">
      <div v-if="selectedLog">
        <NDescriptions label-placement="left" :column="1" bordered size="small">
          <NDescriptionsItem label="发生时间">{{ selectedLog.timestamp.replace('T', ' ').slice(0, 19) }}</NDescriptionsItem>
          <NDescriptionsItem label="操作用户">{{ selectedLog.actor_name || 'System' }}</NDescriptionsItem>
          <NDescriptionsItem label="动作行为">{{ selectedLog.action }}</NDescriptionsItem>
          <NDescriptionsItem label="资源类型">{{ selectedLog.resource_type }}</NDescriptionsItem>
          <NDescriptionsItem label="资源 ID">{{ selectedLog.resource_id }}</NDescriptionsItem>
          <NDescriptionsItem label="客户端 IP">{{ selectedLog.client_ip || '-' }}</NDescriptionsItem>
          <NDescriptionsItem label="链路追踪 ID (Correlation-ID)">
            <span class="monospace-small">{{ selectedLog.correlation_id || '-' }}</span>
          </NDescriptionsItem>
          <NDescriptionsItem label="执行状态">
            <NTag size="small" :bordered="false" :type="selectedLog.status === 'success' ? 'success' : 'error'">
              {{ selectedLog.status }}
            </NTag>
          </NDescriptionsItem>
          <NDescriptionsItem v-if="selectedLog.changes" label="详细变更">
            <pre class="changes-pre">{{ JSON.stringify(selectedLog.changes, null, 2) }}</pre>
          </NDescriptionsItem>
          <NDescriptionsItem v-if="selectedLog.remark" label="备注说明">
            {{ selectedLog.remark }}
          </NDescriptionsItem>
        </NDescriptions>
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.audit-log-admin {
  width: 100%;
}
.filter-panel {
  background: var(--color-bg-base);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  border: 1px solid var(--color-border);
}
.filter-form {
  flex-wrap: wrap;
}
.date-sep {
  margin: 0 var(--space-2);
  color: var(--color-text-secondary);
}
.tab-header {
  margin-bottom: var(--space-4);
  display: flex;
  justify-content: flex-end;
}
.admin-table {
  width: 100%;
  margin-top: var(--space-2);
}
.monospace-small {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--color-text-secondary);
}
.weight-medium {
  font-weight: 500;
}
.time-col {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.empty-cell {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--color-text-tertiary);
}
.okr-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-top: var(--space-2);
}
.okr-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.01);
}
.owner-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.okr-progress-section {
  margin-bottom: var(--space-4);
}
.progress-title {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-1);
}
.kr-section {
  border-top: 1px dashed var(--color-border);
  padding-top: var(--space-3);
}
.kr-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}
.kr-title {
  font-size: 13px;
  color: var(--color-text-primary);
}
.changes-pre {
  margin: 0;
  padding: var(--space-2);
  background: var(--color-bg-base);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono, monospace);
  font-size: 11px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
