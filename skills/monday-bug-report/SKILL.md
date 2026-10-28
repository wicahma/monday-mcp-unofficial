---
name: monday-bug-report
description: >-
  Create standardized bug reports and incident tracking cards on Monday.com boards.
  Use when documenting defects, regression issues, or production incidents with severity, reproduction steps, and stack traces.
---

# Monday Bug & Defect Reporting Workflow

Standardized skill to create and track bug cards on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, objective, factual tone.
- **Zero emojis**.
- Standardized severity: `P1 - Blocker`, `P2 - Major`, `P3 - Minor`, `P4 - Trivial`.
- Title format: `[BUG][SEVERITY] Clear description of the issue` (e.g. `[BUG][P1] Token session rotation failure on corporate SSO`).

## Execution Procedure

### 1. Card Payload:
- `name`: Title format `[BUG][P1/P2] Issue summary`.
- `status`: `Stuck` or `Working on it`.
- `text`: Tautan Sentry, Jira issue, atau log tracing.

### 2. Attach Defect Details as Update:
Always post detailed reproduction steps as an update comment to the card:
- **Environment**: Production, Staging, atau Development.
- **Steps to Reproduce**: Urutan langkah yang menyebabkan kegagalan.
- **Expected Behavior**: Perilaku sistem yang diharapkan.
- **Actual Behavior**: Kesalahan atau respon gagal yang teramati.
- **Stack Trace / Logs**: Cuplikan log error relevan.

### 3. Creation via Python Client:
```python
from src.client import MondayClient

client = MondayClient()

# 1. Create bug card
card = client.create_item(
    board_id="5032042833",
    group_id="new_group29179",
    item_name="[BUG][P1] Kegagalan parsing token expired pada session runner",
    column_values={
        "status": {"label": "Stuck"},
        "text": "https://sentry.company.local/issues/9482"
    }
)

# 2. Attach reproduction details
defect_body = """LAPORAN DEFECT / BUG SYSTEM

1. Environment:
- Cluster: Production (https://portal.company.com)
- Service: Auth Proxy Service v2.1.0

2. Langkah Reproduksi:
- Buka portal dan biarkan sesi idle selama 15 menit.
- Lakukan request mutasi GraphQL.
- Token refresh gagal dan mengembalikan HTTP 401.

3. Dampak Bisnis:
- Pengguna korporat terputus dari sesi kerja aktif."""

client.post_update(item_id=card["id"], body=defect_body)
```
