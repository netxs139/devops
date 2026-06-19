<script setup lang="ts">
/**
 * @file TestCaseView.vue
 * @description 测试用例管理控制台主视图
 */
import { ref, onMounted, computed, watch } from 'vue'
import {
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NSpace,
  NInput,
  NSelect,
  NButton,
  NDrawer,
  NDrawerContent,
  NEmpty,
  useMessage
} from 'naive-ui'
import type { TestCase, TestSummary, TestCaseStatus, BusinessException, MDMProject } from '@/types/api'
import { http } from '@/utils/request'
import ProductSelector from '@/components/ProductSelector.vue'
import TestCaseDetail from '@/components/TestCaseDetail.vue'
import TestCaseForm from '@/components/TestCaseForm.vue'

const message = useMessage()

// 控制主视图切换: 'list' 列表页, 'create' 新建用例页
const currentView = ref<'list' | 'create'>('list')

// 过滤参数
const scopeType = ref<'product' | 'org'>('product')
const scopeId = ref<string | null>(null)
const searchKeyword = ref('')
const statusFilter = ref<string>('all')
const priorityFilter = ref<string>('all')

// 数据缓存
const allCases = ref<TestCase[]>([])
const mdmProjects = ref<MDMProject[]>([])
const statsTotal = ref(0)
const statsPassed = ref(0)
const statsFailed = ref(0)
const statsBlocked = ref(0)

// 选中的用例详情 & 抽屉控制
const drawerActive = ref(false)
const selectedCase = ref<TestCase | null>(null)
const targetProjectId = ref<number | null>(null)
const loading = ref(false)

// 自动解析 GitLab 仓库 ID
watch([scopeType, scopeId], () => {
  if (scopeType.value === 'product' && scopeId.value) {
    const matched = mdmProjects.value.find(proj =>
      proj.products?.some(p => p.product_id === scopeId.value)
    )
    targetProjectId.value = matched?.lead_repo_id ?? null
  } else {
    targetProjectId.value = null
  }
  loadTestCases()
})

// 拉取主项目列表 (用于解析 GitLab ID)
async function loadMdmProjects() {
  try {
    const data = await http.get<MDMProject[]>('/admin/mdm-projects')
    mdmProjects.value = data
  } catch (error) {
    console.error('Failed to load mdm-projects:', error)
  }
}

// 核心：根据当前产品/部门拉取用例列表
async function loadTestCases() {
  if (!scopeId.value) {
    allCases.value = []
    resetStats()
    return
  }

  loading.value = true
  try {
    let url = ''
    if (scopeType.value === 'product') {
      url = `/test-management/aggregated/test-cases?product_id=${scopeId.value}`
    } else {
      url = `/test-management/aggregated/test-cases?org_id=${scopeId.value}`
    }

    const data = await http.get<TestCase[]>(url)
    allCases.value = data

    // 统计更新
    if (scopeType.value === 'product' && targetProjectId.value) {
      // 若是单项目，尝试从后端获取更精确的统计
      await loadTestSummary(targetProjectId.value)
    } else {
      // 否则进行本地聚合计算
      calcStatsLocal(data)
    }
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error('加载用例列表失败: ' + err.message)
    allCases.value = []
    resetStats()
  } finally {
    loading.value = false
  }
}

// 获取后端统计
async function loadTestSummary(projectId: number) {
  try {
    const summary = await http.get<TestSummary>(`/test-management/projects/${projectId}/test-summary`)
    statsTotal.value = summary.total
    statsPassed.value = summary.passed
    statsFailed.value = summary.failed
    statsBlocked.value = summary.blocked ?? 0
  } catch {
    calcStatsLocal(allCases.value)
  }
}

function calcStatsLocal(cases: TestCase[]) {
  statsTotal.value = cases.length
  statsPassed.value = cases.filter(c => c.result === 'passed').length
  statsFailed.value = cases.filter(c => c.result === 'failed').length
  statsBlocked.value = cases.filter(c => c.result === 'blocked').length
}

function resetStats() {
  statsTotal.value = 0
  statsPassed.value = 0
  statsFailed.value = 0
  statsBlocked.value = 0
}

const statsPassRate = computed(() => {
  const total = statsTotal.value
  if (total === 0) return 0
  return Math.round((statsPassed.value / total) * 100)
})

// 客户端多维度筛选
const filteredCases = computed(() => {
  let result = allCases.value

  // 搜索词过滤 (ID 或标题)
  const query = searchKeyword.value.trim().toLowerCase()
  if (query) {
    result = result.filter(c =>
      String(c.iid).includes(query) ||
      (c.title || '').toLowerCase().includes(query)
    )
  }

  // 状态过滤
  if (statusFilter.value !== 'all') {
    result = result.filter(c => c.result === statusFilter.value)
  }

  // 优先级过滤
  if (priorityFilter.value !== 'all') {
    result = result.filter(c => c.priority === priorityFilter.value)
  }

  return result
})

// 事件处理器
function handleScopeChange(payload: { type: 'product' | 'org'; id: string | null }) {
  scopeType.value = payload.type
  scopeId.value = payload.id
}

function openCaseDetail(item: TestCase) {
  // 如果没有具体 targetProjectId，尝试从用例关联的 project_name 去主项目中映射
  if (!targetProjectId.value && item.project_name) {
    const matchedProj = mdmProjects.value.find(p => p.project_name === item.project_name)
    selectedCase.value = { ...item }
    drawerActive.value = true
    // 临时设定该用例的执行 project_id
    drawerProjectId.value = matchedProj?.lead_repo_id ?? null
  } else {
    selectedCase.value = { ...item }
    drawerProjectId.value = targetProjectId.value
    drawerActive.value = true
  }
}

const drawerProjectId = ref<number | null>(null)

function handleCaseExecuted(_result: TestCaseStatus) {
  // 刷新列表
  loadTestCases()
  // 刷新 drawer 中选中的 TestCase 详情
  if (selectedCase.value) {
    selectedCase.value.result = _result
  }
}

function handleCaseSaved() {
  currentView.value = 'list'
  loadTestCases()
}

onMounted(() => {
  loadMdmProjects()
})

const statusOptions = [
  { label: '全部执行状态', value: 'all' },
  { label: '通过 (Passed)', value: 'passed' },
  { label: '失败 (Failed)', value: 'failed' },
  { label: '阻塞 (Blocked)', value: 'blocked' },
  { label: '未执行 (Pending)', value: 'pending' }
]

const priorityOptions = [
  { label: '全部优先级', value: 'all' },
  { label: 'P0 - 紧急', value: 'P0' },
  { label: 'P1 - 高', value: 'P1' },
  { label: 'P2 - 中', value: 'P2' },
  { label: 'P3 - 低', value: 'P3' }
]
</script>

<template>
  <div class="test-case-page">
    <!-- 切录入表单视图 -->
    <div v-if="currentView === 'create'">
      <TestCaseForm @saved="handleCaseSaved" @cancel="currentView = 'list'" />
    </div>

    <!-- 列表视图 -->
    <div v-else class="list-layout">
      <!-- 顶部统计卡片 -->
      <NGrid :cols="4" :x-gap="24" class="stats-grid">
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="用例总数" :value="statsTotal">
              <template #suffix><span class="unit">个</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="验证通过" :value="statsPassed">
              <template #suffix><span class="unit green">个</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="验证失败" :value="statsFailed">
              <template #suffix><span class="unit red">个</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
        <NGridItem>
          <NCard class="stat-card" size="small">
            <NStatistic label="用例通过率" :value="statsPassRate">
              <template #suffix><span class="unit primary">%</span></template>
            </NStatistic>
          </NCard>
        </NGridItem>
      </NGrid>

      <!-- 过滤器与工具栏 -->
      <div class="toolbar-card">
        <div class="toolbar-left">
          <ProductSelector
            :id="scopeId"
            :type="scopeType"
            @change="handleScopeChange"
          />
        </div>

        <div v-if="scopeId" class="toolbar-right">
          <NSpace :size="16" align="center">
            <NInput
              v-model:value="searchKeyword"
              placeholder="🔍 搜索用例标题或 ID..."
              clearable
              style="width: 200px;"
            />
            <NSelect
              v-model:value="statusFilter"
              :options="statusOptions"
              style="width: 140px;"
            />
            <NSelect
              v-model:value="priorityFilter"
              :options="priorityOptions"
              style="width: 120px;"
            />
            <NButton
              type="primary"
              :disabled="!targetProjectId"
              @click="currentView = 'create'"
            >
              新建用例
            </NButton>
          </NSpace>
        </div>
      </div>

      <!-- 用例列表 -->
      <div v-if="scopeId" class="list-wrapper">
        <NCard class="table-card" :bordered="false" :loading="loading">
          <div v-if="filteredCases.length > 0" class="test-cases-list">
            <div
              v-for="item in filteredCases"
              :key="item.iid"
              class="case-row"
              @click="openCaseDetail(item)"
            >
              <!-- 状态圈 -->
              <div
                class="status-circle"
                :class="'status-' + (item.result || 'pending')"
              ></div>

              <!-- 用例 ID -->
              <div class="case-iid">#{{ item.iid }}</div>

              <!-- 用例标题 -->
              <div class="case-title">{{ item.title }}</div>

              <!-- 元数据标签 -->
              <div class="case-tags">
                <NTag
                  :bordered="false"
                  size="small"
                  :type="item.priority === 'P0' ? 'error' : item.priority === 'P1' ? 'warning' : 'info'"
                >
                  {{ item.priority || 'P2' }}
                </NTag>
                <NTag
                  round
                  :bordered="false"
                  size="small"
                  :type="item.result === 'passed' ? 'success' : item.result === 'failed' ? 'error' : item.result === 'blocked' ? 'warning' : 'default'"
                >
                  {{ item.result || 'PENDING' }}
                </NTag>
              </div>
            </div>
          </div>
          <div v-else class="empty-layout">
            <NEmpty description="没有匹配的测试用例" />
          </div>
        </NCard>
      </div>

      <!-- 未选择产品提示 -->
      <div v-else class="welcome-layout">
        <NCard class="welcome-card" :bordered="false">
          <div class="welcome-text">
            <h3>🔍 请在左上方选择业务产品或组织部门</h3>
            <p>选择对应的上下文后，系统将自动同步拉取相关的测试用例，并开放用例录入与执行门禁功能。</p>
          </div>
        </NCard>
      </div>
    </div>

    <!-- 侧边抽屉展示用例详情 -->
    <NDrawer v-model:show="drawerActive" :width="750" placement="right">
      <NDrawerContent title="测试用例执行控制台" closable>
        <TestCaseDetail
          v-if="selectedCase && drawerProjectId"
          :case-item="selectedCase"
          :project-id="drawerProjectId"
          @executed="handleCaseExecuted"
          @report-bug="message.info('缺陷提报跳转开发中')"
        />
        <div v-else style="padding: 40px; text-align: center; color: var(--color-text-secondary);">
          项目上下文缺失，无法执行测试，请检查产品与项目的关联映射关系。
        </div>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.test-case-page {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  margin-bottom: var(--space-4);
}

.stat-card {
  border-radius: var(--radius-lg);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.01);
}

.unit {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-left: 4px;
}
.unit.green { color: var(--color-success); }
.unit.red { color: var(--color-error); }
.unit.primary { color: var(--color-primary); }

.toolbar-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  background: transparent;
}

.table-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.02);
  overflow: hidden;
}

.test-cases-list {
  display: flex;
  flex-direction: column;
}

.case-row {
  display: grid;
  grid-template-columns: 24px 60px 1fr auto;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  gap: var(--space-4);
  cursor: pointer;
  border-bottom: 1px solid var(--color-border);
  transition: all var(--transition-fast);
}

.case-row:last-child {
  border-bottom: none;
}

.case-row:hover {
  background: var(--color-primary-light);
}

.status-circle {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-passed {
  background: var(--color-success);
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
}

.status-failed {
  background: var(--color-error);
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.15);
}

.status-blocked {
  background: var(--color-warning);
  box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.15);
}

.status-pending {
  background: var(--color-text-tertiary);
}

.case-iid {
  font-family: monospace;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.case-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.case-tags {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.empty-layout {
  padding: 80px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.welcome-layout {
  margin-top: 40px;
}

.welcome-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  padding: 40px;
  text-align: center;
}

.welcome-text h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.welcome-text p {
  color: var(--color-text-secondary);
  font-size: 14px;
  max-width: 600px;
  margin: 0 auto;
}
</style>
