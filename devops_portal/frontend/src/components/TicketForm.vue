<script setup lang="ts">
/**
 * @file TicketForm.vue
 * @description 客服工单提交表单组件（绿地重构版），供外部客户提交问题或需求。
 * 遵守 Naive UI 规范及 VueUse 生态。
 */
import { ref, reactive } from 'vue'
import {
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NButton,
  useMessage,
  type FormInst,
  type FormRules
} from 'naive-ui'
import { useMutation } from '@tanstack/vue-query'
import { http } from '@/utils/request'
import type { TicketCreateExternal, TicketResponse } from '@/types/api'

const emit = defineEmits<{
  (e: 'success', ticket: TicketResponse): void
  (e: 'cancel'): void
}>()

const formRef = ref<FormInst | null>(null)
const message = useMessage()

const formModel = reactive<TicketCreateExternal>({
  title: '',
  description: '',
  ticket_type: 'CONSULTATION'
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入工单标题', trigger: 'blur' }],
  ticket_type: [{ required: true, message: '请选择工单类型', trigger: 'blur' }]
}

const typeOptions = [
  { label: '故障反馈 (Incident)', value: 'INCIDENT' },
  { label: '需求建议 (Requirement)', value: 'REQUIREMENT' },
  { label: '技术咨询 (Consultation)', value: 'CONSULTATION' },
  { label: '缺陷报告 (Bug)', value: 'BUG' }
]

const { mutate: createTicket, isPending } = useMutation({
  mutationFn: (data: TicketCreateExternal) => {
    return http.post<TicketResponse>('/api/customer/tickets', data)
  },
  onSuccess: (data) => {
    message.success('工单提交成功！')
    emit('success', data) // TicketResponse
  },
  onError: (err: unknown) => {
    const error = err as Error
    message.error(error.message || '工单提交失败，请重试')
  }
})

function handleSubmit() {
  formRef.value?.validate((errors) => {
    if (!errors) {
      createTicket(formModel)
    }
  })
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <div class="ticket-form-wrapper">
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="top"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="工单标题" path="title">
        <n-input v-model:value="formModel.title" placeholder="请简述您遇到的问题或需求" />
      </n-form-item>

      <n-form-item label="工单类型" path="ticket_type">
        <n-select v-model:value="formModel.ticket_type" :options="typeOptions" />
      </n-form-item>

      <n-form-item label="详细描述" path="description">
        <n-input
          v-model:value="formModel.description"
          type="textarea"
          placeholder="请提供详细信息以便我们更好地帮助您"
          :autosize="{ minRows: 4, maxRows: 8 }"
        />
      </n-form-item>

      <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px;">
        <n-button :disabled="isPending" @click="handleCancel">取消</n-button>
        <n-button type="primary" :loading="isPending" @click="handleSubmit">
          提交工单
        </n-button>
      </div>
    </n-form>
  </div>
</template>

<style scoped>
.ticket-form-wrapper {
  padding: var(--space-4);
  background-color: var(--color-bg-card);
  border-radius: var(--radius-md);
}
</style>
