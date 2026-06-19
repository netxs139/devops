<script setup lang="ts">
/**
 * @file TestCaseDetail.vue
 * @description 测试用例详情面板 (GitLab Style x Apple Aesthetic)
 */
import { ref, computed, watch } from 'vue'
import {
  NTag,
  NButton,
  NInput,
  NSelect,
  NProgress,
  useMessage
} from 'naive-ui'
import type { TestCase, ExecutionReport, TestCaseStatus, BusinessException } from '@/types/api'
import { http } from '@/utils/request'

const props = defineProps<{
  caseItem: TestCase
  projectId: number
}>()

const emit = defineEmits<{
  executed: [result: TestCaseStatus]
  'report-bug': [payload: { iid: number; title: string }]
}>()

const message = useMessage()

// 状态管理
const completedSteps = ref<Record<number, boolean>>({})
const comment = ref('')
const environment = ref('QA')
const executing = ref(false)

// 监听 caseItem 变化重置步骤进度
watch(() => props.caseItem.iid, () => {
  completedSteps.value = {}
  comment.value = ''
}, { immediate: true })

const stepsTotal = computed(() => props.caseItem.steps?.length ?? 0)
const stepsCheckedCount = computed(() => {
  return Object.values(completedSteps.value).filter(Boolean).length
})
const stepsPercentage = computed(() => {
  const total = stepsTotal.value
  if (total === 0) return 0
  return Math.round((stepsCheckedCount.value / total) * 100)
})

const envOptions = [
  { label: '测试环境 (QA)', value: 'QA' },
  { label: '开发环境 (Dev)', value: 'Dev' },
  { label: '预发环境 (Pre-prod)', value: 'Pre-prod' },
  { label: '生产环境 (Prod)', value: 'Prod' }
]

function toggleStep(stepNumber: number) {
  completedSteps.value[stepNumber] = !completedSteps.value[stepNumber]
}

// 提交执行结果
async function submitExecution(result: TestCaseStatus) {
  if (result === 'failed' && !comment.value.trim()) {
    message.error('测试执行失败时，必须填写执行备注或异常证据！')
    return
  }

  executing.value = true
  try {
    const payload: ExecutionReport = {
      result,
      comment: comment.value.trim() || null,
      environment: environment.value
    }

    await http.post(
      `/test-management/projects/${props.projectId}/test-cases/${props.caseItem.iid}/execute?result=${result}`,
      payload
    )

    message.success(`用例 #${props.caseItem.iid} 已成功标记为 ${result === 'passed' ? '通过' : '失败'}`)
    emit('executed', result)
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error(err.message || '提交执行结果失败')
  } finally {
    executing.value = false
  }
}

function handleReportBug() {
  emit('report-bug', {
    iid: props.caseItem.iid,
    title: props.caseItem.title
  })
}
</script>

<template>
  <div class="detail-container">
    <div class="main-content">
      <div class="header">
        <div class="iid">Test Case #{{ props.caseItem.iid }}</div>
        <h1 class="title">{{ props.caseItem.title }}</h1>
      </div>

      <div class="section">
        <div class="section-title">前置条件</div>
        <div class="content-box">
          <ul v-if="props.caseItem.pre_conditions && props.caseItem.pre_conditions.length > 0" class="pre-list">
            <li v-for="(pre, idx) in props.caseItem.pre_conditions" :key="idx">
              {{ pre }}
            </li>
          </ul>
          <div v-else class="text-dim">无前置条件。</div>
        </div>
      </div>

      <div class="section">
        <div class="section-title-row">
          <span class="section-title">执行步骤</span>
          <span class="step-progress-text">
            已完成 {{ stepsCheckedCount }} / {{ stepsTotal }} 项 ({{ stepsPercentage }}%)
          </span>
        </div>
        <div class="progress-bar-wrapper">
          <NProgress
            type="line"
            :percentage="stepsPercentage"
            :show-indicator="false"
            color="var(--color-success)"
            processing
          />
        </div>
        <div v-if="props.caseItem.steps && props.caseItem.steps.length > 0" class="steps-list">
          <div
            v-for="step in props.caseItem.steps"
            :key="step.step_number"
            class="step-item"
            :class="{ 'is-completed': completedSteps[step.step_number] }"
            @click="toggleStep(step.step_number)"
          >
            <div class="step-check" :class="{ 'is-checked': completedSteps[step.step_number] }">
              <svg
                v-if="completedSteps[step.step_number]"
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="4"
              >
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            <div class="step-num">{{ step.step_number }}</div>
            <div class="step-body">
              <div class="step-action">{{ step.action }}</div>
              <div class="step-expect">
                <span class="expect-label">预期反馈:</span>
                {{ step.expected_result }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-dim italic">未定义步骤。</div>
      </div>
    </div>

    <div class="sidebar">
      <div class="sidebar-group">
        <div class="sidebar-label">当前状态</div>
        <div class="status-badge-wrapper">
          <NTag
            :type="props.caseItem.result === 'passed' ? 'success' : props.caseItem.result === 'failed' ? 'error' : props.caseItem.result === 'blocked' ? 'warning' : 'default'"
            round
            size="medium"
          >
            {{ props.caseItem.result?.toUpperCase() || 'PENDING' }}
          </NTag>
        </div>
      </div>

      <div class="sidebar-group">
        <div class="sidebar-label">优先级</div>
        <div class="sidebar-value">
          <NTag :bordered="false" size="small" type="info">
            {{ props.caseItem.priority || 'P2' }}
          </NTag>
        </div>
      </div>

      <div class="sidebar-group">
        <div class="sidebar-label">关联需求</div>
        <div class="sidebar-value text-link">
          {{ props.caseItem.requirement_id ? '#' + props.caseItem.requirement_id : '无关联需求' }}
        </div>
      </div>

      <div class="sidebar-group">
        <div class="sidebar-label">所属主项目</div>
        <div class="sidebar-value">{{ props.caseItem.project_name || '-' }}</div>
      </div>

      <div class="exec-toolbar">
        <div class="sidebar-label center-label">执行反馈记录</div>

        <NSelect
          v-model:value="environment"
          :options="envOptions"
          size="small"
          class="margin-bottom"
        />

        <NInput
          v-model:value="comment"
          type="textarea"
          placeholder="添加执行备注或异常证据 (执行失败时为必填项)..."
          :autosize="{ minRows: 3, maxRows: 6 }"
          class="margin-bottom"
        />

        <NButton
          type="success"
          block
          secondary
          :loading="executing"
          class="margin-bottom"
          @click="submitExecution('passed')"
        >
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
          </template>
          标记为 通过 (Pass)
        </NButton>

        <NButton
          type="error"
          block
          secondary
          :loading="executing"
          class="margin-bottom"
          @click="submitExecution('failed')"
        >
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </template>
          标记为 失败 (Fail)
        </NButton>

        <NButton
          type="warning"
          block
          secondary
          :loading="executing"
          class="margin-bottom"
          @click="submitExecution('blocked')"
        >
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </template>
          标记为 阻塞 (Blocked)
        </NButton>

        <NButton
          type="primary"
          block
          ghost
          class="margin-top"
          @click="handleReportBug"
        >
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2c0 4-4 8-4 8s-4-4-4-8 4-8 4-8z"></path>
              <path d="M8 14c0 4 4 8 4 8s4-4 4-8-4-8-4-8z"></path>
              <circle cx="9" cy="9" r="2"></circle>
              <circle cx="15" cy="9" r="2"></circle>
            </svg>
          </template>
          一键提报缺陷 (Bug)
        </NButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-container {
  display: grid;
  grid-template-columns: 1fr 240px;
  height: 100%;
}

.main-content {
  padding: var(--space-4) var(--space-6);
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
}

.header {
  margin-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--space-4);
}

.iid {
  font-family: monospace;
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-bottom: var(--space-1);
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  margin: 0;
}

.section {
  margin-bottom: var(--space-6);
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
  margin-bottom: var(--space-2);
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.step-progress-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.progress-bar-wrapper {
  margin-bottom: var(--space-4);
}

.content-box {
  background: var(--color-bg-base);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  font-size: 14px;
}

.pre-list {
  margin: 0;
  padding-left: var(--space-4);
}

.pre-list li {
  margin-bottom: var(--space-1);
}

.text-dim {
  color: var(--color-text-secondary);
}

.italic {
  font-style: italic;
}

/* Steps List */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.step-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.step-item:hover {
  border-color: var(--color-primary-hover);
  background: var(--color-primary-light);
}

.step-item.is-completed {
  opacity: 0.6;
}

.step-check {
  width: 18px;
  height: 18px;
  border-radius: var(--radius-sm);
  border: 2px solid var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-top: 2px;
  flex-shrink: 0;
  background: #ffffff;
  transition: all var(--transition-fast);
  color: transparent;
}

.step-check.is-checked {
  background: var(--color-success);
  border-color: var(--color-success);
  color: #ffffff;
}

.step-num {
  width: 22px;
  height: 22px;
  background: var(--color-bg-base);
  color: var(--color-text-secondary);
  border-radius: 50%;
  text-align: center;
  line-height: 22px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-item.is-completed .step-num {
  background: var(--color-border);
}

.step-body {
  flex: 1;
}

.step-action {
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.step-item.is-completed .step-action {
  text-decoration: line-through;
  color: var(--color-text-secondary);
}

.step-expect {
  color: var(--color-text-secondary);
  font-size: 13px;
  background: var(--color-bg-base);
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  margin-top: var(--space-2);
}

.expect-label {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 11px;
  text-transform: uppercase;
  display: block;
  margin-bottom: 2px;
}

/* Sidebar */
.sidebar {
  padding: var(--space-4) var(--space-3);
  background: var(--color-bg-base);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  border-left: 1px solid var(--color-border);
}

.sidebar-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.center-label {
  text-align: center;
  margin-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 4px;
}

.sidebar-value {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
}

.text-link {
  color: var(--color-primary);
  font-weight: 600;
}

.exec-toolbar {
  display: flex;
  flex-direction: column;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.margin-bottom {
  margin-bottom: var(--space-2);
}

.margin-top {
  margin-top: var(--space-3);
}
</style>
