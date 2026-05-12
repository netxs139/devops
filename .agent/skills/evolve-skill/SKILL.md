---
name: evolve-skill
description: Workflow for evolve-skill
---

# Workflow: /evolve-skill (技能进化与教训沉淀)

---
description: 技能演进工作流 —— 将 Lessons Learned 转化为自动化审计能力。
---

# 技能演进协议 (Skill Evolution Protocol)

> **触发指令**：`/evolve-skill [Lesson_ID]`
> **核心目标**：实现“教训 -> 失败用例 -> 技能指令更新 -> 闭环验证”的自进化闭环。

---

## Phase 1: 知识提取 (Knowledge Distillation)

Agent 必须定位 `docs/history/lessons-learned.log` 中的特定条目并完成以下分析：
1. **模式提取**：该问题是否具有“特征代码”？（如：特定 SQL 函数、特定 Pydantic 配置）。
2. **影响域判定**：该教训应归属于哪个专家 Skill？
   - dbt/SQL 问题 ➔ `dbt-pipeline-auditor`
   - ORM/建模问题 ➔ `mdm-integrity-arbiter`
   - 韧性/崩溃问题 ➔ `chaos-sentinel`

## Phase 2: 构造“毒素资产” (Toxic Asset Synthesis)

为了验证进化效果，Agent 必须构造一个包含该故障的“毒素文件”：
1. **创建临时文件**：在 `/tmp/evolve/[Skill]/` 目录下创建一个典型的“错误示范”文件。
2. **示例**：如果教训是“JSONB 引号陷阱”，则创建一个包含 `(raw->>'f')::boolean` 的 SQL 文件。

## Phase 3: 注入评估集 (Eval Ingestion)

1. **读取 Skill Evals**：打开目标 Skill 的 `evals/evals.json`。
2. **新增用例**：向数组中插入一个新的评估用例，明确指出：`"input": "/tmp/evolve/..."`, `"expected_focus": "捕获该特定的 [教训描述] 风险"`。

## Phase 4: 技能指令突变 (Instruction Mutation) [CORE]

1. **修改 SKILL.md**：打开对应 Skill 的指令主文件。
2. **注入防御逻辑**：在 `## 审计清单` 或 `## 执行规程` 中增加一条精准的防御规则。
3. **格式要求**：使用 `[Ref LL#{ID}]` 标记来源，以便后续追溯。
   - *示例*: `- [ ] [Ref LL#69] 强制检查 JSONB 提取是否包含 nullif+trim 组合，防止物理引号地雷。`

## Phase 5: 进化闭环验证 (Certification)

1. **运行评估**：执行 `just eval [Skill_Name]`。
2. **通过标准**：
   - [ ] Agent 在处理 Phase 2 构造的“毒素文件”时，**必须**显式指出并给出了 Phase 4 中定义的防御方案。
   - [ ] 评估分值应显著提升或保持满分。

## Phase 6: 状态落盘 (Persistence)

1. **更新日志**：在 `docs/history/lessons-learned.log` 的该条记录下注释：`[Codified into Skill: XXX at YYYY-MM-DD]`。
2. **公告**：更新 `progress.txt` 的“最近完成”：“技能演进完成：[Skill Name] 现已具备防御 [LL描述] 的能力。”

---

## 关键原则

- **隔离性**：不改变原有功能逻辑，仅增强审计深度。
- **可复现性**：即使 LL Log 被删除，Evals 目录下的测试用例也能永久保留这个教训。
- **Fail-Safe**：如果进化后的 Skill 无法捕获“毒素资产”，则必须回退修改并重新诊断。
