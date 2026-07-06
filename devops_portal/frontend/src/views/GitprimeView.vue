<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import {
  NCard,
  NDataTable,
  type DataTableColumns,
  NTag,
  NSkeleton,
  useMessage
} from 'naive-ui'
import { useDocumentVisibility } from '@vueuse/core'
import { http } from '@/utils/request'
import type { DeveloperActivityProfile } from '@/types/api'

const message = useMessage()
const visibility = useDocumentVisibility()

const loading = ref(true)
const activityData = ref<DeveloperActivityProfile[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

const columns: DataTableColumns<DeveloperActivityProfile> = [
  {
    title: 'Developer',
    key: 'developer_name',
    width: 200,
    render(row: DeveloperActivityProfile) {
      return row.developer_name
    }
  },
  {
    title: 'Archetype',
    key: 'developer_archetype',
    width: 150,
    render(row: DeveloperActivityProfile) {
      if (!row.developer_archetype) return '-'
      const typeMap: Record<string, 'default' | 'success' | 'warning' | 'info' | 'error'> = {
        'Review Master': 'success',
        'Code Machine': 'warning',
        'Task Closer': 'info',
        'Generalist': 'default'
      }
      return h(NTag, {
        type: typeMap[row.developer_archetype] || 'default',
        round: true,
        size: 'small'
      }, { default: () => row.developer_archetype })
    }
  },
  {
    title: 'Impact Score',
    key: 'total_impact_score',
    width: 150,
    sorter: 'default'
  },
  {
    title: 'Daily Velocity',
    key: 'daily_velocity',
    width: 150,
    sorter: 'default'
  },
  {
    title: 'Total Commits',
    key: 'total_commits',
    width: 150,
    sorter: 'default'
  },
  {
    title: 'Total Reviews',
    key: 'total_reviews',
    width: 150,
    sorter: 'default'
  },
  {
    title: 'Active Days',
    key: 'active_days_count',
    width: 150
  }
]

const fetchData = async () => {
  try {
    const res = await http.get<DeveloperActivityProfile[]>('/bi/metrics/developer/activity')
    activityData.value = res
  } catch {
    message.error('Failed to fetch developer activity')
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
  }, 15000)
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

<script lang="ts">
import { h } from 'vue'
</script>

<template>
  <div class="gitprime-dashboard">
    <div class="page-header">
      <h2>Developer Activity (Gitprime)</h2>
      <p class="subtitle">Developer Impact, Velocity, and Archetypes</p>
    </div>

    <n-card class="data-card" :bordered="false">
      <!-- 骨架屏占位 -->
      <div v-if="loading" class="skeleton-wrapper">
        <n-skeleton text :repeat="5" height="40px" style="margin-bottom: 8px" />
      </div>

      <!-- 真实数据渲染 -->
      <n-data-table
        v-else
        :columns="columns"
        :data="activityData"
        :pagination="{ pageSize: 15 }"
        virtual-scroll
        style="max-height: 600px;"
        :row-key="(row: DeveloperActivityProfile) => row.developer_name"
      />
    </n-card>
  </div>
</template>

<style scoped>
.gitprime-dashboard {
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

.data-card {
  border-radius: var(--radius-lg);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.skeleton-wrapper {
  padding: var(--space-4);
}
</style>
