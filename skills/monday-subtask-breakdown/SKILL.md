---
name: monday-subtask-breakdown
description: >-
  Break down a parent task, feature, or epic into technical subitems on Monday.com.
  Use when decomposing complex requirements into granular development steps, checklist items, or test tasks.
---

# Monday Subtask Breakdown Workflow

Standardized skill to decompose any parent task card into technical subitems on Monday.com using the `create_subitem` MCP tool.

## Standards
- Professional, corporate engineering tone.
- **Zero emojis**.
- Standardized subitem status: `Working on it`, `Done`, or `Stuck`.
- Format subtask titles clearly: `[MODULE] Specific technical task` (e.g., `[AUTH] Database schema migration`, `[AUTH] Endpoint integration`).

## Execution Procedure

### 1. Identify Parent Task
Resolve the parent item ID from the board (`get_board_items_page`) or from the user, and read it with `get_item`.

### 2. Draft the Subtasks
Each subtask should be a discrete, verifiable unit of work:
- Backend: Schema migrations, service logic, API endpoints.
- Frontend: UI components, form validation, state management.
- Testing: Unit test suite, integration test scenarios.

Show the proposed list to the user before creating anything. Example:
- `[BACKEND] Buat skema migrasi tabel pengguna dan session token`
- `[BACKEND] Implementasi endpoint autentikasi OAuth2 dan SSO`
- `[FRONTEND] Integrasi form login dan penanganan error token expired`
- `[QA] Buat automated unit tests dengan coverage minimal 85%`

### 3. Create the Subitems (`create_subitem`, one call per subtask)
```json
{
  "parent_item_id": "<PARENT_ITEM_ID>",
  "item_name": "[BACKEND] Buat skema migrasi tabel pengguna dan session token"
}
```
Subitems live on a separate subitems board with its own column IDs. To set a status, first look up the subitem board's columns (for example with `all_api_read`: `query { items(ids: ["<PARENT_ITEM_ID>"]) { subitems { board { id columns { id title type } } } } }`), then pass `column_values` with the real status column ID.

### 4. Report
List the created subitem IDs and titles.
