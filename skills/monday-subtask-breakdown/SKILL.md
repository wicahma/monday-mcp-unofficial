---
name: monday-subtask-breakdown
description: >-
  Break down a parent task, feature, or epic into technical subitems on Monday.com.
  Use when decomposing complex requirements into granular development steps, checklist items, or test tasks.
---

# Monday Subtask Breakdown Workflow

Standardized skill to decompose any parent task card into technical subitems on Monday.com (`acc-projects.monday.com`) using `create_subitem`.

## Standards
- Professional, corporate engineering tone.
- **Zero emojis**.
- Standardized subitem status: `Working on it`, `Done`, or `Stuck`.
- Format subtask titles clearly: `[MODULE] Specific technical task` (e.g., `[AUTH] Database schema migration`, `[AUTH] Endpoint integration`).

## Execution Procedure

### 1. Identify Parent Task:
Resolve the target parent card ID (item ID) from the board or user context.

### 2. Subtask Structure:
Each subtask should encompass a discrete, verifiable unit of work:
- Backend: Schema migrations, service logic, API endpoints.
- Frontend: UI components, form validation, state management.
- Testing: Unit test suite, integration test scenarios.

### 3. Creation via Python Client:
```python
from src.client import MondayClient

client = MondayClient()

# Decompose parent task 2892773856 into granular subitems
subtasks = [
    "[BACKEND] Buat skema migrasi tabel pengguna dan session token",
    "[BACKEND] Implementasi endpoint autentikasi OAuth2 dan SSO",
    "[FRONTEND] Integrasi form login dan penanganan error token expired",
    "[QA] Buat automated unit tests dengan coverage minimal 85%"
]

for title in subtasks:
    res = client.create_subitem(
        parent_item_id="2892773856",
        item_name=title,
        column_values={"status": {"label": "Working on it"}}
    )
    print(f"Created subitem: {res.get('id')} - {title}")
```
