# BI 度量中心底层数仓调研报告

通过对 `dbt_project/models` 目录下的核心 SQL 脚本进行深入调研，我发现目前数据团队已经在 dbt 数据集市 (`marts`) 层构建了极其完整、成熟的业务模型。

数据抽取的脏活累活、业务概念的关联、甚至前端展示层需要的一部分呈现逻辑，都已经在数据仓库内部被彻底解决。

## 1. 核心模型解析

### 💎 `rpt_dora_dashboard_summary` (DORA 大盘预聚合模型)

这是一个令前端与后端都非常开心的模型。它直接基于 `fct_dora_metrics_v2` 生成了**专门为前端大屏优化**的宽表：

- **时序环比与趋势**：自动利用 `lag()` 窗口函数计算了上个月的数值，并直接生成了趋势图标 (`deploy_trend_icon` 为 `↑`、`↓` 或 `→`)。
- **DORA 四大核心指标**：部署频率、MTTR（平均恢复时间）、前置时间、变更失败率，一应俱全。
- **效能评级计算**：基于 `lead_time_hours` 自动输出 DORA 官方定义的四个评级维度：`ELITE`, `HIGH`, `MEDIUM`, `LOW`。
- **UI 视觉映射**：甚至连 Apple 风格的语义十六进制颜色代码 (`health_color_hex` 如 `#34C759`, `#FF3B30`) 都已经在 SQL 层预先计算完成！

### 🧬 `fct_developer_activity_profile` (开发者 DNA 画像)

该模型（即我们关注的 ELOC 模块）基于每日明细 `dws_developer_metrics_daily` 进行汇总。

- **多维度度量**：聚合了总提交数、评审评论数、合并请求数、问题关闭数以及综合影响力得分 (`total_impact_score`)。
- **开发者原型 (Archetype) 判定**：通过 SQL 分支语句将开发者按贡献类型自动打标签，如：
  - `Review Master` (评审主导者)
  - `Code Machine` (无情打码机)
  - `Task Closer` (收割机)
  - `Generalist` (全干工程师)
- **研发日流速**：计算了 `daily_velocity`，并且排除了节假日，分子是得分，分母是真实的 `active_days_count`。

## 2. 调研结论与对架构的决定性影响

目前的数仓分层极度规范（`stg` -> `int` -> `dws` / `fct` -> `rpt`）。数据侧已经把所有脏活干完了。这直接影响我们对 `bi_metrics_module` 建设方案的决策：

> [!TIP]
> **绝对应该选择 方案 A (纯只读 ORM 直连架构)**。

**理由**：

1. **0 业务逻辑冗余**：因为 `rpt_dora_dashboard_summary` 甚至把前端的颜色代码都算好了，我们的 Python / FastAPI 后端如果在接口里再去写聚合逻辑，不仅是脱裤子放屁，更会造成两套指标口径打架。
1. **开发成本极低**：我们只需要在 `bi_metrics_module/models.py` 中建立针对这几个表的 `viewonly=True` SQLAlchemy ORM，并通过 FastAPI 原样暴露即可。
1. **架构极简**：不需要引入 Redis 缓存或者定时同步任务。dbt 运行完，前端直接刷新就能看到最新图表和状态。

### 后续落地建议

如果同意该结论，接下来的落地动作极其明确：

1. 创建 `bi_metrics_module` 目录结构。
1. 建立针对上述几个 `fct_` 和 `rpt_` 宽表的 SQLAlchemy 只读模型。
1. 建立 `bi_router.py` 对前端大屏暴露 API（提供必要的时间过滤和分页支持）。

______________________________________________________________________

## 3. Streamlit 现有 BI 大屏调研报告

`dashboard/` 目录下共有 **24 个 Streamlit 页面**，覆盖了极其完整的指标体系。以下是最有价值的页面盘点及其可借鉴的具体设计要素。

### 3.1 现有页面体系全景

| 编号 | 页面文件 | 所属指标域 | 数据来源 |
|---|---|---|---|
| 1 | `1_Gitprime.py` | ELOC 开发者价值贡献榜 | `commit_metrics` + `daily_dev_stats` |
| 2 | `2_DORA_Metrics.py` | DORA 四大指标 (v1) | `fct_dora_metrics` |
| 17 | `17_SPACE_Framework.py` | SPACE 多维生产力矩阵 | `dws_space_metrics_daily` |
| 19 | `19_Strategic_Executive_Cockpit.py` | 研发作战指挥中心 | 多个 `fct_*` 表联动 |
| 21 | `21_DORA_Refined.py` | DORA 2.0 精修大盘 | `fct_dora_metrics_v2` |
| 23 | `23_Radar_Intelligence.py` | 效能雷达 (混合数据源) | dbt 宽表 + FastAPI |

### 3.2 关键设计模式（可直接移植进 Vue 3）

**[A] 企业级简洁样式体系（已替换原有的毛玻璃）**

为了强调数据本身和符合后台管理系统的直觉，我们已决定废弃原有的 Glassmorphism 毛玻璃特效，采用标准的「企业级简洁样式」。
样式要求：摒弃多余的阴影和背景模糊，使用清晰的网格、充足的留白以及明确的色块，以最大化提升数据的可读性。

**[B] 指标评级的语义化颜色体系**

`2_DORA_Metrics.py` 中对 DORA 评级颜色有明确定义，直接对应 dbt `health_color_hex` 字段：

- `ELITE` → `#a855f7` (紫色)
- `HIGH` → `#38bdf8` (天蓝)
- `MEDIUM` → `#f59e0b` (橙色)
- `LOW` → `#ef4444` (红色)

**[C] 交付漏斗图（Plotly Funnel）**

`21_DORA_Refined.py` 中使用 Plotly `go.Funnel` 实现了「需求响应 → 代码开发 → 制品发布」三段式漏斗，且数据直接来自 `int_dora_issue_commit_lifecycle`（我们 dbt 层已存在的 intermediate 模型），Vue 3 中可使用 ECharts `funnelChart` 等价实现。

**[D] 雷达图（SPACE + 协同维度）**

两处雷达图设计：

- `17_SPACE_Framework.py`：5 维 SPACE 多边形雷达图
- `23_Radar_Intelligence.py`：研发协同雷达（流动效率、评审深度、非秒批率、响应时效、代码复杂度）

两者均使用 `go.Scatterpolar`，且**填充+配色逻辑**完全可以用 ECharts `radar` 图替代。

**[E] 双数据源混合架构（重要发现）**

`23_Radar_Intelligence.py` 揭示了一个关键的混合数据源架构：

- 大部分数据走 **dbt 宽表直连**（PostgreSQL ORM）
- 「下钻明细」和「ELOC 分布」则走 **FastAPI `/api/traceability/radar`** 端点
- 使用 `dashboard/common/api_client.py` 中的单例 `ApiClient` 完成后端通信

这说明 `bi_metrics_module` 的 FastAPI 接口**已经被 Streamlit 消费**，我们只需让 Vue 3 大屏调用同一套 `/api/bi/...` 接口即可复用。

### 3.3 对 Vue 3 移植的核心结论

| Streamlit 方式 | Vue 3 等效实现 |
|---|---|
| `st.cache_data(ttl=600)` | FastAPI Router 层的 `@alru_cache(ttl=60)` |
| `st.columns(4)` | Naive UI `NGrid` + 简洁风格 `MetricCard` 组件 |
| `px.line / px.bar / go.Scatterpolar` | ECharts `LineChart` / `BarChart` / `RadarChart` |
| `go.Funnel` | ECharts `FunnelChart` |
| `st.sidebar.selectbox` | Naive UI `NSelect` 放在 Filter Bar |
| `api_client.get('/api/...')` | 项目内置 `utils/request.ts` (Axios) + 原生 `setInterval` 轮询 |
| `@st.cache_resource` (DB Engine) | `bi_metrics_module` SQLAlchemy 只读连接池 |

> [!IMPORTANT]
> **关键启示**：`23_Radar_Intelligence.py` 已经证明了「FastAPI 作为 Streamlit 后端」这个架构的可行性。我们只需将 Streamlit 消费者换成 Vue 3，`bi_metrics_module` 的 FastAPI 接口基于 db 视图可极速搭建。

### 3.4 最新落地决策与 DDAP 规范 (BI Dashboard Norms)

基于上述调研以及后续的技术讨论，我们已将以下 4 条最佳实践确立为 DDAP 项目针对 BI 域及高频展现页面的强制规范：

1. **可见性感知轮询（智能暂停）**：必须结合 `Page Visibility API` (`document.hidden`)，当浏览器处于后台时自动暂停 `setInterval` 轮询，切回前台时立即同步并恢复，大幅节省网络和后端 DB 负载。
1. **防内存泄漏（生命周期销毁）**：在 Vue 3 的 `onBeforeUnmount` 阶段，必须显式调用 ECharts 的 `.dispose()` 清理实例；且必须使用 `ResizeObserver` 替代全局 `window.onresize` 监听。
1. **微型内存屏障（高并发防雪崩）**：由于采用 Thin Layer 直接暴露 db 宽表架构，FastAPI 路由层必须对只读接口应用短周期内存缓存（例如 TTL 60 秒），防止早高峰访问穿透打垮数据库。
1. **渐进式加载（Skeleton 骨架屏）**：严格禁止加载慢的宽表拖累全屏渲染（禁用全局 Blocking Loading）。各大屏指标卡或图表区需独立使用骨架屏组件（如 `<n-skeleton>`），实现无缝、渐进式的数据展示。
