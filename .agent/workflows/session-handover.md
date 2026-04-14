---
description: 会话交接协议 — 上下文恢复清单与状态对齐
---

# 会话交接协议 (Session Handover Protocol)

> **适用场景**：新会话开始时、会话中断后恢复时。
> **核心目标**：确保新会话在 60 秒内与上一次会话的状态完全对齐，避免重复探索或遗漏中间状态。

---

## Part A: 新会话启动清单 (Session Bootstrap Checklist)

Agent 在每次新会话开始时，必须按以下顺序执行上下文恢复：

### 1. 读取项目状态快照 (30s)
// turbo
```powershell
# 读取进展跟踪
cat progress.txt
```

// turbo
```powershell
# 确认当前 Git 状态（分支 + 未提交变更）
git branch --show-current
git status --short
```

// turbo
```powershell
# 确认容器运行状态
docker-compose ps --format "table {{.Name}}\t{{.Status}}"
```

### 2. 扫描最近教训 (15s)
// turbo
```powershell
# 读取最近 10 条 Lessons Learned
Get-Content docs/lessons-learned.log | Select-Object -Last 15
```

### 3. 识别未完成工作 (15s)
- 检查 `progress.txt` 的 [进行中] 区域
- 检查 `git stash list` 是否有暂存的工作
- 检查是否有未合并的 Feature Branch

### 4. 产出状态摘要
完成以上步骤后，Agent 必须向用户呈现一份简洁的状态摘要：

```
📍 会话恢复摘要:
- 分支: main | feat/xxx
- 未提交变更: X files modified
- 容器状态: ✅ All healthy / ⚠️ [service] unhealthy
- 当前焦点: [从 progress.txt 提取]
- 待办优先: [从 progress.txt 提取前 2 项]
- 近期教训: [最近 3 条高相关的 Lesson]
```

---

## Part B: 会话结束交接 (Session Debriefing)

每次会话结束前（或用户明确表示切换话题/结束工作时），Agent 应主动执行：

### 1. 状态持久化
- 更新 `progress.txt`（将已完成的移到「最近完成」，新发现的加入「接下来」）
- 确保所有有价值的中间状态已 Commit 或 Stash

### 2. 🚨 知识割取 Harvest [MANDATORY — 每次交接强制执行]
> **红线要求**：不管本次会话是遭遇了阻断报错（Blocker）还是异常顺利，**每一次**会话交接都必须强制沉淀**至少一条**经验教训落盘至 `docs/lessons-learned.log`。严禁以“一切顺利无异常”为由绕过此流程。

获取知识的两个维度（每次必择其一）：
- **🚨 踩坑血泪史**（自问：有没有超过 2 次才跑通的代码？有没有被第三方库版本、时区、ORM 关联坑过？）：记录具体的报错现象与根因。
- **✅ 最佳实践验证**（如果真的极其顺利）：提炼出“为什么这么平通”的原因（比如：精准遵循了某条上下文约束、提前防御了什么参数漏洞等）。

沉淀时，在 `docs/lessons-learned.log` 末尾追加一行，格式与字段为：
```text
| {date} | {Domain} | {现象或正向实践} | {根因分析} | {防线规则/经验固化} |
```

### 3. 交接备忘 (Handover Notes)
在 `progress.txt` 的 [当前状态] 区域，留下给下一个 Agent/会话的简要说明：
- 当前卡在哪里？
- 下一步最该做什么？
- 有什么已经尝试过但失败的方案？（避免重复探索）

### 4. 环境卫生
// turbo
```powershell
# 清理临时文件
make clean
```

### 5. 交接完工标准 (Handover DoD) [MANDATORY]
在宣告会话交接完成前，Agent 必须确信以下五项已 100% 达成：
- [ ] **物理事实对齐**：通过 `git status` 和 `docker ps` 确认环境处于预期状态。
- [ ] **进度状态更新**：`progress.txt` 已准确反映本次会话的所有完成项与待办项。
- [ ] **知识资产沉淀**：本次会话发现的所有坑点已在 `docs/lessons-learned.log` 完成倒序落盘。
- [ ] **工程轨迹溯源**：已将本次会话的关键操作、物理证据（日志碎片）及决策点记录至 `docs/session-history.log`。
- [ ] **交接备忘交底**：已向用户清晰呈现“当前阻断点”与“下一步行动（Next Step）”。

**【核心原则】**：严禁在未更新 `lessons-learned.log` 和 `session-history.log` 的情况下使用“任务已圆满完成”或“会话已就绪”等描述。

---

## Part C: 中断恢复 (Crash Recovery)

当会话因意外中断（如网络断开、Token 超时）后恢复时：

1. **严禁假设上一次操作成功**。必须通过工具验证：
   - `git log -1` 确认最后一次提交内容
   - `docker-compose ps` 确认服务状态
   - `git diff --stat` 确认未提交的变更
2. **检查一致性**：`progress.txt` 中记录的状态是否与物理事实一致。
3. **若发现不一致**：以物理事实为准，修正 `progress.txt`。

---

## 关键原则

- **Physical Truth > Logical Consistency**：永远以工具输出为准，不靠推理猜测
- **Zero Assumption**：不假设上次会话做了什么，每次都验证
- **Fail-Safe**：宁可多读一个文件，也不要跳过验证步骤
