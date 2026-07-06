/**
 * @file main.ts
 * @description 应用入口：注册 Pinia、Router、全局指令、Naive UI
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { vPermission } from './directives/permission'
import { VueQueryPlugin } from '@tanstack/vue-query'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueQueryPlugin)


// 按钮级鉴权指令（全局注册）
app.directive('permission', vPermission)

app.mount('#app')
