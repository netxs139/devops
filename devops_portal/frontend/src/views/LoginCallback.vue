<script setup lang="ts">
/**
 * GitLab OAuth 回调处理组件
 * 后端重定向到 /login/callback?access_token=xxx
 * 本组件截获 query 参数，写入 Auth Store，然后跳转目标页
 */
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NSpin } from 'naive-ui'
import { useAuthStore } from '@/store/auth'
import { useNotificationStore } from '@/store/notification'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notifyStore = useNotificationStore()

onMounted(() => {
  const token = route.query.access_token as string | undefined
  if (token) {
    authStore.setToken(token)
    notifyStore.connect()
    const redirect = (route.query.redirect as string) ?? '/home'
    router.replace(redirect)
  } else {
    // Token 缺失，回到登录页
    router.replace('/login?error=oauth_failed')
  }
})
</script>

<template>
  <div style="display: flex; align-items: center; justify-content: center; height: 100vh;">
    <NSpin size="large" description="正在验证身份，请稍候..." />
  </div>
</template>
