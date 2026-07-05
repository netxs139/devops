<script setup lang="ts">
/**
 * @file OrgUserAdmin.vue
 * @description 组织与用户管理组件，支持导入、导出及用户画像展示
 */
import { ref, onMounted } from 'vue'
import {
  NCard,
  NTabs,
  NTabPane,
  NTable,
  NSpace,
  NButton,
  NDrawer,
  NDrawerContent,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'
import type { OrganizationView, UserFullProfile, ImportSummary } from '@/types/api'

interface BriefUser {
  user_id: string
  full_name: string
  email: string
}

const message = useMessage()

// 选项控制
const activeTab = ref<'orgs' | 'users'>('orgs')
const loadingOrgs = ref(false)
const loadingUsers = ref(false)
const orgs = ref<OrganizationView[]>([])
const users = ref<BriefUser[]>([])

// 组织表单/弹窗
const showAddOrgModal = ref(false)
const submittingOrg = ref(false)
const orgForm = ref({
  org_id: '',
  org_name: '',
  org_level: 1,
  parent_org_id: null as string | null,
  manager_user_id: null as string | null
})

// 用户详情画像 (Drawer)
const showUserDrawer = ref(false)
const loadingProfile = ref(false)
const userProfile = ref<UserFullProfile | null>(null)

// 引用 file input
const orgFileInput = ref<HTMLInputElement | null>(null)
const userFileInput = ref<HTMLInputElement | null>(null)

// 加载组织
async function loadOrganizations() {
  loadingOrgs.value = true
  try {
    const data = await http.get<OrganizationView[]>('/admin/organizations')
    orgs.value = data
  } catch (err: unknown) {
    message.error('加载组织架构失败: ' + (err as Error).message)
  } finally {
    loadingOrgs.value = false
  }
}

// 加载用户
async function loadUsers() {
  loadingUsers.value = true
  try {
    const data = await http.get<BriefUser[]>('/admin/users')
    users.value = data
  } catch (err: unknown) {
    message.error('加载用户列表失败: ' + (err as Error).message)
  } finally {
    loadingUsers.value = false
  }
}

// 用户画像详情
async function showProfile(userId: string) {
  loadingProfile.value = true
  showUserDrawer.value = true
  userProfile.value = null
  try {
    const data = await http.get<UserFullProfile>(`/admin/users/${userId}`)
    userProfile.value = data
  } catch (err: unknown) {
    message.error('加载用户画像失败: ' + (err as Error).message)
    showUserDrawer.value = false
  } finally {
    loadingProfile.value = false
  }
}

// 创建组织
async function handleCreateOrg() {
  if (!orgForm.value.org_id.trim() || !orgForm.value.org_name.trim()) {
    message.warning('请输入组织 ID 及名称')
    return
  }
  submittingOrg.value = true
  try {
    await http.post('/admin/organizations', {
      org_code: orgForm.value.org_id.trim(),
      org_name: orgForm.value.org_name.trim(),
      org_level: orgForm.value.org_level,
      parent_org_id: orgForm.value.parent_org_id || null,
      manager_user_id: orgForm.value.manager_user_id || null
    })
    message.success('组织创建成功')
    showAddOrgModal.value = false
    loadOrganizations()
  } catch (err: unknown) {
    message.error('创建组织失败: ' + (err as Error).message)
  } finally {
    submittingOrg.value = false
  }
}

// 导出 CSV 通用逻辑
async function handleExport(endpoint: string, filename: string) {
  try {
    const response = await http.get(endpoint, { responseType: 'blob' })
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const blob = new Blob([response as any], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
    message.success('导出成功')
  } catch (err: unknown) {
    message.error('导出失败: ' + (err as Error).message)
  }
}

// 导入 CSV 文件通用逻辑
async function handleImportFile(event: Event, endpoint: string) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  // 限制 5MB
  if (file.size > 5 * 1024 * 1024) {
    message.error('文件大小不得超过 5MB')
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  try {
    message.info('正在解析并导入数据，请稍候...')
    const result = await http.post<ImportSummary>(endpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    const total = result.total_processed || 0
    const success = result.success_count || 0
    const fail = result.failure_count || 0
    message.success(`导入完成。总处理数: ${total}, 成功: ${success}, 失败: ${fail}`)
    if (activeTab.value === 'orgs') {
      loadOrganizations()
    } else {
      loadUsers()
    }
  } catch (err: unknown) {
    message.error('导入失败: ' + (err as Error).message)
  } finally {
    target.value = '' // 清空 input
  }
}

onMounted(() => {
  loadOrganizations()
  loadUsers()
})
</script>

<template>
  <div class="org-user-admin">
    <NCard :bordered="false" size="small">
      <NTabs v-model:value="activeTab" type="line" animated>
        <!-- 组织架构 Tab -->
        <NTabPane name="orgs" tab="🏢 组织架构 (Organizations)">
          <div class="tab-header">
            <NSpace>
              <NButton type="primary" size="small" @click="showAddOrgModal = true">
                新建组织
              </NButton>
              <NButton size="small" @click="orgFileInput?.click()">
                导入组织 CSV
              </NButton>
              <NButton size="small" secondary type="info" @click="handleExport('/admin/export/organizations', 'orgs_export.csv')">
                导出组织 CSV
              </NButton>
            </NSpace>
            <input ref="orgFileInput" type="file" accept=".csv" style="display: none;" @change="handleImportFile($event, '/admin/import/organizations')" />
          </div>

          <NTable :single-line="false" size="small" class="admin-table">
            <thead>
              <tr>
                <th>组织ID (Code)</th>
                <th>组织名称</th>
                <th>层级 (Level)</th>
                <th>负责人</th>
                <th>上级部门</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="org in orgs" :key="org.id">
                <td class="monospace">{{ org.org_id }}</td>
                <td class="weight-medium">{{ org.org_name }}</td>
                <td><NTag size="small" :bordered="false" type="info">LV {{ org.org_level }}</NTag></td>
                <td>{{ org.manager_name || '-' }}</td>
                <td>{{ org.parent_name || '-' }}</td>
              </tr>
              <tr v-if="orgs.length === 0 && !loadingOrgs">
                <td colspan="5" class="empty-cell">🔍 暂无组织架构信息</td>
              </tr>
            </tbody>
          </NTable>
        </NTabPane>

        <!-- 用户管理 Tab -->
        <NTabPane name="users" tab="👤 用户管理 (Users)">
          <div class="tab-header">
            <NSpace>
              <NButton size="small" @click="userFileInput?.click()">
                导入用户 CSV
              </NButton>
              <NButton size="small" secondary type="info" @click="handleExport('/admin/export/users', 'users_export.csv')">
                导出用户 CSV
              </NButton>
            </NSpace>
            <input ref="userFileInput" type="file" accept=".csv" style="display: none;" @change="handleImportFile($event, '/admin/import/users')" />
          </div>

          <NTable :single-line="false" size="small" class="admin-table">
            <thead>
              <tr>
                <th>全局用户 ID</th>
                <th>姓名</th>
                <th>主邮箱</th>
                <th style="text-align: center;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.user_id">
                <td class="monospace-small">{{ u.user_id }}</td>
                <td class="weight-medium">{{ u.full_name }}</td>
                <td>{{ u.email }}</td>
                <td style="text-align: center;">
                  <NButton size="tiny" type="primary" secondary @click="showProfile(u.user_id)">
                    画像详情
                  </NButton>
                </td>
              </tr>
              <tr v-if="users.length === 0 && !loadingUsers">
                <td colspan="4" class="empty-cell">🔍 暂无用户信息</td>
              </tr>
            </tbody>
          </NTable>
        </NTabPane>
      </NTabs>
    </NCard>

    <!-- 新建组织 Modal -->
    <NModal v-model:show="showAddOrgModal" preset="card" title="新建组织机构" style="width: 500px;">
      <NForm :model="orgForm" label-placement="left" label-width="90">
        <NFormItem label="组织 ID">
          <NInput v-model:value="orgForm.org_id" placeholder="如 DEPT_TECH" />
        </NFormItem>
        <NFormItem label="组织名称">
          <NInput v-model:value="orgForm.org_name" placeholder="如 技术研发部" />
        </NFormItem>
        <NFormItem label="组织层级">
          <NInputNumber v-model:value="orgForm.org_level" :min="1" :max="10" />
        </NFormItem>
        <NFormItem label="上级组织代码">
          <NInput v-model:value="orgForm.parent_org_id" placeholder="可空，如 DEPT_ROOT" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showAddOrgModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="submittingOrg" @click="handleCreateOrg">确认创建</NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- 用户画像 Drawer -->
    <NDrawer v-model:show="showUserDrawer" :width="500" placement="right">
      <NDrawerContent title="👤 用户全景画像" closable>
        <div v-if="loadingProfile" style="padding: 24px; text-align: center; color: var(--color-text-secondary);">
          加载画像中...
        </div>
        <div v-else-if="userProfile">
          <NDescriptions label-placement="left" :column="1" bordered size="small" class="profile-desc">
            <NDescriptionsItem label="姓名">{{ userProfile.full_name }}</NDescriptionsItem>
            <NDescriptionsItem label="账号名">{{ userProfile.username || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="主邮箱">{{ userProfile.primary_email }}</NDescriptionsItem>
            <NDescriptionsItem label="工号">{{ userProfile.employee_id || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="所属部门">{{ userProfile.department_name || '-' }}</NDescriptionsItem>
            <NDescriptionsItem label="在职状态">
              <NTag size="small" :bordered="false" :type="userProfile.is_active ? 'success' : 'error'">
                {{ userProfile.is_active ? '在职' : '离职' }}
              </NTag>
            </NDescriptionsItem>
            <NDescriptionsItem label="人事关系">{{ userProfile.hr_relationship || '-' }}</NDescriptionsItem>
          </NDescriptions>

          <!-- 团队身份 -->
          <div class="profile-section-title">👥 所属虚拟团队</div>
          <NTable :single-line="false" size="small" style="margin-top: 8px;">
            <thead>
              <tr>
                <th>团队名称</th>
                <th>角色</th>
                <th>工时占比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in userProfile.teams" :key="t.team_id">
                <td class="weight-medium">{{ t.team_name }}</td>
                <td><NTag size="small" :bordered="false" type="info">{{ t.role }}</NTag></td>
                <td>{{ Math.round(t.allocation * 100) }}%</td>
              </tr>
              <tr v-if="!userProfile.teams || userProfile.teams.length === 0">
                <td colspan="3" style="text-align: center; color: var(--color-text-tertiary);">未加入任何团队</td>
              </tr>
            </tbody>
          </NTable>

          <!-- 身份映射 -->
          <div class="profile-section-title">🔗 外部身份映射</div>
          <NTable :single-line="false" size="small" style="margin-top: 8px;">
            <thead>
              <tr>
                <th>来源系统</th>
                <th>外部用户标识</th>
                <th>置信度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ident in userProfile.identities" :key="ident.id">
                <td><NTag size="small" :bordered="false">{{ ident.source_system }}</NTag></td>
                <td class="monospace-small">{{ ident.external_user_id }}</td>
                <td>{{ Math.round(ident.confidence_score * 100) }}%</td>
              </tr>
              <tr v-if="!userProfile.identities || userProfile.identities.length === 0">
                <td colspan="3" style="text-align: center; color: var(--color-text-tertiary);">暂无身份映射记录</td>
              </tr>
            </tbody>
          </NTable>
        </div>
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
.org-user-admin {
  width: 100%;
}
.tab-header {
  margin-bottom: var(--space-4);
  display: flex;
  justify-content: flex-end;
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
.profile-desc {
  margin-bottom: var(--space-6);
}
.profile-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-top: var(--space-6);
  margin-bottom: var(--space-2);
}
</style>
