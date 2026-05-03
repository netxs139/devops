# Workflow: /task-kickoff (任务入场与意图驱动切片)

> **触发条件**：收到用户的具体需求、缺陷报告或 `/task-kickoff <需求说明>` 指令时。
> **目标**：强迫 AI 和开发者在动手编码前，先定级、划定红线、设计测试意图，并分解为原子任务（Micro-Loop），彻底杜绝“盲人摸象”式的开发。

## Phase 1: 物理感知与防偏航 (Context Sniffing)

1. **宿主嗅探**: 读取 `.git` 状态，执行 `git status -s`。如有大量未提交代码，**必须警告**用户是否要 stash。
1. **知识装载**: 静默查阅 `progress.txt` 了解最近进度，并根据所涉及的模块，按需检索 `contexts.md` 中的领域规则。
1. **查阅 ADR**: 如果涉及到新组件或基础结构改变，必须查阅 `docs/adr/` 了解历史架构决策。

## Phase 2: 意图驱动定级与切片 (Intent-Driven Slicing) [TDD 2.0 UPGRADE]

根据 **TDD 2.0 哲学（意图驱动流水线）**，严禁使用“写 UI -> 写后端 -> 测试”的传统面条式切片。任务切片必须以“构建可验证的物理契约”为核心。

1. **确定定级 (L1-L4)**:

   - **L1 (微调)**: 纯文本/样式修改，无逻辑变更。
   - **L2 (常规)**: 单一模块的隔离增强。
   - **L3 (核心)**: 跨表、跨组件、改动基础 API。
   - **L4 (高危)**: 引入新依赖、重构、变更部署流水线。

1. **意图先导切片法 (TDD 2.0 Slicing Logic)**:
   所有 L2 及以上的任务，强制按以下模式划分子任务：

   - **切片 A: [建模与契约对齐]** (Schema-First)
     - 确定数据模型 (Pydantic/SQLAlchemy) 与接口输入输出。
   - **切片 B: [编写失败的意图测试]** (Red Test)
     - 编写一个必定失败的 `pytest` 用例，物理固化需求边界。
   - **切片 C: [触发 /ai-solve 闭环]** (Auto-Implementation)
     - 调用 AI 的自愈合编码流水线完成逻辑填充，直至绿灯。
   - **切片 D: [集成与防腐自检]** (Green & Refactor)
     - 运行 `just arch-audit` 和全量 Lint 门禁，确保未引发架构退化。

## Phase 3: 架构防腐与资源探测 (Architecture Guardrails)

如果任务被定级为 **L3/L4**，强制追加以下准入点：

1. **关联审查**: 该模块是否涉及 `contexts.md` 中的 `[MANDATORY]` 红线？如果有，需在提纲中加粗标注。
1. **专家干预**: 判断是否需要提前调用特定 Skill（如 `frontend-design` 技能）。

## Phase 4: 文档与对齐矩阵 (Document Sync Matrix)

根据最新定级，向用户输出预估所需的文档操作：

- L1/L2: 更新 `progress.txt`。
- L3/L4: 需要额外输出 ADR、更新 `DATA_DICTIONARY.md`。

______________________________________________________________________

## 完工签章与行动解锁

AI 将向用户输出以下卡片，等待放行信号：

```text
[Kickoff Complete] 
- Level: L{x} 
- Branch: {当前分支} 
- TDD Intent: 已明确 (需优先构建 XX 测试契约)
- Target Skill: {需要调用的 Skill}

> [!IMPORTANT]
> 意图驱动切片已就绪。是否同意按此契约执行？ (请回复“OK”以解除执行锁，进入 /ai-solve 流程)
```
