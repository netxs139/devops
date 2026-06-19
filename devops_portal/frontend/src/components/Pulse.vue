<script setup lang="ts">
/**
 * @file Pulse.vue
 * @description 团队心情反馈组件 (Team Pulse)
 * 存储：localStorage（B2）
 * key 格式：pulse_<date>_<userId>
 */
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'

// ─── 类型 ─────────────────────────────────────────────────────────────────────
interface EmojiOption {
  emoji: string
  label: string
  key: string
  color: string
}

interface PulseEntry {
  userId: string
  emoji: string
  date: string
  ts: number
}

// ─── Emoji 选项 ───────────────────────────────────────────────────────────────
const EMOJI_OPTIONS: EmojiOption[] = [
  { emoji: '🚀', label: '冲鸭！',   key: 'rocket', color: '#1A56DB' },
  { emoji: '🔥', label: '燃！',     key: 'fire',   color: '#ef4444' },
  { emoji: '😊', label: '不错',     key: 'smile',  color: '#059669' },
  { emoji: '😐', label: '一般般',   key: 'meh',    color: '#D97706' },
  { emoji: '😔', label: '有点累',   key: 'tired',  color: '#6B7280' },
]

// ─── Auth Store ───────────────────────────────────────────────────────────────
const auth = useAuthStore()

// ─── 工具函数 ─────────────────────────────────────────────────────────────────
function todayStr(): string {
  return new Date().toISOString().slice(0, 10) // 'YYYY-MM-DD'
}

function lsKey(userId: string): string {
  return `pulse_${todayStr()}_${userId}`
}

// ─── Mock 历史（团队昨日心情分布，用于图表展示）────────────────────────────────
const MOCK_HISTORY: Record<string, number> = {
  rocket: 3,
  fire:   5,
  smile:  8,
  meh:    2,
  tired:  1,
}

// ─── 状态 ─────────────────────────────────────────────────────────────────────
const todayVote     = ref<string | null>(null)    // 当前用户今日选项
const animatingKey  = ref<string | null>(null)     // 触发弹跳动画的 key
const teamCounts    = ref<Record<string, number>>({ ...MOCK_HISTORY })

onMounted(() => {
  const userId = auth.currentUser?.username ?? 'anonymous'
  const stored = localStorage.getItem(lsKey(userId))
  if (stored) {
    todayVote.value = stored
    // 已投票则叠加到计数（避免重复计算，Mock 历史已含昨日数据）
  }
})

// ─── 投票逻辑 ─────────────────────────────────────────────────────────────────
function vote(key: string) {
  const userId = auth.currentUser?.username ?? 'anonymous'

  // 若已投过票，撤回旧票
  if (todayVote.value && todayVote.value !== key) {
    teamCounts.value[todayVote.value] = Math.max(0, (teamCounts.value[todayVote.value] ?? 0) - 1)
  }

  if (todayVote.value === key) {
    // 再次点击：撤回投票
    teamCounts.value[key] = Math.max(0, (teamCounts.value[key] ?? 0) - 1)
    todayVote.value = null
    localStorage.removeItem(lsKey(userId))
    return
  }

  // 新投票
  todayVote.value = key
  teamCounts.value[key] = (teamCounts.value[key] ?? 0) + 1

  // 持久化
  const entry: PulseEntry = { userId, emoji: key, date: todayStr(), ts: Date.now() }
  localStorage.setItem(lsKey(userId), entry.emoji)

  // 触发弹跳动画
  animatingKey.value = key
  setTimeout(() => { animatingKey.value = null }, 600)
}

// ─── 计算总票数（用于进度条） ─────────────────────────────────────────────────
const totalVotes = computed(() =>
  Object.values(teamCounts.value).reduce((s, v) => s + v, 0)
)

function pct(key: string): number {
  if (totalVotes.value === 0) return 0
  return Math.round(((teamCounts.value[key] ?? 0) / totalVotes.value) * 100)
}

// ─── 团队主情绪（最多票的 emoji） ────────────────────────────────────────────
const dominantEmoji = computed(() => {
  let maxKey = 'smile'
  let maxVal = 0
  for (const [k, v] of Object.entries(teamCounts.value)) {
    if (v > maxVal) { maxVal = v; maxKey = k }
  }
  return EMOJI_OPTIONS.find(o => o.key === maxKey)
})
</script>

<template>
  <div class="pulse-root">
    <!-- 标题 -->
    <div class="pulse-header">
      <span class="pulse-title">团队心情 · Pulse</span>
      <span v-if="dominantEmoji" class="pulse-dominant" :title="`团队主情绪：${dominantEmoji.label}`">
        {{ dominantEmoji.emoji }}
      </span>
    </div>

    <p class="pulse-hint">
      {{ todayVote ? '已记录今日心情，可再次点击撤回 👇' : '今天感觉怎么样？选一个吧 👇' }}
    </p>

    <!-- Emoji 选项 -->
    <div class="pulse-options">
      <button
        v-for="opt in EMOJI_OPTIONS"
        :key="opt.key"
        class="pulse-btn"
        :class="{
          'pulse-btn--selected': todayVote === opt.key,
          'pulse-btn--bounce':   animatingKey === opt.key,
        }"
        :style="todayVote === opt.key ? { '--pulse-color': opt.color } : {}"
        :aria-label="opt.label"
        :title="opt.label"
        @click="vote(opt.key)"
      >
        <span class="pulse-emoji">{{ opt.emoji }}</span>
        <span class="pulse-emoji-label">{{ opt.label }}</span>
      </button>
    </div>

    <!-- 分布条 -->
    <div class="pulse-dist">
      <div class="dist-title">今日团队分布（{{ totalVotes }} 票）</div>
      <div v-for="opt in EMOJI_OPTIONS" :key="opt.key" class="dist-row">
        <span class="dist-emoji">{{ opt.emoji }}</span>
        <div class="dist-bar-wrap">
          <div
            class="dist-bar"
            :style="{ width: pct(opt.key) + '%', background: opt.color }"
          />
        </div>
        <span class="dist-pct">{{ teamCounts[opt.key] ?? 0 }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pulse-root {
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: var(--space-4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

/* ── 标题 ── */
.pulse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-1);
}

.pulse-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.pulse-dominant {
  font-size: 22px;
  line-height: 1;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.15));
}

.pulse-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-3) 0;
}

/* ── Emoji 按钮 ── */
.pulse-options {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.pulse-btn {
  flex: 1;
  min-width: 52px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: var(--space-2) var(--space-1);
  border-radius: var(--radius-md);
  border: 2px solid var(--color-border);
  background: var(--color-bg-base);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, transform 0.15s;
}

.pulse-btn:hover {
  border-color: var(--color-primary-light);
  background: rgba(26, 86, 219, 0.04);
  transform: translateY(-2px);
}

.pulse-btn--selected {
  border-color: var(--pulse-color, var(--color-primary));
  background: color-mix(in srgb, var(--pulse-color, var(--color-primary)) 10%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--pulse-color, var(--color-primary)) 20%, transparent);
}

.pulse-btn--bounce .pulse-emoji {
  animation: emoji-bounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pulse-emoji {
  font-size: 24px;
  line-height: 1;
  display: block;
}

.pulse-emoji-label {
  font-size: 10px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

/* ── 分布条 ── */
.pulse-dist {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.dist-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-1);
}

.dist-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dist-emoji {
  font-size: 16px;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.dist-bar-wrap {
  flex: 1;
  height: 8px;
  background: var(--color-bg-base);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.dist-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.34, 1.1, 0.64, 1);
  min-width: 2px;
}

.dist-pct {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  width: 24px;
  text-align: right;
  flex-shrink: 0;
}

/* ── 弹跳动画 ── */
@keyframes emoji-bounce {
  0%   { transform: scale(1); }
  30%  { transform: scale(1.5) rotate(-10deg); }
  60%  { transform: scale(0.9) rotate(5deg); }
  100% { transform: scale(1); }
}
</style>
