---
name: doc-update
description: Workflow for doc-update
---

# Workflow: /doc-update (Feature Spec Sync)

> Trigger: When user calls /doc-update, or during session handover if new business fields/logic were added.
> Goal: Automatically translate code changes into human-readable business specifications.

## Phase 1: Change Tracing

1. Run git diff or git log -p -1.
1. Extract business intent from new fields or logic.

## Phase 2: Domain Spec Locator

1. Find matching .md file in docs/features/ or docs/architecture/.
1. If none, create it.

## Phase 3: Spec Translation

Translate code to business spec:

1. **Business Context**: "Why was this field added?"
1. **Capabilities**: What new features does it unlock?
1. **Data Topology**: E.g., API Field -> DB Field.
1. **Trace Tag**: *(Updated: YYYY-MM-DD by /doc-update)*

## Phase 4: Verification

Report the updated paths to the user.
