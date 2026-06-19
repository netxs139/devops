<script setup lang="ts">
/**
 * @file Radar.vue
 * @description Traceability Radar ECharts 5 看板渲染组件
 */
import { computed } from 'vue'
import { NTable, NTag, NEmpty } from 'naive-ui'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import type { RadarResponse } from '@/types/api'

// 注册 ECharts 5 核心模块
use([
  CanvasRenderer,
  RadarChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const props = defineProps<{
  data: RadarResponse
}>()

// 1. 构建 ECharts 五维雷达配置
const radarOption = computed(() => {
  const vsm = props.data.vsm
  const col = props.data.collaboration

  // 5 个维度的数值计算
  const flowEfficiencyVal = vsm.flow_efficiency ?? 0.5
  const reviewDepthVal = col.effective_review_rate ?? 0.5
  const noRubberStampVal = Math.max(0, 1 - (col.rubber_stamp_rate ?? 0))
  const waitTimeSlaVal = Math.max(0, 1 - (vsm.avg_wait_minutes ?? 0) / 480) // 假设 8 小时为 SLA 极限
  const commitsQualityVal = 0.7 // 规划阶段占位符

  return {
    title: {
      text: '研发效能多维评估',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#111827'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: [
        { name: '流动效率 (Flow Eff)', max: 1 },
        { name: '评审深度 (Review Depth)', max: 1 },
        { name: '拒绝秒批 (No Rubber Stamp)', max: 1 },
        { name: '时效达成 (Wait SLA)', max: 1 },
        { name: '提交质量 (Commit Quality)', max: 1 }
      ],
      shape: 'circle',
      splitNumber: 5,
      axisName: {
        color: '#4b5563',
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.06)'
        }
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(249, 250, 251, 0.3)', 'rgba(243, 244, 246, 0.5)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.08)'
        }
      }
    },
    series: [
      {
        name: '研发效能得分',
        type: 'radar',
        data: [
          {
            value: [
              flowEfficiencyVal,
              reviewDepthVal,
              noRubberStampVal,
              waitTimeSlaVal,
              commitsQualityVal
            ],
            name: '综合评估得分'
          }
        ],
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#1A56DB' // 企业深蓝
        },
        lineStyle: {
          width: 2,
          color: '#1A56DB'
        },
        areaStyle: {
          color: 'rgba(26, 86, 219, 0.15)' // 浅蓝半透明填充
        }
      }
    ]
  }
})

// 2. 构建 ELOC 贡献者横向柱状图配置
const elocOption = computed(() => {
  const eloc = props.data.eloc

  return {
    title: {
      text: '贡献者有效代码行 (ELOC) 排名',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#111827'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        color: '#6b7280',
        fontSize: 10
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      }
    },
    yAxis: {
      type: 'category',
      data: eloc.labels.slice().reverse(), // 反转一下展示最高者在最上方
      axisLabel: {
        color: '#4b5563',
        fontSize: 10
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    },
    series: [
      {
        name: 'ELOC',
        type: 'bar',
        data: eloc.values.slice().reverse(),
        barWidth: '50%',
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: 'rgba(26, 86, 219, 0.6)' },
              { offset: 1, color: '#1A56DB' }
            ]
          },
          borderRadius: [0, 4, 4, 0]
        }
      }
    ]
  }
})
</script>

<template>
  <div class="radar-charts-wrapper">
    <!-- 图表层 -->
    <div class="charts-row">
      <div class="chart-container">
        <VChart class="echart-inst" :option="radarOption" autoresize />
      </div>
      <div class="chart-container">
        <VChart class="echart-inst" :option="elocOption" autoresize />
      </div>
    </div>

    <!-- 价值流 Timeline (最近 10 条已合并 MR) -->
    <div class="vsm-section">
      <div class="vsm-title">价值流周期明细 (最近 10 条合并请求)</div>

      <div v-if="props.data.vsm_timeline && props.data.vsm_timeline.length > 0" class="table-wrapper">
        <NTable :bordered="false" :single-line="false" size="small" class="vsm-table">
          <thead>
            <tr class="table-header">
              <th style="width: 80px;">MR ID</th>
              <th style="width: 280px;">标题 (Title)</th>
              <th>生命周期周期比 (Draft / Wait / Review)</th>
              <th style="width: 80px; text-align: center;">秒批率</th>
              <th style="width: 80px; text-align: center;">评论数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in props.data.vsm_timeline" :key="item.id">
              <td class="mr-id">{{ item.id }}</td>
              <td class="mr-title" :title="item.title">{{ item.title }}</td>
              <td>
                <div class="stacked-bar-container">
                  <!-- Draft 段 -->
                  <div
                    v-if="item.draft_minutes"
                    class="bar-segment draft"
                    :style="{ width: ((item.draft_minutes / (item.total_minutes || 1)) * 100) + '%' }"
                    :title="'草稿期: ' + Math.round(item.draft_minutes) + 'm'"
                  ></div>
                  <!-- Wait 段 -->
                  <div
                    v-if="item.wait_minutes"
                    class="bar-segment wait"
                    :style="{ width: ((item.wait_minutes / (item.total_minutes || 1)) * 100) + '%' }"
                    :title="'等待评审: ' + Math.round(item.wait_minutes) + 'm'"
                  ></div>
                  <!-- Review 段 -->
                  <div
                    v-if="item.review_minutes"
                    class="bar-segment review"
                    :style="{ width: ((item.review_minutes / (item.total_minutes || 1)) * 100) + '%' }"
                    :title="'有效评审期: ' + Math.round(item.review_minutes) + 'm'"
                  ></div>
                </div>
              </td>
              <td style="text-align: center;">
                <NTag
                  v-if="item.rubber_stamp"
                  type="warning"
                  size="small"
                  round
                  :bordered="false"
                >
                  秒批
                </NTag>
                <NTag
                  v-else
                  type="success"
                  size="small"
                  round
                  :bordered="false"
                >
                  规范
                </NTag>
              </td>
              <td class="comment-count">{{ item.effective_comments }}</td>
            </tr>
          </tbody>
        </NTable>
      </div>
      <div v-else class="empty-vsm">
        <NEmpty description="选定时间段内没有已合并的 MR 数据" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.radar-charts-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
}

.chart-container {
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: var(--space-4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.01);
  height: 350px;
}

.echart-inst {
  width: 100%;
  height: 100%;
}

.vsm-section {
  background: #ffffff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: var(--space-4);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.01);
}

.vsm-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.vsm-table {
  font-size: 13px;
}

.table-header th {
  color: var(--color-text-secondary) !important;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600 !important;
}

.mr-id {
  font-weight: 600;
  color: var(--color-primary);
  font-family: monospace;
}

.mr-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.comment-count {
  text-align: center;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Stacked Bar */
.stacked-bar-container {
  display: flex;
  height: 10px;
  width: 100%;
  border-radius: 5px;
  overflow: hidden;
  background: var(--color-bg-base);
  border: 1px solid var(--color-border);
}

.bar-segment {
  height: 100%;
  transition: width 0.3s ease;
}

.bar-segment.draft {
  background: var(--color-primary-light);
}

.bar-segment.wait {
  background: var(--color-warning);
}

.bar-segment.review {
  background: var(--color-primary);
}

.empty-vsm {
  padding: 40px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
