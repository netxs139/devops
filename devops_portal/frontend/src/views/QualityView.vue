<script setup lang="ts">
/**
 * @file QualityView.vue
 * @description 质量监控大屏 (Quality Monitor)
 * 核心指标：同步成功率, 审计异常, 数据新鲜度
 */
import { ref } from 'vue'
import { NGrid, NGridItem, NCard, NStatistic, NSpace, NText, NProgress, NAlert } from 'naive-ui'

// Mock Data
const syncSuccessRate = ref(99.8)
const auditAnomalies = ref(12)
const dataFreshness = ref(5) // mins

const anomalyList = ref([
  { id: 1, type: 'Data Drop', desc: 'GitLab Commit sync dropped 20 events', time: '10:24 AM' },
  { id: 2, type: 'Schema Mismatch', desc: 'Jira API response schema changed', time: '09:12 AM' },
  { id: 3, type: 'High Latency', desc: 'SonarQube API latency > 5s', time: '08:45 AM' },
])
</script>

<template>
  <div class="quality-container">
    <div class="header-section">
      <h1 class="page-title">质量监控 (Quality Monitor)</h1>
      <p class="page-subtitle">底座数据采集与同步的健康度总览</p>
    </div>

    <!-- 核心指标看板 -->
    <NGrid :cols="3" :x-gap="24" class="stats-grid">
      <NGridItem>
        <NCard class="stat-card" size="small">
          <NSpace justify="space-between" align="center">
            <NStatistic label="同步成功率 (Sync Success)">
              <NText type="success" style="font-size: 28px; font-weight: 600;">
                {{ syncSuccessRate }}<span style="font-size: 16px;">%</span>
              </NText>
            </NStatistic>
            <div class="progress-ring">
              <NProgress type="circle" :percentage="syncSuccessRate" status="success" :show-indicator="false" :stroke-width="8" style="width: 50px;" />
            </div>
          </NSpace>
        </NCard>
      </NGridItem>

      <NGridItem>
        <NCard class="stat-card" size="small">
          <NStatistic label="审计异常 (Audit Anomalies)">
            <NText type="error" style="font-size: 28px; font-weight: 600;">
              {{ auditAnomalies }}
            </NText>
          </NStatistic>
          <template #footer>
            <NText depth="3" style="font-size: 12px;">较昨日增加 3 项</NText>
          </template>
        </NCard>
      </NGridItem>

      <NGridItem>
        <NCard class="stat-card" size="small">
          <NStatistic label="数据新鲜度 (Data Freshness)">
            <NText type="info" style="font-size: 28px; font-weight: 600;">
              {{ dataFreshness }}<span style="font-size: 16px;"> mins</span>
            </NText>
          </NStatistic>
          <template #footer>
            <NText depth="3" style="font-size: 12px;">平均延迟</NText>
          </template>
        </NCard>
      </NGridItem>
    </NGrid>

    <NGrid :cols="1" :y-gap="24" class="details-grid">
      <NGridItem>
        <NCard title="最新审计异常" class="list-card" :bordered="false">
          <NSpace vertical :size="12">
            <NAlert v-for="item in anomalyList" :key="item.id" type="warning" show-icon>
              <template #header>
                {{ item.type }} <span class="time-stamp">- {{ item.time }}</span>
              </template>
              {{ item.desc }}
            </NAlert>
          </NSpace>
        </NCard>
      </NGridItem>
    </NGrid>
  </div>
</template>

<style scoped>
.quality-container {
  max-width: 1440px;
  margin: 0 auto;
}

.header-section {
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

.list-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.02);
}

.time-stamp {
  font-size: 12px;
  color: var(--color-text-tertiary);
  font-weight: normal;
}
</style>
