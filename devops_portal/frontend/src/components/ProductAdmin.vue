<script setup lang="ts">
/**
 * @file ProductAdmin.vue
 * @description 产品及产品-项目关联矩阵组件，支持 CSV 导入/导出
 */
import { ref, onMounted } from 'vue'
import {
  NCard,
  NTabs,
  NTabPane,
  NTable,
  NSpace,
  NButton,
  NTag,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  useMessage
} from 'naive-ui'
import { http } from '@/utils/request'
import type { ProductView, MDMProject, ImportSummary } from '@/types/api'

interface BriefUser {
  user_id: string
  full_name: string
  email: string
}

const message = useMessage()
const loadingProducts = ref(false)
const products = ref<ProductView[]>([])
const projects = ref<MDMProject[]>([])
const users = ref<BriefUser[]>([])

// 创建产品 Modal
const showAddProductModal = ref(false)
const submittingProduct = ref(false)
const productForm = ref({
  product_id: '',
  product_name: '',
  product_description: '',
  category: 'App',
  product_manager_id: null as string | null
})

// 关联产品到项目 Modal
const showLinkProductModal = ref(false)
const linking = ref(false)
const linkForm = ref({
  project_id: '',
  product_id: '',
  relation_type: 'PRIMARY',
  allocation_ratio: 1.0
})

// file inputs
const prodFileInput = ref<HTMLInputElement | null>(null)
const matrixFileInput = ref<HTMLInputElement | null>(null)

// 加载产品
async function loadProducts() {
  loadingProducts.value = true
  try {
    const data = await http.get<ProductView[]>('/admin/products')
    products.value = data
  } catch (err: unknown) {
    message.error('加载产品列表失败: ' + (err as Error).message)
  } finally {
    loadingProducts.value = false
  }
}

// 加载项目（用于映射关联）
async function loadProjects() {
  try {
    const data = await http.get<MDMProject[]>('/admin/mdm-projects')
    projects.value = data
  } catch (err: unknown) {
    console.error('加载主项目失败', err)
  }
}

// 加载用户（用于产品经理选择）
async function loadUsers() {
  try {
    const data = await http.get<BriefUser[]>('/admin/users')
    users.value = data
  } catch (err: unknown) {
    console.error('加载用户失败', err)
  }
}

// 创建产品
async function handleCreateProduct() {
  if (!productForm.value.product_id.trim() || !productForm.value.product_name.trim()) {
    message.warning('请填写产品代码与名称')
    return
  }
  submittingProduct.value = true
  try {
    await http.post('/admin/products', {
      product_id: productForm.value.product_id.trim(),
      product_name: productForm.value.product_name.trim(),
      product_description: productForm.value.product_description.trim(),
      category: productForm.value.category,
      product_manager_id: productForm.value.product_manager_id || null
    })
    message.success('产品创建成功')
    showAddProductModal.value = false
    productForm.value.product_id = ''
    productForm.value.product_name = ''
    productForm.value.product_description = ''
    loadProducts()
  } catch (err: unknown) {
    message.error('创建产品失败: ' + (err as Error).message)
  } finally {
    submittingProduct.value = false
  }
}

// 关联产品到项目
async function handleLinkProduct() {
  if (!linkForm.value.project_id || !linkForm.value.product_id) {
    message.warning('请选择项目与产品')
    return
  }
  linking.value = true
  try {
    await http.post('/admin/link-product', {
      project_id: linkForm.value.project_id,
      product_id: linkForm.value.product_id,
      relation_type: linkForm.value.relation_type,
      allocation_ratio: linkForm.value.allocation_ratio
    })
    message.success('产品-项目关联关系建立成功')
    showLinkProductModal.value = false
    loadProjects() // 刷新项目中的关联产品
  } catch (err: unknown) {
    message.error('关联失败: ' + (err as Error).message)
  } finally {
    linking.value = false
  }
}

// 导出 CSV
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

// 导入 CSV
async function handleImportFile(event: Event, endpoint: string) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

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
    loadProducts()
    loadProjects()
  } catch (err: unknown) {
    message.error('导入失败: ' + (err as Error).message)
  } finally {
    target.value = ''
  }
}

onMounted(() => {
  loadProducts()
  loadProjects()
  loadUsers()
})
</script>

<template>
  <div class="product-admin">
    <NCard :bordered="false" size="small">
      <NTabs type="line" animated>
        <!-- 产品管理 -->
        <NTabPane name="products" tab="📦 产品线配置 (Products)">
          <div class="tab-header">
            <NSpace>
              <NButton type="primary" size="small" @click="showAddProductModal = true">
                新建产品
              </NButton>
              <NButton size="small" @click="prodFileInput?.click()">
                导入产品 CSV
              </NButton>
              <NButton size="small" secondary type="info" @click="handleExport('/admin/export/products', 'products_export.csv')">
                导出产品 CSV
              </NButton>
            </NSpace>
            <input ref="prodFileInput" type="file" accept=".csv" style="display: none;" @change="handleImportFile($event, '/admin/import/products')" />
          </div>

          <NTable :single-line="false" size="small" class="admin-table">
            <thead>
              <tr>
                <th>产品代码 (ID)</th>
                <th>产品名称</th>
                <th>分类</th>
                <th>生命周期状态</th>
                <th>描述</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in products" :key="p.product_id">
                <td class="monospace-small weight-medium">{{ p.product_id }}</td>
                <td class="weight-medium">{{ p.product_name }}</td>
                <td><NTag size="small" :bordered="false" type="info">{{ p.category || '通用' }}</NTag></td>
                <td>
                  <NTag size="small" :bordered="false" :type="p.lifecycle_status === 'active' ? 'success' : 'warning'">
                    {{ p.lifecycle_status === 'active' ? '在线' : '维护中' }}
                  </NTag>
                </td>
                <td class="desc-col">{{ p.product_description || '-' }}</td>
              </tr>
              <tr v-if="products.length === 0 && !loadingProducts">
                <td colspan="5" class="empty-cell">🔍 暂无产品主数据信息</td>
              </tr>
            </tbody>
          </NTable>
        </NTabPane>

        <!-- 产品-项目关联矩阵 -->
        <NTabPane name="matrix" tab="🔗 产品-项目映射矩阵 (Mappings)">
          <div class="tab-header">
            <NSpace>
              <NButton type="primary" size="small" @click="showLinkProductModal = true">
                建立产品-项目关联
              </NButton>
              <NButton size="small" @click="matrixFileInput?.click()">
                导入关联矩阵 CSV
              </NButton>
              <NButton size="small" secondary type="info" @click="handleExport('/admin/export/product-mappings', 'product_mappings_export.csv')">
                导出关联矩阵 CSV
              </NButton>
            </NSpace>
            <input ref="matrixFileInput" type="file" accept=".csv" style="display: none;" @change="handleImportFile($event, '/admin/import/product-mappings')" />
          </div>

          <NTable :single-line="false" size="small" class="admin-table">
            <thead>
              <tr>
                <th>业务主项目代码</th>
                <th>业务主项目名称</th>
                <th>关联产品代码</th>
                <th>关联产品名称</th>
                <th>关联类型 (Relation)</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="prj in projects" :key="prj.project_id">
                <tr v-for="(prod, idx) in prj.products" :key="prod.product_id">
                  <td v-if="idx === 0" :rowspan="prj.products.length" class="monospace-small">{{ prj.project_id }}</td>
                  <td v-if="idx === 0" :rowspan="prj.products.length" class="weight-medium">{{ prj.project_name }}</td>
                  <td class="monospace-small">{{ prod.product_id }}</td>
                  <td class="weight-medium">{{ prod.product_name }}</td>
                  <td>
                    <NTag size="small" :bordered="false" :type="prod.relation_type === 'PRIMARY' ? 'success' : 'default'">
                      {{ prod.relation_type }}
                    </NTag>
                  </td>
                </tr>
              </template>
              <tr v-if="projects.length === 0">
                <td colspan="5" class="empty-cell">🔍 暂无关联矩阵数据</td>
              </tr>
            </tbody>
          </NTable>
        </NTabPane>
      </NTabs>
    </NCard>

    <!-- 新建产品 Modal -->
    <NModal v-model:show="showAddProductModal" preset="card" title="新建产品主数据" style="width: 500px;">
      <NForm :model="productForm" label-placement="left" label-width="90">
        <NFormItem label="产品代码">
          <NInput v-model:value="productForm.product_id" placeholder="如 PROD_CRM" />
        </NFormItem>
        <NFormItem label="产品名称">
          <NInput v-model:value="productForm.product_name" placeholder="如 客户关系管理系统" />
        </NFormItem>
        <NFormItem label="分类">
          <NInput v-model:value="productForm.category" placeholder="如 System / App / Component" />
        </NFormItem>
        <NFormItem label="产品经理">
          <NSelect
            v-model:value="productForm.product_manager_id"
            placeholder="选择产品负责人"
            :options="users.map(u => ({ label: `${u.full_name} (${u.email})`, value: u.user_id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="描述说明">
          <NInput v-model:value="productForm.product_description" type="textarea" placeholder="填写产品背景及使用说明..." />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showAddProductModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="submittingProduct" @click="handleCreateProduct">确认创建</NButton>
        </NSpace>
      </template>
    </NModal>

    <!-- 关联产品到项目 Modal -->
    <NModal v-model:show="showLinkProductModal" preset="card" title="建立产品与项目关联" style="width: 500px;">
      <NForm :model="linkForm" label-placement="left" label-width="100">
        <NFormItem label="业务主项目">
          <NSelect
            v-model:value="linkForm.project_id"
            placeholder="请选择主项目"
            :options="projects.map(p => ({ label: `[${p.project_id}] ${p.project_name}`, value: p.project_id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="关联产品">
          <NSelect
            v-model:value="linkForm.product_id"
            placeholder="请选择产品"
            :options="products.map(p => ({ label: `[${p.product_id}] ${p.product_name}`, value: p.product_id }))"
            filterable
          />
        </NFormItem>
        <NFormItem label="关联角色">
          <NSelect
            v-model:value="linkForm.relation_type"
            :options="[
              { label: '首要支持系统 (PRIMARY)', value: 'PRIMARY' },
              { label: '辅助集成系统 (SECONDARY)', value: 'SECONDARY' }
            ]"
          />
        </NFormItem>
        <NFormItem label="分摊系数">
          <NInputNumber v-model:value="linkForm.allocation_ratio" :min="0.1" :max="1.0" :step="0.1" />
        </NFormItem>
      </NForm>
      <template #footer>
        <NSpace justify="end">
          <NButton size="small" @click="showLinkProductModal = false">取消</NButton>
          <NButton size="small" type="primary" :loading="linking" @click="handleLinkProduct">确认关联</NButton>
        </NSpace>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.product-admin {
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
.monospace-small {
  font-family: var(--font-mono, monospace);
  font-size: 12px;
  color: var(--color-text-secondary);
}
.weight-medium {
  font-weight: 500;
}
.desc-col {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty-cell {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--color-text-tertiary);
}
</style>
