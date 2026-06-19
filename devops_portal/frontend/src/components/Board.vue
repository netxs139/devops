<script setup lang="ts">
/**
 * @file Board.vue
 * @description 迭代看板（HTML5 原生 Drag & Drop）
 * 数据源：Mock 静态数据（A2）
 * 列定义：待办 / 进行中 / 测试中 / 已完成
 */
import { ref, computed } from 'vue'
import { NTag, NTooltip, NBadge } from 'naive-ui'
import type { BoardColumn, BoardItem } from '@/types/api'

// ─── Mock 数据 ──────────────────────────────────────────────────────────────
const MOCK_ITEMS = ref<BoardItem[]>([
  { iid: 1,  title: '用户登录体系 Vue 3 SFC 迁移',      type: 'task',        state: 'closed',  assignee: 'wxy', priority: 'P0', column: 'done',        story_points: 5 },
  { iid: 2,  title: 'QA 质量域 TestCaseView 实现',      type: 'requirement', state: 'closed',  assignee: 'lmn', priority: 'P0', column: 'done',        story_points: 8 },
  { iid: 3,  title: 'RadarView 效能雷达下钻看板',        type: 'requirement', state: 'closed',  assignee: 'wxy', priority: 'P1', column: 'done',        story_points: 5 },
  { iid: 4,  title: '迭代看板 Board HTML5 Drag/Drop',   type: 'requirement', state: 'opened',  assignee: 'wxy', priority: 'P0', column: 'in_progress', story_points: 8 },
  { iid: 5,  title: 'Pulse 心情反馈组件',                type: 'task',        state: 'opened',  assignee: 'lmn', priority: 'P1', column: 'in_progress', story_points: 3 },
  { iid: 6,  title: '服务台 ServiceDeskView 实现',       type: 'requirement', state: 'opened',  assignee: 'zhl', priority: 'P1', column: 'todo',        story_points: 5 },
  { iid: 7,  title: 'AdminView 系统管理页面',             type: 'requirement', state: 'opened',  assignee: 'zhl', priority: 'P2', column: 'todo',        story_points: 3 },
  { iid: 8,  title: 'Playwright E2E 框架落地',           type: 'task',        state: 'opened',  assignee: 'lmn', priority: 'P1', column: 'todo',        story_points: 8 },
  { iid: 9,  title: 'Dashboard Map 23模块路由注册',       type: 'task',        state: 'opened',  assignee: 'wxy', priority: 'P2', column: 'todo',        story_points: 2 },
  { iid: 10, title: '登录 E2E 集成测试修复',              type: 'bug',         state: 'opened',  assignee: 'lmn', priority: 'P0', column: 'review',      story_points: 2 },
  { iid: 11, title: 'CSP 策略 nonce 化升级',             type: 'task',        state: 'opened',  assignee: 'zhl', priority: 'P2', column: 'review',      story_points: 3 },
])

// ─── 列定义 ──────────────────────────────────────────────────────────────────
interface ColumnDef {
  key: BoardColumn
  label: string
  wipLimit: number
  color: string
  iconClass: string
}

const COLUMNS: ColumnDef[] = [
  { key: 'todo',        label: '待办',   wipLimit: 99, color: '#6B7280', iconClass: 'col-icon--todo'     },
  { key: 'in_progress', label: '进行中', wipLimit: 3,  color: '#1A56DB', iconClass: 'col-icon--progress' },
  { key: 'review',      label: '测试中', wipLimit: 4,  color: '#D97706', iconClass: 'col-icon--review'   },
  { key: 'done',        label: '已完成', wipLimit: 99, color: '#059669', iconClass: 'col-icon--done'     },
]

// ─── 列数据 computed ──────────────────────────────────────────────────────────
const columnItems = computed<Record<BoardColumn, BoardItem[]>>(() => {
  const map: Record<BoardColumn, BoardItem[]> = {
    todo: [], in_progress: [], review: [], done: []
  }
  for (const item of MOCK_ITEMS.value) {
    map[item.column].push(item)
  }
  return map
})

// ─── 拖拽状态 ────────────────────────────────────────────────────────────────
const draggingIid   = ref<number | null>(null)
const dragOverCol   = ref<BoardColumn | null>(null)

function onDragStart(e: DragEvent, item: BoardItem) {
  draggingIid.value = item.iid
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(item.iid))
  }
}

function onDragOver(e: DragEvent, col: BoardColumn) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
  dragOverCol.value = col
}

function onDragLeave() {
  dragOverCol.value = null
}

function onDrop(e: DragEvent, targetCol: BoardColumn) {
  e.preventDefault()
  dragOverCol.value = null
  if (draggingIid.value === null) return
  const item = MOCK_ITEMS.value.find(i => i.iid === draggingIid.value)
  if (item && item.column !== targetCol) {
    item.column = targetCol
  }
  draggingIid.value = null
}

function onDragEnd() {
  draggingIid.value = null
  dragOverCol.value = null
}

// ─── WIP 超限检测 ─────────────────────────────────────────────────────────────
function isWipExceeded(col: ColumnDef): boolean {
  return col.wipLimit < 99 && columnItems.value[col.key].length > col.wipLimit
}

// ─── 优先级样式 ──────────────────────────────────────────────────────────────
const PRIORITY_TYPE_MAP: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
  P0: 'error', P1: 'warning', P2: 'info', P3: 'default'
}

// ─── 卡片类型 ────────────────────────────────────────────────────────────────
const TYPE_LABEL_MAP: Record<string, string> = {
  bug: '🐛', requirement: '📋', task: '⚙️'
}

// ─── Story Points 总计 ───────────────────────────────────────────────────────
function columnPoints(col: BoardColumn): number {
  return columnItems.value[col].reduce((s, i) => s + (i.story_points ?? 0), 0)
}
</script>

<template>
  <div class="board-root">
    <div
      v-for="col in COLUMNS"
      :key="col.key"
      class="board-column"
      :class="{
        'board-column--dragover': dragOverCol === col.key,
        'board-column--wip-exceeded': isWipExceeded(col),
      }"
      @dragover="onDragOver($event, col.key)"
      @dragleave="onDragLeave()"
      @drop="onDrop($event, col.key)"
    >
      <!-- 列标题 -->
      <div class="col-header">
        <div class="col-header__left">
          <span class="col-dot" :style="{ background: col.color }" />
          <span class="col-label">{{ col.label }}</span>
          <NBadge
            :value="columnItems[col.key].length"
            :type="isWipExceeded(col) ? 'error' : 'default'"
            class="col-badge"
          />
        </div>
        <div class="col-header__right">
          <NTooltip v-if="col.wipLimit < 99" placement="top">
            <template #trigger>
              <span class="wip-limit" :class="{ 'wip-limit--exceeded': isWipExceeded(col) }">
                WIP {{ col.wipLimit }}
              </span>
            </template>
            进行中卡片上限为 {{ col.wipLimit }}，超限时请优先处理。
          </NTooltip>
          <span class="col-points">{{ columnPoints(col.key) }} SP</span>
        </div>
      </div>

      <!-- 卡片列表 -->
      <div class="col-cards">
        <div
          v-for="item in columnItems[col.key]"
          :key="item.iid"
          class="board-card"
          :class="{
            'board-card--dragging': draggingIid === item.iid,
            [`board-card--${item.priority?.toLowerCase()}`]: !!item.priority,
          }"
          draggable="true"
          @dragstart="onDragStart($event, item)"
          @dragend="onDragEnd()"
        >
          <!-- 卡片顶部：类型 + 优先级 -->
          <div class="card-meta">
            <span class="card-type">{{ TYPE_LABEL_MAP[item.type] ?? '📌' }}</span>
            <NTag
              v-if="item.priority"
              size="tiny"
              :type="PRIORITY_TYPE_MAP[item.priority] ?? 'default'"
              :bordered="false"
              round
            >
              {{ item.priority }}
            </NTag>
          </div>

          <!-- 卡片标题 -->
          <div class="card-title">{{ item.title }}</div>

          <!-- 卡片底部：IID + Assignee + Story Points -->
          <div class="card-footer">
            <span class="card-iid">#{{ item.iid }}</span>
            <div class="card-footer__right">
              <NTooltip v-if="item.assignee" placement="top">
                <template #trigger>
                  <span class="card-avatar">{{ item.assignee.substring(0, 2).toUpperCase() }}</span>
                </template>
                {{ item.assignee }}
              </NTooltip>
              <span v-if="item.story_points" class="card-sp">{{ item.story_points }}SP</span>
            </div>
          </div>
        </div>

        <!-- 拖拽放置区占位 -->
        <div
          v-if="dragOverCol === col.key && draggingIid !== null"
          class="drop-placeholder"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── 看板根容器 ── */
.board-root {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  height: 100%;
  min-height: 500px;
}

/* ── 列 ── */
.board-column {
  background: var(--color-bg-base);
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: border-color 0.2s ease, background 0.2s ease;
  min-height: 400px;
}

.board-column--dragover {
  border-color: var(--color-primary);
  background: rgba(26, 86, 219, 0.04);
}

.board-column--wip-exceeded {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.02);
}

/* ── 列标题 ── */
.col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-2);
}

.col-header__left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.col-header__right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.col-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.col-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.col-badge {
  margin-left: 2px;
}

.wip-limit {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-bg-surface);
  padding: 1px 6px;
  border-radius: 10px;
  border: 1px solid var(--color-border);
  cursor: default;
}

.wip-limit--exceeded {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.08);
  animation: pulse-red 1.5s ease-in-out infinite;
}

.col-points {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

/* ── 卡片列表 ── */
.col-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex: 1;
}

/* ── 卡片 ── */
.board-card {
  background: #ffffff;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  padding: var(--space-3);
  cursor: grab;
  transition: box-shadow 0.2s ease, transform 0.15s ease, opacity 0.2s ease;
  user-select: none;
  position: relative;
}

.board-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.board-card:active {
  cursor: grabbing;
}

.board-card--dragging {
  opacity: 0.4;
  transform: rotate(2deg) scale(0.97);
  box-shadow: 0 8px 24px rgba(26, 86, 219, 0.2);
}

/* 优先级左侧彩条 */
.board-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: transparent;
}
.board-card--p0::before { background: #ef4444; }
.board-card--p1::before { background: #f59e0b; }
.board-card--p2::before { background: #3b82f6; }
.board-card--p3::before { background: #9ca3af; }

/* ── 卡片内容 ── */
.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.card-type {
  font-size: 14px;
  line-height: 1;
}

.card-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  line-height: 1.45;
  margin-bottom: 8px;
  word-break: break-word;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-footer__right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-iid {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-family: monospace;
}

.card-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1A56DB 0%, #5850EC 100%);
  color: #ffffff;
  font-size: 9px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
}

.card-sp {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  background: var(--color-bg-base);
  padding: 1px 5px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

/* ── 放置占位 ── */
.drop-placeholder {
  height: 72px;
  border-radius: var(--radius-md);
  border: 2px dashed var(--color-primary);
  background: rgba(26, 86, 219, 0.05);
  animation: fade-in 0.15s ease;
}

/* ── 动画 ── */
@keyframes pulse-red {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.6; }
}

@keyframes fade-in {
  from { opacity: 0; transform: scaleY(0.8); }
  to   { opacity: 1; transform: scaleY(1); }
}

/* ── 响应式 ── */
@media (max-width: 1280px) {
  .board-root {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .board-root {
    grid-template-columns: 1fr;
  }
}
</style>
