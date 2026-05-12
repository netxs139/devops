---
name: lint
description: Workflow for lint
---

# Workflow: /lint (代码质量自检)

---
description: [lint] æ§è¡å¨é¡¹ç®ä»£ç è´¨éå®¡è®¡ï¼åå« Ruff éææ£æ¥ãåç«¯è¡æ°éå¶åå¨é¾è·¯å¯¹é½è§èã?---

# å¨é¡¹ç®è´¨éå®¡è®?(Comprehensive Lint)

è¯¥å·¥ä½æµç¨äºå¨åå¹¶æäº¤ä»åï¼å¯¹é¡¹ç®è¿è¡å¨æ¹ä½"å®ªæ³"åè§æ§æ£æ¥ã?
> **å·¥å·é?*ï¼é¡¹ç®å·²ç»ä¸ä½¿ç¨ **Ruff** ä½ä¸ºå¯ä¸ç?Lint + Format å·¥å·ï¼åè§?[`contexts.md#18`](contexts.md#L568)ï¼ã?> æææ£æ¥ä»¥æ ¹ç®å½?`ruff.toml` ä¸ºåã?
## å®¡è®¡æ­¥éª¤ (Audit Steps)

// turbo
1. **Ruff ä»£ç æ£æ?(Lint)**
   è¿è¡ Ruff æ£æ¥ä»£ç è´¨éä¸è§èåè§ï¼?   ```powershell
   make lint
   ```
   - ç­ä»·äº?`ruff check devops_collector/ devops_portal/ tests/ scripts/`
   - **éè¿æ¡ä»¶**ï¼Exit Code = 0ï¼é¶éè¯¯ã?   - è¥å¤±è´¥ï¼ä¼åå°è¯ `make ruff-fix` èªå¨ä¿®å¤ï¼ä»æéçåæå¨å¤çã?
// turbo
2. **Ruff ä»£ç æ ¼å¼åæ£æ?(Format)**
   æ£æ¥ä»£ç æ ¼å¼ä¸è´æ§ï¼ä¸èªå¨ä¿®æ¹ï¼ï¼?   ```powershell
   ruff format --check devops_collector/ devops_portal/ tests/ scripts/
   ```
   - è¥å¤±è´¥ï¼æ§è¡ `make fmt` èªå¨æ ¼å¼åï¼ç¶åéæ° Commitã?
3. **åç«¯è¡æ°å®¡è®¡ (300 Line Law)**
   æ£æ?HTML/CSS/JS æä»¶æ¯å¦è¶è¿ 300 è¡ï¼
   ```powershell
   python scripts/lint_frontend.py
   ```
   - **çº¢çº¿**ï¼è¥æä»¶è¶éï¼?*ä¸¥ç¦**ç´æ¥éè¿ `# noqa` ç»è¿ï¼å¿é¡»å¨æ¥åä¸­æåºãæ ¸å¿é»è¾æåå»ºè®®ãã?
4. **å¨é¾è·¯å¯¹é½å®¡è®?(Naming Alignment Audit)**
   å¼ºå¶æ ¸å¯¹ [`contexts.md#11.1`](contexts.md#L323) å®ä¹çä¸å¡ååç¼ï¼?   - Service Desk: `sd_`
   - Administration: `adm_`
   - Project Management: `pm_`
   - Testing / Quality: `qa_`
   - Maintenance: `ops_`
   - Report / Dashboard: `rpt_`
   - System / Infra: `sys_`

5. **ä¾èµå¯¼å¥å®¡è®¡ (Dependency Health)**
   è¿è¡ç¯å¢ä¾èµæ£æ¥èæ¬ï¼
   ```powershell
   python scripts/check_imports.py
   ```

## å®å·¥æ å (DoD)
- [ ] `make lint` è¾åº 0 éè¯¯ (Green Build)ã?- [ ] è¥å­å¨é»å¡æ§éè¯¯ï¼å¦ä»£ç æ æ³å¯¼å¥ï¼ï¼å¿é¡»ç«å³ä¿®å¤ã?- [ ] è¥å æ¶æéæ±æ¾å¼å¿½ç¥è§åï¼éå?`ruff.toml` æè¡å?`# noqa` æ æ³¨åå ã?- [ ] å°å®¡è®¡ç»è®ºæ±æ»å¹¶ä»¥è¡¨æ ¼å½¢å¼åé¦ã?
