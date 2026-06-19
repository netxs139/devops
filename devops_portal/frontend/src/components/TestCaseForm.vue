<script setup lang="ts">
/**
 * @file TestCaseForm.vue
 * @description 建立测试用例表单 (Apple Style Card Form)
 */
import { ref, onMounted, computed, watch } from 'vue'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NButton,
  NSpace,
  NInputNumber,
  NDivider,
  useMessage
} from 'naive-ui'
import type { TestCaseCreate, BusinessException, MDMProject } from '@/types/api'
import { http } from '@/utils/request'

interface Product {
  product_id: string
  product_name: string
}

interface Organization {
  org_id: string
  org_name: string
  org_level: number
}

interface StepInput {
  action: string
  expected: string
}

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const message = useMessage()

// 表单状态
const orgId = ref<string | null>(null)
const productId = ref<string | null>(null)
const title = ref('')
const requirementIid = ref<number | null>(null)
const priority = ref('P2')
const testType = ref('功能测试')
const preConditions = ref('')
const steps = ref<StepInput[]>([{ action: '', expected: '' }])

const products = ref<Product[]>([])
const organizations = ref<Organization[]>([])
const mdmProjects = ref<MDMProject[]>([])
const loading = ref(false)
const saving = ref(false)
const aiGenerating = ref(false)

// 解析出的 GitLab 仓库 ID
const targetProjectId = ref<number | null>(null)

// 根据选择的产品自动解析 GitLab 仓库 ID (lead_repo_id)
watch(productId, (newProductId) => {
  if (!newProductId) {
    targetProjectId.value = null
    return
  }

  // 查找包含该产品的主项目
  const matchedProject = mdmProjects.value.find(proj =>
    proj.products?.some(p => p.product_id === newProductId)
  )

  if (matchedProject && matchedProject.lead_repo_id) {
    targetProjectId.value = matchedProject.lead_repo_id
  } else {
    targetProjectId.value = null
    message.warning('该产品尚未关联任何 GitLab 项目，无法录入用例，请联系管理员！')
  }
})

// 加载产品、组织和主项目列表
async function loadFormData() {
  loading.value = true
  try {
    const [prodData, orgData, projData] = await Promise.all([
      http.get<Product[]>('/admin/products'),
      http.get<Organization[]>('/admin/organizations'),
      http.get<MDMProject[]>('/admin/mdm-projects')
    ])
    products.value = prodData
    organizations.value = orgData
    mdmProjects.value = projData
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error('加载选项数据失败: ' + err.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFormData()
})

// 选项列表转换
const orgOptions = computed(() => {
  return organizations.value.map(o => {
    const indent = o.org_level > 1 ? '\u00A0\u00A0'.repeat(o.org_level - 1) + '├─ ' : ''
    return {
      label: indent + o.org_name,
      value: o.org_id
    }
  })
})

const productOptions = computed(() => {
  return products.value.map(p => ({
    label: p.product_name,
    value: p.product_id
  }))
})

const priorityOptions = [
  { label: 'P0 - 紧急 (Blocker)', value: 'P0' },
  { label: 'P1 - 高 (Critical)', value: 'P1' },
  { label: 'P2 - 中 (Normal)', value: 'P2' },
  { label: 'P3 - 低 (Minor)', value: 'P3' }
]

const testTypeOptions = [
  { label: '功能测试', value: '功能测试' },
  { label: '兼容性测试', value: '兼容性测试' },
  { label: '性能测试', value: '性能测试' },
  { label: '安全测试', value: '安全测试' },
  { label: 'UI/体验测试', value: 'UI/体验测试' }
]

// 步骤操作
function addStep() {
  steps.value.push({ action: '', expected: '' })
}

function removeStep(index: number) {
  if (steps.value.length > 1) {
    steps.value.splice(index, 1)
  }
}

// AI 生成步骤
async function handleAiGenerate() {
  if (!targetProjectId.value || !requirementIid.value) {
    message.warning('请先选择所属产品，并输入有效的关联需求 ID (Issue IID)！')
    return
  }

  aiGenerating.value = true
  try {
    const response = await http.post<{ title?: string; steps: Array<{ action: string; expected: string }> }>(
      `/test-management/projects/${targetProjectId.value}/test-cases/generate-from-ac?requirement_iid=${requirementIid.value}`
    )
    if (response.steps && response.steps.length > 0) {
      steps.value = response.steps.map(s => ({
        action: s.action,
        expected: s.expected
      }))
      message.success('✨ AI 已根据需求验收标准自动为您生成测试步骤！')
    } else {
      message.info('未能从该需求中提取到有效的验收标准步骤。')
    }
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error('AI 生成失败: ' + err.message)
  } finally {
    aiGenerating.value = false
  }
}

// 提交表单
async function handleSubmit() {
  if (!title.value.trim() || !productId.value || !orgId.value || !targetProjectId.value) {
    message.warning('标题、部门、产品及有效的目标仓库均为必填项！')
    return
  }

  const selectedProduct = products.value.find(p => p.product_id === productId.value)
  const selectedOrg = organizations.value.find(o => o.org_id === orgId.value)

  const productName = selectedProduct ? selectedProduct.product_name : ''
  const orgName = selectedOrg ? selectedOrg.org_name : ''

  // 过滤出有内容的步骤
  const stepsData = steps.value
    .filter(s => s.action.trim())
    .map((s, idx) => ({
      step_number: idx + 1,
      action: s.action,
      expected: s.expected
    }))

  if (stepsData.length === 0) {
    message.warning('请至少填写一个有效的操作步骤！')
    return
  }

  saving.value = true
  try {
    const payload: TestCaseCreate = {
      title: title.value.trim(),
      priority: priority.value,
      test_type: testType.value,
      pre_conditions: preConditions.value.trim(),
      steps: stepsData,
      requirement_iid: requirementIid.value || null,
      product_id: productName, // 传递名称用于 Label
      org_id: orgName          // 传递名称用于 Label
    }

    await http.post(`/test-management/projects/${targetProjectId.value}/test-cases`, payload)
    message.success('测试用例保存并同步至 GitLab 成功！')
    emit('saved')
  } catch (error: unknown) {
    const err = error as Error | BusinessException
    message.error('保存失败: ' + err.message)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="form-container">
    <NCard class="form-card" :bordered="false">
      <template #header>
        <div class="form-header">
          <h2 class="form-title">建立测试用例</h2>
          <p class="form-subtitle">录入结构化的测试场景，支持 AI 结合需求验收标准生成测试步骤。</p>
        </div>
      </template>

      <NForm label-placement="top" size="medium" :disabled="saving || aiGenerating">
        <NGrid :cols="24" :x-gap="24">
          <!-- 归属部门 -->
          <NGridItem :span="12">
            <NFormItem label="所属部门 *" required>
              <NSelect
                v-model:value="orgId"
                :options="orgOptions"
                placeholder="🔍 请选择归属部门..."
                filterable
              />
            </NFormItem>
          </NGridItem>

          <!-- 所属产品 -->
          <NGridItem :span="12">
            <NFormItem label="所属产品 *" required>
              <NSelect
                v-model:value="productId"
                :options="productOptions"
                placeholder="🔍 请选择归属业务产品..."
                filterable
              />
            </NFormItem>
          </NGridItem>

          <!-- 用例标题 -->
          <NGridItem :span="12">
            <NFormItem label="用例标题 *" required>
              <NInput
                v-model:value="title"
                placeholder="例如：验证多因素认证登录流程"
              />
            </NFormItem>
          </NGridItem>

          <!-- 关联需求 -->
          <NGridItem :span="12">
            <NFormItem label="关联需求 ID (Issue IID)">
              <div class="ai-input-group">
                <NInputNumber
                  v-model:value="requirementIid"
                  placeholder="可选项，如 101"
                  :show-button="false"
                  style="width: 100%;"
                />
                <NButton
                  type="primary"
                  ghost
                  :loading="aiGenerating"
                  :disabled="!targetProjectId || !requirementIid"
                  @click="handleAiGenerate"
                >
                  ✨ AI 生成步骤
                </NButton>
              </div>
            </NFormItem>
          </NGridItem>

          <!-- 优先级 -->
          <NGridItem :span="12">
            <NFormItem label="优先级">
              <NSelect v-model:value="priority" :options="priorityOptions" />
            </NFormItem>
          </NGridItem>

          <!-- 测试类型 -->
          <NGridItem :span="12">
            <NFormItem label="测试类型">
              <NSelect v-model:value="testType" :options="testTypeOptions" />
            </NFormItem>
          </NGridItem>

          <!-- 前置条件 -->
          <NGridItem :span="24">
            <NFormItem label="前置条件">
              <NInput
                v-model:value="preConditions"
                type="textarea"
                placeholder="描述执行该用例前系统需达到的状态..."
                :autosize="{ minRows: 2, maxRows: 4 }"
              />
            </NFormItem>
          </NGridItem>
        </NGrid>

        <NDivider />

        <!-- 步骤区块 -->
        <div class="steps-section">
          <div class="steps-title">执行步骤与预期反馈 (Steps) *</div>
          <div class="steps-container">
            <div
              v-for="(step, idx) in steps"
              :key="idx"
              class="step-row"
            >
              <NInput
                v-model:value="step.action"
                :placeholder="'操作步骤 ' + (idx + 1)"
                class="step-input"
              />
              <NInput
                v-model:value="step.expected"
                :placeholder="'预期反馈 ' + (idx + 1)"
                class="step-input"
              />
              <NButton
                type="error"
                circle
                quaternary
                size="small"
                :disabled="steps.length === 1"
                @click="removeStep(idx)"
              >
                ✕
              </NButton>
            </div>
          </div>
          <NButton
            dashed
            block
            type="primary"
            class="add-step-btn"
            @click="addStep"
          >
            + 添加新步骤
          </NButton>
        </div>

        <NDivider />

        <!-- 操作区 -->
        <div class="form-actions">
          <NSpace justify="end" :size="16">
            <NButton secondary @click="emit('cancel')">
              取消并返回
            </NButton>
            <NButton
              type="primary"
              :loading="saving"
              :disabled="!targetProjectId"
              @click="handleSubmit"
            >
              {{ targetProjectId ? '保存并同步至 GitLab' : '请选择有效关联产品' }}
            </NButton>
          </NSpace>
        </div>
      </NForm>
    </NCard>
  </div>
</template>

<style scoped>
.form-container {
  max-width: 800px;
  margin: 20px auto;
}

.form-card {
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--color-border);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
}

.form-header {
  padding-bottom: var(--space-2);
}

.form-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
  letter-spacing: -0.01em;
}

.form-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.ai-input-group {
  display: flex;
  gap: var(--space-2);
  width: 100%;
}

.steps-section {
  margin-top: var(--space-2);
}

.steps-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  margin-bottom: var(--space-3);
  letter-spacing: 0.05em;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.step-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.step-input {
  flex: 1;
}

.add-step-btn {
  border-radius: var(--radius-md);
}

.form-actions {
  padding-top: var(--space-2);
}
</style>
