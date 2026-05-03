---
name: frontend-design
description: 创建独特的、生产级别的高质量前端界面。当用户要求构建网页组件、页面、作品、海报或应用程序时使用此技能（例如网站、落地页、仪表盘、React 组件、HTML/CSS 布局，或对任何网页 UI 进行样式美化）。生成富有创意、精致的代码和 UI 设计，避免千篇一律的 AI 审美。
license: 完整条款见 LICENSE.txt
---

本技能指导创建独特的、生产级别的前端界面，避免千篇一律的"AI 流水线"审美。实现真正可用的代码，对美学细节和创意选择给予极致关注。

用户提供前端需求：需要构建的组件、页面、应用程序或界面。他们可能会提供关于用途、目标受众或技术约束的背景信息。

---

## 🔴 Step 0：项目合规性预检 [MANDATORY — 编码前必须执行]

> 这是任何前端工作的第一步，不允许跳过。

### 0.0 宿主环境觉醒 (Host-Platform Awareness)

在编写任何 UI 代码前，**必须**首先判定目标宿主环境：

1.  **决策中心 (Decision Hub)**: 运行在 `dashboard/` 目录下，基于 **Streamlit**。
    *   **适用场景**：非高频、重分析、重度量、高管视角（如：效能雷达分析、趋势对比）。
    *   **技术栈**：Python, Streamlit API, Plotly, Altair, Pandas。
2.  **管理门户 (DevOps Portal)**: 运行在 `devops_portal/static/` 目录下，基于 **Vanilla JS**。
    *   **适用场景**：高频交互、低延迟、重流程、作业视角（如：用例执行、缺陷管理、数据修正）。
    *   **技术栈**：HTML5, Vanilla JS (Modules), CSS Variables, Web Components, Chart.js, D3.js。

**强制动作**：若任务描述模糊，**必须**先向用户确认目标宿主（遵循 `AGENTS.md` 中的“UI 集成决策锁”）。

### 0.1 仪表盘页面注册检查

如果本次任务涉及新增或修改 **`devops_portal/static/` 下的 Dashboard 页面**，必须：

1. 查阅 `contexts.md §6.5 Frontend Dashboard Map`，确认 Index 唯一性，**严禁 Index 冲突**。
2. 若为新页面，**必须先在该表中注册 Index + Page Module + Domain**，再编写任何 HTML。
3. 示例检查指令：`grep -n "traceability" contexts.md` — 确认未被已有条目占用。

### 0.2 项目 CSS 规范加载

读取项目设计规范文件（若存在）：
- `docs/frontend/CONVENTIONS.md` — 项目 CSS 变量体系与 Apple Style 规范
- `devops_portal/static/css/main.css` — 当前全局 CSS 变量定义

**强制约束**（来自 `contexts.md §6`）：
- **必须**优先使用已有 CSS 变量（如 `--glass-bg`, `--primary-color`），**严禁**在新文件中硬编码 Hex 颜色值。
- 若创建独立主题页面（如仪表盘子模块），新 CSS 文件中的色彩系统**必须**通过 `:root` 变量定义，不得散落在选择器内。

### 0.3 API 接口契约对齐

如果新页面需要调用后端 API（`fetch()`），则：
1. **先查阅或创建** 对应的 Pydantic `ResponseSchema`（位于 `devops_portal/schemas.py` 或独立 `schemas_*.py`）。
2. 前端 JS 中的字段名**必须**与 Python Schema 字段名**镜像对齐**（同名、同含义）。
3. 禁止在 JS 中用字面量硬编码 API 响应结构，必须有 Python 侧的 Schema 作为"物理契约"。

---

## 设计思维

在编码之前，理解上下文并确定一个**大胆**的美学方向：
- **目的**：这个界面解决什么问题？谁在使用它？
- **基调**：选择一个极端方向：极简主义、极繁主义混沌风、复古未来主义、有机自然风、奢华精致风、趣味玩具风、杂志编辑风、粗野主义原始风、装饰艺术几何风、柔和粉彩风、工业实用风等。
- **约束**：技术要求（框架、性能、可访问性）。
- **差异化**：什么让这个设计令人**难忘**？用户会记住的那一个亮点是什么？

**关键**：选择一个清晰的概念方向并精准执行。

然后实现可工作的代码（HTML/CSS/JS、React、Vue 等），需满足：
- 生产级别且功能完善
- 视觉冲击力强且令人难忘
- 具有清晰美学观点的整体协调性
- 每个细节都精雕细琢

---

## 前端美学指南

重点关注：
- **字体排版**：选择美观、独特、有趣的字体。避免使用 Arial 和 Inter 等通用字体；选择能提升前端美感的独特字体；出人意料的、有个性的字体选择。将独特的展示字体与精致的正文字体搭配。
- **色彩与主题**：坚持统一的美学风格。使用 CSS 变量保持一致性。主导色配合鲜明的强调色，效果优于胆怯的、平均分布的配色方案。
- **动效**：使用动画实现效果和微交互。HTML 优先使用纯 CSS 解决方案。聚焦高影响力时刻：一个精心编排的页面加载动画配合错落有致的渐显效果（animation-delay）比零散的微交互更令人愉悦。使用能带来惊喜的滚动触发和悬停状态。
- **空间构图**：出人意料的布局。不对称。重叠。对角线流动。打破网格的元素。大量留白或可控的密集感。
- **背景与视觉细节**：营造氛围和层次感，而非默认使用纯色。运用创意形式如渐变网格、噪点纹理、几何图案、叠加透明度、戏剧性阴影、装饰边框、颗粒覆盖层。

**绝不**使用千篇一律的 AI 生成审美，如过度使用的字体（Inter、Roboto、Arial）、陈词滥调的配色方案（尤其是白底紫色渐变）、可预测的布局和组件模式。

---

## 🔴 交付前检查清单 (Pre-Delivery Checklist) [MANDATORY]

### 合规性
- [ ] **Dashboard Map** 已查阅，Index 无冲突（或已完成注册）
- [ ] CSS 颜色全部通过变量定义，无硬编码 Hex 泄漏
- [ ] API 字段命名与 Python ResponseSchema **镜像对齐**

### 可视容器验证 (DOM Smoke Test)
- [ ] 所有图表容器（`canvas`、`svg`、`div`）在 CSS 中已明确设置高度（`height` 或 `min-height`）
- [ ] **Chart.js / SVG / Canvas 容器高度不为零**：若容器的 `height` 依赖父级 `flex`，必须在父级明确设置 `min-height`，或使用 `position: relative + min-height` 组合
- [ ] 用浏览器 DevTools 验证容器 `getBoundingClientRect().height > 0`，再提交代码

### 视觉质量
- [ ] 无 emoji 作为 UI 图标（使用 SVG 替代）
- [ ] 所有可点击元素有 `cursor: pointer`
- [ ] Hover 状态有清晰视觉反馈，过渡时长 150-300ms
- [ ] 响应式在 375px / 768px / 1440px 均正常

### 可访问性
- [ ] 所有图片有 `alt` 属性
- [ ] 色彩不是唯一的信息载体（辅以文字或图标）
- [ ] `prefers-reduced-motion` 已考虑（核心动画添加媒体查询降级）
