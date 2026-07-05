<script setup lang="ts">
/**
 * @file IdentityMappingAdmin.vue
 * @description 身份映射管理组件，支持绑定外部账号、修改状态及删除
 */
import { ref, onMounted } from 'vue'
import {
  NCard,
  NTable,
  NSpace,
  NButton,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'
import type { IdentityMappingView } from '@/types/api'

interface BriefUser {
  user_id: string
  full_name: string
  email: string
}

const message = useMessage()
const loading = ref(false)
const mappings = ref<IdentityMappingView[]>([])
const users = ref<BriefUser[]>([])

// 新增映射相关
const showAddModal = ref(false)
const submitting = ref(false)
const mappingForm = ref({
  global_user_id: '',
  source_system: 'gitlab',
  external_user_id: '',
  external_username: '',
  external_email: ''
})

const systemOptions = [
  { label: 'GitLab', value: 'gitlab' },
  { label: 'ZenTao (禅道)', value: 'zentao' },
  { label: 'SonarQube', value: 'sonarqube' },
  { label: 'Jenkins', value: 'jenkins' }
]

// 加载映射
async function loadMappings() {
  loading.value = true
  try {
    const data = await http.get<IdentityMappingView[]>('/admin/identity-mappings')
    mappings.value = data
  } catch (err: unknown) {
    message.error('加载身份映射失败: ' + (err as Error).message)
  } finally {
    loading.value = false
  }
}

// 加载用户（供下拉框选择）
async function loadUsers() {
  try {
    const data = await http.get<BriefUser[]>('/admin/users')
    users.value = data
  } catch (err: unknown) {
    console.error('加载用户失败', err)
  }
}

// 更改状态（启用/禁用）
async function toggleStatus(mapping: IdentityMappingView) {
  const nextStatus = mapping.mapping_status === 'active' ? 'inactive' : 'active'
  try {
    await http.patch(`/admin/identity-mappings/${mapping.id}/status`, {
      mapping_status: nextStatus
    })
    message.success(`映射已成功${nextStatus === 'active' ? '启用' : '禁用'}`)
    loadMappings()
  } catch (err: unknown) {
    message.error('修改状态失败: ' + (err as Error).message)
  }
}

// 删除映射
async function handleDelete(mappingId: number) {
  try {
    await http.delete(`/admin/identity-mappings/${mappingId}`)
    message.success('映射删除成功')
    loadMappings()
  } catch (err: unknown) {
    message.error('删除映射失败: ' + (err as Error).message)
  }
}

// 创建映射
async function handleCreateMapping() {
  if (!mappingForm.value.global_user_id || !mappingForm.value.external_user_id.trim()) {
    message.warning('请选择关联的系统用户并输入外部 ID')
    return
  }
  submitting.value = true
  try {
    await http.post('/admin/identity-mappings', {
      global_user_id: mappingForm.value.global_user_id,
      source_system: mappingForm.value.source_system,
      external_user_id: mappingForm.value.external_user_id.trim(),
      external_username: mappingForm.value.external_username.trim() || null,
      external_email: mappingForm.value.external_email.trim() || null
    })
    message.success('外部账号映射绑定成功')
    showAddModal.value = false
    // 重置表单
    mappingForm.value.global_user_id = ''
    mappingForm.value.external_user_id = ''
    mappingForm.value.external_username = ''
    mappingForm.value.external_email = ''
    loadMappings()
  } catch (err: unknown) {
    message.error('绑定映射失败: ' + (err as Error).message)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadMappings()
  loadUsers()
})
</script>

<template>
  <div class="identity-mapping-admin">
    <NCard :bordered="false" size="small">
      <div class="card-header">
        <div class="header-desc">统一外部身份对齐与治理操作台</div>
        <NButton type="primary" size="small" @click="showAddModal = true">
          绑定外部账号
        </NButton>
      </div>

      <NTable :single-line="false" size="small" class="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>系统用户</th>
            <th>外部源系统</th>
            <th>外部用户 ID</th>
            <th>外部用户名</th>
            <th>置信度 (Confidence)</th>
            <th>状态</th>
            <th style="text-align: center; width: 180px;">管理操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in mappings" :key="m.id">
            <td class="monospace-small">#{{ m.id }}</td>
            <td class="weight-medium">{{ m.user_name || 'Unknown' }}</td>
            <td>
              <NTag size="small" :bordered="false" type="info">
                {{ m.source_system.toUpperCase() }}
              </NTag>
            </td>
            <td class="monospace">{{ m.external_user_id }}</td>
            <td>{{ m.external_username || '-' }}</td>
            <td>
              <span :style="{ color: m.confidence_score >= 0.8 ? 'var(--color-success)' : 'var(--color-warning)' }">
                {{ Math.round(m.confidence_score * 100) }}%
              </span>
            </td>
            <td>
              <NTag size="small" :bordered="false" :type="m.mapping_status === 'active' ? 'success' : 'default'">
                {{ m.mapping_status === 'active' ? '生效中' : '已禁用' }}
              </NTag>
            </td>
            <td style="text-align: center;">
              <NSpace justify="center" :size="8">
                <NButton size="tiny" secondary :type="m.mapping_status === 'active' ? 'warning' : 'success'" @click="toggleStatus(m)">
                  {{ m.mapping_status === 'active' ? '禁用' : '启用' }}
                </NButton>
                <NButton size="tiny" ghost type="error" @click="handleDelete(m.id)">
                  解绑
                </NButton>
              </NSpace>
            </td>
          </tr>
          <tr v-if="mappings.length === 0 && !loading">
            <td colspan="8" class="empty-cell">🔍 暂无外部身份映射数据</td>
          </tr>
        </tbody>
      </NTable>
    </NCard>

    <!-- 绑定外部账号 Modal -->
    <NModal v-model:show="showAddModal" preset="card" title="绑定外部账号身份" style="width: 500px;">
      <NForm :model="mappingForm" label-placement="left" label-width="90">
        <NFormItem label="系统用户">
          <NSelect
            v-model:value="mappingForm.global_user_id"
            placeholder="请选择要关联的平台用户"
            :options="users.map(u => ({ label: `${u.full_name} (${u.email})`, value: u.user_id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="来源系统">
          <NSelect v-model:value="mappingForm.source_system" :options="systemOptions" />
        </NFormItem>
        <NFormItem label="外部用户 ID">
          <NInput v-model:value="mappingForm.external_user_id" placeholder="外部系统的唯一标识 ID (如 GitLab User ID)" />
        </NFormItem>
        <NFormItem label="外部账号名">
          <NInput v-model:value="mappingForm.external_username" placeholder="可选，外部系统中的用户名" />
        </NFormItem>
        <NFormItem label="外部邮箱">
          <NInput v-model:value="mappingForm.external_email" placeholder="可选，外部系统中的绑定邮箱" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showAddModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="submitting" @click="handleCreateMapping">确认绑定</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.identity-mapping-admin {
  width: 100%;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
.header-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
}
.admin-table {
  width: 100%;
  margin-top: var(--space-2);
}
.monospace {
  font-family: var(--font-mono, monospace);
  font-size: 13px;
  color: var(--color-text-secondary);
}
.monospace-small {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--color-text-secondary);
}
.weight-medium {
  font-weight: 500;
}
.empty-cell {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--color-text-tertiary);
}
</style>
