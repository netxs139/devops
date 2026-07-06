<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import {
  NCard,
  NGrid,
  NGi,
  NStatistic,
  NSkeleton,
  NTag,
  useMessage
} from 'naive-ui'
import { useDocumentVisibility } from '@vueuse/core'
import { http } from '@/utils/request'
import type { DoraDashboardSummary } from '@/types/api'

const message = useMessage()
const visibility = useDocumentVisibility()

const loading = ref(true)
const doraData = ref<DoraDashboardSummary[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

const fetchData = async () => {
  try {
    const res = await http.get<DoraDashboardSummary[]>('/bi/metrics/dora/summary')
    doraData.value = res
  } catch {
    message.error('Failed to fetch DORA metrics')
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(() => {
    if (visibility.value === 'visible') {
      fetchData()
    }
  }, 15000) // 15s polling matches TTL
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

watch(visibility, (current) => {
  if (current === 'visible') {
    fetchData()
    startPolling()
  } else {
    stopPolling()
  }
})

onMounted(() => {
  fetchData()
  startPolling()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<template>
  <div class="dora-dashboard">
    <div class="page-header">
      <h2>DORA Metrics Dashboard</h2>
      <p class="subtitle">Deployment Frequency, Lead Time, MTTR, and Change Failure Rate</p>
    </div>

    <!-- 骨架屏占位 -->
    <n-grid v-if="loading" :x-gap="16" :y-gap="16" cols="1 s:1 m:2 l:3 xl:3" responsive="screen">
      <n-gi v-for="i in 6" :key="i">
        <n-card class="dora-card" :bordered="false">
          <n-skeleton text :repeat="1" height="24px" width="60%" />
          <n-skeleton text :repeat="3" style="margin-top: 16px" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 真实数据渲染 -->
    <n-grid v-else :x-gap="16" :y-gap="16" cols="1 s:1 m:2 l:3 xl:3" responsive="screen">
      <n-gi v-for="product in doraData" :key="product.product_name">
        <n-card class="dora-card" :bordered="false" size="small">
          <template #header>
            <div class="card-header">
              <span class="product-name">{{ product.product_name }}</span>
              <n-tag
                v-if="product.performance_rating"
                :style="{ backgroundColor: product.health_color_hex || 'var(--color-primary)', color: '#fff', border: 'none' }"
                size="small"
                round
              >
                {{ product.performance_rating }}
              </n-tag>
            </div>
          </template>

          <n-grid :cols="2" :x-gap="12" :y-gap="12">
            <n-gi>
              <n-statistic label="Deployment Frequency">
                <div class="stat-value">
                  {{ product.deployment_frequency ?? '-' }}
                  <span v-if="product.deploy_trend_icon" class="trend">{{ product.deploy_trend_icon }}</span>
                </div>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="Lead Time (Hours)">
                <div class="stat-value">
                  {{ product.lead_time_hours ?? '-' }}
                  <span v-if="product.lead_time_trend_icon" class="trend">{{ product.lead_time_trend_icon }}</span>
                </div>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="MTTR (Hours)">
                <div class="stat-value">
                  {{ product.mttr_hours ?? '-' }}
                  <span v-if="product.mttr_trend_icon" class="trend">{{ product.mttr_trend_icon }}</span>
                </div>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="Change Failure Rate">
                <div class="stat-value">
                  {{ product.change_failure_rate_pct != null ? product.change_failure_rate_pct + '%' : '-' }}
                  <span v-if="product.cfr_trend_icon" class="trend">{{ product.cfr_trend_icon }}</span>
                </div>
              </n-statistic>
            </n-gi>
          </n-grid>
          <div class="card-footer">
            <span class="meta-info">Last updated: {{ product.last_updated_month }}</span>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<style scoped>
.dora-dashboard {
  padding: var(--space-4);
  background-color: var(--color-bg-base);
  min-height: 100%;
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  margin: 0 0 var(--space-2) 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.subtitle {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.dora-card {
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow var(--transition-base) ease;
}

.dora-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 16px;
}

.stat-value {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.trend {
  font-size: 14px;
  color: var(--color-text-tertiary);
}

.card-footer {
  margin-top: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  text-align: right;
}

.meta-info {
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>
