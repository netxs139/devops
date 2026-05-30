# 前端设计与组件化契约 (Frontend Design & Componentization)

> **定位**: 本文档是 `contexts.md` 的领域扩展，涵盖前端开发规范、UI 组件化、代码格式化及仪表盘的命名空间策略。当进行 `devops_portal/static/` 相关的变更时，必须严格遵守。

## 1. 核心设计指令 (Core Design Directive)

> 🎨 **最高行动指令**：所有前端样式与组件开发，必须严格遵循 `docs/frontend/CONVENTIONS.md`。任何与该文档冲突的 UI 实现均视为 Bug。

- **Apple Style 规范**: 强制使用预定义的 CSS 变量（如 `--glass-bg`, `--primary-color`），严禁硬编码 Hex 颜色值。
- **组件工程**: 优先使用 Web Components (Shadow DOM) 实现高内聚组件（如搜索框、卡片）。
- **通信机制**: 跨组件通信通过 `CustomEvent` 实现，严禁随意污染全局 `window` 命名空间。

## 2. 前端与文档格式化策略 (Frontend & Doc Formatting)

为保持环境纯净，本项目拒绝引入 Node.js/Prettier 体系，采用纯 Python 生态工具进行前端格式化：

- **HTML/Jinja2**: 强制使用 `djhtml` 进行缩进对齐（`--tabwidth 2`）。它能完美识别 Jinja2 标签且不破坏语义。
- **Markdown**: 强制使用 `mdformat` 统一文档风格。
- **JS/CSS**: 暂不引入重型工具。依赖 IDE 内置格式化及 AI 生成时的样式自律（Apple Style 规范）。
- **执行机制**: 上述工具已集成至 `pre-commit` 门禁，确保入库代码 100% 物理对齐。

## 3. 前端功能全景地图 (Frontend Dashboard Map) [MANDATORY PRE-CHECK]

任何涉及前端 `dashboard/pages` 的新增或修改任务，**必须首先**在该地图中确认索引位（Index）与业务域（Domain）的唯一性，严禁索引冲突。

| Index | Page Module | Domain | Key Indicators |
| :--- | :--- | :--- | :--- |
| **0** | **Quality_Monitor** | **底座/质量** | **同步成功率, 审计异常, 数据新鲜度** |
| 1 | Gitprime | 效能/代码 | 提交频率, 活跃开发人数, 影响度 |
| 2 | DORA_Metrics | 效能/标准 | 部署频率, MTTR, 变更为失效率 (V1) |
| 3 | Project_Health | 项目/全景 | 进度偏差, 资源饱和度, 里程碑风险 |
| 4 | Compliance_Audit | 安全/合规 | 密钥泄露, 仓库权限违规, 依赖漏洞 |
| 5 | ABI_Analysis | 技术/二进制 | 接口兼容性突破, 符号导出变化 |
| 6 | User_Profile | 人员/画像 | 技能雷达, 贡献分布, 异常加班预警 |
| 7 | Capitalization_Audit | 财经/资本化 | 研发/资本化投入比例, 工时对齐 |
| 8 | Shadow_IT | 治理/发现 | 未注册系统探测, 资产黑户统计 |
| 9 | Talent_Radar | 人员/储备 | 骨干流失风险, 关键路径依赖 (Bus Factor) |
| 10 | Metrics_Guard | 质量/拦截 | 指标 3-Sigma 离群值标记 |
| 11 | Unified_Activities | 研发/全踪 | 跨源动态流 (MR, Issue, Commit) |
| 12 | Work_Items | 协作/任务 | 迭代进度, 燃尽图, 前置周期时间 |
| 13 | Entity_Alignment | MDM/对齐 | 跨系统实体映射完整度 (MDM Bridge) |
| 14 | Delivery_Costs | 成本/FinOps | 单次交付成本, 资源账单分摊 |
| 15 | Metadata_Governance | 治理/标准 | 元数据覆盖率, 字典完整性 |
| 16 | Michael_Feathers_Code_Hotspots | 技术/重构 | 变更频率 vs 复杂度散点图 (Hotspots) |
| 17 | SPACE_Framework | 人员/体验 | 开发者满意度, 研发心流, 专注时长 |
| 18 | Value_Stream | 价值/过程 | 价值周转率, 瓶颈探测, 触点损耗 |
| 19 | Strategic_Executive_Cockpit | 决策/大屏 | 集团级核心指标聚合 (Executive Only) |
| 20 | Nexus_FinOps | 治理/资产 | 制品库存储分布, 僵尸包回收建议 |
| 21 | DORA_Refined | 效能/标准 | 变更前置时间 (分段), 部署频率 (V2) |
| 22 | Code_Traceability | 效能/溯源 | 单项 Issue->Commit->MR 血缘追踪 |
| 23 | Radar_Intelligence | 效能/聚合 | 流动效率, 协同质量, 安全态势雷达 |

**[强制开发规程]**:

1. **查表**: 开发前必须核查上表，确保 Index 不冲突。
2. **更新**: 若新增页面，必须同步在此表中“注册”占位。
3. **视觉**: 必须引用 `--glass-bg` 等 Apple Style 变量，保持视觉归一化。
