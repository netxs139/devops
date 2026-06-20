<script setup lang="ts">
/**
 * @file TicketForm.vue
 * @description 服务台新建工单表单（缺陷提报/产品需求），支持三层项目联动校验与附件上传
 */
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import type { UploadCustomRequestOptions } from 'naive-ui'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NButton,
  NUpload,
  NAlert,
  NSpace,
  NDatePicker,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'
import type { MDMProject, ServiceDeskBugSubmit, ServiceDeskRequirementSubmit } from '@/types/api'

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const route = useRoute()
const message = useMessage()

// 表单模式: 'bug' 缺陷报告, 'requirement' 产品需求
const ticketType = ref<'bug' | 'requirement'>('bug')

// 下拉框数据
interface BusinessProduct {
  id: string
  name: string
  description?: string
  status?: string
}
const products = ref<BusinessProduct[]>([])
const mdmProjects = ref<MDMProject[]>([])
const loading = ref(false)

// 表单响应式状态
const selectedProductId = ref<string | null>(null)
const formTitle = ref('')
const severity = ref('S2')
const priority = ref('P2')
const environment = ref('QA')
const stepsToRepro = ref('')
const actualResult = ref('')
const expectedResult = ref('')
const bugCategory = ref('code-error')
const requirementDescription = ref('')
const reqType = ref('feature')
const expectedDelivery = ref<number | null>(null)
const attachments = ref<string[]>([])
const submitting = ref(false)

// 三层项目联动解析
const matchedProject = computed(() => {
  if (!selectedProductId.value) return null
  return mdmProjects.value.find(proj =>
    proj.products?.some(p => p.product_id === selectedProductId.value)
  ) ?? null
})

const matchedProductInfo = computed(() => {
  if (!selectedProductId.value) return null
  const prod = products.value.find(p => p.id === selectedProductId.value)
  return prod ? `${prod.name} (${prod.id})` : selectedProductId.value
})

const leadRepoId = computed(() => {
  return matchedProject.value?.lead_repo_id ?? null
})

// 选项配置
const severityOptions = [
  { label: 'S1 - 致命 (Blocker)', value: 'S1' },
  { label: 'S2 - 严重 (Critical)', value: 'S2' },
  { label: 'S3 - 一般 (Normal)', value: 'S3' },
  { label: 'S4 - 微小 (Minor)', value: 'S4' }
]

const priorityOptions = [
  { label: 'P0 - 紧急', value: 'P0' },
  { label: 'P1 - 高', value: 'P1' },
  { label: 'P2 - 中', value: 'P2' },
  { label: 'P3 - 低', value: 'P3' }
]

const envOptions = [
  { label: 'QA / 测试环境', value: 'QA' },
  { label: 'Dev / 开发环境', value: 'Dev' },
  { label: 'Pre-prod / 预发环境', value: 'Pre-prod' },
  { label: 'Prod / 生产环境', value: 'Prod' }
]

const bugCategoryOptions = [
  { label: '代码缺陷 (Code Error)', value: 'code-error' },
  { label: '配置相关 (Configuration)', value: 'configuration' },
  { label: '性能问题 (Performance)', value: 'performance' },
  { label: '安全漏洞 (Security)', value: 'security' },
  { label: 'UI体验/不合规 (UI/UX)', value: 'ui-ux' }
]

const reqTypeOptions = [
  { label: '全新功能 (Feature)', value: 'feature' },
  { label: '配置变更 (Config)', value: 'config' },
  { label: '接口对接 (Interface)', value: 'interface' },
  { label: '性能优化 (Optimization)', value: 'optimization' }
]

// 拉取选项数据
async function loadFormData() {
  loading.value = true
  try {
    const [prodData, mdmData] = await Promise.all([
      http.get<BusinessProduct[]>('/service-desk/business-projects'),
      http.get<MDMProject[]>('/admin/mdm-projects')
    ])
    products.value = prodData
    mdmProjects.value = mdmData

    // 默认选中第一个有 lead_repo_id 的产品，或者是 Query 传入的产品
    const queryProd = route.query.product_id as string
    if (queryProd && prodData.some(p => p.id === queryProd)) {
      selectedProductId.value = queryProd
    } else if (prodData.length > 0) {
      selectedProductId.value = prodData[0].id
    }
  } catch (err: unknown) {
    message.error('加载选项数据失败: ' + (err as Error).message)
  } finally {
    loading.value = false
  }
}

// 监听路由 Query 参数回填
function parseQueryParameters() {
  if (route.query.type === 'bug') {
    ticketType.value = 'bug'
  } else if (route.query.type === 'requirement') {
    ticketType.value = 'requirement'
  }

  if (route.query.title) {
    formTitle.value = route.query.title as string
  }
  if (route.query.steps) {
    stepsToRepro.value = route.query.steps as string
  }
}

// Naive UI NUpload 自定义上传处理器
const handleCustomUpload = async ({ file, onFinish, onError, onProgress }: UploadCustomRequestOptions) => {
  if (!matchedProject.value) {
    message.error('请先选择有效的产品以确定项目上下文！')
    onError()
    return
  }
  if (!file.file) {
    message.error('未选择有效的文件！')
    onError()
    return
  }
  const formData = new FormData()
  formData.append('file', file.file)
  try {
    const res = await http.post<{ markdown: string; url: string }>(
      `/service-desk/upload?mdm_id=${matchedProject.value.project_id}`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = progressEvent.total ? Math.round((progressEvent.loaded * 100) / progressEvent.total) : 0
          onProgress({ percent })
        }
      }
    )
    if (res && res.url) {
      attachments.value.push(res.url)
      // 若存在 markdown，自动追加到内容文本框底部方便预览/追踪
      if (res.markdown) {
        if (ticketType.value === 'bug') {
          stepsToRepro.value += `\n\n${res.markdown}`
        } else {
          requirementDescription.value += `\n\n${res.markdown}`
        }
      }
      message.success('附件上传成功')
      onFinish()
    } else {
      throw new Error('未返回有效的附件地址')
    }
  } catch (err: unknown) {
    message.error('附件上传失败: ' + ((err as Error).message || '未知错误'))
    onError()
  }
}

// 提交工单
async function handleSubmit() {
  if (!selectedProductId.value) {
    message.warning('请选择提报的业务产品')
    return
  }
  if (!formTitle.value.trim()) {
    message.warning('标题为必填项')
    return
  }
  if (!leadRepoId.value) {
    message.error('当前选择的产品未配置有效的 GitLab 受理仓库，禁止提报')
    return
  }

  submitting.value = true
  try {
    let res: { message?: string } | null = null
    if (ticketType.value === 'bug') {
      const payload: ServiceDeskBugSubmit = {
        title: formTitle.value.trim(),
        severity: severity.value,
        priority: priority.value,
        environment: environment.value,
        steps_to_repro: stepsToRepro.value.trim(),
        actual_result: actualResult.value.trim(),
        expected_result: expectedResult.value.trim(),
        bug_category: bugCategory.value,
        attachments: attachments.value
      }
      res = await http.post(`/service-desk/submit-bug?mdm_id=${selectedProductId.value}`, payload)
    } else {
      const formattedDate = expectedDelivery.value
        ? new Date(expectedDelivery.value).toISOString().split('T')[0]
        : undefined
      const payload: ServiceDeskRequirementSubmit = {
        title: formTitle.value.trim(),
        description: requirementDescription.value.trim(),
        priority: priority.value,
        req_type: reqType.value,
        expected_delivery: formattedDate,
        attachments: attachments.value
      }
      res = await http.post(`/service-desk/submit-requirement?mdm_id=${selectedProductId.value}`, payload)
    }

    message.success(res?.message || '提报成功！')
    emit('saved')
  } catch (err: unknown) {
    message.error('提报失败: ' + ((err as Error).message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadFormData()
  parseQueryParameters()
})
</script>

<template>
  <div class="ticket-form-card">
    <NCard :bordered="false" size="large" class="apple-card">
      <template #header>
        <div class="card-header-wrapper">
          <div class="header-text-group">
            <h2 class="form-title">新建服务工单</h2>
            <p class="form-subtitle">在线提交产品需求与缺陷反馈，系统将自动映射并流转至 GitLab 敏捷开发中心。</p>
          </div>
          <div class="segmented-control">
            <div
              class="segment"
              :class="{ active: ticketType === 'bug' }"
              @click="ticketType = 'bug'"
            >
              🐞 缺陷提报
            </div>
            <div
              class="segment"
              :class="{ active: ticketType === 'requirement' }"
              @click="ticketType = 'requirement'"
            >
              💡 产品需求
            </div>
          </div>
        </div>
      </template>

      <NForm label-placement="top" size="medium" :disabled="submitting || loading" class="form-body">
        <!-- 业务产品选择 -->
        <div class="form-row">
          <div class="form-col col-24">
            <NFormItem label="归属业务产品 (MDM Product) *" required>
              <NSelect
                v-model:value="selectedProductId"
                :options="products.map(p => ({ label: p.name, value: p.id }))"
                placeholder="请选择受影响或所属的业务产品..."
                filterable
                :loading="loading"
              />
            </NFormItem>
          </div>
        </div>

        <!-- 三层映射联动面板 -->
        <div v-if="selectedProductId" class="form-row">
          <div class="form-col col-24">
            <div class="linkage-panel" :class="{ 'warning-border': !leadRepoId }">
              <div class="linkage-title">💡 三层项目联动映射解析：</div>
              <div class="linkage-content">
                <div class="linkage-item">
                  <span class="label">① 业务产品：</span>
                  <span class="val">{{ matchedProductInfo }}</span>
                </div>
                <div class="linkage-item">
                  <span class="label">② 归属项目：</span>
                  <span class="val">{{ matchedProject ? matchedProject.project_name : '未关联主数据项目' }}</span>
                </div>
                <div class="linkage-item">
                  <span class="label">③ 受理仓库：</span>
                  <span class="val" :class="{ 'error-text': !leadRepoId }">
                    {{ leadRepoId ? `GitLab Repo ID: ${leadRepoId}` : '❌ 无关联 GitLab 仓库' }}
                  </span>
                </div>
              </div>
              <div v-if="!leadRepoId" class="warning-alert-box">
                <NAlert title="映射配置缺失" type="error" :bordered="false">
                  当前所选的业务产品尚未配置对应的线上 GitLab 受理中心（lead_repo_id 缺失）。请联系管理员配置主数据项目映射，或更换产品提报，否则将无法提交。
                </NAlert>
              </div>
            </div>
          </div>
        </div>

        <!-- 标题 -->
        <div class="form-row">
          <div class="form-col col-24">
            <NFormItem label="工单主题/标题 *" required>
              <NInput
                v-model:value="formTitle"
                placeholder="请简明扼要概括问题，例如：[核心模块] 用户认证登录偶发 502 错误"
                maxlength="80"
                show-count
              />
            </NFormItem>
          </div>
        </div>

        <!-- 缺陷表单字段 -->
        <template v-if="ticketType === 'bug'">
          <div class="form-row">
            <div class="form-col col-8">
              <NFormItem label="严重程度 (Severity) *">
                <NSelect v-model:value="severity" :options="severityOptions" />
              </NFormItem>
            </div>
            <div class="form-col col-8">
              <NFormItem label="优先级 (Priority)">
                <NSelect v-model:value="priority" :options="priorityOptions" />
              </NFormItem>
            </div>
            <div class="form-col col-8">
              <NFormItem label="缺陷分类 (Category)">
                <NSelect v-model:value="bugCategory" :options="bugCategoryOptions" />
              </NFormItem>
            </div>
          </div>

          <div class="form-row">
            <div class="form-col col-24">
              <NFormItem label="受影响环境 *">
                <NSelect v-model:value="environment" :options="envOptions" />
              </NFormItem>
            </div>
          </div>

          <div class="form-row">
            <div class="form-col col-24">
              <NFormItem label="复现步骤 (Steps to Reproduce) *">
                <NInput
                  v-model:value="stepsToRepro"
                  type="textarea"
                  :placeholder="'1. 进入登录页\n2. 输入测试账号并快速双击登录按钮\n3. 观察控制台网络请求'"
                  :autosize="{ minRows: 4, maxRows: 8 }"
                />
              </NFormItem>
            </div>
          </div>

          <div class="form-row">
            <div class="form-col col-12">
              <NFormItem label="实际结果 (Actual Result) *">
                <NInput
                  v-model:value="actualResult"
                  type="textarea"
                  placeholder="请输入观察到的实际异常状态，如：按钮卡死，网络请求返回 500"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                />
              </NFormItem>
            </div>
            <div class="form-col col-12">
              <NFormItem label="预期结果 (Expected Result) *">
                <NInput
                  v-model:value="expectedResult"
                  type="textarea"
                  placeholder="请输入正常状态下的系统行为，如：双击后应限制防抖，正常登入系统"
                  :autosize="{ minRows: 3, maxRows: 5 }"
                />
              </NFormItem>
            </div>
          </div>
        </template>

        <!-- 需求表单字段 -->
        <template v-else>
          <div class="form-row">
            <div class="form-col col-8">
              <NFormItem label="需求类型 (Req Type)">
                <NSelect v-model:value="reqType" :options="reqTypeOptions" />
              </NFormItem>
            </div>
            <div class="form-col col-8">
              <NFormItem label="优先级 (Priority)">
                <NSelect v-model:value="priority" :options="priorityOptions" />
              </NFormItem>
            </div>
            <div class="form-col col-8">
              <NFormItem label="期望交付日期">
                <NDatePicker
                  v-model:value="expectedDelivery"
                  type="date"
                  placeholder="请选择日期..."
                  style="width: 100%"
                />
              </NFormItem>
            </div>
          </div>

          <div class="form-row">
            <div class="form-col col-24">
              <NFormItem label="需求描述与验收标准 (Description) *" required>
                <NInput
                  v-model:value="requirementDescription"
                  type="textarea"
                  placeholder="请详细描述此需求的商业价值、用户故事以及具体验收指标 (AC)..."
                  :autosize="{ minRows: 6, maxRows: 12 }"
                />
              </NFormItem>
            </div>
          </div>
        </template>

        <!-- 附件上传 (Naive UI NUpload) -->
        <div class="form-row">
          <div class="form-col col-24">
            <NFormItem label="附件上传 (图片、文档)">
              <NUpload
                multiple
                :disabled="!leadRepoId"
                :custom-request="handleCustomUpload"
                list-type="image-card"
              >
                <div class="upload-placeholder">
                  <span class="upload-icon">➕</span>
                  <span class="upload-text">添加附件</span>
                </div>
              </NUpload>
            </NFormItem>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="form-actions">
          <NSpace :size="16" justify="end">
            <NButton secondary @click="emit('cancel')">取消并返回</NButton>
            <NButton
              type="primary"
              :loading="submitting"
              :disabled="!leadRepoId || !formTitle.trim()"
              @click="handleSubmit"
            >
              {{ leadRepoId ? '提报并同步 GitLab' : '请先绑定受理仓库' }}
            </NButton>
          </NSpace>
        </div>
      </NForm>
    </NCard>
  </div>
</template>

<style scoped>
.ticket-form-card {
  width: 100%;
  max-width: 900px;
  margin: 0 auto var(--space-8) auto;
}

.apple-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.02);
  background: var(--color-bg-card);
}

.card-header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.header-text-group {
  flex: 1;
}

.form-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.form-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.segmented-control {
  display: inline-flex;
  background: rgba(0, 0, 0, 0.05);
  padding: 3px;
  border-radius: var(--radius-lg);
  user-select: none;
}

.segment {
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1);
}

.segment.active {
  background: #ffffff;
  color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.form-body {
  margin-top: var(--space-6);
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  margin-left: -12px;
  margin-right: -12px;
  margin-bottom: var(--space-4);
}

.form-col {
  padding-left: 12px;
  padding-right: 12px;
  box-sizing: border-box;
}

.col-24 { width: 100%; }
.col-12 { width: 50%; }
.col-8 { width: 33.333%; }

.linkage-panel {
  background: var(--color-primary-light);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin-bottom: var(--space-2);
  transition: border-color var(--transition-fast);
}

.linkage-panel.warning-border {
  background: rgba(239, 68, 68, 0.03);
  border-color: var(--color-error);
}

.linkage-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.linkage-content {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.linkage-item {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.linkage-item .val {
  font-weight: 600;
  color: var(--color-text-primary);
}

.linkage-item .error-text {
  color: var(--color-error);
}

.warning-alert-box {
  margin-top: var(--space-3);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.upload-icon {
  font-size: 20px;
  margin-bottom: 4px;
}

.upload-text {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.form-actions {
  margin-top: var(--space-8);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

@media (max-width: 768px) {
  .col-12, .col-8 {
    width: 100%;
  }
  .card-header-wrapper {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
