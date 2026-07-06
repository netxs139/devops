<script setup lang="ts">
/**
 * @file AdminView.vue
 * @description 系统管理主页 (Coordination Hub)
 */
import { ref } from 'vue'
import { NTabs, NTabPane, NCard } from 'naive-ui'
import IamKitIntegration from '@/components/IamKitIntegration.vue'
import ProjectMappingAdmin from '@/components/ProjectMappingAdmin.vue'
import ProductAdmin from '@/components/ProductAdmin.vue'
import AuditLogAdmin from '@/components/AuditLogAdmin.vue'

const activeTab = ref<'iam' | 'project' | 'product' | 'audit'>('iam')
</script>

<template>
  <div class="admin-container">
    <!-- 页面头部 -->
    <div class="header-section">
      <h1 class="page-title">系统管理与平台治理 (Administration)</h1>
      <p class="page-subtitle">管理组织架构、项目/仓库多维映射、外部账号身份对齐及系统安全审计日志。</p>
    </div>

    <!-- 主卡片及 Tab 控制 -->
    <NCard class="admin-main-card" :bordered="false">
      <NTabs v-model:value="activeTab" type="card" class="admin-tabs">
        <NTabPane name="iam" tab="🏢 身份与用户管理 (IAM)">
          <IamKitIntegration />
        </NTabPane>
        <NTabPane name="project" tab="🗺️ 项目与仓库绑定">
          <ProjectMappingAdmin />
        </NTabPane>
        <NTabPane name="product" tab="📦 产品与关联矩阵">
          <ProductAdmin />
        </NTabPane>
        <NTabPane name="audit" tab="🔒 安全审计与指标">
          <AuditLogAdmin />
        </NTabPane>
      </NTabs>
    </NCard>
  </div>
</template>

<style scoped>
.admin-container {
  max-width: 1440px;
  margin: 0 auto;
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

.admin-main-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-bg-card);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.02);
  padding: var(--space-2);
}

.admin-tabs :deep(.n-tabs-tab-pad) {
  width: 16px;
}
</style>
