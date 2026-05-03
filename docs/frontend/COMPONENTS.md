# DevOps Platform 前端组件规范 (UI Components Contract)

> **SSOT (Single Source of Truth)**: 本文档定义了 `devops_portal/static/js/components/` 下核心 Web Components 的行为契约，包括输入属性 (Attributes)、数据属性 (Properties) 以及外发事件 (Events)。

______________________________________________________________________

## 1. 基础架构原则

- **Encapsulation**: 采用 Shadow DOM 隔离样式。
- **Communication**:
  - **Downwards**: 通过 `Attributes` 或 `data` 属性注入数据。
  - **Upwards**: 通过 `CustomEvent` (bubbles: true, composed: true) 冒泡通知父级。
- **Styling**: 继承全局 `main.css` 定义的 Design Tokens。

______________________________________________________________________

## 2. 核心组件目录

### 2.1 `adm-product-selector` (产品/部门切换器)

- **选择器**: `<adm-product-selector>`
- **输入属性**:
  - `selected-type`: `'product'` | `'org'`
  - `selected-id`: 选中项的物理 ID
- **外发事件**:
  - `change`: 当切换类型或选择项变化时触发。
    - `detail`: `{ type: string, id: string }`

### 2.2 `qa-test-case-card` (测试用例行)

- **选择器**: `<qa-test-case-card>`
- **数据属性**:
  - `data`: 传入完整的测试用例对象。
- **视觉反馈**:
  - `[active]`: 属性存在时显示选中高亮状态。
- **外发事件**:
  - `select-case`: 点击整行时触发。
    - `detail`: `{ item: Object }` (原始测试用例数据)

### 2.3 `qa-test-case-detail` (测试用例详情面板)

- **选择器**: `<qa-test-case-detail>`
- **数据属性**:
  - `data`: 传入测试用例详情。
- **外发事件**:
  - `execute`: 点击执行按钮时触发。
    - `detail`: `{ iid: number, result: string, report: string }`
  - `report-bug`: 点击提单按钮时触发。
    - `detail`: `{ iid: number }`

### 2.4 `sys-pulse` (系统监控波形图)

- **选择器**: `<sys-pulse>`
- **输入属性**:
  - `type`: 监控类型 (cpu, memory, disk)
  - `color`: 曲线颜色
- **数据注入**:
  - `pushData(value)`: 实例方法，用于推入实时监测值。

### 2.5 `qa-radar-drawer` (效能详情抽屉) [NEW]

- **选择器**: `<qa-radar-drawer>`
- **数据属性**:
  - `data`: 传入列表数据 `list[RadarDetailItem]`。
- **输入属性**:
  - `title`: 抽屉标题 (如 "秒批 MR 详情")。
  - `opened`: 布尔值，控制抽屉开关。
- **外发事件**:
  - `close`: 点击遮罩或关闭按钮时触发。

______________________________________________________________________

## 3. 开发规范 (Development Laws)

1. **事件解耦**: 禁止在组件内部直接修改全局 `state` 或调用 `Api`（除非是像 `adm-product-selector` 这种需要自取数据的全局组件）。
1. **属性映射**: `attributeChangedCallback` 必须能实时反映 `_state` 的变化。
1. **命名空间**: 事件名称应使用 kebab-case (如 `select-case`)，避免与原生事件冲突。
1. **影子穿透**: 组件内部样式应尽量使用 CSS Variables 以支持主题切换。
