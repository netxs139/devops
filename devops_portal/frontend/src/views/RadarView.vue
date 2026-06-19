<script setup lang="ts">
/**
 * @file RadarView.vue
 * @description Traceability Radar 效能看板视图
 */
import { ref, onMounted, watch } from 'vue'
import {
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NSpace,
  NSelect,
  NButton,
  NDrawer,
  NDrawerContent,
  NList,
  NListItem,
  NThing,
  NTag,
  NEmpty,
  useMessage
} from 'naive-ui'
import type { RadarResponse, RadarDetailItem, RadarDetailResponse, MDMProject, BusinessException } from '@/types/api'
import { http } from '@/utils/request'
import ProductSelector from '@/components/ProductSelector.vue'
import Radar from '@/components/Radar.vue'

const message = useMessage()

// 过滤参数
const scopeType = ref<'product' | 'org'>('product')
const scopeId = ref<string | null>(null)
const days = ref(30)

// 数据缓存
const mdmProjects = ref<MDMProject[]>([])
const targetProjectId = ref<number | null>(null)
const radarData = ref<RadarResponse | null>(null)
const loading = ref(false)

// 下钻抽屉控制
const drawerActive = ref(false)
const drawerTitle = ref('')
const drawerLoading = ref(false)
const drawerItems = ref<RadarDetailItem[]>([])

// 自动解析 GitLab 项目 ID
watch([scopeType, scopeId], () => {
  if (scopeType.value === 'product' && scopeId.value) {
    const matched = mdmProjects.value.find(proj =>
      proj.products?.some(p => p.product_id === scopeId.value)
    )
    targetProjectId.value = matched?.lead_repo_id ?? null
  } else {
    targetProjectId.value = null
  }
  loadRadarData()
})

// 监听天数变化刷新数据
watch(days, () => {
  loadRadarData()
})

async function loadMdmProjects() {
  try {
    const data = await http.get<MDMProject[]>('/admin/mdm-projects')
    mdmProjects.value = data
  } catch (error) {
    console.error('Failed to load mdm-projects:', error)
  }
}

// 获取雷达与 VSM 聚合数据
async function loadRadarData() {
  loading.value = true
  try {
    const params: Record<string, string | number> = { days: days.value }
    if (targetProjectId.value) {
      params.project_id = targetProjectId.value
    }

    const data = await http.get<RadarResponse>('/traceability/radar', { params })
    radarData.value = data
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error('加载雷达效能数据失败: ' + err.message)
    radarData.value = null
  } finally {
    loading.value = false
  }
}

// 展开指标明细下钻
async function handleDrilldown(type: 'VSM_WAITING' | 'RUBBER_STAMP' | 'VULNERABILITY', title: string) {
  drawerTitle.value = title
  drawerActive.value = true
  drawerLoading.value = true
  drawerItems.value = []

  try {
    const params: Record<string, string | number> = {
      metric_type: type,
      days: days.value
    }
    if (targetProjectId.value) {
      params.project_id = targetProjectId.value
    }

    const response = await http.get<RadarDetailResponse>('/traceability/detail', { params })
    drawerItems.value = response.items
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error('加载下钻详情失败: ' + err.message)
  } finally {
    drawerLoading.value = false
  }
}

function handleScopeChange(payload: { type: 'product' | 'org'; id: string | null }) {
  scopeType.value = payload.type
  scopeId.value = payload.id
}

onMounted(() => {
  loadMdmProjects()
  loadRadarData() // 初次加载，默认显示全局
})

const daysOptions = [
  { label: '最近 7 天', value: 7 },
  { label: '最近 30 天', value: 30 },
  { label: '最近 90 天', value: 90 },
  { label: '最近 180 天', value: 180 },
  { label: '最近 365 天', value: 365 }
]
</script>

<template>
  <div class="radar-page">
    <!-- 过滤器面板 -->
    <div class="toolbar">
      <NSpace align="center" justify="space-between" style="width: 100%;">
        <ProductSelector
          :id="scopeId"
          :type="scopeType"
          @change="handleScopeChange"
        />
        <NSpace align="center" :size="16">
          <NSelect
            v-model:value="days"
            :options="daysOptions"
            style="width: 130px;"
          />
          <NButton
            type="primary"
            secondary
            :loading="loading"
            @click="loadRadarData"
          >
            同步刷新
          </NButton>
        </NSpace>
      </NSpace>
    </div>

    <!-- 数据图表面板 -->
    <div v-if="radarData" class="dashboard-content">
      <!-- 指标卡片行 -->
      <NGrid :cols="4" :x-gap="24" class="stat-grid">
        <!-- 平均等待评审时长 -->
        <NGridItem>
          <NCard
            class="stat-card clickable"
            size="small"
            @click="handleDrilldown('VSM_WAITING', '长等待合并请求 (MR) 列表')"
          >
            <NStatistic label="平均评审等待时间" :value="Math.round(radarData.vsm.avg_wait_minutes)">
              <template #suffix><span class="unit">分钟</span></template>
            </NStatistic>
            <div class="card-footer">
              <span class="view-detail-text">点击查看长等待 MR 详情 ↗</span>
            </div>
          </NCard>
        </NGridItem>

        <!-- 秒批率 -->
        <NGridItem>
          <NCard
            class="stat-card clickable"
            size="small"
            @click="handleDrilldown('RUBBER_STAMP', '秒批合并请求 (MR) 预警')"
          >
            <NStatistic label="合并请求秒批率" :value="(radarData.collaboration.rubber_stamp_rate * 100).toFixed(1)">
              <template #suffix><span class="unit red">%</span></template>
            </NStatistic>
            <div class="card-footer">
              <span class="view-detail-text">点击查看秒批 MR 预警 ↗</span>
            </div>
          </NCard>
        </NGridItem>

        <!-- 有效评审率 -->
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="有效同行评审率" :value="(radarData.collaboration.effective_review_rate * 100).toFixed(1)">
              <template #suffix><span class="unit green">%</span></template>
            </NStatistic>
            <div class="card-footer">
              <span class="detail-label">均次评论:</span>
              <span class="detail-val">{{ radarData.collaboration.avg_effective_comments }} 个</span>
            </div>
          </NCard>
        </NGridItem>

        <!-- 安全漏洞 -->
        <NGridItem>
          <NCard
            class="stat-card clickable highlight-error"
            size="small"
            @click="handleDrilldown('VULNERABILITY', '活跃安全漏洞明细')"
          >
            <NStatistic label="活跃安全漏洞数" :value="radarData.security.total_active">
              <template #suffix><span class="unit">个</span></template>
            </NStatistic>
            <div class="card-footer">
              <span class="view-detail-text">
                {{ radarData.security.critical }} Critical / {{ radarData.security.high }} High ↗
              </span>
            </div>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 雷达与 ELOC + VSM 表格 -->
      <Radar :data="radarData" />
    </div>

    <!-- 加载与空数据兜底 -->
    <div v-else class="empty-state">
      <NEmpty description="无雷达效能数据，请重新选择产品/项目或刷新同步数据" />
    </div>

    <!-- 下钻详情抽屉 -->
    <NDrawer v-model:show="drawerActive" :width="500" placement="right">
      <NDrawerContent :title="drawerTitle" closable>
        <div v-if="drawerLoading" style="padding: 40px; text-align: center; color: var(--color-text-secondary);">
          加载明细数据中...
        </div>
        <div v-else-if="drawerItems.length > 0" class="drawer-list-wrapper">
          <NList hoverable clickable>
            <NListItem v-for="item in drawerItems" :key="item.id">
              <NThing>
                <template #header-extra>
                  <span class="drawer-timestamp">
                    {{ item.timestamp ? item.timestamp.split('T')[0] : '' }}
                  </span>
                </template>
                <template #header>
                  <span class="drawer-item-id">#{{ item.id }}</span>
                </template>
                <template #description>
                  <div class="drawer-item-title">{{ item.title }}</div>
                </template>
                <template #footer>
                  <div class="drawer-item-footer">
                    <NSpace align="center" justify="space-between" style="width: 100%;">
                      <NSpace>
                        <NTag v-if="item.author" size="small" :bordered="false" type="info">
                          {{ item.author }}
                        </NTag>
                        <NTag v-if="item.value" size="small" :bordered="false" type="success">
                          {{ item.value }}
                        </NTag>
                      </NSpace>
                      <a :href="item.url || '#'" target="_blank" class="gitlab-link-btn">
                        在 GitLab 中查看 ↗
                      </a>
                    </NSpace>
                  </div>
                </template>
              </NThing>
            </NListItem>
          </NList>
        </div>
        <div v-else class="empty-drawer">
          <NEmpty description="暂无相关下钻明细记录" />
        </div>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.radar-page {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.toolbar {
  margin-bottom: var(--space-4);
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.stat-grid {
  margin-bottom: var(--space-2);
}

.stat-card {
  border-radius: var(--radius-lg);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.01);
  transition: all var(--transition-fast) ease;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  box-shadow: 0 8px 24px rgba(26, 86, 219, 0.08);
}

.stat-card.highlight-error.clickable:hover {
  border-color: var(--color-error);
  box-shadow: 0 8px 24px rgba(239, 68, 68, 0.08);
}

.card-footer {
  margin-top: var(--space-2);
  border-top: 1px solid var(--color-border);
  padding-top: 6px;
  display: flex;
  align-items: center;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.view-detail-text {
  color: var(--color-primary);
  font-weight: 500;
}

.highlight-error .view-detail-text {
  color: var(--color-error);
}

.detail-label {
  font-weight: 500;
  margin-right: 4px;
}

.detail-val {
  font-weight: 600;
  color: var(--color-text-primary);
}

.unit {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-left: 4px;
}
.unit.red { color: var(--color-error); }
.unit.green { color: var(--color-success); }

.empty-state {
  padding: 100px 0;
  text-align: center;
}

/* Drawer styles */
.drawer-timestamp {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.drawer-item-id {
  font-family: monospace;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.drawer-item-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-top: 4px;
}

.drawer-item-footer {
  margin-top: var(--space-2);
  width: 100%;
}

.gitlab-link-btn {
  font-size: 12px;
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.gitlab-link-btn:hover {
  text-decoration: underline;
}

.empty-drawer {
  padding: 80px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
