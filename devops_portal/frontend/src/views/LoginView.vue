<script setup lang="ts">
/**
 * @file LoginView.vue
 * @description 企业级登录页
 *
 * 支持两种登录方式：
 * 1. 密码登录 — POST /auth/login (application/x-www-form-urlencoded)
 * 2. GitLab OAuth — 跳转 /auth/gitlab/login
 *
 * 安全要求（等保三级）：
 * - 密码字段不可复制，使用 NInput type="password"
 * - 错误信息模糊化（不区分邮箱/密码哪个错误）
 */
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NText,
  NDivider,
  NAlert,
  type FormInst,
  type FormRules,
} from 'naive-ui'
// [CONTRACT EXEMPTION] 登录接口是 token 的来源，此时尚无 Bearer token 可注入。
// 直接使用 axios 绕过 request.ts 的 Authorization 拦截器是预期行为。
// 参见 frontend.md §5 注释：/auth/login 为合法豁免端点。
import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import { useNotificationStore } from '@/store/notification'
import type { AuthToken } from '@/types/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notifyStore = useNotificationStore()

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const errorMsg = ref<string | null>(
  route.query.error === 'oauth_failed' ? 'GitLab 授权失败，请重试或使用密码登录' : null,
)

const model = ref({ email: '', password: '' })

const rules: FormRules = {
  email: [
    { required: true, message: '请填写企业邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: ['blur', 'change'] },
  ],
  password: [
    { required: true, message: '请填写密码', trigger: 'blur' },
    { min: 6, message: '密码不能少于 6 位', trigger: 'blur' },
  ],
}

async function handleLogin(): Promise<void> {
  errorMsg.value = null
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    const body = new URLSearchParams({
      username: model.value.email,
      password: model.value.password,
    })
    const resp = await axios.post<AuthToken>('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    authStore.setToken(resp.data.access_token)
    notifyStore.connect()
    const redirect = (route.query.redirect as string | undefined) ?? '/home'
    router.replace(redirect)
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const detail = err.response?.data?.detail
      errorMsg.value = typeof detail === 'string' ? detail : '邮箱或密码不正确'
    } else {
      errorMsg.value = '网络连接异常，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

function handleGitLabOAuth(): void {
  window.location.href = '/auth/gitlab/login'
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 品牌标识 -->
      <div class="brand">
        <div class="brand-icon">D</div>
        <NText class="brand-name">DevOps Portal</NText>
        <NText depth="3" class="brand-desc">研发效能数据平台</NText>
      </div>

      <!-- 登录卡片 -->
      <NCard class="login-card" :bordered="false">
        <NForm
          ref="formRef"
          :model="model"
          :rules="rules"
          label-placement="top"
        >
          <NFormItem label="企业邮箱" path="email">
            <NInput
              v-model:value="model.email"
              type="text"
              placeholder="your@company.com"
              size="large"
              :input-props="{ autocomplete: 'email', type: 'email' }"
            />
          </NFormItem>

          <NFormItem label="密码" path="password">
            <NInput
              v-model:value="model.password"
              type="password"
              placeholder="请输入登录密码"
              size="large"
              show-password-on="click"
              :input-props="{ autocomplete: 'current-password' }"
              @keyup.enter="handleLogin"
            />
          </NFormItem>

          <!-- 错误提示 -->
          <NAlert
            v-if="errorMsg"
            type="error"
            :title="errorMsg"
            style="margin-bottom: 16px;"
            closable
            @close="errorMsg = null"
          />

          <NButton
            type="primary"
            size="large"
            block
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </NButton>
        </NForm>

        <NDivider>或</NDivider>

        <!-- GitLab OAuth 登录 -->
        <NButton
          secondary
          block
          size="large"
          class="gitlab-btn"
          @click="handleGitLabOAuth"
        >
          <template #icon>
            <svg
              width="18"
              height="18"
              viewBox="0 0 380 380"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M189.776 357.256L258.214 148.876H121.337L189.776 357.256Z"
                fill="#E24329"
              />
              <path
                d="M189.776 357.256L121.337 148.876H25.6548L189.776 357.256Z"
                fill="#FC6D26"
              />
              <path
                d="M25.655 148.876L3.48022 215.614C1.51748 221.696 3.7259 228.358 8.91575 232.013L189.776 357.256L25.655 148.876Z"
                fill="#FCA326"
              />
              <path
                d="M25.655 148.876H121.337L80.1756 23.2842C78.0434 16.7893 68.9491 16.7893 66.8169 23.2842L25.655 148.876Z"
                fill="#E24329"
              />
              <path
                d="M189.776 357.256L258.214 148.876H353.897L189.776 357.256Z"
                fill="#FC6D26"
              />
              <path
                d="M353.897 148.876L376.072 215.614C378.034 221.696 375.826 228.358 370.636 232.013L189.776 357.256L353.897 148.876Z"
                fill="#FCA326"
              />
              <path
                d="M353.897 148.876H258.214L299.376 23.2842C301.508 16.7893 310.602 16.7893 312.735 23.2842L353.897 148.876Z"
                fill="#E24329"
              />
            </svg>
          </template>
          通过 GitLab 账户登录
        </NButton>
      </NCard>

      <NText depth="3" class="footer-tip">
        © {{ new Date().getFullYear() }} 企业内部系统，请勿对外分享访问地址
      </NText>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-bg-base);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}

.login-container {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
}

/* 品牌区 */
.brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.brand-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-lg);
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-md);
}

.brand-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.3px;
}

.brand-desc {
  font-size: 13px;
}

/* 卡片 */
.login-card {
  width: 100%;
  box-shadow: var(--shadow-lg);
  border-radius: var(--radius-xl) !important;
}

/* GitLab 按钮 */
.gitlab-btn {
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.gitlab-btn:hover {
  border-color: #E24329;
}

/* 底部提示 */
.footer-tip {
  font-size: 12px;
  text-align: center;
}
</style>
