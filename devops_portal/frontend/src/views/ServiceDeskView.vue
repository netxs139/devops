<script setup lang="ts">
/**
 * @file ServiceDeskView.vue
 * @description 服务台主页面，采用 Vue 3 + Vue Query + Naive UI (绿地重构版)
 */
import { ref, computed, h } from 'vue'
import {
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NTabs,
  NTabPane,
  NDataTable,
  NTag,
  NButton,
  NSpace,
  NDrawer,
  NDrawerContent,
  NForm,
  NFormItem,
  NSelect,
  useMessage,
  type DataTableColumns
} from 'naive-ui'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import dayjs from 'dayjs'
import { http } from '@/utils/request'
import type { TicketResponse, TicketTriageUpdate } from '@/types/api'
import TicketForm from '@/components/TicketForm.vue'

const message = useMessage()
const queryClient = useQueryClient()

// 视图切换
const activeTab = ref<'customer' | 'agent'>('customer')

// 获取 Customer Tickets
const { data: customerTickets, isLoading: customerLoading } = useQuery({
  queryKey: ['customerTickets'],
  queryFn: () => http.get<TicketResponse[]>('/api/customer/tickets')
})

// 获取 Agent Tickets
const { data: agentTickets, isLoading: agentLoading } = useQuery({
  queryKey: ['agentTickets'],
  queryFn: () => http.get<TicketResponse[]>('/api/agent/tickets')
})

// 统计度量 (以 Agent 视角为例)
const statsTotal = computed(() => agentTickets.value?.length || 0)
const statsPending = computed(() => agentTickets.value?.filter(t => t.status !== 'RESOLVED' && t.status !== 'CLOSED').length || 0)
const statsResolved = computed(() => agentTickets.value?.filter(t => t.status === 'RESOLVED' || t.status === 'CLOSED').length || 0)

// 表格列定义
const createColumns = (isAgent: boolean): DataTableColumns<TicketResponse> => [
  { title: '工单 ID', key: 'id', width: 280, ellipsis: true },
  { title: '标题', key: 'title', ellipsis: true },
  {
    title: '类型',
    key: 'ticket_type',
    width: 150,
    render(row) {
      const typeMap: Record<string, 'default' | 'error' | 'info' | 'warning'> = {
        INCIDENT: 'error',
        BUG: 'error',
        REQUIREMENT: 'info',
        CONSULTATION: 'default'
      }
      return h(
        NTag,
        { type: typeMap[row.ticket_type] || 'default' },
        { default: () => row.ticket_type }
      )
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    render(row) {
      const statusMap: Record<string, 'default' | 'success' | 'warning' | 'info'> = {
        NEW: 'default',
        ACCEPTED: 'info',
        IN_PROGRESS: 'warning',
        RESOLVED: 'success',
        CLOSED: 'default'
      }
      return h(
        NTag,
        { type: statusMap[row.status] || 'default' },
        { default: () => row.status }
      )
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render(row) {
      return dayjs(row.created_at).format('YYYY-MM-DD HH:mm:ss')
    }
  },
  ...(isAgent ? [{
    title: '操作',
    key: 'actions',
    width: 100,
      render(row: TicketResponse) {
      return h(
        NButton,
        { size: 'small', onClick: () => openTriageDrawer(row) },
        { default: () => '分诊' }
      )
    }
  }] : [])
]

const customerColumns = createColumns(false)
const agentColumns = createColumns(true)

// 创建工单处理
function onTicketCreated() {
  queryClient.invalidateQueries({ queryKey: ['customerTickets'] })
  queryClient.invalidateQueries({ queryKey: ['agentTickets'] })
  activeTab.value = 'customer'
}

// 分诊抽屉控制
const showTriageDrawer = ref(false)
const triageTicket = ref<TicketResponse | null>(null)
const triageModel = ref<TicketTriageUpdate>({ ticket_type: '', product_id: '' })

function openTriageDrawer(ticket: TicketResponse) {
  triageTicket.value = ticket
  triageModel.value = { ticket_type: ticket.ticket_type, product_id: ticket.product_id || '' }
  showTriageDrawer.value = true
}

const productOptions = [
  { label: 'CloudNative 产品线 (agile-project-A)', value: 'product_a' },
  { label: 'Data 平台产品线 (agile-project-B)', value: 'product_b' }
]

const { mutate: triageMutate, isPending: triagePending } = useMutation({
  mutationFn: (data: { id: string, payload: TicketTriageUpdate }) => {
    return http.patch<TicketResponse>(`/api/agent/tickets/${data.id}/triage`, data.payload)
  },
  onSuccess: () => {
    message.success('分诊成功')
    showTriageDrawer.value = false
    queryClient.invalidateQueries({ queryKey: ['agentTickets'] })
  },
  onError: (err: unknown) => {
    const error = err as Error
    message.error(error.message || '分诊失败')
  }
})

function handleTriageSubmit() {
  if (triageTicket.value) {
    triageMutate({ id: triageTicket.value.id, payload: triageModel.value })
  }
}
</script>

<template>
  <div class="service-desk-view">
    <n-grid :cols="3" :x-gap="16" style="margin-bottom: 24px;">
      <n-grid-item>
        <n-card>
          <n-statistic label="全部工单" :value="statsTotal" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="待处理" :value="statsPending" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="已解决" :value="statsResolved" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card>
      <n-tabs v-model:value="activeTab" type="line" animated>
        <n-tab-pane name="customer" tab="客户门户 (提报)">
          <n-space vertical :size="24">
            <TicketForm @success="onTicketCreated" />

            <h3>我的工单历史</h3>
            <n-data-table
              :columns="customerColumns"
              :data="customerTickets || []"
              :loading="customerLoading"
              :bordered="false"
              virtual-scroll
              :max-height="400"
            />
          </n-space>
        </n-tab-pane>

        <n-tab-pane name="agent" tab="内部分诊台 (处理)">
          <n-space vertical :size="24">
            <h3>全量反馈池</h3>
            <n-data-table
              :columns="agentColumns"
              :data="agentTickets || []"
              :loading="agentLoading"
              :bordered="false"
              virtual-scroll
              :max-height="600"
            />
          </n-space>
        </n-tab-pane>
      </n-tabs>
    </n-card>

    <n-drawer v-model:show="showTriageDrawer" :width="500" placement="right">
      <n-drawer-content title="工单分诊" closable>
        <n-form :model="triageModel" label-placement="top">
          <n-form-item label="修正工单类型">
            <n-select v-model:value="triageModel.ticket_type" :options="[
              { label: '故障反馈 (Incident)', value: 'INCIDENT' },
              { label: '需求建议 (Requirement)', value: 'REQUIREMENT' },
              { label: '技术咨询 (Consultation)', value: 'CONSULTATION' },
              { label: '缺陷报告 (Bug)', value: 'BUG' }
            ]" />
          </n-form-item>
          <n-form-item label="流转产品线">
            <n-select v-model:value="triageModel.product_id" :options="productOptions" placeholder="分配给底层敏捷产品池" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space>
            <n-button :disabled="triagePending" @click="showTriageDrawer = false">取消</n-button>
            <n-button type="primary" :loading="triagePending" @click="handleTriageSubmit">确认分诊</n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<style scoped>
.service-desk-view {
  padding: var(--space-4);
  background-color: var(--color-bg-base);
  min-height: 100vh;
}
</style>
