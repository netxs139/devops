<script setup lang="ts">
/**
 * @file ProjectMappingAdmin.vue
 * @description 主项目 (MDM) 与 GitLab 仓库绑定组件，支持设定受理中心
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
  NCheckbox,
  NInputNumber,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'

interface MDMProject {
  project_id: string
  project_name: string
  project_type: string
  status: string
  org_name: string
  repo_count: number
  lead_repo_id: number | null
  products: Array<{ product_id: string; product_name: string; relation_type: string }>
}

interface UnlinkedRepo {
  id: number
  name: string
  path: string
}

interface Org {
  id: number
  org_id: string
  org_name: string
}

const message = useMessage()
const loading = ref(false)
const projects = ref<MDMProject[]>([])
const unlinkedRepos = ref<UnlinkedRepo[]>([])
const orgs = ref<Org[]>([])

// 新建主项目 Modal
const showAddProjectModal = ref(false)
const submittingProject = ref(false)
const projectForm = ref({
  project_code: '',
  project_name: '',
  org_id: null as number | null,
  project_type: 'SPRINT',
  status: 'PLAN'
})

// 关联仓库 Modal
const showLinkRepoModal = ref(false)
const linking = ref(false)
const linkForm = ref({
  mdm_project_code: '',
  gitlab_project_id: null as number | null,
  is_lead: false
})

// 设定受理中心 (Lead Repo) Modal
const showSetLeadModal = ref(false)
const settingLead = ref(false)
const leadRepoForm = ref({
  project_code: '',
  gitlab_project_id: null as number | null
})

// 加载主项目
async function loadProjects() {
  loading.value = true
  try {
    const data = await http.get<MDMProject[]>('/admin/mdm-projects')
    projects.value = data
  } catch (err: unknown) {
    message.error('加载主项目列表失败: ' + (err as Error).message)
  } finally {
    loading.value = false
  }
}

// 加载未关联仓库
async function loadUnlinkedRepos() {
  try {
    const data = await http.get<UnlinkedRepo[]>('/admin/unlinked-repos')
    unlinkedRepos.value = data
  } catch (err: unknown) {
    console.error('加载未关联仓库失败', err)
  }
}

// 加载组织（供主项目归属选择）
async function loadOrgs() {
  try {
    const data = await http.get<Org[]>('/admin/organizations')
    orgs.value = data
  } catch (err: unknown) {
    console.error('加载部门失败', err)
  }
}

// 创建主项目
async function handleCreateProject() {
  if (!projectForm.value.project_code.trim() || !projectForm.value.project_name.trim() || !projectForm.value.org_id) {
    message.warning('请填写主项目代码、名称及归属组织')
    return
  }
  submittingProject.value = true
  try {
    await http.post('/admin/mdm-projects', {
      project_code: projectForm.value.project_code.trim(),
      project_name: projectForm.value.project_name.trim(),
      org_id: projectForm.value.org_id,
      project_type: projectForm.value.project_type,
      status: projectForm.value.status
    })
    message.success('业务主项目创建成功')
    showAddProjectModal.value = false
    // 重置
    projectForm.value.project_code = ''
    projectForm.value.project_name = ''
    projectForm.value.org_id = null
    loadProjects()
  } catch (err: unknown) {
    message.error('创建主项目失败: ' + (err as Error).message)
  } finally {
    submittingProject.value = false
  }
}

// 关联仓库
async function handleLinkRepo() {
  if (!linkForm.value.mdm_project_code || !linkForm.value.gitlab_project_id) {
    message.warning('请选择主项目与要绑定的 GitLab 仓库')
    return
  }
  linking.value = true
  try {
    await http.post('/admin/link-repo', {
      mdm_project_code: linkForm.value.mdm_project_code,
      gitlab_project_id: linkForm.value.gitlab_project_id,
      is_lead: linkForm.value.is_lead
    })
    message.success('GitLab 仓库成功关联至主项目')
    showLinkRepoModal.value = false
    linkForm.value.mdm_project_code = ''
    linkForm.value.gitlab_project_id = null
    linkForm.value.is_lead = false
    loadProjects()
    loadUnlinkedRepos()
  } catch (err: unknown) {
    message.error('关联仓库失败: ' + (err as Error).message)
  } finally {
    linking.value = false
  }
}

// 打开设置受理中心 Modal
function openSetLeadModal(projectCode: string) {
  leadRepoForm.value.project_code = projectCode
  leadRepoForm.value.gitlab_project_id = null
  showSetLeadModal.value = true
}

// 提交受理中心设置
async function handleSetLeadRepo() {
  if (!leadRepoForm.value.gitlab_project_id) {
    message.warning('请输入 GitLab 仓库 ID')
    return
  }
  settingLead.value = true
  try {
    await http.post(`/admin/mdm-projects/${leadRepoForm.value.project_code}/set-lead`, {
      gitlab_project_id: leadRepoForm.value.gitlab_project_id
    })
    message.success('受理中心仓库设定成功')
    showSetLeadModal.value = false
    loadProjects()
  } catch (err: unknown) {
    message.error('设置受理中心失败: ' + (err as Error).message)
  } finally {
    settingLead.value = false
  }
}

onMounted(() => {
  loadProjects()
  loadUnlinkedRepos()
  loadOrgs()
})
</script>

<template>
  <div class="project-mapping-admin">
    <NCard :bordered="false" size="small">
      <div class="card-header">
        <div class="header-desc">关联 GitLab 物理仓库到 MDM 业务主项目，并定义线上受理中心 (Lead Repo)</div>
        <NSpace>
          <NButton type="primary" size="small" @click="showAddProjectModal = true">
            新建主项目
          </NButton>
          <NButton size="small" secondary type="info" @click="showLinkRepoModal = true">
            关联 GitLab 仓库
          </NButton>
        </NSpace>
      </div>

      <NTable :single-line="false" size="small" class="admin-table">
        <thead>
          <tr>
            <th>主项目代码 (Code)</th>
            <th>主项目名称</th>
            <th>类型</th>
            <th>当前状态</th>
            <th>归属组织</th>
            <th>已绑仓库数</th>
            <th>关联产品</th>
            <th>受理仓 ID (Lead Repo)</th>
            <th style="text-align: center;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in projects" :key="p.project_id">
            <td class="monospace-small weight-medium">{{ p.project_id }}</td>
            <td class="weight-medium">{{ p.project_name }}</td>
            <td><NTag size="small" :bordered="false">{{ p.project_type }}</NTag></td>
            <td>
              <NTag size="small" :bordered="false" :type="p.status === 'PLAN' ? 'info' : 'success'">
                {{ p.status }}
              </NTag>
            </td>
            <td>{{ p.org_name }}</td>
            <td>
              <span class="weight-medium" style="color: var(--color-primary)">
                {{ p.repo_count }}
              </span>
            </td>
            <td>
              <NSpace :size="4">
                <NTag v-for="prod in p.products" :key="prod.product_id" size="small" :bordered="false" type="info">
                  {{ prod.product_name }}
                </NTag>
                <span v-if="!p.products || p.products.length === 0" class="dim-text">-</span>
              </NSpace>
            </td>
            <td>
              <NSpace v-if="p.lead_repo_id" align="center" :size="8">
                <span class="monospace-small">#{{ p.lead_repo_id }}</span>
                <NTag size="tiny" type="success" :bordered="false">Lead</NTag>
              </NSpace>
              <span v-else class="dim-text">未设定</span>
            </td>
            <td style="text-align: center;">
              <NButton size="tiny" secondary type="warning" @click="openSetLeadModal(p.project_id)">
                设定受理仓
              </NButton>
            </td>
          </tr>
          <tr v-if="projects.length === 0 && !loading">
            <td colspan="9" class="empty-cell">🔍 暂无业务主项目及仓库映射数据</td>
          </tr>
        </tbody>
      </NTable>
    </NCard>

    <!-- 新建主项目 Modal -->
    <NModal v-model:show="showAddProjectModal" preset="card" title="新建业务主项目" style="width: 500px;">
      <NForm :model="projectForm" label-placement="left" label-width="90">
        <NFormItem label="项目代码">
          <NInput v-model:value="projectForm.project_code" placeholder="如 PRJ_2026_ERP" />
        </NFormItem>
        <NFormItem label="项目名称">
          <NInput v-model:value="projectForm.project_name" placeholder="如 企业 ERP 系统升级项目" />
        </NFormItem>
        <NFormItem label="归属组织">
          <NSelect
            v-model:value="projectForm.org_id"
            placeholder="选择归属部门"
            :options="orgs.map(o => ({ label: o.org_name, value: o.id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="项目类型">
          <NSelect
            v-model:value="projectForm.project_type"
            :options="[
              { label: '迭代项目 (SPRINT)', value: 'SPRINT' },
              { label: '瀑布项目 (WATERFALL)', value: 'WATERFALL' }
            ]"
          />
        </NFormItem>
        <NFormItem label="项目状态">
          <NSelect
            v-model:value="projectForm.status"
            :options="[
              { label: '规划中 (PLAN)', value: 'PLAN' },
              { label: '开发中 (DEV)', value: 'DEV' },
              { label: '归档 (ARCHIVED)', value: 'ARCHIVED' }
            ]"
          />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showAddProjectModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="submittingProject" @click="handleCreateProject">确认创建</NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- 关联仓库 Modal -->
    <NModal v-model:show="showLinkRepoModal" preset="card" title="关联 GitLab 仓库" style="width: 500px;">
      <NForm :model="linkForm" label-placement="left" label-width="100">
        <NFormItem label="业务主项目">
          <NSelect
            v-model:value="linkForm.mdm_project_code"
            placeholder="请选择主数据项目"
            :options="projects.map(p => ({ label: `[${p.project_id}] ${p.project_name}`, value: p.project_id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="GitLab 仓库">
          <NSelect
            v-model:value="linkForm.gitlab_project_id"
            placeholder="请选择未绑定的 GitLab 仓库"
            :options="unlinkedRepos.map(r => ({ label: `${r.name} (${r.path})`, value: r.id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="是否为受理仓">
          <NCheckbox v-model:checked="linkForm.is_lead">
            设定为该项目的线上工单受理中心 (Lead Repo)
          </NCheckbox>
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showLinkRepoModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="linking" @click="handleLinkRepo">确认关联</NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- 设定受理仓 Modal -->
    <NModal v-model:show="showSetLeadModal" preset="card" title="设定受理中心仓库" style="width: 400px;">
      <NForm label-placement="left" label-width="90">
        <NFormItem label="GitLab ID">
          <NInputNumber v-model:value="leadRepoForm.gitlab_project_id" placeholder="请输入 GitLab 仓库 ID" :min="1" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showSetLeadModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="settingLead" @click="handleSetLeadRepo">确认设定</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.project-mapping-admin {
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
.dim-text {
  color: var(--color-text-tertiary);
  font-size: 12px;
}
</style>
