<script setup lang="ts">
/**
 * @file PlaceholderView.vue
 * @description 通用占位组件，用于尚未开发的模块。读取路由元数据展示名称与说明。
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NEmpty, NButton, NSpace } from 'naive-ui'

const route = useRoute()
const router = useRouter()

const moduleTitle = computed(() => route.meta?.title || '未知模块')
const moduleDomain = computed(() => route.meta?.domain || '通用域')
</script>

<template>
  <div class="placeholder-container">
    <div class="header-section">
      <h1 class="page-title">{{ moduleTitle }}</h1>
      <p class="page-subtitle">所属域：{{ moduleDomain }}</p>
    </div>

    <div class="empty-state">
      <NEmpty description="此模块正在建设中..." size="huge">
        <template #extra>
          <NSpace justify="center">
            <NButton type="primary" secondary @click="router.push('/')">
              返回首页大厅
            </NButton>
          </NSpace>
        </template>
      </NEmpty>
    </div>
  </div>
</template>

<style scoped>
.placeholder-container {
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.header-section {
  margin-bottom: var(--space-6);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.02);
}
</style>
