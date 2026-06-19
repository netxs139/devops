<script setup lang="ts">
/**
5:  * @file ProductSelector.vue
6:  * @description 产品与部门选择聚合组件
7:  */
import { ref, onMounted, computed } from 'vue'
import { NSelect } from 'naive-ui'
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

const props = defineProps<{
  type: 'product' | 'org'
  id: string | null
}>()

const emit = defineEmits<{
  'update:type': [val: 'product' | 'org']
  'update:id': [val: string | null]
  'change': [payload: { type: 'product' | 'org'; id: string | null }]
}>()

const products = ref<Product[]>([])
const organizations = ref<Organization[]>([])
const loading = ref(false)

// 加载数据
async function fetchData() {
  loading.value = true
  try {
    const [prodData, orgData] = await Promise.all([
      http.get<Product[]>('/admin/products'),
      http.get<Organization[]>('/admin/organizations')
    ])
    products.value = prodData
    organizations.value = orgData
  } catch (error) {
    console.error('Failed to load selector data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})

// 计算 NSelect 选项
const selectOptions = computed(() => {
  if (props.type === 'product') {
    return products.value.map(p => ({
      label: p.product_name,
      value: p.product_id
    }))
  } else {
    return organizations.value.map(o => {
      const indent = o.org_level > 1 ? '\u00A0\u00A0'.repeat(o.org_level - 1) + '├─ ' : ''
      return {
        label: indent + o.org_name,
        value: o.org_id
      }
    })
  }
})

function handleTypeSwitch(newType: 'product' | 'org') {
  if (props.type !== newType) {
    emit('update:type', newType)
    emit('update:id', null)
    emit('change', { type: newType, id: null })
  }
}

function handleValueChange(newVal: string | null) {
  emit('update:id', newVal)
  emit('change', { type: props.type, id: newVal })
}
</script>

<template>
  <div class="selector-container">
    <div class="segmented-control">
      <div
        class="segment"
        :class="{ active: props.type === 'product' }"
        @click="handleTypeSwitch('product')"
      >
        产品
      </div>
      <div
        class="segment"
        :class="{ active: props.type === 'org' }"
        @click="handleTypeSwitch('org')"
      >
        部门
      </div>
    </div>
    <div class="divider"></div>
    <div class="select-wrapper">
      <NSelect
        :value="props.id"
        :options="selectOptions"
        :placeholder="props.type === 'product' ? '请选择业务产品...' : '请选择归属部门...'"
        clearable
        filterable
        :loading="loading"
        @update:value="handleValueChange"
      />
    </div>
  </div>
</template>

<style scoped>
.selector-container {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: 6px var(--space-4);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

.segmented-control {
  display: flex;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px;
  border-radius: var(--radius-md);
}

.segment {
  padding: 4px 12px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
}

.segment.active {
  background: #ffffff;
  color: var(--color-text-primary);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
}

.select-wrapper {
  width: 240px;
}
</style>
