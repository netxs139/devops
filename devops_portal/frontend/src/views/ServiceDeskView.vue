<script setup lang="ts">
/**
 * @file ServiceDeskView.vue
 * @description 服务台主页面，展示工单列表与度量，支持驳回与状态流转
 */
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NTabs,
  NTabPane,
  NTable,
  NTag,
  NSpace,
  NButton,
  NModal,
  NInput,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'
import type { Ticket, TicketStatus } from '@/types/api'
import TicketForm from '@/components/TicketForm.vue'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 视图切换: 'list' 列表视图, 'create' 创建表单视图
const currentView = ref<'list' | 'create'>('list')

// Tab 切换: 'my' 我的工单, 'all' 全量反馈
const activeTab = ref<'my' | 'all'>('my')

const tickets = ref<Ticket[]>([])
const loading = ref(false)

// 驳回 Modal 控制
const showRejectModal = ref(false)
const rejectReason = ref('')
const selectedTicket = ref<Ticket | null>(null)
const rejecting = ref(false)

// 状态流转加载状态
const transitionLoading = ref<Record<number, boolean>>({})

// 统计度量（基于本地缓存或后端列表计算）
const statsTotal = ref(0)
const statsPending = ref(0)
const statsResolved = ref(0)

// 根据当前列表实时更新统计
function updateStats(list: Ticket[]) {
  statsTotal.value = list.length
  statsPending.value = list.filter(t =>
    t.status === 'pending' || t.status === 'opened' || t.status === 'processing'
  ).length
  statsResolved.value = list.filter(t =>
    t.status === 'resolved' || t.status === 'closed'
  ).length
}

// 加载数据
async function loadTickets() {
  loading.value = true
  try {
    let data: Ticket[] = []
    if (activeTab.value === 'my') {
      data = await http.get<Ticket[]>('/service-desk/my-tickets')
    } else {
      data = await http.get<Ticket[]>('/service-desk/tickets')
    }
    // 强制转换为 TicketType 避免后端返回的字符串类型不匹配
    tickets.value = data
    updateStats(data)
  } catch (err: unknown) {
    message.error('加载工单列表失败: ' + (err as Error).message)
    tickets.value = []
  } finally {
    loading.value = false
  }
}

// 监听 Tab 切换重新拉取
watch(activeTab, () => {
  loadTickets()
})

// 驳回工单
function openRejectModal(ticket: Ticket) {
  selectedTicket.value = ticket
  rejectReason.value = ''
  showRejectModal.value = true
}

async function handleRejectSubmit() {
  if (!selectedTicket.value) return
  if (!rejectReason.value.trim()) {
    message.warning('请输入驳回原因')
    return
  }

  rejecting.value = true
  try {
    // 1. 获取工单完整详情以解析 gitlab_project_id 与 gitlab_issue_iid
    const detail = await http.get<Ticket>(`/service-desk/track/${selectedTicket.value.id}`)
    const projId = detail.gitlab_project_id
    const issueIid = detail.gitlab_issue_iid

    if (!projId || !issueIid) {
      throw new Error('当前工单缺失 GitLab 项目/Issue 映射，无法通过 API 驳回')
    }

    // 2. 调用驳回接口
    await http.post(`/service-desk/tickets/${issueIid}/reject`, {
      project_id: projId,
      reason: rejectReason.value.trim()
    })

    message.success('工单驳回成功')
    showRejectModal.value = false
    loadTickets()
  } catch (err: unknown) {
    message.error('驳回失败: ' + ((err as Error).message || '未知错误'))
  } finally {
    rejecting.value = false
  }
}

// 状态流转操作
async function handleStatusTransition(ticketId: number, nextStatus: TicketStatus) {
  transitionLoading.value[ticketId] = true
  try {
    await http.patch(`/service-desk/tickets/${ticketId}/status?new_status=${nextStatus}`)
    message.success(`工单状态已成功更新为：${nextStatus}`)
    loadTickets()
  } catch (err: unknown) {
    message.error('状态更新失败: ' + ((err as Error).message || '未知错误'))
  } finally {
    transitionLoading.value[ticketId] = false
  }
}

// 处理新建完成
function handleSaved() {
  currentView.value = 'list'
  // 新建后默认切换到“我的工单”并刷新
  activeTab.value = 'my'
  loadTickets()
  // 清理 URL Query 参数，防止刷新时再次弹窗
  router.replace({ path: '/service-desk' })
}

// 取消返回
function handleCancel() {
  currentView.value = 'list'
  router.replace({ path: '/service-desk' })
}

onMounted(() => {
  // 检测 Query 参数，若包含 type 则自动打开表单
  if (route.query.type) {
    currentView.value = 'create'
  } else {
    loadTickets()
  }
})
</script>

<template>
  <div class="service-desk-page">
    <!-- 切录入表单视图 -->
    <div v-if="currentView === 'create'">
      <TicketForm @saved="handleSaved" @cancel="handleCancel" />
    </div>

    <!-- 列表视图 -->
    <div v-else class="list-layout">
      <!-- 顶部标题与新建工单按钮 -->
      <div class="page-header">
        <div class="header-title-group">
          <h1 class="page-title">服务台 (Service Desk)</h1>
          <p class="page-subtitle">提报系统缺陷与需求，闭环跟踪 GitLab Issue 研发生命周期。</p>
        </div>
        <NButton type="primary" size="large" @click="currentView = 'create'">
          <template #icon>➕</template>
          新建工单
        </NButton>
      </div>

      <!-- 统计指标卡片 -->
      <NGrid :cols="3" :x-gap="24" class="stats-grid">
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="累计反馈工单" :value="statsTotal">
              <template #suffix><span class="unit">个</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="待处理/处理中" :value="statsPending">
              <template #suffix><span class="unit warning">个</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="已解决/已关闭" :value="statsResolved">
              <template #suffix><span class="unit success">个</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 双 Tab 切换列表 -->
      <NCard class="table-card" :bordered="false" :loading="loading">
        <NTabs v-model:value="activeTab" type="line" animated class="custom-tabs">
          <!-- 我的工单 Tab -->
          <NTabPane name="my" tab="我的工单 (My Submissions)" />
          <!-- 全量反馈 Tab -->
          <NTabPane name="all" tab="全量反馈 (All Feedback)" />
        </NTabs>

        <div class="table-wrapper">
          <NTable :single-line="false" size="medium" class="apple-style-table">
            <thead>
              <tr>
                <th style="width: 80px;">工单 ID</th>
                <th style="width: 100px;">类型</th>
                <th>工单主题 (Title)</th>
                <th v-if="activeTab === 'all'" style="width: 140px;">发起部门</th>
                <th v-if="activeTab === 'all'" style="width: 140px;">研发受理部门</th>
                <th style="width: 120px;">状态</th>
                <th style="width: 160px;">创建时间</th>
                <th style="width: 240px; text-align: center;">操作选项</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ticket in tickets" :key="ticket.id">
                <td class="monospace-id">#{{ ticket.id }}</td>
                <td>
                  <NTag
                    :bordered="false"
                    size="small"
                    :type="ticket.issue_type === 'bug' ? 'error' : 'info'"
                  >
                    {{ ticket.issue_type === 'bug' ? '🐞 缺陷' : '💡 需求' }}
                  </NTag>
                </td>
                <td class="ticket-title-col" :title="ticket.title">{{ ticket.title }}</td>
                <td v-if="activeTab === 'all'">{{ ticket.origin_dept_name || '-' }}</td>
                <td v-if="activeTab === 'all'">{{ ticket.target_dept_name || '-' }}</td>
                <td>
                  <span
                    class="status-dot-badge"
                    :class="'status-' + (ticket.status || 'pending')"
                  >
                    {{
                      ticket.status === 'opened' || ticket.status === 'pending'
                        ? '待处理'
                        : ticket.status === 'processing'
                        ? '处理中'
                        : ticket.status === 'resolved'
                        ? '已解决'
                        : ticket.status === 'rejected'
                        ? '已拒绝'
                        : '已关闭'
                    }}
                  </span>
                </td>
                <td class="time-col">{{ ticket.created_at ? ticket.created_at.replace('T', ' ').slice(0, 19) : '-' }}</td>
                <td style="text-align: center;">
                  <NSpace justify="center" :size="8">
                    <!-- 状态流转按钮 (仅在未解决/未关闭/未拒绝时可用) -->
                    <template v-if="ticket.status !== 'resolved' && ticket.status !== 'closed' && ticket.status !== 'rejected'">
                      <NButton
                        v-if="ticket.status === 'opened' || ticket.status === 'pending'"
                        size="tiny"
                        type="info"
                        secondary
                        :loading="transitionLoading[ticket.id]"
                        @click="handleStatusTransition(ticket.id, 'processing')"
                      >
                        处理
                      </NButton>
                      <NButton
                        v-if="ticket.status === 'processing'"
                        size="tiny"
                        type="success"
                        secondary
                        :loading="transitionLoading[ticket.id]"
                        @click="handleStatusTransition(ticket.id, 'resolved')"
                      >
                        解决
                      </NButton>
                      <NButton
                        size="tiny"
                        type="error"
                        ghost
                        @click="openRejectModal(ticket)"
                      >
                        驳回
                      </NButton>
                    </template>
                    <NButton
                      v-if="ticket.status === 'resolved'"
                      size="tiny"
                      type="default"
                      secondary
                      :loading="transitionLoading[ticket.id]"
                      @click="handleStatusTransition(ticket.id, 'closed')"
                    >
                      关闭
                    </NButton>
                    <span v-if="ticket.status === 'closed' || ticket.status === 'rejected'" class="dim-action-text">
                      已完成流转
                    </span>
                  </NSpace>
                </td>
              </tr>
              <tr v-if="tickets.length === 0">
                <td :colspan="activeTab === 'all' ? 8 : 6" class="empty-table-cell">
                  <div class="empty-box">
                    <span>🔍 暂无工单反馈记录</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </NTable>
        </div>
      </NCard>
    </div>

    <!-- 驳回模态框 -->
    <NModal
      v-model:show="showRejectModal"
      preset="card"
      title="工单驳回确认"
      style="width: 450px;"
      class="apple-modal"
    >
      <div class="modal-body">
        <p class="modal-warning">您正在执行工单驳回，该操作将关闭对应的 GitLab Issue。请填写具体的驳回说明：</p>
        <NInput
          v-model:value="rejectReason"
          type="textarea"
          placeholder="请输入驳回原因（如：无法复现、不合理需求、属于外部系统等）..."
          :autosize="{ minRows: 3, maxRows: 6 }"
          class="margin-top"
        />
      </div>
      <template #footer>
        <NSpace justify="end" :size="12">
          <NButton :disabled="rejecting" @click="showRejectModal = false">取消</NButton>
          <NButton
            type="error"
            :loading="rejecting"
            :disabled="!rejectReason.trim()"
            @click="handleRejectSubmit"
          >
            确认驳回
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.service-desk-page {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.stats-grid {
  margin-bottom: var(--space-6);
}

.stat-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.01);
}

.unit {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-left: 4px;
}
.unit.warning { color: var(--color-warning); }
.unit.success { color: var(--color-success); }

.table-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  padding: var(--space-4);
}

.custom-tabs {
  margin-bottom: var(--space-4);
}

.table-wrapper {
  overflow-x: auto;
}

.apple-style-table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
}

.apple-style-table th {
  background: var(--color-bg-base);
  color: var(--color-text-secondary);
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid var(--color-border);
}

.apple-style-table td {
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  color: var(--color-text-primary);
}

.monospace-id {
  font-family: monospace;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.ticket-title-col {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;
}

.time-col {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.status-dot-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  font-size: 12px;
}

.status-dot-badge::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-opened::before,
.status-pending::before {
  background: var(--color-warning);
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
}

.status-processing::before {
  background: var(--color-info);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
}

.status-resolved::before,
.status-closed::before {
  background: var(--color-success);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.status-rejected::before {
  background: var(--color-error);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.dim-action-text {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.empty-table-cell {
  padding: 60px 0;
  text-align: center;
}

.empty-box {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.modal-warning {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.margin-top {
  margin-top: var(--space-4);
}
</style>
