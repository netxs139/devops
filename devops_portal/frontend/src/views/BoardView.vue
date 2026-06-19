<script setup lang="ts">
/**
 * @file BoardView.vue
 * @description 迭代看板页（阶段四）
 * 组合：Sprint 信息栏 + Board（Drag/Drop 看板）+ Pulse（心情反馈）
 */
import { ref, computed } from 'vue'
import { NProgress } from 'naive-ui'
import Board from '@/components/Board.vue'
import Pulse from '@/components/Pulse.vue'

// ─── Mock Sprint 元数据 ───────────────────────────────────────────────────────
interface SprintMeta {
  name: string
  startDate: string
  endDate: string
  totalPoints: number
  donePoints: number
  goal: string
}

const sprint = ref<SprintMeta>({
  name:        'Sprint 2026-S4',
  startDate:   '2026-06-16',
  endDate:     '2026-06-30',
  totalPoints: 53,
  donePoints:  18,
  goal:        '完成 Vue 3 重构阶段三到五，确保 E2E 冒烟通过',
})

// ─── Sprint 进度 ──────────────────────────────────────────────────────────────
const progressPct = computed(() =>
  Math.round((sprint.value.donePoints / sprint.value.totalPoints) * 100)
)

// ─── 剩余天数 ─────────────────────────────────────────────────────────────────
const daysLeft = computed(() => {
  const end  = new Date(sprint.value.endDate)
  const now  = new Date()
  const diff = Math.ceil((end.getTime() - now.getTime()) / 86400000)
  return Math.max(0, diff)
})

// ─── 状态颜色 ─────────────────────────────────────────────────────────────────
const progressStatus = computed<'success' | 'warning' | 'error' | 'default'>(() => {
  if (progressPct.value >= 80) return 'success'
  if (progressPct.value >= 50) return 'warning'
  if (daysLeft.value <= 3)     return 'error'
  return 'default'
})
</script>

<template>
  <div class="board-view">
    <!-- ── Sprint 信息栏 ── -->
    <div class="sprint-bar">
      <div class="sprint-bar__left">
        <div class="sprint-name">{{ sprint.name }}</div>
        <div class="sprint-dates">{{ sprint.startDate }} → {{ sprint.endDate }}</div>
        <div class="sprint-goal" :title="sprint.goal">🎯 {{ sprint.goal }}</div>
      </div>

      <div class="sprint-bar__center">
        <div class="progress-label">
          <span>迭代进度</span>
          <span class="progress-value">{{ sprint.donePoints }} / {{ sprint.totalPoints }} SP</span>
        </div>
        <NProgress
          type="line"
          :percentage="progressPct"
          :status="progressStatus"
          :height="10"
          :border-radius="5"
          :fill-border-radius="5"
          indicator-placement="inside"
        />
      </div>

      <div class="sprint-bar__right">
        <div class="stat-block">
          <span class="stat-value">{{ progressPct }}%</span>
          <span class="stat-label">完成率</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-block">
          <span class="stat-value" :class="{ 'stat-value--urgent': daysLeft <= 3 }">
            {{ daysLeft }}
          </span>
          <span class="stat-label">剩余天数</span>
        </div>
        <div class="stat-divider" />
        <div class="stat-block">
          <span class="stat-value">{{ sprint.totalPoints - sprint.donePoints }}</span>
          <span class="stat-label">待完成 SP</span>
        </div>
      </div>
    </div>

    <!-- ── 主内容区：看板 + 心情面板 ── -->
    <div class="board-layout">
      <!-- 左主区：看板 -->
      <div class="board-main">
        <Board />
      </div>

      <!-- 右侧面板：Pulse -->
      <div class="board-sidebar">
        <Pulse />
      </div>
    </div>
  </div>
</template>

<style scoped>
.board-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  height: 100%;
}

/* ── Sprint 信息栏 ── */
.sprint-bar {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: var(--space-4) var(--space-5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.sprint-bar__left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 220px;
}

.sprint-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.sprint-dates {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-family: monospace;
}

.sprint-goal {
  font-size: 12px;
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 280px;
}

.sprint-bar__center {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.progress-value {
  color: var(--color-text-primary);
}

.sprint-bar__right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-shrink: 0;
}

.stat-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: 22px;
  font-weight: 800;
  color: var(--color-text-primary);
  line-height: 1;
}

.stat-value--urgent {
  color: #ef4444;
  animation: pulse-red 1.5s ease-in-out infinite;
}

.stat-label {
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background: var(--color-border);
}

/* ── 主内容布局 ── */
.board-layout {
  display: flex;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.board-main {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: var(--space-4);
}

.board-sidebar {
  width: 240px;
  flex-shrink: 0;
  overflow-y: auto;
}

/* ── 响应式 ── */
@media (max-width: 1280px) {
  .sprint-bar {
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .sprint-bar__center {
    min-width: 100%;
    order: 3;
  }

  .board-layout {
    flex-direction: column;
  }

  .board-sidebar {
    width: 100%;
  }
}

/* ── 动画（复用 Board.vue 的 pulse-red） ── */
@keyframes pulse-red {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.6; }
}
</style>
