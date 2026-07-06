<script setup lang="ts">
/**
 * @file IamKitIntegration.vue
 * @description 身份与权限管理模块联邦集成占位组件 (Mock of @company/iam-kit)
 * 真实的生产环境中，该组件将通过 Module Federation 或 Iframe 加载来自 identity_module 的 UI 资产。
 */
import { ref } from 'vue'
import { NCard, NResult, NButton, NSpin, NSpace } from 'naive-ui'

const loading = ref(true)

// 模拟加载联邦模块的延迟
setTimeout(() => {
  loading.value = false
}, 1000)

function handleReload() {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1000)
}
</script>

<template>
  <div class="iam-kit-container">
    <NCard :bordered="false" class="integration-card">
      <div v-if="loading" class="loading-state">
        <NSpin size="large" />
        <div class="loading-text">正在加载 @company/iam-kit 联邦模块...</div>
      </div>

      <NResult
        v-else
        status="success"
        title="身份管理组件已挂载"
        description="身份验证与组织架构管理能力已由 AMDP identity_module 全面接管"
      >
        <template #footer>
          <NSpace justify="center">
            <NButton type="primary" disabled>用户管理 (IAM)</NButton>
            <NButton type="info" disabled>组织架构管理 (IAM)</NButton>
            <NButton @click="handleReload">重新加载模块</NButton>
          </NSpace>
        </template>
        <div class="integration-details">
          <p>🔧 <b>集成方式:</b> Module Federation (微前端)</p>
          <p>📦 <b>依赖包:</b> <code>@company/iam-kit</code></p>
          <p>🛡️ <b>权限体系:</b> OIDC & RBAC 统一鉴权</p>
          <p>在此区域内，将完整渲染包括人员变动、组织架构树、跨系统外键映射在内的全部身份相关 UI。原有 DDAP 本地的 OrgUserAdmin 等代码已被移除。</p>
        </div>
      </NResult>
    </NCard>
  </div>
</template>

<style scoped>
.iam-kit-container {
  width: 100%;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.integration-card {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-base);
  border: 1px dashed var(--color-border-hover);
  border-radius: var(--radius-lg);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--color-text-secondary);
}

.integration-details {
  margin-top: 32px;
  padding: 16px;
  background: var(--color-bg-layout);
  border-radius: var(--radius-md);
  text-align: left;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.integration-details p {
  margin: 8px 0;
}
</style>
