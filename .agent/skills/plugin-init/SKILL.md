---
name: plugin-init
description: Workflow for plugin-init
---

# Workflow: /plugin-init (插件初始化与环境构建)

---
description: [plugin-init] æä»¶å·¥åå·¥ä½æµ?â?æ åååå»ºæ°æ°æ®æºéææä»?(GitLab/ZenTao/Jira ç­?
---

# æä»¶å·¥åå·¥ä½æµ?(Plugin Factory Workflow)

> **è§¦åæ¶æº**ï¼éè¦æ¥å¥æ°çå¤é¨ç³»ç»ï¼å¦?Jira, Jenkins, SonarQubeï¼ææ°å¢ç¬ç«çä¸å¡åæ¨¡åã?> **æ ¸å¿ç®æ **ï¼? åéåçæåè§ç Router-Service-Worker-Bridge åå±æ¶æã?
---

## Step 1: æ³¨åä¸å½åè§å?(Registry & Naming)

1. **æ¥éå®ªæ³**ï¼AI å¿é¡»é¦åæå¼ [`contexts.md#11.1`](contexts.md#L323)ï¼æ£æ¥æ¯å¦å·²ç»å­å¨è¯¥ä¸å¡åçåç¼ã?   - è¥ä¸å­å¨ï¼æè®®ä¸ä¸ªæ°ç?2-3 å­æ¯åç¼ï¼å¦ `jr_` ä»£è¡¨ Jiraï¼ã?   - è¥å­å¨ï¼ä¸¥æ ¼æ§è¡ã?
2. **æ ¸å¿åæ°æ®å®ä¹?*ï¼?   - Prefix: `[prefix]_`
   - Domain Component: `[component_name]`
   - Source System: `[system_id]`

## Step 2: éª¨æ¶çæ (Scaffolding)

AI å¨æ§è¡?`/plugin-init` æ¶ï¼å¿é¡»æä»¥ä¸æ åç»æçææä»¶ï¼ä¸å¾ç¼ºå¤±ï¼ï¼

### ð 1. åç«¯ - ä¸å¡é»è¾å±?(Business Layer)
- `devops_collector/plugins/[prefix]_[component]/service.py` -> æ ¸å¿ä¸å¡é»è¾
- `devops_collector/plugins/[prefix]_[component]/bridge.py` -> æ°æ®æ¡¥æ¥ä¸éé
- `devops_collector/plugins/[prefix]_[component]/worker.py` -> å¼æ­¥ééä»»å¡

### ð 2. åç«¯ - API æ¥å£å±?(API Gateway)
- `devops_portal/routers/[prefix]_[component]_router.py` -> ä»éè·¯ç±ãåæ°æ ¡éªãResponse Modelã?
### ð 3. æ°æ®æä¹å±?(Persistence)
- å?`devops_collector/models/` ä¸åå»ºæ¨¡åæä»¶ã?- **å¼ºå¶çº¦æ**ï¼å¿é¡»åå?`id` (BigInt), `source_id`, `created_at` ç­?mdm åºç¡å­æ®µï¼ç¬¦å?[`contexts.md#5`](contexts.md#L91)ã?
### ð 4. èªå¨åæµè¯?(Testing)
- `tests/plugins/[prefix]_[component]/test_worker.py` -> Worker ééæ¨¡æã?- `tests/plugins/[prefix]_[component]/test_router.py` -> Router æ¥å£æ¨¡æã?
---

## Step 3: æå¨éæä¸æ³¨å?(Manual Wiring)

1. å?`devops_portal/main.py` ä¸­æ³¨å?`router`ã?2. å?`devops_collector/core/worker_factory.py` ä¸­æ³¨å?`worker` ä»»å¡ã?3. æ§è¡ `make migrations` çæ Alembic èæ¬ã?
## Step 4: åçæµè¯ (Smoke Test)

// turbo
1. æ§è¡ `make lint` ç¡®ä¿å½åå®å¨å¯¹é½ã?2. è¿è¡åºç¡ mock æµè¯ï¼`pytest tests/plugins/[prefix]_[component]/`ã?
---

## å®å·¥ç­¾ç« 

å¨åå¤ä¸­åå«ï¼?```
[Plugin Init Complete] Domain: [Name] | Prefix: [xx_] | Scaffolding: 6 files generated | Ready for dbt modeling
```
