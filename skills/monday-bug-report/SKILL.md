---
name: monday-bug-report
description: >-
  Create standardized bug reports and incident tracking cards on Monday.com boards.
  Use when documenting defects, regression issues, or production incidents with severity, reproduction steps, and stack traces.
---

# Monday Bug & Defect Reporting Workflow

Standardized skill to create and track bug cards on Monday.com via the `monday` MCP server.

## Standards
- Professional, objective, factual tone.
- **Zero emojis**.
- Standardized severity: `P1 - Blocker`, `P2 - Major`, `P3 - Minor`, `P4 - Trivial`.
- Title format: `[BUG][SEVERITY] Clear description of the issue` (e.g. `[BUG][P1] Token session rotation failure on corporate SSO`).
- Redact secrets, tokens, passwords and customer personal data from logs and stack traces before posting.

## Execution Procedure

### 1. Resolve Board, Group and Columns
Call `get_board_schema` on the target board. Pick the bug/defect group and map the status and link columns to their real IDs.

### 2. Create the Card (`create_item`)
```json
{
  "board_id": "<BOARD_ID>",
  "group_id": "<BUG_GROUP_ID>",
  "item_name": "[BUG][P1] Kegagalan parsing token expired pada session runner",
  "column_values": {
    "<status column id>": {"label": "Stuck"},
    "<link/text column id>": "https://sentry.example.com/issues/9482"
  }
}
```

### 3. Attach Defect Details as Update (`create_update`)
Always post detailed reproduction steps on the new card:
- **Environment**: Production, Staging, atau Development.
- **Steps to Reproduce**: Urutan langkah yang menyebabkan kegagalan.
- **Expected Behavior**: Perilaku sistem yang diharapkan.
- **Actual Behavior**: Kesalahan atau respon gagal yang teramati.
- **Stack Trace / Logs**: Cuplikan log error relevan (sudah diredaksi).

Example body:
```text
LAPORAN DEFECT / BUG SYSTEM

1. Environment:
- Cluster: Production
- Service: Auth Proxy Service v2.1.0

2. Langkah Reproduksi:
- Buka portal dan biarkan sesi idle selama 15 menit.
- Lakukan request mutasi GraphQL.
- Token refresh gagal dan mengembalikan HTTP 401.

3. Dampak Bisnis:
- Pengguna korporat terputus dari sesi kerja aktif.
```

### 4. Report
Return the card ID and update ID to the user.
