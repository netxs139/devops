---
name: deploy
description: Workflow for deploy
---

# Workflow: /deploy (发布与部署流水线)

---
description: [deploy] çäº§åå¸ä¸æ ¸å¯¹å·¥ä½æµ â?åå«å¤ä»½ãç°åº¦é¨ç½²ä¸å¥åº·æ¢éæ ¡éª
---

# çäº§åå¸ä¸æ ¸å¯¹å·¥ä½æµ (Deployment Workflow)

> **è§¦åæ¶æº**ï¼ä»»å¡å·²éè¿ `/merge` åå¥æµè¯ï¼åå¤é¨ç½²è³çäº§ç¯å¢æçäº§ç¯å¢æ¼ç»ã?> **æ ¸å¿åå**ï¼é¨ç½²å¿é¡»å¯è§æµãå¯åæ»ãæè¯æ®ã?
---

## Step 1: åå¸åå¿«ç?(Pre-deployment Snapshot)

1. **æ°æ®åºéé»å¤ä»?*ï¼?   ```powershell
   make db-backup  # å¤ä»½ devops_db è?artifacts/backups/
   ```
2. **ç¯å¢åéæ ¡éª**ï¼æ£æ¥çäº§ç¯å¢?`.env` çææå¯é¥æ¯å¦å­å¨ç¼ºå¤±ï¼å¯¹æ¯ `.env.example`ï¼ã?
## Step 2: ç°åº¦é¨ç½²æ§è¡ (Execution)

1. **åæ¯éªè¯**ï¼ç¡®ä¿å½åå¤äº?`main` æ?`release/*` åæ¯ã?2. **å®¹å¨æ»å¨æ´æ°**ï¼?   ```powershell
   make deploy-prod
   ```
   - **æ³¨æäºé¡¹**ï¼ç±äºä½¿ç?Docker Composeï¼ç¡®ä¿?`restart: unless-stopped` å·²çæã?
## Step 3: éä¸éå¥åº·æ¢é (Liveness Check)

é¨ç½²å?AI å¿é¡»æ§è¡ä»¥ä¸æ¢éï¼ç¡®è®¤ç³»ç»æªå¤äºâåæ­»âç¶æï¼

1. **æ ¸å¿ API æ¢é**ï¼è°ç?`GET /health` æ?`/api/v1/auth/status`ï¼ç¡®ä¿è¿å?`200 OK`ã?2. **Worker éåæ¢æµ**ï¼?   ```bash
   docker-compose exec rabbitmq rabbitmqctl list_queues
   ```
   - æ£æ¥æ¯å¦æç§¯åï¼æ¶è´¹èæ¯å¦å¨çº¿ã?3. **æ¥å¿éä¸éå®¡è®¡**ï¼?   ```bash
   docker-compose logs -f --tail=50 api worker
   ```
   - æ«æå?5 åéæ¥å¿ï¼ç¡®è®¤ä¸º `INFO/DEBUG` ç­çº§ï¼æ çåæ?`ERROR/CRITICAL`ã?
---

## Step 4: åå¸å­è¯ä¸åå¸è¯´æ?(Post-deploy)

1. æ´æ° `progress.txt` å°å¯¹åºä»»å¡æ è®°ä¸º `[Deployed] @TIMESTAMP`ã?2. çæ 3 è¡åå¸è¯´æ?(Release Notes)ï¼?   - `ð æ°åè? ...`
   - `ð§ ä¿®å¤é¡? ...`
   - `â ï¸ è¿ç»´æ³¨æ: ...`

---

## å®å·¥ç­¾ç« 

å¨åå¤ä¸­åå«ï¼?```
[Production Deployed] Version: [Tag] | Health: All Green | Backup: artifacts/backups/xxx.sql
```
