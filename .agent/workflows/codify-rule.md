# Workflow: /codify-rule (活宪法：规则自动化提取与物理护栏固化)

> **触发条件**：当用户输入 `/codify-rule <文档路径/规则描述>` 或人类要求“将某条自然语言规则转化为审计代码”时。
> **目标**：将 Markdown 文档中的自然语言约束，自动转化为 `scripts/arch_auditor.py` 中的可执行 Python AST/字符串匹配规则，实现“文档即代码”的防腐化闭环。

## 阶段 1：知识提取 (Knowledge Extraction)

1. **阅读目标文档**：读取用户指定的 Markdown 文档（如 `docs/architecture-alignment.md` 或 `contexts.md`）。
1. **定位核心约束**：识别其中的强制性约束（如 "必须使用..."、"严禁使用..."）。
1. **确定审计作用域**：判断该规则应该应用于哪些文件类型或目录（如 `is_router`, `in_scd_class`, `is_service` 等，参考 `arch_auditor.py` 中定义的 `file_ctx`）。

## 阶段 2：编写审计护栏 (Guardrail Codegen)

1. **查阅审计引擎**：读取 `scripts/arch_auditor.py`，了解现有的 `RULES` 列表结构与上下文变量 (`ctx["..."]`)。
1. **生成校验逻辑**：为新提取的规则编写 Python 字典：
   ```python
   {
       "id": "ARCH-XXX", # 自动递增分配下一个可用 ID
       "name": "Rule Short Name",
       "severity": "ERROR" 或 "WARNING",
       "check": lambda line, ctx: <你的 Python 判断逻辑>,
       "message": "违反规则时的友好的英文提示信息。"
   }
   ```
   *注意：判断逻辑尽量轻量化，可以通过简单的字符串 `in` 判断或正则表达式实现。*

## 阶段 3：代码注入与沙盒验证 (Injection & Validation)

1. **注入代码**：将新生成的规则字典插入到 `scripts/arch_auditor.py` 的 `RULES` 列表中（位于 `[ADD_NEW_RULE_HERE]` 注释之前）。
1. **编写毒素测试（TDD）**：
   - 在 `.agent/scratch/` 目录下创建一个包含违反该规则的伪代码文件（例如 `bad_code.py`）。
   - 在同目录下创建一个遵循该规则的规范代码文件（例如 `good_code.py`）。
1. **物理验证**：
   - 运行 `python scripts/arch_auditor.py`，必须能**精准拦截** `bad_code.py`，且**完全放行** `good_code.py` 及现有合法代码。
   - 如果运行崩溃或产生大量误报，**立即撤销**注入，并重构 `lambda` 逻辑。

## 阶段 4：现场清理与持久化 (Cleanup & Persistence)

1. **清理沙盒**：删除 `.agent/scratch/` 下的临时测试文件。
1. **文档对齐**：在最初提取规则的 Markdown 文件的对应段落旁，添加徽章或注释：`<!-- [Codified: ARCH-XXX] -->`，向人类证明该条款已被物理保护。
1. **汇报结果**：向用户展示成功拦截违规代码的终端输出日志，并结束任务。
