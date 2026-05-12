---
name: ai-solve
description: Workflow for ai-solve
---

# Workflow: /ai-solve (测试驱动意图：自愈合编码流水线 v2.3)

> **触发条件**：当用户输入 `/ai-solve <测试文件路径/Schema名>`，或者人类写好了一个必定失败的单元测试/空 Schema 让你"把它跑通"时。
> **目标**：彻底免除自然语言沟通的歧义。AI 负责在受限的沙盒内不断执行"编写-测试-纠错"循环，直至测试点亮绿灯，并确保全局契约与文档同步。
>
> **[V2.3 新增]** 本版本将流水线扩展为双轨制，同时覆盖后端（Python/pytest）和前端（HTML/CSS/JS/API）开发场景。

______________________________________________________________________

## 🔍 任务类型判定（必须首先执行）

在进入任何阶段前，判断本次任务属于哪条轨道：

| 信号 | 轨道 |
|------|------|
| 涉及 `.py`、`models`、`router`、`service`、`worker` | **后端轨道 → 执行阶段 1B + 2B + 3B** |
| 涉及 `.html`、`.css`、`.js`、`static/`、`fetch()` | **前端轨道 → 执行阶段 1F + 2F + 3F** |
| 同时涉及前后端（如 API + JS 接入） | **全栈模式 → 先后端轨道，再前端轨道** |

______________________________________________________________________

## ⚙️ 后端轨道 (Backend Track)

### 阶段 1B：事前防呆与契约解析 (Pre-Flight)

1. **测试基座嗅探**：确认团队测试依赖风格（`pytest-mock` / `monkeypatch`），**严禁引入非标依赖**。
1. **方言与环境预警 (Dialect Awareness)**：
   - 若涉及数据库操作，检查是否有 `DateTime`、`JSON` 或聚合运算。
   - **预警**：SQLite vs PostgreSQL 差异（时区、函数），优先使用 `CAST`/`JULIANDAY` 跨平台方案。
1. **物理导包预检 (Import Integrity Check)**：
   - 在修改代码前，执行 `python -c "import <目标模块>"` 确保环境基座稳健。
1. **承诺声明**：AI 简短汇报已理解的契约与约束。

### 阶段 2B：闭环微循环 (Micro-Loop)

1. **物理探路导包 (Path-Sniffing)**：强制使用 `grep_search` 确认准确路径，严禁凭直觉导包。
1. **初次实现 (First Pass)**：编写最简 MVP 实现。
1. **执行验证**：`uv run pytest <测试文件路径> -v`
1. **自我纠偏**：分析 Traceback，优先排查"环境副作用"（数据库锁定、时区漂移、Mock 泄露）。
   - *熔断机制*：连续失败 **3 次** 后暂停并向人类汇报。
1. **绿灯放行**：测试通过（🟢）。

### 阶段 3B：工程严谨性对齐 (Engineering & Regression)

1. **物理导入二次验证**：`python -c "import <修改后的模块>"`，确保无循环引用。
1. **模块级防退化测试**：运行所在目录全量测试；若修改了 `mixins` 或 `Base`，强制执行 `just verify`。
1. **架构合规性扫描**：`python scripts/arch_auditor.py`，确保通过 ARCH-015 等卡点。
1. **SSOT/文档同步**：若涉及模型变更，执行 `just docs` + `just docs-verify`。

______________________________________________________________________

## 🎨 前端轨道 (Frontend Track) [V2.3 新增]

### 阶段 1F：前端预飞行检查 (Frontend Pre-Flight) [NEW]

1. **项目规范加载**（继承自 `frontend-design` SKILL Step 0）：

   - 查阅 `contexts.md §6.5 Frontend Dashboard Map`，确认 Index 不冲突或已注册。
   - 读取 `docs/frontend/CONVENTIONS.md` 获取 CSS 变量体系与 Apple Style 规范。

1. **API 契约对齐（前后端字段镜像）[NEW]**：

   - 若本次任务涉及 `fetch()` 调用，**必须先查阅或创建** 对应 Python `ResponseSchema`（位于 `devops_portal/schemas_*.py`）。
   - 提取 Schema 字段清单，作为 JS 侧的"字段合同"——**字段命名必须镜像对齐**，禁止在 JS 中自行约定字段名。
   - 执行 Pre-flight 导入：`python -c "from devops_portal.schemas_xxx import XxxResponse; print(list(XxxResponse.model_fields.keys()))"`

1. **容器尺寸预检（Canvas/SVG/图表）[NEW]**：

   - 若任务涉及图表渲染（Chart.js / SVG / Canvas），**必须在 CSS 中显式声明容器高度**（`height` 或 `min-height`）。
   - 规则：依赖父级 `flex: 1` 的容器，父级必须有 `min-height`；否则图表高度为 0 无法渲染。
   - ⚠️ **这是已知的"假绿灯"陷阱**——代码生成完毕不代表图表已渲染。

1. **前端"Red"信号定义 [NEW]**：
   前端没有 pytest，但必须在动手前明确"什么是成功"：

   - **HTTP 可达性**：`Invoke-WebRequest -Uri "http://localhost:8000/static/<页面>" | StatusCode` → 期望 200
   - **API 响应**：`Invoke-WebRequest -Uri "http://localhost:8000/<api路径>"` → 期望返回正确 JSON
   - **DOM 渲染**：图表容器 `getBoundingClientRect().height > 0`（浏览器 DevTools 验证）

### 阶段 2F：前端闭环微循环 (Frontend Micro-Loop) [NEW]

1. **实现 HTML/CSS/JS**（遵循 `frontend-design` SKILL 美学指南）。

1. **HTTP 可达性验证（第一层 Green）**：

   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/static/<页面>" -UseBasicParsing | Select-Object StatusCode
   ```

   若返回 404 → 检查静态文件路径与 FastAPI `StaticFiles` mount 配置。

1. **API 端点验证（第二层 Green）**：

   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/<api路径>" -UseBasicParsing | Select-Object StatusCode, Content
   ```

   若返回 422/500 → 检查 Pydantic Schema 与查询逻辑。

1. **自我纠偏**：

   - 图表不渲染 → 优先检查容器高度（`getComputedStyle(el).height`），而非逻辑 Bug。
   - *熔断机制*：连续失败 **3 次** 后暂停并向人类汇报。

1. **绿灯放行**：HTTP 200 + API 正常响应（🟢）。

### 阶段 3F：前端工程严谨性对齐 (Frontend Engineering) [NEW]

1. **Dashboard Map 注册核查**：确认新页面已在 `contexts.md §6.5` 注册 Index。
1. **CSS 变量合规扫描**：检查新 CSS 文件中无硬编码 Hex（可执行 `grep -n "#[0-9A-Fa-f]\{6\}" <css文件>`，确认所有颜色均为 CSS 变量引用）。
1. **JS-Python 字段镜像审计**：对照 ResponseSchema 字段清单，逐一验证 JS 侧引用的字段名无拼写偏差。
1. **交付检查清单**（来自 `frontend-design` SKILL Pre-Delivery Checklist）：所有条目必须 ✅。

______________________________________________________________________

## 📦 阶段 4：成果交付 (Delivery)

向用户输出结果报告，格式如下：

- **轨道**: 后端 / 前端 / 全栈
- **状态**: ✅ 全局绿灯通过
- **循环次数**: X 次（记录排障过程）
- **环境兼容性**（后端）: 已验证跨数据库方言 / 导入完整性。
- **可达性验证**（前端）: HTTP 200 / API 正常响应 / 容器高度非零。
- **契约对齐**（全栈）: JS 字段命名与 Python ResponseSchema 镜像一致。
- **文档同步**: 数据字典 / Dashboard Map / API Schema 已同步更新。

准备进入后续流程（如 `/merge` 或 `/session-handover`）。
